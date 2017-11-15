'''
Created on 9. nov 2017

@author: Johan
'''

from common.smp_common import LOG
from client.smp_client import SMPClient

from PySide import QtGui
import sys


if __name__ == '__main__':
	LOG.info('Starting SudokuMP client')
	app = QtGui.QApplication(sys.argv)
	client = SMPClient()

	app.aboutToQuit.connect(client.exit)
	app.exec_()

	LOG.info('All done')
