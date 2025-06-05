import streamlit as st
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# 1) Definições de funções (sempre antes de qualquer chamada no Streamlit UI)
# ─────────────────────────────────────────────────────────────────────────────

def calc_irpf_anual(renda_anual: float) -> float:
    """
    Calcula o Imposto de Renda anual devido, pela tabela progressiva (ano-calendário 2024).
    Retorna o valor de IR (R$).
    """
    base = renda_anual
    if base <= 26_963.20:
        return 0.0
    elif base <= 33_919.80:
        aliquota = 0.075
        deducao = 2_022.24
    elif base <= 45_012.60:
        aliquota = 0.15
        deducao = 4_566.23
    elif base <= 55_976.16:
        aliquota = 0.225
        deducao = 7_942.17
    else:
        aliquota = 0.275
        deducao = 10_740.98

    ir = base * aliquota - deducao
    return max(ir, 0.0)

def get_aliquota_regressiva(anos: int) -> float:
    """
    Retorna alíquota regressiva de IR para previdência, de acordo com anos completos.
    """
    if anos <= 2:
        return 0.35
    elif anos <= 4:
        return 0.30
    elif anos <= 6:
        return 0.25
    elif anos <= 8:
        return 0.20
    elif anos <= 10:
        return 0.15
    else:
        return 0.10

def simular_pgbl_fifo_com_outros(renda_anual, percentual_aporte, taxa_retorno, prazo_anos):
    """
    Simula aportes anuais em PGBL (até 12% da renda) e reinvestimento da economia de IR em 'outros'.
    Retorna:
      - lotes_pgbl: lista de tuplas (ano_do_aporte, valor_aporte_anual_em_R$)
      - saldo_outros: valor acumulado em 'outros investimentos' ao fim de prazo_anos
    """
    ir_sem_pgbl = calc_irpf_anual(renda_anual)
    ir_base = ir_sem_pgbl

    lotes_pgbl = []      # cada item: (ano_do_aporte, valor_aporte)
    saldo_outros = 0.0   # acumulado do reinvestimento da economia
    prev_economia = 0.0  # economia de IR do ano anterior

    for ano in range(1, int(prazo_anos) + 1):
        aporte_base = renda_anual * percentual_aporte

        if ano == 1:
            adicional_pgbl = 0.0
            aporte_outros = 0.0
        else:
            teto_pgbl_total = renda_anual * 0.12
            disponivel_para_pgbl = max(teto_pgbl_total - (renda_anual * percentual_aporte), 0.0)
            adicional_pgbl = min(prev_economia, disponivel_para_pgbl)
            aporte_outros = prev_economia - adicional_pgbl

        aporte_pgbl = aporte_base + adicional_pgbl
        lotes_pgbl.append((ano, aporte_pgbl))

        # Calcular IR com aporte total neste ano
        ir_com_aporte = calc_irpf_anual(renda_anual - aporte_pgbl)
        economia_ano = ir_base - ir_com_aporte

        # Atualizar saldo de 'outros investimentos' (investimento anual simples)
        saldo_outros = (saldo_outros + aporte_outros) * (1 + taxa_retorno)

        prev_economia = economia_ano

    return lotes_pgbl, saldo_outros

