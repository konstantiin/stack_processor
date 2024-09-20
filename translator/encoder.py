from translator.statement import Statement
import re
from translator.mnemcode import Mnemcode,Faddr
class Encoder:
  def __init__(self, root):
    self.root = root
    self.mnemcode = Mnemcode(0)
    self.memory_stack_ptr = 0xffffff
    self.variables = {}

  def recursive_encoding(self, node):    
    instr = Mnemcode(0)
    match node.func_name:
      case "statement-list":
        for arg in node.params:
          instr.concat(self.recursive_encoding(arg))
      case "+":
        instr.concat(self.recursive_encoding(node.params[0]))
        instr.concat(self.recursive_encoding(node.params[1]))
        instr.append("add")
      case "-"|"<":
        instr.concat(self.recursive_encoding(node.params[0]))
        instr.concat(self.recursive_encoding(node.params[1]))
        instr.append("sub")
      case "<=":
        instr.concat(self.recursive_encoding(node.params[0]))  #(r1)
        instr.concat(self.recursive_encoding(node.params[1]))  #(r1,r2)
        instr.append("sub")                                    #(r1 - r2)
        instr.append("push", 1)                                #(r1 - r2, 1)
        instr.append("sub")                                    #(r1 - r2 - 1)
      case "read":
        buffer_start = self.memory_stack_ptr-(200*8)
        self.memory_stack_ptr-=(200*8)
        self.memory_stack_ptr-=32
        instr.append("push", buffer_start)                     #(buf_start)
        instr.append("push", self.memory_stack_ptr)            #(buf_start, mem_addr)
        instr.append("ld")#saved buffer start                  #(buf_start, mem_addr) mem_addr is pointer to cur_char
        instr.append("pop")                                    #(buf_start)
        instr.append("pop")                                    #(),
        instr.append("push", Faddr(instr.get_end() + 64))      #(loop_addr) address of next instruction
        instr.append("in")                                     #(loop_addr, in)
        instr.append("push", self.memory_stack_ptr)            #(loop_addr, in, mem_addr)
        instr.append("mov")                                    #(loop_addr, in, cur_char)
        instr.append("ld")#saved char to buf                   #(loop_addr, in, cur_char)
        instr.append("pop")                                    #(loop_addr, in, cur_char)
        instr.append("push", 8)                                #(loop_addr, in, cur_char, 0x08)
        instr.append("sub")                                    #(loop_addr, in, cur_char - 8)
        instr.append("push", self.memory_stack_ptr)            #(loop_addr, in, cur_char - 8, mem_addr)
        instr.append("ld")                                     #(loop_addr, in, buf_start - 8, mem_addr)
        instr.append("pop")                                    #(loop_addr, in, buf_start - 8)
        instr.append("pop")                                    #(loop_addr, in)
        instr.append("jz")                                     #(loop_addr) jz decrements tos
        instr.append("pop")                                    #()
        instr.append("push", buffer_start)                     #(buf_start)
      case "prints":
        instr.concat(self.recursive_encoding(node.params[0]))  #(str_start)
        self.memory_stack_ptr -= 32
        instr.append("push", self.memory_stack_ptr)            #(str_start, mem_addr)
        instr.append("ld")#saved str_start to mem_addr         #(str_start, mem_addr)
        instr.append("pop")                                    #(str_start)
        instr.append("pop")                                    #()
        instr.append("push", Faddr(instr.get_end() + 64))      #(loop_addr) address of next instruction
        instr.append("push", self.memory_stack_ptr)            #(loop_addr,mem_addr)
        instr.append("mov")                                    #(loop_addr,cur_str) pointer to current char
        instr.append("mov")                                    #(loop_addr,char)
        instr.append("out")                                    #(loop_addr,char)
        instr.append("push", self.memory_stack_ptr)            #(loop_addr,char,mem_addr)
        instr.append("mov")                                    #(loop_addr,char,cur_str)
        instr.append("push", 8)                                #(loop_addr,char,cur_str,0x08)
        instr.append("sub")                                    #(loop_addr,char,cur_str - 8)
        instr.append("push", self.memory_stack_ptr)            #(loop_addr,char,cur_str-8,mem_addr)
        instr.append("ld")                                     #(loop_addr,char,cur_str-8,mem_addr)
        instr.append("pop")                                    #(loop_addr,char,cur_str-8)
        instr.append("pop")                                    #(loop_addr,char)
        instr.append("jz")                                     #(loop_addr)
        instr.append("pop")                                    #()
      case "printi":
        instr.concat(self.recursive_encoding(node.params[0]))
        instr.append("out") #first byte out
        instr.append("rol") 
        instr.append("out") #second byte out
        instr.append("rol")
        instr.append("out") #third byte out
        instr.append("rol")
        instr.append("out") #forth byte out
        instr.append("pop") #()
      case "string":
        buffer_size = (len(node.params[0])+1)
        buffer_start = self.memory_stack_ptr-(buffer_size*8)
        self.memory_stack_ptr-=(buffer_size*8)
        next_char_addr = buffer_start
        for c in (node.params[0]):
          instr.append("push", ord(c))                         #(char)
          instr.append("push", next_char_addr)                 #(char, mem_addr)
          instr.append("ld")                                   #(char, mem_addr)
          instr.append("pop")                                  #(char)
          instr.append("pop")                                  #()
          next_char_addr += 8
        instr.append("push", 0)                                #(null)
        instr.append("push", next_char_addr)                   #(null, mem_addr)
        instr.append("ld")                                     #(null, mem_addr)
        instr.append("pop")                                    #(null)
        instr.append("pop")
        instr.append("push", buffer_start)                                    #()
      case "setq":
        instr.concat(self.recursive_encoding(node.params[1]))  #(value)
        self.memory_stack_ptr -= 32
        instr.append("push", self.memory_stack_ptr)            #(value, addr)
        instr.append("ld")                                     #(value, addr)
        instr.append("pop")                                    #(value)
        instr.append("pop")                                    #()
        self.variables[node.params[0].func_name] = self.memory_stack_ptr
      case "if":
        is_true = self.recursive_encoding(node.params[1])
        is_false = self.recursive_encoding(node.params[2])
        cond = self.recursive_encoding(node.params[0])
        false_addr = instr.get_end() + 32 + cond.get_end() + 2*32 + is_true.get_end() + 2*32
        #------------------------------^(push)---------------^(jns, pop)----------------^(push, jump)
        end_addr = false_addr + 32 + is_false.get_end()
        #-----------------------^(pop)----------------
        instr.append("push", Faddr(false_addr))                  #(addr_false)
        instr.concat(cond)                                     #(addr_false, cond)
        instr.append("jns")                                   #(addr_false)
        instr.append("pop")                                   #()
        instr.concat(is_true)                                  #(rt)
        instr.append("push", Faddr(end_addr))                  #(rt,addr_end)
        instr.append("jump")                                   #(rt)
        instr.append("pop")                                   #()
        instr.concat(is_false)                                 #(rf)
      case "when":
        is_true = self.recursive_encoding(node.params[1])
        cond = self.recursive_encoding(node.params[0])
        false_addr = instr.get_end() + 32 + cond.get_end() + 2*32 + is_true.get_end() + 32
        #------------------------------^(push)---------------^(jns, pop)----------------^(push 0)
        instr.append("push", Faddr(false_addr))                  #(addr_false)
        instr.concat(cond)                                     #(addr_false, cond)
        instr.append("jns")                                   #(addr_false)
        instr.append("pop")                                   #()
        instr.concat(is_true)                                  #(rt)
        instr.append("push", 0)                               #(rt, 0)
        instr.append("pop")                                   #(rt) or ()
      case "break":
        instr.append("push", "unknown")                        #(end_of_loop)
        instr.append("jump")                                   #()
      case "loop":
        for arg in node.params:
          instr.concat(self.recursive_encoding(arg))
        instr.append("push", Faddr(0))#loop starts at 0        #(0)
        instr.append("jump")                                   #()
        break_addr = Faddr(instr.get_end())
        for instruct in instr.instructions:
          if isinstance(instruct, list) and instruct[1] == "unknown":
            instruct[1] = break_addr
      case _:
        if re.search(r'[a-zA-Z_]', node.func_name):
          assert node.func_name in self.variables.keys(), node.func_name + " not variable"
          instr.append("push", self.variables[node.func_name])#(addr)
          instr.append("mov")                                 #(value)
        else:
          instr.append("push", int(node.func_name))
    return instr
  
  def make_code(self):
    self.mnemcode = self.recursive_encoding(self.root)