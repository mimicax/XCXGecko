from PyQt4.QtGui import QComboBox

from StaticEntryFrame import *


class ComboEntriesFrame(StaticEntryFrame):
  def __init__(self, codes, label=None, parent=None):
    keys = sorted(codes.keys())
    dft_code = None
    if codes is not None:
      dft_code = codes[keys[0]]
    super(ComboEntriesFrame, self).__init__(dft_code, label, parent)
    self.codes = codes
    
    self.cmb_entries = QComboBox(self)
    self.cmb_entries.addItems(keys)
    self.cmb_entries.activated[str].connect(self.onChooseEntry)
    
    self.layout.insertWidget(1, self.cmb_entries)

  @pyqtSlot(str)
  def onChooseEntry(self, entry):
    self.changeCode(self.codes[str(entry)])
    self.read.emit(self.code.label)
