import random
import string
from obfuscations import ast_nodes as ast


class DummyFunctionInjector:
    def __init__(self):
        self.dummy_func_counter = 0
        self.dummy_var_counter = 0

    def _generate_dummy_func_name(self):
        self.dummy_func_counter += 1;
        suffix = ''.join(random.choices(string.ascii_lowercase, k=3))
        return f"dummy_fn_{suffix}{self.dummy_func_counter}"

    def _generate_dummy_var_name(self):
        self.dummy_var_counter += 1;
        suffix = ''.join(random.choices(string.ascii_lowercase, k=2))
        return f"dv_{suffix}{self.dummy_var_counter}"

    def _create_dummy_function(self):
        func_name, return_type = self._generate_dummy_func_name(), ast.TypeNode(name="int")
        params = []
        if random.choice([True, False]): params.append(
            ast.ParamNode(ast.TypeNode("int"), self._generate_dummy_var_name()))
        if random.choice([True, False]): params.append(
            ast.ParamNode(ast.TypeNode("char"), self._generate_dummy_var_name()))

        body_items = []
        var_a = self._generate_dummy_var_name()
        body_items.append(
            ast.VarDeclNode(ast.TypeNode("int"), var_a, ast.ConstantNode("int", str(random.randint(1, 100)))))
        var_b = self._generate_dummy_var_name()
        body_items.append(ast.VarDeclNode(ast.TypeNode("char"), var_b,
                                          ast.ConstantNode("char", f"'{random.choice(string.ascii_lowercase)}'")))

        if_cond = ast.BinaryOpNode('>', ast.IdNode(var_a), ast.ConstantNode("int", str(random.randint(1, 10))))
        assign_if = ast.AssignmentNode(ast.IdNode(var_a),
                                       ast.BinaryOpNode('*', ast.IdNode(var_a), ast.ConstantNode("int", "2")))
        if_true_body = ast.CompoundStatementNode(items=[ast.ExprStatementNode(expr=assign_if)])
        body_items.append(ast.IfNode(cond=if_cond, if_true_body=if_true_body))

        ret_expr = ast.IdNode(var_a)
        if params and params[0].name: ret_expr = ast.BinaryOpNode("+", ret_expr, ast.IdNode(params[0].name))
        body_items.append(ast.ReturnNode(expr=ret_expr))

        return ast.FuncDefNode(return_type, func_name, params, ast.CompoundStatementNode(body_items))

    def visit_ProgramNode(self, node: ast.ProgramNode, num_to_insert=1):
        for _ in range(num_to_insert):
            node.declarations.insert(random.randint(0, len(node.declarations)), self._create_dummy_function())
        return node


def apply_dummy_function_insertion(ast_root: ast.ProgramNode, num_to_insert=1):
    if num_to_insert <= 0: return ast_root
    return DummyFunctionInjector().visit_ProgramNode(ast_root, num_to_insert=num_to_insert)