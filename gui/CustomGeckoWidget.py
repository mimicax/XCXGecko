import operator

from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from StaticEntryFrame import *


class CustomGeckoWidget(QWidget):
  read = pyqtSignal(str) # code_label
  poke = pyqtSignal(str, int) # code_label, new_val
  word_read = pyqtSignal(str, int) # txt_addr, word_val
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, codes, parent=None):
    super(CustomGeckoWidget, self).__init__(parent)
    self.codes = codes
    self.entries = []

    for code in (sorted(codes.values(), key=operator.attrgetter('idx'))):
      if not code.hidden:
        self.entries.append(StaticEntryFrame(code, None, self))

    self.layout = QVBoxLayout(self)
    even = True
    for entry in self.entries:
      even = not even
      if even:
        entry.setAlternateBGColor()
      self.layout.addWidget(entry)
    self.layout.addStretch()
    self.layout.setSpacing(0)

    for entry in self.entries:
      entry.read.connect(self.read)
      entry.poke.connect(self.poke)
      self.word_read.connect(entry.onWordRead)
      entry.log.connect(self.log)

    self.setStyleSheet('CustomGeckoWidget {background-color: white}')
    self.show()
