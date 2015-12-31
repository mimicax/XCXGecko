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
    self.custom_codes = dict()
    self.item_ids = dict()
    self.item_lines = []
    self.item_types = []


def parse_cfg_file(cfg_path):
  items = [('General', 'wiiu_ip', 'wiiu_ip'),
           ('Databases', 'code_db', 'code_db'),
           ('Databases', 'item_id_db', 'item_id_db'),
           ('Databases', 'local_code_db', 'local_code_db'),
           ('Databases', 'local_item_id_db', 'local_item_id_db'),
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
  config['verbose_read'] = (config['verbose_read'] == 'True')
  config['verbose_poke'] = (config['verbose_poke'] == 'True')
  config['verbose_poke_str'] = (config['verbose_poke_str'] == 'True')
  return config


class Code:
  free_id = 0

  def __init__(self, label, addr_txt, bit_rshift, num_bytes, dft_value,
               is_float, is_ascii):
    # Populate fields
    Code.free_id += 1
    self.id = Code.free_id
    self.label = label

    self.addr_txt = addr_txt # either 0xMEMADDR or [0xPOINTER]+OFFSET
    self.is_ptr = False
    self.addr_base = None
    self.ptr_offset = None
    self.bit_rshift = bit_rshift
    self.num_bytes = num_bytes
    self.dft_value = dft_value # either None or packed bytes
    self.is_float = is_float
    self.is_ascii = is_ascii

    # Parse addr_txt into memory or pointer addr_base
    if self.addr_txt[:2] == '0x':
      self.is_ptr = False
      self.addr_base = int(self.addr_txt[2:], 16)
      self.ptr_offset = None
    elif self.addr_txt[:3] == '[0x' and self.addr_txt.find('+') > 0:
      self.is_ptr = True
      self.addr_base = int(self.addr_txt[3:11], 16)
      self.ptr_offset = int(self.addr_txt[13:])
    elif self.addr_txt[0] == '[' and self.addr_txt.find('+') > 0: # omitted 0x in pointer address
      self.addr_base = int(self.addr_txt[1:9], 16)
      self.is_ptr = True
      self.ptr_offset = int(self.addr_txt[11:])
    else: # omitted 0x in memory address
      self.addr_base = int(self.addr_txt, 16)
      self.is_ptr = False
      self.ptr_offset = None

    # Adjust addr_base/bit_rshift so that (bit_rshift+num_bytes*8) < 32 bits, to facilitate read_mem
    if (not self.is_ascii) and (self.num_bytes > 4 or (self.num_bytes == 4 and self.bit_rshift > 0)):
      raise ValueError('missing support for non-text codes spanning multiple words') # use 2+ codes instead
    if self.bit_rshift != 0:
      if not self.is_ptr:
        total_num_bits = self.bit_rshift + self.num_bytes*8
        if self.num_bytes == 1 or self.num_bytes == 2:
          rem_num_bits = (total_num_bits - 1) % 32 + 1
          num_word_shift = (total_num_bits - rem_num_bits) / 32
          self.bit_rshift -= num_word_shift * 32
          self.addr_base += num_word_shift * 4
      else: # self.is_ptr
        if self.bit_rshift + self.num_bytes*8 > 32:
          raise ValueError('missing support for bit-shifted pointer code spanning multiple words')

  def __str__(self):
    msg = ''
    msg += str(self.id) + ' - ' + self.label + ': '
    if self.is_ptr:
      msg += '[0x%08X]+%d ' % (self.addr_base, self.ptr_offset)
    else:
      msg += '0x%08X ' % self.addr_base
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
    if self.bit_rshift != 0:
      msg += ' >>%d' % self.bit_rshift
    return msg


class CodeSet:
  def __init__(self, label):
    self.id = None
    self.label = label
    self.hidden = False # hidden in Other Codes view
    self.c = []

  def addCode(self, addr_txt, bit_rshift, num_bytes, dft_value, is_float, is_ascii):
    code_i = len(self.c) + 1
    label = self.label
    if code_i > 1:
      label += '-%d' % code_i
    code = Code(label, addr_txt, bit_rshift, num_bytes, dft_value, is_float, is_ascii)
    if self.id is None:
      self.id = code.id
    self.c.append(code)

  def __str__(self):
    msg = ''
    for code in self.c:
      if self.hidden:
        msg += '_ '
      else:
        msg += '* '
      msg += str(code) + '\n'
    return msg


# Supported code formats:
# ARG1_ADDR ARG2_VALUE ARG3_OPT
#
# ARG1_ADDR  = MEMORY_ADDR | [POINTER_ADDR]+BYTE_OFFSET
# ARG2_VALUE = XX | XXXX | XXXXXXXX | HEX_VALUE | ASCII(BYTES)
# ARG3_OPT   = >>BIT_RSHIFT
#
# Examples:
# 16-bit memory poke: 12345678 XXXX
# 8-bit memory poke with default value: 12345678 1A
# 32-bit pointer memory poke: [1F000000]+128 XXXXXXXX
# 8-bit pointer memory poke with 3-bit right shift and default value: [1F900000]+12 F9 >>3
# 10-byte ASCII memory poke: 1C303984 ASCII(10)
def parse_codes(codes_txt):
  codes_lines = codes_txt.split('\n')
  codes = dict()

  cs = None
  line_count = 0
  try:
    for line in codes_lines:
      line_count += 1

      line = line.strip()
      if len(line) <= 0: # new code
        if cs is not None and len(cs.c) == 0:
          codes.pop(cs.label) # Prune empty code
        cs = None
      elif line[0] == '#': # comment line
        continue
      elif cs is None: # label line
        label = line.strip()
        if label in codes:
          raise ValueError('duplicate label for ' + label)
        cs = CodeSet(label)
        codes[label] = cs

      else: # code line
        tokens = line.split()
        if len(tokens) < 2:
          raise SyntaxError('invalid code entry, expecting ARG1_ADDR ARG2_VALUE (ARG3_OPT)')
        
        addr_txt = tokens[0]
        bit_rshift = 0
        dft_value = None
        is_float = (cs.label.find('(float)') >= 0)
        is_ascii = False
        if len(tokens) >= 3 and len(tokens[2]) > 2 and tokens[2][:2] == '>>':
          bit_rshift = int(tokens[2][2:])
          if bit_rshift < 0:
            raise ValueError('bit_rshift should be non-negative') # suspect typo in code
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
          raise ValueError('hex format or hex value must be 1/2/4 bytes')

        cs.addCode(addr_txt, bit_rshift, num_bytes, dft_value, is_float, is_ascii)

  except BaseException, e:
    traceback.print_exc()
    raise BaseException('Failed to parse Codes DB on line %d: %s' % (line_count, str(e)))

  return codes


class Item:
  MAX_ID_VAL = 0x3FF # NOTE: also used as bit mask!

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

  def __str__(self):
    msg = 'l%d t%02X i%03X v%08X %s' % (self.line, self.type_val, self.id_val, self.val_word, self.name)
    return msg


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
