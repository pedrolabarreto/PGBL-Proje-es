
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador de PGBL", layout="wide")
st.title("Simulador de PGBL")

########################
# 1. Entradas do Usuário
########################

st.sidebar.header("Parâmetros de Entrada")

# 1.1 Renda bruta anual
renda_bruta = st.sidebar.number_input("Renda Bruta Anual (R$)", min_value=0.0, format="%.2f", step=1000.0)

# 1.2 Percentual de aporte (0% a 12%)
perc_pct = st.sidebar.slider("Percentual a aportar (% da renda bruta)", 0.0, 12.0, 12.0, 0.1)

# 1.3 Modalidade de aporte
modo_aporte = st.sidebar.selectbox("Modalidade de aporte", ["Único Anual", "Mensal (dividido por 12)"])

# 1.4 Prazo total de aportes (anos)
anos_aporte = st.sidebar.number_input("Prazo de aportes (anos)", min_value=1, max_value=50, value=20, step=1)

# 1.5 Prazo de resgate (anos)
anos_resgate = st.sidebar.number_input("Prazo de resgate (anos)", min_value=1, max_value=50, value=30, step=1)

# 1.6 Inflação estimada anual (%)
inflacao = st.sidebar.number_input("Inflação estimada anual (%)", min_value=0.0, format="%.2f", value=4.0, step=0.1)

# 1.7 Taxa nominal de retorno (PGBL) anual (%)
taxa_nominal = st.sidebar.number_input("Taxa nominal anual (%) (PGBL)", min_value=0.0, format="%.2f", value=10.0, step=0.1)

# 1.8 Taxa nominal de retorno (%) para fundo de longo prazo
taxa_fundo = st.sidebar.number_input("Taxa nominal anual (%) (Fundo Longo Prazo)", min_value=0.0, format="%.2f", value=10.0, step=0.1)

# 1.9 Tabela regressiva de IR do PGBL (não usada diretamente aqui)
st.sidebar.markdown("#### Tabela Regressiva (PGBL)")
tabela_regressiva = [
    (0, 2, 35.0),
    (2, 4, 30.0),
    (4, 6, 25.0),
    (6, 8, 20.0),
    (8, 10, 15.0),
    (10, 100, 10.0),
]

# 1.10 Modo de resgate pós-acumulação
st.sidebar.markdown("#### Modo de Resgate")
modo_resgate = st.sidebar.selectbox(
    "Selecione modo de resgate:",
    [
        "Renda Vitalícia (mensal)",
        f"Resgate Mensal por {anos_resgate} anos",
        f"Resgates Anuais (parcela em alíquota 10%)"
    ]
)

st.sidebar.markdown("---")
btn_calcular = st.sidebar.button("Calcular Simulação")

########################
# 2. Funções Auxiliares
########################

def aplica_come_cotas_semestre(valor_acumulado, taxa_anual):
    prev = valor_acumulado
    valor_semestral = prev * (1 + taxa_anual) ** 0.5
    ganho = valor_semestral - prev
    ir_sem = ganho * 0.15
    return valor_semestral - ir_sem

def calcula_saque_mensal(total_lp, total_pgbl, taxa_real_lp_mensal, taxa_real_pgbl_mensal, meses):
    def simula(saque):
        saldo_lp = total_lp
        saldo_pgbl = total_pgbl
        for _ in range(meses):
            saldo_lp *= (1 + taxa_real_lp_mensal)
            saldo_pgbl *= (1 + taxa_real_pgbl_mensal)
            if saldo_lp >= saque:
                saldo_lp -= saque
            else:
                rem = saque - saldo_lp
                saldo_lp = 0.0
                saldo_pgbl = max(saldo_pgbl - rem, 0.0)
        return saldo_lp + saldo_pgbl

    low = 0.0
    high = (total_lp + total_pgbl) / meses * 2
    for _ in range(50):
        mid = (low + high) / 2
        rem = simula(mid)
        if rem > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2

