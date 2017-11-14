'''
Created on 9. nov 2017

@author: Johan
'''

from common import smp_network
from common.smp_common import LOG, SMPSocketClosedException, SMPException
from common.smp_network import MSG, RSP, DEFAULT_HOST, DEFAULT_PORT, \
    smpnet_recv_head, smpnet_recv_data, smpnet_send_msg
import socket, threading
from common.smp_game_state import SMPGameState


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
			LOG.error('SMPClientNet.connect() socket error: {}'.format(e))
			self._sock.close()
			self._sock = None
			raise SMPException('Unable to connect to {}'.format(addr, port))



	def run(self):
		''' Main client network loop '''
		try:
			self.send_cname()

			while True:
				(mhead, dlen) = smpnet_recv_head(self._sock)
				LOG.debug('Received header: ' + str((mhead, dlen)))

				# If the server indicates a disconnect,
				# respond with the same thing and disconnect
				if mhead == MSG.BYE:
					LOG.info('MSG.BYE received')
					smpnet_send_msg(self._sock, MSG.BYE, '')
					break

				d = smpnet_recv_data(self._sock, dlen)
				LOG.debug('Received data: ' + str((dlen, d)))
				if d != None:
					self.handle_message(mhead, dlen, d)

		except SMPSocketClosedException:
			if not self._bye:
				LOG.info('SMPClientNet: Connection unexpectedly closed. Terminating network thread.')

		except SMPException as e:
			LOG.error(str(e))

# 		except Exception as e:
# 			# TODO: identify specific exceptions
# 			LOG.critical('SMPClientNet: Unhandled exception: {}'.format(e))

		finally:
			LOG.info('SMPClientNet: Network thread done. Closing socket.')
			if self._sock:
				self._sock.close()
				self._sock = None

			# If connection was dropped unexpectedly, do some cleaning up
			if not self._bye:
				self._client.server_disconnect()

			self._client = None


	def disconnect(self):
		''' Starts the client-initiated disconnect routine '''
		self._bye = True

		# Check if the client is actually connected
		if self._sock:
			smpnet_send_msg(self._sock, MSG.BYE, '')
			self._sock.shutdown(socket.SHUT_RDWR)
			self._sock.close()

		self._client = None



	#### NETWORK PROTOCOL HANDLING ####

	def handle_message(self, mhead, dlen, data):
		''' Process the received messages '''

		# Note: MSG.BYE is handled in the receiving loop

		if mhead == MSG.CID:
			LOG.debug('MSG.CID received')
			cid = smp_network.unpack_uint32(data)
			if cid == None:
				cid = 0
			self._client.set_cid(cid)

		elif mhead == RSP.GLIST:
			LOG.debug('RSP.GLIST received')
			gilist = self.unserialize_game_info_list(data)
			self._client.notify_game_list_received(gilist)

		elif mhead == RSP.GJOIN:
			LOG.debug('RSP.GJOIN received')
			LOG.critical('Compare given and received game id. If they don\'t match, the client was already in another game.')
			self._client.notify_game_joined(smp_network.unpack_uint32(data))

		else:
			LOG.critical('Unhandled message: {}'.format((mhead, dlen, data)))



	# PROTOCOL HANDLERS




	def unserialize_game_info_list(self, data):
		gilist = []
		curpos = 0

		while curpos < len(data):
			gilen = smp_network.unpack_uint32(data[curpos:curpos + 4])
			curpos += 4
			gilist.append(SMPGameState.unserialize_info_dict(data[curpos:curpos + gilen]))
			curpos += gilen

		return gilist



	# REQUEST / SEND FUNCTIONS

	def send_cname(self):
		if not smpnet_send_msg(self._sock, MSG.CNAME, self._client._cname):
			raise SMPException('Unable to send player name. Closing connection.')
		LOG.debug('Sent player name')

	def req_new_game(self, max_players):
		smpnet_send_msg(self._sock, MSG.REQ_GNEW, smp_network.pack_uint8(max_players))
		LOG.debug('Sent new game request')

	def req_game_info_list(self):
		smpnet_send_msg(self._sock, MSG.REQ_GLIST, '')
		LOG.debug('Sent game info request')

	def req_join_game(self, gid):
		smpnet_send_msg(self._sock, MSG.REQ_GJOIN, smp_network.pack_uint32(gid))
		LOG.debug('Sent join game request, gid={}'.format(gid))

	def req_leave_game(self):
		smpnet_send_msg(self._sock, MSG.REQ_GLEAVE, '')
		LOG.debug('Sent leave game request')

	def req_enter_number(self, row, col, value):
		msg = 	smp_network.pack_uint8(row) + \
			 	smp_network.pack_uint8(col) + \
			 	smp_network.pack_uint8(value)

		smpnet_send_msg(self._sock, MSG.REQ_GENTRY, msg)
		LOG.debug('Sent MGS.REQ_GENTRY {}'.format((row, col, value)))