def calcular_economia_total(renda_anual, percentual_aporte, taxa_retorno, prazo_anos):
    """
    Calcula a economia total de IR projetada ao longo de 'prazo_anos', considerando:
      1) Economia anual de IR = IR sem PGBL - IR com aporte
      2) Reinvestimento dessa economia em 'outros'
      3) Na saída (apos 10 anos de cada lote de PGBL) tira-se IR a 10% sobre o valor futuro.
    Retorna:
      - economia_total_bruta: soma de tudo que não foi pago de IR (inclui reinvestimentos)
      - economia_total_liquida: valor líquido projetado após tributação na saída do PGBL
    """
    ir_sem_pgbl = calc_irpf_anual(renda_anual)
    ir_base = ir_sem_pgbl

    lotes_pgbl = []
    prev_economia = 0.0
    # lista de tuplas para cada lote: (ano_do_aporte, valor_aporte, economia_do_ano)
    historico_economia = []

    for ano in range(1, int(prazo_anos) + 1):
        aporte_base = renda_anual * percentual_aporte

        if ano == 1:
            adicional_pgbl = 0.0
            aporte_outros = 0.0
        else:
            teto_pgbl_total = renda_anual * 0.12
            disponivel_para_pgbl = max(teto_pgbl_total - (renda_anual * percentual_aporte), 0.0)
            adicional_pgbl = min(prev_economia, disponivel_para_pgbl)
            aporte_outros = prev_economia - adicional_pgbl

        aporte_pgbl = aporte_base + adicional_pgbl
        lotes_pgbl.append((ano, aporte_pgbl))

        ir_com_aporte = calc_irpf_anual(renda_anual - aporte_pgbl)
        economia_ano = ir_base - ir_com_aporte

        historico_economia.append((ano, economia_ano))
        prev_economia = economia_ano

    # Agora, calcular projeção do que foi economizado:
    #   - Cada ano de economia reinvestido ao retorno 'taxa_retorno' até cada lote de PGBL sair
    economia_total_bruta = 0.0
    economia_total_liquida = 0.0

    for (ano_aporte, aporte) in lotes_pgbl:
        # Ano em que este lote completa 10 anos:
        ano_saida = ano_aporte + 10 - 1  # se a contagem do ano do aporte = 1, +9 para ter 10 total
        if ano_saida > prazo_anos:
            # Saída ocorreria depois do horizonte, mas incluiremos como se fosse ano N+...
            anos_para_saida = (prazo_anos - ano_aporte + 1) + (10 - (prazo_anos - ano_aporte + 1))
        else:
            anos_para_saida = 10

        # Somar todas as economias de IR dos anos até ano_aporte (essas economias são
        # reinvestidas em 'outros' até ano_saida):
        soma_economias_reinvestidas = 0.0
        for (ano_economia, econ_val) in historico_economia:
            if ano_economia <= ano_aporte:
                # reinvestir econ_val por (ano_saida - ano_economia + 1) anos
                periodo = ano_saida - ano_economia + 1
                soma_economias_reinvestidas += econ_val * ((1 + taxa_retorno) ** periodo)

        # Valor bruto futuro do lote de PGBL:
        valor_futuro_lote = aporte * ((1 + taxa_retorno) ** anos_para_saida)
        aliquota_lote = get_aliquota_regressiva(anos_para_saida)
        valor_liquido_lote = valor_futuro_lote * (1 - aliquota_lote)

        economia_total_bruta += soma_economias_reinvestidas
        economia_total_liquida += (soma_economias_reinvestidas + valor_futuro_lote) * (1 - aliquota_lote)

    return round(economia_total_bruta, 2), round(economia_total_liquida, 2)

# ─────────────────────────────────────────────────────────────────────────────
# 2) INÍCIO DA INTERFACE STREAMLIT
# ─────────────────────────────────────────────────────────────────────────────

st.title("🧮 Simulador Financeiro de PGBL (com IR, FIFO e Renda Real)")

st.markdown("""
Este aplicativo permite:
1. Calcular IR sem PGBL e com aportes em PGBL (até 12% da renda).
2. Exibir economia de IR anual e acumulada, com reinvestimento.
3. Projetar evolução de patrimônio (PGBL e outros investimentos).
4. Calcular rendimento perpétuo (nominal e real, considerando inflação).
""")

# 1) Renda Bruta Anual
renda_anual = st.number_input(
    "Renda Bruta Anual (R$):", min_value=0.0, value=100_000.0, step=1_000.0, format="%.2f"
)

# 2) Percentual de aporte em PGBL (0–12%)
percentual_input = st.slider(
    "Percentual de Renda a Aportar em PGBL (%):", 
    min_value=0.0, max_value=12.0, value=12.0, step=0.1
) / 100.0

# 3) Taxa de retorno anual esperada (ex.: 10%)
taxa_retorno = st.number_input(
    "Taxa de Retorno Anual (%):", min_value=0.0, max_value=100.0, value=10.0, step=0.1
) / 100.0

# 4) Prazo de projeção para aportes em anos
prazo_anos = st.number_input(
    "Prazo de Projeção (anos):", min_value=1, max_value=50, value=15, step=1
)

# 5) Frequência de aporte: "Anual" ou "Mensal"
frequencia = st.radio(
    "Frequência dos Aportes:",
    ("Anual", "Mensal")
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# 3) Cálculos de IR anual imediato (sem PGBL, com 12%, com % escolhido)
# ─────────────────────────────────────────────────────────────────────────────

ir_sem_pgbl = calc_irpf_anual(renda_anual)

# IR se aportasse 12% da renda (teto)
deducao_12 = renda_anual * 0.12
ir_com_12 = calc_irpf_anual(renda_anual - deducao_12)

# IR se aportasse percentual escolhido
deducao_escolhida = renda_anual * percentual_input
ir_com_escolha = calc_irpf_anual(renda_anual - deducao_escolhida)

economia_12 = ir_sem_pgbl - ir_com_12
economia_escolha = ir_sem_pgbl - ir_com_escolha

# Mostra os métricos de IR imediatamente
st.subheader("📊 Imposto de Renda e Economia Imediata")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="IR sem PGBL (R$):", value=f"{ir_sem_pgbl:,.2f}")
    st.metric(label="IR com PGBL a 12% (R$):", value=f"{ir_com_12:,.2f}")