########################
# 3. Cálculo principal
########################

if btn_calcular:
    st.header("Resultados da Simulação")

    # Cálculo PGBL nominal
    aporte_anual = renda_bruta * perc_pct / 100.0
    resolucao = 12
    dt = 1 / resolucao

    timeline = np.arange(0, anos_aporte + dt, dt)
    valor_pgbl = np.zeros(len(timeline))
    for idx, t in enumerate(timeline):
        if idx == 0:
            valor_pgbl[idx] = 0.0
        else:
            valor_pgbl[idx] = valor_pgbl[idx - 1] * (1 + taxa_nominal/100.0) ** dt
            if abs(t - round(t)) < 1e-6 and 1 <= round(t) <= anos_aporte:
                valor_pgbl[idx] += aporte_anual

    valor_final_pgbl_nom = valor_pgbl[-1]

    # Cálculo Fundo LP nominal (semestres com come-cotas)
    restit_ano = aporte_anual * 0.275
    semestres = int(anos_aporte * 2)
    valor_lp = 0.0
    lp_sem_vals = [valor_lp]
    for k in range(1, semestres + 1):
        valor_lp = aplica_come_cotas_semestre(valor_lp, taxa_fundo/100.0)
        if k % 2 == 0:
            ano_corrente = k // 2
            if 1 <= ano_corrente <= (anos_aporte - 1):
                valor_lp += restit_ano
        lp_sem_vals.append(valor_lp)

    valor_lp_timeline = np.zeros(len(timeline))
    for idx, t in enumerate(timeline):
        sem_atual = int(np.floor(t * 2))
        valor_lp_timeline[idx] = lp_sem_vals[sem_atual]

    valor_final_lp_nom = valor_lp_timeline[-1]

    # Ajuste para valor real (descontar inflação)
    fator_inflacao = (1 + inflacao/100.0) ** anos_aporte
    valor_pgbl_real = valor_final_pgbl_nom / fator_inflacao
    valor_lp_real = valor_final_lp_nom / fator_inflacao

    # Exibir evolução nominal de PGBL e Fundo LP
    st.subheader("Evolução Nominal ao Longo dos 20 Anos")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(timeline, valor_pgbl, label="PGBL (Bruto)")
    ax.plot(timeline, valor_lp_timeline, label="Fundo LP (Bruto)", linestyle="--")
    ax.set_xlabel("Anos")
    ax.set_ylabel("Valor Acumulado (R$)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Projeção de Resgate
    st.subheader("Projeção de Resgate")

    taxa_real_ano = (1 + taxa_nominal/100.0) / (1 + inflacao/100.0) - 1
    taxa_real_mensal = (1 + taxa_real_ano) ** (1/12) - 1
    taxa_real_lp_ano = (1 + taxa_fundo/100.0) / (1 + inflacao/100.0) - 1
    taxa_real_lp_mensal = (1 + taxa_real_lp_ano) ** (1/12) - 1

    meses_resgate = int(anos_resgate * 12)
    saque_mensal = calcula_saque_mensal(
        total_lp=valor_lp_real,
        total_pgbl=valor_pgbl_real,
        taxa_real_lp_mensal=taxa_real_lp_mensal,
        taxa_real_pgbl_mensal=taxa_real_mensal,
        meses=meses_resgate
    )

    st.write(f"- Valor acumulado no PGBL (nominal): R$ {valor_final_pgbl_nom:,.2f}")
    st.write(f"- Valor acumulado no Fundo LP (nominal): R$ {valor_final_lp_nom:,.2f}")
    st.write(f"- Valor real no PGBL (hoje): R$ {valor_pgbl_real:,.2f}")
    st.write(f"- Valor real no Fundo LP (hoje): R$ {valor_lp_real:,.2f}")
    st.write(f"- Saque mensal constante por {anos_resgate} anos (valor real): R$ {saque_mensal:,.2f}")

