'''
Created on 2. nov 2017

@author: Johan Kutt
'''

import socket
from smp_server_client import SMPServerClient
from common.smp_common import LOG
from common.smp_network import DEFAULT_HOST, DEFAULT_PORT



class SMPServerNet():
	'''
	Class implementing the network interface of the server
	'''

	_clients = []  # A reference to the main server client list
	_server = None
	_lsock = None
	_laddr = None
	_lport = None
	_next_cid = 1


	def __init__(self, addr=DEFAULT_HOST, port=DEFAULT_PORT, clist=[], server=None):
		'''
		Constructor. Does basic configuration of the network interface.
		'''
		self._laddr = addr
		self._lport = port
		self._clients = clist
		self._server = server


	def start(self):
		'''
		Just a wrapper in case the class will be changed back
		to inherit from threading.Thread
		'''
		self.run()

	def run(self):
		'''
		Sets up listening port.
		Starts the main server loop for accepting connections.
		'''

		self._listen()

		try:
			LOG.info('Waiting for connections.')
			while True:
				csock = None
				(csock, addr) = self._lsock.accept()
				LOG.info('New connection from {}, cid={}'.format(addr, self._next_cid))
				c = SMPServerClient(self._next_cid, csock, self._server)
				self._clients.append(c)
				c.start()
				self._next_cid += 1

		except KeyboardInterrupt:
			LOG.info('Keyboard interrupt received. Stopping server.')

		finally:
			self.disconnect()

			# Close the newly created client socket
			# if it wasn't handed over to the client thread yet
			if csock:
				csock.close()



	def _listen(self):
		'''
		Sets up the server listening socket
		'''
		self._lsock = socket.socket()
		self._lsock.bind((self._laddr, self._lport))
		backlog = 2
		self._lsock.listen(backlog)
		LOG.info('Listening on ({}:{}), backlog={}'.format(self._laddr, self._lport, backlog))


	def disconnect(self):
		'''
		Closes the listening socket and disconnects all clients 
		'''
		if self._lsock:
			self._lsock.close()
			self._lsock = None

		# Notify all clients to disconnect
		# Clients are removed from the list using the client-initiated disconnect routine
		LOG.debug('Notifying all clients to disconnect')
		for c in self._clients:
			c.notify_disconnect()

		# Wait until all clients have disconnected
		while self._clients:
			c = self._clients[0]
			c.join(1)

			# If the client hasn't disconnected by itself,
			# forcefully close the connection and delete the client
			if c.is_alive():
				LOG.warn('Client {} did not disconnect. Killing the connection.'.format(c))
				c.force_disconnect()
				if c in self._clients:
					self._clients.remove(c)
