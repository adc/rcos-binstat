"""
TODO redo bitmin/bitmax gunk

probably rewrite this entire mess
"""
import graphs
import struct
import util

import ir

class undefined_value:
  def __init__(self, name):
    """docstring for __init__"""
    self.name = name
    self.type = 'undefined_value'
  
  def __str__(self):
    return self.__repr__()
  
  def __repr__(self):
    return "(undefined_%s)"%self.name

  def eval(self):
    return []

class address_value:
  def __init__(self, addr_value, bitmin, bitmax):
    self.value = addr_value
    self.bitmin = bitmin
    self.bitmax = bitmax
  def __str__(self):
    return "addr_[%s]"%str(self.value)
  def __repr__(self):
    return self.__str__()
  

class ssa_symbol:
  def __init__(self, name, bitmin, bitmax):
    """docstring for __init__"""
    self.name = name
    self.bitmin = bitmin
    self.bitmax = bitmax
    #values is a dictionary that goes (addr, aux_loc) : [states]
    self.values = { (0,0): [undefined_value(self.name)]}
    self._last_address = (0,0)
  
  def __vals_by_addr(self):
    keys = self.values.keys()
    keys.sort(reverse=True)
    for k in keys:
      yield k
    
  def get_values(self, address=None, aux_loc=0):
    """returns a list of possible values for a variable; 
       a value is None if it could not be resolved"""
    states = self.get_states(address, aux_loc)
    output = []

    for s in states:
      if isinstance(s, ssa_state):
        output += s.eval()
      else:
        output += [s]
    
    return output

  def get_states(self, address=None, aux_loc=0):
    """returns a list of possible states for a variable"""

    
    if not address:
      #get most recent
      return self.values[self._last_address]

    #print "GET %x:%d"%(address,aux_loc)

    ######XXX careful w/ off by ones here.
    for (entry_addr, entry_aux_loc) in self.__vals_by_addr():
      if address >= entry_addr:
        #if
        if address == entry_addr and entry_aux_loc >= aux_loc: 
          continue
        #print "GOT %x:%d"%(entry_addr, entry_aux_loc)
        ret = self.values[(entry_addr, entry_aux_loc)]
        return ret

    raise Exception("shouldn't reach here since every symbol at least has the undefined entry...")
    return []
    
    
  def update(self, states, address, aux_loc = 0):
    """update sets a new value for a variable after address"""
    #print 'updating %s @ %x:%d  w/ %s'%(self.name, address,aux_loc,str(states))

    if (address, aux_loc) in self.values:
      #check if an additional state needs to be added
      entry = self.values[(address, aux_loc)]
      for state in states:
        if state not in entry:
          entry.append(state)
          for n in entry:
            #remove undefined if its there
            if isinstance(n, undefined_value):
              entry.remove(n)
    else:
      self.values[(address, aux_loc)] = states
      if (address, aux_loc) > self._last_address:
        self._last_address = (address, aux_loc)
        
  def clear(self, address, aux_loc = 0):
    """clear a symbol after an address, setting it back to undefined"""
    #print 'updating %s @ %d:%d  w/ %s'%(self.name, address,aux_loc,str(states))

    self.values[(address, aux_loc)] = [undefined_value(self.name)]

    if (address, aux_loc) > self._last_address:
      self._last_address = (address, aux_loc)
        

class ssa_state:
  def __init__(self, address, aux_loc):
    self.address, self.aux_loc = address, aux_loc
    #TODO self.bitmin, self.bitmax = bitmin, bitmax
    self.expression = []
  
  def __cmp__(self, b):
    #print 'cmp called on %x:%d'%(self.address,self.aux_loc)
    #return 1
    if isinstance(b, ssa_state):
      if self.expression == b.expression:
        return 0
    return 1
  
  def eval_helper(self):
    """returns a list of possibilities to be eval'd
      Here be dragons :("""
    rets = [""]

    for e in self.expression:
      if isinstance(e, ssa_symbol):
        vals = e.get_states(self.address, self.aux_loc)          
        if id(self) in [id(x) for x in vals]:
          print e, e.name
          q = vals.index(self)
          raise Exception("RECURSIVE REFERENCE. the state at <%x:%d> has symbols which references itself <%x:%d>"%(self.address, self.aux_loc, vals[vals.index(self)].address, vals[vals.index(self)].aux_loc ))
        #TODO::: mark that there are unresolved states...\n
        new_ = []
        for i in range(len(rets)):
          for v in vals[1:]:
            #if isinstance(v, list):
            #  #for n in v:
            if isinstance(v, ssa_state):
              new_ += ['%s'%(rets[i] + x) for x in v.eval_helper()]
            else:
              new_.append( rets[i] + '%s'%v)
          if isinstance(vals[0], ssa_state):
            new_strings = vals[0].eval_helper()
            new_ += [rets[i] + x for x in new_strings[1:]]
            rets[i] += new_strings[0]
          else:
            rets[i] += str(vals[0])
        rets += new_

      else:
        for i in range(len(rets)):
          rets[i] +=str(e)

    return ['(%s)'%x for x in rets]
  
  def __repr__(self):
    return '%s'%', '.join("(%s)"%x for x in self.eval_helper()) 
    
  def eval(self):
    #print "\nasked to eval ourself @ %d:%d...\n"%(self.address, self.aux_loc)
    rets = self.eval_helper()
    
    values = []
    for string in rets:
      try:
        values.append( eval(string) )
      except:
        #TODO:: mark failure
        values.append(None)
    return values

  def copy(self):
    """Return a new instance of this state"""
    n = ssa_state(self.address, self.aux_loc)
    n.expression = self.expression
    return n
    
    
