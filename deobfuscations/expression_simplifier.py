from obfuscations import ast_nodes as ast


class ExpressionSimplifierVisitor:
    def visit(self, node):
        if node is None: return None
        method_name = 'visit_' + node.__class__.__name__
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node: ast.Node):
        for attr_name in dir(node):
            if not attr_name.startswith('_') and attr_name != 'coord':
                attr_value = getattr(node, attr_name)
                if isinstance(attr_value, ast.Node):
                    setattr(node, attr_name, self.visit(attr_value))
                elif isinstance(attr_value, list):
                    new_list = []
                    for item in attr_value:
                        if isinstance(item, ast.Node):
                            new_list.append(self.visit(item))
                        else:
                            new_list.append(item)
                    try:
                        setattr(node, attr_name, new_list)
                    except AttributeError:
                        pass
        return node

    def visit_BinaryOpNode(self, node: ast.BinaryOpNode):
        # Recursively visit children first
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)

        # Simplify specific patterns
        # Pattern: a - (-b) -> a + b
        if node.op == '-' and isinstance(node.right, ast.UnaryOpNode) and node.right.op == '-':
            node.op = '+'
            node.right = node.right.expr

        return node


def apply_expression_simplification(ast_root: ast.ProgramNode):
    simplifier = ExpressionSimplifierVisitor()
    return simplifier.visit(ast_root)