with col2:
    st.metric(label=f"IR com PGBL a {percentual_input*100:.1f}% (R$):", value=f"{ir_com_escolha:,.2f}")
    st.metric(label="Economia de Imposto Ano 1 (R$):", value=f"{economia_escolha:,.2f}")
with col3:
    st.metric(label="Economia de Imposto Ano-teto (12%) (R$):", value=f"{economia_12:,.2f}")
    st.metric(label="Economia Percentual Escolhido (%)", value=f"{100 * economia_escolha / ir_sem_pgbl if ir_sem_pgbl>0 else 0:.2f}%")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# 4) Projeção de Evolução Ano a Ano (PGBL e Outros), com lotes FIFO
# ─────────────────────────────────────────────────────────────────────────────

# Saldo inicial
saldo_pgb = 0.0
saldo_outros = 0.0
prev_economia = 0.0
ir_base = ir_sem_pgbl

anos = []
lista_saldo_pgb = []
lista_saldo_outros = []
lista_contrib_pgb = []
lista_contrib_outros = []
lista_economia = []

for ano in range(1, int(prazo_anos) + 1):
    aporte_base = renda_anual * percentual_input

    if ano == 1:
        adicional_pgbl = 0.0
        aporte_outros = 0.0
    else:
        teto_pgbl_total = renda_anual * 0.12
        disponivel_para_pgbl = max(teto_pgbl_total - (renda_anual * percentual_input), 0.0)
        adicional_pgbl = min(prev_economia, disponivel_para_pgbl)
        aporte_outros = prev_economia - adicional_pgbl

    aporte_pgbl = aporte_base + adicional_pgbl

    # Atualiza saldos de PGBL e "Outros"
    if frequencia == "Anual":
        saldo_pgb = (saldo_pgb + aporte_pgbl) * (1 + taxa_retorno)
        saldo_outros = (saldo_outros + aporte_outros) * (1 + taxa_retorno)
    else:
        # Capitalização mensal
        taxa_m = (1 + taxa_retorno)**(1/12) - 1
        aporte_mensal_pgb = aporte_pgbl / 12.0
        aporte_mensal_outros = aporte_outros / 12.0

        for _ in range(12):
            saldo_pgb = (saldo_pgb + aporte_mensal_pgb) * (1 + taxa_m)
            saldo_outros = (saldo_outros + aporte_mensal_outros) * (1 + taxa_m)

    ir_com_total = calc_irpf_anual(renda_anual - aporte_pgbl)
    economia_ano = ir_base - ir_com_total

    anos.append(ano)
    lista_saldo_pgb.append(saldo_pgb)
    lista_saldo_outros.append(saldo_outros)
    lista_contrib_pgb.append(aporte_pgbl)
    lista_contrib_outros.append(aporte_outros)
    lista_economia.append(economia_ano)

    prev_economia = economia_ano

# Monta DataFrame para exibição
df_evolucao = pd.DataFrame({
    "Ano": anos,
    "Aporte PGBL (R$)": lista_contrib_pgb,
    "Aporte Outros (R$)": lista_contrib_outros,
    "Saldo PGBL (R$)": lista_saldo_pgb,
    "Saldo Outros (R$)": lista_saldo_outros,
    "Economia IR (R$)": lista_economia
})

st.subheader("📅 Evolução Ano a Ano (PGBL vs Outros)")
st.dataframe(df_evolucao.style.format({
    "Aporte PGBL (R$)": "{:,.2f}",
    "Aporte Outros (R$)": "{:,.2f}",
    "Saldo PGBL (R$)": "{:,.2f}",
    "Saldo Outros (R$)": "{:,.2f}",
    "Economia IR (R$)": "{:,.2f}"
}))

st.subheader("📊 Gráficos de Evolução")
st.line_chart(df_evolucao.set_index("Ano")[["Saldo PGBL (R$)", "Saldo Outros (R$)"]])
st.line_chart(df_evolucao.set_index("Ano")[["Aporte PGBL (R$)", "Aporte Outros (R$)"]])
st.line_chart(df_evolucao.set_index("Ano")[["Economia IR (R$)"]])

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# 5) Projeção de Saques Lote a Lote (FIFO)
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("💰 Saques Anuais FIFO (Lote a Lote)")

