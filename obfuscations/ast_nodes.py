class Node:
    def __init__(self, coord=None):
        self.coord = coord
    def __repr__(self):
        attrs = [f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith('_') and k != 'coord']
        return f"{self.__class__.__name__}({', '.join(attrs)})"

class ProgramNode(Node):
    def __init__(self, declarations, coord=None):
        super().__init__(coord)
        self.declarations = declarations

class FuncDefNode(Node):
    def __init__(self, return_type, name, params, body, coord=None):
        super().__init__(coord)
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body

class ParamNode(Node):
    def __init__(self, type_node, name, coord=None):
        super().__init__(coord)
        self.type_node = type_node
        self.name = name

class VarDeclNode(Node):
    def __init__(self, type_node, name, initializer=None, coord=None):
        super().__init__(coord)
        self.type_node = type_node
        self.name = name
        self.initializer = initializer

class TypeNode(Node):
    def __init__(self, name, coord=None):
        super().__init__(coord)
        self.name = name

class CompoundStatementNode(Node):
    def __init__(self, items, coord=None):
        super().__init__(coord)
        self.items = items if items is not None else []

class ExpressionNode(Node): pass

class IdNode(ExpressionNode):
    def __init__(self, name, coord=None):
        super().__init__(coord)
        self.name = name

class ConstantNode(ExpressionNode):
    def __init__(self, type, value, coord=None):
        super().__init__(coord)
        self.type = type
        self.value = value

class StringLiteralNode(ExpressionNode):
    def __init__(self, value, coord=None):
        super().__init__(coord)
        self.value = value

class BinaryOpNode(ExpressionNode):
    def __init__(self, op, left, right, coord=None):
        super().__init__(coord)
        self.op = op
        self.left = left
        self.right = right

class UnaryOpNode(ExpressionNode):
    def __init__(self, op, expr, coord=None):
        super().__init__(coord)
        self.op = op
        self.expr = expr

class FuncCallNode(ExpressionNode):
    def __init__(self, name_expr, args, coord=None):
        super().__init__(coord)
        self.name_expr = name_expr
        self.args = args if args is not None else []

class AssignmentNode(ExpressionNode):
    def __init__(self, lvalue, rvalue, op="=", coord=None):
        super().__init__(coord)
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.op = op

class StatementNode(Node): pass

class ExprStatementNode(StatementNode):
    def __init__(self, expr, coord=None):
        super().__init__(coord)
        self.expr = expr

class IfNode(StatementNode):
    def __init__(self, cond, if_true_body, if_false_body=None, coord=None):
        super().__init__(coord)
        self.cond = cond
        self.if_true_body = if_true_body
        self.if_false_body = if_false_body

class WhileNode(StatementNode):
    def __init__(self, cond, body, coord=None):
        super().__init__(coord)
        self.cond = cond
        self.body = body

class ForNode(StatementNode):
    def __init__(self, init, cond, update, body, coord=None):
        super().__init__(coord)
        self.init = init
        self.cond = cond
        self.update = update
        self.body = body

class ReturnNode(StatementNode):
    def __init__(self, expr=None, coord=None):
        super().__init__(coord)
        self.expr = expr