import tkinter as tk
from tkinter import ttk, messagebox
import json
import hashlib
import os
import random
import re

# ──────────────────────────────────────────────────────────────────────────────
#  STYLING & THEME
# ──────────────────────────────────────────────────────────────────────────────
BG = "#0F111A"
PANEL = "#1A1C2E"
BORDER = "#2A2D3E"
TEXT = "#FFFFFF"
SUBTEXT = "#8F93A1"
ACCENT = "#00D2FF"  # Cyan
ACCENT2 = "#7B61FF" # Purple
GREEN = "#00FFA3"
RED = "#FF3D71"
WARN = "#FFD644"

DEFAULT_PET_IDS = "1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033, 1034, 1035, 1036, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050, 1051, 1053, 1054, 1055, 1056, 1057, 1059, 1060, 1061, 1062, 1063, 1064, 1065, 1066, 1068, 1069, 1070, 1072, 1073, 1075, 1077, 1078, 1079, 1080, 1081, 1082, 1083, 1084, 1085, 1086, 1087, 1088, 1089, 1090, 1091, 1092, 1093, 1094, 1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1110, 1111, 1112, 1113, 1116, 1117"
DEFAULT_GODDESS_IDS = "3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008"
AWAKEN_ID_LIST = [1001, 1002, 1003, 1004, 1005, 1009, 1013, 1014, 1021, 1023, 1025, 1026, 1030, 1031, 1032, 1034, 1036, 1041, 1043, 1044, 1048, 1050, 1051, 1053, 1054, 1055, 1059, 1060, 1063, 1064, 1065, 1066, 1068, 1070, 1072, 1073, 1077, 1078, 1079, 1080, 1081, 1082, 1083, 1084, 1085, 1086, 1087, 1088, 1089, 1090, 1091, 1092, 1093, 1094, 1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1110, 1111, 1112, 1113, 1116, 1117]

# ──────────────────────────────────────────────────────────────────────────────
#  CORE LOGIC (from pet_payload_gen.py)
# ──────────────────────────────────────────────────────────────────────────────

def make_serial(pet_id, random_seed=False):
    if random_seed:
        return hashlib.sha1(os.urandom(32)).hexdigest()
    # Deterministic serial from pet_payload_gen.py
    a = hashlib.md5(f"pet_{pet_id}".encode()).hexdigest()
    b = hashlib.md5(f"s2_{pet_id}".encode()).hexdigest()[:8]
    return a + b

def extract_pet_list_v2(text):
    key = '"pet_list_v2":['
    start = text.find(key)
    if start == -1: return None, None
    bracket_start = start + len(key) - 1
    depth, in_string, escape = 0, False, False
    i = bracket_start
    while i < len(text):
        c = text[i]
        if escape:      escape = False
        elif c == '\\' and in_string: escape = True
        elif c == '"' and not escape: in_string = not in_string
        elif not in_string:
            if c == '[': depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0: return start, i + 1
        i += 1
    return None, None

# ──────────────────────────────────────────────────────────────────────────────
#  UI CLASSES
# ──────────────────────────────────────────────────────────────────────────────

class PetGenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pet Payload Forger Pro")
        self.geometry("1100x960")
        self.configure(bg=BG)
        
        self._build_vars()
        self._build_ui()
        self.status("Ready. Enter parameters and IDs, then Generate.")

    def _build_vars(self):
        self.v_user_id      = tk.StringVar(value="VVG0000034278")
        self.v_star_id      = tk.StringVar(value="4")
        self.v_star_spirit  = tk.StringVar(value="10")
        self.v_level        = tk.StringVar(value="20")
        self.v_quality      = tk.StringVar(value="4")
        self.v_hp           = tk.StringVar(value="99")
        self.v_rhp          = tk.StringVar(value="99")
        self.v_atk          = tk.StringVar(value="99")
        self.v_exp          = tk.StringVar(value="99")
        self.v_might        = tk.StringVar(value="99")
        self.v_pve_set_lv   = tk.StringVar(value="0")
        self.v_pvp_set_lv   = tk.StringVar(value="0")
        self.v_awake_lv     = tk.StringVar(value="0")
        self.v_awake_star   = tk.StringVar(value="0")
        self.v_source       = tk.StringVar(value="summon")
        self.v_create_time  = tk.StringVar(value="2024-03-12 19:12:44")
        self.v_last_update  = tk.StringVar(value="2026-02-21 02:05:04")
        self.v_random_serial = tk.BooleanVar(value=True)
        self.v_awaken_toggle = tk.BooleanVar(value=False)
        self.status_text     = tk.StringVar()
        
        # Refs for enabling/disabling
        self.entry_awake_lv = None
        self.entry_awake_star = None

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=PANEL, height=60)
        hdr.pack(fill="x", side="top")
        tk.Label(hdr, text="⚡ PET PAYLOAD FORGER", bg=PANEL, fg=ACCENT, 
                 font=("Segoe UI", 16, "bold"), padx=25).pack(side="left")
        tk.Label(hdr, text="PRO VERSION", bg=PANEL, fg=SUBTEXT, 
                 font=("Segoe UI", 9, "bold")).pack(side="left", pady=(5, 0))

        # Goddess Launcher
        self.god_btn = self._styled_button(hdr, "🌸 GODDESS FORGER", ACCENT2, self._cmd_open_goddess, padx=15, pady=5, font=("Segoe UI", 9, "bold"))
        self.god_btn.pack(side="right", padx=25, pady=10)

        # Status Bar
        self._status_bar = tk.Label(self, textvariable=self.status_text, bg=BG, fg=SUBTEXT, 
                                   font=("Segoe UI", 9), anchor="w", padx=20, pady=8)
        self._status_bar.pack(fill="x", side="bottom")

        # Main Layout
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=10)

        # Sidebar (Instructions)
        self._build_sidebar(body)
        
        # Main Content Area
        main_content = tk.Frame(body, bg=BG)
        main_content.pack(fill="both", expand=True, side="right")

        # Row 1: Parameters Card
        self._build_params_card(main_content)
        
        # Row 2: IDs & Input Card
        self._build_input_card(main_content)

        # Row 3: Action & Output Card
        self._build_output_card(main_content)

    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=PANEL, width=240)
        side.pack(fill="y", side="left", padx=(0, 15))
        side.pack_propagate(False)

        tk.Label(side, text="HOW TO USE", bg=PANEL, fg=ACCENT2, 
                 font=("Segoe UI", 10, "bold"), pady=15).pack()

        steps = [
            ("1", "Configure Stats", "HP, ATK, Level, etc. will apply to ALL forged pets."),
            ("2", "Edit Pet IDs", "Add/remove IDs in the IDs box. One ID per line or comma separated."),
            ("3", "Burp Mode", "Generates full 'pet_list_v2':[...] for Match and Replace."),
            ("4", "Patch Mode", "Paste a raw response below to replace its pet_list_v2."),
            ("5", "Copy & Hack", "Use the Copy button in output. Paste into Burp Replace field.")
        ]

        for num, title, desc in steps:
            f = tk.Frame(side, bg=PANEL, padx=15, pady=10)
            f.pack(fill="x")
            tk.Label(f, text=f"{num}. {title}", bg=PANEL, fg=TEXT, 
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")
            tk.Label(f, text=desc, bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8), 
                     wraplength=180, justify="left", anchor="w").pack(fill="x")

        tk.Label(side, text="v2.1 Premium", bg=PANEL, fg=BORDER, 
                 font=("Segoe UI", 8, "bold")).pack(side="bottom", pady=10)

    def _build_params_card(self, parent):
        card = tk.Frame(parent, bg=PANEL, padx=15, pady=15)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(card, text="PET PARAMETERS", bg=PANEL, fg=ACCENT, 
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))

        fields = [
            ("User ID", self.v_user_id), ("Level", self.v_level), ("Quality (0-4)", self.v_quality),
            ("HP", self.v_hp), ("RHP", self.v_rhp), ("ATK", self.v_atk),
            ("EXP", self.v_exp),            ("Might", self.v_might), ("Star ID (0-4)", self.v_star_id),
            ("Star Spirit", self.v_star_spirit), ("PVE Set Lv", self.v_pve_set_lv), ("PVP Set Lv", self.v_pvp_set_lv),
            ("Awake Lv", self.v_awake_lv), ("Awake Star", self.v_awake_star), ("Source", self.v_source)
        ]

        self._param_entries = {}
        for i, (label, var) in enumerate(fields):
            r, c = divmod(i, 3)
            # Label
            tk.Label(card, text=label, bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8, "bold")).grid(row=r*2+1, column=c*2, sticky="w", padx=(5, 5))
            # Entry
            e = tk.Entry(card, textvariable=var, bg=BG, fg=TEXT, insertbackground=TEXT, 
                         relief="flat", font=("Segoe UI", 9), width=15,
                         highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)
            e.grid(row=r*2+1, column=c*2+1, pady=3, padx=(0, 15))
            self._param_entries[label] = e

        self.entry_awake_lv = self._param_entries["Awake Lv"]
        self.entry_awake_star = self._param_entries["Awake Star"]

        # Checkbox for random serial
        cb_frame = tk.Frame(card, bg=PANEL)
        cb_frame.grid(row=11, column=0, columnspan=2, sticky="w", pady=(10, 0))

        tk.Checkbutton(cb_frame, text="Random Serial", variable=self.v_random_serial,
                       bg=PANEL, fg=TEXT, selectcolor=BG, activebackground=PANEL, 
                       activeforeground=ACCENT, font=("Segoe UI", 8, "bold")).pack(side="left")

        tk.Checkbutton(cb_frame, text="Specialized Awakening", variable=self.v_awaken_toggle,
                       bg=PANEL, fg=ACCENT2, selectcolor=BG, activebackground=PANEL, 
                       activeforeground=ACCENT2, font=("Segoe UI", 8, "bold"),
                       command=self._on_toggle_awaken).pack(side="left", padx=(10, 0))

        tk.Label(card, text="Create Time:", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8)).grid(row=11, column=2, sticky="e")
        tk.Entry(card, textvariable=self.v_create_time, bg=BG, fg=TEXT, font=("Segoe UI", 8), width=20, relief="flat", highlightthickness=1, highlightbackground=BORDER).grid(row=11, column=3, padx=5)
        
        tk.Label(card, text="Update Time:", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8)).grid(row=11, column=4, sticky="e")
        tk.Entry(card, textvariable=self.v_last_update, bg=BG, fg=TEXT, font=("Segoe UI", 8), width=20, relief="flat", highlightthickness=1, highlightbackground=BORDER).grid(row=11, column=5, padx=5)

    def _build_input_card(self, parent):
        card = tk.Frame(parent, bg=PANEL, padx=15, pady=15)
        card.pack(fill="both", expand=True, pady=(0, 10))

        # Split card into IDs (left) and Response (right)
        tk.Label(card, text="PET IDs TO FORGE (One per line or comma separated)", bg=PANEL, fg=ACCENT, 
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(card, text="OPTIONAL: PASTE RESPONSE HERE (FOR PATCH MODE)", bg=PANEL, fg=ACCENT, 
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="w", padx=(15, 0))

        self.ids_text = tk.Text(card, bg=BG, fg=TEXT, font=("Consolas", 9), height=8, 
                               relief="flat", highlightthickness=1, highlightbackground=BORDER)
        self.ids_text.grid(row=1, column=0, sticky="nsew", pady=5)
        self.ids_text.insert("1.0", DEFAULT_PET_IDS.replace(", ", "\n"))

        self.patch_frame = tk.Frame(card, bg=PANEL)
        self.patch_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(15, 0))
        
        self.patch_lbl = tk.Label(self.patch_frame, text="OPTIONAL: PASTE RESPONSE HERE (FOR PATCH MODE)", bg=PANEL, fg=ACCENT, 
                                 font=("Segoe UI", 9, "bold"))
        self.patch_lbl.pack(anchor="w")

        self.patch_input = tk.Text(self.patch_frame, bg=BG, fg=SUBTEXT, font=("Consolas", 9), height=8, 
                                  relief="flat", highlightthickness=1, highlightbackground=BORDER)
        self.patch_input.pack(fill="both", expand=True, pady=5)
        self.patch_input.insert("1.0", "Paste raw JSON here to patch...")
        self.patch_input.bind("<FocusIn>", lambda e: self._clear_placeholder(self.patch_input))

        # Awaken IDs Frame (hidden by default)
        self.awaken_frame = tk.Frame(card, bg=PANEL)
        # We don't grid it yet, it will replace patch_frame if toggle is ON
        
        tk.Label(self.awaken_frame, text="IDs TO FORCE AWAKE_STAR = 3", bg=PANEL, fg=ACCENT2, 
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        
        self.awaken_ids_text = tk.Text(self.awaken_frame, bg=BG, fg=TEXT, font=("Consolas", 9), height=8, 
                                      relief="flat", highlightthickness=1, highlightbackground=BORDER)
        self.awaken_ids_text.pack(fill="both", expand=True, pady=5)
        self.awaken_ids_text.insert("1.0", ", ".join(map(str, AWAKEN_ID_LIST)))

        # Initial Toggle State
        self._on_toggle_awaken()

        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(1, weight=1)

    def _build_output_card(self, parent):
        card = tk.Frame(parent, bg=PANEL, padx=15, pady=15)
        card.pack(fill="x")

        # Buttons
        btn_frame = tk.Frame(card, bg=PANEL)
        btn_frame.pack(fill="x", pady=(0, 10))

        self.gen_btn = self._styled_button(btn_frame, "⚡ GENERATE BURP PAYLOAD", ACCENT, self._cmd_generate)
        self.gen_btn.pack(side="left", padx=(0, 10))

        self.patch_btn = self._styled_button(btn_frame, "🛠️ PATCH RESPONSE", ACCENT2, self._cmd_patch)
        self.patch_btn.pack(side="left", padx=(0, 10))

        self._styled_button(btn_frame, "🧹 CLEAR", BORDER, self._cmd_clear).pack(side="right")

        # Output Area
        tk.Label(card, text="GENERATED OUTPUT", bg=PANEL, fg=GREEN, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.out_text = tk.Text(card, bg=BG, fg=TEXT, font=("Consolas", 9), height=8, 
                               relief="flat", highlightthickness=1, highlightbackground=BORDER)
        self.out_text.pack(fill="x", pady=5)

        # Copy buttons
        copy_frame = tk.Frame(card, bg=PANEL)
        copy_frame.pack(fill="x")
        
        self.copy_btn = self._styled_button(copy_frame, "📋 COPY OUTPUT", GREEN, self._cmd_copy, padx=10, pady=5, font=("Segoe UI", 8, "bold"))
        self.copy_btn.pack(side="left")

        tk.Label(copy_frame, text='Match Regex:', bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(20, 5))
        self.regex_entry = tk.Entry(copy_frame, bg=BG, fg=ACCENT, font=("Consolas", 9), width=40, relief="flat", highlightthickness=1, highlightbackground=BORDER)
        self.regex_entry.pack(side="left")
        self.regex_entry.insert(0, '"pet_list_v2":\\[.*?\\],"pet_god_list"')
        
        self._styled_button(copy_frame, "📋 COPY REGEX", ACCENT, lambda: self._copy_to_clip(self.regex_entry.get()), padx=10, pady=5, font=("Segoe UI", 8, "bold")).pack(side="left", padx=5)

    def _styled_button(self, parent, text, color, command, **kw):
        padx = kw.pop("padx", 20)
        pady = kw.pop("pady", 10)
        font = kw.pop("font", ("Segoe UI", 10, "bold"))
        btn = tk.Label(parent, text=text, bg=color, fg=TEXT, cursor="hand2",
                       padx=padx, pady=pady, font=font, **kw)
        btn.bind("<Button-1>", lambda e: command())
        # Hover
        orig_color = color
        def on_enter(e): btn.config(bg=self._lighten(orig_color, 20))
        def on_leave(e): btn.config(bg=orig_color)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _lighten(self, hex_color, amount):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(min(255, c + amount) for c in rgb)
        return '#%02x%02x%02x' % new_rgb

    def _cmd_open_goddess(self):
        GoddessGenApp(self)

    def _on_toggle_awaken(self):
        enabled = self.v_awaken_toggle.get()
        if enabled:
            # Show Awaken IDs, Hide Patch Response
            self.patch_frame.grid_remove()
            self.awaken_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(15, 0))
            # Enable global fields
            self.entry_awake_lv.config(state="normal", bg=BG)
            self.entry_awake_star.config(state="normal", bg=BG)
            self.status("Specialized Awakening ON. Global awake settings enabled.")
        else:
            # Hide Awaken IDs, Show Patch Response
            self.awaken_frame.grid_remove()
            self.patch_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(15, 0))
            # Disable global fields and set to 0 (to avoid ambiguity)
            self.v_awake_lv.set("0")
            self.v_awake_star.set("0")
            self.entry_awake_lv.config(state="disabled", bg=PANEL)
            self.entry_awake_star.config(state="disabled", bg=PANEL)
            self.status("Specialized Awakening OFF. Awake stats forced to 0.")

    # ──────────────────────────────────────────────────────────────────────────────
    #  COMMANDS
    # ──────────────────────────────────────────────────────────────────────────────

    def status(self, msg, error=False, warn=False):
        c = RED if error else (WARN if warn else SUBTEXT)
        self._status_bar.config(fg=c)
        self.status_text.set(msg)

    def _clear_placeholder(self, widget):
        if "Paste raw JSON" in widget.get("1.0", "end"):
            widget.delete("1.0", "end")
            widget.config(fg=TEXT)

    def _cmd_clear(self):
        self.ids_text.delete("1.0", "end")
        self.ids_text.insert("1.0", DEFAULT_PET_IDS.replace(", ", "\n"))
        self.patch_input.delete("1.0", "end")
        self.patch_input.insert("1.0", "Paste raw JSON here to patch...")
        self.patch_input.config(fg=SUBTEXT)
        self.out_text.delete("1.0", "end")
        self.status("Cleared.")

    def _get_params(self):
        return {
            "user_id":      self.v_user_id.get().strip(),
            "star_id":      self.v_star_id.get().strip(),
            "star_spirit":  self.v_star_spirit.get().strip(),
            "level":        self.v_level.get().strip(),
            "quality":      self.v_quality.get().strip(),
            "hp":           self.v_hp.get().strip(),
            "rhp":          self.v_rhp.get().strip(),
            "atk":          self.v_atk.get().strip(),
            "exp":          self.v_exp.get().strip(),
            "might":        self.v_might.get().strip(),
            "pve_set_lv":   self.v_pve_set_lv.get().strip(),
            "pvp_set_lv":   self.v_pvp_set_lv.get().strip(),
            "awake_lv":     self.v_awake_lv.get().strip(),
            "awake_star":   self.v_awake_star.get().strip(),
            "source":       self.v_source.get().strip(),
            "create":       self.v_create_time.get().strip(),
            "update":       self.v_last_update.get().strip(),
        }

    def _collect_ids(self):
        txt = self.ids_text.get("1.0", "end").strip()
        ids = txt.replace(",", " ").split()
        return [pid.strip() for pid in ids if pid.strip()]

    def _collect_awaken_ids(self):
        txt = self.awaken_ids_text.get("1.0", "end").strip()
        ids = txt.replace(",", " ").split()
        return set(pid.strip() for pid in ids if pid.strip())

    def _forge_pets(self, ids, params):
        use_random = self.v_random_serial.get()
        use_special_awaken = self.v_awaken_toggle.get()
        awaken_ids = self._collect_awaken_ids() if use_special_awaken else set()
        
        results = []
        for pid in ids:
            # Force awake_star based on toggle/list
            if use_special_awaken:
                alvl = params["awake_lv"]
                astar = "3" if str(pid) in awaken_ids else params["awake_star"]
            else:
                alvl = "0"
                astar = "0"

            p = {
                "pet_serial_id":              make_serial(pid, use_random),
                "user_id":                    params["user_id"],
                "pet_id":                     str(pid),
                "current_hp":                 params["hp"],
                "current_rhp":                params["rhp"],
                "current_atk":                params["atk"],
                "level":                      params["level"],
                "quality":                    params["quality"],
                "star_id":                    params["star_id"],
                "star_spirit":                params["star_spirit"],
                "pvp_might":                  params["might"],
                "exp":                        params["exp"],
                "pve_set_lv":                 params["pve_set_lv"],
                "pvp_set_lv":                 params["pvp_set_lv"],
                "solid_passive_skill_serial": None,
                "source_from":                params["source"],
                "awake_level":                alvl,
                "awake_star":                 astar,
                "create_time":                params["create"],
                "last_update_time":           params["update"],
                "active_skills":              [],
                "solid_passive_skills":       [],
                "succinct_passive_skills":    [],
                "active_skills_id":           f"7{pid}",
                "pvp_active_skills_id":       f"72{pid}"
            }
            results.append(p)
        return results

    def _cmd_generate(self):
        ids = self._collect_ids()
        if not ids:
            self.status("No pet IDs provided!", error=True)
            return
        
        params = self._get_params()
        self.status(f"Generating for {len(ids)} pets...")
        self.update_idletasks()
        
        pets = self._forge_pets(ids, params)
        inner = json.dumps(pets, separators=(",", ":"), ensure_ascii=False)
        output = f'"pet_list_v2":{inner},"pet_god_list"'
        
        self.out_text.delete("1.0", "end")
        self.out_text.insert("1.0", output)
        self.status(f"✓ Generated {len(ids)} pets. Use 'burp_replace' mode.")

    def _cmd_patch(self):
        raw = self.patch_input.get("1.0", "end").strip()
        if not raw or "Paste raw JSON" in raw:
            self.status("Paste original response JSON first!", error=True)
            return

        ids = self._collect_ids()
        if not ids:
            self.status("No pet IDs provided!", error=True)
            return

        params = self._get_params()
        self.status("Patching...")
        self.update_idletasks()

        pets = self._forge_pets(ids, params)
        new_array = json.dumps(pets, separators=(",", ":"), ensure_ascii=False)
        
        start, end = extract_pet_list_v2(raw)
        if start is None:
            self.status("Could not find 'pet_list_v2' array in provided text.", error=True)
            return

        patched = raw[:start] + '"pet_list_v2":' + new_array + raw[end:]
        self.out_text.delete("1.0", "end")
        self.out_text.insert("1.0", patched)
        self.status(f"✓ Patched! {len(ids)} pets injected into response.")

    def _cmd_copy(self):
        txt = self.out_text.get("1.0", "end").strip()
        if not txt: return
        self._copy_to_clip(txt)
        self.status("✓ Copied to clipboard!")

    def _copy_to_clip(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

# ──────────────────────────────────────────────────────────────────────────────
#  GODDESS FORGER CLASS
# ──────────────────────────────────────────────────────────────────────────────

class GoddessGenApp(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Goddess Payload Forger Pro")
        self.geometry("1100x720")
        self.configure(bg=BG)
        self.transient(master)
        
        self._build_vars()
        self._build_ui()
        self.status("Goddess Forger Ready.")

    def _build_vars(self):
        self.v_user_id      = tk.StringVar(value="VVG0000034278")
        self.v_star_id      = tk.StringVar(value="5")
        self.v_star_spirit  = tk.StringVar(value="151")
        self.v_level        = tk.StringVar(value="99")
        self.v_might        = tk.StringVar(value="0")
        self.v_awake_lv     = tk.StringVar(value="0")
        self.v_awake_star   = tk.StringVar(value="0")
        self.v_create_time  = tk.StringVar(value="2025-03-20 06:18:33")
        self.v_last_update  = tk.StringVar(value="2026-02-23 11:49:43")
        self.v_random_serial = tk.BooleanVar(value=True)
        self.status_text     = tk.StringVar()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=PANEL, height=60)
        hdr.pack(fill="x", side="top")
        tk.Label(hdr, text="🌸 GODDESS PAYLOAD FORGER", bg=PANEL, fg=ACCENT2, 
                 font=("Segoe UI", 16, "bold"), padx=25).pack(side="left")

        # Status Bar
        self._status_bar = tk.Label(self, textvariable=self.status_text, bg=BG, fg=SUBTEXT, 
                                   font=("Segoe UI", 9), anchor="w", padx=20, pady=8)
        self._status_bar.pack(fill="x", side="bottom")

        # Main Layout
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=10)

        # Main Content Area
        main_content = tk.Frame(body, bg=BG)
        main_content.pack(fill="both", expand=True)

        # Parameters Card
        self._build_params_card(main_content)
        
        # IDs Card
        self._build_input_card(main_content)

        # Output Card
        self._build_output_card(main_content)

    def _build_params_card(self, parent):
        card = tk.Frame(parent, bg=PANEL, padx=15, pady=15)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(card, text="GODDESS PARAMETERS", bg=PANEL, fg=ACCENT2, 
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))

        fields = [
            ("User ID", self.v_user_id), ("Level", self.v_level), ("Star ID", self.v_star_id),
            ("Star Spirit", self.v_star_spirit), ("Might", self.v_might), 
            ("Awake Lv", self.v_awake_lv), ("Awake Star", self.v_awake_star)
        ]

        for i, (label, var) in enumerate(fields):
            r, c = divmod(i, 3)
            tk.Label(card, text=label, bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8, "bold")).grid(row=r*2+1, column=c*2, sticky="w", padx=(5, 5))
            e = tk.Entry(card, textvariable=var, bg=BG, fg=TEXT, insertbackground=TEXT, 
                         relief="flat", font=("Segoe UI", 9), width=15,
                         highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT2)
            e.grid(row=r*2+1, column=c*2+1, pady=3, padx=(0, 15))

        cb_frame = tk.Frame(card, bg=PANEL)
        cb_frame.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))
        tk.Checkbutton(cb_frame, text="Random Serial", variable=self.v_random_serial,
                       bg=PANEL, fg=TEXT, selectcolor=BG, activebackground=PANEL, 
                       activeforeground=ACCENT2, font=("Segoe UI", 8, "bold")).pack(side="left")

        tk.Label(card, text="Create Time:", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8)).grid(row=5, column=2, sticky="e")
        tk.Entry(card, textvariable=self.v_create_time, bg=BG, fg=TEXT, font=("Segoe UI", 8), width=20, relief="flat", highlightthickness=1, highlightbackground=BORDER).grid(row=5, column=3, padx=5)
        
        tk.Label(card, text="Update Time:", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8)).grid(row=5, column=4, sticky="e")
        tk.Entry(card, textvariable=self.v_last_update, bg=BG, fg=TEXT, font=("Segoe UI", 8), width=20, relief="flat", highlightthickness=1, highlightbackground=BORDER).grid(row=5, column=5, padx=5)

    def _build_input_card(self, parent):
        card = tk.Frame(parent, bg=PANEL, padx=15, pady=15)
        card.pack(fill="both", expand=True, pady=(0, 10))

        tk.Label(card, text="GODDESS IDs (3001-3007 default)", bg=PANEL, fg=ACCENT2, 
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")

        self.ids_text = tk.Text(card, bg=BG, fg=TEXT, font=("Consolas", 9), height=8, 
                               relief="flat", highlightthickness=1, highlightbackground=BORDER)
        self.ids_text.pack(fill="both", expand=True, pady=5)
        self.ids_text.insert("1.0", DEFAULT_GODDESS_IDS.replace(", ", "\n"))

    def _build_output_card(self, parent):
        card = tk.Frame(parent, bg=PANEL, padx=15, pady=15)
        card.pack(fill="x")

        btn_frame = tk.Frame(card, bg=PANEL)
        btn_frame.pack(fill="x", pady=(0, 10))

        self._styled_button(btn_frame, "🌸 GENERATE GODDESS PAYLOAD", ACCENT2, self._cmd_generate).pack(side="left")
        self._styled_button(btn_frame, "🧹 CLEAR", BORDER, self._cmd_clear).pack(side="right")

        tk.Label(card, text="GENERATED OUTPUT", bg=PANEL, fg=GREEN, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.out_text = tk.Text(card, bg=BG, fg=TEXT, font=("Consolas", 9), height=8, 
                               relief="flat", highlightthickness=1, highlightbackground=BORDER)
        self.out_text.pack(fill="x", pady=5)

        copy_frame = tk.Frame(card, bg=PANEL)
        copy_frame.pack(fill="x")
        self._styled_button(copy_frame, "📋 COPY OUTPUT", GREEN, self._cmd_copy, padx=10, pady=5, font=("Segoe UI", 8, "bold")).pack(side="left")

        tk.Label(copy_frame, text='Match Regex:', bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(20, 5))
        self.regex_entry = tk.Entry(copy_frame, bg=BG, fg=ACCENT2, font=("Consolas", 9), width=40, relief="flat", highlightthickness=1, highlightbackground=BORDER)
        self.regex_entry.pack(side="left")
        self.regex_entry.insert(0, '"goddess_record":\\[.*?\\]')
        self._styled_button(copy_frame, "📋 COPY REGEX", ACCENT2, lambda: self._copy_to_clip(self.regex_entry.get()), padx=10, pady=5, font=("Segoe UI", 8, "bold")).pack(side="left", padx=5)

    def _styled_button(self, parent, text, color, command, **kw):
        # Access shared logic from PetGenApp if needed, but here we rebuild it for Toplevel context
        padx = kw.pop("padx", 20)
        pady = kw.pop("pady", 10)
        font = kw.pop("font", ("Segoe UI", 10, "bold"))
        btn = tk.Label(parent, text=text, bg=color, fg=TEXT, cursor="hand2",
                       padx=padx, pady=pady, font=font, **kw)
        btn.bind("<Button-1>", lambda e: command())
        orig_color = color
        def on_enter(e): btn.config(bg=self._lighten(orig_color, 20))
        def on_leave(e): btn.config(bg=orig_color)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _lighten(self, hex_color, amount):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(min(255, c + amount) for c in rgb)
        return '#%02x%02x%02x' % new_rgb

    def status(self, msg, error=False):
        c = RED if error else SUBTEXT
        self._status_bar.config(fg=c)
        self.status_text.set(msg)

    def _cmd_clear(self):
        self.ids_text.delete("1.0", "end")
        self.ids_text.insert("1.0", DEFAULT_GODDESS_IDS.replace(", ", "\n"))
        self.out_text.delete("1.0", "end")
        self.status("Cleared.")

    def _cmd_generate(self):
        txt = self.ids_text.get("1.0", "end").strip()
        ids = txt.replace(",", " ").split()
        ids = [pid.strip() for pid in ids if pid.strip()]
        if not ids:
            self.status("No Goddess IDs provided!", error=True)
            return

        results = []
        for gid in ids:
            results.append({
                "goddess_serial_id": hashlib.sha1(os.urandom(32)).hexdigest() if self.v_random_serial.get() else make_serial(gid),
                "user_id": self.v_user_id.get(),
                "goddess_id": str(gid),
                "level": self.v_level.get(),
                "star_id": self.v_star_id.get(),
                "star_spirit": self.v_star_spirit.get(),
                "pvp_might": self.v_might.get(),
                "awake_level": self.v_awake_lv.get(),
                "awake_star": self.v_awake_star.get(),
                "create_time": self.v_create_time.get(),
                "last_update_time": self.v_last_update.get(),
                "skin_record": [],
                "skin_highest_star_record": [],
                "talent_record": [],
                "skin_skill": []
            })
        
        output = f'"goddess_record":{json.dumps(results, separators=(",", ":"), ensure_ascii=False)}'
        self.out_text.delete("1.0", "end")
        self.out_text.insert("1.0", output)
        self.status(f"✓ Generated {len(results)} goddesses.")

    def _cmd_copy(self):
        txt = self.out_text.get("1.0", "end").strip()
        if txt: self._copy_to_clip(txt)
        self.status("✓ Copied to clipboard!")

    def _copy_to_clip(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

if __name__ == "__main__":
    try:
        app = PetGenApp()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Critical Error", str(e))
