'''
Created on 12. nov 2017

@author: Johan
'''

from common.smp_game_state import SMPGameState


class SMPServerGame():
	'''
	classdocs
	'''

	_gid = 0  # Unique game id
	_game_state = None  # An instance of SMPGameState
	_clients = []  # A list of clients who have joined this game


	def __init__(self, gid):
		self._gid = gid
		self._game_state = SMPGameState(gid)


	def serialize_game_info(self):
		return self._game_state.serialize_game_info()
