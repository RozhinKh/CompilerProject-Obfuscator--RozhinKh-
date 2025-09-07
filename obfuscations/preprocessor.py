import re

def preprocess_code(code_string):
    code_string = re.sub(r'//.*', '', code_string)
    code_string = re.sub(r'/\*.*?\*/', '', code_string, flags=re.DOTALL)
    code_string = re.sub(r'^\s*#include\s*<[^>]*>\s*$', '', code_string, flags=re.MULTILINE)
    code_string = re.sub(r'^\s*#include\s*"[^"]*"\s*$', '', code_string, flags=re.MULTILINE)
    code_string = re.sub(r'^\s*#define\s+.*$', '', code_string, flags=re.MULTILINE)
    code_string = re.sub(r'^\s*#if.*$', '', code_string, flags=re.MULTILINE)
    code_string = re.sub(r'^\s*#else.*$', '', code_string, flags=re.MULTILINE)
    code_string = re.sub(r'^\s*#elif.*$', '', code_string, flags=re.MULTILINE)
    code_string = re.sub(r'^\s*#endif.*$', '', code_string, flags=re.MULTILINE)
    code_string = re.sub(r'^\s*#pragma\s+.*$', '', code_string, flags=re.MULTILINE)
    code_string = re.sub(r'__attribute__\s*\(\([^)]*\)\)', '', code_string)
    code_string = re.sub(r'__restrict(?:__)?', '', code_string)
    code_string = re.sub(r'__extension__', '', code_string)
    code_string = re.sub(r'__asm__\s*\(\s*".*?"\s*\)', '', code_string)
    code_string = re.sub(r'__asm\s*\(\s*".*?"\s*\)', '', code_string)
    code_string = re.sub(r'__declspec\s*\([^)]*\)', '', code_string)
    code_string = "\n".join(line for line in code_string.splitlines() if line.strip())
    return code_string