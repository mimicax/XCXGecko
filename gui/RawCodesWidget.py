import operator

from PyQt4.QtCore import QByteArray
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from StaticEntryFrame import *


class RawCodesWidget(QWidget):
  read = pyqtSignal(str) # code_label
  word_read = pyqtSignal(str, int) # txt_addr, word_val
  poke = pyqtSignal(str, int) # code_label, new_val
  readmem = pyqtSignal(int, int) # start_addr, num_bytes
  block_read = pyqtSignal(int, int, QByteArray) # start_addr, num_bytes, raw_bytes
  writestr = pyqtSignal(int, QByteArray) # start_addr, ascii_bytes
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, data_store, parent=None):
    super(RawCodesWidget, self).__init__(parent)
    self.d = data_store
    self.entries = []

    for code in (sorted(self.d.codes.values(), key=operator.attrgetter('idx'))):
      if not code.hidden:
        self.entries.append(StaticEntryFrame(code, None, self))

    self.layout = QVBoxLayout(self)
    if len(self.entries) > 0:
      even = True
      for entry in self.entries:
        even = not even
        if even:
          entry.setAlternateBGColor()
        self.layout.addWidget(entry)
    else:
      self.layout.addWidget(QLabel('No extra codes found in DB'))
    self.layout.addStretch()
    self.layout.setSpacing(0)

    for entry in self.entries:
      entry.read.connect(self.read)
      self.word_read.connect(entry.onWordRead)
      entry.poke.connect(self.poke)
      entry.readmem.connect(self.readmem)
      self.block_read.connect(entry.onBlockRead)
      entry.writestr.connect(self.writestr)
      entry.log.connect(self.log)

    self.setStyleSheet('RawCodesWidget {background-color: white}')
