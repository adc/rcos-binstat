import struct
"""
TODO:
  64-bit support.
"""
#et_type

ET_NONE = 0
ET_REL = 1
ET_EXEC = 2
ET_DYN = 3 
ET_CORE = 4
ET_NUM = 5 
ET_LOOS = 0xfe00
ET_HIOS = 0xfeff
ET_LOPROC = 0xff00
ET_HIPROC = 0xffff

#p_type
PT_NULL = 0
PT_LOAD = 1
PT_DYNAMIC = 2
PT_INTERP = 3
PT_NOTE = 4
PT_SHLIB = 5
PT_PHDR = 6
PT_TLS = 7
PT_NUM = 8
PT_LOPROC = 0x70000000
#...
#todo finish adding later
#PT_HIPROC

#p_flags
PF_X =  (1 << 0)
PF_W =      (1 << 1)
PF_R =       (1 << 2)
PF_PAGEEXEC     =(1 << 4)
PFF_NOPAGEEXEC  = (1<< 5)
PF_SEGMEXEC     =(1 << 6)
PF_NOSEGMEXEC   =(1 << 7)
PF_MPROTECT     =(1 << 8)
PF_NOMPROTECT   =(1 << 9)
PF_RANDEXEC     =(1 << 10)
PF_NORANDEXEC   =(1 << 11)
PF_EMUTRAMP     =(1 << 12)
PF_NOEMUTRAMP   =(1 << 13)
PF_RANDMMAP     =(1 << 14)
PF_NORANDMMAP   =(1 << 15)
PF_MASKOS       =0x0ff00000
PF_MASKPROC = 0xf0000000

SHN_UNDEF   =0
SHN_LORESERVE =  0xff00 
SHN_LOPROC = 0xff00     
SHN_BEFORE = 0xff00     
SHN_AFTER  = 0xff01     
SHN_HIPROC = 0xff1f     
SHN_LOOS   = 0xff20     
SHN_HIOS   = 0xff3f     
SHN_ABS    = 0xfff1     
SHN_COMMON = 0xfff2      
SHN_XINDEX = 0xffff      
SHN_HIRESERVE  = 0xffff 


# Legal values for sh_flags (section flags). 

SHF_WRITE      =  (1 << 0)
SHF_ALLOC      =  (1 << 1)   
SHF_EXECINSTR  =  (1 << 2)   
SHF_MERGE      =  (1 << 4)   
SHF_STRINGS    =  (1 << 5)   
SHF_INFO_LINK  =  (1 << 6)  
SHF_LINK_ORDER =  (1 << 7)   
SHF_OS_NONCONFORMING= (1 << 8)   
SHF_GROUP      =  (1 << 9)   
SHF_TLS        =  (1 << 10)  
SHF_MASKOS     =  0x0ff00000
SHF_MASKPROC   =  0xf0000000
SHF_ORDERED    =  (1 << 30)  
SHF_EXCLUDE  =    (1 << 31)

# Legal values for d_tag (dynamic entry type).  
DT_NULL     = 0
DT_NEEDED   =1  
DT_PLTRELSZ =2   
DT_PLTGOT   =3 
DT_HASH     =4 
DT_STRTAB   =5 
DT_SYMTAB   =6 
DT_RELA     =7 
DT_RELASZ   =8 
DT_RELAENT  =9 
DT_STRSZ    =10
DT_SYMENT   =11
DT_INIT     =12
DT_FINI     =13
DT_SONAME   =14
DT_RPATH    =15
DT_SYMBOLIC =16
DT_REL      =17
DT_RELSZ    =18
DT_RELENT   =19
DT_PLTREL   =20
DT_DEBUG    =21
DT_TEXTREL  =22
DT_JMPREL   =23
DT_BIND_NOW =24
DT_INIT_ARRAY  = 25  
DT_FINI_ARRAY  = 26
DT_INIT_ARRAYSZ= 27
DT_FINI_ARRAYSZ= 28
DT_RUNPATH  =29
DT_FLAGS    =30
DT_ENCODING= 32
DT_PREINIT_ARRAY =32
DT_PREINIT_ARRAYSZ =33
DT_NUM   =   34
DT_LOOS =    0x6000000d  
DT_HIOS=     0x6ffff000 
DT_LOPROC =  0x70000000
DT_HIPROC =  0x7fffffff
DT_PROCNUM  = 0x32 #DT_MIPS_NUM /* Most used by any processor */
#TODO finish ...

