"""Desktop Spotlight Quick Box: Floating prompt optimizer summoned by Win+O."""

import json
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
from typing import Optional, Dict, Any

try:
    import keyboard
except ImportError:
    keyboard = None

logger = logging.getLogger(__name__)
API_ENDPOINT = "http://localhost:8000/api/quick-optimize"


class SpotlightApp:
    """Floating Spotlight-style Box for instant prompt optimization summoned by Win+O."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("⚡ PromptCompiler Spotlight [Win+O]")
        self.root.geometry("820x600")
        self.root.configure(bg="#0d1117")
        self.root.attributes("-topmost", True)

        # Center on screen
        self._center_window(820, 600)

        self.current_response: Optional[Dict[str, Any]] = None
        self.clarification_answers: Dict[str, str] = {}
        self.active_question_id: Optional[str] = None
        self.is_visible = True

        self._build_ui()
        self._bind_shortcuts()
        self._setup_global_hotkeys()

        # Handle window close button (X) -> hide to background instead of terminate
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def _center_window(self, w: int, h: int):
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w // 2) - (w // 2)
        y = (screen_h // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Header / Search bar container
        header_frame = tk.Frame(
            self.root,
            bg="#161b22",
            padx=16,
            pady=12,
            highlightthickness=1,
            highlightbackground="#30363d"
        )
        header_frame.pack(fill="x", padx=14, pady=(12, 6))

        top_row = tk.Frame(header_frame, bg="#161b22")
        top_row.pack(fill="x", pady=(0, 6))

        logo_lbl = tk.Label(
            top_row,
            text="⚡ PromptCompiler Spotlight",
            font=("Segoe UI", 11, "bold"),
            fg="#58a6ff",
            bg="#161b22"
        )
        logo_lbl.pack(side="left")

        hotkey_tag = tk.Label(
            top_row,
            text="Global Hotkey: Win+O",
            font=("Segoe UI", 9, "bold"),
            fg="#2ea043",
            bg="#21262d",
            padx=6,
            pady=1
        )
        hotkey_tag.pack(side="left", padx=(10, 0))

        esc_hint = tk.Label(
            top_row,
            text="Esc: Hide  |  Ctrl+Enter: Run  |  [1] Copy Concise  |  [2] Copy Precision",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#161b22"
        )
        esc_hint.pack(side="right")

        # Input text area
        self.input_text = tk.Text(
            header_frame,
            height=4,
            bg="#0d1117",
            fg="#f0f6fc",
            insertbackground="#58a6ff",
            font=("Segoe UI", 10),
            wrap="word",
            relief="flat",
            padx=10,
            pady=8,
            highlightthickness=1,
            highlightbackground="#30363d"
        )
        self.input_text.pack(fill="x", pady=4)
        self.input_text.focus_set()

        # Action bar under input
        btn_bar = tk.Frame(header_frame, bg="#161b22")
        btn_bar.pack(fill="x", pady=(4, 0))

        self.status_lbl = tk.Label(
            btn_bar,
            text="Type or paste prompt above, then press Ctrl+Enter to optimize.",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#161b22"
        )
        self.status_lbl.pack(side="left")

        self.optimize_btn = tk.Button(
            btn_bar,
            text="⚡ Optimize (Ctrl+Enter)",
            bg="#238636",
            fg="white",
            activebackground="#2ea043",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=12,
            pady=3,
            cursor="hand2",
            command=self.start_optimization
        )
        self.optimize_btn.pack(side="right")

        paste_btn = tk.Button(
            btn_bar,
            text="📋 Paste Clipboard",
            bg="#21262d",
            fg="#c9d1d9",
            activebackground="#30363d",
            font=("Segoe UI", 8),
            relief="flat",
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.paste_clipboard
        )
        paste_btn.pack(side="right", padx=(0, 6))

        clear_btn = tk.Button(
            btn_bar,
            text="🗑️ Clear",
            bg="#21262d",
            fg="#8b949e",
            activebackground="#30363d",
            font=("Segoe UI", 8),
            relief="flat",
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.clear_input
        )
        clear_btn.pack(side="right", padx=(0, 6))

        # Ambiguity Banner (Hidden by default)
        self.ambiguity_frame = tk.Frame(
            self.root,
            bg="#2d2200",
            padx=14,
            pady=10,
            highlightthickness=1,
            highlightbackground="#d29922"
        )

        amb_top = tk.Frame(self.ambiguity_frame, bg="#2d2200")
        amb_top.pack(fill="x")
        self.ambiguity_lbl = tk.Label(
            amb_top,
            text="⚠️ Ambiguity Detected: What did you intend?",
            font=("Segoe UI", 9, "bold"),
            fg="#e3b341",
            bg="#2d2200"
        )
        self.ambiguity_lbl.pack(side="left")

        self.ambiguity_q_lbl = tk.Label(
            self.ambiguity_frame,
            text="",
            font=("Segoe UI", 9),
            fg="#f0f6fc",
            bg="#2d2200",
            wraplength=760,
            justify="left"
        )
        self.ambiguity_q_lbl.pack(anchor="w", pady=(2, 6))

        q_input_row = tk.Frame(self.ambiguity_frame, bg="#2d2200")
        q_input_row.pack(fill="x")

        self.clarify_entry = tk.Entry(
            q_input_row,
            bg="#0d1117",
            fg="#f0f6fc",
            insertbackground="#e3b341",
            font=("Segoe UI", 9),
            relief="flat",
            highlightthickness=1,
            highlightbackground="#d29922"
        )
        self.clarify_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=3)
        self.clarify_entry.bind("<Return>", lambda e: self.submit_clarification())

        self.clarify_submit_btn = tk.Button(
            q_input_row,
            text="Apply & Run ↵",
            bg="#d29922",
            fg="black",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=12,
            cursor="hand2",
            command=self.submit_clarification
        )
        self.clarify_submit_btn.pack(side="right")

        # Results Container (Split 2 Columns: Concise vs High Precision)
        self.results_frame = tk.Frame(self.root, bg="#0d1117")
        self.results_frame.pack(fill="both", expand=True, padx=14, pady=6)

        # Card 1: Concise (Fast & Lean)
        self.card_concise = tk.Frame(
            self.results_frame,
            bg="#161b22",
            highlightthickness=1,
            highlightbackground="#30363d",
            padx=12,
            pady=10
        )
        self.card_concise.pack(side="left", fill="both", expand=True, padx=(0, 6))

        c1_head = tk.Frame(self.card_concise, bg="#161b22")
        c1_head.pack(fill="x")
        tk.Label(
            c1_head,
            text="1️⃣ Concise (Fast & Lean)",
            font=("Segoe UI", 9, "bold"),
            fg="#2ea043",
            bg="#161b22"
        ).pack(side="left")
        self.c1_badge = tk.Label(
            c1_head,
            text="0 tokens",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#21262d",
            padx=6,
            pady=1
        )
        self.c1_badge.pack(side="right")

        self.c1_desc = tk.Label(
            self.card_concise,
            text="Minimalist imperative directives, trims soft styling.",
            font=("Segoe UI", 7),
            fg="#8b949e",
            bg="#161b22",
            anchor="w"
        )
        self.c1_desc.pack(fill="x", pady=(2, 4))

        self.c1_text = tk.Text(
            self.card_concise,
            bg="#0d1117",
            fg="#e6edf3",
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            padx=8,
            pady=6,
            highlightthickness=1,
            highlightbackground="#30363d"
        )
        self.c1_text.pack(fill="both", expand=True, pady=4)

        self.copy_c1_btn = tk.Button(
            self.card_concise,
            text="📋 Copy Concise [Key: 1]",
            bg="#21262d",
            fg="#c9d1d9",
            activebackground="#2ea043",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            pady=5,
            cursor="hand2",
            command=self.copy_concise
        )
        self.copy_c1_btn.pack(fill="x", pady=(4, 0))

        # Card 2: High Precision (Strict & Complete)
        self.card_hp = tk.Frame(
            self.results_frame,
            bg="#161b22",
            highlightthickness=1,
            highlightbackground="#30363d",
            padx=12,
            pady=10
        )
        self.card_hp.pack(side="right", fill="both", expand=True, padx=(6, 0))

        c2_head = tk.Frame(self.card_hp, bg="#161b22")
        c2_head.pack(fill="x")
        tk.Label(
            c2_head,
            text="2️⃣ High Precision (Strict)",
            font=("Segoe UI", 9, "bold"),
            fg="#58a6ff",
            bg="#161b22"
        ).pack(side="left")
        self.c2_badge = tk.Label(
            c2_head,
            text="0 tokens",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#21262d",
            padx=6,
            pady=1
        )
        self.c2_badge.pack(side="right")

        self.c2_desc = tk.Label(
            self.card_hp,
            text="Structured schema, strict execution invariants & edge cases.",
            font=("Segoe UI", 7),
            fg="#8b949e",
            bg="#161b22",
            anchor="w"
        )
        self.c2_desc.pack(fill="x", pady=(2, 4))

        self.c2_text = tk.Text(
            self.card_hp,
            bg="#0d1117",
            fg="#e6edf3",
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            padx=8,
            pady=6,
            highlightthickness=1,
            highlightbackground="#30363d"
        )
        self.c2_text.pack(fill="both", expand=True, pady=4)

        self.copy_c2_btn = tk.Button(
            self.card_hp,
            text="📋 Copy High Precision [Key: 2]",
            bg="#21262d",
            fg="#c9d1d9",
            activebackground="#58a6ff",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            pady=5,
            cursor="hand2",
            command=self.copy_high_precision
        )
        self.copy_c2_btn.pack(fill="x", pady=(4, 0))

    def _bind_shortcuts(self):
        self.root.bind("<Escape>", lambda e: self.hide_window())
        self.root.bind("<Control-Return>", lambda e: self.start_optimization())
        self.root.bind("<Alt-Return>", lambda e: self.start_optimization())

        # Hotkeys 1 and 2 to copy
        self.root.bind("1", lambda e: self.copy_concise() if self.current_response and self.root.focus_get() not in [self.input_text, self.clarify_entry] else None)
        self.root.bind("2", lambda e: self.copy_high_precision() if self.current_response and self.root.focus_get() not in [self.input_text, self.clarify_entry] else None)

    def _setup_global_hotkeys(self):
        """Register global Win+O hotkey to summon the Spotlight box."""
        if not keyboard:
            logger.warning("Keyboard library not available. Global hotkey disabled.")
            return

        def on_hotkey_pressed():
            # Dispatch to Tkinter main thread safely
            self.root.after(0, self.toggle_window)

        try:
            keyboard.add_hotkey("win+o", on_hotkey_pressed)
            # Also bind alt+o as a seamless alternative
            keyboard.add_hotkey("alt+o", on_hotkey_pressed)
            logger.info("Registered global hotkeys: Win+O and Alt+O")
        except Exception as e:
            logger.error(f"Failed to register global hotkey: {e}")

    def show_window(self):
        """Summon and focus the window on screen."""
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self._center_window(820, 600)
        self.root.focus_force()
        self.input_text.focus_set()
        self.is_visible = True

    def hide_window(self):
        """Hide window to background."""
        self.root.withdraw()
        self.is_visible = False

    def toggle_window(self):
        """Toggle visible/hidden state when hotkey is pressed."""
        if self.is_visible:
            # If already open and focused, hide; if open but unfocused, bring forward
            self.show_window()
        else:
            self.show_window()

    def clear_input(self):
        self.input_text.delete("1.0", tk.END)
        self.input_text.focus_set()

    def paste_clipboard(self):
        try:
            cb = self.root.clipboard_get()
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert(tk.END, cb)
        except Exception:
            pass

    def start_optimization(self):
        raw = self.input_text.get("1.0", tk.END).strip()
        if not raw:
            return
        self.status_lbl.config(text="⚡ Compiling prompt in background...", fg="#58a6ff")
        self.optimize_btn.config(state="disabled")

        threading.Thread(
            target=self._call_backend,
            args=(raw, self.clarification_answers),
            daemon=True
        ).start()

    def _call_backend(self, raw_prompt: str, answers: Dict[str, str]):
        payload = json.dumps({
            "raw_prompt": raw_prompt,
            "backend_type": "mock",
            "clarification_answers": answers if answers else None
        }).encode("utf-8")

        req = urllib.request.Request(
            API_ENDPOINT,
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.root.after(0, self._render_results, data)
        except Exception as e:
            self.root.after(0, self._handle_error, str(e))

    def _render_results(self, data: Dict[str, Any]):
        self.optimize_btn.config(state="normal")
        status = data.get("status")

        if status == "needs_clarification":
            questions = data.get("clarification_questions", [])
            if questions:
                q = questions[0]
                self.active_question_id = q.get("id")
                self.ambiguity_q_lbl.config(
                    text=f"Question: {q.get('question')}\nDefault: {q.get('default_assumption')}"
                )
                self.clarify_entry.delete(0, tk.END)
                self.ambiguity_frame.pack(fill="x", padx=14, pady=(0, 6), before=self.results_frame)
                self.clarify_entry.focus_set()
                self.status_lbl.config(text="Ambiguity detected. Answer question above or press Apply.", fg="#d29922")
                return

        # Status == "ready"
        self.ambiguity_frame.pack_forget()
        self.current_response = data

        concise = data.get("concise", {})
        hp = data.get("high_precision", {})

        # Fill Concise
        self.c1_text.delete("1.0", tk.END)
        self.c1_text.insert(tk.END, concise.get("prompt_text", ""))
        pct = concise.get("reduction_percentage", 0)
        self.c1_badge.config(text=f"{concise.get('token_count', 0)} tokens (-{pct:.0f}%)")
        self.c1_desc.config(text=concise.get("description", "Minimalist imperative directives."))

        # Fill High Precision
        self.c2_text.delete("1.0", tk.END)
        self.c2_text.insert(tk.END, hp.get("prompt_text", ""))
        self.c2_badge.config(text=f"{hp.get('token_count', 0)} tokens")
        self.c2_desc.config(text=hp.get("description", "Structured schema & invariants."))

        self.status_lbl.config(
            text="Optimization complete! Press [1] for Concise, [2] for High Precision.",
            fg="#2ea043"
        )

    def submit_clarification(self):
        val = self.clarify_entry.get().strip()
        if self.active_question_id and val:
            self.clarification_answers[self.active_question_id] = val
        self.start_optimization()

    def copy_concise(self):
        txt = self.c1_text.get("1.0", tk.END).strip()
        if txt:
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            self.status_lbl.config(text="✓ Concise Prompt copied to clipboard! (Press Esc to hide)", fg="#2ea043")

    def copy_high_precision(self):
        txt = self.c2_text.get("1.0", tk.END).strip()
        if txt:
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            self.status_lbl.config(text="✓ High Precision Prompt copied to clipboard! (Press Esc to hide)", fg="#58a6ff")

    def _handle_error(self, err_msg: str):
        self.optimize_btn.config(state="normal")
        self.status_lbl.config(text=f"Error: {err_msg}", fg="#f85149")


def launch():
    root = tk.Tk()
    app = SpotlightApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
