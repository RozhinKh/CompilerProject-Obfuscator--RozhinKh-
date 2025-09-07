from obfuscations.ast_nodes import (
    ProgramNode, FuncDefNode, ParamNode, VarDeclNode, TypeNode, CompoundStatementNode,
    IdNode, ConstantNode, StringLiteralNode, BinaryOpNode, UnaryOpNode, FuncCallNode,
    AssignmentNode, ExprStatementNode, IfNode, WhileNode, ForNode, ReturnNode, Node
)


class CCodeGenerator:
    def __init__(self):
        self.indent_level = 0
        self.is_global_scope = True

    def _indent(self):
        return "    " * self.indent_level

    def visit(self, node):
        if node is None: return ""
        method_name = 'visit_' + node.__class__.__name__
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node):
        print(f"CCodeGenerator Warning: No specific visit method for {node.__class__.__name__}")
        return f"/* Unhandled Node: {node.__class__.__name__} */"

    def visit_ProgramNode(self, node: ProgramNode):
        self.is_global_scope = True
        output = [self.visit(decl) for decl in node.declarations if decl]
        self.is_global_scope = False
        return "\n\n".join(output)

    def visit_FuncDefNode(self, node: FuncDefNode):
        self.is_global_scope = False
        params_str = ", ".join(self.visit(p) for p in node.params) if node.params else "void"
        if not node.params and self.visit(node.return_type) == "void" and node.name == "main": params_str = ""

        return f"{self.visit(node.return_type)} {node.name}({params_str}) {self.visit(node.body)}"

    def visit_ParamNode(self, node: ParamNode):
        return f"{self.visit(node.type_node)} {node.name}"

    def visit_VarDeclNode(self, node: VarDeclNode):
        s = "" if self.is_global_scope else self._indent()
        s += f"{self.visit(node.type_node)} {node.name}"
        if node.initializer: s += f" = {self.visit(node.initializer)}"
        s += ";"
        return s

    def visit_TypeNode(self, node: TypeNode):
        return node.name

    def visit_IdNode(self, node: IdNode):
        return node.name

    def visit_ConstantNode(self, node: ConstantNode):
        return node.value

    def visit_StringLiteralNode(self, node: StringLiteralNode):
        return node.value

    def visit_CompoundStatementNode(self, node: CompoundStatementNode):
        code = "{\n"
        self.indent_level += 1
        for item in node.items:
            if item is None: continue
            item_code = self.visit(item)
            if isinstance(item, VarDeclNode):
                code += item_code + "\n"
            elif item_code.strip():
                code += self._indent() + item_code + "\n"
        self.indent_level -= 1
        code += self._indent() + "}"
        return code

    def visit_BinaryOpNode(self, node: BinaryOpNode):
        return f"({self.visit(node.left)} {node.op} {self.visit(node.right)})"

    def visit_UnaryOpNode(self, node: UnaryOpNode):
        expr_code = self.visit(node.expr)
        if isinstance(node.expr, BinaryOpNode): expr_code = f"({expr_code})"
        return f"{node.op}{expr_code}"

    def visit_FuncCallNode(self, node: FuncCallNode):
        args_str = ", ".join(self.visit(arg) for arg in node.args)
        return f"{self.visit(node.name_expr)}({args_str})"

    def visit_AssignmentNode(self, node: AssignmentNode):
        return f"{self.visit(node.lvalue)} {node.op} {self.visit(node.rvalue)}"

    def visit_ExprStatementNode(self, node: ExprStatementNode):
        return f"{self.visit(node.expr)};" if node.expr else ";"

    def _format_body(self, body_node, body_code_str):
        if not isinstance(body_node, CompoundStatementNode):
            res = "\n"
            self.indent_level += 1
            res += self._indent() + body_code_str
            if not body_code_str.strip().endswith(";") and not body_code_str.strip().endswith("}"): res += ";"
            res += "\n"
            self.indent_level -= 1
            return res
        return " " + body_code_str

    def visit_IfNode(self, node: IfNode):
        code = f"if ({self.visit(node.cond)})"
        code += self._format_body(node.if_true_body, self.visit(node.if_true_body))

        if node.if_false_body:
            if isinstance(node.if_true_body, CompoundStatementNode):
                code += " "
            else:
                code += self._indent()
            code += "else"
            code += self._format_body(node.if_false_body, self.visit(node.if_false_body))
        return code.strip()

    def visit_WhileNode(self, node: WhileNode):
        code = f"while ({self.visit(node.cond)})"
        code += self._format_body(node.body, self.visit(node.body))
        return code

    def visit_ForNode(self, node: ForNode):
        init_str = ""
        if isinstance(node.init, VarDeclNode):
            original_is_global, self.is_global_scope = self.is_global_scope, False
            init_str = self.visit(node.init).rstrip(';')
            self.is_global_scope = original_is_global
        elif node.init:
            init_str = self.visit(node.init)

        cond_str = self.visit(node.cond) if node.cond else ""
        update_str = self.visit(node.update) if node.update else ""
        code = f"for ({init_str}; {cond_str}; {update_str})"
        code += self._format_body(node.body, self.visit(node.body))
        return code

    def visit_ReturnNode(self, node: ReturnNode):
        return f"return {self.visit(node.expr)};" if node.expr else "return;"