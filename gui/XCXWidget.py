from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from StaticEntryFrame import *


class XCXWidget(QWidget):
  read = pyqtSignal(str) # code_label
  poke = pyqtSignal(str, int) # code_label, new_val
  word_read = pyqtSignal(str, int) # txt_addr, word_val
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, codes, parent=None):
    super(XCXWidget, self).__init__(parent)
    self.codes = codes
    self.entries = []

    code_keys = codes.keys()
    key = [key for key in code_keys if key.find('Funds Modifier') == 0]
    if key:
      code = codes[key[0]]
      code.hidden = True
      self.entries.append(StaticEntryFrame(code, 'Funds', self))

    key = [key for key in code_keys if key.find('Miranium Modifier') == 0]
    if key:
      code = codes[key[0]]
      code.hidden = True
      self.entries.append(StaticEntryFrame(code, 'Miranium', self))

    key = [key for key in code_keys if key.find('Reward Tickets Modifier') == 0]
    if key:
      code = codes[key[0]]
      code.hidden = True
      self.entries.append(StaticEntryFrame(code, 'Reward Tickets', self))

    self.entries.append(None) # horizontal divider

    hdiv = QFrame()
    hdiv.setFrameShape(QFrame.HLine)
    hdiv.setFrameShadow(QFrame.Sunken)

    self.layout = QVBoxLayout(self)
    even = True
    for entry in self.entries:
      even = not even
      if entry is None: # add horizontal divider
        self.layout.addWidget(hdiv)
      else:
        if even:
          entry.setAlternateBGColor()
        self.layout.addWidget(entry)
    self.layout.addStretch()
    self.layout.setSpacing(0)

    for entry in self.entries:
      if entry is not None:
        entry.read.connect(self.read)
        entry.poke.connect(self.poke)
        self.word_read.connect(entry.onWordRead)
        entry.log.connect(self.log)

    self.show()
