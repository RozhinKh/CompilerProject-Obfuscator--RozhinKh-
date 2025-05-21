
from pycparser import c_ast
import random
import string

FUNCTION_PREFIX = "dummyFunction_"
VARIABLE_PREFIX = "dummyVariable_"
dummy_counters = {'func': 0, 'var': 0}


def dummy_function():
    dummy_counters['func'] += 1
    return f"{FUNCTION_PREFIX}{dummy_counters['func']}"


def dummy_variable():
    dummy_counters['var'] += 1
    return f"{VARIABLE_PREFIX}{dummy_counters['var']}"


def reset_dummy_state():
    dummy_counters['func'] = 0
    dummy_counters['var'] = 0


class DummyFunctionInjector:
    def create_dummy(self):
        dummy_function_name = dummy_function()
        params = None
        return_type_declaration = c_ast.TypeDecl(
            declname=dummy_function_name,
            quals=[],
            type=c_ast.IdentifierType(['int']),
            align=None
        )
        func_declaration_type = c_ast.FuncDecl(args=params, type=return_type_declaration)

        var_a_name = dummy_variable()
        var_b_name = dummy_variable()

        declaration_a = c_ast.Decl( name=var_a_name, quals=[], storage=[], funcspec=[],
             type=c_ast.TypeDecl(
                declname=var_a_name, quals=[],
                type=c_ast.IdentifierType(['int']),
                align=None
            ),
            init=c_ast.Constant('int', str(random.randint(1, 100))),
            bitsize=None,
            align=None
        )
        declaration_b = c_ast.Decl( name=var_b_name, quals=[], storage=[], funcspec=[],
             type=c_ast.TypeDecl(
                declname=var_b_name, quals=[],
                type=c_ast.IdentifierType(['char']),
                align=None
            ),
            init=c_ast.Constant('char', f"'{random.choice(string.ascii_lowercase)}'"),
            bitsize=None,
            align=None
        )

        condition_left = c_ast.BinaryOp('>', c_ast.ID(name=var_a_name),
                                   c_ast.Constant('int', str(random.randint(1, 5))))
        condition_right = c_ast.BinaryOp('==', c_ast.ID(name=var_b_name),
                                    c_ast.Constant('char', f"'{random.choice(string.ascii_lowercase)}'"))
        condition = c_ast.BinaryOp('&&', condition_left, condition_right)

        assign_right = c_ast.BinaryOp('-', c_ast.BinaryOp('*', c_ast.ID(name=var_a_name), c_ast.Constant('int', '2')),
                                    c_ast.Constant('int', '1'))
        if_assign = c_ast.Assignment('=', c_ast.ID(name=var_a_name), assign_right)
        if_compound = c_ast.Compound(block_items=[if_assign])
        if_statement = c_ast.If(cond=condition, iftrue=if_compound, iffalse=None)

        cast_to_type = c_ast.Typename(
            name=None,
            quals=[],
            type=c_ast.TypeDecl(
                declname=None,
                quals=[],
                type=c_ast.IdentifierType(['int']),
                align=None
            ),
            align=None
        )
        cast_b_to_int = c_ast.Cast(to_type=cast_to_type, expr=c_ast.ID(name=var_b_name))

        return_expression = c_ast.BinaryOp('+', c_ast.ID(name=var_a_name), cast_b_to_int)
        return_statement = c_ast.Return(expr=return_expression)

        function_items = [declaration_a, declaration_b, if_statement, return_statement]
        function_body = c_ast.Compound(block_items=function_items)

        declaration_node = c_ast.Decl(
            name=dummy_function_name,
            quals=[], storage=['extern'], funcspec=[],
            type=func_declaration_type,
            init=None,
            bitsize=None,
            align=None
        )

        dummy_definition = c_ast.FuncDef(
            decl=declaration_node,
            param_decls=None,
            body=function_body
        )
        return dummy_definition

    def dummy_injection(self, ast_root_node, num_dummy_functions=1):
        for _ in range(num_dummy_functions):
            dummy_func_ast = self.create_dummy()
            if ast_root_node.ext is None:
                ast_root_node.ext = []
            ast_root_node.ext.append(dummy_func_ast)


def apply_dummy_function_insertion(root_node, num_to_insert=1):
    if num_to_insert <= 0:
        return root_node



    reset_dummy_state()
    injector = DummyFunctionInjector()
    injector.dummy_injection(root_node, num_dummy_functions=num_to_insert)
    return root_node
