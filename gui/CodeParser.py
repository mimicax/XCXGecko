import math


class Code:
  def __init__(self, idx, txt_addr='0x10000000', bit_rshift=0, num_bytes=4, dft_value=None, label='NO_LABEL [NO_USER]'):
    self.idx = idx
    self.txt_addr = txt_addr # either 0xMEMADDR or [0xPOINTER]+OFFSET
    self.bit_rshift = bit_rshift
    self.num_bytes = num_bytes
    self.dft_value = dft_value # either None or hex
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
    if self.dft_value is not None:
      fmt = '0x%%0%dX' % (self.num_bytes*2)
      msg += fmt % self.dft_value
    else:
      msg += 'X'*(self.num_bytes*2)
    msg += ' >>%d' % self.bit_rshift
    return msg


# Supported code formats:
# <MEMORY_ADDR | [POINTER_ADDR]+BYTE_OFFSET> <HEX_FORMAT | HEX_VALUE> >>OPTIONAL_BIT_RSHIFT
#
# Examples:
# 16-bit memory poke: 12345678 XXXX
# 8-bit memory poke with specific value: 12345678 1A
# 32-bit pointer memory poke: [1F000000]+128 XXXXXXXX
# 8-bit pointer memory poke with 3-bit right shift and specific value: [1F900000]+12 FF >>3
def parse_codes(path):
  codes = {}
  code_idx = 0
  with open(path, 'r') as f:
    label = None
    label_multi_count = 0
    line_number = 0
    for line in f.readlines():
      line_number += 1
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
        tokens = line.split()
        if len(tokens) < 2:
          raise BaseException('parser failed on line %d: expecting MEM_ADDR|[PTR_ADDR]+OFFSET HEX_FORMAT|HEX_VALUE' %
                              line_number)
        txt_addr = tokens[0]
        if len(tokens) >= 3 and len(tokens[2]) > 2 and tokens[2][:2] == '>>':
          bit_rshift = int(tokens[2][2:])
          if bit_rshift <= 0 or bit_rshift >= 24:
            raise BaseException('parser failed on line %d: bit rshift %d not within [0, 24] range' %
                                (line_number, bit_rshift))
        if len(tokens[1]) == 2:
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
          raise BaseException('parser failed on line %d: format or value must have 1/2/4 bytes length' % line_number)

        # Store code line
        label_multi_count += 1
        cur_label = label
        if label_multi_count > 1:
          cur_label = '%s (%d)' % (label, label_multi_count)
        if cur_label in codes:
          raise BaseException('parser failed on line %d: duplicate label - %s' % (line_number, cur_label))
        codes[cur_label] = Code(code_idx, txt_addr, bit_rshift, num_bytes, dft_value, cur_label)
        code_idx += 1
  return codes
