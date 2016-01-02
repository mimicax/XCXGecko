import struct

from PyQt4.QtCore import QByteArray
from PyQt4.QtCore import QSize
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QComboBox
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPushButton

from FixItemNameDialog import FixItemNameDialog


class ItemEntriesFrame(QFrame):
  read_block = pyqtSignal(int, int) # start_addr, num_bytes
  poke_block = pyqtSignal(int, QByteArray, bool) # start_addr, raw_bytes, is_ascii
  log = pyqtSignal(str, str) # msg, color

  MISSING_ITEM_NAME = '[NOT IN DB]'

  def __init__(self, type_val, addr_start, addr_end, label, id2name, idx2id, names, parent=None):
    super(ItemEntriesFrame, self).__init__(parent)
    self.type_val = type_val
    self.addr_start = addr_start
    self.addr_end = addr_end
    self.max_num_slots = (addr_end - addr_start)/3/4 + 1
    self.label = label
    self.id2name = id2name
    self.idx2id = idx2id
    self.names = names

    self.slots_cache = [] # tuple: (addr_hex, addr_val, slot_number, cur_val)
    self.cur_slot_idx = -1

    self.lbl_label = QLabel(self.label, self)

    self.btn_read_slots = QPushButton(' Cache Slots', self)
    self.btn_read_slots.setIcon(QIcon('img/flaticon/data110.png'))
    self.btn_read_slots.setStyleSheet('background-color: white')
    self.btn_read_slots.clicked.connect(self.onReadSlots)

    self.btn_search_cache = QPushButton(' Search ID', self)
    self.btn_search_cache.setIcon(QIcon('img/flaticon/magnifier13.png'))
    self.btn_search_cache.setToolTip('Find slot in cache with specified item ID')
    self.btn_search_cache.setStyleSheet('background-color: white')
    self.btn_search_cache.clicked.connect(self.onSearchCacheForID)

    self.btn_read = QPushButton(self)
    self.btn_read.setIcon(QIcon('img/flaticon/open135.png'))
    self.btn_read.setToolTip('Read item slot value from memory')
    self.btn_read.setStyleSheet('background-color: white')
    self.btn_read.clicked.connect(self.onReadSlot)

    self.cmb_slots = QComboBox(self)
    self.cmb_slots.setToolTip('')
    self.cmb_slots.setStyleSheet('background-color: white')
    self.cmb_slots.currentIndexChanged[int].connect(self.onChangeSlot)
    self.cmb_slots.setDisabled(True)

    self.cmb_names = QComboBox(self)
    self.cmb_names.setEditable(True)
    self.cmb_names.addItems(self.names)
    self.cmb_names.lineEdit().setText(ItemEntriesFrame.MISSING_ITEM_NAME)
    self.cmb_names.currentIndexChanged[int].connect(self.fetchID)

    self.txt_id = QLineEdit(self)
    self.txt_id.setPlaceholderText('ID (hex)')
    self.txt_id.setMaxLength(3)
    self.txt_id.textChanged.connect(self.fetchName)

    self.btn_rename = QPushButton(' Fix Name', self)
    self.btn_rename.setIcon(QIcon('img/flaticon/cloud-storage3.png'))
    self.btn_rename.setToolTip('Add/Correct Item Name for %s (type: %02X)' % (self.label, type_val))
    self.btn_rename.setStyleSheet('background-color: white')
    self.btn_rename.clicked.connect(self.onRename)

    self.txt_amount = QLineEdit(self)
    self.txt_amount.setPlaceholderText('Amount')
    self.txt_amount.setMaxLength(3)

    self.btn_poke = QPushButton(self)
    self.btn_poke.setIcon(QIcon('img/flaticon/draw39.png'))
    self.btn_poke.setToolTip('Poke new value for item slot')
    self.btn_poke.setStyleSheet('background-color: white')
    self.btn_poke.clicked.connect(self.onPokeSlot)

    self.layout = QGridLayout(self)
    self.layout.addWidget(self.lbl_label, 0, 0)
    self.layout.addWidget(self.btn_read_slots, 0, 1)
    self.layout.addWidget(self.btn_search_cache, 0, 2)
    self.layout.addWidget(self.cmb_slots, 0, 3)
    self.layout.addWidget(self.btn_read, 0, 4)
    self.layout.addWidget(self.cmb_names, 1, 0)
    self.layout.addWidget(self.txt_id, 1, 1)
    self.layout.addWidget(self.btn_rename, 1, 2)
    self.layout.addWidget(self.txt_amount, 1, 3)
    self.layout.addWidget(self.btn_poke, 1, 4)

    self.layout.setColumnStretch(0, 7)
    self.layout.setColumnStretch(1, 3)
    self.layout.setColumnStretch(2, 3)
    self.layout.setColumnStretch(3, 3)
    self.layout.setColumnStretch(4, 1)
    self.layout.setContentsMargins(0, 2, 0, 2)

    icon_height = self.lbl_label.height()*8/15
    icon_size = QSize(icon_height, icon_height)
    self.btn_read_slots.setIconSize(icon_size)
    self.btn_search_cache.setIconSize(icon_size)
    self.btn_rename.setIconSize(icon_size)
    self.btn_read.setIconSize(icon_size)
    self.btn_poke.setIconSize(icon_size)
    btn_size = QSize(icon_height*1.5, icon_height*1.5)
    self.btn_read.setFixedSize(btn_size)
    self.btn_poke.setFixedSize(btn_size)

    self.updateUI()

  def updateUI(self):
    # Disable editing if cache missing
    if not (0 <= self.cur_slot_idx < len(self.slots_cache)):
      self.cmb_names.lineEdit().setText(ItemEntriesFrame.MISSING_ITEM_NAME)
      self.cmb_names.setDisabled(True)
      self.txt_id.setText('')
      self.txt_id.setDisabled(True)
      return

    # Validate current value
    cur_val = self.slots_cache[self.cur_slot_idx][3]
    (type_val, id_val, amount) = parse_item_word(cur_val)
    if type_val != self.type_val and type_val != 0:
      self.log.emit('Coding error: val(%s)=%08X, type (%02X) != expected (%02X)' %
                    (self.cur_addr_str, cur_val, type_val, self.type_val), 'red')
      return

    # Update UI
    self.txt_id.setDisabled(False)
    self.txt_id.setText('%03X' % id_val)
    self.cmb_names.setDisabled(False)
    self.fetchName()
    self.txt_amount.setText(str(amount))

  def setAlternateBGColor(self):
    self.setStyleSheet('ItemEntriesFrame { background-color:rgb(248,248,248) }')

  @pyqtSlot()
  def onRename(self):
    id_txt = str(self.txt_id.text())
    if len(id_txt) != 3:
      return
    dialog = FixItemNameDialog('%02X' % self.type_val, id_txt, self)
    dialog.log.connect(self.log)
    dialog.exec_()

  @pyqtSlot()
  def onReadSlots(self):
    self.read_block.emit(self.addr_start, self.max_num_slots*4*3)

  @pyqtSlot(int, int, QByteArray)
  def onBlockRead(self, addr_start, num_bytes, raw_bytes):
    # Determine whether block has cache or single slot
    if addr_start == self.addr_start and num_bytes == self.max_num_slots*4*3:
      self.onCacheRead(addr_start, num_bytes, raw_bytes)
    elif num_bytes == 4: # Assume read slot
      # Ignore if no cache
      if not (0 <= self.cur_slot_idx < len(self.slots_cache)):
        return
      self.onSlotRead(addr_start, raw_bytes)

  def onCacheRead(self, addr_start, num_bytes, raw_bytes):
    slot_bytes = str(raw_bytes)
    self.slots_cache = []
    slots_txt = []
    for slot_i in xrange(self.max_num_slots):
      byte_offset = slot_i*3*4
      cur_slot_bytes = slot_bytes[byte_offset:(byte_offset+4)]
      if len(cur_slot_bytes) != 4:
        continue
      cur_slot_val = struct.unpack('>I', cur_slot_bytes)[0]
      (type_val, id_val, amount) = parse_item_word(cur_slot_val)
      if type_val == 0 or amount == 0:
        continue
      elif type_val != self.type_val:
        self.log.emit('val(%08X)=%08X, type_val(%02X) unexpected(%02X)' %
                      (addr_start+byte_offset, cur_slot_val, type_val, self.type_val),
                      'red')
        continue
      else:
        addr_val = addr_start + byte_offset
        addr_hex = '%08X' % addr_val
        slot_number = slot_i+1
        self.slots_cache.append((addr_hex, addr_val, slot_number, cur_slot_val))
        slots_txt.append('Slot %03d' % slot_number)

    # Update UI
    self.log.emit('Found %d %s slots in memory' % (len(self.slots_cache), self.label), 'black')
    self.cmb_slots.clear()
    if len(self.slots_cache) <= 0:
      self.cmb_slots.setDisabled(True)
      self.cur_slot_idx = -1
    else:
      self.cmb_slots.setDisabled(False)
      self.cmb_slots.addItems(slots_txt)
      self.cur_slot_idx = 0
    self.updateUI()

  def onSlotRead(self, addr_word, raw_bytes):
    addr_cur_slot = self.slots_cache[self.cur_slot_idx][1]
    if addr_word == addr_cur_slot:
      cur_cache = self.slots_cache[self.cur_slot_idx]
      new_val = struct.unpack('>I', str(raw_bytes))[0]
      new_cache = (cur_cache[0], cur_cache[1], cur_cache[2], new_val)
      self.slots_cache[self.cur_slot_idx] = new_cache
      self.updateUI()
    else: # Update cached value of other slots
      addr_first_slot = self.slots_cache[0][1]
      addr_last_slot = self.slots_cache[-1][1]
      if (addr_first_slot <= addr_word <= addr_last_slot) and \
         ((addr_word - addr_first_slot) % 12 == 0):
        for slot_i in xrange(len(self.slots_cache)):
          addr_cur_slot = self.slots_cache[slot_i][1]
          if addr_word == addr_cur_slot:
            cur_cache = self.slots_cache[slot_i]
            new_val = struct.unpack('>I', str(raw_bytes))[0]
            new_cache = (cur_cache[0], cur_cache[1], cur_cache[2], new_val)
            self.slots_cache[slot_i] = new_cache
            return

  @pyqtSlot()
  def onSearchCacheForID(self):
    # Stop if no cache
    if not (0 <= self.cur_slot_idx < len(self.slots_cache)):
      self.log.emit('Must cache slots before searching', 'red')
      return

    # Fetch and validate target ID
    target_id_val = None
    try:
      target_id_val = int(str(self.txt_id.text()), 16)
      if target_id_val < 0 or target_id_val > Item.MAX_ID_VAL:
        self.log.emit('Item ID out of [0, 0x%03X] range' % Item.MAX_ID_VAL)
        return
    except ValueError, e:
      self.log.emit('Failed to parse item ID, expecting XXX', 'red')
      return

    # Search ID in cache
    for cand_slot_idx in xrange(len(self.slots_cache)):
      (type_val, id_val, amount) = parse_item_word(self.slots_cache[cand_slot_idx][3])
      if id_val == target_id_val and type_val == self.type_val:
        self.cur_slot_idx = cand_slot_idx
        self.cmb_slots.setCurrentIndex(self.cur_slot_idx)
        self.updateUI()
        return
    self.log.emit('Did not find ID=%03X in %d cached %s slots' %
                  (target_id_val, self.label, len(self.slots_cache)), 'red')

  @pyqtSlot(int)
  def onChangeSlot(self, new_slot_idx):
    # Validate new_slot_idx
    if not (0 <= new_slot_idx < len(self.slots_cache)):
      return

    # Update slot idx and read value from memory
    self.cur_slot_idx = new_slot_idx
    cur_addr_hex = self.slots_cache[self.cur_slot_idx][0]
    self.cmb_slots.setToolTip(cur_addr_hex)
    self.cmb_names.lineEdit().setText(ItemEntriesFrame.MISSING_ITEM_NAME)
    self.cmb_names.setDisabled(True)
    self.txt_id.setText('')
    self.txt_id.setDisabled(True)
    self.onReadSlot()

  @pyqtSlot()
  def fetchName(self):
    try:
      id_val = int(str(self.txt_id.text()), 16)
    except ValueError, e:
      return
    name = self.MISSING_ITEM_NAME
    if id_val in self.id2name:
      name = self.id2name[id_val]
    self.cmb_names.lineEdit().setText(name)

  @pyqtSlot(int)
  def fetchID(self, cmb_idx):
    if cmb_idx < 0 or cmb_idx >= len(self.idx2id):
      self.txt_id.setText('')
    else:
      self.txt_id.setText(self.idx2id[cmb_idx])

  @pyqtSlot()
  def onReadSlot(self):
    try:
      if not (0 <= self.cur_slot_idx < len(self.slots_cache)):
        raise ValueError('must cache slots before poking')
      addr_cur_slot = self.slots_cache[self.cur_slot_idx][1]
      self.read_block.emit(addr_cur_slot, 4)
    except ValueError, e:
      cur_slot_num = self.slots_cache[self.cur_slot_idx][2]
      self.log.emit('READ %s Slot %03d failed: %s' % (self.label, cur_slot_num, str(e)), 'red')
    except BaseException, e:
      cur_slot_num = self.slots_cache[self.cur_slot_idx][2]
      self.log.emit('READ %s Slot %03d failed: %s' % (self.label, cur_slot_num, str(e)), 'red')
      traceback.print_exc()

  @pyqtSlot()
  def onPokeSlot(self):
    try:
      if not (0 <= self.cur_slot_idx < len(self.slots_cache)):
        raise ValueError('must cache slots before poking')

      addr_cur_slot = self.slots_cache[self.cur_slot_idx][1]
      cur_val = self.slots_cache[self.cur_slot_idx][3]
      (type_val, id_val, cur_amount) = parse_item_word(cur_val)
      if self.type_val == 0 or cur_amount == 0:
        raise ValueError('cannot poke empty item slot')

      id_txt = str(self.txt_id.text())
      if len(id_txt) <= 0:
        raise ValueError('item ID not specified')

      id_val = int(id_txt, 16)
      if id_val < 0 or id_val > Item.MAX_ID_VAL:
        raise ValueError('item ID not in [0x000, 0x%03X] range' % Item.MAX_ID_VAL)

      amount_txt = str(self.txt_amount.text())
      if len(amount_txt) <= 0:
        raise ValueError('amount not specified')

      new_amount = int(amount_txt)
      if new_amount <= 0 or new_amount > 0xFF:
        raise ValueError('item amount not in [1, 255] range')

      val_word = form_item_word(self.type_val, id_val, new_amount)
      raw_bytes = struct.pack('>I', val_word)
      self.poke_block.emit(addr_cur_slot, QByteArray(raw_bytes), False)
      self.read_block.emit(addr_cur_slot, 4)

    except ValueError, e:
      cur_slot_num = self.slots_cache[self.cur_slot_idx][2]
      self.log.emit('POKE %s Slot %03d failed: %s' % (self.label, cur_slot_num, str(e)), 'red')
    except BaseException, e:
      cur_slot_num = self.slots_cache[self.cur_slot_idx][2]
      self.log.emit('POKE %s Slot %03d failed: %s' % (self.label, cur_slot_num, str(e)), 'red')
      traceback.print_exc()
