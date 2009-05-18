try:
  from macholib.MachO import MachO
  import macholib
except ImportError:
  macholib = None
import struct

CPU_TYPE_X86 = 7
READ = 1; WRITE = 2; EXEC = 4

SEGMENT_COMMAND = macholib.mach_o.segment_command
THREAD_COMMAND = macholib.mach_o.thread_command
SYMTAB_COMMAND =macholib.mach_o.symtab_command
DYSYMTAB_COMMAND = macholib.mach_o.dysymtab_command 

N_EXT = macholib.mach_o.N_EXT


class macho:
  def __init__(self, filename):
    if not macholib:
      raise Exception("Missing MachO")

    self.filename = filename
  
    fat = MachO(filename)
    self.macho_header = None
    for arch in fat.headers:
     if arch.header.cputype == CPU_TYPE_X86:
       self.macho_header = arch
       self.offset = arch.offset
       break
    if not self.macho_header:
     raise Exception("Couldn't find x86 header")

  def read(self):
    return open(self.filename).read()[self.offset:self.offset+self.macho_header.size]

#struct nlist {
#	union {
##ifndef __LP64__
#		char *n_name;	/* for use when in-core */
##endif
#		int32_t n_strx;	/* index into the string table */
#	} n_un;
#	uint8_t n_type;		/* type flag, see below */
#	uint8_t n_sect;		/* section number or NO_SECT */
#	int16_t n_desc;		/* see <mach-o/stab.h> */
#	uint32_t n_value;	/* value of this symbol (or stab offset) */
#};
#
class macho_symbol:
  def __init__(self, data=0, n_type=0, n_sect=0, n_desc=0, n_value=0, strname=""):
    if type(data) is str:
      self.load(data)
    else:
      self.n_strx = data
      self.n_type = n_type
      self.n_sect = n_sect
      self.n_desc = n_desc
      self.n_value = n_value
      self.strname = strname

  def load(self, data):
    self.n_strx, self.n_type, self.n_sect, self.n_desc, \
      self.n_value = struct.unpack("<LBBHL", data)
  
  def set_name(self, strname):
    self.strname = strname
    
  def dump(self):
    return struct.pack("<LBBHL", self.n_strx, self.N_type, self.n_sect, 
                                self.n_desc, self.n_value)


def getascii(string, offset):
  if offset < len(string):
    return string[offset: string.find("\x00", offset)]
  return ""
  
def macho_resolve_external_funcs(target):
  
  dysymtab = None
  symtab = None
  jumptable_base = 0
  
  for cmd in target.binformat.commands:
    if type(cmd[1]) == SYMTAB_COMMAND:
      symtab = cmd
    elif type(cmd[1]) == SEGMENT_COMMAND:
      if cmd[1].segname[:8] == "__IMPORT":
        for sect in cmd[2]:
          if sect.sectname[:12] == "__jump_table":
            jumptable_base = sect.addr
            
            start_index = sect.reserved1
            stub_size = sect.reserved2
            
    elif type(cmd[1]) == DYSYMTAB_COMMAND:
      dysymtab = cmd[1]

  if not dysymtab or not symtab or jumptable_base == 0:
    return {}
  
  symtab = symtab[1]
  
  string_table = target.data[symtab.stroff:symtab.stroff+symtab.strsize]
  count = 0 
  
  symbols = []
  
  for i in range(symtab.symoff, symtab.symoff+symtab.nsyms*12, 12):
    sym = macho_symbol(target.data[i:i+12])
    name = getascii(string_table, sym.n_strx)
    sym.strname = name
    symbols.append(sym)

  #read indirect symbol table
  indirect_indexes = struct.unpack('<'+'L'*dysymtab.nindirectsyms, 
      target.data[dysymtab.indirectsymoff:dysymtab.indirectsymoff+dysymtab.nindirectsyms*4])

  functions = {}
  
  for index in indirect_indexes[start_index:]:
    if index in [0x40000000, 0x80000000]:
      pass
    elif index < len(symbols):
      addr = jumptable_base + stub_size*count
      functions[addr] = symbols[index].strname
    else:
      print "[-] ERR ON:: macho indirect symbol out of range", index
    count += 1
  
  return functions
