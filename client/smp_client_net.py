'''
Created on 9. nov 2017

@author: Johan
'''

from common import smp_network
from common.smp_common import LOG, SMPSocketClosedException
from common.smp_network import MSG, RSP, DEFAULT_HOST, DEFAULT_PORT, \
	smpnet_recv_head, smpnet_recv_data, smpnet_send_msg
import socket, threading



class SMPClientNet(threading.Thread):
	'''
	Implements the network connection of the client.
	Each time the client connects to a server
	a new instance of this object must be created.
	'''

	_client = None  # Reference to the main client class
	_sock = None
	_bye = False  # Set to True when client initiates disconnect


	def __init__(self, client):
		super(SMPClientNet, self).__init__(name="SMPClientNetThread")
		self._client = client


	def connect(self, addr=DEFAULT_HOST, port=DEFAULT_PORT):
		'''
		Connects to the given server and
		starts the network thread 
		'''

		try:
			self._sock = socket.socket()
			self._sock.connect((addr, port))
			LOG.info('Connected to server. Starting network thread.')
			self.start()

		except socket.error as e:
			LOG.error('Socket error: {}'.format(e))

		finally:
			self._sock.close()
			self._sock = None



	def run(self):
		''' Main client network loop '''
		try:
			while True:
				(mhead, dlen) = smpnet_recv_head(self._sock)

				# If the server indicates a disconnect,
				# respond with the same thing and disconnect
				if mhead == MSG.BYE:
					LOG.debug('MSG.BYE received')
					smpnet_send_msg(self._sock, MSG.BYE, '')
					break

				d = smpnet_recv_data(self._sock, dlen)
				if d:
					self.handle_message(mhead, dlen, d)

		except SMPSocketClosedException:
			if not self._bye:
				LOG.debug('SMPClientNet: Server closed connection. Terminating network thread.')

# 		except Exception as e:
# 			# TODO: identify specific exceptions
# 			LOG.critical('SMPClientNet: Unhandled exception: {}'.format(e))

		finally:
			LOG.debug('SMPClientNet: Network thread done. Disconnecting from server.')
			if self._sock:
				self._sock.close()
				self._sock = None

			# If connection was dropped unexpectedly, do some cleaning up
			if not self._bye:
				self._client.server_disconnect()


	def disconnect(self):
		''' Starts the client-initiated disconnect routine '''
		self._bye = True

		# Check if the client is actually connected
		if self._sock:
			smpnet_send_msg(self._sock, MSG.BYE, '')
			self._sock.shutdown(socket.SHUT_RDWR)
			self._sock.close()


	#### NETWORK PROTOCOL HANDLING ####

	def handle_message(self, mhead, dlen, data):
		''' Process the received messages '''

		# Note: MSG.BYE is handled in the receiving loop

		if mhead == MSG.CID:
			cid = smp_network.unpack_uint32(data)
			if cid == None:
				cid = 0
			self._client.set_cid(cid)

		else:
			LOG.critical('Need to handle received message: {}'.format((mhead, dlen, data)))