# Pergunta: em quantos anos após N o usuário planeja fazer os saques periódicos?
resgate_anos = st.number_input(
    "Horizonte de Saque (anos) após fim de N:", min_value=1, max_value=50, value=5, step=1
)

if st.button("Calcular Saques FIFO"):
    # Re-executar função para obter lotes
    lotes_pgbl, _ = simular_pgbl_fifo_com_outros(renda_anual, percentual_input, taxa_retorno, prazo_anos)

    retiradas = []
    used_lotes = set()

    # Para cada ano de saque (do período N+1 até N+resgate_anos)
    for ano_saque in range(int(prazo_anos + 1), int(prazo_anos + 1 + resgate_anos)):
        bruto_retirado = 0.0
        detalhes = []

        for (ano_lote, valor_lote) in lotes_pgbl:
            if (ano_lote, valor_lote) in used_lotes:
                continue
            idade = ano_saque - ano_lote + 1
            if idade >= 10:
                valor_futuro = valor_lote * (1 + taxa_retorno) ** idade
                bruto_retirado += valor_futuro
                used_lotes.add((ano_lote, valor_lote))
                detalhes.append((ano_lote, idade, round(valor_futuro, 2)))

        liquido_retirado = bruto_retirado * 0.90  # 10% IR
        retiradas.append({
            "Ano de Saque": ano_saque,
            "Bruto Retirado (R$)": round(bruto_retirado, 2),
            "Líquido Retirado (R$)": round(liquido_retirado, 2),
            "Detalhes": detalhes
        })

    df_retiradas = pd.DataFrame([{
        "Ano de Saque": r["Ano de Saque"],
        "Bruto Retirado (R$)": r["Bruto Retirado (R$)"],
        "Líquido Retirado (R$)": r["Líquido Retirado (R$)"]
    } for r in retiradas])

    st.dataframe(df_retiradas.style.format({
        "Bruto Retirado (R$)": "{:,.2f}",
        "Líquido Retirado (R$)": "{:,.2f}"
    }))

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# 6) Cálculo de Economia Total de IR (acumulada) – conceitual
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("📈 Economia Total de IR (Projetada até Saída)")

if st.button("Calcular Economia Total de IR"):
    econ_bruta, econ_liquida = calcular_economia_total(renda_anual, percentual_input, taxa_retorno, prazo_anos)
    st.metric(label="Economia Total Bruta (R$):", value=f"{econ_bruta:,.2f}")
    st.metric(label="Economia Total Líquida (R$):", value=f"{econ_liquida:,.2f}")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# 7) Renda Perpétua Real (opcional)
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("🔢 Renda Perpétua Real (opcional)")

inflacao = st.number_input(
    "Taxa de Inflação Anual (em %):", min_value=0.0, max_value=100.0, value=4.0, step=0.1
) / 100.0

if st.button("Calcular Renda Perpétua Real"):
    lotes_pgbl, saldo_outros_iter = simular_pgbl_fifo_com_outros(renda_anual, percentual_input, taxa_retorno, prazo_anos)

    # Determinar principal perpétuo PGBL (idade >= 10)
    principal_perp_pgb = 0.0
    for (ano_lote, valor_lote) in lotes_pgbl:
        idade = prazo_anos - ano_lote + 1
        if idade >= 10:
            valor_principal = valor_lote * (1 + taxa_retorno) ** 10
            principal_perp_pgb += valor_principal

    # Renda nominal perpétua
    renda_nominal_pgb_bruto = principal_perp_pgb * taxa_retorno
    renda_nominal_pgb_liquido = renda_nominal_pgb_bruto * (1 - 0.10)

    renda_nominal_outros_bruto = saldo_outros_iter * taxa_retorno
    renda_nominal_outros_liquido = renda_nominal_outros_bruto * (1 - 0.15)

    # Fator de inflação acumulada até N
    fator_infl = (1 + inflacao) ** prazo_anos

    real_pgb_liquido = renda_nominal_pgb_liquido / fator_infl
    real_outros_liquido = renda_nominal_outros_liquido / fator_infl

    df_real_perp = pd.DataFrame({
        "Componente": ["PGBL (alíquota 10%)", "Outros Investimentos (15%)"],
        "Principal no Ano N (R$)": [round(principal_perp_pgb, 2), round(saldo_outros_iter, 2)],
        "Renda Líquida Nominal (R$/ano)": [round(renda_nominal_pgb_liquido, 2), round(renda_nominal_outros_liquido, 2)],
        "Renda Real Líquida (R$/ano em valores de hoje)": [round(real_pgb_liquido, 2), round(real_outros_liquido, 2)]
    })
    st.dataframe(df_real_perp)
