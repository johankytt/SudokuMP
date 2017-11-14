'''
Created on 12. nov 2017

@author: Johan
'''

from common.smp_game_state import SMPGameState
import threading
from common.smp_common import LOG


class SMPServerGame():
	'''
	classdocs
	'''

	_gid = 0  # Unique game id
	_game_state = None  # An instance of SMPGameState
	_clients = None  # A list of clients who have joined this game
	_client_lock = None

	def __init__(self, gid, max_players):
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
		with self._client_lock:
			self._game_state.remove_player(client._pinfo)
			self._clients.remove(client)


	################# SERIALIZATION ################
	def serialize_game_info(self):
		return self._game_state.serialize_game_info()
