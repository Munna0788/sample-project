"""Desktop Spotlight Quick Box: Minimalist prompt optimizer summoned by Win+O.
Features:
- Pure minimal layout: Paste text and hit Enter to generate
- Global system-wide hotkeys Win+O and Alt+O
- Automatically pops up to foreground when summoned
- Press Enter directly to generate
- High Precision prompt with real-time Token Optimization
- 1-Click copy (Enter / Click to copy, Esc to hide)
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


class SpotlightApp:
    """Minimalist Spotlight-style Box: Paste and Generate with instant token optimization."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("⚡ Prompt Compiler [Win+O]")
        self.root.geometry("820x580")
        self.root.configure(bg="#0d1117")

        self._position_window(680, 320)

        # In-process backup optimizer
        self.dynamic_backend = OllamaBackend() if OllamaBackend().is_available() else MockLLMBackend()
        self.fallback_optimizer = QuickOptimizer(backend=self.dynamic_backend)

        self.current_response: Optional[Dict[str, Any]] = None
        self.is_visible = True

        self._build_ui()
        self._bind_shortcuts()
        self._setup_global_hotkeys()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Automatically pop up immediately upon launching
        self.root.after(100, self.show_window)

    def _position_window(self, w: int = 680, h: int = 320):
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w // 2) - (w // 2)
        # Position floating pleasantly above the bottom chat input bar
        y = max(40, screen_h - h - 150)
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
            text="⚡ Prompt Compiler",
            font=("Segoe UI", 11, "bold"),
            fg="#58a6ff",
            bg="#161b22"
        )
        logo_lbl.pack(side="left")

        hotkey_tag = tk.Label(
            top_row,
            text="Win+O",
            font=("Segoe UI", 9, "bold"),
            fg="#2ea043",
            bg="#21262d",
            padx=8,
            pady=2
        )
        hotkey_tag.pack(side="left", padx=(10, 0))

        esc_tag = tk.Label(
            top_row,
            text="Esc to hide",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#161b22"
        )
        esc_tag.pack(side="right")

        # Input text area (Enter directly generates!)
        self.input_text = tk.Text(
            header_frame,
            height=3,
            bg="#0d1117",
            fg="#f0f6fc",
            insertbackground="#58a6ff",
            font=("Segoe UI", 10),
            wrap="word",
            relief="flat",
            padx=12,
            pady=10,
            highlightthickness=1,
            highlightbackground="#30363d"
        )
        self.input_text.pack(fill="x", pady=(4, 6))
        self.input_text.focus_set()

        # Action bar under input
        btn_bar = tk.Frame(header_frame, bg="#161b22")
        btn_bar.pack(fill="x")

        self.status_lbl = tk.Label(
            btn_bar,
            text="Paste your prompt, then press Enter to generate.",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#161b22"
        )
        self.status_lbl.pack(side="left")

        self.optimize_btn = tk.Button(
            btn_bar,
            text="⚡ Generate (Enter)",
            bg="#238636",
            fg="white",
            activebackground="#2ea043",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=16,
            pady=4,
            cursor="hand2",
            command=self.start_optimization
        )
        self.optimize_btn.pack(side="right")

        paste_btn = tk.Button(
            btn_bar,
            text="📋 Paste",
            bg="#21262d",
            fg="#c9d1d9",
            activebackground="#30363d",
            font=("Segoe UI", 8),
            relief="flat",
            padx=10,
            pady=4,
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
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.clear_input
        )
        clear_btn.pack(side="right", padx=(0, 6))

        # Results Container (Clean High Precision Card with Token Metrics)
        self.results_frame = tk.Frame(self.root, bg="#0d1117")
        self.results_frame.pack(fill="both", expand=True, padx=14, pady=6)

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

        self.hp_title = tk.Label(
            hp_head,
            text="🎯 Optimized Prompt",
            font=("Segoe UI", 10, "bold"),
            fg="#58a6ff",
            bg="#161b22"
        )
        self.hp_title.pack(side="left")

        self.hp_badge = tk.Label(
            hp_head,
            text="⚡ Token Optimization",
            font=("Segoe UI", 8, "bold"),
            fg="#58a6ff",
            bg="#21262d",
            padx=10,
            pady=2
        )
        self.hp_badge.pack(side="right")

        self.hp_desc = tk.Label(
            self.card_hp,
            text="Strict invariants & execution rules enforced with deterministic token optimization.",
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
            text="📋 Copy Prompt (Enter / Click)",
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

        # In input_text: ENTER directly generates! Shift+Enter creates a new line
        self.input_text.bind("<Return>", self._on_input_enter)
        self.input_text.bind("<Shift-Return>", self._on_input_shift_enter)

        # Outside input_text: ENTER copies the prompt!
        self.root.bind("<Return>", self._handle_window_return)
        self.root.bind("<Control-c>", self._handle_ctrl_c)

    def _on_input_enter(self, event):
        """Directly optimize when Enter is pressed inside the input text box!"""
        self.start_optimization()
        return "break"  # Prevent inserting newline

    def _on_input_shift_enter(self, event):
        """Allow Shift+Enter to insert multiline input if needed."""
        return None

    def _handle_window_return(self, event):
        focused = self.root.focus_get()
        if focused != self.input_text:
            self.copy_high_precision()

    def _handle_ctrl_c(self, event):
        focused = self.root.focus_get()
        if focused != self.input_text:
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
        self._position_window(680, 320)
        self.is_visible = True

        # Win32 force foreground to bypass Windows focus lock
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            hwnd = self.root.winfo_id()
            root_hwnd = user32.GetAncestor(hwnd, 2) or hwnd

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

        # Release hard topmost lock after 500ms
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
        self.status_lbl.config(text="⚡ Optimizing prompt...", fg="#58a6ff")
        self.optimize_btn.config(state="disabled")

        threading.Thread(
            target=self._execute_optimization,
            args=(raw,),
            daemon=True
        ).start()

    def _execute_optimization(self, raw_prompt: str):
        """Call backend with direct force_generate=True (no questions, pure output)."""
        payload = json.dumps({
            "raw_prompt": raw_prompt,
            "backend_type": "mock",
            "force_generate": True
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
                force_generate=True
            )
            data = res.model_dump()
            self.root.after(0, self._render_results, data)
        except Exception as e:
            self.root.after(0, self._handle_error, str(e))

    def _render_results(self, data: Dict[str, Any]):
        self.optimize_btn.config(state="normal")
        self.current_response = data

        hp = data.get("high_precision") or {}
        orig_t = data.get("original_tokens", 0)
        hp_t = hp.get("token_count", 0)
        saved = orig_t - hp_t

        self.hp_text.delete("1.0", tk.END)
        self.hp_text.insert(tk.END, hp.get("prompt_text", ""))

        # Display token optimization metrics
        if orig_t > 0:
            pct = (saved / orig_t) * 100
            if saved > 0:
                self.hp_badge.config(text=f"⚡ {orig_t} ➔ {hp_t} tokens (-{pct:.0f}%)", fg="#2ea043")
                self.hp_desc.config(
                    text=f"Token Optimization: Saved {saved} tokens ({pct:.0f}% reduction). Zero boilerplate."
                )
            else:
                self.hp_badge.config(text=f"⚡ {orig_t} ➔ {hp_t} tokens", fg="#58a6ff")
                self.hp_desc.config(
                    text="Direct imperative prompt with essential technical constraints. Zero boilerplate."
                )
        else:
            self.hp_badge.config(text=f"⚡ {hp_t} tokens", fg="#58a6ff")
            self.hp_desc.config(
                text="Direct imperative prompt with essential technical constraints. Zero boilerplate."
            )

        self.status_lbl.config(
            text=f"✓ Optimized ({hp_t} tokens)! Press Enter or click Copy button.",
            fg="#2ea043"
        )
        self.copy_hp_btn.focus_set()

    def copy_high_precision(self):
        txt = self.hp_text.get("1.0", tk.END).strip()
        if txt:
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            self.card_hp.config(highlightbackground="#2ea043")
            self.status_lbl.config(text="✓ Copied to clipboard! (Esc to hide)", fg="#2ea043")
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
