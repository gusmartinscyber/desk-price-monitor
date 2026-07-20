import tkinter as tk
import requests
import threading
import time

MODELS_TO_WATCH = {
    "meta-llama/llama-3.3-70b-instruct": {
        "nickname": "Llama 3.3 70B",
        "base_in": 0.0000006,
        "base_out": 0.0000008,
    },
    "anthropic/claude-3.5-sonnet": {
        "nickname": "Claude 3.5 Sonnet",
        "base_in": 0.000003,
        "base_out": 0.000015,
    },
    "deepseek/deepseek-chat": {
        "nickname": "DeepSeek V3",
        "base_in": 0.00000014,
        "base_out": 0.00000028,
    },
}

INTERVALO_ATUALIZACAO = 60


class OpenRouterWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenRouter Monitor")

        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("380x250+50+50")
        self.root.configure(bg="#1e1e2e")

        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)

        self.header = tk.Label(
            root,
            text="📊 OPENROUTER MONITOR",
            bg="#313244",
            fg="#cdd6f4",
            font=("Helvetica", 10, "bold"),
            pady=5,
        )
        self.header.pack(fill=tk.X)

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

        self.model_labels = {}
        self.setup_ui_rows()

        self.running = True
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread.start()

    def setup_ui_rows(self):
        for model_id, config in MODELS_TO_WATCH.items():
            row = tk.Frame(self.list_frame, bg="#1e1e2e", pady=5)
            row.pack(fill=tk.X)

            name_lbl = tk.Label(
                row,
                text=config["nickname"],
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

            self.model_labels[model_id] = price_lbl

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

            time.sleep(INTERVALO_ATUALIZACAO)

    def refresh_ui(self, api_data):
        agora = time.strftime("%H:%M:%S")
        self.status_label.config(text=f"Última checagem: {agora}")

        for model_id, config in MODELS_TO_WATCH.items():
            if model_id in api_data and model_id in self.model_labels:
                pricing = api_data[model_id]

                curr_in_m = float(pricing.get("prompt", 0)) * 1_000_000
                curr_out_m = float(pricing.get("completion", 0)) * 1_000_000

                base_in_m = config["base_in"] * 1_000_000
                base_out_m = config["base_out"] * 1_000_000

                discount_in = 1 - (curr_in_m / base_in_m) if base_in_m > 0 else 0
                discount_out = 1 - (curr_out_m / base_out_m) if base_out_m > 0 else 0
                max_discount = max(discount_in, discount_out)

                texto_preco = f"In: ${curr_in_m:.2f} | Out: ${curr_out_m:.2f}"

                if max_discount >= 0.15:
                    self.model_labels[model_id].config(
                        text=f"🔥 {texto_preco} (-{max_discount*100:.0f}%)",
                        fg="#a6e3a1",
                    )
                else:
                    self.model_labels[model_id].config(
                        text=texto_preco,
                        fg="#bac2de",
                    )

    def set_status(self, text):
        self.status_label.config(text=text)


if __name__ == "__main__":
    root = tk.Tk()
    app = OpenRouterWidget(root)
    root.mainloop()
