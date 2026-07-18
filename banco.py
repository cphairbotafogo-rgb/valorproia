# -*- coding: utf-8 -*-
import os
import pandas as pd

# =============================================================================
# CONSTANTES E ARQUIVOS LOCAIS (LEGADO — o app principal usa Supabase)
# =============================================================================

DB_FILE            = "minhas_transacoes.csv"
LOG_PRECOS_FILE    = "historico_precos.csv"
DIVIDENDOS_FILE    = "meus_dividendos.csv"
PRECOS_MANUAIS_FILE = "precos_manuais.csv"
SNAPSHOT_FILE      = "snapshot_patrimonio.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df["Data"] = pd.to_datetime(df["Data"]).dt.date
        df["Qtd"] = pd.to_numeric(df["Qtd"], errors="coerce").fillna(0)
        df["Preco_Pago"] = pd.to_numeric(df["Preco_Pago"], errors="coerce").fillna(0)
        df["Categoria"] = df["Categoria"].replace({"Acao": "Ações", "FII": "FIIs"})
        return df
    return pd.DataFrame(columns=["Data", "Ticker", "Qtd", "Preco_Pago", "Categoria"])

def carregar_log_precos():
    if os.path.exists(LOG_PRECOS_FILE):
        return pd.read_csv(LOG_PRECOS_FILE)
    return pd.DataFrame(columns=["Data_Update", "Ticker", "Preco_Antigo", "Preco_Novo", "Variacao_R$", "Variacao_%"])

def carregar_precos_manuais(arquivo: str = None):
    """Lê preços manuais. Aceita caminho por usuário para evitar mistura de dados."""
    caminho = arquivo or PRECOS_MANUAIS_FILE
    if os.path.exists(caminho):
        return pd.read_csv(caminho).set_index("Ticker")["Preco"].to_dict()
    return {}

def salvar_preco_manual(ticker, preco, arquivo: str = None):
    caminho = arquivo or PRECOS_MANUAIS_FILE
    precos = carregar_precos_manuais(caminho)
    precos[ticker] = preco
    pd.DataFrame(list(precos.items()), columns=["Ticker", "Preco"]).to_csv(caminho, index=False)

# =============================================================================
# CONSOLIDAÇÃO COM PREÇO MÉDIO CORRETO (regra da Receita Federal)
# =============================================================================
# Correção importante: a versão anterior somava Qtd*Preço de compras E vendas.
# Isso distorcia o preço médio sempre que havia uma venda (a venda "abatia"
# o custo pelo preço de venda, e não pelo preço médio). Agora o cálculo é
# cronológico: compras aumentam o custo, vendas reduzem a posição pelo
# preço médio vigente — exatamente como a Receita exige.

def consolidar(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    df = df_raw.copy()
    df["Qtd"] = pd.to_numeric(df["Qtd"], errors="coerce").fillna(0)
    df["Preco_Pago"] = pd.to_numeric(df["Preco_Pago"], errors="coerce").fillna(0)
    if "Data" in df.columns:
        df["_Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.sort_values("_Data", kind="stable")

    linhas = []
    for ticker, grupo in df.groupby("Ticker", sort=False):
        qtd, custo = 0.0, 0.0
        categoria = grupo["Categoria"].iloc[0] if "Categoria" in grupo.columns else "Ações"
        for _, op in grupo.iterrows():
            q, p = float(op["Qtd"]), float(op["Preco_Pago"])
            if q > 0:                      # compra: soma ao custo
                custo += q * p
                qtd += q
            elif q < 0 and qtd > 0:        # venda: baixa pelo preço médio
                pm = custo / qtd
                vendida = min(abs(q), qtd)
                custo -= vendida * pm
                qtd -= vendida
        if qtd > 1e-9:
            linhas.append({
                "Ticker": ticker,
                "Qtd": qtd,
                "Custo_Total": custo,
                "Categoria": categoria,
                "Preco_Medio": custo / qtd if qtd > 0 else 0.0,
            })

    return pd.DataFrame(linhas)
