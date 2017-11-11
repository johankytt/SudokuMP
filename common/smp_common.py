'''
encoding: utf-8
Created on 2. nov 2017

@author: Johan
'''

# Set up logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(threadName)-2s) [%(levelname)s] %(message)s')  # datefmt='%H:%M:%S.'
LOG = logging.getLogger('SMPLogger')



class SMPException(Exception):
	'''
	Custom exception used for any exceptions
	generated by this application
	'''
	# def __init__(self, msg):
	# 	super(SMPException, self).__init__(msg)

class SMPSocketClosedException(SMPException):
	''' Used for detecting remote side socket closure '''