
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
renda_bruta = st.sidebar.number_input(
    "Renda Bruta Anual (R$)",
    min_value=0.0,
    format="%.2f",
    step=1000.0
)

# 1.2 Percentual de aporte (0% a 12%)
perc_pct = st.sidebar.slider(
    "Percentual a aportar (% da renda bruta)",
    0.0, 12.0, 10.0, 0.1
)

# 1.3 Modalidade de aporte
modo_aporte = st.sidebar.selectbox(
    "Modalidade de aporte",
    ["Único Anual", "Mensal (dividido por 12)"]
)

# 1.4 Prazo total de aportes (anos)
anos_aporte = st.sidebar.number_input(
    "Prazo de aportes (anos)",
    min_value=1,
    max_value=50,
    value=20,
    step=1
)

# 1.5 Prazo de resgate (anos) para cálculo de resgate por prazo
anos_resgate = st.sidebar.number_input(
    "Prazo de resgate (anos)",
    min_value=1,
    max_value=50,
    value=30,
    step=1
)

# 1.6 Inflação estimada anual (%)
inflacao = st.sidebar.number_input(
    "Inflação estimada anual (%)",
    min_value=0.0,
    format="%.2f",
    value=4.0,
    step=0.1
)

# 1.7 Taxa nominal de retorno (PGBL) anual (%)
taxa_nominal = st.sidebar.number_input(
    "Taxa nominal anual (%) (PGBL)",
    min_value=0.0,
    format="%.2f",
    value=10.0,
    step=0.1
)

# 1.8 Taxa nominal de retorno (%) para fundo de longo prazo
taxa_fundo = st.sidebar.number_input(
    "Taxa nominal anual (%) (Fundo Longo Prazo)",
    min_value=0.0,
    format="%.2f",
    value=10.0,
    step=0.1
)

# 1.9 Tabela regressiva de IRPF
st.sidebar.markdown("#### Tabela Regressiva (IRPF)")
tabela_irpf = [
    (0.0, 22847.76, 0.0, 0.0),
    (22847.77, 33919.80, 0.075, 1713.58),
    (33919.81, 45012.60, 0.15, 4257.57),
    (45012.61, 55976.16, 0.225, 7633.51),
    (55976.17, 1e12, 0.275, 10432.32),
]

st.sidebar.markdown("---")
btn_calcular = st.sidebar.button("Calcular Simulação")

########################
# 2. Funções Auxiliares
########################

def calcula_irpf_anual(renda):
    imposto = 0.0
    aliquota_ef = 0.0
    for faixa in tabela_irpf:
        base_inf, base_sup, aliquota, deducao = faixa
        if renda >= base_inf and renda <= base_sup:
            imposto = renda * aliquota - deducao
            break
    if imposto < 0:
        imposto = 0.0
    aliquota_ef = (imposto / renda * 100) if renda > 0 else 0.0
    return imposto, aliquota_ef

def aplica_come_cotas_semestre(valor_acumulado, taxa_anual):
    prev = valor_acumulado
    valor_semestral = prev * (1 + taxa_anual) ** 0.5
    ganho = valor_semestral - prev
    ir_sem = ganho * 0.15
    return valor_semestral - ir_sem

def calcula_saque_mensal(total_lp, total_pgbl, taxa_real_lp_mensal, taxa_real_pgbl_mensal, meses):
    def simula(saque):
        saldo_lp   = total_lp
        saldo_pgbl = total_pgbl
        for _ in range(meses):
            saldo_lp   *= (1 + taxa_real_lp_mensal)
            saldo_pgbl *= (1 + taxa_real_pgbl_mensal)
            if saldo_lp >= saque:
                saldo_lp -= saque
            else:
                rem       = saque - saldo_lp
                saldo_lp  = 0.0
                saldo_pgbl = max(saldo_pgbl - rem, 0.0)
        return saldo_lp + saldo_pgbl

    low  = 0.0
    high = (total_lp + total_pgbl) / meses * 2.0
    for _ in range(100):
        mid = (low + high) / 2.0
        rem = simula(mid)
        if rem > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0

