import struct
import traceback

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

from gear_utils import form_gear_bytes
from gear_utils import parse_gear_bytes
from gear_utils import is_gear_empty


class GearEntriesFrame(QFrame):
  read_block = pyqtSignal(int, int)  # start_addr, num_bytes
  poke_block = pyqtSignal(int, QByteArray, bool)  # start_addr, raw_bytes, is_ascii
  log = pyqtSignal(str, str)  # msg, color

  MISSING_SKILL_NAME = '[NOT IN DB]'

  def __init__(self, addr_start, addr_end, class_label, skill2id, id2skill, parent=None):
    super(GearEntriesFrame, self).__init__(parent)
    self.code_offset = 0
    self.addr_start = addr_start
    self.addr_end = addr_end
    self.max_num_slots = (addr_end - addr_start) / 6 / 4 + 1
    self.class_label = class_label
    self.skill2id = skill2id
    self.id2skill = id2skill

    self.skill_names = self.skill2id.keys()
    self.skill_names.sort()

    self.slots_cache = []  # list of raw 6*4 bytes
    self.slots_txt = None
    self.cur_slot_idx = -1
    self.cur_slot_bytes = None

    self.lbl_label = QLabel(self.class_label, self)

    self.btn_read_slots = QPushButton(' Cache Slots', self)
    self.btn_read_slots.setIcon(QIcon('img/flaticon/data110.png'))
    self.btn_read_slots.setStyleSheet('background-color: white')
    self.btn_read_slots.clicked.connect(self.onReadSlots)

    self.cmb_slots = QComboBox(self)
    self.cmb_slots.setStyleSheet('background-color: white')
    self.cmb_slots.currentIndexChanged[str].connect(self.onChangeSlot)
    self.cmb_slots.setDisabled(True)

    self.btn_read = QPushButton(self)
    self.btn_read.setIcon(QIcon('img/flaticon/open135.png'))
    self.btn_read.setToolTip('Read item slot value from memory')
    self.btn_read.setStyleSheet('background-color: white')
    self.btn_read.clicked.connect(self.onReadSlot)

    self.txt_raw = QLineEdit(self)
    self.txt_raw.setPlaceholderText('Raw hex data')
    self.txt_raw.setMaxLength(8 * 6 + 5)
    self.txt_raw.editingFinished.connect(self.onChangeRaw)

    self.btn_poke = QPushButton(self)
    self.btn_poke.setIcon(QIcon('img/flaticon/draw39.png'))
    self.btn_poke.setToolTip('Poke new value for item slot')
    self.btn_poke.setStyleSheet('background-color: white')
    self.btn_poke.clicked.connect(self.onPokeSlot)

    self.cmb_skills_a = QComboBox(self)
    self.cmb_skills_a.setEditable(True)
    self.cmb_skills_a.addItems(self.skill_names)
    self.cmb_skills_a.lineEdit().setText(GearEntriesFrame.MISSING_SKILL_NAME)
    self.cmb_skills_a.currentIndexChanged[str].connect(self.onChangeSkillA)

    self.cmb_skills_b = QComboBox(self)
    self.cmb_skills_b.setEditable(True)
    self.cmb_skills_b.addItems(self.skill_names)
    self.cmb_skills_b.lineEdit().setText(GearEntriesFrame.MISSING_SKILL_NAME)
    self.cmb_skills_b.currentIndexChanged[str].connect(self.onChangeSkillB)

    self.cmb_skills_c = QComboBox(self)
    self.cmb_skills_c.setEditable(True)
    self.cmb_skills_c.addItems(self.skill_names)
    self.cmb_skills_c.lineEdit().setText(GearEntriesFrame.MISSING_SKILL_NAME)
    self.cmb_skills_c.currentIndexChanged[str].connect(self.onChangeSkillC)

    incr_labels = []
    for incr in xrange(16):
      incr_labels.append('+%d' % incr)

    self.cmb_incr_a = QComboBox(self)
    self.cmb_incr_a.addItems(incr_labels)
    self.cmb_incr_a.currentIndexChanged[int].connect(self.onChangeIncrA)

    self.cmb_incr_b = QComboBox(self)
    self.cmb_incr_b.addItems(incr_labels)
    self.cmb_incr_b.currentIndexChanged[int].connect(self.onChangeIncrB)

    self.cmb_incr_c = QComboBox(self)
    self.cmb_incr_c.addItems(incr_labels)
    self.cmb_incr_c.currentIndexChanged[int].connect(self.onChangeIncrC)

    slot_labels = []
    for incr in xrange(4):
      slot_labels.append('%d Augment Slots' % incr)

    self.cmb_augments = QComboBox(self)
    self.cmb_augments.addItems(slot_labels)
    self.cmb_augments.currentIndexChanged[int].connect(self.onChangeAugments)

    self.layout = QGridLayout(self)
    self.layout.addWidget(self.lbl_label, 0, 0)
    self.layout.addWidget(self.btn_read_slots, 0, 1)
    self.layout.addWidget(self.cmb_slots, 0, 2)
    self.layout.addWidget(self.btn_read, 0, 3)
    self.layout.addWidget(self.txt_raw, 1, 0, 1, 3)
    self.layout.addWidget(self.btn_poke, 1, 3)
    self.layout.addWidget(self.cmb_skills_a, 2, 0)
    self.layout.addWidget(self.cmb_incr_a, 2, 1)
    self.layout.addWidget(self.cmb_skills_b, 3, 0)
    self.layout.addWidget(self.cmb_incr_b, 3, 1)
    self.layout.addWidget(self.cmb_skills_c, 4, 0)
    self.layout.addWidget(self.cmb_incr_c, 4, 1)
    self.layout.addWidget(self.cmb_augments, 2, 2)

    self.layout.setColumnStretch(0, 7)
    self.layout.setColumnStretch(1, 3)
    self.layout.setColumnStretch(2, 3)
    self.layout.setColumnStretch(3, 1)
    self.layout.setContentsMargins(0, 2, 0, 2)

    icon_height = self.lbl_label.height() * 8 / 15
    icon_size = QSize(icon_height, icon_height)
    self.btn_read_slots.setIconSize(icon_size)
    self.btn_read.setIconSize(icon_size)
    self.btn_poke.setIconSize(icon_size)
    btn_size = QSize(icon_height * 1.5, icon_height * 1.5)
    self.btn_read.setFixedSize(btn_size)
    self.btn_poke.setFixedSize(btn_size)

    self.updateUI()

  def updateUI(self):
    # Disable editing if cache missing
    if not (0 <= self.cur_slot_idx < len(self.slots_cache)) or self.cur_slot_bytes is None:
      self.cur_slot_idx = -1
      self.cur_slot_bytes = None
      self.cmb_slots.setDisabled(True)
      self.cmb_skills_a.setDisabled(True)
      self.cmb_skills_b.setDisabled(True)
      self.cmb_skills_c.setDisabled(True)
      self.cmb_incr_a.setDisabled(True)
      self.cmb_incr_b.setDisabled(True)
      self.cmb_incr_c.setDisabled(True)
      self.cmb_augments.setDisabled(True)
      self.txt_raw.setDisabled(True)
      return
    else:
      self.cmb_slots.setDisabled(False)
      self.cmb_skills_a.setDisabled(False)
      self.cmb_skills_b.setDisabled(False)
      self.cmb_skills_c.setDisabled(False)
      self.cmb_incr_a.setDisabled(False)
      self.cmb_incr_b.setDisabled(False)
      self.cmb_incr_c.setDisabled(False)
      self.cmb_augments.setDisabled(False)
      self.txt_raw.setDisabled(False)

    # Validate current slot's raw bytes
    try:
      (gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
       skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id) = parse_gear_bytes(self.cur_slot_bytes)
      cur_slot_words = struct.unpack('>IIIIII', self.cur_slot_bytes)
      num_augments = (augment_a_id != 0xFFFF) + (augment_b_id != 0xFFFF) + (augment_c_id != 0xFFFF)
    except ValueError, e:
      self.log.emit('Gear parsing failed: %s' % e.what(), 'red')
      return

    # Update UI
    self.txt_raw.setDisabled(False)
    self.txt_raw.editingFinished.disconnect()
    self.txt_raw.setText('%08X %08X %08X %08X %08X %08X' % cur_slot_words)
    self.txt_raw.editingFinished.connect(self.onChangeRaw)

    self.cmb_skills_a.setDisabled(False)
    self.cmb_skills_a.currentIndexChanged[str].disconnect()
    try:
      skill_name = self.id2skill[skill_a_id]
      skill_idx = self.skill_names.index(skill_name)
      self.cmb_skills_a.setCurrentIndex(skill_idx)
    except (KeyError, ValueError):
      self.cmb_skills_a.lineEdit().setText(GearEntriesFrame.MISSING_SKILL_NAME)
    self.cmb_skills_a.currentIndexChanged[str].connect(self.onChangeSkillA)

    self.cmb_skills_b.setDisabled(False)
    self.cmb_skills_b.currentIndexChanged[str].disconnect()
    try:
      skill_name = self.id2skill[skill_b_id]
      skill_idx = self.skill_names.index(skill_name)
      self.cmb_skills_b.setCurrentIndex(skill_idx)
    except (KeyError, ValueError):
      self.cmb_skills_b.lineEdit().setText(GearEntriesFrame.MISSING_SKILL_NAME)
    self.cmb_skills_b.currentIndexChanged[str].connect(self.onChangeSkillB)

    self.cmb_skills_c.setDisabled(False)
    self.cmb_skills_c.currentIndexChanged[str].disconnect()
    try:
      skill_name = self.id2skill[skill_c_id]
      skill_idx = self.skill_names.index(skill_name)
      self.cmb_skills_c.setCurrentIndex(skill_idx)
    except (KeyError, ValueError):
      self.cmb_skills_c.lineEdit().setText(GearEntriesFrame.MISSING_SKILL_NAME)
    self.cmb_skills_c.currentIndexChanged[str].connect(self.onChangeSkillC)

    self.cmb_incr_a.setDisabled(False)
    self.cmb_incr_a.currentIndexChanged[int].disconnect()
    self.cmb_incr_a.setCurrentIndex(skill_a_incr)
    self.cmb_incr_a.currentIndexChanged[int].connect(self.onChangeIncrA)

    self.cmb_incr_b.setDisabled(False)
    self.cmb_incr_b.currentIndexChanged[int].disconnect()
    self.cmb_incr_b.setCurrentIndex(skill_b_incr)
    self.cmb_incr_b.currentIndexChanged[int].connect(self.onChangeIncrB)

    self.cmb_incr_c.setDisabled(False)
    self.cmb_incr_c.currentIndexChanged[int].disconnect()
    self.cmb_incr_c.setCurrentIndex(skill_c_incr)
    self.cmb_incr_c.currentIndexChanged[int].connect(self.onChangeIncrC)

    self.cmb_augments.setDisabled(False)
    self.cmb_augments.currentIndexChanged[int].disconnect()
    self.cmb_augments.setCurrentIndex(num_augments)
    self.cmb_augments.currentIndexChanged[int].connect(self.onChangeAugments)

  def setAlternateBGColor(self):
    self.setStyleSheet('GearEntriesFrame { background-color:rgb(248,248,248) }')

  @pyqtSlot(int)
  def onSetCodeOffset(self, signed_offset):
    self.code_offset = signed_offset

  @pyqtSlot()
  def onReadSlots(self):
    self.read_block.emit(self.addr_start + self.code_offset, self.max_num_slots * 4 * 6)

  @pyqtSlot(int, int, QByteArray)
  def onBlockRead(self, addr_start, num_bytes, raw_bytes):
    # Determine whether block has cache or single slot
    if (addr_start == (self.addr_start + self.code_offset)) and (num_bytes == self.max_num_slots * 4 * 6):
      self.onCacheRead(raw_bytes)
    elif num_bytes == 4 * 6:  # Assume read slot
      # Ignore if no cache
      if not (0 <= self.cur_slot_idx < len(self.slots_cache)):
        return
      self.onSlotRead(addr_start, raw_bytes)

  def onCacheRead(self, raw_bytes):
    slot_bytes = str(raw_bytes)
    old_slots_cache = self.slots_cache
    self.slots_cache = []

    self.slots_txt = []
    for slot_i in xrange(self.max_num_slots):
      byte_offset = slot_i*6*4
      cur_slot_bytes = slot_bytes[byte_offset:(byte_offset+6*4)]
      if len(cur_slot_bytes) != 6*4:
        continue
      self.slots_cache.append(cur_slot_bytes)
      if not is_gear_empty(cur_slot_bytes):
        # print '%03d: %08X %08X %08X %08X %08X %08X' % (slot_i+1,
        #                                                struct.unpack('>I',cur_slot_bytes[0:4])[0],
        #                                                struct.unpack('>I', cur_slot_bytes[4:8])[0],
        #                                                struct.unpack('>I', cur_slot_bytes[8:12])[0],
        #                                                struct.unpack('>I', cur_slot_bytes[12:16])[0],
        #                                                struct.unpack('>I', cur_slot_bytes[16:20])[0],
        #                                                struct.unpack('>I', cur_slot_bytes[20:24])[0])
        self.slots_txt.append('Slot %03d' % (slot_i+1))
      elif self.cur_slot_idx == slot_i: # Previously-selected gear now empty, so reset selection
        self.cur_slot_idx = -1
        self.cur_slot_bytes = None

    # Update UI
    self.log.emit('Found %d %s slots in memory' % (len(self.slots_txt), self.class_label), 'black')
    self.cmb_slots.currentIndexChanged[str].disconnect()
    self.cmb_slots.clear()
    self.cmb_slots.currentIndexChanged[str].connect(self.onChangeSlot)
    if len(self.slots_cache) <= 0:
      self.cur_slot_idx = -1
      self.cur_slot_bytes = None
    else:
      prev_slot_idx = self.cur_slot_idx
      self.cmb_slots.currentIndexChanged[str].disconnect()
      self.cmb_slots.addItems(self.slots_txt)
      # If previously did not select slot, then find first valid slot idx
      if self.cur_slot_idx < 0:
        for slot_idx in xrange(len(self.slots_cache)):
          if not is_gear_empty(self.slots_cache[slot_idx]):
            self.cur_slot_idx = slot_idx
            break
      # Find first changed slot idx
      if 0 <= self.cur_slot_idx < len(self.slots_cache):
        max_cmp = min(len(old_slots_cache), len(self.slots_cache))
        for slot_idx in xrange(max_cmp):
          if old_slots_cache[slot_idx] != self.slots_cache[slot_idx]:
            if not is_gear_empty(self.slots_cache[slot_idx]):
              self.cur_slot_idx = slot_idx
              break
      if 0 <= self.cur_slot_idx < len(self.slots_cache):
        self.cur_slot_bytes = self.slots_cache[self.cur_slot_idx]
        cur_slot_txt = 'Slot %03d' % (self.cur_slot_idx + 1)
        cur_slot_cmb_idx = self.slots_txt.index(cur_slot_txt)
        self.cmb_slots.setCurrentIndex(cur_slot_cmb_idx)
      self.cmb_slots.currentIndexChanged[str].connect(self.onChangeSlot)
    self.updateUI()

  def onSlotRead(self, addr_word, raw_bytes):
    addr_cur_slot = self.addr_start + self.code_offset + self.cur_slot_idx * 4 * 6
    if addr_word == addr_cur_slot:
      self.slots_cache[self.cur_slot_idx] = raw_bytes
      if is_gear_empty(raw_bytes):
        self.refreshSlots()
      else:
        self.cur_slot_bytes = raw_bytes
        self.updateUI()
    else:  # Update cached value of other slots
      addr_first_slot = self.addr_start + self.code_offset
      addr_last_slot = self.addr_end + self.code_offset
      if (addr_first_slot <= addr_word <= addr_last_slot) and \
         ((addr_word - addr_first_slot) % 4 * 6 == 0):
        slot_i = (addr_word - addr_first_slot) / 4 / 6
        self.slots_cache[slot_i] = raw_bytes

  def refreshSlots(self):
    self.slots_txt = []
    first_valid_slot_idx = -1
    for slot_i in xrange(len(self.slots_cache)):
      if not is_gear_empty(self.slots_cache[slot_i]):
        self.slots_txt.append('Slot %03d' % (slot_i+1))
        if first_valid_slot_idx < 0:
          first_valid_slot_idx = slot_i

    self.cmb_slots.clear()
    if len(self.slots_cache) <= 0:
      self.cmb_slots.setDisabled(True)
      self.cur_slot_idx = -1
      self.cur_slot_bytes = None
    else:
      self.cmb_slots.setDisabled(False)
      self.cmb_slots.addItems(self.slots_txt)
      self.cur_slot_idx = first_valid_slot_idx
      if 0 <= self.cur_slot_idx < len(self.slots_cache):
        self.cur_slot_bytes = self.slots_cache[self.cur_slot_idx]

    self.updateUI()

  @pyqtSlot(str)
  def onChangeSlot(self, slot_name):
    # Validate new_slot_idx
    if len(slot_name) <= 5: # Suspect that this occurs when scrolling across many combo box entries
      return
    new_slot_idx = int(slot_name[4:]) - 1
    if not (0 <= new_slot_idx < len(self.slots_cache)):
      return

    # Update slot idx and read value from memory
    self.cur_slot_idx = new_slot_idx
    cur_addr_hex = self.addr_start + self.cur_slot_idx * 4 * 6
    self.cmb_skills_a.setDisabled(True)
    self.cmb_incr_a.setDisabled(True)
    self.cmb_skills_b.setDisabled(True)
    self.cmb_incr_b.setDisabled(True)
    self.cmb_skills_c.setDisabled(True)
    self.cmb_incr_c.setDisabled(True)
    self.cmb_slots.setDisabled(True)
    self.txt_raw.setDisabled(True)
    self.onReadSlot()

  @pyqtSlot()
  def onChangeRaw(self):
    # Parse and validate hex string
    raw_txt = str(self.txt_raw.text())
    raw_words = raw_txt.split()
    if len(raw_words) != 6 or len(raw_words[0]) != 8 or len(raw_words[1]) != 8 or len(raw_words[2]) != 8 or \
       len(raw_words[3]) != 8 or len(raw_words[4]) != 8 or len(raw_words[5]) != 8:
      self.log.emit('Invalid raw gear data format, expecting XXXXXXXX XXXXXXXX XXXXXXXX XXXXXXXX XXXXXXXX XXXXXXXX',
                    'red')
      self.txt_raw.editingFinished.disconnect()
      if self.cur_slot_bytes is not None and len(self.cur_slot_bytes) == 24:
        cur_slot_words = struct.unpack('>IIIIII', self.cur_slot_bytes)
        self.txt_raw.setText('%08X %08X %08X %08X %08X %08X' % cur_slot_words)
      else:
        self.txt_raw.setText('')
      self.txt_raw.editingFinished.connect(self.onChangeRaw)
      return

    self.cur_slot_bytes = ''
    for idx in xrange(6):
      self.cur_slot_bytes += struct.pack('>I', int(raw_words[idx], 16))
    self.updateUI()

  @pyqtSlot(str)
  def onChangeSkillA(self, skill):
    skill = str(skill)
    if skill in self.skill2id:
      new_skill_id = self.skill2id[skill]
      (gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
       skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id) = parse_gear_bytes(self.cur_slot_bytes)
      if new_skill_id == skill_a_id:
        return
      self.cur_slot_bytes = form_gear_bytes(gear_id_bytes, index, post_index, new_skill_id, skill_a_incr,
                                            skill_b_id, skill_b_incr, skill_c_id, skill_c_incr,
                                            augment_a_id, augment_b_id, augment_c_id)
      self.updateUI()
    else:
      self.log.emit('Coding Error: unrecognized skill - %s' % skill, 'red')

  @pyqtSlot(str)
  def onChangeSkillB(self, skill):
    skill = str(skill)
    if skill in self.skill2id:
      new_skill_id = self.skill2id[skill]
      (gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
       skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id) = parse_gear_bytes(self.cur_slot_bytes)
      if new_skill_id == skill_b_id:
        return
      self.cur_slot_bytes = form_gear_bytes(gear_id_bytes, index, post_index, skill_a_id, skill_a_incr,
                                            new_skill_id, skill_b_incr, skill_c_id, skill_c_incr,
                                            augment_a_id, augment_b_id, augment_c_id)
      self.updateUI()
    else:
      self.log.emit('Coding Error: unrecognized skill - %s' % skill, 'red')

  @pyqtSlot(str)
  def onChangeSkillC(self, skill):
    skill = str(skill)
    if skill in self.skill2id:
      new_skill_id = self.skill2id[skill]
      (gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
       skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id) = parse_gear_bytes(self.cur_slot_bytes)
      if new_skill_id == skill_c_id:
        return
      self.cur_slot_bytes = form_gear_bytes(gear_id_bytes, index, post_index, skill_a_id, skill_a_incr,
                                            skill_b_id, skill_b_incr, new_skill_id, skill_c_incr,
                                            augment_a_id, augment_b_id, augment_c_id)
      self.updateUI()
    else:
      self.log.emit('Coding Error: unrecognized skill - %s' % skill, 'red')

  @pyqtSlot(int)
  def onChangeIncrA(self, new_incr):
    new_incr = int(new_incr)
    (gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
     skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id) = parse_gear_bytes(self.cur_slot_bytes)
    if new_incr == skill_a_incr:
      return
    self.cur_slot_bytes = form_gear_bytes(gear_id_bytes, index, post_index, skill_a_id, new_incr,
                                          skill_b_id, skill_b_incr, skill_c_id, skill_c_incr,
                                          augment_a_id, augment_b_id, augment_c_id)
    self.updateUI()

  @pyqtSlot(int)
  def onChangeIncrB(self, new_incr):
    new_incr = int(new_incr)
    (gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
     skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id) = parse_gear_bytes(self.cur_slot_bytes)
    if new_incr == skill_b_incr:
      return
    self.cur_slot_bytes = form_gear_bytes(gear_id_bytes, index, post_index, skill_a_id, skill_a_incr,
                                          skill_b_id, new_incr, skill_c_id, skill_c_incr,
                                          augment_a_id, augment_b_id, augment_c_id)
    self.updateUI()

  @pyqtSlot(str)
  def onChangeIncrC(self, new_incr):
    new_incr = int(new_incr)
    (gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
     skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id) = parse_gear_bytes(self.cur_slot_bytes)
    if new_incr == skill_c_incr:
      return
    self.cur_slot_bytes = form_gear_bytes(gear_id_bytes, index, post_index, skill_a_id, skill_a_incr,
                                          skill_b_id, skill_b_incr, skill_c_id, new_incr,
                                          augment_a_id, augment_b_id, augment_c_id)
    self.updateUI()

  @pyqtSlot(int)
  def onChangeAugments(self, new_num_augments):
    new_num_augments = int(new_num_augments)
    (gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
     skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id) = parse_gear_bytes(self.cur_slot_bytes)
    cur_num_augments = (augment_a_id != 0xFFFF) + (augment_b_id != 0xFFFF) + (augment_c_id != 0xFFFF)
    if new_num_augments == cur_num_augments:
      return
    if augment_a_id == 0xFFFF:
      augment_a_id = augment_b_id
      augment_b_id = augment_c_id
      augment_c_id = 0xFFFF
    if augment_a_id == 0xFFFF:
      augment_a_id = augment_b_id
      augment_b_id = 0xFFFF
    if new_num_augments == 1:
      if augment_a_id == 0xFFFF: augment_a_id = 0x0000
      augment_b_id = 0xFFFF
      augment_c_id = 0xFFFF
    elif new_num_augments == 2:
      if augment_a_id == 0xFFFF: augment_a_id = 0x0000
      if augment_b_id == 0xFFFF: augment_b_id = 0x0000
      augment_c_id = 0xFFFF
    elif new_num_augments == 3:
      if augment_a_id == 0xFFFF: augment_a_id = 0x0000
      if augment_b_id == 0xFFFF: augment_b_id = 0x0000
      if augment_c_id == 0xFFFF: augment_c_id = 0x0000
    else: # Assume new_num_augments == 0 by default
      augment_a_id = 0xFFFF
      augment_b_id = 0xFFFF
      augment_c_id = 0xFFFF
    self.cur_slot_bytes = form_gear_bytes(gear_id_bytes, index, post_index, skill_a_id, skill_a_incr,
                                          skill_b_id, skill_b_incr, skill_c_id, skill_c_incr,
                                          augment_a_id, augment_b_id, augment_c_id)
    self.updateUI()

  @pyqtSlot()
  def onReadSlot(self):
    try:
      if not (0 <= self.cur_slot_idx < len(self.slots_cache)):
        raise ValueError('must cache slots before reading')
      addr_cur_slot = self.addr_start + self.code_offset + self.cur_slot_idx * 4 * 6
      self.read_block.emit(addr_cur_slot, 4 * 6)
    except ValueError, e:
      self.log.emit('READ %s Slot %03d failed: %s' % (self.class_label, self.cur_slot_idx + 1, str(e)), 'red')
    except BaseException, e:
      self.log.emit('READ %s Slot %03d failed: %s' % (self.class_label, self.cur_slot_idx + 1, str(e)), 'red')
      traceback.print_exc()

  @pyqtSlot()
  def onPokeSlot(self):
    try:
      if not (0 <= self.cur_slot_idx < len(self.slots_cache)) or self.cur_slot_bytes is None:
        raise ValueError('must cache slots before poking')

      addr_cur_slot = self.addr_start + self.code_offset + self.cur_slot_idx * 4 * 6
      if is_gear_empty(self.cur_slot_bytes):
        raise ValueError('cannot poke empty gear to slot')

      self.poke_block.emit(addr_cur_slot, QByteArray(self.cur_slot_bytes), False)
      self.read_block.emit(addr_cur_slot, 4 * 6)

    except ValueError, e:
      self.log.emit('POKE %s Slot %03d failed: %s' % (self.class_label, self.cur_slot_idx + 1, str(e)), 'red')
    except BaseException, e:
      self.log.emit('POKE %s Slot %03d failed: %s' % (self.class_label, self.cur_slot_idx + 1, str(e)), 'red')
      traceback.print_exc()
