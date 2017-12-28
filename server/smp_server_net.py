'''
Created on 2. nov 2017

@author: Johan Kutt
'''

from smp_server_client import SMPServerClient
from common import smp_common
from common.smp_common import LOG
from common.smp_network import DEFAULT_HOST, DEFAULT_PORT
import threading
import snakemq.link, snakemq.packeter, snakemq.messaging, snakemq.rpc


class SMPServerNet():
	'''
	Class implementing the network interface of the server
	'''

	def __init__(self, server, clist, addr=DEFAULT_HOST, port=DEFAULT_PORT,):
		'''
		Constructor. Does basic configuration of the network interface.
		'''
		self._laddr = addr
		self._lport = port

		self._clients = clist  # A reference to the main server client list
		self.client_lock = threading.Lock()
		self._next_cid = 1

		self._server = server

		''' Sets up the snakemq rpc interface '''
		self.mqLink = snakemq.link.Link()
		self.mqLink.add_listener((self._laddr, self._lport))

		self.mqPacketer = snakemq.packeter.Packeter(self.mqLink)
		self.mqMessaging = snakemq.messaging.Messaging(
			smp_common.SERVER_ID, "", self.mqPacketer
		)

		self.mqReceiveHook = snakemq.messaging.ReceiveHook(self.mqMessaging)
		self.mqRpcClient = snakemq.rpc.RpcClient(self.mqReceiveHook)  # For obtaining client interfaces

		self.mqRpcServer = snakemq.rpc.RpcServer(self.mqReceiveHook)
		self.mqRpcServer.transfer_exceptions = False
		self.mqRpcServer.register_object(self, smp_common.SERVER_RPC_NAME)

		# Add custom callbacks
		self.mqMessaging.on_connect.add(self.clientConnect)
		# self.mqMessaging.on_disconnect.add(self.clientDisconnect)  # TODO:

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

		try:
			LOG.debug('Starting snakemq link loop')
			self.mqLink.loop()

		except KeyboardInterrupt:
			LOG.info('KEYBOARD INTERRUPT received. Stopping server.')  # Caps for easier finding in server log

		finally:
			self.disconnect()

	def clientConnect(self, cid, cname):
		'''
		Called when a client connects to the server's public address.
		Creates a new SMPServerClient instance and tells the client
		to reconnect directly to that instance.
		'''

		LOG.debug('ClientConnect: {}, {}'.format(cid, cname))

		# Get client server proxy
		clientProxy = self.mqRpcClient.get_proxy(cname, cname + smp_common.RPC_EXT)
		clientProxy.reconnect.as_signal(smp_common.DEFAULT_MESSAGE_TTL)

		c = SMPServerClient(self._next_cid, self._laddr, self._server)
		c.set_cname(str(cname))

		with self.client_lock:
			self._clients.append(c)
			self._next_cid += 1
			c.start()

		# Tell the new client to reconnect at the given ip/port
		clientProxy.reconnect(c.getAddress(), c.get_cid())

	def disconnect(self):
		'''
		Closes the listening socket and disconnects all clients 
		'''
		# Stop accepting new connections
		self.mqLink.stop()

		# Notify all clients to disconnect
		# Clients are removed from the list using the client-initiated disconnect routine
		LOG.debug('Notifying all clients to disconnect')
		with self.client_lock:
			for c in self._clients:
				c.notify_disconnect()

		# Wait until all clients have disconnected
		while self._clients:
			c = self._clients[0]
			c.join(2.0)

			# If the client hasn't disconnected by itself,
			# forcefully close the connection and delete the client
			if c.is_alive():
				LOG.warn('Client {} did not disconnect. Killing the connection.'.format(c))
				c.force_disconnect()
				with self.client_lock:
					if c in self._clients:
						self._clients.remove(c)

		# Clean up the network interface
		self.mqLink.cleanup()
