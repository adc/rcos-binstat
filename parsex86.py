DATA = "x86data"

def ishex(s):
  for x in s:
    if x not in '0123456789ABCDEF':
      return 0
  return 1

def parse_inst(line):
  #rip out mnemonic
  mnemonic, line =  line.split(' ',1)
  
  #pull out operands
  next, line = line.split(' ',1)
  operands = []
  while not ishex(next):
    operands.append(next)
    next, line = line.split(' ',1)
  #pull out opcodes
  opcodes = []
  while ishex(next):
    opcodes.append(int(next,16))
    parts = line.split(' ',1)
    next = parts[0]
    if len(parts) == 1:
      break
    else:
      line = parts[1]
  #check for modrm description
  
  modrm = None
  if next[0] in '/+':
    modrm = next
    next, line = line.split(' ',1)
  
  immediate = None
  #check for immediate
  imdesc = ["ib", "iw", "id", "iq"]
  if next in imdesc:
    immediate = next
  
  code_offset = None
  coffsets = ['cb', 'cw', 'cd', 'cq', 'm64']
  if next in coffsets:
    code_offset = next

  if not immediate and not code_offset:
    line = next+' '+line


  #rest is instruction notes
  notes = line


  return {'mnemonic':mnemonic, 'opcodes': opcodes, 'operands':operands, 
         'modrm':modrm, 'immediate':immediate, 'code_offset': code_offset,
         'note': notes}
  #return ('XADD', [15, 193], ['reg/mem16,', 'reg16'], '/r', None, None, 'Exchange the contents of a 16-bit register with the contents of a 16-bit destination register or memory operand and load their sum into the destination. ')

def get_decode_dict():
  decode = {}

  data =open(DATA, 'r').read()

  for instruction in data.split("\n\n"):
    info = []
    for line in instruction.split('\n'):
      if 'eflags' in line:
        info.append(line)
      else:
        info.append(parse_inst(line))
  
    #load up multi-byte opcodes into the dictionary
    for instr in info[:-1]:
      instr['eflags'] = info[-1][7:]
      
      ops = instr['opcodes']
      #create nested dictionaries
      #since opcodes also depend on modrm bits, 
      #multiple instructions are possible,
      # all possible instructions are stored in a list.
      prev = decode
      for i in range(0, len(ops)-1):
        if ops[i] not in prev:
          prev[ops[i]] = {}
        prev = prev[ops[i]]
      if ops[-1] not in prev:
        prev[ops[-1]] = {}

      #get the modes of the instruction
      #this is to deal with the flexibility of 
      #multiple addressing modes for the same opcodes
      modes = []
      for i in [16,32,64]:
        for operand in instr['operands']:
          if ('%d'%i) in operand:
            modes.append(i)
            break
            
      if 'instr' not in prev[ops[-1]]:
        prev[ops[-1]]['instr'] = {}
        for m in modes:
          prev[ops[-1]]['instr'][m] = [instr]
        if not modes:
          for m in [16, 32, 64]:
            prev[ops[-1]]['instr'][m] = [instr]
      else:
        if not modes:
          for m in [16, 32, 64]:
            if m in prev[ops[-1]]['instr']:
              prev[ops[-1]]['instr'][m].append(instr)
            else:
              prev[ops[-1]]['instr'][m] = [instr]
        for m in modes:
          if m in prev[ops[-1]]['instr']:
            prev[ops[-1]]['instr'][m].append(instr)
          else:
            prev[ops[-1]]['instr'][m] = [instr]

  return decode

if __name__ == "__main__":
  get_decode_dict()