
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

# 1.3 Escolher modalidade: anual ou mensal
modo_aporte = st.sidebar.selectbox("Modalidade de aporte", ["Único Anual", "Mensal (dividido por 12)"])

# 1.4 Prazo total de aportes (anos)
anos_aporte = st.sidebar.number_input("Prazo de aportes (anos)", min_value=1, max_value=50, value=10, step=1)

# 1.5 Prazo de resgate (anos)
anos_resgate = st.sidebar.number_input("Prazo de resgate (anos)", min_value=1, max_value=50, value=20, step=1)

# 1.6 Inflação estimada anual (%)
inflacao = st.sidebar.number_input("Inflação estimada anual (%)", min_value=0.0, format="%.2f", value=4.0, step=0.1)

# 1.7 Taxa nominal de retorno (PGBL) anual (%)
taxa_nominal = st.sidebar.number_input("Taxa nominal anual (%) (PGBL)", min_value=0.0, format="%.2f", value=6.0, step=0.1)

# 1.8 Taxa nominal de retorno (%) para fundo de longo prazo (se houver)
taxa_fundo = st.sidebar.number_input("Taxa nominal anual (%) (Fundo Longo Prazo)", min_value=0.0, format="%.2f", value=6.0, step=0.1)

# 1.9 Tabela regressiva de IR do PGBL
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

def calcula_irpf_anual(renda):
    faixas = [
        (0.0, 22847.76, 0.0, 0.0),
        (22847.77, 33919.80, 0.075, 1713.58),
        (33919.81, 45012.60, 0.15, 4257.57),
        (45012.61, 55976.16, 0.225, 7633.51),
        (55976.17, 1e12, 0.275, 10432.32),
    ]
    imposto = 0.0
    for faixa in faixas:
        base_inf, base_sup, aliquota, deducao = faixa
        if renda >= base_inf and renda <= base_sup:
            imposto = renda * aliquota - deducao
            break
    if imposto < 0:
        imposto = 0.0
    aliquota_ef = (imposto / renda * 100) if renda > 0 else 0.0
    return imposto, aliquota_ef

def aplica_come_cotas(valor_acumulado, taxa_anual, periodos=1):
    for _ in range(periodos):
        rend_sem = valor_acumulado * ((1 + taxa_anual) ** 0.5 - 1)
        ir_sem = rend_sem * 0.15
        valor_acumulado = valor_acumulado + rend_sem - ir_sem
    return valor_acumulado

def aliquota_regressiva(anos):
    for faixa in tabela_regressiva:
        a_inf, a_sup, aliq = faixa
        if anos >= a_inf and anos < a_sup:
            return aliq / 100.0
    return tabela_regressiva[-1][2] / 100.0

########################
# 3. Cálculo principal
########################

