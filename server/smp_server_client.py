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
	_bye = False  # Set to true when the server forcefully disconnects the client

	def __init__(self, cid, client_sock, server):
		super(SMPServerClient, self).__init__(name='Client_{}'.format(cid))
		self._cid = cid
		self._sock = client_sock
		self._server = server

	def __str__(self):
		return 'SMPServerClient:{}'.format(self._cid)


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
			LOG.debug('MSG.CNAME received')
			try:
				self._pinfo = SMPPlayerInfo(self._cid, msg)
			except SMPException:
				self._pinfo = SMPPlayerInfo(self._cid, msg[:255])
				LOG.warning('Too long player name given. Truncated to 255.')

		elif mhead == MSG.REQ_GLIST:
			LOG.debug('MSG.REQ_GLIST received')
			self.send_game_info_list()

		else:
			LOG.critical('Need to handle received message: {}'.format((mhead, dlen, msg)))


	# PROTOCOL HANDLERS



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
