##smp_server_game.py

def send_player_info(self):
		''' Sends information about all clients'''
		for j in self._clients:
			smpnet_send_msg(self._sock, RSP.PLIST, self.serialize_player_info())
		LOG.debug('Sent game info')
		
		
		
def serialize_player_info():		''' Returns serialised game info '''
		LOG.debug('Serialising player info')
		gi = ''
		gi += smp_network.pack_uint32(self._gid)		
		for p in in self._clients:
			gi += p.serialize()
		LOG.debug('Serialized player info')
		return gi

##smp_server.py
def send_player_info(self, gid):
		''' Returns Player Info '''
		# [<4:uint32:GI length><GameInfo>]*

		pilstr = ''
		pistr = g[gid].serialize_game_info()
		pilstr += smp_network.pack_uint32(len(gistr))
		pilstr += gistr

		return pilstr		
		
		
		