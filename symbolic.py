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
