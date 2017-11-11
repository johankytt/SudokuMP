'''
Created on 9. nov 2017

@author: Johan
'''

import threading
from common import smp_network
from common.smp_common import LOG, SMPSocketClosedException
from common.smp_network import MSG, RSP, \
	smpnet_send_msg, smpnet_recv_head, smpnet_recv_data
import socket

BUFFER_SIZE = 1024


class SMPServerClient(threading.Thread):
	'''
	Implements server-side client functionality
	Mainly network protocol related things
	'''

	_sock = None
	_server = None  # Reference to the main server object
	_cid = 0  # Unique client id created by the server. 0 = not assigned / invalid.
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

				# If the remote client disconnected,
				# stop the thread and tell the server to clean up
				if mhead == MSG.BYE:
					LOG.debug('MSG.BYE received')
					break

				d = smpnet_recv_data(self._sock, dlen)
				if d:
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

		if mhead == MSG.REQ_GLIST:
			gilist = self._server.get_game_info_list()
			# TODO: serialize gilist
			if self._sock:
				smpnet_send_msg(self._sock, RSP.GLIST, str(gilist))
				LOG.critical('Game list is not properly serialized')

		else:
			LOG.critical('Need to handle received message: {}'.format((mhead, dlen, msg)))



	def send_cid(self):
		''' Sends the unique client id to the remote client. '''
		smpnet_send_msg(self._sock, MSG.CID, smp_network.pack_uint32(self._cid))

