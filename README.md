
# Simulador de PGBL

Este é um simulador de Plano Gerador de Benefício Livre (PGBL) em Python, integrado com Streamlit. Ele calcula:

- Evolução do capital no PGBL e no Fundo de Longo Prazo (LP).
- Ajuste para valor real descontando inflação.
- Projeção de resgate (resgate mensal por prazo e renda vitalícia perpétua).
- Benefício Fiscal Real, considerando:
  - Dedução de até 12% da renda bruta anual no PGBL.
  - Direcionamento das restituições de IR (27,5%) para PGBL até o teto e excedente ao LP.
  - Tributação semestral (come-cotas) no LP.
  - Tributação de 10% sobre o principal no resgate de PGBL.

## Como usar

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
2. Rode o Streamlit:
   ```
   streamlit run app.py
   ```
3. Ajuste os parâmetros na barra lateral (renda, percentual de aporte, prazos, taxas, etc.)

## Estrutura de arquivos

- `app.py`: Lógica completa do simulador.
- `requirements.txt`: Dependências Python.
- `README.md`: Este arquivo de instruções.

## Licença

MIT License.
