from pycparser import c_ast

rename_name = {}

rename_name_counters = {
    'var': 0,
    'func': 0,
}

PREFIXES = {
    'var': "var",
    'func': "xyz",
}

RESERVED_NAMES = {
    'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'float', 'for', 'if', 'int', 'long',
    'return', 'static','struct', 'switch', 'void', 'while'
}


VARIABLE_PREFIXES = ["deadcode_", "dummyVariable_", "opaque_var_"]
FUNCTION_PREFIXES = ["dummyFunction_"]


def name_for_category(name, category_prefixes):
    for prefix in category_prefixes:
        if name.startswith(prefix):
            return True
    return False


def generate_obfuscated_name(category_key):
    rename_name_counters[category_key] += 1
    prefix = PREFIXES[category_key]
    return f"{prefix}{rename_name_counters[category_key]}"


def get_or_create_renamed_name(original_name, category_key):
    if original_name in RESERVED_NAMES:
        return original_name
    actual_category_key_for_cache = category_key if category_key == 'func' else 'var'
    cache_key = (original_name, actual_category_key_for_cache)

    if cache_key not in rename_name:
        rename_name[cache_key] = generate_obfuscated_name(actual_category_key_for_cache)
    return rename_name[cache_key]


def reset_renaming_state():
    rename_name.clear()
    for key in rename_name_counters:
        rename_name_counters[key] = 0


class IdentifierRenamer(c_ast.NodeVisitor):

    def visit_ID(self, node):
        if node.name in RESERVED_NAMES:
            return

        renamed_as_func = rename_name.get((node.name, 'func'))
        renamed_as_var = rename_name.get((node.name, 'var'))

        if renamed_as_func:
            node.name = renamed_as_func
        elif renamed_as_var:
            node.name = renamed_as_var
        elif name_for_category(node.name, VARIABLE_PREFIXES):
            new_name = get_or_create_renamed_name(node.name, 'var')
            node.name = new_name
        elif name_for_category(node.name, FUNCTION_PREFIXES):
            new_name = get_or_create_renamed_name(node.name, 'func')
            node.name = new_name

    def visit_Decl(self, node):
        if node.type is not None:
            self.visit(node.type)

        if node.name and node.name not in RESERVED_NAMES:
            original_name = node.name
            category = 'var'
            if isinstance(node.type, c_ast.FuncDecl):
                category = 'func'
            elif name_for_category(original_name, VARIABLE_PREFIXES):
                category = 'var'
            elif name_for_category(original_name, FUNCTION_PREFIXES):
                category = 'func'

            new_name = get_or_create_renamed_name(original_name, category)
            node.name = new_name
            type_ptr = node.type
            while hasattr(type_ptr, 'type') and not isinstance(type_ptr, c_ast.IdentifierType):
                if isinstance(type_ptr, c_ast.TypeDecl) and type_ptr.declname == original_name:
                    type_ptr.declname = new_name
                    break
                if not hasattr(type_ptr, 'type'):
                    break
                type_ptr = type_ptr.type

            if isinstance(type_ptr, c_ast.TypeDecl) and type_ptr.declname == original_name:
                type_ptr.declname = new_name

        if node.init is not None:
            self.visit(node.init)

    def visit_FuncDef(self, node):
        if node.decl is not None:
            self.visit(node.decl)
        if node.body is not None:
            self.visit(node.body)

    def visit_FuncDecl(self, node):
        if node.args:
            self.visit(node.args)
        if node.type:
            self.visit(node.type)


def apply_renaming(root_node):
    reset_renaming_state()
    renamer_visitor = IdentifierRenamer()
    renamer_visitor.visit(root_node)
    return root_node


