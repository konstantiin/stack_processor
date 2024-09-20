from translator.statement import Statement

custom_funcs_params = {}
custom_funcs_bodies = {}
class Inliner:
  def __init__(self, statement):
    self.root = statement
  
  def replace_func_vars(statement, old_name, new_name):
    assert isinstance(statement, Statement), statement + " is not Statement"
    if statement.func_name == 'string':
      return
    if statement.func_name == old_name:
      statement.func_name = new_name
    for s in statement.params:
      Inliner.replace_func_vars(s, old_name, new_name)

  def process_defun_varnames(self):
    for statement in self.root.params:
      if statement.func_name == 'defun':
        new_params = []
        for var_name in statement.params[1]:
          for s in statement.params[2:]:
            Inliner.replace_func_vars(s, var_name, statement.params[0] + "." + var_name)
          var = Statement()
          var.func_name = statement.params[0] + "." + var_name
          new_params.append(var)
        statement.params[1] = new_params
        custom_funcs_params[statement.params[0]] = statement.params[1]
        custom_funcs_bodies[statement.params[0]] = statement.params[2:]
  
  def inline_functions(statement):
    assert isinstance(statement, Statement), statement + " is not Statement"
    
    if statement.func_name in custom_funcs_params.keys():
      new_statement = Statement()
      new_statement.func_name = "statement-list"
      for i,arg in enumerate(statement.params):
        init_var = Statement()
        init_var.func_name = "setq"
        var_name = custom_funcs_params[statement.func_name][i]
        init_var.params = [ var_name, arg]
        new_statement.params.append(init_var)
      for s in custom_funcs_bodies[statement.func_name]:
        new_statement.params.append(s)
      statement.func_name = new_statement.func_name
      statement.params = new_statement.params
    for s in statement.params:
      if isinstance(s, Statement):
        Inliner.inline_functions(s)
    
  def inline_and_delete_functions(self):
    self.process_defun_varnames()
    for s in self.root.params:
      Inliner.inline_functions(s)
    new_params = []
    for s in self.root.params:
      if s.func_name != "defun":
        new_params.append(s)
    self.root.params = new_params



        


