from obfuscations import ast_nodes as ast
from deobfuscations.name_restorer import RESERVED_NAMES


class SemanticRenamerVisitor:
    def __init__(self):
        self.name_map = {}
        self.used_names = set(RESERVED_NAMES)
        self.var_counter = 0
        self.func_counter = 0

    def _generate_unique_name(self, base_name):
        new_name = base_name
        counter = 1
        while new_name in self.used_names:
            new_name = f"{base_name}_{counter}"
            counter += 1
        self.used_names.add(new_name)
        return new_name

    def visit(self, node):
        if node is None:
            return None
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
                    new_list = [self.visit(item) if isinstance(item, ast.Node) else item for item in attr_value]
                    try:
                        setattr(node, attr_name, new_list)
                    except AttributeError:
                        pass
        return node

    def visit_ProgramNode(self, node: ast.ProgramNode):
        for decl in node.declarations:
            self.visit(decl)
        return node

    def visit_FuncDefNode(self, node: ast.FuncDefNode):
        # Semantic naming for functions (e.g., based on parameters or body content)
        if node.name not in RESERVED_NAMES:
            suggested_name = "func"
            if len(node.params) == 2 and isinstance(node.params[0], ast.ParamNode) and isinstance(node.params[1],
                                                                                                  ast.ParamNode):
                # Look for common binary operations in the function's return statement
                return_stmt = next((item for item in node.body.items if isinstance(item, ast.ReturnNode)), None)
                if return_stmt and isinstance(return_stmt.expr, ast.BinaryOpNode):
                    if return_stmt.expr.op == '+':
                        suggested_name = "sum"
                    elif return_stmt.expr.op == '-':
                        suggested_name = "diff"
                    elif return_stmt.expr.op == '*':
                        suggested_name = "product"
                    elif return_stmt.expr.op == '/':
                        suggested_name = "quotient"

            new_name = self._generate_unique_name(suggested_name)
            self.name_map[node.name] = new_name
            node.name = new_name

        # Visit function body and parameters
        if node.params:
            for param in node.params: self.visit(param)
        if node.body:
            self.visit(node.body)
        return node

    def visit_ParamNode(self, node: ast.ParamNode):
        if node.name not in RESERVED_NAMES:
            suggested_name = "arg"
            new_name = self._generate_unique_name(suggested_name)
            self.name_map[node.name] = new_name
            node.name = new_name
        return node

    def visit_VarDeclNode(self, node: ast.VarDeclNode):
        if node.name not in RESERVED_NAMES:
            suggested_name = "var"
            # Simple heuristic: if initializer is a function call, maybe the variable stores a result.
            if isinstance(node.initializer, ast.FuncCallNode):
                suggested_name = "result"

            new_name = self._generate_unique_name(suggested_name)
            self.name_map[node.name] = new_name
            node.name = new_name

        if node.initializer:
            self.visit(node.initializer)
        return node

    def visit_IdNode(self, node: ast.IdNode):
        # Remap IDs to new names
        if node.name in self.name_map:
            node.name = self.name_map[node.name]
        return node


def apply_semantic_renaming(ast_root: ast.ProgramNode):
    renamer = SemanticRenamerVisitor()
    return renamer.visit(ast_root)