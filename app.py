
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
taxa_fundo = st.sidebar.number_input("Taxa nominal anual (%) (Fundo Longo Prazo)", min_value=0.0, format="%.2f", value=10.0, step=0.1)

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

# Aplica come-cotas semestral: desconta 15% de IR sobre rendimento semestral
def aplica_come_cotas_semestre(valor_acumulado, taxa_anual):
    prev = valor_acumulado
    valor_semestral = valor_acumulado * (1 + taxa_anual) ** 0.5
    ganho = valor_semestral - prev
    ir_sem = ganho * 0.15
    return valor_semestral - ir_sem

def calcula_saque_mensal(total_lp, total_pgbl, taxa_real_lp, taxa_real_pgbl, meses):
    # Usa método de busca binária para encontrar saque mensal constante que zera saldo após "meses"
    def simula(saque):
        saldo_lp = total_lp
        saldo_pgbl = total_pgbl
        for i in range(meses):
            # cresce real
            saldo_lp = saldo_lp * (1 + taxa_real_lp)
            saldo_pgbl = saldo_pgbl * (1 + taxa_real_pgbl)
            # saque
            if saldo_lp >= saque:
                saldo_lp -= saque
            else:
                rem = saque - saldo_lp
                saldo_lp = 0.0
                saldo_pgbl = max(saldo_pgbl - rem, 0.0)
        return saldo_lp + saldo_pgbl

    # Buscar saque entre 0 e total/meses * 2
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

    # IRPF sem PGBL
    imposto_sem_pgbl, aliq_ef_sem = calcula_irpf_anual(renda_bruta)
    st.subheader("IRPF sem PGBL")
    st.write(f"- Imposto Anual (sem PGBL): R$ {imposto_sem_pgbl:,.2f}")
    st.write(f"- Alíquota efetiva: {aliq_ef_sem:.2f}%")

    # Valor a aportar no PGBL
    valor_aporte_anual = renda_bruta * (perc_pct / 100.0)
    st.subheader("Valores de Aporte")
    st.write(f"- Valor anual a aportar no PGBL: R$ {valor_aporte_anual:,.2f}")

    # Definir cronograma de aportes (apenas para PGBL)
    contribs = []
    if modo_aporte == "Único Anual":
        for i in range(1, int(anos_aporte) + 1):
            contribs.append((i, valor_aporte_anual))
    else:
        valor_mensal = valor_aporte_anual / 12.0
        total_meses = int(anos_aporte * 12)
        for m in range(1, total_meses + 1):
            contribs.append((m / 12.0, valor_mensal))

    df_contribs = pd.DataFrame(contribs, columns=["ano", "aporte"])
    total_investido = df_contribs["aporte"].sum()
    st.write(f"- Total investido ao longo de {anos_aporte} anos: R$ {total_investido:,.2f}")

    # Simular PGBL mensalmente
    resolucao = 12
    dt = 1 / resolucao

    timeline = np.arange(0, anos_aporte + dt, dt)
    valor_pgbl = np.zeros(len(timeline))

    for idx, t in enumerate(timeline):
        if idx == 0:
            valor_pgbl[idx] = 0.0
            continue
        valor_pgbl[idx] = valor_pgbl[idx - 1] * (1 + taxa_nominal / 100.0) ** dt
        # aportes no PGBL
        mask = np.isclose(df_contribs["ano"], t, atol=1e-6)
        if mask.any():
            valor_pgbl[idx] += df_contribs.loc[mask, "aporte"].sum()

    valor_final_pgbl = valor_pgbl[-1]

    # Simular Fundo LP em semestres
    restit_ano = valor_aporte_anual * 0.275
    semestres = int(anos_aporte * 2)
    valor_lp = 0.0
    lp_sem_vals = [valor_lp]
    for k in range(1, semestres + 1):
        valor_lp = aplica_come_cotas_semestre(valor_lp, taxa_fundo / 100.0)
        if k % 2 == 0:
            ano_corrente = k // 2
            if 1 <= ano_corrente <= (anos_aporte - 1):
                valor_lp += restit_ano
        lp_sem_vals.append(valor_lp)

    # Criar vetor de valor_lp no mesmo timeline (forward-fill semestral)
    valor_lp_timeline = np.zeros(len(timeline))
    for idx, t in enumerate(timeline):
        sem_atual = int(np.floor(t * 2))
        valor_lp_timeline[idx] = lp_sem_vals[sem_atual]

    valor_final_fundo = valor_lp_timeline[-1]

    # Exibição do gráfico com PGBL e Fundo LP
    st.subheader("Evolução Bruta ao Longo do Tempo")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(timeline, valor_pgbl, label="PGBL (Bruto)")
    ax.plot(timeline, valor_lp_timeline, label="Fundo LP (Bruto)", linestyle="--")
    ax.set_xlabel("Anos")
    ax.set_ylabel("Valor Acumulado (R$)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    st.subheader("Projeção de Resgate")

    # PGBL
    st.write(f"- Valor acumulado no PGBL (bruto): R$ {valor_final_pgbl:,.2f}")
    valor_real_pgbl = valor_final_pgbl / ((1 + inflacao / 100.0) ** anos_aporte)

    # Fundo LP
    valor_real_fundo = valor_final_fundo / ((1 + inflacao / 100.0) ** anos_aporte)

    # Mostrar valores brutos e reais
    st.write(f"- Valor futuro no PGBL descontado da inflação: R$ {valor_real_pgbl:,.2f}")
    if valor_final_fundo > 0:
        st.write(f"- Valor acumulado no Fundo LP (bruto): R$ {valor_final_fundo:,.2f}")
        st.write(f"- Valor futuro no Fundo LP descontado da inflação: R$ {valor_real_fundo:,.2f}")

    # Resgates
    if modo_resgate == "Renda Vitalícia (mensal)":
        # calcular taxa real mensal para LP e PGBL
        taxa_real_pgbl_ano = (1 + taxa_nominal / 100.0) / (1 + inflacao / 100.0) - 1
        taxa_real_fundo_ano = (1 + taxa_fundo / 100.0) / (1 + inflacao / 100.0) - 1
        taxa_real_pgbl_mensal = (1 + taxa_real_pgbl_ano) ** (1/12) - 1
        taxa_real_fundo_mensal = (1 + taxa_real_fundo_ano) ** (1/12) - 1

        meses = int(anos_resgate * 12)
        saque_mensal = calcula_saque_mensal(
            total_lp=valor_real_fundo,
            total_pgbl=valor_real_pgbl,
            taxa_real_lp=taxa_real_fundo_mensal,
            taxa_real_pgbl=taxa_real_pgbl_mensal,
            meses=meses
        )
        st.write(f"- Renda vitalícia mensal estimada (em R$ de hoje): R$ {saque_mensal:,.2f}")
        st.markdown("_Observação: a renda vitalícia mensal considera primeiro o saldo do Fundo LP e depois do PGBL._")

    elif modo_resgate.startswith("Resgate Mensal"):
        # similar à renda vitalícia, mas resgate por anos especificados
        taxa_real_pgbl_ano = (1 + taxa_nominal / 100.0) / (1 + inflacao / 100.0) - 1
        taxa_real_fundo_ano = (1 + taxa_fundo / 100.0) / (1 + inflacao / 100.0) - 1
        taxa_real_pgbl_mensal = (1 + taxa_real_pgbl_ano) ** (1/12) - 1
        taxa_real_fundo_mensal = (1 + taxa_real_fundo_ano) ** (1/12) - 1

        meses = int(anos_resgate * 12)
        saque_mensal = calcula_saque_mensal(
            total_lp=valor_real_fundo,
            total_pgbl=valor_real_pgbl,
            taxa_real_lp=taxa_real_fundo_mensal,
            taxa_real_pgbl=taxa_real_pgbl_mensal,
            meses=meses
        )
        st.write(f"- Saque mensal constante por {anos_resgate} anos: R$ {saque_mensal:,.2f}")

    else:
        # Resgates anuais sem simulação complexa, apenas soma valores reais e divide
        saque_anual = (valor_real_pgbl + valor_real_fundo) / anos_resgate
        st.write(f"- Saque anual por {anos_resgate} anos: R$ {saque_anual:,.2f}")
        st.markdown(
            "_Observação: dependendo da ordem cronológica dos aportes, parte do capital resgatado poderá ter tempo de permanência menor que 10 anos, gerando alíquotas superiores a 10% no IR regressivo._"
        )

    imposto_economizado_total = restit_ano * (anos_aporte - 1)
    st.subheader("Economia Fiscal")
    st.write(f"- Imposto economizado ao longo do período: R$ {imposto_economizado_total:,.2f}")
