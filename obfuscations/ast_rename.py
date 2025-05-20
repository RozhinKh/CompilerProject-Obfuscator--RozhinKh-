

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
    'break', 'case', 'char', 'continue', 'default', 'do', 'double',
    'else', 'enum', 'float', 'for',  'if', 'int', 'return', 'switch', 'void', 'volatile', 'while'
}

VARIABLE_PREFIXES = ["deadcode_", "dummyVariable_", "opaque_var_"]
FUNCTION_PREFIXES = ["dummyFunction_"]


def name_for_category(name, category_prefixes):
    for prefixes in category_prefixes:
        if name.startswith(prefixes):
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
    for key in rename_name_counters: rename_name_counters[key] = 0