from obfuscations import ast_nodes as ast


class AdvancedFlowReconstructorVisitor:
    """
    A visitor that restructures a specific obfuscated control flow pattern.
    It looks for a while loop containing a state machine pattern and flattens it.
    """

    def visit(self, node):
        if node is None:
            return None
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
                    new_list = [self.visit(item) for item in attr_value]
                    try:
                        setattr(node, attr_name, new_list)
                    except AttributeError:
                        pass
        return node

    def visit_CompoundStatementNode(self, node: ast.CompoundStatementNode):
        new_items = []
        for item in node.items:
            # Visit the item to apply transformations recursively
            visited_item = self.visit(item)
            if isinstance(visited_item, list):
                new_items.extend(visited_item)
            elif visited_item:
                new_items.append(visited_item)
        node.items = new_items
        return node

    def visit_WhileNode(self, node: ast.WhileNode):
        # A simplified check for a 'while-switch' pattern.
        # This implementation looks for a `while` loop with a simple conditional
        # that can be unrolled. This is a common obfuscation pattern.

        # Check if the while loop's condition is simple (e.g., `selector > 0`)
        # and its body is a compound statement.
        is_obfuscated_loop = False
        if isinstance(node.cond, ast.BinaryOpNode):
            if isinstance(node.cond.left, ast.IdNode) and isinstance(node.cond.right, ast.ConstantNode):
                is_obfuscated_loop = True

        # If the body is simple enough, we can flatten it.
        if is_obfuscated_loop and isinstance(node.body, ast.CompoundStatementNode):
            # This logic assumes the obfuscated loop contains a sequence of statements
            # that we can safely reorder or "unroll."
            flattened_statements = []
            for item in node.body.items:
                if isinstance(item, ast.ExprStatementNode):
                    # We can directly add simple expression statements
                    flattened_statements.append(item)
                elif isinstance(item, ast.IfNode):
                    # We can recursively simplify nested control flow if needed.
                    simplified_if = self.visit(item)
                    flattened_statements.append(simplified_if)
                else:
                    # If we encounter a complex statement, we stop unrolling for safety.
                    # In a real tool, this would be handled with more advanced analysis.
                    return self.generic_visit(node)

            return flattened_statements

        return self.generic_visit(node)


def apply_flow_reconstruction(ast_root: ast.ProgramNode):
    reconstructor = AdvancedFlowReconstructorVisitor()
    return reconstructor.visit(ast_root)