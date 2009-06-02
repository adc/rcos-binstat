"""
TODO clean up bitmin/bitmax gunk

probably rewrite this entire mess
"""
import graphs
import struct
import util

import ir


class undefined_value:
  def __init__(self, name):
    self.name = name
  def __str__(self):
    return 'undefined_'+str(self.name)
  def __repr__(self):
    return self.__str__()
  def __cmp__(a,b):
    if isinstance(b, undefined_value):
      return self.name.__cmp__(b.name)
    return 1

class address_value:
  def __init__(self, addr_value, bitmin, bitmax):
    self.value = addr_value
    self.bitmin = bitmin
    self.bitmax = bitmax
  def __str__(self):
    return "addr_[%s]"%str(self.value)
  def __repr__(self):
    return self.__str__()
    
import copy

class state:
  def __init__(self, expression=None):
    self.expression = []
    if expression is not None:
      self.expressions.append(expression)
      
    self.__getitem__ = self.expressions.__getitem__
    self.__len__ = self.expressions.__len__
  
  def eval(self):
    try:
      return eval(self.__str__())
    except:
      return None
      
  def __str__(self):
    if is instance(self.expression, list):
      return '('+"".join(str(x) for x in self.expressions)+')\n'[:-1]
    else:
      return '(%s)'%str(self.express)

  def __repr__(self):
    return self.__str__()

class ssa_symbol:
  def __init__(self, name, size, bitmin, bitmax):
    self.name = name
    self.size = size
    self.bitmin = bitmin
    self.bitmax = bitmax
    self.location = 0
    self.aux_loc = 0
    self.states = []
    
    self.parent = None
  
  def __str__(self):
    return str(self.get_values())
  
  def comes_before(self, addr, aux_loc):
    if addr > self.location:
      return 1
    elif addr == self.location:
      if aux_loc > self.aux_loc:
        return 1
    return 0
  
  def is_same_place(self, addr, aux_loc):
    return self.location == addr and aux_loc == self.aux_loc

  def get_evals(self):
    o = []
    for e in self.expressions:
      try:
        o.append(eval(str(e)))
      except:
        o.append(e)
    return o
    
  def get_values(self, location=None, aux_loc=None):
    if not location:
      return self.expressions
    
    if self.comes_before(location,aux_loc):
      return self.expressions
    
    if self.parent:
      return self.parent.get_values(location, aux_loc)
    raise Exception("LOST HEAD!")
  
  def update(self, expr, location, aux_loc):
    if self.comes_before(location,aux_loc):
      #print "new update", self.name, expr, location, aux_loc, 'vs', self.location, self.aux_loc
      #update is newer than current symbol
      #push current data back
      
      #copy to old obj
      old = ssa_symbol(self.name, self.size, self.bitmin, self.bitmax)
      old.location = self.location
      old.aux_loc = self.aux_loc
      old.expressions = self.expressions
      old.parent = self.parent      
      
      #make new data
      self.expressions = ssa_expression(expr)
      self.location = location
      self.aux_loc = aux_loc
      self.parent = old
    elif self.is_same_place(location, aux_loc):
      #print "pushing another value at the same location"
      self.expressions.push(expr)
    else:
      #print "retroactive update"
      #update is retroactive
      #pass data long to parent..
      if self.parent:
        self.parent.update(expr, location, aux_loc)
      else:
        #create it as a parent
        parent = ssa_symbol(self.name, self.size, self.bitmin, self.bitmax)
        parent.location = location
        parent.aux_loc = aux_loc
        parent.expressions = expr
        

def resolve_ssa(symbols, ops, location=None):
  result = ssa_expression()
  for op in ops:
    if isinstance(op, ir.register_operand):
      reg_name = str(op.register.register_name)
      result.push(symbols[reg_name])
    else:
      result.push(op)
  return ssa_expression(result)

    