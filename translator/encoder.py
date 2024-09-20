from translator.statement import Statement
import re
from translator.mnemcode import Mnemcode,Faddr
class Encoder:
  def __init__(self, root):
    self.root = root
    self.mnemcode = Mnemcode(0)
    self.data_memory = 0x0000000
    self.variables = {}

  def recursive_encoding(self, node):    
    instr = Mnemcode(0)
    match node.func_name:
      case "statement-list":
        for arg in node.params:
          instr.concat(self.recursive_encoding(arg))
      case "+":
        instr.concat(self.recursive_encoding(node.params[0])) #(r1)
        instr.concat(self.recursive_encoding(node.params[1])) #(r1,r2)
        instr.append("add")                                   #(r1+r2)
      case "-"|"<":
        instr.concat(self.recursive_encoding(node.params[0])) #(r1)
        instr.concat(self.recursive_encoding(node.params[1])) #(r1,r2)
        instr.append("sub")                                   #(r1-r2)
      case "<=":
        instr.concat(self.recursive_encoding(node.params[0]))  #(r1)
        instr.concat(self.recursive_encoding(node.params[1]))  #(r1,r2)
        instr.append("sub")                                    #(r1 - r2)
        instr.append("push", 1)                                #(r1 - r2, 1)
        instr.append("sub")                                    #(r1 - r2 - 1)
      case "read":
        buffer_start = self.data_memory
        self.data_memory += 200*32#buffer capacity - 200
        instr.append("push", buffer_start)                     #(buf_start)
        cur_char_ptr = self.data_memory
        self.data_memory += 32
        instr.append("push", cur_char_ptr)                     #(buf_start, mem_addr)
        instr.append("ld")#saved buffer start                  #(buf_start, mem_addr) mem_addr is pointer to cur_char
        instr.append("pop")                                    #(buf_start)
        instr.append("pop")                                    #(),
        loop_start = Faddr(instr.get_end())
        instr.append("in")                                     #(in)
        instr.append("push", cur_char_ptr)                     #(in, mem_addr)
        instr.append("mov")                                    #(in, cur_char)
        instr.append("ld")#saved char to buf                   #(in, cur_char)
        instr.append("push", 32)                               #(in, cur_char, 0x032)
        instr.append("add")                                    #(in, cur_char + 32)
        instr.append("push", cur_char_ptr)                     #(in, cur_char + 32, mem_addr)
        instr.append("ld")                                     #(in, buf_start + 32, mem_addr)
        instr.append("pop")                                    #(in, buf_start + 32)
        instr.append("pop")                                    #(in)
        instr.append("jz", loop_start)                         #() jz decrements tos
        instr.append("pop")                                    #()
        instr.append("push", buffer_start)                     #(buf_start)
      case "prints":
        instr.concat(self.recursive_encoding(node.params[0]))  #(str_start)
        cur_char_ptr = self.data_memory
        instr.append("push", cur_char_ptr)                     #(str_start, mem_addr)
        self.data_memory += 32
        instr.append("ld")#saved str_start to mem_addr         #(str_start, mem_addr)
        instr.append("pop")                                    #(str_start)
        instr.append("pop")                                    #()
        loop_start = Faddr(instr.get_end())
        instr.append("push", cur_char_ptr)                     #(mem_addr)
        instr.append("mov")                                    #(cur_str) pointer to current char
        instr.append("mov")                                    #(char)
        instr.append("out")                                    #(char)
        instr.append("push", cur_char_ptr)                     #(char,mem_addr)
        instr.append("mov")                                    #(char,cur_str)
        instr.append("push", 32)                               #(char,cur_str,0x032)
        instr.append("add")                                    #(char,cur_str + 32)
        instr.append("push", cur_char_ptr)                     #(char,cur_str+32,mem_addr)
        instr.append("ld")                                     #(char,cur_str+32,mem_addr)
        instr.append("pop")                                    #(char,cur_str+32)
        instr.append("pop")                                    #(char)
        instr.append("jz", loop_start)                         #()
        instr.append("pop")                                    #()
      case "printi":
        instr.concat(self.recursive_encoding(node.params[0]))  #(r1)
        instr.append("out")                                    #(r1)
        instr.append("pop")                                    #()
      case "string":
        buffer_size = (len(node.params[0])+1)
        buffer_start = self.data_memory
        next_char_addr = buffer_start
        for c in (node.params[0]):
          instr.append("push", ord(c))                         #(char)
          instr.append("push", next_char_addr)                 #(char, mem_addr)
          instr.append("ld")                                   #(char, mem_addr)
          instr.append("pop")                                  #(char)
          instr.append("pop")                                  #()
          next_char_addr += 32
        instr.append("push", 0)                                #(null)
        instr.append("push", next_char_addr)                   #(null, mem_addr)
        instr.append("ld")                                     #(null, mem_addr)
        instr.append("pop")                                    #(null)
        instr.append("pop")                                    #()
        instr.append("push", buffer_start)                     #(str_start)
      case "setq":
        instr.concat(self.recursive_encoding(node.params[1]))  #(value)
        var_addr = self.data_memory
        instr.append("push", var_addr)                         #(value, addr)
        self.data_memory += 32
        instr.append("ld")                                     #(value, addr)
        instr.append("pop")                                    #(value)
        instr.append("pop")                                    #()
        self.variables[node.params[0].func_name] = var_addr
      case "if":
        cond = self.recursive_encoding(node.params[0])
        is_true = self.recursive_encoding(node.params[1])
        is_false = self.recursive_encoding(node.params[2])
        instr.concat(cond)                                     #(cond) s if cond==true
        false_addr = instr.get_end() + 32 + is_true.get_end() + 32
        endif_addr = instr.get_end() + 32 + is_true.get_end() + 32 + is_false.get_end()
        instr.append("jns", Faddr(false_addr))                 #()
        instr.concat(is_true)                                  #(rt)
        instr.append("jump", Faddr(endif_addr))                #(rt)
        instr.concat(is_false)                                 #(rf)
      case "when":
        cond = self.recursive_encoding(node.params[0])
        is_true = self.recursive_encoding(node.params[1])
        instr.concat(cond)                                     #(cond)s if cond==true
        endif_addr = instr.get_end() + 32 + is_true.get_end()
        instr.append("jns", Faddr(endif_addr))                 #()
        instr.concat(is_true)                                  #(rt)
      case "break":
        instr.append("jump", "unknown")                        #()
      case "loop":
        for arg in node.params:
          instr.concat(self.recursive_encoding(arg))
        instr.append("jump", Faddr(0))#loop starts at 0        #(0)
        end_addr = Faddr(instr.get_end())
        for instruct in instr.instructions:
          if isinstance(instruct, list) and instruct[1] == "unknown":
            instruct[1] = end_addr
      case _:
        if re.search(r'[a-zA-Z_]', node.func_name):
          assert node.func_name in self.variables.keys(), node.func_name + " not variable"
          instr.append("push", self.variables[node.func_name]) #(addr)
          instr.append("mov")                                  #(value)
        else:
          instr.append("push", int(node.func_name))            #(const)
    return instr
  
  def make_code(self):
    self.mnemcode = self.recursive_encoding(self.root)