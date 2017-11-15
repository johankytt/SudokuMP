'''
Created on 12. nov 2017

@author: Johan
'''
from common.smp_common import SMPException
from common import smp_network


class SMPPlayerInfo(object):
	'''
	Representation of player info in a game session
	'''

	_cid = 0  # Unique client id
	_cname = ''  # Player name
	_score = 0  # Current score


	def __init__(self, cid, name='', score=0):
		self.set_name(name)
		self._cid = cid
		self._score = score

	def __str__(self):
		return 'SMPPlayerInfo[cid={}, cname={}, score={}]'.format(self._cid, self._cname, self._score)


	def set_name(self, name):
		if len(name) > 255:
			raise SMPException('Player name is too long, max 255.')
		self._cname = name

	def set_score(self, score):
		self._score = score

	def add_score(self, update):
		self._score += update
		self._score = max(min(127, self._score), -127)  # Clamp score to [-127,127]

	def get_cid(self):
		return self._cid

	def get_score(self):
		return self._score

	def get_name(self):
		return self._cname


	########### SERIALIZATION ###########

	def serialize(self):
		pistr = smp_network.pack_uint32(self._cid)
		pistr += smp_network.pack_int8(self._score)
		pistr += smp_network.pack_uint8(len(self._cname))
		pistr += self._cname
		return pistr


	@staticmethod
	def unserialize(pi_str):
		''' 
		Unserializes player info object
		@return tuple, (SMPPlayerInfo, number of bytes used)
		'''
		cid = smp_network.unpack_uint32(pi_str[0:4])
		score = smp_network.unpack_int8(pi_str[4:5])
		nl = smp_network.unpack_uint8(pi_str[5:6])
		cname = pi_str[6:6 + nl]
		return (SMPPlayerInfo(cid, cname, score), 6 + nl)
