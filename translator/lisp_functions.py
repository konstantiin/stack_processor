'''
everything is a function)) 
'''
available_functions = {
  "statement-list": -1, #ok
  "string": 1,        #ok
  "defun": 3,     #inline
  "printi": 1,    #ok
  "prints":1,     #ok
  "read": 0,      #ok
  "if": 3,       #ok
  "setq": 2,    #ok
  "loop": -1,  #ok
  "when": 2,    #ok
  "break": 1,  #ok
  "<": 2,        #ok
  "<=": 2,       #ok
  "+": 2,        #ok
  "-": 2         #ok
}