
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