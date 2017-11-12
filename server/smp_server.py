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

class SMPServer():
	'''
	The main SMP server object.
	Holds the lists of connected clients and created games.
	Manages created games. 
	'''

	_server_net = None
	_clients = []
	_games = []  # Private list of all created game sessions
	_next_gid = 1
	_game_lock = None  # A thread lock for game related tasks


	def __init__(self, laddr=DEFAULT_HOST, lport=DEFAULT_PORT):
		'''
		Constructor
		'''
		self._server_net = SMPServerNet(server=self, clist=self._clients, addr=laddr, port=lport)
		self._game_lock = threading.Lock()


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

		LOG.critical('Client cleanup UNIMPLEMENTED. Client {}.'.format(client))
		with self._server_net.client_lock:
			self._clients.remove(client)
			# TODO: implement game clean up


	### GAME RELATED FUNCTIONS ###
	def create_game(self):
		with self._game_lock:
			g = SMPServerGame(self._next_gid)
			self._next_gid += 1
			# TODO: implement game creation
			LOG.critical('New game creation requested. Not implemented yet.')
			self._games.append(g)
			return g

	def destroy_game(self, game):
		# TODO: Clean up the game
		with self._game_lock:
			self._games.remove(game)

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
