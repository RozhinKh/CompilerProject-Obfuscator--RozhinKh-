from pycparser import c_ast

class EquivalentExpression(c_ast.NodeVisitor):

    def visit_BinaryOp(self, node):
        self.generic_visit(node)

        if node.op == '+':
            if isinstance(node.right, (c_ast.ID, c_ast.Constant)) and \
                    not (isinstance(node.right, c_ast.Constant) and node.right.value.startswith('-')):
                negated_right_operand = c_ast.UnaryOp(op='-', expr=node.right)
                node.op = '-'
                node.right = negated_right_operand
                return
        elif node.op == '-':
            if isinstance(node.right, (c_ast.ID, c_ast.Constant)) and \
                    not (isinstance(node.right, c_ast.Constant) and node.right.value.startswith('-')):
                negated_right_operand = c_ast.UnaryOp(op='-', expr=node.right)
                node.op = '+'
                node.right = negated_right_operand
                return

def apply_equivalent_expression(root_node):
    replacer_visitor = EquivalentExpression()
    replacer_visitor.visit(root_node)
    return root_node
