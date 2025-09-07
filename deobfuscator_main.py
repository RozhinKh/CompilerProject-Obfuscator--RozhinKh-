import tkinter as tk
from tkinter import filedialog, ttk
import os
import sys
import time
import subprocess
import tkinter.messagebox as messagebox

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from grammer.MiniCLexer import MiniCLexer
from grammer.MiniCParser import MiniCParser
from obfuscations.ast_builder_visitor import ASTBuilderVisitor
from obfuscations.c_generator_visitor import CCodeGenerator
from obfuscations.preprocessor import preprocess_code

from deobfuscations.semantic_renamer import apply_semantic_renaming
from deobfuscations.dead_code_remover import apply_dead_code_removal
from deobfuscations.expression_simplifier import apply_expression_simplification
from deobfuscations.flow_reconstructor import apply_flow_reconstruction


class MiniCErrorListener(ErrorListener):
    """Custom error listener to capture syntax errors during parsing."""

    def __init__(self, error_messages_list):
        super().__init__()
        self.error_messages = error_messages_list

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.error_messages.append(f"ERROR - Line {line}:{column} : {msg}")


class DeobfuscatorGUI:
    """The main GUI application for the Mini-C De-obfuscator."""

    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Mini-C De-obfuscator")
        self.current_input_filepath = None
        self.current_input_filename = "obfuscated.mc"

        self._configure_styles()
        self._setup_gui_layout()

    def _configure_styles(self):
        """Configures the look and feel of the GUI widgets."""
        style = ttk.Style()
        try:
            preferred_themes = ['alt', 'clam', 'default']
            for theme in preferred_themes:
                if theme in style.theme_names():
                    style.theme_use(theme)
                    break
        except tk.TclError:
            pass
        style.configure("TButton", padding=6, font=('TkDefaultFont', 9))
        style.configure("TLabel", font=('TkDefaultFont', 9))
        style.configure("TEntry", padding=5, font=('TkDefaultFont', 9))
        style.configure("TCheckbutton", font=('TkDefaultFont', 9))
        style.configure("TLabelframe.Label", font=('TkDefaultFont', 9, 'bold'))

    def _setup_gui_layout(self):
        """Sets up the frames, widgets, and buttons for the GUI."""
        main_app_frame = ttk.Frame(self.root, padding="10")
        main_app_frame.pack(fill=tk.BOTH, expand=True)

        # File selection frame
        file_frame = ttk.LabelFrame(main_app_frame, text="Files", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.input_entry = ttk.Entry(file_frame, width=60)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(file_frame, text="Import", command=self.action_load_file).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, padx=(0, 5), pady=5, sticky="w")
        self.output_entry = ttk.Entry(file_frame, width=60)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(file_frame, text="Save As...", command=self.action_select_output_file).grid(row=1, column=2, pady=5)

        # De-obfuscation options frame
        options_frame = ttk.LabelFrame(main_app_frame, text="De-obfuscation Techniques", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        self.deobf_options = {}
        self.techniques_map = {
            "name_restoration": ("Restore Names", True, apply_semantic_renaming),
            "dead_code_removal": ("Remove Dead Code", True, apply_dead_code_removal),
            "expression_simplification": ("Simplify Expressions", True, apply_expression_simplification),
            "control_flow_simplification": ("Simplify Control Flow", True, apply_flow_reconstruction),
        }
        for i, (key, (text, default_val, _)) in enumerate(self.techniques_map.items()):
            self.deobf_options[key] = tk.BooleanVar(value=default_val)
            ttk.Checkbutton(options_frame, text=text, variable=self.deobf_options[key]).grid(row=i, column=0,
                                                                                             sticky="w", padx=5, pady=2)

        self.performance_option = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Generate Performance Report", variable=self.performance_option).grid(row=4,
                                                                                                                  column=0,
                                                                                                                  sticky="w",
                                                                                                                  padx=5,
                                                                                                                  pady=2)

        # Text areas for code display
        text_areas_frame = ttk.Frame(main_app_frame)
        text_areas_frame.pack(fill=tk.BOTH, expand=True)
        text_areas_frame.columnconfigure(0, weight=1)
        text_areas_frame.columnconfigure(1, weight=1)
        text_areas_frame.rowconfigure(0, weight=1)
        input_text_frame = ttk.LabelFrame(text_areas_frame, text="Obfuscated Code", padding=5)
        input_text_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        input_text_frame.grid_rowconfigure(0, weight=1)
        input_text_frame.grid_columnconfigure(0, weight=1)
        self.input_text_area = tk.Text(input_text_frame, undo=True, wrap=tk.WORD, font=('Consolas', 10), height=15)
        self.input_text_scrollbar = ttk.Scrollbar(input_text_frame, orient="vertical",
                                                  command=self.input_text_area.yview)
        self.input_text_area["yscrollcommand"] = self.input_text_scrollbar.set
        self.input_text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.input_text_area.grid(row=0, column=0, sticky="nsew")
        output_text_frame = ttk.LabelFrame(text_areas_frame, text="De-obfuscated Code", padding=5)
        output_text_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        output_text_frame.grid_rowconfigure(0, weight=1)
        output_text_frame.grid_columnconfigure(0, weight=1)
        self.output_text_area = tk.Text(output_text_frame, undo=True, wrap=tk.WORD, font=('Consolas', 10), height=15,
                                        state="disabled", bg="#f0f0f0")
        self.output_text_scrollbar = ttk.Scrollbar(output_text_frame, orient="vertical",
                                                   command=self.output_text_area.yview)
        self.output_text_area["yscrollcommand"] = self.output_text_scrollbar.set
        self.output_text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text_area.grid(row=0, column=0, sticky="nsew")

        # Action buttons
        action_buttons_frame = ttk.Frame(main_app_frame, padding="10 0 0 0")
        action_buttons_frame.pack(fill=tk.X)
        ttk.Button(action_buttons_frame, text="Run De-obfuscator", command=self.action_deobfuscate_code).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_frame, text="Clear All", command=self.action_clear_all).pack(side=tk.LEFT, padx=5)

    def _update_output_area(self, content, is_error=False):
        """Updates the output text area with new content."""
        self.output_text_area.config(state="normal", bg="white")
        self.output_text_area.delete("1.0", tk.END)
        self.output_text_area.insert(tk.END, content)
        self.output_text_area.config(state="disabled", bg="#f0f0f0" if not is_error else "#ffe0e0")

    def _generate_comparison_report(self, original_path, cleaned_path):
        """Generates a performance and file size comparison report."""
        report = []
        report.append("--- De-obfuscation Performance Report ---")

        # 1. Compare File Sizes
        try:
            original_size = os.path.getsize(original_path)
            cleaned_size = os.path.getsize(cleaned_path)
            report.append(f"\nOriginal Code Size: {original_size} bytes")
            report.append(f"De-obfuscated Code Size: {cleaned_size} bytes")
            size_diff = original_size - cleaned_size
            report.append(f"Code Size Difference: {size_diff} bytes {'(smaller)' if size_diff > 0 else '(larger)'}")
        except FileNotFoundError:
            report.append("\nError: Could not find one of the files for size comparison.")

        # 2. Compare Performance (Execution Time)
        report.append("\n--- Execution Time Comparison (with GCC) ---")

        def compile_and_run(file_path):
            exe_path = os.path.splitext(file_path)[0]
            gcc_path = r'C:\mingw64\bin\gcc.exe'
            try:
                # Check if the gcc executable exists at the specified path
                if not os.path.exists(gcc_path) and gcc_path != 'gcc':
                    return None, f"GCC executable not found at: {gcc_path}"

                # Compile the file, explicitly treating it as C code
                subprocess.run([gcc_path, '-x', 'c', file_path, '-o', exe_path], check=True, capture_output=True,
                               text=True)

                # Run the executable and measure time
                start_time = time.time()
                result = subprocess.run([exe_path], check=True, capture_output=True, text=True)
                end_time = time.time()

                # Clean up the executable
                os.remove(exe_path)

                return end_time - start_time, result.stdout.strip()
            except FileNotFoundError:
                return None, "GCC compiler not found. Please install it to run this benchmark."
            except subprocess.CalledProcessError as e:
                return None, f"Compilation/Execution failed: {e.stderr}"

        orig_time, orig_output = compile_and_run(original_path)
        clean_time, clean_output = compile_and_run(cleaned_path)

        if orig_time is not None and clean_time is not None:
            report.append(f"Original Code Runtime: {orig_time:.6f} seconds")
            report.append(f"De-obfuscated Code Runtime: {clean_time:.6f} seconds")
            report.append(f"\nOriginal Output:\n{orig_output}")
            report.append(f"\nDe-obfuscated Output:\n{clean_output}")
        else:
            report.append(orig_output if orig_output else clean_output)

        # 3. Save the report to a file
        report_path = os.path.join(os.path.dirname(cleaned_path), "deobfuscation_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))

        return "\n".join(report)

    def action_load_file(self):
        """Handles loading an input file into the GUI."""
        filepath = filedialog.askopenfilename(title="Select Obfuscated Mini-C File",
                                              filetypes=[("Mini-C Files", "*.c *.mc"), ("All Files", "*.*")])
        if not filepath: return
        self.current_input_filepath, self.current_input_filename = filepath, os.path.basename(filepath)
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                input_code = f.read()
            self.input_text_area.delete("1.0", tk.END)
            self.input_text_area.insert(tk.END, input_code)
            name, ext = os.path.splitext(self.current_input_filename)
            ext = ext or ".mc"
            out_path = os.path.join(os.path.dirname(filepath), f"{name}_deobf{ext}")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, out_path.replace("\\", "/"))
            self._update_output_area("")
        except Exception as e:
            self._update_output_area(f"Error loading file: {e}", True)

    def action_select_output_file(self):
        """Allows the user to select and set an output file path."""
        in_val = self.input_entry.get()
        init_dir, init_file = ".", "cleaned.mc"
        src_path = in_val if in_val and os.path.isfile(in_val) else self.current_input_filepath
        if src_path:
            init_dir = os.path.dirname(src_path)
            name, ext = os.path.splitext(os.path.basename(src_path))
            ext = ext or ".mc"
            init_file = f"{name}_deobf{ext}"
        filepath = filedialog.asksaveasfilename(initialdir=init_dir, initialfile=init_file, defaultextension=".mc",
                                                filetypes=[("Mini-C Files", "*.mc"), ("C Files", "*.c"),
                                                           ("All Files", "*.*")])
        if filepath:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filepath.replace("\\", "/"))

    def action_deobfuscate_code(self):
        """Executes the de-obfuscation process on the input code."""
        input_code = self.input_text_area.get("1.0", tk.END).strip()
        output_fpath = self.output_entry.get().strip()
        error_msgs_antlr = []
        if not input_code:
            self._update_output_area("Error: Input code is empty.", True);
            return
        if not output_fpath:
            self._update_output_area("Error: Output file path not set.", True);
            return

        self.root.config(cursor="watch");
        self.root.update_idletasks()
        processed_code = ""
        try:
            processed_code = preprocess_code(input_code)
            if not processed_code.strip():
                raise ValueError("Code is empty after preprocessing.")
            lexer = MiniCLexer(InputStream(processed_code))
            lexer.removeErrorListeners();
            err_listener = MiniCErrorListener(error_msgs_antlr);
            lexer.addErrorListener(err_listener)
            parser = MiniCParser(CommonTokenStream(lexer))
            parser.removeErrorListeners();
            parser.addErrorListener(err_listener)
            parse_tree = parser.program()
            if error_msgs_antlr:
                raise SyntaxError("Parsing failed:\n" + "\n".join(error_msgs_antlr))
            custom_ast = ASTBuilderVisitor().visit(parse_tree)
            if custom_ast is None:
                raise ValueError("AST construction failed.")

            for key, (_, _, deobf_func) in self.techniques_map.items():
                if self.deobf_options[key].get():
                    custom_ast = deobf_func(custom_ast)
            deobfuscated_c_code = CCodeGenerator().visit(custom_ast)

            out_dir = os.path.dirname(output_fpath)
            if out_dir and not os.path.exists(out_dir): os.makedirs(out_dir)
            with open(output_fpath, 'w', encoding='utf-8') as f:
                f.write(deobfuscated_c_code)

            final_message = f"De-obfuscation successful! Saved to: {output_fpath}\n\n--- De-obfuscated Code ---\n{deobfuscated_c_code}"
            if self.performance_option.get():
                report_content = self._generate_comparison_report(self.current_input_filepath, output_fpath)
                final_message += f"\n\n{report_content}"
            self._update_output_area(final_message)

        except Exception as e:
            err_detail = f"Error: {e}\n"
            if processed_code: err_detail += f"\nProcessed code before error:\n---\n{processed_code}\n---\n"
            if error_msgs_antlr: err_detail += "\nANTLR Parse Errors:\n" + "\n".join(error_msgs_antlr) + "\n"
            self._update_output_area(err_detail, True)
            print(err_detail, file=sys.stderr)
        finally:
            self.root.config(cursor="")

    def action_clear_all(self):
        """Clears all input and output fields in the GUI."""
        self.input_text_area.delete("1.0", tk.END)
        self._update_output_area("")
        self.input_entry.delete(0, tk.END)
        self.output_entry.delete(0, tk.END)
        self.current_input_filepath, self.current_input_filename = None, "obfuscated.mc"


