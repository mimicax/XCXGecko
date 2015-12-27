import ConfigParser
import math
import string
import traceback


class DataStore:
  def __init__(self):
    self.config = None
    self.ip = ''
    self.connected = False
    self.codes = dict()
    self.item_ids = dict()
    self.item_lines = []
    self.item_types = []


def parse_cfg_file(cfg_path):
  items = [('General', 'wiiu_ip', 'wiiu_ip'),
           ('Databases', 'code_db', 'code_db'),
           ('Databases', 'item_id_db', 'item_id_db'),
           ('Verbosity', 'read', 'verbose_read'),
           ('Verbosity', 'poke', 'verbose_poke'),
           ('Verbosity', 'poke_str', 'verbose_poke_str')]

  config = dict()
  try:
    cfg = ConfigParser.RawConfigParser()
    cfg.read(cfg_path)
    for section, option, label in items:
      config[label] = cfg.get(section, option)
  except BaseException, e:
    traceback.print_exc()
    raise BaseException('Failed to parse %s: %s' % (cfg_path, str(e)))
  return config


class Code:
  def __init__(self, idx, txt_addr='0x10000000', bit_rshift=0, num_bytes=4, dft_value=None, is_float=False, is_acsii=False, label='NO_LABEL [NO_USER]'):
    self.idx = idx
    self.txt_addr = txt_addr # either 0xMEMADDR or [0xPOINTER]+OFFSET
    self.bit_rshift = bit_rshift
    self.num_bytes = num_bytes
    self.dft_value = dft_value # either None or hex
    self.is_float = is_float
    self.is_ascii = is_acsii
    self.label = label

    self.num_mem_words = int(math.ceil(float(bit_rshift+num_bytes*8)/32)) # number of 32-bit addresses spanning value
    self.hidden = False # hidden in custom gecko codes view

    if self.txt_addr[:2] == '0x':
      self.is_ptr = False
      self.base_addr = int(self.txt_addr[2:], 16)
      self.ptr_offset = None
    elif self.txt_addr[:3] == '[0x' and self.txt_addr.find('+') > 0:
      self.is_ptr = True
      self.base_addr = int(self.txt_addr[3:11], 16)
      self.ptr_offset = int(self.txt_addr[13:])
    elif self.txt_addr[0] == '[' and self.txt_addr.find('+') > 0: # forgot 0x in pointer address
      self.base_addr = int(self.txt_addr[1:9], 16)
      self.is_ptr = True
      self.ptr_offset = int(self.txt_addr[11:])
    else: # forgot 0x in memory address
      self.base_addr = int(self.txt_addr, 16)
      self.is_ptr = False
      self.ptr_offset = None

    # Compute word-aligned memory address (if not pointer)
    if not self.is_ptr:
      if num_bytes == 1 or num_bytes == 2:
        rem = self.base_addr % 4
        if rem > 0:
          self.bit_rshift += rem * 8
          self.base_addr -= rem

  def __str__(self):
    msg = ''
    if self.hidden:
      msg += '* '
    else:
      msg += '  '
    msg += self.label + ': '
    if self.is_ptr:
      msg += '[0x%08X]+%d ' % (self.base_addr, self.ptr_offset)
    else:
      msg += '0x%08X ' % self.base_addr
    if self.is_ascii:
      msg += 'ASCII(%d)' % self.num_bytes
    elif self.dft_value is not None:
      if self.is_float:
        msg += '%f(f)' % self.dft_value
      else:
        fmt = '0x%%0%dX' % (self.num_bytes*2)
        msg += fmt % self.dft_value
    else:
      msg += 'X'*(self.num_bytes*2)
      if self.is_float:
        msg += '(f)'
    msg += ' >>%d' % self.bit_rshift
    return msg


