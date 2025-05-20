from pycparser import c_ast
import random

PREFIX_DEADCODE = "deadcode_"
deadcode_counters = {'var': 0}


def generate_deadcode_variable_name():
    deadcode_counters['var'] += 1
    return f"{PREFIX_DEADCODE}{deadcode_counters['var']}"


def reset_dead_code_state():
    deadcode_counters['var'] = 0


class DeadCodeInserter(c_ast.NodeVisitor):

    def create_dead_variable(self):
        temp_dead_var_name = generate_deadcode_variable_name()
        return c_ast.Decl(
            name=temp_dead_var_name,
            quals=[], storage=[], funcspec=[],
            type=c_ast.TypeDecl(
                declname=temp_dead_var_name,
                quals=[],
                type=c_ast.IdentifierType(['int']),
                align=None
            ),
            init=c_ast.Constant('int', str(random.randint(1000, 2000))),
            bitsize=None,
            align=None
        )

    def visit_Compound(self, node):
        if node.block_items is None: node.block_items = []

        dead_var_decl = self.create_dead_variable()
        node.block_items.insert(0, dead_var_decl)

        self.generic_visit(node)


def apply_dead_code_insertion(ast_root_node):
    reset_dead_code_state()
    inserter_visitor = DeadCodeInserter()
    inserter_visitor.visit(ast_root_node)
    return ast_root_node