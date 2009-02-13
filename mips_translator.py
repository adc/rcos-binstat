import ir
import struct

class Translator:
  """ Base class for IR translators
    To implement a translator for your architecture
    you must implement the following:

    register_info() -> returns information about available flags, registers, and their sizes

    disassemble(bytecodes, base_addr)
    translate(target) -> returns IR representation of binary
    
    mem_info() -> describes memory regions 
    """
  def __init__(self):
    pass

class MIPS_Translator(Translator):
  def __init__(self):
    Translator.__init__(self)
    self.registers = [\
        ir.register("$0", "$zero"),
        ir.register("$1", "$at"),
        ir.register("$2", "$v0"),
        ir.register("$3", "$v1"),
        ir.register("$4", "$a0"),
        ir.register("$5", "$a1"),
        ir.register("$6", "$a2"),
        ir.register("$7", "$a3"),
        ir.register("$8", "$t0"),
        ir.register("$9", "$t1"),
        ir.register("$10", "$t2"),
        ir.register("$11", "$t3"),
        ir.register("$12", "$t4"),
        ir.register("$13", "$t5"),
        ir.register("$14", "$t6"),
        ir.register("$15", "$t7"),
        ir.register("$16", "$s0"),
        ir.register("$17", "$s1"),
        ir.register("$18", "$s2"),
        ir.register("$19", "$s3"),
        ir.register("$20", "$s4"),
        ir.register("$21", "$s5"),
        ir.register("$22", "$s6"),
        ir.register("$23", "$s7"),
        ir.register("$24", "$t8"),
        ir.register("$25", "$t9"),
        ir.register("$26", "$k0"),
        ir.register("$27", "$k1"),
        ir.register("$28", "$gp"),
        ir.register("$29", "$sp"),
        ir.register("$30", "$fp"),
        ir.register("$31", "$ra"), 
        ir.register("$32", "$pc")]
    for i in range(32):
      self.registers.append(ir.register("$f%d"%i))
    self.registers.append(ir.register("FP_COND"))
    self.registers.append(ir.register("HILO",size=8))
      
  def mem_info():
    pass
    
  def decode_register(self, reg):
    R = None
    if type(reg) == str:
      for r in self.registers:
        if r.name == reg or reg in r.aliases:
          R = r
          break
      if not R:
        raise Exception("DR: Unknown register: %s"%reg)
    else:
      for r in self.registers:
        if r.name == "$%d"%reg:
          R = r
          break
      if not R:
        raise Exception("DR: Unknown register: $%d"%reg)

  def get_r_type(self, opcode):
    function = opcode & 0x3f
    rs = (opcode>>21) & 0x1f
    rt = (opcode>>16) & 0x1f
    rd = (opcode>>11) & 0x1f
    sa = (opcode>>6) & 0x1f
    
    DR = self.decode_register
    instructions = {
      0   : ("sll rd = rt << sa", 
          [ir.operation(DR(rd),"=",DR(rs),"<<",DR(sa), signed=0)]),
      2   : ("srl  rd = rt >> sa", 
          [ir.operation(DR(rd),"=",DR(rs),">>",DR(sa), signed=0)]),
      3   : ("sra rd = rt >> sa",
          [ir.operation(DR(rd),"=",DR(rs),">>",DR(sa))]),
      4   : "sllv",
      6   : "srlv",
      7   : "srav",
      8   : ("jr PC = rs", 
          [ir.jump(DR(rs))]),
      9   : ("jalr rd = return_addr, PC = rs ",
          [ir.operation(ir.operation(DR(rd),'=',DR("$pc"),"+",4)),
           ir.call(rs)]),
      12  : "syscall",
      13  : "break",
      16  : ("mfhi", 
          [ir.operation(DR(rd),'=',DR("HILO"))]),
      17  : ("mthi",     
          [ir.operation(DR("HILO"),'=',DR(rs),'<<',ir.constant_operand(32))]), 
      18  : ("mflo",
          [ir.operation(DR(rd),'=',DR("HILO"))]),   
      19  : ("mtlo",
          [ir.operation(DR("HILO"),'=',DR(rs))]),
      24  : ("mult LO,HI = rs*rt",
          [ir.operation(DR("HILO"),"=",DR(rs),"*",DR(rt))]),
      25  : ("multu",
          [ir.operation(DR("HILO"),"=",DR(rs),"*",DR(rt), signed=0)]),
      26  : ("div",
            [ir.operation(DR("HILO"),"=",DR(rs),"/",DR(rt))]),
      27  : ("divu",
            [ir.operation(DR("HILO"),"=",DR(rs),"/",DR(rt), signed=0)]),
      28  : "dmult",
      29  : "dmultu",
      30  : "ddiv",
      32  : ("add  rd = rs + rt",
          [ir.operation(DR(rd),"=",DR(rs),"+",DR(rt))]),
      33  : ("addu",
          [ir.operation(DR(rd),"=",DR(rs),"+",DR(rt), signed=0)]),
      34  : ("sub",
            [ir.operation(DR(rd),'=',DR(rs),"-",DR(rt))]),
      35  : ("subu",
          [ir.operation(DR(rd),'=',DR(rs),"-",DR(rt), signed=0)]),
      36  : ("and",
          [ir.operation(DR(rd),"=",DR(rs),"&",DR(rt))]),
      37  : ("or",
          [ir.operation(DR(rd),"=",DR(rs),"|",DR(rt))]),
      38  : ("xor", 
          [ir.operation(DR(rd),"=",DR(rs),"^",DR(rt))]),
      39  : ("nor",
          [ir.operation(DR(rd),'=',DR(rs),"~",DR(rt))]),
      42  : ("slt",
          [ir.operation(DR(rd),'=',DR(rs), "<", DR(rt))]),
      43  : ("sltu",
          [ir.operation(DR(rd),'=',DR(rs), "<", DR(rt), signed=0)]),
      45  : "daddu",
      47  : "dsubu",
      52  : "teq",
      56  : "dssl",
      59  : "dsra",
      60  : "dsll32",
      63  : "dsra32"
    }
    try:
      return instructions[function]
    except:
      raise Exception("unknown function code for R types: %d"%function)
  """
  Instruction	 Opcode	 Notes
  bgez	 rs, label        	 000001	 rt = 00001
  bgtz	 rs, label        	 000111	 rt = 00000
  blez	 rs, label        	 000110	 rt = 00000
  bltz	 rs, label        	 000001	 rt = 00000

  swc1	 rt, immediate(rs)	 111001	
  xori	 rt, rs, immediate	 001110"""      
  def get_i_type(self, opcode):
    OP = opcode >> 26
    instructions = {
      1   :   "bgez",
      4   :   "beq",
      5   :   "bne",
      6   :   "blez",
      7   :   "bgtz",
      8   :   "addi",
      9   :   "addiu",
      10  :   "slti",
      11  :   "sltiu",
      12  :   "andi",
      13  :   "ori",
      14  :   "xori",
      15  :   "lui",
      20  :   "beqzl",
      21  :   "bnezl",
      22  :   "blezl",
      23  :   "bgtzl",
      25  :   "daddiu",
      26  :   "ldl",
      27  :   "ldr",
      32  :   "lb",
      33  :   "ll",
      34  :   "lwl",
      35  :   "lw",
      36  :   "lbu",
      37  :   "lhu",
      38  :   "lwr",
      39  :   "lw",
      40  :   "sb",
      41  :   "sh",
      43  :   "sw",
      44  :   "sdl",
      45  :   "sdr",
      49  :   "lwc1",
      53  :   "ldc1",
      55  :   "ld",
      57  :   "swc1",
      61  :   "sdc1",
      63  :   "sd",
      
    }
    
    try:
      return instructions[OP]
    except:
      raise Exception("unknown op code for I types: %d"%OP)

  def get_j_type(self, opcode):
    OP = opcode >> 26
    target = opcode & 0x3ffffff
    
    if OP == 2:
      return "j"
    elif OP == 3:
      return "jal"

  def get_coproc_type(self, opcode):
    return "unsupported"
  
  def disassemble(self, bytecodes, base_addr):
    opcode = struct.unpack(">L", bytecodes)[0]
    
    OP = opcode >> 26

    if OP == 0:
      self.get_r_type(opcode)
    elif OP in [2,3]:
      self.get_j_type(opcode)
    elif OP in [16,17,18,19]:
      self.get_coproc_type(opcode)
    else:
      self.get_i_type(opcode)

  def translate(self, target):
    for seg in target.memory.segments:
      if seg.code:
        x = target.entry_points[0]
        print hex(x)
        while x < seg.end:
          print hex(x)+">>>"
          self.disassemble(target.memory[x:x+4], x)
          x += 4
        

        