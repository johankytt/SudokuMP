'''
Created on 8. nov 2017

@author: Johan Kutt
'''

from smp_server_net import SMPServerNet
from common.smp_common import LOG
from common.smp_network import DEFAULT_HOST, DEFAULT_PORT
import threading
from server.smp_server_game import SMPServerGame
from common import smp_network
from common.smp_server_discovery import SMPDiscoveryListener


class SMPServer():
	'''
	The main SMP server object.
	Holds the lists of connected clients and created games.
	Manages created games. 
	'''

	def __init__(self, laddr=DEFAULT_HOST, lport=DEFAULT_PORT):
		'''
		Constructor
		'''
		self._clients = []
		self._games = []  # Private list of all created game sessions
		self._next_gid = 1

		self._server_net = SMPServerNet(server=self, clist=self._clients, addr=laddr, port=lport)
		self._game_lock = threading.RLock()  # A thread lock for game related tasks

	def start(self):
		'''
		Run the main loop.
		This function will return when the server is exiting.
		'''
		self._serverDiscovery = SMPDiscoveryListener(
			(self._server_net._laddr, self._server_net._lport), self
		)
		LOG.debug('SMPServer: starting server discovery')
		self._serverDiscovery.start()
		self._server_net.start()  # Loops infinitely
		LOG.debug('SMPServer: stopping server discovery')
		self._serverDiscovery.stop()
		self._serverDiscovery.wait()

	def client_disconnect(self, client):
		'''
		Called by SMPServerClient to indicate that
		the client has disconnected and the game and client lists
		need to be cleaned up 
		'''

		LOG.debug('SMPServer: client_disconnect({})'.format(client))
		with self._game_lock:  # TODO:
			if client._game:
				client._game.remove_player(client)
		with self._server_net.client_lock:
			self._clients.remove(client)

	###### GAME RELATED FUNCTIONS ######

	def create_game(self, max_players):
		with self._game_lock:
			g = SMPServerGame(self, self._next_gid, max_players)
			LOG.debug('SMPServer: New game created, {}'.format(g._gid))
			self._next_gid += 1
			self._games.append(g)
			return g.get_gid()

	def remove_game(self, game):
		LOG.info('Removing game gid={}'.format(game._gid))
		with self._game_lock:
			self._games.remove(game)

	def destroy_game(self, game):
		LOG.info('SMPServer: Destroying game gid={}'.format(game._gid))
		game.remove_all_players()

	def get_game(self, gid):
		with self._game_lock:
			for g in self._games:
				if g.get_gid() == gid:
					return g
		return None

	def serialize_game_info_list(self):
		''' Returns a list of serialised game infos '''
		# [<4:uint32:GI length><GameInfo>]*

		gilstr = ''
		with self._game_lock:
			for g in self._games:
				gistr = g.serialize_game_info()
				gilstr += smp_network.pack_uint32(len(gistr))
				gilstr += gistr

		return gilstr
