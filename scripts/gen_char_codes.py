# Removed protagonist (1C38B624) due to having different memory offsets
chars_raw = '''Nagi 1C38EB44
L 1C38F0C0
Lao 1C38F63C
H.B. 1C38FBB8
Gwin 1C390134
Fyre 1C3906B0
Doug 1C390C2C
Yelv 1C3911A8
Boze 1C391724
Phog 1C391CA0
Elma 1C39221C
Lin 1C392798
Celica 1C392D14
Irina 1C393290
Murderess 1C39380C
Alexa 1C393D88
Hope 1C394304
Mia 1C394880
'''

traits_raw = '''Lv Exp [MiMiC]: 7C 000F423F
Rank Exp [MiMiC]: 12C 7FFF
BP [MiMiC]: 374 0000270F
Affinity [MiMiC]: 57A 32
Height (float) [Intropy]: 68 3F8020C4
Chest Depth (float) [Intropy]: 6C 3F8020C4
Chest Height (float) [Intropy]: 70 3F8020C4
Chest Width (float) [Intropy]: 74 3F8020C4
'''

traits = []
for line in traits_raw.splitlines():
  colon_idx = line.find(':')
  space_idx = line.find(' ', colon_idx+2)
  label = line[:colon_idx]
  incr = int(line[colon_idx+2:space_idx], 16)
  value = line[space_idx+1:]
  traits.append((label, incr, value))
  # print '> %s: +0x%08X %s' % (label, incr, value)


chars = []
for line in chars_raw.splitlines():
  name, addr = line.split()
  addr = int(addr, 16)
  chars.append((name, addr))
  # print '> %s: 0x%08X' % (name, addr)

  print '%s Name [MiMiC]\n%08X ASCII(10)\n' % (name, addr)

  for (trait, incr, value) in traits:
    print '%s %s\n%08X %s\n' % (name, trait, addr+incr, value)

  print '\n'
