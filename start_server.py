'''
Created on 8. nov 2017

@author: Johan Kutt
'''
from server.smp_server import SMPServer
from common.smp_common import LOG
from common.smp_network import DEFAULT_HOST, DEFAULT_PORT
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import sys

if __name__ == '__main__':
	LOG.info('Starting SudokuMP server')

	# Set up argument parser
	parser = ArgumentParser(description="SudokuMP Server", formatter_class=ArgumentDefaultsHelpFormatter)
	parser.add_argument("-H", "--host", help="IP or Name of the host server", default=DEFAULT_HOST)
	parser.add_argument("-P", "--port", help="Listening port of the host server", default=DEFAULT_PORT, type=int)

	# Process arguments
	args = parser.parse_args()

	# Verify that the given port is valid
	try:
		args.port = int(args.port)
	except ValueError:
		LOG.error('Invalid port specified. Port value must be an integer. Unable to start server')
		sys.exit(1)

	if args.port > 65535:
		LOG.error('Invalid port specified. Port must be in the range 0-65535.')
		sys.exit(1)

	server = SMPServer(laddr=args.host, lport=args.port)
	server.start()