def run_cli_mode():
    """Runs the de-obfuscator in command-line mode."""
    if not (2 <= len(sys.argv) <= 3):
        print("Usage: python deobfuscator_main.py <input_file> [output_file]");
        sys.exit(1)
    in_f, err_msgs_cli = sys.argv[1], []
    if not os.path.exists(in_f):
        print(f"Error: Input file '{in_f}' not found.", file=sys.stderr);
        sys.exit(1)
    out_f = sys.argv[2] if len(
        sys.argv) == 3 else f"{os.path.splitext(os.path.basename(in_f))[0]}_deobf{os.path.splitext(in_f)[1] or '.mc'}"
    processed_cli_code = ""
    try:
        with open(in_f, 'r', encoding='utf-8') as f:
            code_to_deobf = f.read()
        processed_cli_code = preprocess_code(code_to_deobf)
        # if not processed_code.strip():
        #     print("Error: Code empty after preprocessing.", file=sys.stderr);
        #     sys.exit(1)
        lexer = MiniCLexer(InputStream(processed_cli_code));
        lexer.removeErrorListeners();
        cli_err_listener = MiniCErrorListener(err_msgs_cli);
        lexer.addErrorListener(cli_err_listener)
        parser = MiniCParser(CommonTokenStream(lexer));
        parser.removeErrorListeners();
        parser.addErrorListener(cli_err_listener)
        parse_tree = parser.program()
        if err_msgs_cli:
            print("Parse Errors (CLI):\n" + "\n".join(err_msgs_cli), file=sys.stderr);
            sys.exit(1)
        custom_ast = ASTBuilderVisitor().visit(parse_tree)
        if custom_ast is None:
            print("Error: AST construction failed (CLI).", file=sys.stderr);
            sys.exit(1)
        techniques_cli = {
            "name_restoration": apply_semantic_renaming,
            "dead_code_removal": apply_dead_code_removal,
            "expression_simplification": apply_expression_simplification,
            "control_flow_simplification": apply_flow_reconstruction,
        }
        for name, func in techniques_cli.items(): custom_ast = func(custom_ast)
        deobfuscated_code = CCodeGenerator().visit(custom_ast)
        out_dir_cli = os.path.dirname(out_f)
        if out_dir_cli and not os.path.exists(out_dir_cli): os.makedirs(out_dir_cli)
        with open(out_f, 'w', encoding='utf-8') as f:
            f.write(deobfuscated_code)
        print(f"De-obfuscation successful (CLI)! Saved to: {out_f}")
    except Exception as e:
        print(f"CLI Error: {e}", file=sys.stderr)
        if processed_cli_code: print(f"\nProcessed code before error:\n---\n{processed_cli_code}\n---", file=sys.stderr)
        if err_msgs_cli: print("\nANTLR Parse Errors:\n" + "\n".join(err_msgs_cli), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != '--gui':
        run_cli_mode()
    else:
        gui_root = tk.Tk()
        DeobfuscatorGUI(gui_root)
        gui_root.mainloop()