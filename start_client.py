'''
Created on 9. nov 2017

@author: Johan
'''

from common.smp_common import LOG
from client.smp_client import SMPClient
from client.smp_gui import SMPGui
from time import sleep

from Tkinter import *

# TODO: Add command line configuration options

if __name__ == '__main__':
    # THIS IS ALL FOR TESTING. APPEND OR REPLACE AS NEEDED.

    root = Tk()
    my_gui = SMPGui(root)
    root.mainloop()

    LOG.info('Starting SudokuMP client')
    client = SMPClient()
    client.set_cname('MyName MySurname')
    client.connect()
    client._client_net.req_game_info_list()

    sleep(3)

    client.disconnect(True)
    LOG.info('All done')

