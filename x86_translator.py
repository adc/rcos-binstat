"""
first jab is 32-bit modes, x86 core.
"""
import ir
import struct
import parsex86


X86DecodeTable = parsex86.get_decode_dict()

class InvalidInstruction(Exception): pass
class X86_Translator:
  
  def __init__(self, mode=32):
    self.registers = \
    [ ir.register("eax:32-0", "ax:16-0", "ah:16-8", "al:7-0"),
      ir.register("ebx:32-0", "ax:16-0", "ah:16-8", "al:7-0"),
      ir.register("ecx:32-0", "ax:16-0", "ah:16-8", "al:7-0"),
      ir.register("edx:32-0", "ax:16-0", "ah:16-8", "al:7-0"),
      ir.register("esi:32-0", "si:16-0"),
      ir.register("edi:32-0", "di:16-0"),
      ir.register("ebp:32-0", "bp:16-0"),
      ir.register("esp:32-0", "sp:16-0"),
      ir.register("eip:32-0", "ip:16-0"),
      ir.register("eflags:32-0", "ID:21", "VIP:20", 
                  "VIF:19", "AC:18", "VM:17",
                  "RF:16", "NT:14", "IOPL:13-12", 
                  "OF:11", "DF:10", "IF:9",
                  "TF:8", "SF:7", "ZF:6", 
                  "AF:4", "PF:2", "CF:0")]
    self.mode = 32

    
  def disassemble(self, data, addr):    
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
    regmodes = {16: 2, 32: 3, 64: 4}
    #in 64-bit esi/edi/ebp/esp gain low byte access w/ REX
    
    def decodePrefix(bytes):      
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

    def get_imm(sz, offset, data, signed=0):
      if sz == 1:
        return ir.constant_operand(ord(data[offset]), signed)
      elif sz == 2:
        return ir.constant_operand(struct.unpack('<H',data[offset:offset+2])[0], signed)
      elif sz == 4:
        return ir.constant_operand(struct.unpack('<L',data[offset:offset+4])[0], signed)
      else:
        raise Exception("bad imm value")
  
    def decode_one_op(OP, mode, bytes):
      print 'single'
      DBG = 0
      if DBG: print 'decode 1-op'
      orig = bytes
      bytes = bytes[1:]
      
      if OP in X86DecodeTable:
        instruction = X86DecodeTable[OP]['instr'][mode][0]
      else:
        #check for +r{b/w/d/q} syntax on one-byte opcodes
        if OP & 0xf8 not in X86DecodeTable:
          raise InvalidInstruction("unknown opcode@: %x: %r"%(OP,bytes))
        else:
          if '+' not in X86DecodeTable[OP&0xf8]['instr'][mode][0]['modrm']:
            raise InvalidInstruction("unknown opcode@: %x: %r"%(OP,bytes))

          instruction = X86DecodeTable[OP&0xf8]['instr'][mode][0]
      
      
      Immediate = None
      if instruction['immediate']:
        #XXXX signedness
        if DBG: print instruction['immediate'], mode
        strings = {'ib': 1, 'iw' : 2, 'id': 4, 'iq': 8}
        sz = strings[instruction['immediate']]
        Immediate = get_imm(sz, 0, bytes)
        bytes = bytes[sz:]

      code_offset = None
      if instruction['code_offset']:
        if DBG: print instruction['code_offset'], mode
        strings = {'cb': 1, 'cw' : 2, 'cd': 4, 'cq': 8, 'm64': 8}
        sz = strings[instruction['code_offset']]
        code_offset = get_imm(sz, 0, bytes)
        bytes = bytes[sz:]
      
      Reg = DR(OP & 7, mode)
      
      print Reg, Immediate, code_offset, instruction['operands']
      return len(orig)-len(bytes), instruction['mnemonic']
    
    def DR(number, mode):
      return regdecode[number][regmodes[mode]]
      
      
    def decode_opcode(prefixes, data):
      orig = data
      OP = ord(data[0])
      data = data[1:]
      instruction = None

      DBG = 0
      
      OPmode = self.mode
      ADDRmode = self.mode
      for p in prefixes:
        if 'opsize' in prefixes[p]:
          OPmode = self.mode/2
        elif 'addrsz' in prefixes[p]:
          ADDRmode = self.mode/2
          
      #it might be a one-op code, check it out
      if OP not in X86DecodeTable:
        return decode_one_op(OP, OPmode, data)
      
      #search until OPmode is found
      prev = X86DecodeTable[OP]
      while 'instr' not in prev:
        OP = ord(data[0])
        data = data[1:]
        if OP not in prev:
          raise InvalidInstruction("invalid opcode")
        prev = prev[OP]

      if OPmode not in prev['instr']:
        raise InvalidInstruction("invalid opcode")
      
      if len(prev['instr'][OPmode]) == 1:
        if DBG: print "EZ choice"
        instruction = prev['instr'][OPmode][0]
      else:
        #check if the modrm says which one we want
        if not prev['instr'][OPmode][0]['modrm']:
          if len(prev['instr'][OPmode][0]['operands']) != 0:
            #print "CRAP????? what now"
            #print prev['instr'][OPmode]
            #TODO bug check, picks first one for now
            instruction = prev['instr'][OPmode][0]
          else:
            return decode_one_op(OP,OPmode, data)
        else:
          peek_modrm = ord(data[0])
          target = (peek_modrm >> 3) & 7
          for x in prev['instr'][OPmode]:
            if ('/%d'%target) in x['modrm']:
              #print "****** match %d"%target
              instruction = x
              break
              
          if not instruction:
            raise InvalidInstruction("unmatched regfield in modrm")
      
      modrm = None
      sib = None
      if instruction['modrm']:
        #decode modrm        
        if '+' not in instruction['modrm']:
          if DBG: print 'modrm'
          modrm = ord(data[0])
          data = data[1:]
      
      RegOne = None
      Offset = 0

      if modrm:
        mod = modrm>>6
        if mod != 3 and modrm&7 == 4:
          if DBG: print 'sib'
          sib = ord(data[0])
          data = data[1:]
          
        #mod = [mm][reg2][reg1]
        if mod == 0:
          # [reg1] is an operand
          #TODO
          pass
        elif mod == 1:
          #[reg1+ib]
          Offset = ord(data[0])
          if DBG: print 'mod1'
          data = data[1:]
          RegOne = DR(modrm & 7, ADDRmode)
        elif mod == 2:
          #[reg1+mode_offset]
          Offset = get_imm(ADDRmode/8, 0, data)
          if DBG: print 'mod2'
          data = data[(ADDRmode/8):]
          RegOne = DR(modrm & 7, ADDRmode)
        elif mod == 3:
          #reg1
          if DBG: print 'mod3'
          RegOne = DR(modrm & 7, ADDRmode)
        else:
          raise InvalidInstruction("modrm insanity")
      
      if modrm:
        RegTwo = DR( (modrm >> 3)&7, ADDRmode)
      else:
        RegTwo = None
      
      Immediate = None
      if instruction['immediate']:
        #XXXX signedness
        if DBG: print instruction['immediate'], OPmode
        strings = {'ib': 1, 'iw' : 2, 'id': 4, 'iq': 8}
        sz = strings[instruction['immediate']]
        imm = get_imm(sz, 0, data)
        data = data[sz:]
      
      code_offset = None
      if instruction['code_offset']:
        if DBG: print instruction['code_offset'], OPmode
        strings = {'cb': 1, 'cw' : 2, 'cd': 4, 'cq': 8, 'm64': 8}
        sz = strings[instruction['code_offset']]
        code_offset = get_imm(sz, 0, data)
        data = data[sz:]

      mem_addr = None
      #check for memory offsets in operand ( MOV A3 opcode, etc)
      for oper in instruction['operands']:
        if 'moffset%d'%OPmode in oper:
          sz = OPmode/8
          mem_addr = get_imm(sz, 0, data)
          data = data[sz:]
      
      string = instruction['mnemonic']
      
      #destination comes first followed by others
      operands = []
      for operand in instruction['operands']:
        if operand == "reg/mem32":
          pass
      
      print RegOne, RegTwo, Offset, Immediate, code_offset, mem_addr, instruction['operands']
      return len(orig)-len(data), string
      
      
      
    prefixbytes, prefixes = decodePrefix(data)
    data = data[len(prefixbytes):]
    length, IR = decode_opcode(prefixes, data)

    return length + len(prefixbytes), IR

    #default segments
    #ds -> immediate
    #ds/es (can not override es)
  
  def translate(self, target):
    IRS = []
    
    for seg in target.memory.segments:
      if seg.code:
        addr = target.entry_points[0]
        #addr = 0x8048a65
        while addr+15 < seg.end:
          data = target.memory[addr:addr+15]
            
          if len(data) < 15:
            data = data+"\x00"*15

          #print "disassemble @ %x : %r"%(addr,data)          
          print "\n",hex(addr), [hex(ord(x)) for x in data]
          sz, IR = self.disassemble(data, addr)
          print sz, IR
          #raw_input()
          addr += sz
          
    return IRS
  