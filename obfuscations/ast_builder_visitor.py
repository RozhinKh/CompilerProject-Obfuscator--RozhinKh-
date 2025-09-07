from antlr4 import TerminalNode
from grammer.MiniCParser import MiniCParser
from grammer.MiniCVisitor import MiniCVisitor
from obfuscations.ast_nodes import (
    ProgramNode, FuncDefNode, ParamNode, VarDeclNode, TypeNode, CompoundStatementNode,
    IdNode, ConstantNode, StringLiteralNode, BinaryOpNode, UnaryOpNode, FuncCallNode,
    AssignmentNode, ExprStatementNode, IfNode, WhileNode, ForNode, ReturnNode
)


def get_coord(ctx):
    if ctx and hasattr(ctx, 'start') and ctx.start:
        return (ctx.start.line, ctx.start.column)
    elif ctx and hasattr(ctx, 'symbol') and ctx.symbol:
        return (ctx.symbol.line, ctx.symbol.column)
    return None


class ASTBuilderVisitor(MiniCVisitor):
    def visitProgram(self, ctx: MiniCParser.ProgramContext):
        decls = []
        if ctx.externalDeclaration():
            for ext_decl_ctx in ctx.externalDeclaration():
                visited_decl = self.visit(ext_decl_ctx)
                if isinstance(visited_decl, list):
                    decls.extend(d for d in visited_decl if d is not None)
                elif visited_decl:
                    decls.append(visited_decl)
        return ProgramNode(declarations=decls, coord=get_coord(ctx))

    def visitExternalDeclaration(self, ctx: MiniCParser.ExternalDeclarationContext):
        if ctx.functionDefinition(): return self.visit(ctx.functionDefinition())
        if ctx.declaration(): return self.visit(ctx.declaration())
        return None

    def visitFunctionDefinition(self, ctx: MiniCParser.FunctionDefinitionContext):
        return_type_node = self.visit(ctx.typeSpecifier())
        func_name = ctx.declarator().Identifier().getText()
        params = self.visit(ctx.parameterList()) if ctx.parameterList() else []
        body = self.visit(ctx.compoundStatement())
        return FuncDefNode(return_type_node, func_name, params, body, coord=get_coord(ctx))

    def visitParameterList(self, ctx: MiniCParser.ParameterListContext):
        return [self.visit(p) for p in ctx.parameterDeclaration()] if ctx.parameterDeclaration() else []

    def visitParameterDeclaration(self, ctx: MiniCParser.ParameterDeclarationContext):
        type_node = self.visit(ctx.typeSpecifier())
        name = ctx.declarator().Identifier().getText()
        return ParamNode(type_node, name, coord=get_coord(ctx))

    def visitDeclaration(self, ctx: MiniCParser.DeclarationContext):
        type_node = self.visit(ctx.typeSpecifier())
        var_decls = []
        if ctx.initDeclaratorList():
            for init_decl_ctx in ctx.initDeclaratorList().initDeclarator():
                name = init_decl_ctx.declarator().Identifier().getText()
                initializer_node = self.visit(
                    init_decl_ctx.initializer().assignmentExpression()) if init_decl_ctx.initializer() else None
                var_decls.append(VarDeclNode(type_node, name, initializer_node, coord=get_coord(init_decl_ctx)))
        return var_decls

    def visitTypeSpecifier(self, ctx: MiniCParser.TypeSpecifierContext):
        return TypeNode(ctx.getText(), coord=get_coord(ctx))

    def visitCompoundStatement(self, ctx: MiniCParser.CompoundStatementContext):
        items = []
        if ctx.blockItemList():
            for item_ctx in ctx.blockItemList().blockItem():
                visited_item = self.visit(item_ctx)
                if isinstance(visited_item, list):
                    items.extend(d for d in visited_item if d is not None)
                elif visited_item:
                    items.append(visited_item)
        return CompoundStatementNode(items, coord=get_coord(ctx))

    def visitBlockItem(self, ctx: MiniCParser.BlockItemContext):
        if ctx.statement(): return self.visit(ctx.statement())
        if ctx.declaration(): return self.visit(ctx.declaration())
        return None

    def visitExpressionStatement(self, ctx: MiniCParser.ExpressionStatementContext):
        expr_node = self.visit(ctx.expression()) if ctx.expression() else None
        return ExprStatementNode(expr_node, coord=get_coord(ctx))

    def visitSelectionStatement(self, ctx: MiniCParser.SelectionStatementContext):
        cond = self.visit(ctx.expression())
        if_true_body = self.visit(ctx.statement(0))
        if_false_body = self.visit(ctx.statement(1)) if ctx.ELSE() else None
        return IfNode(cond, if_true_body, if_false_body, coord=get_coord(ctx))

    def visitIterationStatement(self, ctx: MiniCParser.IterationStatementContext):
        if ctx.WHILE():
            cond = self.visit(ctx.expression())
            body = self.visit(ctx.statement())
            return WhileNode(cond, body, coord=get_coord(ctx))
        if ctx.FOR():
            init_node, cond_expr_node, update_expr_node = None, None, None
            if ctx.declaration():
                init_decls = self.visit(ctx.declaration())
                if init_decls: init_node = init_decls[0]
            elif ctx.expressionStatement(0) and ctx.expressionStatement(0).expression():
                init_node = self.visit(ctx.expressionStatement(0).expression())

            cond_expr_stmt_ctx = ctx.expressionStatement(0) if ctx.declaration() and ctx.expressionStatement() else \
                (ctx.expressionStatement(1) if not ctx.declaration() and len(ctx.expressionStatement()) > 1 else None)
            if cond_expr_stmt_ctx and cond_expr_stmt_ctx.expression():
                cond_expr_node = self.visit(cond_expr_stmt_ctx.expression())

            if ctx.expression(): update_expr_node = self.visit(ctx.expression())
            body = self.visit(ctx.statement())
            return ForNode(init_node, cond_expr_node, update_expr_node, body, coord=get_coord(ctx))
        return None

    def visitJumpStatement(self, ctx: MiniCParser.JumpStatementContext):
        if ctx.RETURN():
            expr_node = self.visit(ctx.expression()) if ctx.expression() else None
            return ReturnNode(expr_node, coord=get_coord(ctx))
        return None

    def visitExpression(self, ctx: MiniCParser.ExpressionContext):
        return self.visit(ctx.assignmentExpression()) if ctx.assignmentExpression() else None

    def visitAssignmentExpression(self, ctx: MiniCParser.AssignmentExpressionContext):
        if ctx.ASSIGN() and ctx.assignmentExpression():
            lvalue = self.visit(ctx.conditionalExpression())
            op = ctx.ASSIGN().getText()
            rvalue = self.visit(ctx.assignmentExpression())
            return AssignmentNode(lvalue, rvalue, op, coord=get_coord(ctx))
        return self.visit(ctx.conditionalExpression())

    def visitConditionalExpression(self, ctx: MiniCParser.ConditionalExpressionContext):
        return self.visit(ctx.logicalOrExpression())

    def _build_left_associative_binary_op_tree(self, operand_contexts, operator_nodes_list, visit_operand_method):
        if not operand_contexts: return None
        left_ast_node = visit_operand_method(operand_contexts[0])
        for i, op_terminal_node in enumerate(operator_nodes_list):
            op_text = op_terminal_node.getText()
            right_ast_node = visit_operand_method(operand_contexts[i + 1])
            left_ast_node = BinaryOpNode(op_text, left_ast_node, right_ast_node, coord=get_coord(op_terminal_node))
        return left_ast_node

    def _get_all_op_terminals(self, ctx, op_types):
        terminals = []
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            if isinstance(child, TerminalNode) and child.getSymbol().type in op_types:
                terminals.append(child)
        return terminals

    def visitLogicalOrExpression(self, ctx: MiniCParser.LogicalOrExpressionContext):
        ops = self._get_all_op_terminals(ctx, [MiniCParser.OR_OP])
        return self._build_left_associative_binary_op_tree(ctx.logicalAndExpression(), ops,
                                                           self.visitLogicalAndExpression) if ops else self.visit(
            ctx.logicalAndExpression(0))

    def visitLogicalAndExpression(self, ctx: MiniCParser.LogicalAndExpressionContext):
        ops = self._get_all_op_terminals(ctx, [MiniCParser.AND_OP])
        return self._build_left_associative_binary_op_tree(ctx.equalityExpression(), ops,
                                                           self.visitEqualityExpression) if ops else self.visit(
            ctx.equalityExpression(0))

    def visitEqualityExpression(self, ctx: MiniCParser.EqualityExpressionContext):
        ops = self._get_all_op_terminals(ctx, [MiniCParser.EQ_OP, MiniCParser.NE_OP])
        return self._build_left_associative_binary_op_tree(ctx.relationalExpression(), ops,
                                                           self.visitRelationalExpression) if ops else self.visit(
            ctx.relationalExpression(0))

    def visitRelationalExpression(self, ctx: MiniCParser.RelationalExpressionContext):
        ops = self._get_all_op_terminals(ctx,
                                         [MiniCParser.LT_OP, MiniCParser.GT_OP, MiniCParser.LE_OP, MiniCParser.GE_OP])
        return self._build_left_associative_binary_op_tree(ctx.additiveExpression(), ops,
                                                           self.visitAdditiveExpression) if ops else self.visit(
            ctx.additiveExpression(0))

    def visitAdditiveExpression(self, ctx: MiniCParser.AdditiveExpressionContext):
        ops = self._get_all_op_terminals(ctx, [MiniCParser.PLUS, MiniCParser.MINUS])
        return self._build_left_associative_binary_op_tree(ctx.multiplicativeExpression(), ops,
                                                           self.visitMultiplicativeExpression) if ops else self.visit(
            ctx.multiplicativeExpression(0))

    def visitMultiplicativeExpression(self, ctx: MiniCParser.MultiplicativeExpressionContext):
        ops = self._get_all_op_terminals(ctx, [MiniCParser.MUL, MiniCParser.DIV, MiniCParser.MOD])
        return self._build_left_associative_binary_op_tree(ctx.unaryExpression(), ops,
                                                           self.visitUnaryExpression) if ops else self.visit(
            ctx.unaryExpression(0))

    def visitUnaryExpression(self, ctx: MiniCParser.UnaryExpressionContext):
        if ctx.unaryOperator():
            op = ctx.unaryOperator().getText()
            expr = self.visit(ctx.unaryExpression())
            return UnaryOpNode(op, expr, coord=get_coord(ctx.unaryOperator()))
        return self.visit(ctx.postfixExpression())

    def visitPostfixExpression(self, ctx: MiniCParser.PostfixExpressionContext):
        node = self.visit(ctx.primaryExpression())
        idx = 0
        while ctx.LPAREN(idx) is not None:
            args = self.visit(ctx.argumentExpressionList(idx)) if ctx.argumentExpressionList(idx) else []
            node = FuncCallNode(node, args, coord=get_coord(ctx.LPAREN(idx)))
            idx += 1
        return node

    def visitArgumentExpressionList(self, ctx: MiniCParser.ArgumentExpressionListContext):
        return [self.visit(arg) for arg in ctx.assignmentExpression()] if ctx.assignmentExpression() else []

    def visitPrimaryExpression(self, ctx: MiniCParser.PrimaryExpressionContext):
        if ctx.Identifier(): return IdNode(ctx.Identifier().getText(), coord=get_coord(ctx.Identifier()))
        if ctx.constant():
            const_parse_ctx = ctx.constant()
            if const_parse_ctx.IntegerConstant(): return ConstantNode('int',
                                                                      const_parse_ctx.IntegerConstant().getText(),
                                                                      coord=get_coord(
                                                                          const_parse_ctx.IntegerConstant()))
            if const_parse_ctx.CharacterConstant(): return ConstantNode('char',
                                                                        const_parse_ctx.CharacterConstant().getText(),
                                                                        coord=get_coord(
                                                                            const_parse_ctx.CharacterConstant()))
        if ctx.StringLiteral(): return StringLiteralNode(ctx.StringLiteral().getText(),
                                                         coord=get_coord(ctx.StringLiteral()))
        if ctx.expression(): return self.visit(ctx.expression())
        return None