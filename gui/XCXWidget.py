from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from ItemEntriesFrame import *
from StaticEntryFrame import *


class XCXWidget(QWidget):
  GENERAL_LABEL_NAME_PAIRS = [
    ('Funds Modifier', 'Funds'),
    ('Miranium Modifier', 'Miranium'),
    ('Reward Tickets Modifier', 'Reward Tickets'),
    ('Blade Lv Exp', 'BLADE Lv Exp')
  ]

  CHARACTERS = ['Protagonist', 'Elma', 'Lin', 'Alexa', 'Boze', 'Celica', 'Doug', 'Fyre', 'Gwin',
                'H.B.', 'Hope', 'Irina', 'L', 'Lao', 'Mia', 'Murderess', 'Nagi', 'Phog', 'Yelv']

  TRAIT_LABELS = ['Name', 'Lv Exp', 'Rank Exp', 'BP', 'Affinity', 'Height (float)',
                  'Chest Depth (float)', 'Chest Height (float)', 'Chest Width (float)']

  read_code = pyqtSignal(str, int) # code_set_label, code_id
  code_read = pyqtSignal(str, int, QByteArray) # code_set_label, code_id, raw_bytes
  poke_code = pyqtSignal(str, int, QByteArray) # code_set_label, code_id, new_bytes

  read_block = pyqtSignal(int, int) # start_addr, num_bytes
  block_read = pyqtSignal(int, int, QByteArray) # start_addr, num_bytes, raw_bytes
  poke_block = pyqtSignal(int, QByteArray, bool) # start_addr, raw_bytes, is_ascii

  log = pyqtSignal(str, str) # msg, color

  def __init__(self, data_store, parent=None):
    super(XCXWidget, self).__init__(parent)
    self.d = data_store
    self.entries = []
    code_keys = self.d.codes.keys()

    # Add general code entries
    self.entries.append('<b>GENERAL</b>')

    for code_label, wdg_name in XCXWidget.GENERAL_LABEL_NAME_PAIRS:
      code = None
      key = [key for key in code_keys if key.find(code_label) == 0]
      if key:
        cs = self.d.codes[key[0]]
        if len(cs.c) != 1:
          self.log.emit('Expecting 1 code entry for %s, found %d' % (code_label, len(cs.c)), 'red')
        else:
          cs.hidden = True
          code = cs.c[0]
      self.entries.append(StaticEntryFrame(code, wdg_name, self))

    self.entries.append(None)  # horizontal divider

    # Add entries for character traits
    self.entries.append('''<b>CHARACTER TRAITS:</b>
    <ul>
    <li>for exp-related codes to take effect, win a battle</li>
    <li>for body codes to take effect, enter "Active Members" menu and "Confirm Changes"</li>
    </ul>''')

    for char in XCXWidget.CHARACTERS:
      for trait in XCXWidget.TRAIT_LABELS:
        code_label = '%s %s' % (char, trait)
        key = [key for key in code_keys if key.find(code_label) == 0]
        if key:
          cs = self.d.codes[key[0]]
          if len(cs.c) != 1:
            self.log.emit('Expecting 1 code entry for %s, found %d' % (code_label, len(cs.c)), 'red')
          else:
            cs.hidden = True

    self.cmb_char = QComboBox(self)
    self.cmb_char.addItems(XCXWidget.CHARACTERS)
    self.entries.append(self.cmb_char)
    self.cmb_char.activated[str].connect(self.onChooseChar)

    self.wdg_char_traits = dict()
    for trait in XCXWidget.TRAIT_LABELS:
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
          cs = self.d.codes[key]
          if len(cs.c) != 1:
            self.log.emit('Expecting 1 code entry for %s, found %d' % (type_str, len(cs.c)), 'red')
          else:
            cs.hidden = True
            code = cs.c[0]
            if first_slot is None or first_slot.addr_base > code.addr_base:
              first_slot = code
            if last_slot is None or last_slot.addr_base < code.addr_base:
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
      self.entries.append(ItemEntriesFrame(type_val, first_slot.addr_base, last_slot.addr_base,
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
      if isinstance(entry, StaticEntryFrame):
        entry.read_code.connect(self.read_code)
        self.code_read.connect(entry.onCodeRead)
        entry.poke_code.connect(self.poke_code)
        entry.log.connect(self.log)
      elif isinstance(entry, ItemEntriesFrame):
        entry.read_block.connect(self.read_block)
        self.block_read.connect(entry.onBlockRead)
        entry.poke_block.connect(self.poke_block)
        entry.log.connect(self.log)

    self.setStyleSheet('XCXWidget { background-color: white; }')
    self.onChooseChar(self.CHARACTERS[0])

  @pyqtSlot(str)
  def onChooseChar(self, char):
    code_keys = self.d.codes.keys()

    for trait in self.TRAIT_LABELS:
      new_code = None
      key = [key for key in code_keys if key.find('%s %s' % (char, trait)) == 0]
      if key:
        cs = self.d.codes[key[0]]
        if len(cs.c) > 0:
          new_code = cs.c[0]
      self.wdg_char_traits[trait].changeCode(new_code)
