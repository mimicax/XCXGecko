import traceback
import ConfigParser


class DataStore(object):
  def __init__(self):
    self.config = None
    self.ip = ''
    self.connected = False
    self.codes = dict()
    self.custom_codes = dict()

  def parseCfg(self, path):
    items = [('General', 'wiiu_ip', 'wiiu_ip'),
             ('General', 'code_offset', 'code_offset'),
             ('Databases', 'code_db', 'code_db'),
             ('Databases', 'local_code_db', 'local_code_db'),
             ('Verbosity', 'read', 'verbose_read'),
             ('Verbosity', 'poke', 'verbose_poke'),
             ('Verbosity', 'poke_str', 'verbose_poke_str')]

    config = dict()
    try:
      cfg = ConfigParser.RawConfigParser()
      cfg.read(path)
      for section, option, label in items:
        config[label] = cfg.get(section, option)
    except BaseException, e:
      traceback.print_exc()
      raise SyntaxError('Failed to parse %s: %s' % (path, str(e)))
    config['code_offset'] = int(float(config['code_offset']))
    config['verbose_read'] = (config['verbose_read'] == 'True')
    config['verbose_poke'] = (config['verbose_poke'] == 'True')
    config['verbose_poke_str'] = (config['verbose_poke_str'] == 'True')
    self.config = config


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

  def clear(self):
    self.c = []

  def addCode(self, addr_txt, bit_rshift, num_bytes, dft_value, is_float, is_ascii):
    code_i = len(self.c) + 1
    code = Code(self.label, addr_txt, bit_rshift, num_bytes, dft_value, is_float, is_ascii)
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

  except (SyntaxError, ValueError), e:
    raise SyntaxError('Failed to parse Codes DB on line %d: %s' % (line_count, str(e)))
  except BaseException, e:
    traceback.print_exc()
    raise SyntaxError('Failed to parse Codes DB on line %d: %s' % (line_count, str(e)))

  return codes


# Same as above, but parses all code lines into a single existing code_set
def parse_custom_codes(cs, codes_txt):
  codes_lines = codes_txt.split('\n')
  cs.clear()
  line_count = 0
  try:
    for line in codes_lines:
      line_count += 1

      line = line.strip()
      if len(line) <= 0 or line[0] == '#': # comment line
        continue
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

  except (SyntaxError, ValueError), e:
    raise SyntaxError('Failed to parse line %d: %s' % (line_count, str(e)))
  except BaseException, e:
    traceback.print_exc()
    raise SyntaxError('Failed to parse line %d: %s' % (line_count, str(e)))


def parse_dec_or_hex(s): # return (dec_val, is_hex) if success, else None
  s = str(s).strip()
  if len(s) == 0:
    return None

  is_hex = False
  is_neg = False
  if len(s) > 1 and (s[0] == '+' or s[0] == '-'):
    is_neg = (s[0] == '-')
    s = s[1:]

  try:
    if len(s) > 2 and s[:2] == '0x':
      is_hex = True
      dec_val = int(s[2:], 16)
    else:
      dec_val = int(s)
    if is_neg:
      dec_val *= -1
  except ValueError:
    return None

  return dec_val, is_hex


def to_signed_hex_str(v, num_bytes=None):
  sign_char = '+'
  if v < 0:
    sign_char = '-'
  if num_bytes is None:
    return '%s0x%X' % (sign_char, abs(v))
  else:
    fmt = '%s0x%%0%dX' % (sign_char, num_bytes)
    return fmt % abs(v)
