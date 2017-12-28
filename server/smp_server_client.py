'''
Created on 9. nov 2017

@author: Johan
'''

import threading
from common import smp_common
from common.smp_common import LOG, SMPSocketClosedException, SMPException
from common.smp_player_info import SMPPlayerInfo
import snakemq.link, snakemq.rpc

# BUFFER_SIZE = 1024


class SMPServerClient(threading.Thread):
	'''
	Implements server-side client functionality
	Mainly network protocol related things
	'''

	def __init__(self, cid, serverip, server):
		super(SMPServerClient, self).__init__(name='Client_{}'.format(cid))
		self._cid = cid  # Unique client id created by the server. 0 = not assigned / invalid.
		self._server = server  # Reference to the main server object

		self.clientProxy = None
		self.setupNetwork(serverip)

		self._pinfo = SMPPlayerInfo(cid)  # An instance of SMPPlayerInfo
		self._game = None  # Reference to the SMPServerGame that the client has joined
		self._bye = False  # Set to true when the server forcefully disconnects the client

	##### NETWORK INTERFACE #####

	def setupNetwork(self, serverip):
		''' Sets up the snakemq rpc interface '''
		self.mqLink = snakemq.link.Link()
		self._laddr = self.mqLink.add_listener((serverip, 0))

		self.mqPacketer = snakemq.packeter.Packeter(self.mqLink)
		self.mqMessaging = snakemq.messaging.Messaging(
			smp_common.CLIENT_HANDLER_ID.format(self._cid), "", self.mqPacketer
		)

		self.mqReceiveHook = snakemq.messaging.ReceiveHook(self.mqMessaging)
		self.mqRpcClient = snakemq.rpc.RpcClient(self.mqReceiveHook)  # For obtaining client interface

		self.mqRpcServer = snakemq.rpc.RpcServer(self.mqReceiveHook)
		self.mqRpcServer.transfer_exceptions = False
		self.mqRpcServer.register_object(self,
			smp_common.CLIENT_HANDLER_RPC_NAME.format(self._cid)  # @UndefinedVariable
		)

		# Add callbacks
		self.mqMessaging.on_connect.add(self.clientConnect)

	def clientConnect(self, cid, cname):
		'''
		Called when a client reconnects directly to the
		SMPServerClient instance
		'''

		LOG.debug('ClientConnect: {}, {}'.format(cid, cname))

		# Get client proxy and configure signal functions
		self.clientProxy = self.mqRpcClient.get_proxy(cname, cname + smp_common.RPC_EXT)
		self.clientProxy.bye.as_signal(smp_common.DEFAULT_MESSAGE_TTL)
		self.clientProxy.updateGameInfoList.as_signal(smp_common.DEFAULT_MESSAGE_TTL)
		self.clientProxy.notifyGameJoin.as_signal(smp_common.DEFAULT_MESSAGE_TTL)
		self.clientProxy.updateGameState.as_signal(smp_common.DEFAULT_MESSAGE_TTL)
		self.clientProxy.updatePlayers.as_signal(smp_common.DEFAULT_MESSAGE_TTL)
		self.clientProxy.updateGameBoard.as_signal(smp_common.DEFAULT_MESSAGE_TTL)
		self.clientProxy.notifyGameStart.as_signal(smp_common.DEFAULT_MESSAGE_TTL)
		self.clientProxy.notifyGameEnd.as_signal(smp_common.DEFAULT_MESSAGE_TTL)

	##### UTILITY FUNCTIONS #####

	def __str__(self):
		return 'SMPServerClient:{}'.format(self._cid)

	def getAddress(self):
		return self._laddr

	def get_cid(self):
		return self._cid

	def get_player_info(self):
		return self._pinfo

	def set_cname(self, name):
		self._pinfo.set_name(name)

	def set_game(self, g):
		self._game = g

	##### MAIN LOOP #####

	def run(self):
		LOG.debug('SMPServerClient: starting mq loop ')

		# Loop until externally stopped
		self.mqLink.loop()

		# Disconnect and clean up
		self.clientProxy = None
		self.mqLink.stop()  # Just in case
		self.mqLink.cleanup()
		LOG.info('SMPServerClient network loop done, {}'.format(self))

		# Clean up if client initiated disconnect
		if not self._bye:
			self._server.client_disconnect(self)

	##### NETWORK UTILITIES #####

	def stop(self):
		self.mqLink.stop()

	def notify_disconnect(self):
		'''
		Sends the disconnect message to the client.
		Client should close the socket on receipt.
		'''

		# smpnet_send_msg(self._sock, MSG.BYE, '')
		if self.clientProxy:
			self.clientProxy.bye()

	def force_disconnect(self):
		'''
		Forcefully closes the socket if the client hasn't disconnected in time
		'''
		LOG.debug('SMPServerClient: force_disconnect()')
		self.mqLink.stop()

	##### RPC FUNCTIONS #####

	@snakemq.rpc.as_signal
	def bye(self):
		self.mqLink.stop()

	@snakemq.rpc.as_signal
	def reqGameList(self):
		LOG.debug('MSG.REQ_GLIST received')
		self.send_game_info_list()

	@snakemq.rpc.as_signal
	def reqNewGame(self, maxPlayers):
		LOG.debug('MSG.REQ_GNEW received')
		gameID = self._server.create_game(maxPlayers)
		self.join_game_handler(gameID)

	@snakemq.rpc.as_signal
	def reqGameJoin(self, gameID):
		LOG.debug('MSG.REQ_GJOIN received')
		self.join_game_handler(gameID)

	@snakemq.rpc.as_signal
	def reqGameLeave(self):
		LOG.debug('MSG.REQ_GLEAVE received')
		self._game.remove_player(self)

	@snakemq.rpc.as_signal
	def reqNumberEntry(self, row, col, value):
		LOG.debug('MSG.REQ_GENTRY received')
		if self._game:
			self._game.enter_number(self, row, col, value)

	##### OTHER HANDLERS #####

	def join_game_handler(self, gid):
		LOG.debug('ServClient: Joining game {}'.format(gid))

		# Check if the client is in a game already and respond with that gid
		if self._game != None:
			self._game.add_player(self)

		# Otherwise try to join the game
		else:
			g = self._server.get_game(gid)
			if g != None:
				g.add_player(self)
				# Note: Join response is sent by the game object
			else:
				self._game = None
				self.notify_gjoin()

	# SEND FUNCTIONS

