# Simulador Financeiro de PGBL

Este projeto é um aplicativo em Streamlit para:
- Calcular Imposto de Renda com e sem aportes em PGBL.
- Projetar evolução de patrimônio (PGBL e “outros investimentos”).
- Simular saques perpétuos (nominal e real, considerando inflação).
- Tributação “FIFO” lote a lote no PGBL.

## Instalação

```bash
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
cd SEU_REPOSITORIO
pip install -r requirements.txt
streamlit run app.py
```

## Como usar

1. Preencha no painel:
   - **Renda Bruta Anual**  
   - **Percentual de aporte em PGBL (0–12%)**  
   - **Taxa de retorno esperada**  
   - **Prazo de projeção (anos)**  
   - **Frequência de aporte** (Anual ou Mensal)  
   - **Para renda perpétua real**: informe a inflação anual (em %)  
2. Veja no painel:
   - **IR sem PGBL**, **IR com PGBL a 12%**, **IR com PGBL ao % escolhido**  
   - **Evolução ano a ano** de saldos (PGBL vs Outros) e **Economia de IR anual**  
   - **Saques anuais FIFO** distribuídos ao longo de M anos (ajustados conforme instruções)  
   - **Economia de IR Acumulada** (bruta e líquida ao final)  
   - **Renda Perpétua Real** (em valores de hoje)

## Arquivos

- `app.py` – Código completo do simulador em Streamlit.  
- `requirements.txt` – Lista de dependências: Streamlit, Pandas, NumPy.  
- `README.md` – Este arquivo de instruções e descrição.

## Licença

Este projeto está sob a licença MIT. Sinta‐se livre para utilizar e modificar.
