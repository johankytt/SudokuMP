#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import copy
import random

class GameLogic():
    """Represents the sudoku itself, keeps track of the filling
    and check if moves are legal
    """
    
    def __init__(self,num_zeros):
        self.__game_grid, self.__finished_grid = GameLogic.generate_grid(num_zeros)

	def insertNumber(self, row, column, number):
			"""Insert number into sudoku
			:param number, int from 1-9
			:param coordinate tuple (x, y)
			:returns tuple (point, finish) 
					 point, int from -1 to 1
					 -1 -> False
					 0 -> already full coord.
					 1 -> True
					 
					 finish, boolean
			"""
			if self.__game_grid[row][column] == 0:
				if self.check_if_legal(row, column, number):
					self.__game_grid[row][column] = number
					point = 1 
				else:
					point = -1
			else:
				point = 0    
				
			return point, self.check_if_finished()

    def get_grid(self):
        return self.__game_grid
    
    def check_if_legal(self, row, column, number):
        return self.__finished_grid[row][column] == number
    
    def check_if_finished(self):
        return self.__game_grid == self.__finished_grid
		
	#I did the coding assuming this is the way to generate the sudoku game. But this may not be required
	
	SUDOKU_TEMPLATE = [
    [7, 2, 6, 4, 9, 3, 8, 1, 5],
    [3, 1, 5, 7, 2, 8, 9, 4, 6],
    [4, 8, 9, 6, 5, 1, 2, 3, 7],
    [8, 5, 2, 1, 4, 7, 6, 9, 3],
    [6, 7, 3, 9, 8, 5, 1, 2, 4],
    [9, 4, 1, 3, 6, 2, 7, 5, 8],
    [1, 9, 4, 8, 3, 6, 5, 7, 2],
    [5, 6, 7, 2, 1, 4, 3, 8, 9],
    [2, 3, 8, 5, 7, 9, 4, 6, 1],
]

	def generate_grid(num_zeros):
		"""generate a sudoku grid
        :returns tuple (game_grid, finished_grid)
                start_grid, [9][9]
                full_grid, [9][9]
        """
        finished_grid = SUDOKU_TEMPLATE
        game_grid = copy.deepcopy(finished_grid)
        coords = []
        for i in range(9):
            for j in range(9):
                coords.append((i, j))
        random.shuffle(coords)
        for i, j in coords[:num_zeros]:
            game_grid[i][j] = 0
        return game_grid, finished_grid
		
		
	class Game():
		"""Represents the sudoku game on the server side.
		Creates a sudoku object and keeps track of points
		"""
    
    def __init__(self, name, num_players, username):
        self.__num_players = num_players
        self.__uuid = str(uuid.uuid4())
        self.__sudoku = GameLogic()
        self.__users = {username : 0}
        self.__game_name = name
            
    def join(self, username):
        assert(not self.is_full())
        self.__users[username] = 0

    def get_uuid(self):
        return self.__uuid

    def get_sudoku(self):
        return self.__sudoku

    def get_scores(self):
        return sorted(self.__users.items(), key = lambda i: i[1]) # convert dict to array of tuples

    def get_num_players(self):
        return self.__num_players    

    def get_cur_num_players(self):
        return len(self.__users)

    def is_full(self):
        return len(self.__users) == self.__num_players
        
    def insert_number(self, username, row, column, number):
        point, finish = self.__sudoku.insert(row, column, number)
        self.__users[username] += point
        return point, finish
        
    def leave_game(self, username):
        del self.__users[username]
        return self.get_cur_num_players() == 1

    def get_game_name(self):    
        return self.__game_name
		
	def notifyAll(self):
		for i in self.__users:
			return #serialized game object
                
        
    def game_over(self):
        for i in self.__users:
            