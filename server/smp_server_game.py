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

	def get_gid(self):
		return self._gid


	############# PLAYER MANAGEMENT ################
	def add_player(self, client):
		with self._client_lock:

			# Check if client is already playing
			if client in self._clients:
				client.notify_gjoin()  # Also sends full game state

			# If not, add it to the lists
			elif self._game_state.add_player(client.get_player_info()):
				self._clients.append(client)
				client.set_game(self)
				client.get_player_info().set_score(0)
				client.notify_gjoin()

				self.send_player_update()

				# If all players have joined, start the game
				if self._game_state.game_full():
					self._start_game()


	def remove_player(self, client):
		LOG.debug('SMPServerGame: removing player cid={}'.format(client._cid))

		with self._client_lock:
			if client in self._clients:
				# Remove client
				self._game_state.remove_player(client.get_player_info())
				self._clients.remove(client)
				client.set_game(None)
				client.send_game_eject(self._gid)

				self.send_player_update()

				# If one player remaining, stop the game
				if len(self._clients) == 1:
					self.stop_game()

				# All players left, destroy game
				elif len(self._clients) == 0:
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


	############# CLIENT UPDATES #############

	def send_player_update(self, client=None):
		'''
		Send player info update to one or all clients.
		Must be called from within self._client_lock.
		'''
		# TODO: consider wrapping the single client in a list
		# TODO: then could also create a list of all other clients except the one who got full game state
		pi_serial = self._game_state.seralize_player_infos()

		if client != None:
			client.send_player_update(pi_serial)
		else:
			for c in self._clients:
				c.send_player_update(pi_serial)


	def send_board_update(self, client=None):
		'''
		Send board update to one or all clients.
		Must be called from within self._client_lock.
		'''
		# TODO: consider wrapping the single client in a list
		# TODO: then could also create a list of all other clients except the one who got full game state
		b_serial = self._game_state.serialize_current_board()

		if client != None:
			client.send_board_update(b_serial)
		else:
			for c in self._clients:
				c.send_board_update(b_serial)



	############### GAME LOGIC ################

	def _start_game(self):
		'''
		Starts the game and sends notifications to all players.
		This function must be called only from another function
		that already holds the client_lock
		'''
		if not self._game_state.has_started():
			self._game_state.set_start_time(time.time())
			for c in self._clients:
				c.send_game_start(self._game_state._start_time)


	def stop_game(self):
		'''
		Stops the game and sends notifications to all players.
		This function must be called only from another function
		that already holds the client_lock
		'''
		if not self._game_state.has_ended():
			self._game_state.set_end_time(time.time())
			for c in self._clients:
				c.send_game_end(self._game_state._end_time)


	def enter_number(self, client, row, col, value):
		'''
		Attempts to enter the given number at the given coordinates.
		@param client, instance of SMPServerClient, the client who is entering the number and gets the points
		@param row
		@param col
		@param value
		'''
		LOG.debug('ServGame.enter_number(): gid={}, cid={}, {}'.format(self._gid, client._cid, (row, col, value)))

		if not self._game_state.has_started() or self._game_state.has_ended():
			LOG.critical('Number Entry: game not started or has ended. How did we get here???')
			return

		with self._client_lock:
			res = self._game_state.enter_number(row, col, value)

			if res == None:
				score = 0
			elif res:
				score = 1
			else:
				score = -1

			client.get_player_info().add_score(score)

			self.send_board_update()
			self.send_player_update()
			if self._game_state.get_puzzle().check_solution():
				self.stop_game()



	################# SERIALIZATION ################

	def serialize_game_info(self):
		return self._game_state.serialize_game_info()

	def serialize_game_state(self):
		return self._game_state.serialize()

	def serialize_current_board(self):
		return self._game_state.serialize_current_board()
