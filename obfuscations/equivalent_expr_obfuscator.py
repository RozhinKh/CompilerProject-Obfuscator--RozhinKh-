import random
from obfuscations import ast_nodes as ast

class EquivalentExpressionVisitor:
    def visit(self, node):
        if node is None: return None
        method_name = 'visit_' + node.__class__.__name__
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node: ast.Node):
        for attr_name in dir(node):
            if not attr_name.startswith('_') and attr_name != 'coord':
                attr_value = getattr(node, attr_name)
                if isinstance(attr_value, ast.Node): setattr(node, attr_name, self.visit(attr_value))
                elif isinstance(attr_value, list):
                    new_list = []
                    for item in attr_value:
                        if isinstance(item, ast.Node):
                            visited_item = self.visit(item)
                            if isinstance(visited_item, list): new_list.extend(v for v in visited_item if v is not None)
                            elif visited_item is not None: new_list.append(visited_item)
                        else: new_list.append(item)
                    try: setattr(node, attr_name, new_list)
                    except AttributeError: pass
        return node

    def visit_BinaryOpNode(self, node: ast.BinaryOpNode):
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)
        if random.random() < 0.5:
            if node.op == '+' and not (isinstance(node.right, ast.UnaryOpNode) and node.right.op == '-'):
                negated_right = ast.UnaryOpNode(op='-', expr=node.right, coord=node.right.coord)
                node.op, node.right = '-', negated_right
            elif node.op == '-' and not (isinstance(node.right, ast.UnaryOpNode) and node.right.op == '-'):
                negated_right = ast.UnaryOpNode(op='-', expr=node.right, coord=node.right.coord)
                node.op, node.right = '+', negated_right
        return node

def apply_equivalent_expression(ast_root: ast.ProgramNode):
    transformer = EquivalentExpressionVisitor()
    return transformer.visit(ast_root)