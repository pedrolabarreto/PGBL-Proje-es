
import streamlit as st
import pandas as pd
import numpy as np

def calc_irpf_anual(renda_anual: float) -> float:
    base = renda_anual
    if base <= 26963.20:
        return 0.0
    elif base <= 33919.80:
        aliquota = 0.075
        deducao = 2022.24
    elif base <= 45012.60:
        aliquota = 0.15
        deducao = 4566.23
    elif base <= 55976.16:
        aliquota = 0.225
        deducao = 7942.17
    else:
        aliquota = 0.275
        deducao = 10740.98

    ir = base * aliquota - deducao
    return max(ir, 0.0)

def get_aliquota_regressiva(anos: int) -> float:
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

def simular_pgbl_fifo(renda_anual, percentual_aporte, taxa_retorno, prazo_anos):
    # Cálculo do IR base
    ir_sem_pgbl = calc_irpf_anual(renda_anual)
    ir_base = ir_sem_pgbl

    # Listas para lotes do PGBL: cada lote é (ano_do_aporte, valor_do_aporte)
    lotes_pgbl = []

    # Lista para saldos de 'outros ativos' (soma de aportes e rendimento simples)
    saldo_outros = 0.0
    total_contrib_outros = 0.0

    prev_economia = 0.0

    # Iterar ano a ano para determinar aportes
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

        # Armazenar lote do ano corrente
        lotes_pgbl.append((ano, aporte_pgbl))

        # Calcular IR com aporte total deste ano
        ir_com_aporte_tot = calc_irpf_anual(renda_anual - aporte_pgbl)
        economia_ano = ir_base - ir_com_aporte_tot

        # Atualizar saldo de 'outros' (investimento imediato, capitalização anual simples)
        saldo_outros = (saldo_outros + aporte_outros) * (1 + taxa_retorno)
        total_contrib_outros += aporte_outros

        prev_economia = economia_ano

    #  Avaliação final dos lotes PGBL (FIFO): para cada lote calculamos valor futuro e tributamos conforme holding
    valor_bruto_pgb = 0.0
    valor_liquido_pgb = 0.0

    for ano_lote, valor_lote in lotes_pgbl:
        anos_para_final = prazo_anos - ano_lote + 1
        valor_futuro = valor_lote * (1 + taxa_retorno) ** anos_para_final
        aliquota = get_aliquota_regressiva(anos_para_final)
        valor_liquido = valor_futuro * (1 - aliquota)
        valor_bruto_pgb += valor_futuro
        valor_liquido_pgb += valor_liquido

    # Tributação dos 'outros ativos'
    ganho_outros = max(saldo_outros - total_contrib_outros, 0.0)
    ir_outros = ganho_outros * 0.15
    valor_liquido_outros = saldo_outros - ir_outros

    valor_total_liquido = valor_liquido_pgb + valor_liquido_outros

    # Retornar resultados
    resultado = {
        "valor_bruto_pgb": valor_bruto_pgb,
        "valor_liquido_pgb": valor_liquido_pgb,
        "saldo_outros": saldo_outros,
        "ir_outros": ir_outros,
        "valor_liquido_outros": valor_liquido_outros,
        "valor_total_liquido": valor_total_liquido,
        "lotes_pgbl": lotes_pgbl
    }
    return resultado

# Streamlit interface
st.title("🧮 Simulador Financeiro de PGBL com FIFO na Tributação")

renda_anual = st.number_input("Renda Bruta Anual (R$):", min_value=0.0, value=100000.0, step=1000.0, format="%.2f")
percentual_input = st.slider("Percentual de Renda a Aportar em PGBL:", min_value=0.0, max_value=12.0, value=12.0, step=0.1) / 100.0
taxa_retorno = st.number_input("Taxa de Retorno Anual (%):", min_value=0.0, max_value=100.0, value=10.0, step=0.1) / 100.0
prazo_anos = st.number_input("Prazo de Projeção (anos):", min_value=1, max_value=50, value=10, step=1)

st.markdown("---")
st.subheader("📊 Resultados com Tributação FIFO")

res = simular_pgbl_fifo(renda_anual, percentual_input, taxa_retorno, prazo_anos)

# Exibir resultados principais
col1, col2 = st.columns(2)
with col1:
    st.metric("Saldo Bruto PGBL (R$):", f"{res['valor_bruto_pgb']:,.2f}")
    st.metric("Saldo Líquido PGBL (R$):", f"{res['valor_liquido_pgb']:,.2f}")
with col2:
    st.metric("Saldo Bruto Outros Ativos (R$):", f"{res['saldo_outros']:,.2f}")
    st.metric("Saldo Líquido Outros Ativos (R$):", f"{res['valor_liquido_outros']:,.2f}")

st.markdown(f"**Total Líquido Projetado:** R$ {res['valor_total_liquido']:,.2f}")

# Exibir detalhes dos lotes
st.subheader("🗓️ Lotes de PGBL (Aporte Anual)")
df_lotes = pd.DataFrame(res["lotes_pgbl"], columns=["Ano do Aporte", "Valor do Aporte (R$)"])
st.dataframe(df_lotes.style.format({"Valor do Aporte (R$)": "{:,.2f}"}))

# ─────────────────────────────────────────────────────────────────────────────
# 8) Cálculo de Renda Perpétua Real (opcional)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("🧮 Renda Perpétua Real (opcional)")

inflacao = st.number_input(
    "Taxa de Inflação Anual (em %):", min_value=0.0, max_value=100.0, value=4.0, step=0.1
) / 100.0

if st.button("Calcular Renda Perpétua Real"):
    # Determinar lotes e saldo_outros para N anos (já calculados anteriormente: lotes_pgbl e saldo_outros)
    # Re-executar simulação de lotes e outros
    lotes_pgbl, saldo_outros_iter = simular_pgbl_fifo_com_outros(renda_anual, percentual_input, taxa_retorno, prazo_anos)

    # Determinar principal perpétuo PGBL (idade >= 10)
    principal_perp_pgb = 0.0
    for ano_lote, valor_lote in lotes_pgbl:
        idade = prazo_anos - ano_lote + 1
        if idade >= 10:
            valor_principal = valor_lote * (1 + taxa_retorno) ** 10
            principal_perp_pgb += valor_principal

    # Renda nominal perpétua
    nobr_pgb_bruto = principal_perp_pgb * taxa_retorno
    nobr_pgb_liquido = nobr_pgb_bruto * (1 - 0.10)
    nobr_outros_bruto = saldo_outros_iter * taxa_retorno
    nobr_outros_liquido = nobr_outros_bruto * (1 - 0.15)

    # Fator de inflação acumulada
    fator_infl = (1 + inflacao) ** prazo_anos

    real_pgb_liquido = nobr_pgb_liquido / fator_infl
    real_outros_liquido = nobr_outros_liquido / fator_infl

    df_real_perp = pd.DataFrame({
        "Componente": ["PGBL (alíquota 10%)", "Outros Investimentos (15%)"],
        "Principal no Ano N (R$)": [round(principal_perp_pgb, 2), round(saldo_outros_iter, 2)],
        "Renda Líquida Nominal (R$/ano)": [round(nobr_pgb_liquido, 2), round(nobr_outros_liquido, 2)],
        "Renda Real Líquida (R$/ano de hoje)": [round(real_pgb_liquido, 2), round(real_outros_liquido, 2)]
    })
    st.dataframe(df_real_perp)
