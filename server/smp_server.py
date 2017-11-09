'''
Created on 8. nov 2017

@author: Johan Kutt
'''

from smp_server_net import SMPServerNet
from common.smp_common import LOG
from common.smp_network import DEFAULT_HOST, DEFAULT_PORT

class SMPServer():
	'''
	The main SMP server object
	'''

	_server_net = None
	_clients = []
	_games = []  # Private list of all created game sessions


	def __init__(self, laddr=DEFAULT_HOST, lport=DEFAULT_PORT):
		'''
		Constructor
		'''
		self._server_net = SMPServerNet(addr=laddr, port=lport, clist=self._clients, server=self)


	def start(self):
		'''
		Configure and start the server
		'''
		self._server_net.start()


	def client_disconnect(self, client):
		'''
		Called by SMPServerClient to indicate that
		the client has disconnected and the game and client lists
		need to be cleaned up 
		'''

		LOG.info('Cleaning up after client {}'.format(client))
		self._clients.remove(client)
		# TODO: implement game clean up

