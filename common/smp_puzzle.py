'''
Created on 11. nov 2017

@author: Johan
'''
from common.smp_common import SMPException
import random, copy

class SMPPuzzle():
	'''
	Representation of a sudoku puzzle +
	a puzzle generator
	'''

	# 2D lists representing the initial state, current state
	# and final solution of the puzzle

	# Initial state consists of 0s and 1s.
	# 0 indicates empty square, 1 a given one.

	initial_state = None  # Must not be changed after initialisation
	current_state = None
	solution = None  # Must not be changed after initialisation



	def __init__(self, initial, solution):
		'''
		Initialises the puzzle given the initial
		and solution matrices.
		'''

		# Check the matrices have correct dimensions
		if not SMPPuzzle._check_dimensions(initial, solution):
			raise SMPException('Initial state or solution dimensions aren\'t 9x9')

		# Deep copy the given data
		self.initial_state = copy.deepcopy(initial)
		self.solution = copy.deepcopy(solution)
		self.current_state = [0] * 9

		# Initialise the current state according to the initial state matrix
		for row in xrange(0, 9):
			self.current_state[row] = [0] * 9

			for col in xrange(0, 9):
				if initial[row][col]:
					self.current_state[row][col] = solution[row][col]



	''' EXTERNAL INTERFACE '''

	@staticmethod
	def get_new_puzzle():
		if len(SMPPuzzle._initials) != len(SMPPuzzle._solutions):
			raise SMPException('Number of hard-coded initials and solutions doesn\'t match')

		n = random.randint(0, len(SMPPuzzle._solutions) - 1)
		return SMPPuzzle(SMPPuzzle._initials[n], SMPPuzzle._solutions[n])



	#####################################################



	''' FROM HERE ON INTERNAL PRIVATE STUFF '''
	@staticmethod
	def _check_dimensions(self, board):
		''' Checks if the dimensions of the 2D list are correct '''
		if len(board) != 9:
			return False

		for row in board:
			if len(row) != 9:
				return False

		return True



	''' HARD-CODED PUZZLES '''


	_initials = [
		[[0, 1, 1, 0, 1, 0, 1, 0, 0], [1, 0, 1, 0, 1, 1, 0, 0, 0], [1, 0, 0, 1, 0, 0, 0, 0, 0],
		 [1, 0, 0, 0, 0, 0, 1, 0, 1], [0, 0, 1, 0, 0, 0, 1, 0, 0], [1, 0, 1, 0, 0, 0, 0, 0, 1],
		 [0, 0, 0, 0, 0, 1, 0, 0, 1], [0, 0, 0, 1, 1, 0, 1, 0, 1], [0, 0, 1, 0, 1, 0, 1, 1, 0]],

		[[0, 1, 0, 1, 0, 1, 0, 1, 0], [0, 0, 1, 1, 0, 1, 1, 0, 0], [1, 0, 0, 0, 0, 0, 0, 0, 1],
		 [1, 0, 0, 1, 0, 1, 0, 0, 1], [0, 0, 1, 0, 0, 0, 1, 0, 0], [1, 0, 0, 1, 0, 1, 0, 0, 1],
		 [1, 0, 0, 0, 0, 0, 0, 0, 1], [0, 0, 1, 1, 0, 1, 1, 0, 0], [0, 1, 0, 1, 0, 1, 0, 1, 0]]
	]

	_solutions = [
		[[4, 2, 3, 6, 9, 7, 8, 1, 5], [6, 9, 1, 5, 3, 8, 4, 7, 2], [5, 8, 7, 4, 2, 1, 6, 3, 9],
		 [3, 1, 9, 8, 7, 5, 2, 6, 4], [2, 5, 6, 1, 4, 9, 3, 8, 7], [7, 4, 8, 3, 6, 2, 5, 9, 1],
		 [9, 6, 4, 2, 1, 3, 7, 5, 8], [1, 3, 5, 7, 4, 8, 9, 2, 6], [8, 7, 2, 9, 5, 6, 1, 4, 3]],

		[[9, 6, 3, 1, 7, 4, 2, 5, 8], [1, 7, 8, 3, 2, 5, 6, 4, 9], [2, 5, 4, 6, 8, 9, 7, 3, 1],
		 [8, 2, 1, 4, 3, 7, 5, 9, 6], [4, 9, 6, 8, 5, 2, 3, 1, 7], [7, 3, 5, 9, 6, 1, 8, 2, 4],
		 [5, 8, 9, 7, 1, 3, 4, 6, 2], [3, 1, 7, 2, 4, 6, 9, 8, 5], [6, 4, 2, 5, 9, 8, 1, 7, 3]]
	]
