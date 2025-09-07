import random
import string
from obfuscations import ast_nodes as ast

RESERVED_NAMES = {
    'main', 'printf', 'scanf', 'int', 'char', 'bool', 'void',
    'if', 'else', 'while', 'for', 'return', 'sum',
}


class RenamerVisitor:
    def __init__(self):
        self.rename_map_global_funcs = {}
        self.scope_stack = [{}]
        self.name_counters = {'var': 0, 'func': 0}

    def _generate_new_name(self, category='var'):
        self.name_counters[category] += 1
        prefix = "vv" if category == 'var' else "ff"
        suffix = ''.join(random.choices(string.ascii_lowercase, k=random.randint(2, 4)))
        return f"{prefix}{suffix}{self.name_counters[category]}"

    def enter_scope(self):
        self.scope_stack.append({})

    def exit_scope(self):
        self.scope_stack.pop()

    def declare_in_current_scope(self, old_name, new_name):
        if self.scope_stack: self.scope_stack[-1][old_name] = new_name

    def lookup_name(self, old_name):
        for scope in reversed(self.scope_stack):
            if old_name in scope: return scope[old_name]
        return self.rename_map_global_funcs.get(old_name)

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

    def visit_ProgramNode(self, node: ast.ProgramNode):
        self.enter_scope()
        for decl in node.declarations:
            if isinstance(decl, ast.FuncDefNode) and decl.name not in RESERVED_NAMES:
                if decl.name not in self.rename_map_global_funcs:
                    new_name = self._generate_new_name('func')
                    self.rename_map_global_funcs[decl.name] = new_name
                    self.declare_in_current_scope(decl.name, new_name)

        new_declarations = [self.visit(decl) for decl in node.declarations if decl is not None]
        node.declarations = [d for d in new_declarations if d is not None]
        self.exit_scope()
        return node

    def visit_FuncDefNode(self, node: ast.FuncDefNode):
        if node.name not in RESERVED_NAMES:
            node.name = self.lookup_name(node.name) or node.name
        self.enter_scope()
        if node.params:
            for param in node.params: self.visit(param)
        if node.body: self.visit(node.body)
        self.exit_scope()
        return node

    def visit_ParamNode(self, node: ast.ParamNode):
        if node.name not in RESERVED_NAMES:
            new_name = self._generate_new_name('var')
            self.declare_in_current_scope(node.name, new_name)
            node.name = new_name
        if node.type_node: self.visit(node.type_node)
        return node

    def visit_VarDeclNode(self, node: ast.VarDeclNode):
        if node.type_node: self.visit(node.type_node)
        if node.name not in RESERVED_NAMES:
            is_global_var = len(self.scope_stack) == 1
            if is_global_var:
                if node.name not in self.scope_stack[0]:
                    new_name = self._generate_new_name('var')
                    self.declare_in_current_scope(node.name, new_name)
                    node.name = new_name
                else:
                    node.name = self.scope_stack[0][node.name]
            else:
                new_name = self._generate_new_name('var')
                self.declare_in_current_scope(node.name, new_name)
                node.name = new_name
        if node.initializer: self.visit(node.initializer)
        return node

    def visit_IdNode(self, node: ast.IdNode):
        if node.name not in RESERVED_NAMES:
            renamed = self.lookup_name(node.name)
            if renamed: node.name = renamed
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


def apply_renaming(ast_root: ast.ProgramNode):
    renamer = RenamerVisitor()
    return renamer.visit(ast_root)