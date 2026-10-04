"""Desktop Spotlight Quick Box: Floating prompt optimizer summoned by Win+O.
Features:
- Global system-wide hotkeys Win+O and Alt+O
- Automatically pops up to foreground when summoned
- Displays exclusively the High Precision optimized prompt
- Ambiguity detection with 1-click option pills
- Quick demo presets (CSV Analyst, Support Bot, JSON Extractor, Code Reviewer)
- Self-contained in-process fallback if HTTP server is offline
- 1-Key instant copy (Enter / Ctrl+C, Esc to hide)
"""

import json
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import ctypes
from typing import Optional, Dict, Any, List

try:
    import keyboard
except ImportError:
    keyboard = None

from prompt_optimizer.backends.ollama import OllamaBackend
from prompt_optimizer.backends.mock import MockLLMBackend
from prompt_optimizer.core.quick_optimizer import QuickOptimizer

logger = logging.getLogger(__name__)
API_ENDPOINT = "http://localhost:8000/api/quick-optimize"

PRESETS = {
    "csv": (
        "Hey! Could you please act as a senior python developer and write a python function that reads "
        "a CSV file containing user records and computes the averages for all numerical columns? Please "
        "make sure it outputs strictly valid JSON only. Please never make up or hallucinate non-existent "
        "columns, and please handle errors. As I said before, please make sure it's valid JSON! Thank you!"
    ),
    "support": (
        "Hello! Please act as a polite customer support agent for our cloud software company. Always be warm "
        "and courteous in your greetings. Never share internal IP addresses or server credentials under any "
        "circumstance. If asked about refunds, direct them to billing.example.com. Keep answers under 3 paragraphs."
    ),
    "json": (
        "You are an automated extraction agent. Parse server log lines from the input. Extract timestamp, "
        "request_id, and status_code into a clean JSON list. Do not hallucinate missing fields, and do not wrap "
        "output in conversational text."
    ),
    "code": (
        "Please review this Python code. Check for SQL injection vulnerabilities, async concurrency bottlenecks, "
        "and memory leaks. Give concrete code diffs and keep explanations brief and technical."
    ),
}