# 	def send_text(self, msg):
# 		smpnet_send_msg(self._sock, MSG.TEXT, msg)
# 		LOG.debug('Sent MSG.TEXT')

	def send_game_info_list(self):
		''' Sends information about all available games to the client '''
		self.clientProxy.updateGameInfoList(self._server.serialize_game_info_list())
		LOG.debug('Sent game info list')

	def send_game_eject(self, gid):  # @UnusedVariable
		# TODO: Send info via MSG.TEXT
		# The proxy won't be available if the server unexpectedly disconnects
		if self.clientProxy:
			self.clientProxy.notifyGameJoin(0)
			LOG.debug('Sent game eject message')

	def notify_gjoin(self):
		if self._game != None:
			gid = self._game.get_gid()
		else:
			gid = 0

		self.clientProxy.notifyGameJoin(gid)
		LOG.debug('Notified client: notifyGameJoin gid={}'.format(gid))

		if gid:
			self.send_game_state(self._game.serialize_game_state())

	def send_game_state(self, gs_serial):
		self.clientProxy.updateGameState(gs_serial)
		LOG.debug('Sent MSG.GSTATE')

	def send_player_update(self, pi_serial):
		# The proxy won't be available if the server unexpectedly disconnects
		if self.clientProxy:
			self.clientProxy.updatePlayers(pi_serial)
			LOG.debug('Sent MSG.GPUPDATE')

	def send_board_update(self, b_serial):
		self.clientProxy.updateGameBoard(b_serial)
		LOG.debug('Sent MSG.GBUPDATE')

	def send_game_start(self, starttime):
		self.clientProxy.notifyGameStart(starttime)
		LOG.debug('Sent MSG.GSTART')

	def send_game_end(self, endtime):
		# The proxy won't be available if the server unexpectedly disconnects
		if self.clientProxy:
			self.clientProxy.notifyGameEnd(endtime)
			LOG.debug('Sent MSG.GEND')
