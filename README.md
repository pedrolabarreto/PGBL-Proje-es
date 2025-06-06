
# Simulador de PGBL - Corrigido v12

Este simulador ajusta o cálculo do Valor Futuro das Restituições para aplicar as mesmas regras de capitalização e tributação dos ativos:
- Parte da restituição que cabe no PGBL cresce a 10% a.a.
- Parte excedente ao PGBL vai para o Fundo LP e sofre come-cotas semestrais (15% sobre o ganho semestral).

## Como usar

1. pip install -r requirements.txt
2. streamlit run app.py
