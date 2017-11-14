'''
Created on 12. nov 2017

@author: Johan
'''

from common.smp_game_state import SMPGameState
import threading
from common.smp_common import LOG
import time


class SMPServerGame():
	'''
	classdocs
	'''

	_server = None
	_gid = 0  # Unique game id
	_game_state = None  # An instance of SMPGameState
	_clients = None  # A list of clients who have joined this game
	_client_lock = None

	def __init__(self, server, gid, max_players):
		self._server = server
		self._gid = gid
		self._game_state = SMPGameState(gid, max_players)
		self._clients = []
		self._client_lock = threading.Lock()



	############# PLAYER MANAGEMENT ################
	def add_player(self, client):
		with self._client_lock:
			if self._game_state.add_player(client._pinfo):
				self._clients.append(client)
				client.set_game(self)
				LOG.critical('SMPServerGame: notify all players of player list change UNIMPLEMENTED')
				return True
			else:
				return False

	def remove_player(self, client):
		LOG.debug('SMPServerGame: removing player cid={}'.format(client._cid))
		LOG.critical('SMPServerGame: notify all players of player list change UNIMPLEMENTED')
		with self._client_lock:
			if client in self._clients:
				self._game_state.remove_player(client._pinfo)
				self._clients.remove(client)
				client.notify_game_eject(self._gid)

				if len(self._clients) == 0:
					LOG.info('Last player left. Stopping game. Removing game. gid={}'.format(self._gid))
					self.stop_game()
					self._server.remove_game(self)
				else:
					LOG.debug('{} players remaining.'.format(len(self._clients)))
			else:
				LOG.warn('Client cid={} not in game gid={}'.format(client._cid, self._gid))

	def remove_all_players(self):
		while len(self._clients) > 0:
			c = self._clients[-1]
			self.remove_player(c)

	def player_count(self):
		return len(self._clients)


	############### GAME LOGIC ################

	def start_game(self):
		self._game_state.set_start_time(time.time())
		LOG.critical('Send all players start time update UNIMPLEMENTED')
		LOG.critical('Send all players game board update UNIMPLEMENTED')

	def stop_game(self):
		self._game_state.set_end_time(time.time())
		LOG.critical('Send all players game end notification UNIMPLEMENTED')


	################# SERIALIZATION ################
	def serialize_game_info(self):
		return self._game_state.serialize_game_info()
