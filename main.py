import elf
import ir
import graphs

try:
  from macholib.MachO import MachO
  import macholib
except:
  macholib = None
  
class Binparser:
  def __init__(self, filename):
    self.filename = filename
    self.binformat = None
    self.data = ""
    self.memory = ir.memory()

    self.parse()    
    self.entry_points = self.find_entry_points()

  def parse(self):
    data = open(self.filename).read()
    self.data = data

    if "ELF" in data[:4]:
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
    elif "\xca\xfe\xba\xbe" in data[:4]:
      if not macholib:
        raise Exception("Missing MachO")
      CPU_TYPE_X86 = 7
      READ = 1; WRITE = 2; EXEC = 4
      
      self.data = open(self.filename,'rb').read()
      fat = MachO(self.filename)

      macho_header = None
      for arch in fat.headers:
       if arch.header.cputype == CPU_TYPE_X86:
         macho_header = arch
         break
      if not macho_header:
       raise Exception("Couldn't find x86 header")
      
      #only 386 for now
      self.architecture = "386"
      for cmd in macho_header.commands:
        if type(cmd[1]) == macholib.mach_o.segment_command:
          fake_start = cmd[1].fileoff
        if fake_start == 0:
          fake_start = cmd[1].vmaddr          
          seg = ir.segment(cmd[1].vmaddr, cmd[1].vmaddr+cmd[1].vmsize, 
               data[fake_start : fake_start + cmd[1].filesize], 
               cmd[1].initprot)
          if seg.prot & EXEC:
            seg.code = 1
        self.memory.add( seg )
        
      self.binformat = macho_header
      self.binformat.name = "macho"      
    else:
      raise Exception("- unknown binary format")
  
  def find_entry_points(self):
    if self.binformat.name == "ELF":
      return [self.binformat.e_entry]
    elif self.binformat.name == "macho":
      eip = None
      import struct
      for cmd in self.binformat.commands:
        if type(cmd[1]) == macholib.mach_o.thread_command:
          regs = struct.unpack("<LLLLLLLLLLLLLLLLLL",cmd[2])
          flavor, count = regs[:2]
          regs = regs[2:]

          eip = regs[10]
      del struct
      return [eip]
    else:
      return []

if __name__ == "__main__":
  import sys
  fn = sys.argv[1]
  bin = Binparser(fn)

  if bin.architecture == "MIPS":
    from mips_translator import MIPS_Translator
    mips = MIPS_Translator()
    mips.external_functions = elf.mips_resolve_external_funcs(bin)
    IR_rep = mips.translate(bin)
    
    mips.libcall_transform(IR_rep, bin)
  elif bin.architecture == "386":
    from x86_translator import X86_Translator    
    x86 = X86_Translator()
    IR_rep = x86.translate(bin)
  else:
    print "UNKNOWN ARCHITECTURE", bin.architecture
  
  graphs.make_flow_graph(IR_rep)
