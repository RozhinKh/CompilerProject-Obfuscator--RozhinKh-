
import tkinter as tk
from tkinter import filedialog, ttk
import os
import sys
import random
import re

from pycparser import c_parser, c_ast, c_generator

from obfuscations.ast_rename import apply_renaming
from obfuscations.ast_dead_code import apply_dead_code_insertion
from obfuscations.ast_equivalent_expr import apply_equivalent_expression
from obfuscations.ast_dummy_function import apply_dummy_function_insertion
from obfuscations.ast_opaque_predicate import apply_opaque_predicates

sys.setrecursionlimit(20000)

class ObfuscatorGUI:
    def init(self, root_window):
        self.root = root_window
        self.root.title("Mini-C Obfuscator")
        self.current_input_filepath = None
        self.current_input_filename = "input.mc"

        style = ttk.Style()
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        else:
            style.theme_use('default')

        style.configure("TButton", padding=6, relief="flat", font=('Segoe UI', 9))
        style.configure("TLabel", font=('Segoe UI', 9))
        style.configure("TEntry", padding=5, font=('Segoe UI', 9))
        style.configure("TCheckbutton", font=('Segoe UI', 9))
        style.configure("TLabelframe.Label", font=('Segoe UI', 9, 'bold'))

        main_app_frame = ttk.Frame(self.root, padding="10 10 10 10")
        main_app_frame.pack(fill=tk.BOTH, expand=True)

        file_frame = ttk.LabelFrame(main_app_frame, text="Import input file", padding="10 10 10 10")
        file_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.input_entry = ttk.Entry(file_frame, width=60)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(file_frame, text="Import", command=self.action_load_file).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, padx=(0, 5), pady=5, sticky="w")
        self.output_entry = ttk.Entry(file_frame, width=60)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(file_frame, text="Save", command=self.action_select_output_file).grid(row=1, column=2, padx=5,
                                                                                               pady=5)

        options_frame = ttk.LabelFrame(main_app_frame, text="Obfuscation Techniques", padding="10 10 10 10")
        options_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        self.obf_options = {}
        techniques = {
            "rename": ("Rename Identifiers", True),
            "dead_code": ("Inject Dead Code", True),
            "equivalent_expression": ("Equivalent Expressions", True),
            "dummy_function": ("Insert Dummy Functions", True),
            "opaque_predicate": ("Insert Opaque Predicates", True),
        }

        row_num = 0
        for key, (text, default_val) in techniques.items():
            self.obf_options[key] = tk.BooleanVar(value=default_val)
            ttk.Checkbutton(options_frame, text=text, variable=self.obf_options[key]).grid(row=row_num, column=0,
                                                                                           sticky="w", padx=5, pady=2)
            row_num += 1

        text_areas_frame = ttk.Frame(main_app_frame)
        text_areas_frame.pack(fill=tk.BOTH, expand=True)
        text_areas_frame.columnconfigure(0, weight=1)
        text_areas_frame.columnconfigure(1, weight=1)
        text_areas_frame.rowconfigure(0, weight=1)

        input_text_frame = ttk.LabelFrame(text_areas_frame, text="Input Code", padding=5)
        input_text_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        input_text_frame.rowconfigure(0, weight=1)
        input_text_frame.columnconfigure(0, weight=1)


        self.input_text_area = tk.Text(input_text_frame, undo=True, wrap=tk.WORD, font=('Consolas', 10), height=15)
        self.input_text_scrollbar = ttk.Scrollbar(input_text_frame, orient="vertical",
                                                  command=self.input_text_area.yview)
        self.input_text_area["yscrollcommand"] = self.input_text_scrollbar.set
        self.input_text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.input_text_area.grid(row=0, column=0, sticky="nsew")

        output_text_frame = ttk.LabelFrame(text_areas_frame, text="Obfuscated Code", padding=5)
        output_text_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        output_text_frame.rowconfigure(0, weight=1)
        output_text_frame.columnconfigure(0, weight=1)

        self.output_text_area = tk.Text(output_text_frame, undo=True, wrap=tk.WORD, font=('Consolas', 10), height=15,
                                        state="disabled", bg="#f0f0f0")
        self.output_text_scrollbar = ttk.Scrollbar(output_text_frame, orient="vertical",
                                                   command=self.output_text_area.yview)
        self.output_text_area["yscrollcommand"] = self.output_text_scrollbar.set
        self.output_text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text_area.grid(row=0, column=0, sticky="nsew")

        action_buttons_frame = ttk.Frame(main_app_frame, padding="10 0 0 0")
        action_buttons_frame.pack(fill=tk.X, expand=False)

        ttk.Button(action_buttons_frame, text="Run Obfuscator", command=self.action_obfuscate_code).pack(side=tk.LEFT,
                                                                                                         padx=5)
        ttk.Button(action_buttons_frame, text="Clear", command=self.action_clear_text_areas).pack(side=tk.LEFT,
                                                                                                      padx=5)

    def action_load_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Mini-C File",
            filetypes=[("C/Mini-C Files", "*.c *.mc"), ("All Files", "*.*")]
        )
        if not filepath: return

        self.current_input_filepath = filepath
        self.current_input_filename = os.path.basename(filepath)
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, filepath)

        with open(filepath, 'r', encoding='utf-8') as file:
            input_code = file.read()
        self.input_text_area.delete("1.0", tk.END)
        self.input_text_area.insert(tk.END, input_code)
        name_part, ext_part = os.path.splitext(self.current_input_filename)
        if not ext_part: ext_part = ".mc"
        suggested_output_filename = f"{name_part}_obf{ext_part}" # Changed suffix
        suggested_output_path = os.path.join(os.path.dirname(filepath), suggested_output_filename)
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, suggested_output_path.replace("\\", "/")) # Ensure forward slashes

    def action_select_output_file(self):
        initial_dir = "."
        initial_file = "output.mc"
        if self.current_input_filepath:
            initial_dir = os.path.dirname(self.current_input_filepath)
            name_part, ext_part = os.path.splitext(self.current_input_filename)
            if not ext_part: ext_part = ".mc"
            initial_file = f"{name_part}_obf{ext_part}" # Changed suffix
        elif self.input_entry.get():
            initial_dir = os.path.dirname(self.input_entry.get())
            base = os.path.basename(self.input_entry.get())
            name_part, ext_part = os.path.splitext(base)
            if not ext_part: ext_part = ".mc"
            initial_file = f"{name_part}_obf{ext_part}" # Changed suffix


            filepath = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".mc",
            filetypes=[("Mini-C Files", "*.mc"), ("C Files", "*.c"), ("All Files", "*.*")],
        )
        if filepath:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filepath.replace("\\", "/")) # Ensure forward slashes

    def handle_drop_file(self, event):
        filepath_str = event.data
        if filepath_str.startswith('{') and filepath_str.endswith('}'):
            filepath_str = filepath_str[1:-1]

        filepaths = filepath_str.split()
        filepath = filepaths[0]

        if os.path.isfile(filepath):
            self.current_input_filepath = filepath
            self.current_input_filename = os.path.basename(filepath)
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filepath)
            with open(filepath, 'r', encoding='utf-8') as file:
                input_code = file.read()
            self.input_text_area.delete("1.0", tk.END)
            self.input_text_area.insert(tk.END, input_code)
            name_part, ext_part = os.path.splitext(self.current_input_filename)
            if not ext_part: ext_part = ".mc"
            suggested_output_filename = f"{name_part}_obf{ext_part}" # Changed suffix
            suggested_output_path = os.path.join(os.path.dirname(filepath), suggested_output_filename)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, suggested_output_path.replace("\\", "/")) # Ensure forward slashes
        else:
            print(f"Error: Invalid file dropped: {filepath}")


    def action_obfuscate_code(self):
        input_code_from_textarea = self.input_text_area.get("1.0", tk.END).strip()
        output_filepath_str = self.output_entry.get().strip()


        self.root.config(cursor="watch")
        self.root.update_idletasks()

        processed_c_code_str = input_code_from_textarea

        processed_c_code_str = re.sub(r'attribute__\s*\(\([^)]*\)\)', '', processed_c_code_str)
        processed_c_code_str = re.sub(r'__restrict(?:)?', '', processed_c_code_str)
        processed_c_code_str = re.sub(r'extension', '', processed_c_code_str)
        processed_c_code_str = re.sub(r'volatile(?:)?', '', processed_c_code_str)
        processed_c_code_str = re.sub(r'inline(?:)?', '', processed_c_code_str)
        processed_c_code_str = re.sub(r'asm__\s*\(\s*".*?"\s*\)', '', processed_c_code_str)
        processed_c_code_str = re.sub(r'__asm\s*\(\s*".*?"\s*\)', '', processed_c_code_str)
        processed_c_code_str = re.sub(r'__declspec\s*\([^)]*\)', '', processed_c_code_str)

        parser = c_parser.CParser()
        ast_filename = self.current_input_filename if self.current_input_filename else "input.c"
        ast = parser.parse(processed_c_code_str, filename=ast_filename)

        if self.obf_options.get("dead_code", tk.BooleanVar(value=False)).get():
            ast = apply_dead_code_insertion(ast)
        if self.obf_options.get("dummy_function", tk.BooleanVar(value=False)).get():
            ast = apply_dummy_function_insertion(ast, num_to_insert=random.randint(1, 2))
        if self.obf_options.get("opaque_predicate", tk.BooleanVar(value=False)).get():
            ast = apply_opaque_predicates(ast)
        if self.obf_options.get("rename", tk.BooleanVar(value=False)).get():
            ast = apply_renaming(ast, debug_mode=True)
        if self.obf_options.get("equivalent_expression", tk.BooleanVar(value=False)).get():
            ast = apply_equivalent_expression(ast)

        generator = c_generator.CGenerator()
        obfuscated_c_code = generator.visit(ast)

        with open(output_filepath_str.replace("\\", "/"), 'w', encoding='utf-8') as f:
            f.write(obfuscated_c_code)

        print(f"Obfuscation successful! Saved to: {output_filepath_str.replace("\\", "/")}")

        self.output_text_area.config(state="normal")
        self.output_text_area.delete("1.0", tk.END)
        self.output_text_area.insert(tk.END, obfuscated_c_code)
        self.output_text_area.config(state="disabled")
        self.root.config(cursor="")

    def action_clear_text_areas(self):
        self.input_text_area.delete("1.0", tk.END)
        self.output_text_area.config(state="normal")
        self.output_text_area.delete("1.0", tk.END)
        self.output_text_area.config(state="disabled")
        self.input_entry.delete(0, tk.END)
        self.output_entry.delete(0, tk.END)
        self.current_input_filepath = None
        self.current_input_filename = "input.mc"
        print("Cleared. Ready.")