# Supported code formats:
# <MEMORY_ADDR | [POINTER_ADDR]+BYTE_OFFSET> <HEX_FORMAT | HEX_VALUE | ASCII(BYTES)> >>OPTIONAL_BIT_RSHIFT
#
# Examples:
# 16-bit memory poke: 12345678 XXXX
# 8-bit memory poke with specific value: 12345678 1A
# 32-bit pointer memory poke: [1F000000]+128 XXXXXXXX
# 8-bit pointer memory poke with 3-bit right shift and specific value: [1F900000]+12 FF >>3
# 10-byte ASCII memory poke: 1C303984 ASCII(10)
def parse_codes(codes_txt):
  codes_lines = codes_txt.split('\n')
  codes = {}
  code_idx = 0

  label = None
  label_multi_count = 0
  line_count = 0
  try:
    for line in codes_lines:
      line_count += 1

      line = line.strip()
      if len(line) <= 0: # new code
        label = None
        label_multi_count = 0
      elif line[0] == '#': # comment line
        continue
      elif label is None: # label line
        label = line.strip()
        label_multi_count = 0
      else: # code line
        # Parse code line
        bit_rshift = 0
        dft_value = None
        is_ascii = False
        tokens = line.split()
        if len(tokens) < 2:
          raise BaseException('expecting MEM_ADDR|[PTR_ADDR]+OFFSET HEX_FORMAT|HEX_VALUE|ASCII(BYTES)')
        txt_addr = tokens[0]
        is_float = (label.find('(float)') >= 0)
        if len(tokens) >= 3 and len(tokens[2]) > 2 and tokens[2][:2] == '>>':
          bit_rshift = int(tokens[2][2:])
          if bit_rshift <= 0 or bit_rshift >= 24:
            raise BaseException('bit rshift not within [0, 24] range')
        if tokens[1].find('ASCII(') == 0:
          num_bytes = int(tokens[1][6:-1])
          is_ascii = True
        elif len(tokens[1]) == 2:
          num_bytes = 1
          if tokens[1] != 'XX':
            dft_value = int(tokens[1], 16)
        elif len(tokens[1]) == 4:
          num_bytes = 2
          if tokens[1] != 'XXXX':
            dft_value = int(tokens[1], 16)
        elif len(tokens[1]) == 8:
          num_bytes = 4
          if tokens[1] != 'XXXXXXXX':
            dft_value = int(tokens[1], 16)
        else:
          raise BaseException('format or value must have 1/2/4 bytes length')

        # Store code line
        label_multi_count += 1
        cur_label = label
        if label_multi_count > 1:
          cur_label = '%s (%d)' % (label, label_multi_count)
        if cur_label in codes:
          raise BaseException('duplicate label for ' + cur_label)
        codes[cur_label] = Code(code_idx, txt_addr, bit_rshift, num_bytes, dft_value, is_float, is_ascii, cur_label)
        code_idx += 1
  except BaseException, e:
    traceback.print_exc()
    raise BaseException('Failed to parse Codes DB on line %d: %s' % (line_count, str(e)))

  return codes


class Item:
  MAX_ID_VAL = 0x3FF

  '''
  WARNING: poking an illegal/large ID will cause XCX to crash back to title screen

  Item Value Word Structure:
  0    0    1    3     8    3    1    8
  uuui iiii iiii ittt  tyyy yaaa aaaa afff

  u: unknown
  i: ID
  t: type
  y: type2/unknown
  a: amount
  f: flags/unknown
  '''

  def __init__(self, type_val, id_val, name, line=-1):
    self.type_val = type_val
    self.id_val = id_val
    self.name = name
    self.val_word = form_item_word(type_val, id_val, 0)
    self.line = line


def form_item_word(type_val, id_val, amount):
  type_val &= 0xFF
  id_val &= Item.MAX_ID_VAL
  amount &= 0xFF
  val_word = (id_val << 19) | (type_val << 11) | (amount << 3)
  return val_word


def parse_item_word(val_word):
  type_val = (val_word >> 11) & 0xFF
  id_val = (val_word >> 19) & Item.MAX_ID_VAL
  amount = (val_word >> 3) & 0xFF
  return type_val, id_val, amount


def parse_item_db(db_txt):
  db_lines = db_txt.split('\n')
  item_types = []
  db = dict()

  line_count = 0
  try:
    for line in db_lines:
      line_count += 1

      if len(line) <= 0: # Skip empty lines
        continue

      elif len(line) > 4 and line[:4] == '### ': # Parse TYPE_VAL and TYPE_NAME
        type_tokens = string.split(line, maxsplit=2)
        if len(type_tokens) != 3:
          continue
        try:
          type_val = int(type_tokens[1], 16)
          if type_val < 0 or type_val > 0xFF:
            continue
          type_name = type_tokens[2]
          item_types.append((type_val, type_name))
        except BaseException, e:
          continue

      elif line[0] == '#': # Skip commented lines
        continue

      else: # Parse TYPE_VAL ID_VAL NAME
        tokens = string.split(line, maxsplit=2)
        if len(tokens) != 3:
          raise BaseException('invalid line format, expecting TYPE_VAL ID_VAL NAME')
        type_val = int(tokens[0], 16)
        id_val = int(tokens[1], 16)
        if type_val < 0 or type_val > 0xFF:
          raise BaseException('TYPE_VAL out of [%d, %d] range' % (0, 0xFF))
        if id_val < 0 or id_val > Item.MAX_ID_VAL:
          raise BaseException('ID_VAL out of [%d, %d] range' % (0, Item.MAX_ID_VAL))
        name = tokens[2]
        item = Item(type_val, id_val, name, line_count-1)
        if item.val_word in db:
          raise BaseException('duplicate entry for TYPE=%02X ID=%03X' % (type_val, id_val))
        db[item.val_word] = item
        # print 'Parsed %08X (type=%02X id=%02X): %s' % (item.val_word, item.type_val, item.id_val, item.name)

  except BaseException, e:
    traceback.print_exc()
    raise BaseException('Failed to parse Item ID DB on line %d: %s' % (line_count, str(e)))

  return db, db_lines, item_types
