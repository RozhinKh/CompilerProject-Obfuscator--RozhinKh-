from pycparser import c_ast
import random

OPAQUE_PREFIX = "opaque_var_"
opaque_counters = {'var': 0}

def opaque_predicate_var_name():
    opaque_counters['var'] += 1
    return f"{OPAQUE_PREFIX}{opaque_counters['var']}"

def reset_opaque_state():
    opaque_counters['var'] = 0

class OpaquePredicateInserter(c_ast.NodeVisitor):
    def create_opaque_if(self):
        predicate_var_name = opaque_predicate_var_name()
        known_value = random.randint(1, 100)

        declaration_predicate_var = c_ast.Decl(
            name=predicate_var_name, quals=[], storage=[], funcspec=[],
            type=c_ast.TypeDecl(declname=predicate_var_name, quals=[], type=c_ast.IdentifierType(['int']), align=None),
            init=c_ast.Constant('int', str(known_value)), bitsize=None, align=None
        )

        always_true = random.choice([True, False])

        if always_true:
            opaque_condition = c_ast.BinaryOp('==',
                                              c_ast.ID(name=predicate_var_name),
                                              c_ast.Constant('int', str(known_value)))

            true_var_name = opaque_predicate_var_name()
            true_declaration = c_ast.Decl(
                name=true_var_name, quals=[], storage=[], funcspec=[],
                type=c_ast.TypeDecl(declname=true_var_name, quals=[], type=c_ast.IdentifierType(['int']),
                                    align=None),
                init=c_ast.Constant('int', '1'), bitsize=None, align=None
            )
            true_body = c_ast.Compound(block_items=[true_declaration])

            false_var_name = opaque_predicate_var_name()
            false_declaration = c_ast.Decl(
                name=false_var_name, quals=[], storage=[], funcspec=[],
                type=c_ast.TypeDecl(declname=false_var_name, quals=[], type=c_ast.IdentifierType(['int']),
                                    align=None),
                init=c_ast.Constant('int', '0'), bitsize=None, align=None
            )
            false_body = c_ast.Compound(block_items=[false_declaration])

            opaque_if_statement = c_ast.If(cond=opaque_condition, iftrue=true_body, iffalse=false_body)

        else:
            opaque_condition = c_ast.BinaryOp('==',
                                              c_ast.ID(name=predicate_var_name),
                                              c_ast.Constant('int', str(known_value + 1)))  # Make it false

            true_var_name = opaque_predicate_var_name()
            true_declaration = c_ast.Decl(
                name=true_var_name, quals=[], storage=[], funcspec=[],
                type=c_ast.TypeDecl(declname=true_var_name, quals=[], type=c_ast.IdentifierType(['int']),
                                    align=None),
                init=c_ast.Constant('int', '0'), bitsize=None, align=None  # Dead code
            )
            true_body = c_ast.Compound(block_items=[true_declaration])

            false_var_name = opaque_predicate_var_name()
            false_declaration = c_ast.Decl(
                name=false_var_name, quals=[], storage=[], funcspec=[],
                type=c_ast.TypeDecl(declname=false_var_name, quals=[], type=c_ast.IdentifierType(['int']),
                                    align=None),
                init=c_ast.Constant('int', '1'), bitsize=None, align=None
            )
            false_body = c_ast.Compound(block_items=[false_declaration])

            opaque_if_statement = c_ast.If(cond=opaque_condition, iftrue=true_body, iffalse=false_body)

        return [declaration_predicate_var, opaque_if_statement]

    def visit_Compound(self, node):
        self.generic_visit(node)

        if node.block_items is None: node.block_items = []

        if random.random() < 0.15:
            opaque_statement_list = self.create_opaque_if()
            if opaque_statement_list:
                node.block_items = opaque_statement_list + node.block_items


def apply_opaque_predicates(root_node):
    reset_opaque_state()
    inserter = OpaquePredicateInserter()
    inserter.visit(root_node)
    return root_node
