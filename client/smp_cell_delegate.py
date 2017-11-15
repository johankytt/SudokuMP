'''
Created on 15. nov 2017

@author: Johan
'''
from PySide.QtGui import QStyledItemDelegate, QLineEdit, QIntValidator
from PySide.QtCore import Qt

class SMPCellDelegate(QStyledItemDelegate):

	def createEditor(self, parent, option, index):  # @UnusedVariable
		editor = QLineEdit(parent);
		editor.setAlignment(Qt.AlignCenter)
		editor.setValidator(QIntValidator(1, 9))
		return editor