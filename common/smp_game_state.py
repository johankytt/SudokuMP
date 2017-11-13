'''
Created on 9. nov 2017

@author: Johan
'''

from common import smp_network
from common.smp_player_info import SMPPlayerInfo
from common.smp_puzzle import SMPPuzzle
import threading
from common.smp_common import LOG


class SMPGameState():
	'''
	Implements the state of one game session

	Upper limit of max_players is 255
	The game will start automatically when all players have joined
	'''

	_gid = 0  # Unique game id generated by the server
	_puzzle = None  # An instance of SMPPuzzle
	_max_player_count = 0  # Max number of players.
	_pinfo = None  # A list of SMPPlayerInfo objects
	_pinfo_lock = None
	_start_time = 0
	_end_time = 0


	def __init__(self, gid, max_players):
		'''
		Creates a unique game instance
		@param gid uint A unique game id
		'''
		self._gid = gid
		self._max_player_count = max_players
		self._puzzle = SMPPuzzle.get_new_puzzle()
		self._pinfo = []
		self._pinfo_lock = threading.Lock()


	def add_player(self, player_info):
		# player_info must be a reference to SMPServerClient._pinfo

		with self._pinfo_lock:
			if len(self._pinfo) < self._max_player_count:
				self._pinfo.append(player_info)
				return True
			else:
				return False


	def remove_player(self, player_info):
		with self._pinfo_lock:
			self._pinfo.remove(player_info)

	def has_started(self):
		return self._start_time > 0

	def has_ended(self):
		return self._end_time > self._start_time

	def set_start_time(self, t):
		self._start_time = t

	def set_end_time(self, t):
		self._end_time = t


	############### GAME INFO ##############

	def serialize_game_info(self):
		''' Returns serialised game info '''
		LOG.debug('Serialising game info, gid={}'.format(self._gid))
		gi = ''
		gi += smp_network.pack_uint32(self._gid)
		gi += smp_network.pack_uint32(self._start_time)
		gi += smp_network.pack_uint8(self._max_player_count)
		for p in self._pinfo:
			gi += p.serialize()
		LOG.debug('Serialized game info: gid={}, [{}]'.format(self._gid, (gi,)))
		return gi


	@staticmethod
	def unserialize_info_dict(infostr):
		# GameInfo: <4:uint32:gid><4:uint32:starttime><1:uint8:maxplayers>[PlayerInfo]*
		# PlayerInfo: <4:uint32:cid><1:uint8:score><1:uint8:namelen><namelen:str:cname>

		idict = {}
		idict['gid'] = smp_network.unpack_uint32(infostr[0:4])
		idict['starttime'] = smp_network.unpack_uint32(infostr[4:8])
		idict['maxplayers'] = smp_network.unpack_uint8(infostr[8:9])
		idict['playerinfo'] = []

		curpos = 9
		while curpos < len(infostr):
			(pi, pilen) = SMPPlayerInfo.unserialize(infostr[curpos:])
			idict['playerinfo'].append(pi)
			curpos += pilen

		return idict
