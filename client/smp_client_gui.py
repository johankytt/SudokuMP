'''
Created on 13. nov 2017

@author: Johan
'''
from PySide.QtCore import QObject, Signal, Qt, QTimer, QRegExp
from PySide import QtUiTools
from PySide.QtGui import QMessageBox, QIntValidator, QTableWidgetItem, \
	QColor, QRegExpValidator, QFont
from common.smp_common import LOG
from common import smp_network
from client.smp_cell_delegate import SMPCellDelegate
import math


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
	notify_msgbox_signal = Signal(str)
	notify_text_signal = Signal(str)
	status_update_signal = Signal(str)

	serverDiscoveryRunningSignal = Signal(bool)
	serverDiscoveryFoundSignal = Signal(str, int)

	disconnect_signal = Signal()
	connect_signal = Signal()
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
		self._lobby_gui.playerNameField.setValidator(
			QRegExpValidator(QRegExp("[a-zA-Z0-9_]*"))
		)

		self._lobby_gui.addressField.setText(smp_network.DEFAULT_HOST)
		self._lobby_gui.portField.setText(str(smp_network.DEFAULT_PORT))

		self._game_gui.notificationsArea.setAlignment(Qt.AlignCenter)
		self.board_gui_setup()

	def connect_signals(self):
		# Notification signals
		self.show_lobby_signal.connect(self.show_lobby)
		self.show_game_signal.connect(self.show_game)
		self.game_join_signal.connect(self.notify_game_joined)
		self.notify_msgbox_signal.connect(self.show_msgbox)
		self.notify_text_signal.connect(self.show_textnotif)
		self.status_update_signal.connect(self.update_status)
		self.disconnect_signal.connect(self.notify_disconnect)
		self.connect_signal.connect(self.notify_connect)
		self.serverDiscoveryRunningSignal.connect(self.notify_server_discovery_running)
		self.serverDiscoveryFoundSignal.connect(self.notify_server_discovery_found)
		self.game_list_update_signal.connect(self.update_game_list)

		# Lobby window
		self._lobby_gui.playerNameField.textChanged.connect(self.connection_field_changed)
		self._lobby_gui.addressField.textChanged.connect(self.connection_field_changed)
		self._lobby_gui.portField.textChanged.connect(self.connection_field_changed)

		self._lobby_gui.connectButton.clicked.connect(self.connect_server)
		self._lobby_gui.disconnectButton.clicked.connect(self._client.disconnect)
		self._lobby_gui.findServerButton.clicked.connect(self._client.startStopServerDiscovery)

		self._lobby_gui.refreshGLButton.clicked.connect(self._client.get_game_list)
		self._lobby_gui.joinGameButton.clicked.connect(self.join_game_clicked)

		self._lobby_gui.newGameButton.clicked.connect(self.create_game)
		self._lobby_gui.maxPlayersField.textChanged.connect(self.max_players_changed)

		# Game window
		self._game_gui.leaveGameButton.clicked.connect(self._client.leave_game)
		self.duration_timer.timeout.connect(self.update_game_time)
		self._game_gui.boardTable.cellChanged.connect(self.board_cell_changed)
		self.game_state_signal.connect(self.notify_game_state)
		self.player_update_signal.connect(self.notify_player_update)
		self.board_update_signal.connect(self.notify_board_update)
		self.game_start_signal.connect(self.notify_game_start)
		self.game_end_signal.connect(self.notify_game_end)

	############### ACCESS / UTILITY FUNCTIONS ###############

	def show_lobby(self):
		self._lobby_gui.setGeometry(self._game_gui.geometry())
		self.duration_timer.stop()  # Just in case to ensure it's stopped
		self._lobby_gui.show()
		self._game_gui.hide()
		self._lobby_gui.refreshGLButton.clicked.emit()

	def show_game(self):
		self._game_gui.setGeometry(self._lobby_gui.geometry())
		self._game_gui.show()
		self._lobby_gui.hide()
		self.clear_board()
		self.notify_text_signal.emit('Waiting for Players')

	def set_connected(self, state):
		self._lobby_gui.playerNameField.setEnabled(not state)
		self._lobby_gui.addressField.setEnabled(not state)
		self._lobby_gui.portField.setEnabled(not state)
		self._lobby_gui.connectButton.setEnabled(not state)
		self._lobby_gui.findServerButton.setEnabled(not state)
		self._lobby_gui.disconnectButton.setEnabled(state)
		self._lobby_gui.refreshGLButton.setEnabled(state)
		self._lobby_gui.joinGameButton.setEnabled(state)
		self._lobby_gui.maxPlayersField.setEnabled(state)

	###### SERVER DISCOVERY ######

	def notify_server_discovery_running(self, isrunning):
		LOG.debug('GUI server discovery running udpate: {}'.format(isrunning))
		if isrunning:
			self._lobby_gui.findServerButton.setText('Stop server search')
		else:
			self._lobby_gui.findServerButton.setText('Start server search')

	def notify_server_discovery_found(self, addr, port):
		LOG.debug('GUI server discovery found update: {}'.format(addr, port))
		self._lobby_gui.findServerButton.setText('Server found. Click to search again.')
		self._lobby_gui.addressField.setText(addr)
		self._lobby_gui.portField.setText(str(port))

	######### EXTERNAL NOTIFICATION RECEIVERS ########

	def show_msgbox(self, msg):
		LOG.debug('GUI showing notification []'.format(msg))
		msgbox = QMessageBox()
		msgbox.setText(msg)
		msgbox.exec_()

	def show_textnotif(self, msg):
		self._game_gui.notificationsArea.setText(msg)

	def update_status(self, msg):
		self._lobby_gui.statusLabel.setText('Status: ' + msg)

	def notify_disconnect(self):
		LOG.debug('GUI received disconnect notification')
		self.show_lobby_signal.emit()
		self.set_connected(False)

	def notify_connect(self):
		LOG.debug('GUI received connect notification')
		self.set_connected(True)
		self._lobby_gui.refreshGLButton.clicked.emit()

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

		# self._lobby_gui.gameListTable.resizeColumnsToContents()

	def notify_game_joined(self, gid):
		LOG.debug('gui.notify_game_joined()')
		if gid > 0:
			self.show_game_signal.emit()
			self._game_gui.gidLabel.setText(str(gid))
			self.update_game_time()

		# Left / kicked out of a game
		else:
			self.show_lobby_signal.emit()
			self._lobby_gui.joinGameButton.setEnabled(True)

	############ GAME UPDATES ###########

	def notify_game_start(self):
		self.initial_board_setup()
		self.notify_text_signal.emit('GAME STARTED')
		self.duration_timer.start(1000)  # Start as the last thing

	def notify_game_end(self):
		self.duration_timer.stop()
		self.update_game_time()
		self.disable_board()

		self.notify_text_signal.emit('GAME ENDED')

		pilist = sorted(self._client._game_state.get_pinfo(), key=lambda x:x.get_score(), reverse=True)
		if pilist[0].get_cid() == self._client._cid:
			self.notify_text_signal.emit('YOU WIN')
		else:
			self.notify_text_signal.emit('{} WINS'.format(pilist[0].get_name()))

	def update_game_time(self):
		gs = self._client._game_state
		if gs:
			self._game_gui.durationLabel.setText(str(round(gs.get_duration())) + ' s')
		else:
			self._game_gui.durationLabel.setText('Game not started')

	def notify_game_state(self):
		LOG.debug('GUI game state: {}'.format(self._client._game_state.get_puzzle().solution))
		self._game_gui.gamePlayersLabel.setText('Players (max {})'.format(self._client._game_state._max_player_count))
		self.notify_player_update()

	def notify_player_update(self):
		pilist = self._client._game_state.get_pinfo()
		pt = self._game_gui.playersTable
		pt.setRowCount(0)

		with self._client._game_state._pinfo_lock:
			for pi in pilist:
				row = pt.rowCount()
				pt.insertRow(row)

				pname = QTableWidgetItem(str(pi.get_name()))
				score = QTableWidgetItem(str(pi.get_score()))
				pname.setTextAlignment(Qt.AlignCenter)
				score.setTextAlignment(Qt.AlignCenter)

				if pi.get_cid() == self._client._cid:
					f = pname.font()
					f.setWeight(QFont.Bold)
					pname.setFont(f)
					score.setFont(f)
					pname.setForeground(QColor('darkblue'))
					score.setForeground(QColor('darkblue'))

				pt.setItem(row, 0, pname)
				pt.setItem(row, 1, score)

		pt.sortItems(1, Qt.DescendingOrder)
		# self._game_gui.playersTable.resizeColumnsToContents()

	############ GAME BOARD SLOTS/SIGNALS ############

	def board_gui_setup(self):
		bt = self._game_gui.boardTable

		for row in xrange(bt.rowCount()):
			for col in xrange(bt.columnCount()):
				cell = QTableWidgetItem('')
				cell.setTextAlignment(Qt.AlignCenter)
				cell.setFlags(cell.flags() & (~Qt.ItemIsEditable))

				# Create alternating background colour
				if (math.floor(row / 3) + math.floor(col / 3)) % 2 == 0:
					cell.setBackground(QColor(230, 230, 230))

				bt.setItem(row, col, cell)

		bt.setItemDelegate(SMPCellDelegate())

	def disable_board(self):
		# Sets all cells uneditable
		bt = self._game_gui.boardTable
		bt.blockSignals(True)

		for row in xrange(9):
			for col in xrange(9):
				cell = bt.item(row, col)
				cell.setFlags(cell.flags() & (~Qt.ItemIsEditable))
		bt.blockSignals(False)

	def clear_board(self):
		# Clears all cells
		bt = self._game_gui.boardTable
		bt.blockSignals(True)

		for row in xrange(9):
			for col in xrange(9):
				cell = bt.item(row, col)
				cell.setText('')
				cell.setFlags(cell.flags() & (~Qt.ItemIsEditable))
		bt.blockSignals(False)

	def initial_board_setup(self):
		with self._client._game_lock:
			bt = self._game_gui.boardTable
			bt.blockSignals(True)
			puzzle = self._client._game_state.get_puzzle()

			for row in xrange(9):
				for col in xrange(9):
					cell = bt.item(row, col)

					# Set initial cells uneditable
					if puzzle.initial_state[row][col]:
						cell.setForeground(QColor('darkblue'))
						cell.setFlags(cell.flags() & (~Qt.ItemIsEditable))
						cell.setText(str(puzzle.solution[row][col]))
					else:
						cell.setFlags(cell.flags() | Qt.ItemIsEditable)
						cell.setText('')

			bt.blockSignals(False)

	def board_cell_changed(self, row, col):
		try:
			value = int(self._game_gui.boardTable.item(row, col).text())
		except ValueError:
			value = 0
		LOG.debug('Board cell changed: {}'.format((row, col, value)))
		self._client.enter_number(row, col, value)

	def notify_board_update(self):
		puzzle = self._client._game_state.get_puzzle()
		bt = self._game_gui.boardTable
		bt.blockSignals(True)

		for row in xrange(9):
			for col in xrange(9):
				cell = bt.item(row, col)

				if bt.state() == bt.EditingState:
					if cell.row() == row and cell.column() == col:
						try:
							cellvalue = int(cell.text())
						except ValueError:
							cellvalue = 0

						if cellvalue != puzzle.current_state[row][col]:
							bt.closePersistentEditor(cell)

				if puzzle.current_state[row][col]:
					cell.setText(str(puzzle.current_state[row][col]))
				else:
					cell.setText('')

		bt.blockSignals(False)

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
		self._lobby_gui.connectButton.setEnabled(False)
		self._lobby_gui.disconnectButton.setEnabled(True)

		cname = str(self._lobby_gui.playerNameField.text())
		LOG.debug('GUI: cname: {} type: {}'.format(cname, type(cname)))
		addr = self._lobby_gui.addressField.text()
		port = int(self._lobby_gui.portField.text())

		self._client.connectServer(addr=addr, port=port, cname=cname)
# 		if self._client.connect(addr=addr, port=port, cname=cname):
# 			self.set_connected(True)
# 			self._lobby_gui.refreshGLButton.clicked.emit()

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
			self._client.join_game(gid)

		# No game was selected, re-enable join button
		else:
			self._lobby_gui.joinGameButton.setEnabled(True)
