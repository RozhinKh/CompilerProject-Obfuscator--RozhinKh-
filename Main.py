import re

def generate_random_name(prefix, index):
    return f"{prefix}{index}"

def rename_variables_and_functions(code):
    reserved_keywords = {'int', 'return', 'if', 'while', 'switch', 'case', 'break', 'default', 'else', 'for', 'printf',
                         'main'}
    replacements = {}
    count = 1

    functions = re.findall(r'\bint\s+(\w+)\s*\([^)]*\)\s*\{', code)
    for func in functions:
        if func not in reserved_keywords:
            new_name = generate_random_name("fxz", count)
            replacements[func] = new_name
            count += 1

    variables = re.findall(r'\bint\s+(\w+)\b', code)
    for var in variables:
        if var not in reserved_keywords and var not in replacements:
            new_name = generate_random_name("var", count)
            replacements[var] = new_name
            count += 1

    for old, new in replacements.items():
        code = re.sub(rf'\b{old}\b', new, code)

    return code

def dead_code(code):
    code = re.sub(r'(\{)', r'\1\nint unused = 1234;', code, 1)
    code = re.sub(r'(main\s*\([^)]*\)\s*\{)', r'\1\nint useless = 0;', code, 1)
    return code


