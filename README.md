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
   - Renda Bruta Anual  
   - Percentual de aporte em PGBL (0–12%)  
   - Taxa de retorno esperada  
   - Prazo de projeção (anos)  
   - Inflação anual (para renda real)  
   - Escolha frequência de aporte (Anual/Mensal)  
2. Veja no painel os resultados de IR, projeções e renda perpétua (nominal e real).

## Arquivos

- `app.py` – Código completo do simulador em Streamlit.  
- `requirements.txt` – Dependências: Streamlit, Pandas, NumPy.  
- `README.md` – Este arquivo de descrição e instruções.

## Licença

Este projeto está sob a licença MIT. Sinta‐se livre para utilizar e modificar.
