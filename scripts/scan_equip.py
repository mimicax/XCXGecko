import sys, os, struct
sys.path.append(os.path.abspath('../pygecko'))
from tcpgecko import *

wiiu_addr = '192.168.0.133'
print '> Connecting to Wii U...'
g = TCPGecko(wiiu_addr)
print '> Connected to Wii U'

addr_base = 0x1C3B2460
num_equip = 100
num_bytes = num_equip*24 # each equip uses 6 words

bytes_raw = g.readmem(addr_base, num_bytes)
num_equip_read = len(bytes_raw)/24
for equip_i in xrange(num_equip_read):
  offset = equip_i*24
  addr_curr = addr_base + offset
  bytes_curr_equip = bytes_raw[offset:(offset+24)]
  wv = struct.unpack('>IIIIII', bytes_curr_equip)
  equip_empty = (wv[0] == 0 and wv[1] == 0 and wv[2] == 0)
  if equip_empty:
    print '%08X (%03d): EMPTY' % (addr_curr, equip_i+1)
  else:
    print '%08X (%03d): %08X %08X %08X %08X %08X %08X' % \
          (addr_curr, equip_i+1, wv[0], wv[1], wv[2], wv[3], wv[4], wv[5])

g.s.close()
print '> Disconnected from Wii U'
