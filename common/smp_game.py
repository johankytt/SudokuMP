'''
Created on 9. nov 2017

@author: Johan
'''


class SMPGame():
	'''
	Implements the state of one game session
	'''

	_gid = 0  # Unique server generated game id. 0 indicates not assigned or invalid


	def __init__(self):
		'''
		Constructor
		'''
