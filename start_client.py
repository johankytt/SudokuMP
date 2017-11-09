'''
Created on 9. nov 2017

@author: Johan
'''

from common.smp_common import LOG
from client.smp_client import SMPClient
from time import sleep


# TODO: Add command line configuration options

if __name__ == '__main__':

	# THIS IS ALL FOR TESTING. APPEND OR REPLACE AS NEEDED.

	LOG.info('Starting SudokuMP server')
	client = SMPClient()
	client.connect()

	sleep(5)

	client.disconnect(True)

	LOG.info('All done')
