import random
from obfuscations import ast_nodes as ast

class DeadCodeInserterVisitor:
    def __init__(self):
        self.dead_var_counter = 0

    def _generate_dead_var_name(self):
        self.dead_var_counter += 1
        return f"unused_dead_var_{self.dead_var_counter}"

    def _create_dead_variable_declaration(self):
        var_name = self._generate_dead_var_name()
        type_node = ast.TypeNode(name="int")
        initializer_node = ast.ConstantNode(type="int", value=str(random.randint(1000,9999)))
        return ast.VarDeclNode(type_node=type_node, name=var_name, initializer=initializer_node)

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

    def visit_CompoundStatementNode(self, node: ast.CompoundStatementNode):
        new_items = []
        for item in node.items:
            visited_item = self.visit(item)
            if isinstance(visited_item, list): new_items.extend(v for v in visited_item if v is not None)
            elif visited_item is not None: new_items.append(visited_item)
        node.items = new_items
        if random.random() < 0.3:
            node.items.insert(0, self._create_dead_variable_declaration())
        return node

def apply_dead_code_insertion(ast_root: ast.ProgramNode):
    inserter = DeadCodeInserterVisitor()
    return inserter.visit(ast_root)