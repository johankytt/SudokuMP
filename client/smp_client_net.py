'''
Created on 9. nov 2017

@author: Johan
'''

import threading
import snakemq.link, snakemq.packeter, snakemq.messaging, snakemq.rpc
from common import smp_network, smp_common
from common.smp_common import LOG, SMPSocketClosedException, SMPException
from common.smp_network import MSG, RSP, DEFAULT_HOST, DEFAULT_PORT, \
    smpnet_recv_head, smpnet_recv_data, smpnet_send_msg
from common.smp_game_state import SMPGameState


class SMPClientNet(object):
	'''
	Implements the network connection of the client.
	Each time the client connects to a server
	a new instance of this object must be created.
	'''

	def __init__(self, client):
		super(SMPClientNet, self).__init__()
		self._client = client  # Reference to the main client class
		self._handlerConnection = False  # Indicates if the handler has been connected directly
		self._bye = False  # Set to True when client initiates disconnect

	def connect(self, addr=DEFAULT_HOST, port=DEFAULT_PORT,
			serverId=smp_common.SERVER_ID,
			serverRpcName=smp_common.SERVER_RPC_NAME
		):
		'''
		Connects to the given server and
		starts the network thread.
		Will be used twice, first for initial contact and then
		for reconnecting directly to the client handler.
		'''

		# Set up SnakeMQ
		self.mqLink = snakemq.link.Link()
		self.mqLink.add_connector((addr, port))
		self.mqPacketer = snakemq.packeter.Packeter(self.mqLink)
		self.mqMessaging = snakemq.messaging.Messaging(
			self._client._cname, "", self.mqPacketer
		)

		# Set up SnakeMQ RPC interface
		self.mqReceiveHook = snakemq.messaging.ReceiveHook(self.mqMessaging)

		# Create callback rpc interface for server
		self.mqRpcServer = snakemq.rpc.RpcServer(self.mqReceiveHook)
		self.mqRpcServer.transfer_exceptions = False
		self.mqRpcServer.register_object(self, self._client._cname + smp_common.RPC_EXT)

		# Get server proxy
		self.mqRpcClient = snakemq.rpc.RpcClient(self.mqReceiveHook)
		self.serverProxy = self.mqRpcClient.get_proxy(serverId, serverRpcName)

		LOG.info('Starting network thread.')
		self.mqThread = threading.Thread(target=self.run)
		self.mqThread.start()

		# TODO: Handle connection failure. Avoid infinite loop.
		# raise SMPException('Unable to connect to {}'.format(addr, port))

	@snakemq.rpc.as_signal
	def reconnect(self, addr, cid):
		'''
		Called by the server after initial contact to redirect
		the client to its client handler.
		'''

		LOG.debug('Reconnect: addr={}, cid={}'.format(addr, cid))
		self.mqLink.stop()
		LOG.debug('Reconnect: Waiting for mqThread to die')
		self.mqThread.join()  # Note, cleanup is done within the thread

		LOG.debug('Reconnect: Connecting')
		self._client.set_cid(cid)
		self._handlerConnection = True
		self.connect(addr[0], addr[1],
			smp_common.CLIENT_HANDLER_ID.format(cid),
			smp_common.CLIENT_HANDLER_RPC_NAME.format(cid)  # @UndefinedVariable
		)

		# Configure signal functions
		self.serverProxy.bye.as_signal(smp_common.DEFAULT_MESSAGE_TTL)
		self.serverProxy.req_glist.as_signal(smp_common.DEFAULT_MESSAGE_TTL)
		self.serverProxy.req_newgame.as_signal(smp_common.DEFAULT_MESSAGE_TTL)

		# TODO: Add callbacks
		# self.mqMessaging.on_disconnect.add(self.serverDisconnect)

		# Update gui
		self._client.notify_connect()

	##### MAIN LOOP #####

	def run(self):
		''' Main client network loop '''
		self.mqLink.loop()  # , kwargs={'count':5})

