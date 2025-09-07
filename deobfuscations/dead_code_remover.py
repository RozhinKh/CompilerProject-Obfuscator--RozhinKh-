from obfuscations import ast_nodes as ast


class VariableUsageVisitor:
    def __init__(self):
        self.used_vars = set()
        self.declared_vars = set()

    def visit(self, node):
        if node is None: return
        method_name = 'visit_' + node.__class__.__name__
        visitor_method = getattr(self, method_name, self.generic_visit)
        visitor_method(node)

    def generic_visit(self, node):
        for attr_name in dir(node):
            if not attr_name.startswith('_') and attr_name != 'coord':
                attr_value = getattr(node, attr_name)
                if isinstance(attr_value, ast.Node):
                    self.visit(attr_value)
                elif isinstance(attr_value, list):
                    for item in attr_value:
                        if isinstance(item, ast.Node):
                            self.visit(item)

    def visit_IdNode(self, node: ast.IdNode):
        self.used_vars.add(node.name)

    def visit_VarDeclNode(self, node: ast.VarDeclNode):
        self.declared_vars.add(node.name)
        if node.initializer:
            self.visit(node.initializer)

    def visit_FuncDefNode(self, node: ast.FuncDefNode):
        # Visit function body to find used variables
        if node.body:
            self.visit(node.body)


def apply_dead_code_removal(ast_root: ast.ProgramNode):
    # Pass 1: Find all declared and used variables
    usage_visitor = VariableUsageVisitor()
    usage_visitor.visit(ast_root)

    dead_vars = usage_visitor.declared_vars - usage_visitor.used_vars

    # Pass 2: Remove dead code from the AST
    new_declarations = []
    for decl in ast_root.declarations:
        if isinstance(decl, ast.FuncDefNode):
            # Clean dead vars inside function bodies
            new_items = []
            if decl.body:
                for item in decl.body.items:
                    if isinstance(item, ast.VarDeclNode) and item.name in dead_vars:
                        # Skip dead variable declarations
                        continue
                    new_items.append(item)
                decl.body.items = new_items
            new_declarations.append(decl)
        elif isinstance(decl, ast.VarDeclNode) and decl.name in dead_vars:
            # Skip global dead variable declarations
            continue
        else:
            new_declarations.append(decl)

    ast_root.declarations = new_declarations
    return ast_root