'''
Created on 9. nov 2017

@author: Johan
'''

from common.smp_common import LOG
from client.smp_client import SMPClient
from time import sleep

from PySide import QtGui
import sys


# TODO: Add command line configuration options

if __name__ == '__main__':
	# THIS IS ALL FOR TESTING. APPEND OR REPLACE AS NEEDED.

	LOG.info('Starting SudokuMP client')
	app = QtGui.QApplication(sys.argv)
	client = SMPClient()
	client.set_cname('MyName MySurname')
# 	client.connect()
# 	client._client_net.req_game_info_list()
#
# 	sleep(3)
#
# 	client.disconnect(True)

	app.aboutToQuit.connect(client.exit)
	app.exec_()

	LOG.info('All done')
