import random
from obfuscations import ast_nodes as ast


class OpaquePredicateInserterVisitor:
    def __init__(self):
        self.opaque_var_counter = 0

    def _generate_opaque_var_name(self):
        self.opaque_var_counter += 1
        return f"opq_ctrl_{self.opaque_var_counter}"

    def _create_opaque_predicate_construct(self):
        p_var = self._generate_opaque_var_name();
        known_val = random.randint(1, 100)
        decl_p_var = ast.VarDeclNode(ast.TypeNode("int"), p_var, ast.ConstantNode("int", str(known_val)))

        always_true = random.choice([True, False])
        op, val_to_compare = ('==', known_val) if always_true else ('!=', known_val)
        condition = ast.BinaryOpNode(op, ast.IdNode(p_var), ast.ConstantNode("int", str(val_to_compare)))

        true_body_var = self._generate_opaque_var_name() + ("_t" if always_true else "_t_dead")
        true_decl = ast.VarDeclNode(ast.TypeNode("int"), true_body_var, ast.ConstantNode("int", "1"))
        if_true = ast.CompoundStatementNode(items=[true_decl])

        false_body_var = self._generate_opaque_var_name() + ("_f_dead" if always_true else "_f")
        false_decl = ast.VarDeclNode(ast.TypeNode("int"), false_body_var,
                                     ast.ConstantNode("int", "0" if always_true else "1"))
        if_false = ast.CompoundStatementNode(items=[false_decl])

        return [decl_p_var, ast.IfNode(condition, if_true, if_false)]

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
                            visited_item = self.visit(item)
                            if isinstance(visited_item, list):
                                new_list.extend(v for v in visited_item if v is not None)
                            elif visited_item is not None:
                                new_list.append(visited_item)
                        else:
                            new_list.append(item)
                    try:
                        setattr(node, attr_name, new_list)
                    except AttributeError:
                        pass
        return node

    def visit_CompoundStatementNode(self, node: ast.CompoundStatementNode):
        new_items = []
        for item in node.items:
            visited_item = self.visit(item)
            if isinstance(visited_item, list):
                new_items.extend(v for v in visited_item if v is not None)
            elif visited_item is not None:
                new_items.append(visited_item)
        node.items = new_items

        if random.random() < 0.2:
            opaque_constructs = self._create_opaque_predicate_construct()
            insert_pos = random.randint(0, len(node.items))
            for i, construct_item in enumerate(reversed(opaque_constructs)):
                node.items.insert(insert_pos, construct_item)
        return node


def apply_opaque_predicates(ast_root: ast.ProgramNode):
    inserter = OpaquePredicateInserterVisitor()
    return inserter.visit(ast_root)