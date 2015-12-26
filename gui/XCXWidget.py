from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from ItemEntriesFrame import *
from StaticEntryFrame import *


class XCXWidget(QWidget):
  CHARACTERS = ['Protagonist', 'Elma', 'Lin', 'Alexa', 'Boze', 'Celica', 'Doug', 'Fyre', 'Gwin',
                'H.B.', 'Hope', 'Irina', 'L', 'Lao', 'Mia', 'Murderess', 'Nagi', 'Phog', 'Yelv']
  TRAIT_LABELS = ['Name', 'Lv Exp', 'Rank Exp', 'BP', 'Affinity', 'Height (float)',
                  'Chest Depth (float)', 'Chest Height (float)', 'Chest Width (float)']

  read = pyqtSignal(str) # code_label
  word_read = pyqtSignal(str, int) # txt_addr, word_val
  poke = pyqtSignal(str, int) # code_label, new_val
  readmem = pyqtSignal(int, int) # start_addr, num_bytes
  block_read = pyqtSignal(int, int, QByteArray) # start_addr, num_bytes, raw_bytes
  writestr = pyqtSignal(int, QByteArray) # start_addr, ascii_bytes
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, data_store, parent=None):
    super(XCXWidget, self).__init__(parent)
    self.d = data_store
    self.entries = []

    # Add entries for funds, miranimum, tickets, BLADE lv
    self.entries.append('<b>GENERAL</b>')

    code_keys = self.d.codes.keys()

    code = None
    key = [key for key in code_keys if key.find('Funds Modifier') == 0]
    if key:
      code = self.d.codes[key[0]]
      code.hidden = True
    self.entries.append(StaticEntryFrame(code, 'Funds', self))

    code = None
    key = [key for key in code_keys if key.find('Miranium Modifier') == 0]
    if key:
      code = self.d.codes[key[0]]
      code.hidden = True
    self.entries.append(StaticEntryFrame(code, 'Miranium', self))

    code = None
    key = [key for key in code_keys if key.find('Reward Tickets Modifier') == 0]
    if key:
      code = self.d.codes[key[0]]
      code.hidden = True
    self.entries.append(StaticEntryFrame(code, 'Reward Tickets', self))

    code = None
    key = [key for key in code_keys if key.find('Blade Lv Exp') == 0]
    if key:
      code = self.d.codes[key[0]]
      code.hidden = True
    self.entries.append(StaticEntryFrame(code, 'BLADE Lv Exp', self))

    self.entries.append(None)  # horizontal divider

    # Add entries for character traits
    self.entries.append('''<b>CHARACTER TRAITS:</b>
    <ul>
    <li>for exp-related codes to take effect, win a battle</li>
    <li>for body codes to take effect, enter "Active Members" menu and "Confirm Changes"</li>
    </ul>''')

    for char in self.CHARACTERS:
      for trait in self.TRAIT_LABELS:
        key = [key for key in code_keys if key.find('%s %s' % (char, trait)) == 0]
        if key:
          self.d.codes[key[0]].hidden = True

    self.cmb_char = QComboBox(self)
    self.cmb_char.addItems(self.CHARACTERS)
    self.entries.append(self.cmb_char)
    self.cmb_char.activated[str].connect(self.onChooseChar)

    self.wdg_char_traits = dict()
    for trait in self.TRAIT_LABELS:
      self.wdg_char_traits[trait] = StaticEntryFrame(None, trait, self)
      self.entries.append(self.wdg_char_traits[trait])

    self.entries.append(None)  # horizontal divider

    # Add entries for items
    self.entries.append('''<b>ITEMS:</b>
    <ul>
    <li>poking invalid ID will crash back to title screen</li>
    <li>poking duplicate items may cause glitches; use Search ID instead</li>
    <li>to see updated value, switch Item Category or exit out of menu</li>
    </ul>''')

    for type_val, type_str in self.d.item_types:
      # Find codes for first and last slot
      first_slot = None
      last_slot = None
      for key in self.d.codes:
        if key.find(type_str) == 0:
          code = self.d.codes[key]
          code.hidden = True
          if first_slot is None or first_slot.base_addr > code.base_addr:
            first_slot = code
          if last_slot is None or last_slot.base_addr < code.base_addr:
            last_slot = code
      if first_slot is None or last_slot is None:
        self.entries.append('Need 2+ codes for %s type' % type_str)
        continue

      # Construct ID<->name mappings
      slot_id2name = dict()
      slot_idx2id = []
      slot_names = []
      for key, item in self.d.item_ids.iteritems():
        if item.type_val == type_val:
          if item.id_val in slot_id2name:
            self.log.emit('Found multiple names for %s %03X' % (type_str, item.id_val), 'brown')
            continue
          slot_id2name[item.id_val] = item.name
          slot_idx2id.append((item.name, '%03X' % item.id_val))
      if len(slot_idx2id) > 0:
        slot_idx2id.sort(key=lambda t: t[0])
        (slot_names, slot_idx2id) = zip(*slot_idx2id)
      self.entries.append(ItemEntriesFrame(type_val, first_slot.base_addr, last_slot.base_addr,
                                           type_str, slot_id2name, slot_idx2id, slot_names, self))

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
      if isinstance(entry, StaticEntryFrame) or isinstance(entry, ItemEntriesFrame):
        entry.read.connect(self.read)
        self.word_read.connect(entry.onWordRead)
        entry.poke.connect(self.poke)
        entry.readmem.connect(self.readmem)
        self.block_read.connect(entry.onBlockRead)
        entry.writestr.connect(self.writestr)
        entry.log.connect(self.log)

    self.setStyleSheet('XCXWidget { background-color: white; }')
    self.onChooseChar(self.CHARACTERS[0])
    self.show()

  @pyqtSlot(str)
  def onChooseChar(self, char):
    code_keys = self.d.codes.keys()

    for trait in self.TRAIT_LABELS:
      key = [key for key in code_keys if key.find('%s %s' % (char, trait)) == 0]
      if key:
        self.wdg_char_traits[trait].changeCode(self.d.codes[key[0]])
      else:
        self.wdg_char_traits[trait].changeCode(None)
