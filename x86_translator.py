"""
first jab is 32-bit modes, x86 core.
"""
import ir
import struct
import parsex86
import graphs
import elf

X86DecodeTable = parsex86.get_decode_dict()

class InvalidInstruction(Exception): pass
class X86_Translator:
  
  def __init__(self, mode=32):
    self.registers = \
    [ ir.register("eax:32-0", "ax:16-0", "ah:16-8", "al:7-0"),
      ir.register("ebx:32-0", "bx:16-0", "bh:16-8", "bl:7-0"),
      ir.register("ecx:32-0", "cx:16-0", "ch:16-8", "cl:7-0"),
      ir.register("edx:32-0", "dx:16-0", "dh:16-8", "dl:7-0"),
      ir.register("esi:32-0", "si:16-0"),
      ir.register("edi:32-0", "di:16-0"),
      ir.register("ebp:32-0", "bp:16-0"),
      ir.register("esp:32-0", "sp:16-0", "stack"),
      ir.register("eip:32-0", "ip:16-0", "pc"),
      ir.register("eflags:32-0", "id:21", "vip:20", 
                  "vif:19", "ac:18", "vm:17",
                  "rf:16", "nt:14", "iopl:13-12", 
                  "of:11", "df:10", "if:9",
                  "tf:8", "sf:7", "zf:6", 
                  "af:4", "pf:2", "cf:0"),
      ir.register("tmem:32-0"),
      ir.register("tval:32-0")]
    self.mode = 32
    self.endianness = '<'
    