#SHT 
SHT_NULL = 0
SHT_PROGBITS = 1
SHT_SYMTAB = 2
SHT_STRTAB = 3
SHT_RELA = 4
SHT_HASH = 5
SHT_DYNAMIC = 6
SHT_NOTE = 7
SHT_NOBITS = 8
SHT_REL = 9
SHT_SHLIB = 10
SHT_DYNSYM = 11
SHT_INIT_ARRAY = 14
SHT_FINI_ARRAY = 15
SHT_PREINIT_ARRAY = 16
SHT_GROUP = 17
SHT_SYMTAB_SHNDX = 18
SHT_NUM = 19
SHT_LOOS = 0x60000000
SHT_GNU_LIBLIST = 0x6ffffff7
SHT_CHECKSUM = 0x6ffffff8
SHT_LOSUNW = 0x6ffffffa
SHT_SUNW_move = 0x6ffffffa
SHT_SUNW_COMDAT = 0x6ffffffb
SHT_SUNW_syminfo = 0x6ffffffc
SHT_GNU_verdef = 0x6ffffffd
SHT_GNU_verneed = 0x6ffffffe
SHT_GNU_versym = 0x6fffffff
SHT_HISUNW = 0x6fffffff
SHT_HIOS = 0x6fffffff
SHT_LOPROC = 0x70000000
SHT_HIPROC = 0x7fffffff
SHT_LOUSER = 0x80000000
SHT_HIUSER = 0x8fffffff


EM_NONE = 0
EM_M32 = 1
EM_SPARC = 2
EM_386 = 3
EM_68K = 4
EM_88K = 5
EM_860 = 7
EM_MIPS = 8
EM_S370 = 9
EM_MIPS_RS3_LE = 10


#symbol structures
class Elf32Dyn:
  def __init__(self, data, endianness="<"):
    self.d_tag, self.d_val = struct.unpack(endianness+"LL",data)
    self.d_ptr = self.d_val
class Elf32Rel:
  def __init__(self, data, endianness="<"):
    self.r_offset, self.r_info = struct.unpack(endianness+"LL", data)
class Elf32Rela:
  def __init__(self, data, endianness="<"):
    self.r_offset, self.r_info, self.r_addend = struct.unpack(endianness+"LLL", data)
    
class Elf32Sym:
  def __init__(self, data, endianness="<"):
    #print `data`
    self.st_name, self.st_value, self.st_size, self.st_info, self.st_other,\
    self.st_shndx = struct.unpack(endianness+"LLLBBH",data)

####### main structures
class Shdr:
    strname = "UNDEFINED"
    def __init__(self, name, type, flags, addr, offset, size, link, info, addralign, entsize, e="<"):
      self.endianness = e
      self.name = name
      self.type = type
      self.flags = flags
      self.addr = addr
      self.offset = offset
      self.size = size
      self.link = link
      self.info = info
      self.addralign = addralign
      self.entsize = entsize

    def dump(s):
        return struct.pack(self.endianness+"LLLLLLLLLL",\
                            s.name, s.type, s.flags, s.addr,\
                            s.offset, s.size, s.link, s.info,\
                            s.addralign, s.entsize)

class Phdr:
    def __init__(self, type, offset, vaddr, paddr, filesz, memsz, flags, align, e="<"):
        self.type = type
        self.offset = offset
        self.vaddr = vaddr
        self.paddr = paddr
        self.filesz = filesz
        self.memsz = memsz
        self.flags = flags
        self.align = align
        self.endianness=e

    def dump(s):
        return struct.pack(s.endianness+"LLLLLLLL",\
                            s.type, s.offset, s.vaddr, s.paddr,\
                            s.filesz, s.memsz, s.flags, s.align)
#    def __repr__(s):
#        out  =    "SEGMENT TYPE %s @ vaddr: %s paddr: %s"%(`s.type`,hex(s.vaddr),hex(s.paddr))
#        out += "\nflags: %s fsize: %d msize: %d"%(`s.flags`, s.filesz, s.memsz)
#        return out+"\n"

