'''
Created on 11. nov 2017

@author: Johan
'''
from common.smp_common import SMPException
import random, copy
import threading
from common import smp_network

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
	board_lock = None


	def __init__(self, initial, solution):
		'''
		Initialises the puzzle given the initial
		and solution matrices.
		'''

		self.board_lock = threading.Lock()

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



	#####################################################

	''' EXTERNAL INTERFACE '''

	@staticmethod
	def get_new_puzzle():
		if len(SMPPuzzle._initials) != len(SMPPuzzle._solutions):
			raise SMPException('Number of hard-coded initials and solutions doesn\'t match')

		n = random.randint(0, len(SMPPuzzle._solutions) - 1)
		return SMPPuzzle(SMPPuzzle._initials[n], SMPPuzzle._solutions[n])



	def enter_number(self, row, col, value):
		''' Attempt to enter a number at the given coordinates.
		@return None if the coords contain initial number
				True if the entered number is correct
				False if the entered number is incorrect or deleted correct number
		'''

		with self.board_lock:
			if self.initial_state[row][col]:
				return None

			oldvalue = self.current_state[row][col]

			# Trying to re-enter existing number
			if oldvalue == value:
				return None

			self.current_state[row][col] = value

			# Entered correct number
			if value == self.solution[row][col]:
				return True

			# Entered zero = deleted current number
			if value == 0:
				if oldvalue == self.solution[row][col]:
					return False  # Deleted the correct value

				return None

			# Entered incorrect number
			return False


	def check_solution(self):
		return self.current_state == self.solution




	########## SERIALIZATION #############

	def serialize(self):
		with self.board_lock:
			p_str = self._serialize_board(self.solution)
			p_str += self._serialize_board(self.initial_state)
			p_str += self._serialize_board(self.current_state)
			return p_str

	@staticmethod
	def unserialize(p_serial):
		solution = SMPPuzzle.unserialize_board(p_serial[0:81])
		initial = SMPPuzzle.unserialize_board(p_serial[81:2 * 81])
		current = SMPPuzzle.unserialize_board(p_serial[2 * 81:3 * 81])

		p = SMPPuzzle(initial, solution)
		p.current_state = current
		return p

	def serialize_current(self):
		with self.board_lock:
			return self._serialize_board(self.current_state)

	def unserialize_current(self, cur_serial):
		with self.board_lock:
			self.current_state = SMPPuzzle.unserialize_board(cur_serial)


	def _serialize_board(self, board):
		b_str = ''

		for row in board:
			for n in row:
				b_str += smp_network.pack_uint8(n)

		return b_str

	@staticmethod
	def unserialize_board(b_str):
		board = [None] * 9

		for row in xrange(0, 9):
			board[row] = [None] * 9
			for col in xrange(0, 9):
				board[row][col] = smp_network.unpack_uint8(b_str[row * 9 + col])

		return board


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
		 [1, 0, 0, 0, 0, 0, 0, 0, 1], [0, 0, 1, 1, 0, 1, 1, 0, 0], [0, 1, 0, 1, 0, 1, 0, 1, 0]],

		[[0, 0, 1, 1, 0, 1, 1, 1, 1], [0, 1, 1, 0, 0, 0, 1, 1, 1], [1, 0, 0, 1, 1, 1, 1, 0, 1],
		 [0, 1, 1, 1, 0, 1, 1, 1, 0], [0, 1, 1, 0, 1, 0, 1, 1, 0], [0, 1, 1, 1, 0, 1, 1, 1, 0],
		 [1, 0, 1, 1, 1, 1, 0, 0, 1], [1, 1, 1, 0, 0, 0, 1, 1, 0], [1, 1, 1, 1, 0, 1, 1, 0, 0]]
	]

	_solutions = [
		[[4, 2, 3, 6, 9, 7, 8, 1, 5], [6, 9, 1, 5, 3, 8, 4, 7, 2], [5, 8, 7, 4, 2, 1, 6, 3, 9],
		 [3, 1, 9, 8, 7, 5, 2, 6, 4], [2, 5, 6, 1, 4, 9, 3, 8, 7], [7, 4, 8, 3, 6, 2, 5, 9, 1],
		 [9, 6, 4, 2, 1, 3, 7, 5, 8], [1, 3, 5, 7, 4, 8, 9, 2, 6], [8, 7, 2, 9, 5, 6, 1, 4, 3]],

		[[9, 6, 3, 1, 7, 4, 2, 5, 8], [1, 7, 8, 3, 2, 5, 6, 4, 9], [2, 5, 4, 6, 8, 9, 7, 3, 1],
		 [8, 2, 1, 4, 3, 7, 5, 9, 6], [4, 9, 6, 8, 5, 2, 3, 1, 7], [7, 3, 5, 9, 6, 1, 8, 2, 4],
		 [5, 8, 9, 7, 1, 3, 4, 6, 2], [3, 1, 7, 2, 4, 6, 9, 8, 5], [6, 4, 2, 5, 9, 8, 1, 7, 3]],

		[[5, 3, 4, 6, 7, 8, 9, 1, 2], [6, 7, 2, 1, 9, 5, 3, 4, 8], [1, 9, 8, 3, 4, 2, 5, 6, 7],
		 [8, 5, 9, 7, 6, 1, 4, 2, 3], [4, 2, 6, 8, 5, 3, 7, 9, 1], [7, 1, 3, 9, 2, 4, 8, 5, 6],
		 [9, 6, 1, 5, 3, 7, 2, 8, 4], [2, 8, 7, 4, 1, 9, 6, 3, 5], [3, 4, 5, 2, 8, 6, 1, 7, 9]]
	]

