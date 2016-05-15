from PyQt4.QtCore import QByteArray
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QComboBox
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from GearEntriesFrame import GearEntriesFrame


class GearModWidget(QWidget):
  GEAR_CLASS_NAMES = ['Ranged Weapons', 'Melee Weapons', 'Armor', 'Skell Weapons', 'Skell Armor']

  read_block = pyqtSignal(int, int) # start_addr, num_bytes
  block_read = pyqtSignal(int, int, QByteArray) # start_addr, num_bytes, raw_bytes
  poke_block = pyqtSignal(int, QByteArray, bool) # start_addr, raw_bytes, is_ascii
  set_code_offset = pyqtSignal(int) # signed_offset

  log = pyqtSignal(str, str) # msg, color

  def __init__(self, data_store, parent=None):
    super(GearModWidget, self).__init__(parent)
    self.d = data_store
    self.entries = []
    code_keys = self.d.codes.keys()

    self.entries.append('''<b>Instructions:</b>
    <ol>
    <li>in XCX, equip target gear to be modified</li>
    <li>in XCXGecko, Cache Slots for [Gear Type]</li>
    <li>in XCX, un-equip gear and hover over it in inventory</li>
    <li>in XCXGecko, Cache Slots again to automatically find target gear slot</li>
    <li>in XCXGecko, alter gear attributes as desired, then Poke</li>
    <li>in XCX, move selection cursor to different gear then back to target gear to see updated attributes</li>
    </ol>''')

    self.entries.append('''<b>Notes:</b>
    <ul>
    <li>Cache Slots can take 10+ seconds to complete</li>
    <li>setting 2nd skill to [NO SKILL] will ignore 3rd skill slot, etc...</li>
    <li>do not reduce augment count before removing augment</li>
    <li>setting invalid raw data will cause game to crash to title screen</li>
    <li>do not set combined skill level beyond 20 (XX), and only set +0 for non-leveled skills</li>
    <li>Read about gear format: <b>bit.ly/1rAxrLy</b></li>
    </ul>''')

    for class_label in GearModWidget.GEAR_CLASS_NAMES:
      # Find codes for first and last slot
      first_slot = None
      last_slot = None
      for key in self.d.codes:
        if key.find(class_label) == 0:
          cs = self.d.codes[key]
          if len(cs.c) != 1:
            self.log.emit('Expecting 1 code entry for %s, found %d' % (class_label, len(cs.c)), 'red')
          else:
            cs.hidden = True
            code = cs.c[0]
            if first_slot is None or first_slot.addr_base > code.addr_base:
              first_slot = code
            if last_slot is None or last_slot.addr_base < code.addr_base:
              last_slot = code
      if first_slot is None or last_slot is None:
        self.entries.append('<font color="red">Need 2+ codes for %s</font>' % class_label)
        continue

      # Construct ID<->name mappings
      if class_label == 'Ranged Weapons' or class_label == 'Melee Weapons' or class_label == 'Armor':
        id2skill = self.d.gear_ids['ground']
      else:
        id2skill = self.d.gear_ids['skell']
      skill2id = dict()
      for key, skill in id2skill.iteritems():
        if skill in skill2id:
          self.log.emit('Found multiple IDs for %s' % skill, 'brown')
          continue
        else:
          skill2id[skill] = key
      self.entries.append(GearEntriesFrame(first_slot.addr_base, last_slot.addr_base, class_label, skill2id, id2skill,
                                           self))

    # Set layout
    self.layout = QVBoxLayout(self)
    even = True
    for entry in self.entries:
      if entry is None:  # add horizontal divider
        hdiv = QFrame()
        hdiv.setFrameShape(QFrame.HLine)
        hdiv.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(hdiv)
      elif isinstance(entry, str):
        lbl = QLabel(entry, self)
        self.layout.addWidget(lbl)
      else:
        even = not even
        if even:
          entry.setAlternateBGColor()
        self.layout.addWidget(entry)
    self.layout.addStretch()
    self.layout.setSpacing(0)

    for entry in self.entries:
      if isinstance(entry, GearEntriesFrame):
        entry.read_block.connect(self.read_block)
        self.block_read.connect(entry.onBlockRead)
        entry.poke_block.connect(self.poke_block)
        self.set_code_offset.connect(entry.onSetCodeOffset)
        entry.log.connect(self.log)

    self.setStyleSheet('GearModWidget { background-color: white; }')
