import string
import random
from obfuscations import ast_nodes as ast

RESERVED_NAMES = {
    'main', 'printf', 'scanf', 'int', 'char', 'bool', 'void',
    'if', 'else', 'while', 'for', 'return', 'sum', 'puts'
}


class NameRestorerVisitor:
    def __init__(self):
        self.var_counter = 0
        self.func_counter = 0
        self.name_map = {}
        self.scope_stack = [{}]

    def _generate_new_var_name(self):
        self.var_counter += 1
        return f"var_{self.var_counter}"

    def _generate_new_func_name(self):
        self.func_counter += 1
        return f"func_{self.func_counter}"

    def enter_scope(self):
        self.scope_stack.append({})

    def exit_scope(self):
        self.scope_stack.pop()

    def _get_new_name(self, old_name, category):
        if old_name in RESERVED_NAMES:
            return old_name

        # Check if the name is already mapped in the current or parent scopes
        for scope in reversed(self.scope_stack):
            if old_name in scope:
                return scope[old_name]

        # If not found, generate a new name and map it
        if category == 'var':
            new_name = self._generate_new_var_name()
        elif category == 'func':
            new_name = self._generate_new_func_name()
        else:
            new_name = old_name

        self.scope_stack[-1][old_name] = new_name
        return new_name

    def visit(self, node):
        if node is None: return None
        method_name = 'visit_' + node.__class__.__name__
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node):
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

    def visit_ProgramNode(self, node: ast.ProgramNode):
        self.enter_scope()
        # First pass to register global functions and variables
        for decl in node.declarations:
            if isinstance(decl, ast.FuncDefNode) and decl.name not in RESERVED_NAMES:
                self._get_new_name(decl.name, 'func')
            elif isinstance(decl, ast.VarDeclNode) and decl.name not in RESERVED_NAMES:
                self._get_new_name(decl.name, 'var')

        for decl in node.declarations:
            self.visit(decl)
        self.exit_scope()
        return node

    def visit_FuncDefNode(self, node: ast.FuncDefNode):
        node.name = self._get_new_name(node.name, 'func')
        self.enter_scope()
        if node.params:
            for param in node.params: self.visit(param)
        if node.body: self.visit(node.body)
        self.exit_scope()
        return node

    def visit_ParamNode(self, node: ast.ParamNode):
        node.name = self._get_new_name(node.name, 'var')
        return node

    def visit_VarDeclNode(self, node: ast.VarDeclNode):
        node.name = self._get_new_name(node.name, 'var')
        if node.initializer: self.visit(node.initializer)
        return node

    def visit_IdNode(self, node: ast.IdNode):
        node.name = self._get_new_name(node.name, 'var')
        return node

    def visit_FuncCallNode(self, node: ast.FuncCallNode):
        # We only visit the name part if it's an IdNode, not a complex expression
        if isinstance(node.name_expr, ast.IdNode):
            node.name_expr.name = self._get_new_name(node.name_expr.name, 'func')

        # Visit arguments
        if node.args:
            node.args = [self.visit(arg) for arg in node.args]
        return node

    def visit_CompoundStatementNode(self, node: ast.CompoundStatementNode):
        self.enter_scope()
        new_items = []
        for item in node.items:
            visited = self.visit(item)
            if isinstance(visited, list):
                new_items.extend(v for v in visited if v is not None)
            elif visited is not None:
                new_items.append(visited)
        node.items = new_items
        self.exit_scope()
        return node


def apply_name_restoration(ast_root: ast.ProgramNode):
    restorer = NameRestorerVisitor()
    return restorer.visit(ast_root)