"""
TODO clean up bitmin/bitmax gunk

probably rewrite this entire mess
"""
import graphs
import struct
import util

import ir
import copy
# build expressions made up of
#   ir.mem_operand, ir.constant_operand, ir.math_operand,
#     and reg_holders




######## helpers for storing symbols
class undefined_value:
  def __init__(self, reg, bitmin=-1, bitmax=-1):
    self.type = 'undefined'
    if isinstance(reg, str):
      self.name = reg
      self.bitmin = bitmin
      self.bitmax = bitmax
    else:
      self.name = str(reg.register_name)
      self.bitmin = reg.bitmin
      self.bitmax = reg.bitmax
  
  def __repr__(self):
    return self.name+'[%d-%d]'%(self.bitmin,self.bitmax)

class address_value:
  def __init__(self, address, bitmin, bitmax):
    self.type = 'address'
    self.bitmin = bitmin
    self.bitmax = bitmax
    self.address = address #value_expression representing address
  
  def __repr__(self):
    return 'addr_{'+str(self.address)+'}[%d-%d]'%(self.bitmin,self.bitmax)
  
  
class value_expression:
  def __init__(self, value):
    self.expression = value
    
  def eval(self, **inputs):
    temp = []
    for e in self.expression:
      if isinstance(e, undefined_value):
        if e.name not in inputs:
          raise NameError("unknown variable:%s"%e.name)
        temp.append(inputs[e.name])
      elif isinstance(e, address_value):
        
        try:
          addr = e.address.eval(inputs)
        except NameError:
          raise NameError("Could not resolve address: %s"%e.address)

        if 'addr_'+str(addr) in inputs:
          temp.append(inputs[e.name])
        else:        
          raise NameError("Unknown value for address: %s"%addr)
        
      else:
        temp.append(e)
    
    return eval(value_expression(temp).dump_string())
    
  def get_unknowns(self):
    unknowns = []
    for val in self.expression:
      if isinstance(val, undefined_value):
        unknowns.append(val.name)
    return unknowns
    
  def simplify(self):
    pass
  
  def dump_string(self):
    return str(self)
  
  def __repr__(self):
    return str(self)

  def __str__(self):
    return '('+"".join([str(e) for e in self.expression]) + ')'
  
  def __cmp__(a, b):
    if isinstance(b,value_expression):
      return a.expression != b.expression
    return 1
  

def resolve_ssa(ssa_track, ops, location = None):
  outstring = ""
  
  #this explodes
  exprs = [[]]

  for op in ops:
    if type(op) is str:
      for expr in exprs:
        expr.append( ir.math_operand(op) )
    elif op.type == 'constant':
      for expr in exprs:
        expr.append(op)
    elif op.type == 'register':

      added_exprs = []
      
      for expr in exprs:
        reg_name = op.register.register_name  
        values = ssa_track[reg_name].get(location, op.bitmin, op.bitmax)
        
        if len(values) == 1:
          expr.append( values[0] )
        else:
          #need to make a copy of the expression for each additional possible value
          for i in range(1, len(values)):
            newexpr = copy.copy(expr)
            newexpr.append(values[i])
            added_exprs.append(newexpr)
            
          expr.append( values[0] )

      if added_exprs:
        exprs += added_exprs
          
    else:
      print "UNKNOWN OP TYPE",op, op.type, ops
    
  val = value_expression(expr)

  try:
    return val.eval()
  except:
    return val


#a symbol holds lists of possible values for a target
class ssa_symbol:
  def __init__(self, target, size, bitmin, bitmax):
    self.target = target
    self.names = []
    self.values = {}
    self.size = size
    self.bitmin = bitmin
    self.bitmax = bitmax

  def update(self, addr, aux, value, bitmin=0, bitmax=-1):
    #assumes updates happen sequentially
    # by address
    if bitmax == -1:
      bitmax = self.size * 8
    
    if bitmin != self.bitmin or bitmax != self.bitmax:
      #need point out the bit value here
      # to bitmask or to just :x ???
      pass
      
    ssa_name = self.target + '_'+str(addr) + "_"+ str(aux)    
    self.names = [(addr, ssa_name)] + self.names
    if ssa_name not in self.values:
      self.values[ssa_name] = [value]
    else:
      if value not in self.values[ssa_name]:
        print "APPENDING"
        for v in self.values[ssa_name]:
          print dir(v), v
        print dir(value), value
        self.values[ssa_name].append(value)
  
  def get(self, location=None, bitmin=None, bitmax=None):
    #find first valid address
    #names are in order of most recent assignment
    if bitmin is None:
      bitmin = self.bitmin
    if bitmax is None:
      bitmax = self.bitmax
    
    if location:
      for address, name in self.names:
        if location >= address:
          return self.values[name]
      
      return [undefined_value(self.target, bitmin, bitmax)]
    
    #otherwise return the most recent name
    if len(self.names) == 0:
      return [undefined_value(self.target, bitmin, bitmax)]
    else:
      return self.values[ self.names[0][1] ]











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
                                                    r.size, r.bitmin, r.bitmax)
      for reg in constant_regs:
        ssa_track[str(reg.register_name)].update(0,0,constant_regs[reg])
      
      for instr in block.code:
        addr_value = ir.constant_operand(instr.address, pc_reg.size)
        ssa_track[str(pc_reg.register_name)].update(instr.address,0, addr_value)
        
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
                reg_name = reg_op.register.register_name
                value = resolve_ssa(ssa_track, instr.ops[2:])
                
                
                ssa_track[reg_name].update(instr.address, block.code.index(instr), 
                                           value,
                                           reg_op.bitmin, reg_op.bitmax)
                  

        elif instr.type == 'load':
          #update on load
          for src_addr in ssa_track[str(instr.src.register_name)].get():
            value = address_value(src_addr, 0, instr.src.size*8)
          
            if isinstance(src_addr, int):
              addr = src_addr
              if addr in bin.memory and addr+instr.size in bin.memory:
                sizemap = {1: 'B', 2: 'H', 4: 'L', 8: 'Q'}
                value = struct.unpack(arch.endianness+"%s"%sizemap[instr.size], bin.memory.getrange(addr, instr.size+addr))[0]
                value = value_expression([value])
          
            reg_op = instr.dest
            if isinstance(reg_op, ir.register_operand):
              reg_name = str(reg_op.register.register_name)
              ssa_track[reg_name].update(instr.address,block.code.index(instr), 
                                         value,
                                         reg_op.bitmin, reg_op.bitmax)
              
        elif instr.type == "store":
          #memory destination...
          pass
        elif instr.type == "call":
          #invalidate registers based on calling conventions.
          for x in arch.call_clobber:
            reg_name = str(x.register_name)
            ssa_track[reg_name].update(instr.address,block.code.index(instr),
                                      undefined_value(x))

      block.ssa_vals = ssa_track



      