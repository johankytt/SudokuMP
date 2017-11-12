'''
Created on 12. nov 2017

@author: Johan
'''
from common.smp_common import SMPException
from common import smp_network


class SMPPlayerInfo():
	'''
	Representation of player info in a game session
	'''

	_cid = 0  # Unique client id
	_cname = ''  # Player name
	_score = 0  # Current score


	def __init__(self, cid, cname, score=0):
		if len(cname) > 255:
			raise SMPException('Player name is too long, max 255.')

		self._cid = cid
		self._cname = cname
		self._score = score


	def serialize(self):
		pistr = smp_network.pack_uint32(self._cid)
		pistr += smp_network.pack_uint8(self._score)
		pistr += smp_network.pack_uint8(len(self._cname))
		pistr += self._cname


	@staticmethod
	def unserialize(pi_str):
		cid = smp_network.unpack_uint32(pi_str[0:4])
		score = smp_network.unpack_uint8(pi_str[4:5])
		nl = smp_network.unpack_uint8(pi_str[5:6])
		cname = pi_str[6:6 + nl]
		return (SMPPlayerInfo(cid, cname, score), 6 + nl)