def translate_ops(SYMS, ops, address, aux_loc=0):
  """returns a state or primitive representing an operation"""
  symbolic = False

  ret = ssa_state(address, aux_loc+1)
  curstr = ""
  
  for op in ops:
    if isinstance(op, ir.register_operand):
      symbolic = True
      ret.expression.append(SYMS[str(op.register.register_name)])
    else:
      ret.expression.append(op)
      curstr += str(op)
  #def __init__(self, address, aux_loc, bitmin, bitmax):
  
  if not symbolic:
    #try to evaluate it.
    try:
      return eval(curstr)
    except:
      pass
  #print 'return',ret
  return ret







###### code that actually operates on the IR
def propagate_intra_block_values(arch, callgraph, bin):

  sg = callgraph.keys()
  sg.sort()

  constant_regs = arch.get_analysis_constant_regs(bin)

  for r in arch.registers:
    if "stack" in r.aliases:
      stack_reg = r
    elif "pc" in r.aliases:
      pc_reg = r


  for func in sg:
    for block in callgraph[func]:
      ssa_track = {}
      for r in arch.registers:
        ssa_track[str(r.register_name)] = ssa_symbol(str(r.register_name),
                                                    r.bitmin, r.bitmax)
      for reg in constant_regs:
        ssa_track[str(reg.register_name)].update([constant_regs[reg]], 0)
      
      aux_loc = 0
      for instr in block.code:
        addr_value = ir.constant_operand(instr.address, pc_reg.size)
        ### use -1 as aux_loc, this means that at 0 onwards 
        #### the value is x.
        ssa_track[str(pc_reg.register_name)].update([addr_value], instr.address, -1)

        if instr.type == 'operation':
          if len(instr.ops) > 2:
            if instr.ops[1] == '=':
              #update on assignment
              if instr.ops[0].register in constant_regs:
                pass
              elif instr.ops[0].register == pc_reg:
                print "HUH? write to pc reg???"
              else:
                reg_op = instr.ops[0]
                value = translate_ops(ssa_track, instr.ops[2:], instr.address, aux_loc)

                reg_name = reg_op.register.register_name
                #aux_loc + 1 since it will be valid __after this assignment
                ssa_track[reg_name].update([value], instr.address, aux_loc+1)
                #                           reg_op.bitmin, reg_op.bitmax)

        elif instr.type == 'load':
          #update on load
          src_addrs = ssa_track[str(instr.src.register_name)].get_states()
          for src_addr in src_addrs:
            value = address_value(src_addr, 0, instr.src.size*8)

            if isinstance(src_addr, int):
              addr = src_addr
              if addr in bin.memory and addr+instr.size in bin.memory:
                sizemap = {1: 'B', 2: 'H', 4: 'L', 8: 'Q'}
                value = struct.unpack(arch.endianness+"%s"%sizemap[instr.size], bin.memory.getrange(addr, instr.size+addr))[0]

            reg_op = instr.dest
            if isinstance(reg_op, ir.register_operand):
              reg_name = str(reg_op.register.register_name)
              ssa_track[reg_name].update([value], 
                                        instr.address,block.code.index(instr)) 
              #                           reg_op.bitmin, reg_op.bitmax)

        elif instr.type == "store":
          pass
        elif instr.type == "call":
          #invalidate registers based on calling conventions.
          for x in arch.call_clobber:
            reg_name = str(x.register_name)
            ssa_track[reg_name].update([undefined_value(reg_name)],
                                      instr.address,block.code.index(instr)
                                      )
        aux_loc += 1
      block.ssa_vals = ssa_track

  