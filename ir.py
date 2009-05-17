"""
Lieutenant Dan:   I'm here to try out my sea legs.
Forrest Gump:     But you ain't got no legs, Lieutenant Dan

This module contains IR abstractions for anything IR. 


TODO
  clean up register aliasing

  number representation issues galore:
    endianess isnt payed attention too much in here
      decide if this should be the role of the IR or not
    signedness
    sizes and truncation

    
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
    if addr >= self.start+self.base and addr < self.end+self.base:
      return True
    return False

  def __getitem__(self, addr):
    if addr > self.end+self.base or addr < self.start+self.base:
      raise IndexError("memory address out of range: %x"%addr)
    return self.data[addr - self.start + self.base]

  def __getslice__(self, start, stop):
    if start > self.end+self.base or start < self.start + self.base \
     or stop > self.end+self.base or stop < self.start + self.base:
      print "%x %x"%(self.start, self.end)
      raise IndexError("memory address out of range %x-%x"%(start,stop))
    return self.data[start-self.start+self.base: stop-self.start+self.base]

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


class operand:
  def __init__(self, t):
    self.type = t
    self.size = 0

class alias_name:
  def __init__(self, names):
    self.names = names

  def __cmp__(a, b):
    for x in a.names:
      if x == b:
        return 0
    return 1

  def __repr__(self):
    return self.names[0]

  def __str__(self):
    return self.__repr__()

class register:
  def __init__(self, *names, **var):
    #ir.register("eax:32-0", "ax:16-0", "ah:16-8", "al:7-0")
    self.aliases = {}
    self.callee_save = 0
    self.register_name = names[0]
    if ':' in self.register_name:
      self.register_name = self.register_name[:self.register_name.find(':')]
    if 'size' in var:
      self.size = var['size']
    if 'callee_save' in var:
      self.callee_save = 1
    
    #find bounds
    upper = 0
    lower = 1000
    for name in names:
      if ':' not in name:
        continue
      else:
        if '-' in name:
          top, bottom = name[name.find(":")+1:].split('-')
        else:
          top = bottom = name[name.find(':')+1:]
        top = int(top)
        bottom = int(bottom)
        if top > upper:
          upper = top
        if bottom < lower:
          lower = bottom

    self.bitmax = upper
    self.bitmin = lower

    for name in names:
      if ':' in name:
        if '-' in name:
          top, bottom = name[name.find(":")+1:].split('-')
        else:
          top = bottom = name[name.find(':')+1:]
        top = int(top)
        bottom = int(bottom)
        name = name[:name.find(':')]
      else:
        #assume full register
        top = self.bitmax
        bottom = self.bitmin
        
      self.aliases[name] = {'min': bottom, 'max': top, 'name': name}
    
    self.size = self.bitmax/8

  def __contains__(self, name):
    return name in self.aliases.keys()
    
  """
  TODO: register aliasing. on x86 the register
  rax is the 64-bit version. and eax, ax, ah, 
  and al are aliases for portions of it.
  This poses some design issues for a translator.
  """
  
  
class register_operand(operand):
  def __init__(self, name, register):
    operand.__init__(self,"register")
    self.register = register
    self.bitmin = register.aliases[name]['min']
    self.bitmax = register.aliases[name]['max']
    self.size = (self.bitmax-self.bitmin)/8
    #pull out all registers with the same size
    reglist = register.aliases.keys()
    xlist = []
    for y in reglist:
      if register.aliases[y]['min'] == self.bitmin and register.aliases[y]['max'] == self.bitmax:
        xlist.append(y) 

    xlist = [name] + xlist
    self.register_name = alias_name(xlist)
  
  def __repr__(self):
    return repr(self.register_name)
  
  def __cmp__(a,b):
    if type(b) == type(a):
      if a.register == b.register:
          return 0
    return 1

class mem_operand(operand):
  def __init__(self, address):
    operand.__init__(self, "memory")
    self.relative = 0
    self.address = address
    self.segment = 0

class constant_operand(operand):
  def __init__(self, value, size=4, signed=1):
    operand.__init__(self, "constant")
    self.size = size
    self.signed = signed
    #todo: exceptions on overflows?
    
    #this is all to deal w/ pythons number representation vs registers
    #1) truncate to make sure it fits in 'size' bytes
    value = value & ((256**size)-1)

    if signed:
      #2) check for > max positive value
      if value >= (256**size)/2:
        value = -(256**size - value)
    self.value = value

  def __repr__(self):
    return str(self.value)

def sext16(value):
  if value & 0x8000:
    return value + 0xffff0000
  return value

INST_MATH = 0
INST_DATA = 1
INST_FLOW = 2
INST_MISC = 3

class instruction:
  def __init__(self, t):
    self.size = 0
    self.type = t
    self.address = 0
    self.operands = []
    self.result = [] #changes made to state by instructions, these are described by math
    self.annotation = ""

class operation(instruction):
  def __init__(self,*ops,**vals):
    instruction.__init__(self, "operation")
    signed = 1
    if 'signed' in vals:
      signed = vals['signed']
    self.ops = ops
    #blah blah, figure out how to deal with signedness
    #deal w/ known operators here
  
  def __repr__(self):
    return repr(self.ops)+"     "+self.annotation


###### misc instructions

class unhandled_instruction(instruction):
  def __init__(self, data):
    instruction.__init__(self, "unhandled")
    self.value = data
  def __repr__(self):
    return "UNHANDLED-> %s"%self.value

class native_instruction(instruction):
  def __init__(self, native):
    instruction.__init__(self, "native")
    self.value = native

  

###### data instructions

#moves register to memory and back

class load(instruction):
  """[source_reg mem address] -> dest_reg"""
  def __init__(self, src_op, dest_op, size=4, signed=1):
    instruction.__init__(self, "load")
    self.signed = signed
    self.size = size
    self.dest = dest_op
    self.src = src_op
  
  def __repr__(self):
    return "LOAD %s <- %s"%(self.dest, self.src)+"     "+self.annotation
    
class store(instruction):
  """source_reg -> [dest reg mem address]"""
  def __init__(self, src_op, dest_op, size=4, signed=1):
    instruction.__init__(self, "store")
    self.signed = signed
    self.size = size
    self.dest = dest_op
    self.src = src_op

  def __repr__(self):
    return "STORE %s -> %s"%(self.src, self.dest)+"     "+self.annotation

    
###### flow instructions and abstractions
class jump(instruction):
  def __init__(self, op, relative=False):
    #destination = op
    instruction.__init__(self, "jump")
    self.relative = relative
    self.dest = op
  
  def __repr__(self):
    if isinstance(self.dest, constant_operand):
      if self.relative:
        return "JUMP loc_%x"%(self.dest.value+self.address)+"     "+self.annotation      
      else:
        return "JUMP loc_%x"%self.dest.value+"     "+self.annotation
    else:
      return "JUMP %s"%repr(self.dest)+"     "+self.annotation
      
    
class branch_true(instruction):
  def __init__(self, op, relative=1):
    instruction.__init__(self, "branch_true")
    self.relative = relative
    self.dest = op
  
  def __repr__(self):
    if self.relative:
      mask = 0xffffffff
      #if self.dest.signed:
      #  mask = 0x7fffffff
      return "BRANCH loc_"+hex((self.dest.value+self.address) & mask)+"     "+self.annotation
    else:
      return "BRANCH loc_"+hex(self.dest.value)+"     "+self.annotation

#######function abstractions
#build an activation record
class call(instruction):
  def __init__(self, op, relative=1):
    instruction.__init__(self, "call")
    self.dest = op
    self.relative = relative

  def __repr__(self):
    if isinstance(self.dest, constant_operand):
      if self.relative:
        return "CALLR loc_"+hex(int(repr(self.dest))+int(repr(self.address)))+"     "+self.annotation
      else:
        return "CALL loc_"+hex(self.dest.value)+"     "+self.annotation
    else:
      return "CALL %s"%self.dest+"     "+self.annotation

class library_function(operand):
  def __init__(self, address, name):
    operand.__init__(self, "function")
    self.address = address
    self.name = name
    #todo return value and such
  
#collapse an activation record
class ret(instruction):
  def __init__(self, op):
    instruction.__init__(self, "ret")
    self.dest = op
    self.annotation = str(op)

  def __repr__(self):
    return "RET"+"     "+self.annotation
##########################
#heap abstractions

class allocate_heap(instruction):
  def __init__(self, size):
    instruction.__init__(self, "alloc_heap")

class free_heap(instruction):
  def __init__(self, size):
    instruction.__init__(self, "free_heap")

#stack abstractions
class allocate_stack(instruction):
  def __init__(self, size):
    instruction.__init__(self, "alloc_stack")

class collapse_stack(instruction):
  def __init__(self, size):
    instruction.__init__(self, "free_stack")

class push(instruction):
  def __init__(self, op):
    instruction.__init__(self, "push")
    self.src = op

class pop(instruction):
  def __init__(self, op):
    instruction.__init__(self, "pop")
    self.dest = op