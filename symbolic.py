"""
Symbolic thinking happens here.
The goal is to lay down abstractions for constraint solving
and model building. 
"""

class Variable:
  """A variable is a set of symbols"""
  def __init__(self):
    self.value = None
  
  def set(self, symbol):
    """set initializes to one possible symbol"""
    self.value = [symbol]
  
  def assign(self, symbol):
    """assign inserts an additional symbol to the possible values"""
    if symbol:
      if self.value is None:
        self.value = [symbol]
      else:
        self.value.append(symbol)
    else:
      self.value = None
  
  def get(self):
    if self.value is None:
      return
    
    for s in self.value:
      yield s


class Symbol:
  def __init__(self, size, type='void'):
    self.size = size
    self.type = type
    self.value = 'undefined'

Void = Symbol
  
class Integer(Symbol):
  def __init__(self, size):
    Symbol.__init__(self, size, type='integer')
    self.value = 0

class Pointer(Symbol):
  def __init__(self, size, type='void'):
    Symbol.__init__(self, type, size)
    self.value = 0



def get_ssa(last_reg_write, ssa_history, dest):
  if dest.type == 'register':
    reg_name = dest.register.register_name
    if last_reg_write[reg_name]:
      return ssa_history[last_reg_write[reg_name]]
    else:
      return reg_name
  else:
    return ""

def make_ssa_like(last_reg_write, ssa_history, ops):
  outstring = ""

  for op in ops:
    if type(op) is str:
      outstring += ' %s '%op
    elif op.type == 'constant':
      outstring += " %d "%op.value
    elif op.type == 'register':
      reg_name = op.register.register_name
      if last_reg_write[reg_name]:
        outstring += '('+ssa_history[last_reg_write[reg_name]]+')'
      else:
        outstring += reg_name
    else:
      print "UNKNOWN OP TYPE",op, op.type, ops
    
  try:
    outstring = "%d"%eval(outstring)
  except:
    pass
      
  return outstring

def eval_with_reg_sub(register, string):
  eval_str = string.replace("%s &  -16 "%register.register_name, "0")
  eval_str = eval_str.replace(register.register_name, "0")

  try:
    return eval(eval_str)
  except:
    return None