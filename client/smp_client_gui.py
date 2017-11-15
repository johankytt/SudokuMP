'''
Created on 13. nov 2017

@author: Johan
'''
from PySide.QtCore import QObject, Signal, Qt, QTimer
from PySide import QtUiTools, QtGui
from PySide.QtGui import QMessageBox, QIntValidator, QTableWidgetItem
from common.smp_common import LOG
from common import smp_network
import time


class SMPClientGui(QObject):
	'''
	classdocs
	'''

	_lobby_gui = None
	_game_gui = None
	_client = None

	# SIGNALS
	show_lobby_signal = Signal()
	show_game_signal = Signal()
	messagebox_signal = Signal(str)

	disconnect_signal = Signal()
	game_join_signal = Signal(int)
	game_list_update_signal = Signal(list)

	game_state_signal = Signal()
	player_update_signal = Signal()
	board_update_signal = Signal()
	game_start_signal = Signal()
	game_end_signal = Signal()

	duration_timer = QTimer()

	def __init__(self, client):
		'''
		Constructor
		'''
		super(SMPClientGui, self).__init__()
		self._client = client
		guiloader = QtUiTools.QUiLoader()  # @UndefinedVariable
		self._lobby_gui = guiloader.load('client/lobby.ui')
		self._game_gui = guiloader.load('client/game.ui')

		# self._game_gui.show()
		# self._game_gui.hide()

		self.gui_setup()
		self.connect_signals()

	def gui_setup(self):
		self._lobby_gui.portField.setValidator(QIntValidator(1000, 2 ** 16 - 1))
		self._lobby_gui.maxPlayersField.setValidator(QIntValidator(1, 2 ** 8 - 1))

		self._lobby_gui.addressField.setText(smp_network.DEFAULT_HOST)
		self._lobby_gui.portField.setText(str(smp_network.DEFAULT_PORT))

		self.board_gui_setup()



	def connect_signals(self):
		# Notification signals
		self.show_lobby_signal.connect(self.show_lobby)
		self.show_game_signal.connect(self.show_game)
		self.game_join_signal.connect(self.notify_game_joined)
		self.messagebox_signal.connect(self.show_notification)
		self.disconnect_signal.connect(self.notify_disconnect)
		self.game_list_update_signal.connect(self.update_game_list)
		self.game_state_signal.connect(self.notify_game_state)
		self.player_update_signal.connect(self.notify_player_update)
		self.board_update_signal.connect(self.notify_board_update)
		self.game_start_signal.connect(self.notify_game_start)
		self.game_end_signal.connect(self.notify_game_end)

		# Lobby window
		self._lobby_gui.playerNameField.textChanged.connect(self.connection_field_changed)
		self._lobby_gui.addressField.textChanged.connect(self.connection_field_changed)
		self._lobby_gui.portField.textChanged.connect(self.connection_field_changed)

		self._lobby_gui.connectButton.clicked.connect(self.connect_server)
		self._lobby_gui.disconnectButton.clicked.connect(self._client.disconnect)

		self._lobby_gui.refreshGLButton.clicked.connect(self._client.get_game_list)
		self._lobby_gui.joinGameButton.clicked.connect(self.join_game_clicked)

		self._lobby_gui.newGameButton.clicked.connect(self.create_game)
		self._lobby_gui.maxPlayersField.textChanged.connect(self.max_players_changed)

		# Game window
		self._game_gui.leaveGameButton.clicked.connect(self._client.leave_game)
		self.duration_timer.timeout.connect(self.update_game_time)
		self.connect_board_gui_signals()





	############### ACCESS / UTILITY FUNCTIONS ###############

	def show_lobby(self):
		self._lobby_gui.show()
		self._game_gui.hide()
		# self._game_gui.show()

	def show_game(self):
		self._game_gui.show()
		self._lobby_gui.hide()

	def set_connected(self, state):
		self._lobby_gui.playerNameField.setEnabled(not state)
		self._lobby_gui.addressField.setEnabled(not state)
		self._lobby_gui.portField.setEnabled(not state)
		self._lobby_gui.connectButton.setEnabled(not state)
		self._lobby_gui.disconnectButton.setEnabled(state)
		self._lobby_gui.refreshGLButton.setEnabled(state)
		self._lobby_gui.joinGameButton.setEnabled(state)
		self._lobby_gui.maxPlayersField.setEnabled(state)




	######### EXTERNAL NOTIFICATION RECEIVERS ########

	def show_notification(self, msg):
		LOG.debug('GUI showing notification []'.format(msg))
		msgbox = QMessageBox()
		msgbox.setText(msg)
		msgbox.exec_()

	def notify_disconnect(self):
		LOG.debug('GUI received disconnect notification')
		self.show_lobby_signal.emit()
		self.set_connected(False)

	def update_game_list(self, game_info_list):
		# game_info_list is a list of dicts.
		# See description in SMPGameState.unserialize_info_dict()

		self._lobby_gui.gameListTable.setRowCount(0)

		for gi in game_info_list:
			row = self._lobby_gui.gameListTable.rowCount()
			self._lobby_gui.gameListTable.insertRow(row)

			gid = QTableWidgetItem(str(gi['gid']))
			starttime = QTableWidgetItem(str(gi['starttime']))
			maxplayers = QTableWidgetItem(str(gi['maxplayers']))
			joinedplayers = QTableWidgetItem(str(len(gi['playerinfo'])))
			playernames = QTableWidgetItem(', '.join([pi.get_name() for pi in gi['playerinfo']]))

			gid.setTextAlignment(Qt.AlignCenter)
			starttime.setTextAlignment(Qt.AlignCenter)
			maxplayers.setTextAlignment(Qt.AlignCenter)
			joinedplayers.setTextAlignment(Qt.AlignCenter)

			self._lobby_gui.gameListTable.setItem(row, 0, gid)
			self._lobby_gui.gameListTable.setItem(row, 1, starttime)
			self._lobby_gui.gameListTable.setItem(row, 2, maxplayers)
			self._lobby_gui.gameListTable.setItem(row, 3, joinedplayers)
			self._lobby_gui.gameListTable.setItem(row, 4, playernames)

		self._lobby_gui.gameListTable.resizeColumnsToContents()
		LOG.critical('GUI game list update IN TESTING')

	def notify_game_joined(self, gid):
		LOG.debug('gui.notify_game_joined()')
		if gid > 0:
			self.show_game_signal.emit()
			self._game_gui.gidLabel.setText(str(gid))
			self._game_gui.durationLabel.setText(str(0) + ' s')
			self._client.enter_number(4, 3, 8)  # TODO: remove
			LOG.critical('GUI entered a fake number. Remove after testing.')

		# Left / kicked out of a game
		else:
			self.duration_timer.stop()
			self.show_lobby_signal.emit()
			self._lobby_gui.joinGameButton.setEnabled(True)



	############ GAME UPDATES ###########

	def notify_game_start(self):
		self.initial_board_setup()
		# TODO: Show some kind of message somewhere
		# TODO: timer as a last thing
		self.duration_timer.start(1000)

	def notify_game_end(self):
		self.duration_timer.stop()
		self.update_game_time()
		# TODO: Set game board uneditable
		# TODO: show some kind of message somewhere

	def update_game_time(self):
		gs = self._client._game_state
		if gs:
			self._game_gui.durationLabel.setText(str(round(gs.get_duration())) + ' s')
		else:
			self._game_gui.durationLabel.setText('Game not started')

	def notify_game_state(self):
		LOG.debug('GUI game state: {}'.format(self._client._game_state.get_puzzle().solution))
		self.notify_player_update()
		LOG.critical('GUI game state update incomplete')
		# TODO:

	def notify_player_update(self):
		pilist = self._client._game_state.get_pinfo()
		self._game_gui.playersTable.setRowCount(0)

		with self._client._game_state._pinfo_lock:
			for pi in pilist:
				row = self._game_gui.playersTable.rowCount()
				self._game_gui.playersTable.insertRow(row)

				pname = QTableWidgetItem(str(pi.get_name()))
				score = QTableWidgetItem(str(pi.get_score()))
				score.setTextAlignment(Qt.AlignCenter)

				self._game_gui.playersTable.setItem(row, 0, pname)
				self._game_gui.playersTable.setItem(row, 1, score)

			# self._game_gui.playersTable.resizeColumnsToContents()

	def notify_board_update(self):
		puzzle = self._client._game_state.get_puzzle()
		LOG.critical('GUI board update UNIMPLEMENTED')
		# TODO:



	############ GAME BOARD SLOTS/SIGNALS ############

	def board_gui_setup(self):
		bt = self._game_gui.boardTable
		for row in xrange(bt.rowCount()):
			for col in xrange(bt.columnCount()):
				cell = QTableWidgetItem('')
				cell.setTextAlignment(Qt.AlignCenter)
				bt.setItem(row, col, cell)

	def connect_board_gui_signals(self):
		LOG.critical('Board GUI signals not connected')
		self._game_gui.boardTable.cellChanged.connect(self.board_cell_changed)


	def initial_board_setup(self):
		with self._client._game_lock:
			bt = self._game_gui.boardTable
			bt.blockSignals(True)
			puzzle = self._client._game_state.get_puzzle()

			for row in xrange(9):
				for col in xrange(9):
					cell = bt.item(row, col)
					if puzzle.initial_state[row][col]:
						cell.setFlags(cell.flags() & (~Qt.ItemIsEditable))
						cell.setText(str(puzzle.solution[row][col]))
					else:
						cell.setFlags(cell.flags() | Qt.ItemIsEditable)
						cell.setText('')

			bt.blockSignals(False)



		LOG.critical('GUI initial board setup UNIMPLEMENTED')

	def board_cell_changed(self, row, col):
		LOG.debug('Board cell changed: {}'.format((row, col)))
		LOG.debug(self._game_gui.boardTable.item(row, col))
		LOG.critical('Client: board cell changed. NOT CONNECTED')


	def notify_board_update_received(self, board):
		# board is a 9x9 list of numbers
		LOG.critical('GUI board update UNIMPLEMENTED')





	############ LOBBY WINDOW SLOTS ##############

	def connection_field_changed(self, _):
		''' Enables/Disables Connect button based on text field changes '''
		if	len(self._lobby_gui.playerNameField.text()) == 0 or \
			len(self._lobby_gui.addressField.text()) == 0 or \
			len(self._lobby_gui.portField.text()) == 0:

			self._lobby_gui.connectButton.setEnabled(False)
		else:
			self._lobby_gui.connectButton.setEnabled(True)


	def max_players_changed(self, text):
		self._lobby_gui.newGameButton.setEnabled(len(text) > 0)


	def connect_server(self):
		cname = self._lobby_gui.playerNameField.text()
		addr = self._lobby_gui.addressField.text()
		port = int(self._lobby_gui.portField.text())

		if self._client.connect(addr=addr, port=port, cname=cname):
			self.set_connected(True)


	def create_game(self):
		LOG.debug('ClientGui: Create game clicked.')
		max_players = int(self._lobby_gui.maxPlayersField.text())
		LOG.debug('ClientGui: max_players={}'.format(max_players))
		self._client.create_game(max_players)


	def join_game_clicked(self):
		# Disable join button so several simultaneous join requests can't be made
		self._lobby_gui.joinGameButton.setEnabled(False)

		indexes = self._lobby_gui.gameListTable.selectionModel().selectedRows()
		if indexes:
			gid = int(self._lobby_gui.gameListTable.item(indexes[0].row(), 0).text())
			LOG.critical('Selected gid: {}'.format((gid,)))
			self._client.join_game(gid)

		# No game was selected, re-enable join button
		else:
			self._lobby_gui.joinGameButton.setEnabled(True)
