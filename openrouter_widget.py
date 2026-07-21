import json
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import requests
import threading
import time

CONFIG_PATH = Path(__file__).with_name("models.json")
ALL_LABEL = "Todos"

DEFAULT_CONFIG = {
    "interval": 60,
    "models": {
        "meta-llama/llama-3.3-70b-instruct": {
            "nickname": "Llama 3.3 70B",
            "provider": "Meta",
            "base_in": 0.0000006,
            "base_out": 0.0000008,
        },
        "anthropic/claude-3.5-sonnet": {
            "nickname": "Claude 3.5 Sonnet",
            "provider": "Anthropic",
            "base_in": 0.000003,
            "base_out": 0.000015,
        },
        "deepseek/deepseek-chat": {
            "nickname": "DeepSeek V3",
            "provider": "DeepSeek",
            "base_in": 0.00000014,
            "base_out": 0.00000028,
        },
    },
}


def load_config(path: Path) -> dict:
    if not path.exists():
        try:
            path.write_text(
                json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            return DEFAULT_CONFIG
        except OSError as e:
            print(f"[models.json] Não foi possível criar ({e}). Usando defaults em memória.")
            return DEFAULT_CONFIG

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "models" not in data or not isinstance(data["models"], dict):
            raise ValueError("'models' deve ser um objeto {id: {nickname, provider, base_in, base_out}}")
        data.setdefault("interval", 60)
        if not isinstance(data["interval"], int) or data["interval"] < 1:
            data["interval"] = 60
        for model_id, cfg in data["models"].items():
            for required in ("nickname", "provider", "base_in", "base_out"):
                if required not in cfg:
                    raise ValueError(f"Modelo {model_id!r} sem campo {required!r}")
            cfg["base_in"] = float(cfg["base_in"])
            cfg["base_out"] = float(cfg["base_out"])
        return data
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[models.json] Erro: {e}. Usando defaults em memória.")
        return DEFAULT_CONFIG


class OpenRouterWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenRouter Monitor")

        self.config_path = CONFIG_PATH
        self.config = load_config(self.config_path)
        self.models = self.config["models"]
        self.interval = self.config["interval"]

        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("380x290+50+50")
        self.root.configure(bg="#1e1e2e")

        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)

        self._setup_combobox_style()

        self.header = tk.Frame(root, bg="#313244")
        self.header.pack(fill=tk.X)

        self.title_lbl = tk.Label(
            self.header,
            text="📊 OPENROUTER MONITOR",
            bg="#313244",
            fg="#cdd6f4",
            font=("Helvetica", 10, "bold"),
            pady=5,
            padx=10,
        )
        self.title_lbl.pack(side=tk.LEFT)

        self.providers = self._collect_providers()
        self.provider_var = tk.StringVar(value=ALL_LABEL)
        self.filter_combo = ttk.Combobox(
            self.header,
            textvariable=self.provider_var,
            values=[ALL_LABEL] + self.providers,
            state="readonly",
            width=12,
            font=("Helvetica", 9),
        )
        self.filter_combo.pack(side=tk.RIGHT, padx=10, pady=4)
        self.filter_combo.bind("<<ComboboxSelected>>", self._on_filter_change)

        self.list_frame = tk.Frame(root, bg="#1e1e2e", padx=10, pady=10)
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        self.footer = tk.Frame(root, bg="#11111b", pady=4, padx=10)
        self.footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            self.footer,
            text="Iniciando...",
            bg="#11111b",
            fg="#a6adc8",
            font=("Helvetica", 8),
        )
        self.status_label.pack(side=tk.LEFT)

        self.close_btn = tk.Button(
            self.footer,
            text="✕",
            bg="#11111b",
            fg="#f38ba8",
            bd=0,
            activebackground="#f38ba8",
            activeforeground="#11111b",
            font=("Helvetica", 8, "bold"),
            command=self.root.quit,
        )
        self.close_btn.pack(side=tk.RIGHT)

        self.model_rows = {}
        self.setup_ui_rows()

        if not self.config_path.exists():
            self.status_label.config(text="models.json criado (edite e reinicie)")
        else:
            self.status_label.config(
                text=f"{len(self.models)} modelos carregados de models.json"
            )

        self.running = True
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread.start()

    def _setup_combobox_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "TCombobox",
            fieldbackground="#1e1e2e",
            background="#313244",
            foreground="#cdd6f4",
            arrowcolor="#cdd6f4",
            bordercolor="#45475a",
        )
        self.root.option_add("*TCombobox*Listbox*Background", "#1e1e2e")
        self.root.option_add("*TCombobox*Listbox*Foreground", "#cdd6f4")
        self.root.option_add("*TCombobox*Listbox*selectBackground", "#45475a")
        self.root.option_add("*TCombobox*Listbox*selectForeground", "#cdd6f4")
        self.root.option_add("*TCombobox*Listbox*font", ("Helvetica", 9))

    def _collect_providers(self):
        return sorted({c["provider"] for c in self.models.values()})

    def _on_filter_change(self, _event=None):
        sel = self.provider_var.get()
        for info in self.model_rows.values():
            if sel == ALL_LABEL or info["provider"] == sel:
                info["row"].pack(fill=tk.X)
            else:
                info["row"].pack_forget()

    def setup_ui_rows(self):
        for model_id, config in self.models.items():
            row = tk.Frame(self.list_frame, bg="#1e1e2e", pady=5)
            row.pack(fill=tk.X)

            name_lbl = tk.Label(
                row,
                text=f"{config['nickname']}  ({config['provider']})",
                bg="#1e1e2e",
                fg="#cdd6f4",
                font=("Helvetica", 9, "bold"),
                anchor="w",
            )
            name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            price_lbl = tk.Label(
                row,
                text="Buscando...",
                bg="#1e1e2e",
                fg="#bac2de",
                font=("Helvetica", 9),
                anchor="e",
            )
            price_lbl.pack(side=tk.RIGHT)

            self.model_rows[model_id] = {
                "row": row,
                "price": price_lbl,
                "provider": config["provider"],
            }

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def update_loop(self):
        url = "https://openrouter.ai/api/v1/models"

        while self.running:
            try:
                self.root.after(0, self.set_status, "Atualizando dados...")
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    api_prices = {m["id"]: m.get("pricing", {}) for m in data}
                    self.root.after(0, self.refresh_ui, api_prices)
                else:
                    self.root.after(0, self.set_status, f"Erro API: {response.status_code}")
            except Exception:
                self.root.after(0, self.set_status, "Erro de conexão")

            time.sleep(self.interval)

    def refresh_ui(self, api_data):
        agora = time.strftime("%H:%M:%S")
        self.status_label.config(text=f"Última checagem: {agora}")

        for model_id, config in self.models.items():
            if model_id in api_data and model_id in self.model_rows:
                pricing = api_data[model_id]
                info = self.model_rows[model_id]
                price_lbl = info["price"]

                curr_in_m = float(pricing.get("prompt", 0)) * 1_000_000
                curr_out_m = float(pricing.get("completion", 0)) * 1_000_000

                base_in_m = config["base_in"] * 1_000_000
                base_out_m = config["base_out"] * 1_000_000

                discount_in = 1 - (curr_in_m / base_in_m) if base_in_m > 0 else 0
                discount_out = 1 - (curr_out_m / base_out_m) if base_out_m > 0 else 0
                max_discount = max(discount_in, discount_out)

                texto_preco = f"In: ${curr_in_m:.2f} | Out: ${curr_out_m:.2f}"

                if max_discount >= 0.15:
                    price_lbl.config(
                        text=f"🔥 {texto_preco} (-{max_discount*100:.0f}%)",
                        fg="#a6e3a1",
                    )
                else:
                    price_lbl.config(text=texto_preco, fg="#bac2de")

    def set_status(self, text):
        self.status_label.config(text=text)


if __name__ == "__main__":
    root = tk.Tk()
    app = OpenRouterWidget(root)
    root.mainloop()
