"""
Lieutenant Dan:   I'm here to try out my sea legs.
Forrest Gump:     But you ain't got no legs, Lieutenant Dan

This module contains IR abstractions for
anything IR. 
""" 

##########memory abstractions
class segment:
  def __init__(self,start,end,data="",prot=0,max_prot=0):
    self.base = 0
    self.start = start
    self.end = end
    self.data = data
    self.prot = prot
    self.max_prot = max_prot
    self.code = 0
    
    if len(data) > (end - start):
      self.data = data[:end - start]
    elif len(data) < (end - start):
      self.data += "\x00"*((end-start) - len(data)+1)

  def __contains__(self, addr):
    if addr >= self.start+self.base and addr <= self.end+self.base:
      return True
    return False

  def __getitem__(self, addr):
    if addr > self.end+self.base or addr < self.start+self.base:
      raise IndexError("memory address out of range: %x"%addr)
    return self.data[addr - self.start + self.base]

  def __getslice__(self, start, stop):
    if start > self.end+self.base or start < self.start + self.base \
     or stop > self.end+self.base or stop < self.start + self.base:
      raise IndexError("memory address out of range %x-%x"%(start,stop))
    return self.data[start-self.start: stop-self.start]

class memory:
  def __init__(self, segments=[]):
    self.segments = segments

  def add(self, segment):
    self.segments.append(segment)

  def __contains__(self, addr):
    for x in self.segments:
      if addr in x:
        return True
    return False

  def __getitem__(self, addr):
    for x in self.segments:
      if addr in x:
        return x[addr]
    raise IndexError("memory address out of range")

  def __getslice__(self, start, stop):
    for x in self.segments:
      if start in x:
        return x[start:stop]
    raise IndexError("memory address out of range")


class register:
  def __init__(self, name, *aliases, **var):
    self.name = name
    self.aliases = list(aliases)
    self.size = 0
    self.callee_save = 0

    if 'size' in var:
      self.size = var['size']
    if 'callee_save' in var:
      self.callee_save = 1
    

class operand:
  def __init__(self):
    self.type = ""
    self.size = 0

class register_operand(operand):
  def __init__(self):
    self.register_name = ""
    self.type = ""

class mem_operand(operand):
  def __init__(self):
    self.relative = 0
    self.address = 0
    self.segment = 0

class constant_operand(operand):
  def __init__(self, value, size=4):
    self.value = value
    self.size = size
    pass

INST_MATH = 0
INST_DATA = 1
INST_FLOW = 2
INST_MISC = 3

class instruction:
  def __init__(self):
    self.size = 0
    self.type = ""
    self.address = 0
    self.operands = []
    self.result = [] #changes made to state by instructions, these are described by math

class operation:
  def __init__(self,*ops,**vals):
    signed = 1
    if 'signed' in vals:
      signed = vals['signed']
    operands = ops
    #blah blah, figure out how to deal with signedness
    #deal w/ known operators here

###### data instructions

#moves register to memory and back
class load(instruction):
  def __init__(self, dest_op, src_op):
    pass

class store(instruction):
  def __init__(self, dest_op, src_op):
    pass
    
###### flow instructions
class jump(instruction):
  def __init__(self, op):
    #destination = op
    pass

class branch_true(instruction):
  def __init__(self, op):
    pass

class branch_false(instruction):
  def __init__(self,  op):
    pass

#######function abstractions
#build an activation record
class call(instruction):
  def __init__(self, op):
    pass

#collapse an activation record
class ret(instruction):
  def __init__(self, op):
    pass
##########################
#heap abstractions
#stack abstractions

