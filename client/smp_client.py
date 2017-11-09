'''
Created on 9. nov 2017

@author: Johan
'''
from common.smp_network import DEFAULT_HOST, DEFAULT_PORT
from client.smp_client_net import SMPClientNet
from common.smp_common import LOG

class SMPClient():
	'''
	classdocs
	'''

	_cid = 0  # Unique client id generated by server. 0 indicates unassigned or invalid.
	_client_net = None
	_game = None
	_gui = None



	def connect(self, addr=DEFAULT_HOST, port=DEFAULT_PORT):
		''' For testing. Should be appended/replaced as needed. '''

		LOG.info('SMPClient connecting to {}.'.format((addr, port)))
		self._client_net = SMPClientNet(self)
		self._client_net.connect(addr, port)


	def disconnect(self, blocking=False):
		''' For testing. Should be appended/replaced as needed. '''

		LOG.info('SMPClient disconnect')
		self._client_net.disconnect()

		# Wait for the network thread to finish
		if blocking and self._client_net.is_alive():
			LOG.debug('SMPClient waiting for network thread to finish')
			self._client_net.join()

		self._cid = 0


	def server_disconnect(self):
		''' Called if the connection has been closed unexpectedly'''

		# TODO: Clean up after server-initiated disconnect
		LOG.info('SMPClient: cleaning up after server disconnect')
		self.set_cid(0)


	def set_cid(self, cid):
		LOG.debug('SMPClient: Setting cid={}'.format(cid))
		self._cid = cid
