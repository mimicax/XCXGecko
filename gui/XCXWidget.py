from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from ItemEntriesFrame import *
from StaticEntryFrame import *


class XCXWidget(QWidget):
  CHARACTERS = ['Protagonist', 'Elma', 'Lin', 'Alexa', 'Boze', 'Celica', 'Doug', 'Fyre', 'Gwin', 'H.B.', 'Hope',
                'Irina', 'L', 'Lao', 'Mia', 'Murderess', 'Nagi', 'Phog', 'Yelv']
  TRAIT_LABELS = ['Lv Exp', 'Rank Exp', 'BP', 'Affinity', 'Height', 'Chest Depth', 'Chest Height', 'Chest Width']

  read = pyqtSignal(str)  # code_label
  poke = pyqtSignal(str, int)  # code_label, new_val
  word_read = pyqtSignal(str, int)  # txt_addr, word_val
  log = pyqtSignal(str, str)  # msg, color

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
    self.entries.append('''<b>CHARACTER TRAITS:</b><ul>
    <li>for exp-related codes to take effect, win a battle</li>
    <li>for body codes to take effect, enter "Active Members" menu and "Confirm Changes"</li></ul>''')

    for char in self.CHARACTERS:
      for trait in self.TRAIT_LABELS:
        key = [key for key in code_keys if key.find('%s %s' % (char, trait)) == 0]
        if key:
          self.d.codes[key[0]].hidden = True

    self.cmb_char = QComboBox(self)
    self.cmb_char.addItems(self.CHARACTERS)
    self.entries.append(self.cmb_char)
    self.cmb_char.activated[str].connect(self.onChooseChar)

    self.wdg_char_lv_exp = StaticEntryFrame(None, 'Lv Exp', self)
    self.entries.append(self.wdg_char_lv_exp)

    self.wdg_char_rank_exp = StaticEntryFrame(None, 'Rank Exp', self)
    self.entries.append(self.wdg_char_rank_exp)

    self.wdg_char_bp = StaticEntryFrame(None, 'BP', self)
    self.entries.append(self.wdg_char_bp)

    self.wdg_char_affinity = StaticEntryFrame(None, 'Affinity', self)
    self.entries.append(self.wdg_char_affinity)

    self.wdg_char_height = StaticEntryFrame(None, 'Height (float)', self)
    self.entries.append(self.wdg_char_height)

    self.wdg_char_chest_depth = StaticEntryFrame(None, 'Chest Depth (float)', self)
    self.entries.append(self.wdg_char_chest_depth)

    self.wdg_char_chest_height = StaticEntryFrame(None, 'Chest Height (float)', self)
    self.entries.append(self.wdg_char_chest_height)

    self.wdg_char_chest_width = StaticEntryFrame(None, 'Chest Width (float)', self)
    self.entries.append(self.wdg_char_chest_width)

    self.entries.append(None)  # horizontal divider

    # Add entries for items
    self.entries.append('''<b>ITEMS:</b><br><ul>
      <li><b>DO NOT POKE item slot with 0 amount</b></li>
      <li>to see updated value, switch Item Category or exit out of menu</li>
      </ul>''')

    for type_val, type_str in self.d.item_types:
      first_slot = None
      last_slot = None
      last_slot_id = None
      slot_names = dict()
      slot_ids = dict()
      for key in self.d.codes:
        slot_idx = key.find(': Slot ')
        if key.find(type_str) == 0 and slot_idx > 0:
          code = self.d.codes[key]
          code.hidden = True
          slot = key[slot_idx + len(': Slot '):]
          bracket_idx = slot.find('[')
          if bracket_idx >= 0:
            slot = slot[:bracket_idx]
          slot = int(slot)
          if slot == 1:
            first_slot = code
          elif last_slot_id is None or last_slot_id < slot:
            last_slot_id = slot
            last_slot = code
      if first_slot is None or last_slot is None:
        self.entries.append('Missing slot 001/max codes for %s' % type_str)
      else:
        for key, item in self.d.item_ids.iteritems():
          if item.type_val == type_val:
            slot_names[item.id_val] = item.name
            slot_ids[item.name] = item.id_val
        self.entries.append(ItemEntriesFrame(type_val, first_slot.base_addr, type_str,
                                             last_slot_id, slot_names, slot_ids, self))

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
        entry.poke.connect(self.poke)
        self.word_read.connect(entry.onWordRead)
        entry.log.connect(self.log)

    self.setStyleSheet('XCXWidget { background-color: white; }')
    self.onChooseChar(self.CHARACTERS[0])
    self.show()

  @pyqtSlot(str)
  def onChooseChar(self, char):
    code_keys = self.d.codes.keys()
    key = [key for key in code_keys if key.find('%s Lv Exp' % char) == 0]
    if key:
      self.wdg_char_lv_exp.changeCode(self.d.codes[key[0]])
    else:
      self.wdg_char_lv_exp.changeCode(None)

    key = [key for key in code_keys if key.find('%s Rank Exp' % char) == 0]
    if key:
      self.wdg_char_rank_exp.changeCode(self.d.codes[key[0]])
    else:
      self.wdg_char_rank_exp.changeCode(None)

    key = [key for key in code_keys if key.find('%s BP' % char) == 0]
    if key:
      self.wdg_char_bp.changeCode(self.d.codes[key[0]])
    else:
      self.wdg_char_bp.changeCode(None)

    key = [key for key in code_keys if key.find('%s Affinity' % char) == 0]
    if key:
      self.wdg_char_affinity.changeCode(self.d.codes[key[0]])
    else:
      self.wdg_char_affinity.changeCode(None)

    key = [key for key in code_keys if key.find('%s Height' % char) == 0]
    if key:
      self.wdg_char_height.changeCode(self.d.codes[key[0]])
    else:
      self.wdg_char_height.changeCode(None)

    key = [key for key in code_keys if key.find('%s Chest Depth' % char) == 0]
    if key:
      self.wdg_char_chest_depth.changeCode(self.d.codes[key[0]])
    else:
      self.wdg_char_chest_depth.changeCode(None)

    key = [key for key in code_keys if key.find('%s Chest Height' % char) == 0]
    if key:
      self.wdg_char_chest_height.changeCode(self.d.codes[key[0]])
    else:
      self.wdg_char_chest_height.changeCode(None)

    key = [key for key in code_keys if key.find('%s Chest Width' % char) == 0]
    if key:
      self.wdg_char_chest_width.changeCode(self.d.codes[key[0]])
    else:
      self.wdg_char_chest_width.changeCode(None)
