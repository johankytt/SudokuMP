'''
Created on 28. dets 2017

@author: Johan Kutt
'''

import socket
from PySide.QtCore import QThread
import struct
from common.smp_common import LOG

WELCOME_MAGIC = 0xcc02f462
WELCOME_LENGTH = 4 + 4 + 2
WELCOME_PERIOD = 5  # seconds
WELCOME_ADDR = socket.gethostbyname('<broadcast>')
WELCOME_PORT = 31254

### UTILITY FUNCTIONS USED BY BOTH CLASSES ###


def encodeDiscoveryMessage(addrport):
	LOG.debug('Encoding discovery message with {}'.format(addrport))
	return 	struct.pack(">I", WELCOME_MAGIC) + \
			socket.inet_aton(addrport[0]) + \
			struct.pack(">H", addrport[1])


def decodeDiscoveryMessage(msg):
	# Check received message length
	if len(msg) != WELCOME_LENGTH:
		LOG.debug('Discovery message length incorrect')
		return (None, None)

	# Decode received message
	magic = struct.unpack(">I", msg[0:4])[0]
	if magic != WELCOME_MAGIC:
		LOG.debug('Discovery message magic incorrect')
		LOG.debug('Original: {}'.format(hex(WELCOME_MAGIC)))
		LOG.debug('Received: {}'.format(hex(magic)))
		return (None, None)

	msgaddr = socket.inet_ntoa(msg[4:8])
	msgport = struct.unpack(">H", msg[8:10])[0]
	return (msgaddr, msgport)


class SMPDiscoverySender(QThread):
	'''
	Client part of the server discovery routine.
	When started, periodically broadcasts a discovery message
	and waits for server response.
	
	Parent interface is init/start/stop
	Parent must have the functions notifyServerDiscoveryRunning(bool)
	and notifyServerDiscoveryFound(str,int).
	'''

	def __init__(self, myAddrPort, parent):
		super(SMPDiscoverySender, self).__init__()

		self.chatAddrPort = myAddrPort
		self.parent = parent
		self.continueSearching = True

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.socket.settimeout(WELCOME_PERIOD)
		self.socket.bind((myAddrPort[0], 0))

	def stop(self):
		''' Stops the main loop '''
		LOG.debug('SMPDiscoverySender: stopping main loop')
		self.continueSearching = False
		self.socket.sendto('', self.socket.getsockname())  # A bit of a hack to get out of the receive timeout

	def run(self):
		''' Main loop of the server discovery routine '''

		LOG.debug('SMPDiscoverySender: main loop started')

		# Build the discovery message with
		# a bit of obfuscation for public broadcast
		pingmsg = encodeDiscoveryMessage(self.chatAddrPort)
		self.parent.serverDiscoveryRunningSignal.emit(True)

		while self.continueSearching:
			try:
				# Send a broadcast message and wait for response
				self.socket.sendto(pingmsg, (WELCOME_ADDR, WELCOME_PORT))
				LOG.debug('Sent discovery message to {}'.format((WELCOME_ADDR, WELCOME_PORT)))
				pongmsg, servaddr = self.socket.recvfrom(WELCOME_LENGTH)

				LOG.debug('Discovery response received: "{}", len={}'.format(pongmsg, len(pongmsg)))

				(msgaddr, msgport) = decodeDiscoveryMessage(pongmsg)
				if msgaddr is None or msgport is None:
					continue

				LOG.debug('Decoded server address: {}'.format((msgaddr, msgport)))

				# Check that physical and indicated addresses match
				if msgaddr != servaddr[0]:
					LOG.warning(
						'Server physical address {} doesn\'t match indicated address {}'.
						format(servaddr[0], msgaddr)
					)

				# Notify parent that a server has been found
				# self.parent.notifyServerDiscoveryFound(msgaddr, msgport)
				self.parent.serverDiscoveryFoundSignal.emit(msgaddr, msgport)
				self.continueSearching = False

			# Nothing to do here, just send another broadcast
			except socket.timeout:
				pass
			except socket.error:
				LOG.debug('SMPServerDiscoverySender socket error')
				self.continueSearching = False

		self.socket.close()
		self.parent.serverDiscoveryRunningSignal.emit(False)
		LOG.debug('SMPServerDiscoverySender main loop done')


class SMPDiscoveryListener(QThread):
	'''
	Server part of the server discovery routine.
	Listens for discovery messages and sends replies if the message
	is valid
	'''

	def __init__(self, myAddrPort, parent):
		super(SMPDiscoveryListener, self).__init__()

		self.chatAddrPort = myAddrPort
		self.parent = parent
		self.continueListening = True
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.bind(('', WELCOME_PORT))
		# self.socket.bind((WELCOME_ADDR, WELCOME_PORT))
		LOG.debug('Server discovery socket bound to {}'.format(self.socket.getsockname()))

	def stop(self):
		''' Stops the main loop '''
		LOG.info('Stopping server discovery')
		self.continueListening = False
		self.socket.sendto('', self.socket.getsockname())  # A bit of a hack to get out of the receive timeout

	def run(self):
		''' Main loop of the server discovery routine '''

		# Build the discovery message with
		# a bit of obfuscation for public broadcast
		pongmsg = encodeDiscoveryMessage(self.chatAddrPort)
		LOG.debug('SMPDiscoveryListener main loop started')

		while self.continueListening:
			try:
				pingmsg, caddr = self.socket.recvfrom(WELCOME_LENGTH)
				LOG.debug('Discovery response received from {}: "{}" len={}'.format(caddr, pingmsg, len(pingmsg)))
				if self.continueListening:
					LOG.info('Server discovery message from {}'.format(caddr))

				msgAddrPort = decodeDiscoveryMessage(pingmsg)
				if msgAddrPort[0] is None or msgAddrPort[1] is None:
					continue

				# Check that physical and indicated addresses match
				if msgAddrPort[0] != caddr[0]:
					LOG.warning(
						'Client physical address {} doesn\'t match indicated address {}'.
						format(caddr, msgAddrPort)
					)

				# Send response with chat server listening port
				# to the originating address (not the client chat
				# address given in the message)
				self.socket.sendto(pongmsg, caddr)
			except socket.error:
				LOG.debug('SMPDiscoveryListener socket error')
				self.continueListening = False

		self.socket.close()
		LOG.debug('SMPDiscoveryListener main loop done')

