'''
Created on 13. nov 2017

@author: Johan
'''
from PySide.QtCore import QObject
from PySide import QtUiTools
from PySide.QtGui import QMessageBox, QIntValidator
from common.smp_common import LOG
from common import smp_network


class SMPClientGui(QObject):
	'''
	classdocs
	'''

	_lobby_gui = None
	_game_gui = None
	_client = None


	def __init__(self, client):
		'''
		Constructor
		'''
		super(SMPClientGui, self).__init__()
		self._client = client
		guiloader = QtUiTools.QUiLoader()  # @UndefinedVariable
		self._lobby_gui = guiloader.load('client/lobby.ui')
		self._game_gui = guiloader.load('client/game.ui')

		self.gui_setup()
		self.connect_signals()

	def gui_setup(self):
		self._lobby_gui.portField.setValidator(QIntValidator(1000, 2 ** 16 - 1))
		self._lobby_gui.maxPlayersField.setValidator(QIntValidator(1, 2 ** 8 - 1))

		self._lobby_gui.addressField.setText(smp_network.DEFAULT_HOST)
		self._lobby_gui.portField.setText(str(smp_network.DEFAULT_PORT))


	def connect_signals(self):
		self._lobby_gui.playerNameField.textChanged.connect(self.connection_field_changed)
		self._lobby_gui.addressField.textChanged.connect(self.connection_field_changed)
		self._lobby_gui.portField.textChanged.connect(self.connection_field_changed)
		self._lobby_gui.connectButton.clicked.connect(self.connect_server)
		self._lobby_gui.disconnectButton.clicked.connect(self._client.disconnect)
		self._lobby_gui.newGameButton.clicked.connect(self.create_game)
		self._lobby_gui.maxPlayersField.textChanged.connect(self.max_players_changed)

	############### ACCESS / UTILITY FUNCTIONS ###############

	def show_lobby(self):
		self._lobby_gui.show()
		self._game_gui.hide()

	def show_game(self):
		self._game_gui.show()
		self._lobby_gui.hide()

	def set_connected(self, state):
		self._lobby_gui.playerNameField.setEnabled(not state)
		self._lobby_gui.addressField.setEnabled(not state)
		self._lobby_gui.portField.setEnabled(not state)
		self._lobby_gui.connectButton.setEnabled(not state)
		self._lobby_gui.disconnectButton.setEnabled(state)


	######### EXTERNAL NOTIFICATION RECEIVERS ########
	def show_notification(self, msg):
		msgbox = QMessageBox()
		msgbox.setText(msg)
		msgbox.exec_()

	def notify_disconnect(self):
		self._game_gui.hide()
		self._lobby_gui.show()
		self.set_connected(False)

	def update_game_list(self, game_info_list):
		# game_info_list is a list of dicts.
		# See description in SMPGameState.unserialize_info_dict()
		LOG.critical('GUI game list update UNIMPLEMENTED')


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
		max_players = int(self._lobby_gui.maxPlayersField.text())
		self._client.create_game(max_players)
