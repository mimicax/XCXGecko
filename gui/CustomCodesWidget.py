from PyQt4.QtCore import QByteArray
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from CustomCodeFrame import *


class CustomCodesWidget(QWidget):
  read = pyqtSignal(str) # code_label
  word_read = pyqtSignal(str, int) # txt_addr, word_val
  poke = pyqtSignal(str, int) # code_label, new_val
  readmem = pyqtSignal(int, int) # start_addr, num_bytes
  block_read = pyqtSignal(int, int, QByteArray) # start_addr, num_bytes, raw_bytes
  writestr = pyqtSignal(int, QByteArray) # start_addr, ascii_bytes
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, data_store, parent=None):
    super(CustomCodesWidget, self).__init__(parent)
    self.d = data_store
    self.entries = []

    self.btn_add = QPushButton('Add Entry', self)
    self.btn_add.clicked.connect(self.onAdd)

    self.layout = QVBoxLayout(self)
    self.layout.addWidget(self.btn_add)
    self.layout.addStretch()
    self.layout.setSpacing(0)

    self.setStyleSheet('CustomCodesWidget {background-color: white}')

  def onAdd(self):
    new_entry = CustomCodeFrame(self)
    new_entry.poke.connect(self.poke)
    new_entry.log.connect(self.log)

    self.entries.append(new_entry)
    if len(self.entries) % 2 == 0:
      new_entry.setAlternateBGColor()
    self.layout.insertWidget(len(self.entries), new_entry)