class SpotlightApp:
    """Floating Spotlight-style Box that pops up on Win+O and displays High Precision prompts."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("⚡ PromptCompiler Spotlight [Win+O]")
        self.root.geometry("840x620")
        self.root.configure(bg="#0d1117")

        self._center_window(840, 620)

        # In-process backup optimizer
        self.fallback_backend = OllamaBackend() if OllamaBackend().is_available() else MockLLMBackend()
        self.fallback_optimizer = QuickOptimizer(backend=self.fallback_backend)

        self.current_response: Optional[Dict[str, Any]] = None
        self.clarification_answers: Dict[str, str] = {}
        self.active_question_id: Optional[str] = None
        self.is_visible = True

        self._build_ui()
        self._bind_shortcuts()
        self._setup_global_hotkeys()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Automatically pop up immediately upon launching
        self.root.after(100, self.show_window)

    def _center_window(self, w: int, h: int):
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w // 2) - (w // 2)
        y = (screen_h // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Header Container
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
            text="Global Hotkey: Win+O (or Alt+O)",
            font=("Segoe UI", 9, "bold"),
            fg="#2ea043",
            bg="#21262d",
            padx=8,
            pady=2
        )
        hotkey_tag.pack(side="left", padx=(10, 0))

        esc_hint = tk.Label(
            top_row,
            text="Esc: Hide  |  Ctrl+Enter: Run  |  Enter: Copy Prompt",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#161b22"
        )
        esc_hint.pack(side="right")

        # Presets Bar
        presets_bar = tk.Frame(header_frame, bg="#161b22")
        presets_bar.pack(fill="x", pady=(2, 6))

        tk.Label(
            presets_bar,
            text="💡 Presets:",
            font=("Segoe UI", 8, "bold"),
            fg="#8b949e",
            bg="#161b22"
        ).pack(side="left", padx=(0, 6))

        for key, name in [
            ("csv", "📊 CSV Analyst"),
            ("support", "💬 Support Bot"),
            ("json", "⚡ JSON Extractor"),
            ("code", "🐍 Code Reviewer")
        ]:
            btn = tk.Button(
                presets_bar,
                text=name,
                font=("Segoe UI", 8),
                bg="#21262d",
                fg="#c9d1d9",
                activebackground="#30363d",
                relief="flat",
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda k=key: self.load_preset(k)
            )
            btn.pack(side="left", padx=3)

        # Input text area
        self.input_text = tk.Text(
            header_frame,
            height=3,
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
            text="Type prompt above or pick a preset, then press Ctrl+Enter to optimize.",
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

        # Ambiguity Banner
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
            text="⚠️ Ambiguity Detected: Please clarify what you want:",
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
            wraplength=800,
            justify="left"
        )
        self.ambiguity_q_lbl.pack(anchor="w", pady=(2, 4))

        # Option pills
        self.pills_container = tk.Frame(self.ambiguity_frame, bg="#2d2200")
        self.pills_container.pack(fill="x", pady=(2, 6))

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

        # Results Container (Dedicated Solely to High Precision)
        self.results_frame = tk.Frame(self.root, bg="#0d1117")
        self.results_frame.pack(fill="both", expand=True, padx=14, pady=6)

        # Dedicated High Precision Card
        self.card_hp = tk.Frame(
            self.results_frame,
            bg="#161b22",
            highlightthickness=1,
            highlightbackground="#30363d",
            padx=14,
            pady=12
        )
        self.card_hp.pack(fill="both", expand=True)

        hp_head = tk.Frame(self.card_hp, bg="#161b22")
        hp_head.pack(fill="x")

        tk.Label(
            hp_head,
            text="🎯 High Precision Prompt (Strict & Complete)",
            font=("Segoe UI", 10, "bold"),
            fg="#58a6ff",
            bg="#161b22"
        ).pack(side="left")

        self.hp_badge = tk.Label(
            hp_head,
            text="0 tokens",
            font=("Segoe UI", 8, "bold"),
            fg="#58a6ff",
            bg="#21262d",
            padx=8,
            pady=2
        )
        self.hp_badge.pack(side="right")

        self.hp_desc = tk.Label(
            self.card_hp,
            text="Structured schema, strict invariants, explicit edge-case negative constraints.",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#161b22",
            anchor="w"
        )
        self.hp_desc.pack(fill="x", pady=(2, 6))

        # Full-sized text area for High Precision prompt
        self.hp_text = tk.Text(
            self.card_hp,
            bg="#0d1117",
            fg="#e6edf3",
            font=("Consolas", 10),
            wrap="word",
            relief="flat",
            padx=10,
            pady=8,
            highlightthickness=1,
            highlightbackground="#30363d"
        )
        self.hp_text.pack(fill="both", expand=True, pady=4)

        # Footer with Copy Button
        footer_row = tk.Frame(self.card_hp, bg="#161b22")
        footer_row.pack(fill="x", pady=(6, 0))

        self.copy_hp_btn = tk.Button(
            footer_row,
            text="📋 Copy High Precision Prompt (Enter / Ctrl+C)",
            bg="#238636",
            fg="white",
            activebackground="#2ea043",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            pady=6,
            cursor="hand2",
            command=self.copy_high_precision
        )
        self.copy_hp_btn.pack(fill="x")

    def _bind_shortcuts(self):
        self.root.bind("<Escape>", lambda e: self.hide_window())
        self.root.bind("<Control-Return>", lambda e: self.start_optimization())
        self.root.bind("<Alt-Return>", lambda e: self.start_optimization())

        # Copy when pressing Enter outside of text inputs
        self.root.bind("<Return>", self._handle_return_key)
        self.root.bind("<Control-c>", self._handle_ctrl_c)

    def _handle_return_key(self, event):
        focused = self.root.focus_get()
        if focused not in [self.input_text, self.clarify_entry]:
            self.copy_high_precision()

    def _handle_ctrl_c(self, event):
        focused = self.root.focus_get()
        if focused not in [self.input_text, self.clarify_entry]:
            self.copy_high_precision()

    def _setup_global_hotkeys(self):
        """Register global Win+O, Alt+O, and Ctrl+Alt+O hotkeys."""
        if not keyboard:
            logger.warning("Keyboard library not available. Global hotkeys disabled.")
            return

        def on_hotkey_pressed():
            self.root.after(0, self.show_window)

        hotkeys = ["win+o", "windows+o", "alt+o", "ctrl+alt+o"]
        for hk in hotkeys:
            try:
                keyboard.add_hotkey(hk, on_hotkey_pressed)
                logger.info(f"Registered global hotkey: {hk}")
            except Exception as e:
                logger.debug(f"Hotkey {hk} registration note: {e}")

    def show_window(self):
        """Automatically pop up and force foreground on Windows."""
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.attributes("-topmost", True)
        self._center_window(840, 620)
        self.is_visible = True

        # Win32 force foreground to bypass Windows focus lock
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            hwnd = self.root.winfo_id()
            root_hwnd = user32.GetAncestor(hwnd, 2) or hwnd  # GA_ROOT = 2

            # SW_RESTORE = 9, SW_SHOW = 5
            user32.ShowWindow(root_hwnd, 9)

            fg_hwnd = user32.GetForegroundWindow()
            fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
            cur_thread = kernel32.GetCurrentThreadId()

            if fg_thread != cur_thread:
                user32.AttachThreadInput(fg_thread, cur_thread, True)
                user32.SetForegroundWindow(root_hwnd)
                user32.BringWindowToTop(root_hwnd)
                user32.AttachThreadInput(fg_thread, cur_thread, False)
            else:
                user32.SetForegroundWindow(root_hwnd)
                user32.BringWindowToTop(root_hwnd)
        except Exception as e:
            logger.debug(f"Win32 foreground note: {e}")

        self.root.focus_force()
        self.input_text.focus_set()

        # Release hard topmost lock after 500ms so other windows can be used if desired
        self.root.after(500, lambda: self.root.attributes("-topmost", False))

    def hide_window(self):
        """Hide window to background."""
        self.root.withdraw()
        self.is_visible = False

    def toggle_window(self):
        if self.is_visible:
            self.hide_window()
        else:
            self.show_window()

    def load_preset(self, key: str):
        text = PRESETS.get(key, "")
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, text)
        self.start_optimization()

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
        self.status_lbl.config(text="⚡ Compiling high precision prompt...", fg="#58a6ff")
        self.optimize_btn.config(state="disabled")

        threading.Thread(
            target=self._execute_optimization,
            args=(raw, self.clarification_answers),
            daemon=True
        ).start()

    def _execute_optimization(self, raw_prompt: str, answers: Dict[str, str]):
        """Call FastAPI backend if up, or fall back to in-process engine seamlessly."""
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
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.root.after(0, self._render_results, data)
                return
        except Exception as e:
            logger.info(f"API endpoint offline ({e}). Using in-process engine fallback.")

        # In-process execution fallback
        try:
            res = self.fallback_optimizer.optimize_quick(
                raw_prompt=raw_prompt,
                clarification_answers=answers if answers else None,
            )
            data = res.model_dump()
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
                    text=f"Question: {q.get('question')}\nDefault Assumption: {q.get('default_assumption')}"
                )
                self.clarify_entry.delete(0, tk.END)

                # Render Clickable Option Pills
                for widget in self.pills_container.winfo_children():
                    widget.destroy()

                options = q.get("suggested_options", []) or ["Strict JSON", "Markdown Table", "Plain text bullets"]
                for opt in options:
                    pill_btn = tk.Button(
                        self.pills_container,
                        text=opt,
                        bg="#21262d",
                        fg="#e3b341",
                        activebackground="#d29922",
                        activeforeground="black",
                        font=("Segoe UI", 8),
                        relief="flat",
                        padx=8,
                        pady=2,
                        cursor="hand2",
                        command=lambda o=opt: self.choose_option(o)
                    )
                    pill_btn.pack(side="left", padx=3)

                self.ambiguity_frame.pack(fill="x", padx=14, pady=(0, 6), before=self.results_frame)
                self.clarify_entry.focus_set()
                self.status_lbl.config(text="Ambiguity detected. Click an option or answer above.", fg="#d29922")
                return

        # Status == "ready": Display ONLY High Precision Result
        self.ambiguity_frame.pack_forget()
        self.current_response = data

        hp = data.get("high_precision", {})

        self.hp_text.delete("1.0", tk.END)
        self.hp_text.insert(tk.END, hp.get("prompt_text", ""))
        self.hp_badge.config(text=f"{hp.get('token_count', 0)} tokens")
        self.hp_desc.config(text=hp.get("description", "Structured schema, invariants & edge cases."))

        self.status_lbl.config(
            text="✓ High Precision Prompt ready! Press Enter or click Copy button.",
            fg="#2ea043"
        )
        self.copy_hp_btn.focus_set()

    def choose_option(self, option_text: str):
        self.clarify_entry.delete(0, tk.END)
        self.clarify_entry.insert(tk.END, option_text)
        self.submit_clarification()

    def submit_clarification(self):
        val = self.clarify_entry.get().strip()
        if self.active_question_id and val:
            self.clarification_answers[self.active_question_id] = val
        self.start_optimization()

    def copy_high_precision(self):
        txt = self.hp_text.get("1.0", tk.END).strip()
        if txt:
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            self.card_hp.config(highlightbackground="#2ea043")
            self.status_lbl.config(text="✓ High Precision Prompt copied to clipboard! (Esc to hide)", fg="#2ea043")
            self.root.after(1500, lambda: self.card_hp.config(highlightbackground="#30363d"))

    def _handle_error(self, err_msg: str):
        self.optimize_btn.config(state="normal")
        self.status_lbl.config(text=f"Error: {err_msg}", fg="#f85149")


def launch():
    root = tk.Tk()
    app = SpotlightApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
