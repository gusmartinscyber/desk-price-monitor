# Desk Price Monitor

Widget de desktop minimalista para Ubuntu que monitora os preços por token de modelos de IA servidos pelo [OpenRouter](https://openrouter.ai), direto na sua área de trabalho — sem notificações no celular, sem abrir dashboard no navegador.

A janela flutua sobre as outras aplicações, é arrastável e acende em verde (`🔥`) quando algum modelo monitorado entra em promoção (queda ≥ 15% em relação ao preço-base configurado).

> Por que Tkinter? Já vem com Python no Ubuntu. Zero build, zero runtime externo além de `requests`.

---

## Preview

```
┌────────────────────────────────────────────────┐
│  📊 OPENROUTER MONITOR          [Todos   ▾]   │
├────────────────────────────────────────────────┤
│  Llama 3.3 70B  (Meta)      In: $0.59|Out:… │
│  Claude 3.5 Sonnet (Anthropic) In: $3.00|Out:… │
│  DeepSeek V3  (DeepSeek)     In: $0.14|Out:… │
├────────────────────────────────────────────────┤
│  Última checagem: 14:32:01                  ✕ │
└────────────────────────────────────────────────┘
```

O dropdown no topo direito filtra por provedor — escolha `Meta`, `Anthropic`, `DeepSeek` (ou qualquer outro que você adicionar em `MODELS_TO_WATCH`) para ver só os modelos daquele provedor. `Todos` mostra tudo.

Paleta inspirada em [Catppuccin Mocha](https://github.com/catppuccin/catppuccin).

---

## Pré-requisitos

Ubuntu 20.04+ com Python 3.8+.

```bash
sudo apt update
sudo apt install python3-tk
pip install requests
```

Sem `.env`, sem chave de API — o endpoint `https://openrouter.ai/api/v1/models` é público.

---

## Instalação

```bash
git clone https://github.com/gusmartinscyber/desk-price-monitor.git
cd desk-price-monitor
pip install -r requirements.txt
```

### Ambiente virtual (opcional)

Para isolar a dependência `requests` do Python do sistema, use um venv:

```bash
cd desk-price-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 openrouter_widget.py
deactivate   # quando terminar
```

O `.venv/` já está no `.gitignore`, então não vaza para o commit.

---

## Como executar

```bash
python3 openrouter_widget.py
```

A janela aparece no canto superior esquerdo. Use o mouse para arrastá-la para qualquer canto da tela.

### Controles

| Ação | Como |
|------|------|
| Arrastar a janela | Clique em qualquer parte escura do widget e segure |
| Filtrar por provedor | Dropdown no canto superior direito |
| Fechar | Botão `✕` no canto inferior direito |
| Sair pelo teclado | `Ctrl+C` no terminal que iniciou o processo |

---

## Como funciona

```
[OpenRouter /api/v1/models]  --HTTP-->  thread em background
                                            |
                                            v
                                    self.root.after(0, ...)  --thread-safe-->
                                            |
                                            v
                                    Tkinter UI atualiza preço/cor
                                            |
                                            v
                                    sleep 60s -> repete
```

- A chamada HTTP roda em uma **thread daemon** para não travar a UI.
- O callback de atualização é sempre despachado via `root.after(0, ...)` para rodar na thread do Tk (única thread onde widgets podem ser modificados).
- A cada 60 s, o widget releituras os preços de `prompt` e `completion` por 1M de tokens e compara com os preços-base declarados em `MODELS_TO_WATCH`.

### Regra de promoção

```python
if max(preco_base - preco_atual) / preco_base >= 0.15:
    icone = "🔥"
    cor   = "#a6e3a1"  # verde Catppuccin
else:
    icone = ""
    cor   = "#bac2de"  # cinza padrão
```

---

## Configuração

A lista de modelos vive em **`models.json`** (mesma pasta do script). O arquivo é **criado automaticamente no primeiro run** com 3 modelos de exemplo, e fica **fora do git** (`.gitignore`) — assim suas edições não são sobrescritas em `git pull`.

Para adicionar/remover/editar modelos, basta abrir o `models.json` num editor, salvar, e reiniciar o widget:

```json
{
  "interval": 60,
  "models": {
    "meta-llama/llama-3.3-70b-instruct": {
      "nickname": "Llama 3.3 70B",
      "provider": "Meta",
      "base_in":  0.0000006,
      "base_out": 0.0000008
    },
    "anthropic/claude-3.5-sonnet": {
      "nickname": "Claude 3.5 Sonnet",
      "provider": "Anthropic",
      "base_in":  0.000003,
      "base_out": 0.000015
    },
    "deepseek/deepseek-chat": {
      "nickname": "DeepSeek V3",
      "provider": "DeepSeek",
      "base_in":  0.00000014,
      "base_out": 0.00000028
    }
  }
}
```

| Campo | Significado |
|-------|-------------|
| `interval` | Segundos entre cada checagem da API (mínimo 1) |
| `models` | Dict `{id_openrouter: {nickname, provider, base_in, base_out}}` |
| `nickname` | Apelido curto exibido no widget |
| `provider` | Nome do provedor — usado no dropdown de filtro |
| `base_in` / `base_out` | Preço-base (USD/token) para detectar promoções |

**Validação:** se o `models.json` estiver malformado ou faltar campos obrigatórios, o widget loga o erro no terminal e usa os defaults em memória (sem sobrescrever o seu arquivo).

A lista completa de IDs está em <https://openrouter.ai/models>.

---

## Stack

- **Python 3.8+** — runtime
- **Tkinter** — UI (stdlib)
- **requests** — cliente HTTP

## Estrutura

```
desk-price-monitor/
├── LICENSE              # MIT
├── README.md            # este arquivo
├── requirements.txt     # requests
├── .gitignore
├── openrouter_widget.py # todo o código (~210 linhas, single-file)
└── models.json          # auto-criado no 1º run, gitignored (suas edições ficam)
```

## Licença

MIT — veja [LICENSE](LICENSE).
