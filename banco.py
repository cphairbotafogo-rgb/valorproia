# -*- coding: utf-8 -*-
import os
import pandas as pd

# =============================================================================
# CONSTANTES E BANCO DE DADOS (AGORA LENDO DA PASTA ATUAL)
# =============================================================================

DB_FILE = "minhas_transacoes.csv"
LOG_PRECOS_FILE = "historico_precos.csv"
DIVIDENDOS_FILE = "meus_dividendos.csv"
PRECOS_MANUAIS_FILE = "precos_manuais.csv" 
SNAPSHOT_FILE = "snapshot_patrimonio.csv" 

def carregar_dados():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df["Data"] = pd.to_datetime(df["Data"]).dt.date
        df["Qtd"] = pd.to_numeric(df["Qtd"], errors="coerce").fillna(0)
        df["Preco_Pago"] = pd.to_numeric(df["Preco_Pago"], errors="coerce").fillna(0)
        df["Categoria"] = df["Categoria"].replace({"Acao": "Ações", "FII": "FIIs"})
        return df
    return pd.DataFrame(columns=["Data","Ticker","Qtd","Preco_Pago","Categoria"])

def carregar_log_precos():
    if os.path.exists(LOG_PRECOS_FILE): return pd.read_csv(LOG_PRECOS_FILE)
    return pd.DataFrame(columns=["Data_Update","Ticker","Preco_Antigo","Preco_Novo","Variacao_R$","Variacao_%"])

def carregar_dividendos():
    if os.path.exists(DIVIDENDOS_FILE):
        df = pd.read_csv(DIVIDENDOS_FILE)
        df["Data"] = pd.to_datetime(df["Data"]).dt.date
        return df
    return pd.DataFrame(columns=["Data","Ticker","Valor","Tipo"])

def carregar_precos_manuais():
    if os.path.exists(PRECOS_MANUAIS_FILE): return pd.read_csv(PRECOS_MANUAIS_FILE).set_index("Ticker")["Preco"].to_dict()
    return {}

def salvar_preco_manual(ticker, preco):
    precos = carregar_precos_manuais()
    precos[ticker] = preco
    pd.DataFrame(list(precos.items()), columns=["Ticker", "Preco"]).to_csv(PRECOS_MANUAIS_FILE, index=False)

def consolidar(df_raw):
    if df_raw.empty: return pd.DataFrame()
    df_raw = df_raw.copy()
    df_raw["Qtd"] = pd.to_numeric(df_raw["Qtd"], errors="coerce").fillna(0)
    df_raw["Preco_Pago"] = pd.to_numeric(df_raw["Preco_Pago"], errors="coerce").fillna(0)
    df_raw["Custo_Total"] = df_raw["Qtd"] * df_raw["Preco_Pago"]
    agrupado = df_raw.groupby("Ticker").agg(Qtd=("Qtd","sum"), Custo_Total=("Custo_Total","sum"), Categoria=("Categoria","first")).reset_index()
    agrupado["Preco_Medio"] = agrupado["Custo_Total"] / agrupado["Qtd"].replace(0, pd.NA)
    agrupado["Preco_Medio"] = agrupado["Preco_Medio"].fillna(0)
    return agrupado[agrupado["Qtd"] > 0].copy()