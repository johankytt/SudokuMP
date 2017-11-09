'''
Created on 8. nov 2017

@author: Johan Kutt
'''
from server.smp_server import SMPServer
from common.smp_common import LOG
from common.smp_network import DEFAULT_HOST, DEFAULT_PORT


# TODO: Add command line configuration options

if __name__ == '__main__':
		LOG.info('Starting SudokuMP server')
		server = SMPServer(laddr=DEFAULT_HOST, lport=DEFAULT_PORT)
		server.start()
