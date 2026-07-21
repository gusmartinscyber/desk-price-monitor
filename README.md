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

Edite o dicionário `MODELS_TO_WATCH` no topo de `openrouter_widget.py`:

```python
MODELS_TO_WATCH = {
    "id-do-modelo-no-openrouter": {
        "nickname":  "Nome curto para o widget",
        "provider":  "NomeDoProvedor",   # usado no filtro do dropdown
        "base_in":   0.0000006,          # USD por token (input)
        "base_out":  0.0000008,          # USD por token (output)
    },
    # adicione mais aqui
}
```

O dropdown no header é populado automaticamente com os provedores únicos encontrados em `MODELS_TO_WATCH`, mais a opção `Todos` (default = mostra tudo).

A lista completa de IDs está em <https://openrouter.ai/models>.

Para ajustar o intervalo de checagem, altere:

```python
INTERVALO_ATUALIZACAO = 60  # segundos
```

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
└── openrouter_widget.py # todo o código (~140 linhas, single-file)
```

## Licença

MIT — veja [LICENSE](LICENSE).