# 		try:
# 			while True:
# 				d = smpnet_recv_data(self._sock, dlen)
# 				LOG.debug('Received data: ' + str((dlen, d)))
# 				if d != None:
# 					self.handle_message(mhead, dlen, d)
#
# 		except SMPSocketClosedException:
# 			if not self._bye:
# 				LOG.info('SMPClientNet: Connection unexpectedly closed. Terminating network thread.')
#
# 		except SMPException as e:
# 			LOG.error(str(e))
#
		LOG.info('SMPClientNet: Network thread done. Closing connection.')
		self.mqLink.stop()  # Just in case
		self.mqLink.cleanup()

		# Avoid cleanup for initial server connection
		if self._handlerConnection:
			# If the server disconnected, do some cleanup
			if not self._bye:
				self._client.server_disconnect()

			self._client = None

	##### NETWORK UTILITIES #####

	def is_alive(self):
		return self.mqThread.is_alive()

	def join(self, timeout=None):
		self.mqThread.join(timeout)

	def disconnect(self):
		''' Starts the client-initiated disconnect routine '''
		LOG.debug('SMPClientNet: disconnect()')
		self._bye = True

		# TODO: Check if the client is actually connected
		self.serverProxy.bye()
		self.mqLink.stop()

	@snakemq.rpc.as_signal
	def bye(self):
		''' Graceful server disconnect indication '''
		LOG.debug('Bye() received from server')

		# Disconnect from server and stop network interface
		self.serverProxy.bye()
		self.mqLink.stop()

	##### RPC FUNCTIONS #####

	@snakemq.rpc.as_signal
	def updateGameInfoList(self, msg):
		'''
		Game list update notification from server 
		'''

		LOG.debug('SMPClientNet: updateGameInfoList()')
		gilist = []
		curpos = 0

		while curpos < len(msg):
			gilen = smp_network.unpack_uint32(msg[curpos:curpos + 4])
			curpos += 4
			gilist.append(SMPGameState.unserialize_info_dict(msg[curpos:curpos + gilen]))
			curpos += gilen

		self._client.notify_game_list_received(gilist)

	@snakemq.rpc.as_signal
	def notifyGameJoin(self, gameid):
		LOG.debug('SMPClientNet.notifyGameJoin()')
		# TODO: LOG.critical('Compare given and received game id. ' +
		# 'If they don\'t match, the client was already in another game.')
		self._client.notify_game_joined(gameid)

	@snakemq.rpc.as_signal
	def updateGameState(self, gsSerial):
		LOG.debug('SMPClientNet.updateGameState()')
		self._client.game_state_update(gsSerial)

	#### NETWORK PROTOCOL HANDLING ####

	def handle_message(self, mhead, dlen, data):
		''' Process the received messages '''

# 		if mhead == MSG.TEXT:
# 			LOG.debug('MSG.TEXT received')
# 			# TODO: Use MSG.TEXT for something

# 		if mhead == MSG.GSTATE:
# 			LOG.debug('MSG.GSTATE received')
# 			self._client.game_state_update(data)

		if mhead == MSG.GPUPDATE:
			LOG.debug('MSG.GPUPDATE received')
			self._client.game_player_update(data)

		elif mhead == MSG.GBUPDATE:
			LOG.debug('MSG.GBUPDATE received')
			self._client.game_board_update(data)

		elif mhead == MSG.GSTART:
			LOG.debug('MSG.GSTART received')
			self._client.notify_game_start(smp_network.unpack_uint32(data))

		elif mhead == MSG.GEND:
			LOG.debug('MSG.GEND received')
			self._client.notify_game_end(smp_network.unpack_uint32(data))

		else:
			LOG.critical('Received unhandled message: {}'.format((mhead, dlen, data)))

	########### REQUEST / SEND FUNCTIONS ###########

	def req_game_info_list(self):
		self.serverProxy.req_glist()
		LOG.debug('Sent game info request')

	def req_new_game(self, max_players):
		self.serverProxy.req_newgame(max_players)
		LOG.debug('Sent new game request')

	def req_join_game(self, gid):
		# TODO:
		smpnet_send_msg(self._sock, MSG.REQ_GJOIN, smp_network.pack_uint32(gid))
		LOG.debug('Sent join game request, gid={}'.format(gid))

	def req_leave_game(self):
		# TODO:
		smpnet_send_msg(self._sock, MSG.REQ_GLEAVE, '')
		LOG.debug('Sent leave game request')

	def req_enter_number(self, row, col, value):
		# TODO:
		msg = 	smp_network.pack_uint8(row) + \
			 	smp_network.pack_uint8(col) + \
			 	smp_network.pack_uint8(value)

		smpnet_send_msg(self._sock, MSG.REQ_GENTRY, msg)
		LOG.debug('Sent MGS.REQ_GENTRY {}'.format((row, col, value)))