########################
# 3. Cálculo principal
########################

if btn_calcular:
    st.header("Resultados da Simulação")

    # --- 3.1 Cálculo do IR sem PGBL ---
    imposto_sem_pgbl, aliq_ef_sem = calcula_irpf_anual(renda_bruta)
    st.write(f"- Alíquota efetiva de IR sem aporte no PGBL: {aliq_ef_sem:.2f}%")
    st.write(f"- IR devido sem PGBL (anual): R$ {imposto_sem_pgbl:,.2f}")

    # --- 3.2 Cálculo do aporte e IR pós-aporte ---
    aporte_anual = renda_bruta * (perc_pct / 100.0)
    restit_anual = aporte_anual * 0.275
    ir_apos_aporte = max(imposto_sem_pgbl - restit_anual, 0.0)
    aliq_ef_com_pgbl = (ir_apos_aporte / renda_bruta) * 100 if renda_bruta > 0 else 0.0
    st.write(f"- IR devido após PGBL (anual): R$ {ir_apos_aporte:,.2f}")
    st.write(f"- Alíquota efetiva de IR após aporte no PGBL: {aliq_ef_com_pgbl:.2f}%")

    total_restit = restit_anual * anos_aporte
    st.write(f"- Imposto total economizado durante {anos_aporte} anos de aporte: R$ {total_restit:,.2f}")

    # --- 3.3 Simulação do PGBL nominal ---
    resolucao = 12
    dt = 1 / resolucao
    timeline = np.arange(0, anos_aporte + dt, dt)
    valor_pgbl = np.zeros(len(timeline))
    for idx, t in enumerate(timeline):
        if idx == 0:
            valor_pgbl[idx] = 0.0
        else:
            valor_pgbl[idx] = valor_pgbl[idx - 1] * (1 + taxa_nominal / 100.0) ** dt
            if abs(t - round(t)) < 1e-8 and 1 <= int(round(t)) <= anos_aporte:
                valor_pgbl[idx] += aporte_anual
    valor_final_pgbl_nom = valor_pgbl[-1]

    # --- 3.4 Simulação do Fundo LP nominal ---
    semestres = anos_aporte * 2
    valor_lp = 0.0
    lp_sem_vals = [valor_lp]
    cap_12 = renda_bruta * 0.12

    for k in range(1, semestres + 1):
        valor_lp = aplica_come_cotas_semestre(valor_lp, taxa_fundo / 100.0)
        if k % 2 == 0:
            ano_corrente = k // 2
            if 1 <= ano_corrente <= anos_aporte - 1:
                restit = aporte_anual * 0.275
                contrib_ano_pgbl = aporte_anual
                if contrib_ano_pgbl < cap_12:
                    gap_pgbl = cap_12 - contrib_ano_pgbl
                    to_pgbl = min(restit, gap_pgbl)
                    to_lp = restit - to_pgbl
                    valor_lp += to_lp
                    idx_target = int(ano_corrente * resolucao)
                    if idx_target < len(valor_pgbl):
                        valor_pgbl[idx_target] += to_pgbl
                else:
                    valor_lp += restit
        lp_sem_vals.append(valor_lp)

    valor_lp_timeline = np.zeros(len(timeline))
    for idx, t in enumerate(timeline):
        sem_atual = int(np.floor(t * 2))
        valor_lp_timeline[idx] = lp_sem_vals[sem_atual]    
    valor_final_lp_nom = valor_lp_timeline[-1]

    # --- Exibição dos Valores BRUTOS Projetados ---
    st.subheader("Valores Brutos Projetados ao Final dos Aportes")
    st.write(f"- Valor acumulado no PGBL (nominal): R$ {valor_final_pgbl_nom:,.2f}")
    st.write(f"- Valor acumulado no Fundo LP (nominal): R$ {valor_final_lp_nom:,.2f}")

    # --- 3.5 Ajuste para “valor real” e gráfico ---
    fator_inflacao = (1 + inflacao / 100.0) ** anos_aporte
    valor_pgbl_real = valor_final_pgbl_nom / fator_inflacao
    valor_lp_real = valor_final_lp_nom / fator_inflacao

    st.subheader("Evolução Nominal ao Longo dos 20 Anos")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(timeline, valor_pgbl, label="PGBL (Bruto)")
    ax.plot(timeline, valor_lp_timeline, label="Fundo LP (Bruto)", linestyle="--")
    ax.set_xlabel("Anos")
    ax.set_ylabel("Valor Acumulado (R$)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # --- 3.6 Projeção de Resgate ---
    st.subheader("Projeção de Resgate")
    taxa_real_ano = (1 + taxa_nominal / 100.0) / (1 + inflacao / 100.0) - 1
    taxa_real_mensal = (1 + taxa_real_ano) ** (1 / 12) - 1
    taxa_real_lp_ano = (1 + taxa_fundo / 100.0) / (1 + inflacao / 100.0) - 1
    taxa_real_lp_mensal = (1 + taxa_real_lp_ano) ** (1 / 12) - 1

    meses_resgate = int(anos_resgate * 12)
    saque_mensal_real = calcula_saque_mensal(
        total_lp=valor_lp_real,
        total_pgbl=valor_pgbl_real,
        taxa_real_lp_mensal=taxa_real_lp_mensal,
        taxa_real_pgbl_mensal=taxa_real_mensal,
        meses=meses_resgate
    )
    st.write(f"- Saque mensal constante por {anos_resgate} anos (valor real): R$ {saque_mensal_real:,.2f}")

    renda_vitalicia = (valor_pgbl_real * taxa_real_ano + valor_lp_real * taxa_real_lp_ano) / 12.0
    st.write(f"- Renda vitalícia perpétua (valor real/mês): R$ {renda_vitalicia:,.2f}")

    # --- 3.7 Benefício Fiscal Real nominal ao final do período ---
    r = taxa_nominal / 100.0
    A = aporte_anual * 0.275  # R$ 6.875
    fv_restits = sum(A * (1 + r) ** k for k in range(0, anos_aporte))
    ir_futuro_principal = (aporte_anual * anos_aporte) * 0.10  # 10% sobre R$500.000
    beneficio_fiscal_real = fv_restits - ir_futuro_principal

    st.subheader("Benefício Fiscal Real (ao final dos aportes)")
    st.write(f"- Valor futuro das restituições reinvestidas: R$ {fv_restits:,.2f}")
    st.write(f"- IR futuro sobre o principal aportado (10% de R$ {aporte_anual * anos_aporte:,.2f}): R$ {ir_futuro_principal:,.2f}")
    st.write(f"- **Benefício Fiscal Real (nominal): R$ {beneficio_fiscal_real:,.2f}**")

    # --- 3.8 Benefício Fiscal Anual (evolução ao longo dos anos) ---
    anos = list(range(1, anos_aporte + 1))
    restit_years = [aporte_anual * 0.275 for _ in anos]
    fv_each = [aporte_anual * 0.275 * (1 + r) ** (anos_aporte - t) for t in anos]
    df_benef_ano = pd.DataFrame({
        "Ano": anos,
        "Restituição (R$)": restit_years,
        "Valor Futuro da Restituição ao Ano 20 (R$)": fv_each
    })
    df_benef_ano["Cumulativo Restituições Nominais (R$)"] = df_benef_ano["Restituição (R$)"].cumsum()
    df_benef_ano["Cumulativo FV Restituições (R$)"] = df_benef_ano["Valor Futuro da Restituição ao Ano 20 (R$)"].cumsum()

    st.subheader("Benefício Fiscal ao Longo dos Anos")
    st.dataframe(df_benef_ano)
