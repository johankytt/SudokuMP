'''
Created on 9. nov 2017

@author: Johan
'''

import threading
from common import smp_network
from common.smp_common import LOG, SMPSocketClosedException, SMPException
from common.smp_network import MSG, RSP, \
	smpnet_send_msg, smpnet_recv_head, smpnet_recv_data
import socket
from common.smp_player_info import SMPPlayerInfo

BUFFER_SIZE = 1024


class SMPServerClient(threading.Thread):
	'''
	Implements server-side client functionality
	Mainly network protocol related things
	'''

	_sock = None
	_server = None  # Reference to the main server object
	_cid = 0  # Unique client id created by the server. 0 = not assigned / invalid.
	_pinfo = None  # An instance of SMPPlayerInfo
	_game = None  # Reference to the SMPServerGame that the client has joined
	_bye = False  # Set to true when the server forcefully disconnects the client

	def __init__(self, cid, client_sock, server):
		super(SMPServerClient, self).__init__(name='Client_{}'.format(cid))
		self._cid = cid
		self._sock = client_sock
		self._server = server
		self._pinfo = SMPPlayerInfo(cid)

	def __str__(self):
		return 'SMPServerClient:{}'.format(self._cid)

	def set_game(self, g):
		self._game = g


	def run(self):
		try:
			self.send_cid()

			while True:
				(mhead, dlen) = smpnet_recv_head(self._sock)
				LOG.debug('Received header: ' + str((mhead, dlen)))

				# If the remote client disconnected,
				# stop the thread and tell the server to clean up
				if mhead == MSG.BYE:
					LOG.debug('MSG.BYE received')
					break

				d = smpnet_recv_data(self._sock, dlen)
				LOG.debug('Received data: ' + str((dlen, d)))
				if d != None:
					self.handle_message(mhead, dlen, d)

		except SMPSocketClosedException:
			if not self._bye:
				LOG.debug('{}: Client closed connection. Terminating client thread.'.format(self))

# 		except Exception as e:
# 			# TODO: identify specific exceptions
# 			LOG.error('Unhandled exception: {} in {}'.format(e, self))

		finally:
			# Disconnect and clean up
			LOG.info('Disconnecting {}'.format(self))
			if self._sock != None:
				self._sock.close()
				self._sock = None

			if not self._bye:
				self._server.client_disconnect(self)


	def notify_disconnect(self):
		'''
		Sends the disconnect message to the client.
		Client should close the socket on receipt.
		'''
		smpnet_send_msg(self._sock, MSG.BYE, '')

	def force_disconnect(self):
		'''
		Forcefully closes the socket if the client hasn't disconnected in time
		'''
		if self._sock:
			self._bye = True
			self._sock.shutdown(socket.SHUT_RDWR)
			self._sock.close()


	#### NETWORK PROTOCOL HANDLING ####

	def handle_message(self, mhead, dlen, msg):
		''' Process the received messages '''

		# Note: MSG.BYE is handled in the receiving loop

		if mhead == MSG.CNAME:
			LOG.info('MSG.CNAME received')
			try:
				self._pinfo.set_name(msg)
			except SMPException:
				self._pinfo.set_name(msg[:255])
				LOG.warning('Too long player name given. Truncated to 255.')

		elif mhead == MSG.REQ_GLIST:
			LOG.info('MSG.REQ_GLIST received')
			self.send_game_info_list()

		elif mhead == MSG.REQ_GNEW:
			LOG.info('MSG.REQ_GNEW received')
			gid = self._server.create_game(smp_network.unpack_uint8(msg))
			self.join_game_handler(gid)

		elif mhead == MSG.REQ_GJOIN:
			LOG.info('MSG.REQ_GJOIN received')
			gid = smp_network.unpack_uint32(msg)
			self.join_game_handler(gid)

		elif mhead == MSG.REQ_GLEAVE:
			LOG.info('MSG.REQ_GLEAVE received')
			self._game.remove_player(self)
			self._game = None
		else:
			LOG.critical('Need to handle received message: {}'.format((mhead, dlen, msg)))



	# PROTOCOL HANDLERS
	def join_game_handler(self, gid):
		LOG.debug('ServClient: Joining game {}'.format(gid))
		# Check if client is in a game already and respond with that gid
		if self._game != None:
			resp_id = self._game._gid
		elif self._server.join_game(gid, self):
			resp_id = gid
		else:
			resp_id = 0

		smpnet_send_msg(self._sock, RSP.GJOIN, smp_network.pack_uint32(resp_id))






	# SEND FUNCTIONS

	def send_cid(self):
		''' Sends the unique client id to the remote client. '''
		if not smpnet_send_msg(self._sock, MSG.CID, smp_network.pack_uint32(self._cid)):
			raise SMPException('Unable to send client id. Disconnecting.')
		LOG.debug('Sent client id')

	def send_game_info_list(self):
		''' Sends information about all available games to the client '''
		smpnet_send_msg(self._sock, RSP.GLIST, self._server.serialize_game_info_list())
		LOG.debug('Sent game info')

	def notify_game_eject(self, gid):
		smpnet_send_msg(self._sock, RSP.GJOIN, smp_network.pack_uint32(0))
		LOG.critical('servclient: game eject: Implement server to client text messages')
