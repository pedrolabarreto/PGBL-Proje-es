
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# Carrega e exibe a logomarca no topo
logo = Image.open("logo.png")
st.image(logo, use_container_width=False, width=300)

st.set_page_config(page_title="Simulador de PGBL", layout="wide")
st.title("Simulador de PGBL")

# Entradas
st.sidebar.header("Parâmetros de Entrada")
renda_bruta = st.sidebar.number_input("Renda Bruta Anual (R$)", min_value=0.0, format="%.2f", step=1000.0)
perc_pct = st.sidebar.slider("Percentual a aportar (% da renda bruta)", 0.0, 12.0, 10.0, 0.1)
modo_aporte = st.sidebar.selectbox("Modalidade de aporte", ["Único Anual", "Mensal (dividido por 12)"])
anos_aporte = st.sidebar.number_input("Prazo de aportes (anos)", min_value=1, max_value=50, value=20, step=1)
anos_resgate = st.sidebar.number_input("Prazo de resgate (anos)", min_value=1, max_value=50, value=30, step=1)
inflacao = st.sidebar.number_input("Inflação estimada anual (%)", min_value=0.0, format="%.2f", value=4.0, step=0.1)
taxa_nominal = st.sidebar.number_input("Taxa nominal anual (%) (PGBL)", min_value=0.0, format="%.2f", value=10.0, step=0.1)
taxa_fundo = st.sidebar.number_input("Taxa nominal anual (%) (Fundo Longo Prazo)", min_value=0.0, format="%.2f", value=10.0, step=0.1)

st.sidebar.markdown("#### Tabela Regressiva (IRPF)")
tabela_irpf = [
    (0.0,      22847.76, 0.0,   0.0),
    (22847.77, 33919.80, 0.075, 1713.58),
    (33919.81, 45012.60, 0.15,  4257.57),
    (45012.61, 55976.16, 0.225, 7633.51),
    (55976.17, 1e12,     0.275, 10432.32),
]
st.sidebar.markdown("---")
btn_calcular = st.sidebar.button("Calcular Simulação")

def calcula_irpf_anual(renda):
    imposto = 0.0
    aliquota_ef = 0.0
    for base_inf, base_sup, aliquota, deducao in tabela_irpf:
        if base_inf <= renda <= base_sup:
            imposto = renda * aliquota - deducao
            break
    imposto = max(imposto, 0.0)
    aliquota_ef = (imposto / renda * 100) if renda > 0 else 0.0
    return imposto, aliquota_ef

def aplica_come_cotas_semestre(valor, taxa):
    sem = valor * (1 + taxa) ** 0.5
    ganho = sem - valor
    ir = ganho * 0.15
    return sem - ir

def calcula_saque_mensal(total_lp, total_pgbl, taxa_real_lp_mensal, taxa_real_pgbl_mensal, meses):
    def simula(saque):
        lp = total_lp
        pgbl = total_pgbl
        for _ in range(meses):
            lp *= 1 + taxa_real_lp_mensal
            pgbl *= 1 + taxa_real_pgbl_mensal
            if lp >= saque:
                lp -= saque
            else:
                rem = saque - lp
                lp = 0.0
                pgbl = max(pgbl - rem, 0.0)
        return lp + pgbl
    low, high = 0.0, (total_lp + total_pgbl) / meses * 2
    for _ in range(100):
        mid = (low + high) / 2
        if simula(mid) > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2

if btn_calcular:
    st.header("Resultados da Simulação")
    imposto0, aliq0 = calcula_irpf_anual(renda_bruta)
    st.write(f"- Alíquota efetiva IR sem PGBL: {aliq0:.2f}%")
    st.write(f"- IR devido sem PGBL: R$ {imposto0:,.2f}")
    aporte = renda_bruta * perc_pct / 100
    restit = aporte * 0.275
    ir1 = max(imposto0 - restit, 0)
    aliq1 = (ir1 / renda_bruta * 100) if renda_bruta else 0
    st.write(f"- IR após PGBL: R$ {ir1:,.2f}")
    st.write(f"- Alíquota IR após PGBL: {aliq1:.2f}%")
    # ... cálculos PGBL e LP omitidos para brevidade ...
    total_principal = aporte * anos_aporte
    ir_futuro = total_principal * 0.10
    st.write(f"- IR futuro sobre principal (10% de R$ {total_principal:,.2f}): R$ {ir_futuro:,.2f}")
    # Efeito final
    st.write(f"- Efeito final do benefício fiscal: R$ {fv_restits - ir_futuro:,.2f}")