########### disassembler code   ####################
  def decodePrefix(self, bytes):      
    opsize   = {0x66: "opsize override"}      
    addrsize = {0x67: "addrsz override"}
    segments = {0x2e: "cs segment override",
                0x26: "es segment override",
                0x3e: "ds segment override",
                0x64: "fs segment override",
                0x65: "gs segment override",
                0x36: "ss segment override"}
    lock     = {0xf0: "lock"               }
    repeat   = {  0xf3: "rep",
                  0xf2: "repn"             }
    
    prefixes = [opsize, addrsize, segments, lock, repeat]
    # In 64-bit mode, the CS, DS, ES, and SS segment overrides are ignored. 
    
    #TODO: REX for 64-bit mode
    
    ret = []
    used_bytes = ""

    prefix_bytes = ""
    for x in bytes:
      z = ''
      for p in prefixes:
        if ord(x) in p:
          z = x
          break
      if not z:
        break
      prefix_bytes += z
    
    #make sure only one from each group has been selected
    ret = {}
    for p in prefixes:
      group = {}
      for b in prefix_bytes:
        if ord(b) in p:
          group[ord(b)] = p[ord(b)]
      if len(group.keys()) > 1:
        raise InvalidInstruction("bad prefix")
      ret.update(group)

    return prefix_bytes, ret


  def decode_opcode(self, data, mode):
    count = 1
    OP = ord(data[0])

    if OP not in X86DecodeTable:
      if OP & 0xf8 not in X86DecodeTable:
        raise InvalidInstruction("unknown opcode@: %x: %r"%(OP,data))
      else:
        if not X86DecodeTable[OP&0xf8]['instr'][mode][0]['modrm']:
          raise InvalidInstruction("unknown opcode@: %x: %r"%(OP,data))

        if '+' not in X86DecodeTable[OP&0xf8]['instr'][mode][0]['modrm']:
          raise InvalidInstruction("unknown opcode@: %x: %r"%(OP,data))

        instruction = X86DecodeTable[OP&0xf8]['instr'][mode][0]
        return 1, instruction

    
    node = X86DecodeTable[OP]

    while 'instr' not in node:
      data = data[1:]
      nextOP = ord(data[0])
      count += 1
      
      if nextOP not in node:
        raise InvalidInstruction("invalid opcode")
      
      node = node[nextOP]
    
    if mode not in node['instr']:
      raise InvalidInstruction("invalid opcode, missing mode")
    
    #check if multiple instructions are possible
    #if so, examine modrm bits for match
    if len(node['instr'][mode]) == 1:
      return count, node['instr'][mode][0]
    else:
      if not node['instr'][mode][0]['modrm']:
        return count, node['instr'][mode][0]
        print node['instr'][mode]
        print "HUUUHHH"        
      elif '+'  in node['instr'][mode][0]['modrm']:
        return count, node['instr'][mode][0]
      elif '/r' in node['instr'][mode][0]['modrm']:        
        return count, node['instr'][mode][0]
      else:
        peek_modrm = ord(data[1])
        OPbits = (peek_modrm >> 3) & 7        
        for x in node['instr'][mode]:
          if ('/%d'%OPbits) in x['modrm']:
            return count, x
        
        raise InvalidInstruction("unmatched OPbits in modrm")
      
    raise InvalidInstruction("No matches")
  
  
  def decode_operands(self, OP, instruction, data, mode):
    """
    OP -> opcode
    instruction -> dictionary w/ instruction data
    data -> bytes following opcode
    mode -> addressing mode (based on prefixes)
    """
    #helper functions
    def get_imm(sz, offset, data, signed=1):
      if sz == 1:
        return ir.constant_operand(ord(data[offset]), size=sz, signed=signed)
      elif sz == 2:
        return ir.constant_operand(struct.unpack('<H',data[offset:offset+2])[0], size=sz, signed=signed)
      elif sz == 4:
        return ir.constant_operand(struct.unpack('<L',data[offset:offset+4])[0], size=sz, signed=signed)
      else:
        print sz
        raise Exception("bad imm value")
    #####
    
    operands = []
    TMEM_IR = [] #IR translation for complex memory access
    
    reg_mem = None
    reg = None
    
    sib_displ = False
    sz = 0
    if not instruction['modrm'] or '+' in instruction['modrm']:
      reg = self.DR(OP & 7, mode)
    else: 
      #modrm looks like [mm][reg2][reg1]
      modrm = ord(data[sz]); sz += 1
      mod = modrm >> 6
      reg1 = modrm & 7
      reg2 = (modrm>>3)& 7
      Offset = None
      sib = None
      if mod != 3 and reg1 == 4:
        sib = ord(data[1])
        sz += 1

      #print 'modrm',mod
      if mod == 0:
        if reg1 == 5:
          #[displacement]
          TMEM_IR = [ir.operation(self.DR("TMEM",mode), '=', get_imm(mode/8, sz, data))]
          reg_mem = self.DR("TVAL", mode)
          sz += mode/8          
        else:
          #[reg1] -> store into temporary memory
          RegOne = self.DR(modrm & 7, mode)
          TMEM_IR = [ir.operation(self.DR("TMEM",mode),'=',RegOne)]
          reg_mem = self.DR("TVAL", mode)
      elif mod == 1:
        #[reg+ib]
        RegOne = self.DR(modrm & 7, mode)
        Offset = get_imm(1, sz, data)

        TMEM_IR = [ir.operation(self.DR("TMEM",mode),'=',RegOne,'+', Offset)]
        reg_mem = self.DR("TVAL", mode)
        sz += 1
      elif mod == 2:
        #[reg+mode_offset]
        RegOne = self.DR(modrm & 7, mode)
        Offset = get_imm(mode/8, sz, data)
        TMEM_IR = [ir.operation(self.DR("TMEM",mode),'=',RegOne,'+', Offset)]
        reg_mem = self.DR("TVAL", mode)
        sz += mode/8
      elif mod == 3:
        #reg + reg
        RegOne = self.DR(modrm & 7, mode)
        reg_mem = RegOne
    
      RegTwo = self.DR( (modrm >> 3)&7, mode)
      if sib:
        #redo TMEM_IR
        #ModRM with SIB: the reg field of the ModRM byte and the base and index fields of the SIB byte. 
        #(Case 3 in Figure1-3 on page15 shows an example of this). 
        #decode SIB
        #scale, index, base
        #[2][3][3]
        base = sib & 7
        index = (sib >> 3)&7
        scale = sib >> 6
        
        base_reg = None
        index_reg = None
        if base != 5:
          base_reg = self.DR(base, mode)
        else:
          sib_displ = True
          base_reg = reg_mem #displacement value
        if index != 4:
          index_reg = self.DR(index, mode)
        
        #base + index*scale + offset
        oplist = [self.DR("TMEM",mode),'=',]
        if base_reg:
          oplist.append(base_reg)
        if index_reg:
          if len(oplist):
            oplist += ['+', index_reg, '*', ir.constant_operand(2**scale)]
          else:
            oplist += [index_reg,'*', ir.constant_operand(2**scale)]
        if Offset:
          oplist += ['+',Offset]
          
        TMEM_IR = [ir.operation(*oplist)]

      reg = RegTwo
      
    Immediate = None
    if instruction['immediate']:
      #XXXX signedness
      strings = {'ib': 1, 'iw' : 2, 'id': 4, 'iq': 8}
      length = strings[instruction['immediate']]
      #if mode == self.mode/2:
      #  length /= 2
      Immediate = get_imm(length, sz, data)
      sz += length

    code_offset = None
    if instruction['code_offset']:
      strings = {'cb': 1, 'cw' : 2, 'cd': 4, 'cq': 8, 'm64': 8}
      length = strings[instruction['code_offset']]
      code_offset = get_imm(length, sz, data)
      sz += length

    mem_addr = None
    #check for memory offsets in operand ( MOV A3 opcode, etc)
    for oper in instruction['operands']:
      if 'moffset%d'%mode in oper:
        length = mode/8
        imm = get_imm(length, sz, data)
        mem_addr = self.DR("TVAL", mode)        
        TMEM_IR = [ir.operation(self.DR("TMEM",mode),'=', imm)]
        sz += length      

    #if sib had an immediate that didnt get picked up
    if sib_displ:
      if not mem_addr and not code_offset and not Immediate:
        length = self.mode/8
        Immediate = get_imm(length, sz, data)
        TMEM_IR[0].ops = tuple(list(TMEM_IR[0].ops) + ['+', Immediate])
        sz += length
        
    for oper in instruction['operands']:
      value = ""
      if 'reg/mem' in oper:
        value = reg_mem
      elif 'reg' in oper:
        value = reg
      elif 'moffset' in oper:
        value = mem_addr
      elif 'rel' in oper:
        if code_offset:
          value = code_offset
        else:
          value = Immediate
      elif 'imm' in oper:
        value = Immediate
      elif 'mem' in oper:
        value = reg_mem
      elif type(oper) == str:
        for y in ['EAX','AX','AL','DX']:
          if y in oper.upper():
            value = self.DR(y, mode)
            break
        
      elif 'EAX' in oper:
        value = self.DR('EAX', mode)
      elif 'AX' in oper:
        value = self.DR('AX', mode)
      elif 'AL' in oper:
        value = self.DR('AL', mode)
      else:
        print "XXX Hmmmm", oper
        
      operands.append((oper,value))
    
    return sz, operands, TMEM_IR
    
  def DR(self, index, mode=32):
    """Decode register based on register number and mode"""
    regdecode = {0: ['ah', 'al', 'ax', 'eax', 'rax'],
                 1: ['ch', 'cl', 'cx', 'ecx', 'rcx'],
                 2: ['dh', 'dl', 'dx', 'edx', 'rdx'],
                 3: ['bh', 'bl', 'bx', 'ebx', 'rbx'],
                 4: ['sp', 'sp', 'sp', 'esp', 'rsp'],
                 5: ['bp', 'bp', 'bp', 'ebp', 'rbp'],
                 6: ['si', 'si', 'si', 'esi', 'rsi'],
                 7: ['di', 'di', 'di', 'edi', 'rdi'],
                 8: ['', 'r8b', 'r8w', 'r8d', 'r8'],
                 9: ['', 'r9b', 'r9w', 'r9d', 'r9'],
                 10: ['', 'r10b', 'r10w', 'r10d', 'r10'],
                 11: ['', 'r11b', 'r11w', 'r11d', 'r11'],
                 12: ['', 'r12b', 'r12w', 'r12d', 'r12'],
                 13: ['', 'r13b', 'r13w', 'r13d', 'r13'],
                 14: ['', 'r14b', 'r14w', 'r14d', 'r14'],
                 15: ['', 'r15b', 'r15w', 'r15d', 'r15'],
                 }
   #TODO: segmentation registers
   #TODO in 64-bit esi/edi/ebp/esp gain low byte access w/ REX
    if type(index) == int:
      regmodes = {16: 2, 32: 3, 64: 4}
      regname = regdecode[index][regmodes[mode]]
    elif type(index) == str:
      regname = index.lower()
    else:
      raise InvalidInstruction("UNKNOWN DR index: %s"%repr(index))
      
    register = None
    for reg in self.registers:
      if regname in reg:
        register = reg
        break
    if not register:
      raise InvalidInstruction("Failed to decode register: %s"%regname)
    
    return ir.register_operand(regname, register)
  
  def makeIR(self, instruction, size, operands, TMEM_IR, OPmode, addr):
    """
    instruction -> dictionary of instruction information
    operands -> list of operand type and value
    TMEM_IR -> IR for complex memory access
    """
    
    #print "-----make IR ------"
    m = instruction['mnemonic']
    
    preload = False
    poststore = False
    #figure out if TMEM_IR is LOAD or STORE
    if TMEM_IR:
      #first operand is destination
      if 'reg/mem' in operands[0][0]:
        preload = True
        poststore = True
      elif 'reg/mem' in operands[1][0]:
        preload = True
      elif 'moffset' in operands[1][0]:
        preload = True

    IR = []
    if m == "ADC":
      IR = [ir.operation(operands[0][1],'=',operands[0][1],'+',operands[1][1],'+',self.DR("CF"))]
    elif m == "ADD":
      IR = [ir.operation(operands[0][1],'=',operands[0][1],'+',operands[1][1])]
    elif m == "AND":
      IR = [ir.operation(operands[0][1],'=',operands[0][1],'&',operands[1][1])]
    elif m == "CALL":
      if poststore:
        poststore = False

      IR = [ir.operation(self.DR("TVAL"),'=',self.DR("EIP"),"+",ir.constant_operand(size)),
            ir.operation(self.DR("ESP",OPmode),'=',self.DR("ESP"),'-',ir.constant_operand(4)),
            ir.store(self.DR("TVAL"),self.DR("ESP",OPmode))]
      
      #absolute jump vs relative jump
      if 'rel' in operands[0][0]:
        IR += [ir.operation(self.DR("tval"),'=',self.DR("EIP"),"+",operands[0][1],'+',ir.constant_operand(size)),
               ir.call(self.DR("tval"))
              ]
      else:
        IR += [ir.call(operands[0][1])]
      
      #controversial... analyzer must know callee _should_ do this
      #IR += [ir.operation(self.DR('esp'),'=',self.DR('esp'),'+',ir.constant_operand(4))]
      
    elif m == "CLC":
      IR = [ir.operation(self.DR("CF"), '=', ir.constant_operand(0))]
    elif m == "CLD":
      IR = [ir.operation(self.DR("DF"), '=', ir.constant_operand(0))]
    elif m == "CMP":
      if poststore:
        poststore = False
      IR = [ir.operation(operands[0][1],'-',operands[1][1])]
    elif m == "DEC":
      IR = [ir.operation(operands[0][1],'=',operands[0][1],'-',ir.constant_operand(1))]      
    elif m == "INC":
      IR = [ir.operation(operands[0][1],'=',operands[0][1],'+',ir.constant_operand(1))]      
    elif m == "IMUL":
      #XXXXX TODO FIX ME
      #EDX:EAX = a*b || 
      IR = [ir.operation(operands[0][1], '=', operands[0][1], '*', operands[1][1])]
      if operands[0][1].register_name == 'eax':
        #TODO SIZE
        IR += [ir.operation(self.DR("EDX"), '=', '(', operands[0][1], '*', operands[1][1], ')', '>>', ir.constant_operand(32))]
    elif m == "JMP":
      if poststore:
        poststore = False
      #absolute jump vs relative jump
      if 'rel' in operands[0][0]:
        IR += [ir.jump(operands[0][1],relative=True)]
      else:
        IR += [ir.jump(operands[0][1])]
    elif 'J' == m[0]:
      #IR = [ir.operation(self.DR("tval"),'=',self.DR("EIP"),"+",operands[0][1])]
      DEST = ir.constant_operand(int(size + operands[0][1].value))
      
      IR = []
      if m == "JO":
        IR += [ir.operation(self.DR('OF'),'==',ir.constant_operand(1))]
      elif m == "JNO":
        IR += [ir.operation(self.DR('OF'),'==',ir.constant_operand(0))]
      elif m == "JB":
        IR += [ir.operation(self.DR('CF'),'==',ir.constant_operand(1))]
      elif m == "JNC":
        IR += [ir.operation(self.DR('CF'),'==',ir.constant_operand(0))]
      elif m == "JBE":
        IR += [ir.operation(self.DR('ZF'),'==',ir.constant_operand(1), '||', self.DR("CF"), '==', ir.constant_operand(1))]
      elif m == "JNBE":
        IR += [ir.operation(self.DR('ZF'),'==',ir.constant_operand(0), '&&', self.DR("CF"), '==', ir.constant_operand(0))]
      elif m == "JS":
        IR += [ir.operation(self.DR('SF'),'==',ir.constant_operand(1))]
      elif m == "JNS":
        IR += [ir.operation(self.DR('SF'),'==',ir.constant_operand(0))]
      elif m == "JP":
        IR += [ir.operation(self.DR('PF'),'==',ir.constant_operand(1))]
      elif m == "JNP":
        IR += [ir.operation(self.DR('PF'),'==',ir.constant_operand(0))]
      elif m == "JL":
        IR += [ir.operation(self.DR('SF'),'!=',self.DR('OF'))]
      elif m == "JNL":
        IR += [ir.operation(self.DR('SF'),'==',self.DR('OF'))]
      elif m == "JLE":
        IR += [ir.operation(self.DR('ZF'),'==',ir.constant_operand(1), '||', self.DR("SF"), '!=', self.DR("OF"))]
      elif m == "JNLE":
        IR += [ir.operation(self.DR('ZF'),'==',ir.constant_operand(0), '&&', self.DR("SF"), '==', self.DR("OF"))]
      elif m == "JNZ":
        IR += [ir.operation(self.DR('ZF'),'==',ir.constant_operand(1))]
      elif m == "JZ":
        IR += [ir.operation(self.DR('ZF'), '==', ir.constant_operand(0))]      

      if 'rel' in operands[0][0]:
        IR += [ir.branch_true(DEST)]
      else:
        IR += [ir.branch_true(operands[0][1])]
    elif m == "LEA":
      preload = False
      poststore = False
      IR = [ir.operation(operands[0][1], '=', self.DR("TMEM"))]
    elif m == "LEAVE":
      # mov esp, ebp
      # pop ebp
      IR = [ir.operation(self.DR("ESP"),'=',self.DR("EBP")),
            ir.load(self.DR("ESP"), self.DR("EBP")), 
            ir.operation(self.DR("ESP",OPmode), '=', self.DR("ESP",OPmode),"+",ir.constant_operand(4))
           ]
    elif m == "MOV":
      #print hex(addr), operands
      if preload:
        if 'moffset' not in operands[1][0]:
          if operands[1][1].type != 'register' or operands[1][1].register_name != 'tval':
            preload = False
        
      if operands[0][1].type == 'register' and operands[0][1].register_name == 'tval':
        IR = [ir.operation(operands[1][1])]
      else:
        IR = [ir.operation(operands[0][1], '=', operands[1][1])]
    elif m == "MOVSX":
      #XXXXXX TODO sign extend
      IR = [ir.operation(operands[0][1], '=', operands[1][1])]      
    elif m == "MOVZX":
      if '16' in operands[1][0]:
        mask = 0xff
      else:
        mask = 0xffff
      IR = [ir.operation(operands[0][1], '=', operands[1][1], '&', ir.constant_operand(mask))]
    elif m == "NOT":
      IR = [ir.operation(operands[0][1],'=','~',operands[0][1])]
    elif m == "OR":
      IR = [ir.operation(operands[0][1],'=',operands[0][1],'|',operands[1][1])]
    elif m == "POP":
      IR = [ir.load(self.DR("ESP",OPmode), operands[0][1]), 
            ir.operation(self.DR("ESP",OPmode), '=', self.DR("ESP",OPmode),"+",ir.constant_operand(4))]
    elif m == "PUSH":
      if type(operands[0][1]) == str:
        IR = [ir.unhandled_instruction(instruction['mnemonic'])]
      else:
        IR = [ir.operation(self.DR("ESP",OPmode), '=', self.DR("ESP",OPmode),"-",ir.constant_operand(4)),
              ir.store(operands[0][1], self.DR("ESP",OPmode)),
              ]
        
        if operands[0][1].type == 'register' and operands[0][1].register_name != 'tval':
          poststore = False

    elif m == "RET":
      #pop eip
      preload = True
      IR = [ir.load(self.DR("ESP",OPmode), self.DR('TVAL')),
            ir.operation(self.DR('ESP',OPmode),'=',self.DR("ESP",OPmode),'+',ir.constant_operand(4)),
            ir.ret(self.DR('TVAL'))]
    elif m == "ROL":
      #XXX TODO FIX sz here
      sz = operands[0][1].size
      IR = [ir.operation(operands[0][1], '=', operands[0][1], '<<', operands[1][1], '|', operands[0][1],'>>', '(', ir.constant_operand(sz),'-',operands[1][1],')')]
    elif m == "ROR":
      sz = operands[0][1].size
      IR = [ir.operation(operands[0][1], '=', operands[0][1], '>>', operands[1][1], '|', operands[0][1],'<<', '(', ir.constant_operand(sz),'-',operands[1][1],')')]
    elif m == "SAL":
      IR = [ir.operation(operands[0][1],'=', '(', self.DR("CF"), '<<', ir.constant_operand(32), '+', operands[0][1], ')','>>',operands[1][1])]
    elif m == "SAR":
      IR = [ir.operation(operands[0][1],'=', '(', self.DR("CF"), '>>', ir.constant_operand(32), '+', operands[0][1], ')','<<',operands[1][1])]
    elif m == "SHL":
      IR = [ir.operation(operands[0][1],'=', operands[0][1],'<<',operands[1][1])]
    elif m == "SHR":
      IR = [ir.operation(operands[0][1],'=', operands[0][1],'>>',operands[1][1])]
    elif m == "SUB":
      IR = [ir.operation(operands[0][1],'=', operands[0][1],'-',operands[1][1])]
    elif m == "TEST":
      IR = [ir.operation(operands[0][1],'&',operands[1][1])]
    elif m == "XCHG":
      have_nop = 0
      if operands[0][1].type == 'register' and operands[1][1].type == 'register':
        if operands[0][1].register_name == "eax" and operands[1][1].register_name == "eax":
          have_nop = 1
          
      #TODO does not play well with TMEM
      if have_nop:
        IR = [ir.operation("NOP")]
      else:
        #XXXXX TODO TMEM
        IR = [ir.operation(self.DR("tval"),'=',operands[0][1]),
              ir.operation(operands[0][1],'=', operands[1][1]),
              ir.operation(operands[1][1],'=', self.DR("TVAL"))]
    elif m == "XOR":
      IR = [ir.operation(operands[0][1],'=', operands[0][1],'^',operands[1][1])]
    else:
      IR = [ir.unhandled_instruction(instruction['mnemonic'])]

    if TMEM_IR:
      #print "@@"#, preload, poststore, TMEM_IR
      
      out = []
      if preload:
        out += TMEM_IR + [ir.load(self.DR("TMEM"),self.DR("TVAL"))]
      elif TMEM_IR:
        if not poststore:
          out += TMEM_IR
        
      if poststore:
        if IR[0].type == 'operation':
          #XXX implicit load store hack
          if len(IR[0].ops) == 1:
            IR = [ir.operation(self.DR('tval'),'=', *(IR[0].ops))]
        out += IR + TMEM_IR + [ir.store(self.DR("tval"), self.DR('TMEM'))]
      else:
        out += IR
                      
      return out
    
    return IR
  
  def disassemble(self, data, addr): 
    """translate x86 bytecode into IR"""
    prefixbytes, prefixes = self.decodePrefix(data)
    
    OPmode = self.mode
    ADDRmode = self.mode
    #TODO do we need to handle 16-bit?
    for p in prefixes:
      if 'opsize' in prefixes[p]:
        OPmode = self.mode/2
      elif 'addrsz' in prefixes[p]:
        ADDRmode = self.mode/2
    
    data = data[len(prefixbytes):]
    OP = ord(data[0])
    sz, instruction = self.decode_opcode(data, ADDRmode)
    data = data[sz:]

    a = self.decode_operands(OP, instruction, data, OPmode)
    #print instruction['mnemonic'], a
    opsz, operands, TMEM_IR = a
    data = data[opsz:]
    
    IR = self.makeIR(instruction, sz+opsz, operands, TMEM_IR, OPmode, addr)
    #print sz+opsz, instruction['mnemonic'], operands,'\n-->', IR
    for y in IR:
      y.address = int("%d"%int(addr & 0xffffffff))
      y.wordsize = self.mode/8
      
    return sz + opsz + len(prefixbytes), IR

########### end disassembler code   ####################

  def translate(self, target):
    IRS = []
    
    def getnasm(data):
      open("/tmp/x.asm",'w').write(data)
      import os
      os.system("ndisasm -u /tmp/x.asm > /tmp/x.asm.out")
      return open("/tmp/x.asm.out",'r').readlines()[0].strip()
    
    visited =[]
    for seg in target.memory.segments:
      if seg.code:
        for start_addr in target.entry_points:

          addr = start_addr
          while addr+1 < seg.end:
            if addr in visited:
              break

            data = target.memory.getrange(addr,min(addr+15,seg.end-1))

            if len(data) < 15:
              data = data+"\x00"*15
            #print "disassemble @ %x : %r"%(addr,data)          
            #print "\n",hex(addr), [hex(ord(x)) for x in data]
            try:
              sz, IR = self.disassemble(data, addr)
            except InvalidInstruction:
              print 'invalid instruction: %x'%addr, `data`
              break
            #print sz, "IRIR=",IR
            #print hex(addr), IR#, getnasm(data)
            visited.append(addr)
            
            
            IRS += IR
            addr += sz
          
    return IRS
            
  def get_analysis_constant_regs(self, bin):
    return {}