if btn_calcular:
    st.header("Resultados da Simulação")

    # IRPF sem PGBL
    imposto_sem_pgbl, aliq_ef_sem = calcula_irpf_anual(renda_bruta)
    st.subheader("IRPF sem PGBL")
    st.write(f"- Imposto Anual (sem PGBL): R$ {imposto_sem_pgbl:,.2f}")
    st.write(f"- Alíquota efetiva: {aliq_ef_sem:.2f}%")

    # Valor a aportar no PGBL
    valor_aporte_anual = renda_bruta * (perc_pct / 100.0)
    st.subheader("Valores de Aporte")
    st.write(f"- Valor anual a aportar no PGBL: R$ {valor_aporte_anual:,.2f}")

    # Definir cronograma de aportes
    contribs = []
    if modo_aporte == "Único Anual":
        for i in range(int(anos_aporte)):
            contribs.append((i, valor_aporte_anual))
    else:
        valor_mensal = valor_aporte_anual / 12.0
        total_meses = int(anos_aporte * 12)
        for m in range(total_meses):
            ano_rel = m / 12.0
            contribs.append((ano_rel, valor_mensal))

    df_contribs = pd.DataFrame(contribs, columns=["ano", "aporte"])
    total_investido = df_contribs["aporte"].sum()
    st.write(f"- Total investido ao longo de {anos_aporte} anos: R$ {total_investido:,.2f}")

    # Simular acumulação
    resolucao = 12
    dt = 1 / resolucao

    timeline = np.arange(0, anos_aporte + dt, dt)
    valor_pgbl = np.zeros(len(timeline))
    valor_fundo_lp = np.zeros(len(timeline))

    restit_por_ano = {}
    for ano_int in range(int(anos_aporte)):
        aliquota_marginal = calcula_irpf_anual(renda_bruta)[1] / 100.0
        imposto_economizado = valor_aporte_anual * aliquota_marginal
        restit_por_ano[ano_int + 1] = imposto_economizado

    def preenchimento_pgbl_no_ano(ano):
        soma = 0.0
        for (a, v) in contribs:
            if a < ano:
                soma += v
        return soma

    for idx, t in enumerate(timeline):
        if idx == 0:
            valor_pgbl[idx] = 0.0
            valor_fundo_lp[idx] = 0.0
            continue

        valor_pgbl[idx] = valor_pgbl[idx - 1] * (1 + taxa_nominal / 100.0) ** dt
        valor_fundo_lp[idx] = valor_fundo_lp[idx - 1] * (1 + taxa_fundo / 100.0) ** dt

        mask = np.isclose(df_contribs["ano"], t, atol=1e-6)
        if mask.any():
            soma_aporte = df_contribs.loc[mask, "aporte"].sum()
            valor_pgbl[idx] += soma_aporte

        ano_atual_int = int(np.floor(t))
        if abs(t - ano_atual_int) < 1e-6 and ano_atual_int in restit_por_ano:
            restit = restit_por_ano[ano_atual_int]
            if perc_pct < 12.0:
                total_aportado_ate_hoje = preenchimento_pgbl_no_ano(ano_atual_int)
                capacidade_pgbl = renda_bruta * 0.12
                espaco_pgbl = max(capacidade_pgbl - total_aportado_ate_hoje, 0.0)
                if restit <= espaco_pgbl:
                    valor_pgbl[idx] += restit
                else:
                    valor_pgbl[idx] += espaco_pgbl
                    sobra = restit - espaco_pgbl
                    valor_fundo_lp[idx] += sobra
            else:
                valor_fundo_lp[idx] += restit

        mes_rel = (t * 12) % 12
        if abs(mes_rel - 4) < 1e-3 or abs(mes_rel - 10) < 1e-3:
            valor_pgbl[idx] = aplica_come_cotas(valor_pgbl[idx], taxa_nominal / 100.0, periodos=1)
            valor_fundo_lp[idx] = aplica_come_cotas(valor_fundo_lp[idx], taxa_fundo / 100.0, periodos=1)

    df_evol = pd.DataFrame({
        "Ano": timeline,
        "PGBL_Bruto": valor_pgbl,
        "Fundo_LP_Bruto": valor_fundo_lp
    })

    st.subheader("Evolução Bruta ao Longo do Tempo")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df_evol["Ano"], df_evol["PGBL_Bruto"], label="PGBL (Bruto)")
    ax.plot(df_evol["Ano"], df_evol["Fundo_LP_Bruto"], label="Fundo LP (Bruto)")
    ax.set_xlabel("Anos")
    ax.set_ylabel("Valor Acumulado (R$)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    valor_final_pgbl = valor_pgbl[-1]

    st.subheader("Projeção de Resgate")
    if modo_resgate == "Renda Vitalícia (mensal)":
        valor_real_pgbl = valor_final_pgbl / ((1 + inflacao / 100.0) ** anos_aporte)
        taxa_real = ((1 + taxa_nominal / 100.0) / (1 + inflacao / 100.0)) - 1
        renda_mensal = valor_real_pgbl * taxa_real / 12.0
        st.write(f"- Valor acumulado nominal no PGBL: R$ {valor_final_pgbl:,.2f}")
        st.write(f"- Valor real (hoje) no PGBL: R$ {valor_real_pgbl:,.2f}")
        st.write(f"- Renda vitalícia mensal estimada (em R$ de hoje): R$ {renda_mensal:,.2f}")
    elif modo_resgate.startswith("Resgate Mensal"):
        prazo_meses = anos_resgate * 12
        taxa_real = ((1 + taxa_nominal / 100.0) / (1 + inflacao / 100.0)) - 1
        valor_real_pgbl = valor_final_pgbl / ((1 + inflacao / 100.0) ** anos_aporte)
        if taxa_real == 0:
            saque_mensal = valor_real_pgbl / prazo_meses
        else:
            j = (1 + taxa_real) ** (1 / 12) - 1
            saque_mensal = valor_real_pgbl * j / (1 - (1 + j) ** (-prazo_meses))
        st.write(f"- Valor real acumulado no PGBL (hoje): R$ {valor_real_pgbl:,.2f}")
        st.write(f"- Saque mensal constante por {anos_resgate} anos: R$ {saque_mensal:,.2f}")
    else:
        valor_real_pgbl = valor_final_pgbl / ((1 + inflacao / 100.0) ** anos_aporte)
        saque_anual = valor_real_pgbl / anos_resgate
        st.write(f"- Valor real acumulado no PGBL (hoje): R$ {valor_real_pgbl:,.2f}")
        st.write(f"- Saque anual por {anos_resgate} anos: R$ {saque_anual:,.2f}")
        st.markdown(
            "_Observação: dependendo da ordem cronológica dos aportes, parte do capital resgatado poderá ter tempo de permanência menor que 10 anos, gerando alíquotas superiores a 10% no IR regressivo._"
        )

    imposto_economizado_total = sum(restit_por_ano.values())
    ir_com_pgbl = imposto_sem_pgbl - imposto_economizado_total
    aliq_ef_com_pgbl = (ir_com_pgbl / renda_bruta * 100) if renda_bruta > 0 else 0.0

    st.subheader("Economia Fiscal")
    st.write(f"- Imposto economizado ao longo do período: R$ {imposto_economizado_total:,.2f}")
    st.write(f"- IR devido após restituições (anual): R$ {ir_com_pgbl:,.2f}")
    st.write(f"- Alíquota efetiva após PGBL: {aliq_ef_com_pgbl:.2f}%")

    if st.checkbox("Mostrar tabela detalhada de evolução"):
        df_exibir = df_evol.copy()
        df_exibir["PGBL_Bruto"] = df_exibir["PGBL_Bruto"].round(2)
        df_exibir["Fundo_LP_Bruto"] = df_exibir["Fundo_LP_Bruto"].round(2)
        st.dataframe(df_exibir)
