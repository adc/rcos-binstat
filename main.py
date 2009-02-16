import elf
import ir
import graphs

class Binparser:
  def __init__(self, filename):
    self.filename = filename
    self.binformat = None
    self.data = ""
    self.memory = ir.memory()

    self.parse()    
    self.entry_points = self.find_entry_points()

  def parse(self):
    data = open(fn).read()
    self.data = data

    if "ELF":
      kipler = elf.Elf(data)
      codesegments = []
      for s in kipler.Phdrs:
        if s.type == elf.PT_LOAD:
          seg = ir.segment(s.vaddr, s.vaddr+s.memsz,\
                      data[s.offset:s.offset+s.filesz] + "\x00"*(s.memsz-s.filesz),\
                      s.flags, s.flags)
          if s.flags & elf.PF_X:
            seg.code = 1
          self.memory.add(seg)

      if kipler.e_machine == elf.EM_MIPS:
        self.architecture = "MIPS"
      elif kipler.e_machine == elf.EM_386:
        self.architecture = "386"        

      self.binformat = kipler
  
  def find_entry_points(self):
    if self.binformat.name == "ELF":
      return [self.binformat.e_entry]
    else:
      return []


if __name__ == "__main__":
  import sys
  fn = sys.argv[1]
  bin = Binparser(fn)

  if bin.architecture == "MIPS":
    from mips_translator import MIPS_Translator    
    mips = MIPS_Translator()
    IR_rep = mips.translate(bin)

    for n in IR_rep:
      print hex(n.address) + ':    ' + repr(n)
    
  elif bin.architecture == "386":
    from x86_translator import X86_Translator    
    x86 = X86_Translator()
    IR_rep = x86.translate(bin)    
    graphs.make_flow_graph(IR_rep)
