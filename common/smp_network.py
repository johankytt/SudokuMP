'''
Created on 9. nov 2017

@author: Johan
'''
import struct
from common.smp_common import LOG, SMPSocketClosedException

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 22122

MSG_HEADER_LEN = 1
DATA_LEN_LEN = 4


class MSG():
	'''
	SMP Initiating Messages
	MSG and RSP values are all unique
	'''

	BYE = 0x00  # Disconnect
	CID = 0x01  # Send client ID
	CNAME = 0x02
	REQ_GLIST = 0x10  # Request game list
	REQ_GNEW = 0x11  # Create new game
	REQ_GJOIN = 0x12  # Request to join a game
	REQ_GLEAVE = 0x13  # Request to leave current game
	REQ_GENTRY = 0x14  # Request to enter a number in the game board
	GSTATE = 0x20  # Send full game state
	GPUPDATE = 0x21  # Send player update
	GBUPDATE = 0x22  # Send board update
	GSTART = 0x23  # Send game start notification
	GEND = 0x24  # Send game end notification



class RSP():
	'''
	SMP Response Messages
	MSG and RSP values are all unique
	
	MAYBE THIS DOESN'T NEED TO BE SEPARATE FROM MSG
	'''

	GLIST = 0x80  # Send game list
	GJOIN = 0x81  # Confirm game joining


# Utility functions

def pack_int8(num):
	return struct.pack('>b', num)

def unpack_int8(msg):
	try:
		return struct.unpack('>b', msg)[0]  # unpack returns a tuple
	except struct.error:
		LOG.critical('Unable to unpack int8 from \'{}\''.format(msg))
		return None

def pack_uint8(num):
	return struct.pack('>B', num)

def unpack_uint8(msg):
	try:
		return struct.unpack('>B', msg)[0]  # unpack returns a tuple
	except struct.error:
		LOG.critical('Unable to unpack uint8 from \'{}\''.format(msg))
		return None

def pack_uint32(num):
	return struct.pack('>I', num)

def unpack_uint32(msg):
	try:
		return struct.unpack('>I', msg)[0]  # unpack returns a tuple
	except struct.error:
		LOG.critical('Unable to unpack uint32 from \'{}\''.format(msg))
		return None


def pack_message(msghead, data):
	'''
	Packs the message header and data into a string for sending over tcp.
	@param msghead: int, message header from MSG or RSP.
	@param data: str, data to be sent. If not given as a string, it will be converted to a string.
	@return str if all ok, None if the header isn't an int
	'''

	try:
		int(msghead)  # Check if msghead is an int
		if data == None:  # Check if any data was given, if not set it to length 0
			data = ''
		else:
			if str(data) != data:
				LOG.warn('pack_message: Given data is not a string, but will be sent as a string.')
			data = str(data)

		return pack_uint8(msghead) + pack_uint32(len(data)) + str(data)
	except ValueError:
		LOG.critical('pack_message: Given message header is not an integer: {}'.format(msghead))
		return None


def unpack_message_head(msg):
	''' Returns the message header and data length in a tuple '''

	if len(msg) < (MSG_HEADER_LEN + DATA_LEN_LEN):
		LOG.critical('Not enough data in message: {}. Expected at least {} bytes.'.
					format(len(msg), (MSG_HEADER_LEN + DATA_LEN_LEN)))
		return None

	mhead = unpack_uint8(msg[0])
	dlen = unpack_uint32(msg[1:5])
	return (mhead, dlen)


def smpnet_recv_head(sock):
	'''
	Receives the message header and data length from the given socket.
	Raises SMPSocketClosedException if the socket is closed on the remote side.
	@param
	@return
	@raise SMPSocketClosedException
	'''
	m = sock.recv(MSG_HEADER_LEN + DATA_LEN_LEN)  # Receive message header + data length

	# Check if socket has been closed
	if len(m) == 0:
		LOG.debug('smpnet_recv_header: no data received, raising exception')
		raise SMPSocketClosedException('smpnet recv header: no data received.')

	return unpack_message_head(m)


def smpnet_recv_data(sock, dlen):
	'''
	Receives the given amount of data from the given socket.
	Raises SMPSocketClosedException if the socket is closed on the remote side.
	@param
	@return The received data or None if not enough of bytes were received
	@raise SMPSocketClosedException
	'''

	if dlen == 0:
		return ''

	if sock:
		d = sock.recv(dlen)
	else:
		d = ''

	# Check if socket has been closed
	if len(d) == 0:
		LOG.debug('smpnet_recv_data: no data received, raising exception')
		raise SMPSocketClosedException('smpnet recv data: no data received')

	if dlen != len(d):
		LOG.critical('Received data length does not match indicated data length: ' +
					'received {}, expected {}'.format(len(d), dlen))
		return None
	else:
		return d


def smpnet_send_msg(sock, mhead, data):
	'''
	Packs the given message header and data into a string
	and sends it to the given socket
	@param sock
	@param mhead
	@param data
	@return True if the data was sent, False if errors occurred during packing
	'''

	if sock == None:
		LOG.critical('Sending of message failed. Socket not connected.')
		return False

	msg = pack_message(mhead, data)
	if msg:
		sock.sendall(msg)
		return True
	else:
		LOG.critical('Sending of message failed due to packing errors.')
		return False