class Elf:  
  def __init__(self, file):
    self.name = "ELF"
    self.data = file
    self.loaded_shdrs = 0
    self.endianness = '<'
    
    if self.data[:4] != "\x7fELF":
      raise Exception("Not an ELF file (bad magic)")
    
    try:
      self.getEhdr()
      #auto detect endianness
      if self.is_big_endian(self.e_machine):
        self.endianness = '>'
        self.getEhdr()

      self.getPhdrs()
    except Exception, reason:
      print "Failed to get Ehdr and Phdrs:",reason
      raise Exception(reason)
    try:
      self.getShdrs()
      self.loaded_shdrs = 1
    except Exception,reason:
      print "Failed to get Shdr: %s"%reason

  def is_big_endian(self, machine_code):
    # little endian machine code is read
    # fun part is '8' big endian = 0x800 little endian
    #for now a safe bet is to check if it is not a 386
    if machine_code not in [EM_386]:
      return 1
    return 0

      
  def getEhdr(self):
    self.e_ident = self.data[:16]
    self.e_type, self.e_machine, self.e_version, self.e_entry,\
    self.e_phoff, self.e_shoff, self.e_flags, self.e_ehsize,\
    self.e_phentsize, self.e_phnum, self.e_shentsize, self.e_shnum,\
    self.e_shstrndx = struct.unpack(self.endianness+"HHLLLLLHHHHHH", self.data[16:52])
    

  def elfdump(s):
      return s.e_ident + struct.pack(self.endianness+"HHLLLLLHHHHHH",\
                                      s.e_type, s.e_machine, s.e_version, s.e_entry,\
                                      s.e_phoff, s.e_shoff, s.e_flags, s.e_ehsize,\
                                      s.e_phentsize, s.e_phnum, s.e_shentsize, s.e_shnum,\
                                      s.e_shstrndx)

  def readPhdr(self, data):
      p_type, p_offset, p_vaddr, p_paddr,\
      p_filesz, p_memsz, p_flags, p_align = struct.unpack(self.endianness+"LLLLLLLL",data)
      return Phdr(p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align, self.endianness)

  def getPhdrs(self):
      self.Phdrs = []
      i = self.e_phoff
      phsz = self.e_phentsize
      for n in range(0, self.e_phnum):
          self.Phdrs += [ self.readPhdr(self.data[i:phsz+i]) ]
          i += phsz

  def readShdr(self, data):
      sh_name, sh_type, sh_flags, sh_addr,\
      sh_offset, sh_size, sh_link, sh_info,\
      sh_addralign, sh_entsize = struct.unpack(self.endianness+"LLLLLLLLLL", data)
      return Shdr(sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize, self.endianness)

  def getShdrs(self):
      self.Shdrs = []
      i = self.e_shoff
      shsz = self.e_shentsize
      for n in range(0, self.e_shnum):
          self.Shdrs += [ self.readShdr(self.data[i:shsz+i]) ]
          i += shsz
      #and now add names
      if self.e_shstrndx != SHN_UNDEF:
          s = self.Shdrs[self.e_shstrndx]
          shstrtab = self.data[ s.offset: s.size+ s.offset ]
          for Shdr in self.Shdrs:
              strname = ""
              i = Shdr.name
              while shstrtab[i] != '\0':
                  strname += shstrtab[i]
                  i += 1
              Shdr.strname = strname


  def dump(self, filename): #
      #maintain main data BUT
      
      #new Ehdr
      ehdr = self.elfdump()

      #new Phdrs
      phdrs = ""
      for p in self.Phdrs:
          phdrs += p.dump()

      #new Shdrs
      if self.loaded_shdrs:
        shdrs = ""
        for e in self.Shdrs:
            shdrs += e.dump()

      #place ELF Header
      self.data = ehdr + self.data[len(ehdr):] 
      #place Program Headers
      self.data = self.data[:self.e_phoff] + phdrs + self.data[self.e_phoff + len(phdrs):]
      #place Section Headers
      if self.loaded_shdrs:
        self.data = self.data[:self.e_shoff] + shdrs + self.data[self.e_shoff + len(shdrs):]

      open(filename, "wb").write( self.data )

def pull_ascii(data, offset):
  o = ""
  while offset in data and data[offset] != "\x00":
    o += data[offset]
    offset += 1
  return o
###TODO: does mips have a jmprel or equiv? for sstrip'd binaries
def mips_resolve_symbols(bin):
  addr = 0
  for phdr in bin.binformat.Phdrs:
    if phdr.type == PT_DYNAMIC:
      addr = phdr.vaddr
      break

  strsz = None
  strtab = None
  symtab = None
  dthash = None
  Edyn = Elf32Dyn(bin.memory[addr:addr+8], bin.binformat.endianness)
  while Edyn.d_tag != DT_NULL:
    print hex(addr),'>>>>=    ',hex(Edyn.d_tag), hex(Edyn.d_val)
    if Edyn.d_tag == DT_STRTAB:
      strtab = Edyn.d_val
      print "STRTAB"
    elif Edyn.d_tag == DT_SYMTAB:
      symtab = Edyn.d_val
      print "SYMTAB", hex(symtab)
    elif Edyn.d_tag == DT_HASH:
      dthash = Edyn.d_val
      print "HASH"
    elif Edyn.d_tag == 10:
      strsz = Edyn.d_val
      print "STRSZ"
      
    addr += 8
    Edyn = Elf32Dyn(bin.memory[addr:addr+8], bin.binformat.endianness)
  
  addr = symtab+16
  Esym = Elf32Sym(bin.memory[addr:addr+16], bin.binformat.endianness)
  print Esym.st_name, Esym.st_value, Esym.st_size, Esym.st_info, Esym.st_other, Esym.st_shndx
  while Esym.st_name != 0:
    #self.st_name, self.st_value, self.st_size, self.st_info, self.st_other,\
    #self.st_shndx    
    print "=>>>>", pull_ascii(bin.memory, strtab+Esym.st_name), hex(Esym.st_size),\
                  hex(Esym.st_value), hex(Esym.st_info), hex(Esym.st_other), hex(Esym.st_shndx)
    addr += 16
    Esym = Elf32Sym(bin.memory[addr:addr+16], bin.binformat.endianness)
  
  print hex(addr)