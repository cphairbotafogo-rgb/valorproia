# -*- coding: utf-8 -*-
import yfinance as yf
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

# =============================================================================
# 🧠 INTELIGÊNCIA DE SETORES
# =============================================================================
DICIONARIO_SETORES = {
    "PETR4": "Petróleo e Gás", "PETR3": "Petróleo e Gás", "PRIO3": "Petróleo e Gás", 
    "VALE3": "Mineração", "BRAP4": "Mineração",
    "ITUB4": "Bancos", "BBDC4": "Bancos", "BBAS3": "Bancos", "SANB11": "Bancos",
    "WEGE3": "Bens Industriais", "EMBR3": "Bens Industriais",
    "ELET3": "Energia", "TAEE11": "Energia", "EGIE3": "Energia", "CPLE6": "Energia",
    "SBSP3": "Saneamento", "CSMG3": "Saneamento",
    "MXRF11": "FII - Papel", "KNIP11": "FII - Papel", "KNCR11": "FII - Papel", "IRDM11": "FII - Papel", "CPTS11": "FII - Papel", "VGIR11": "FII - Papel",
    "HGLG11": "FII - Logística", "BTLG11": "FII - Logística", "XPLG11": "FII - Logística", "ALZR11": "FII - Logística",
    "XPML11": "FII - Shopping", "VISC11": "FII - Shopping", "HGBS11": "FII - Shopping",
    "HGRU11": "FII - Renda Urbana", "TRXF11": "FII - Renda Urbana",
    "KNRI11": "FII - Híbrido",
    "BTC-BRL": "Cripto - Bitcoin", "ETH-BRL": "Cripto - Ethereum", "USDT-BRL": "Cripto - Stablecoin",
    "AAPL": "EUA - Tecnologia", "MSFT": "EUA - Tecnologia", "GOOGL": "EUA - Tecnologia", "AMZN": "EUA - Consumo",
    "VOO": "EUA - ETF S&P500", "IVV": "EUA - ETF S&P500"
}

def descobrir_setor(ticker, categoria):
    return DICIONARIO_SETORES.get(ticker.upper(), categoria)

# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================
def _safe_float(val, default=0.0):
    try:
        if val is None: return default
        v = float(val)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError): return default

def formatar_qtd(valor):
    if pd.isna(valor) or valor == "": return "0"
    try: return f"{float(valor):.8f}".rstrip('0').rstrip('.')
    except: return str(valor)

def classificar_ativo(categoria, p_vp, p_l):
    if categoria == "Criptomoedas": return "⚡ Volátil"
    if categoria == "Exterior (EUA)": return "🌎 Global"
    if categoria in ["FIIs", "Fiagro", "FII"]:
        if p_vp <= 0: return "⚪ Sem dados"
        if p_vp < 0.85: return "💎 Muito Barato"
        if p_vp < 0.98: return "✅ Barato"
        if p_vp <= 1.03: return "⚖️ Justo"
        return "⚠️ Caro"
    else:
        if p_l <= 0: return "⚪ Sem dados"
        if p_l < 7: return "💎 Barata"
        if p_l <= 15: return "⚖️ Justa"
        return "⚠️ Cara"

def formatar_delta(valor, is_percent=False):
    if pd.isna(valor) or valor == "" or valor == "-": return "-"
    try:
        val_float = float(valor)
        suffix = "%" if is_percent else ""
        prefix = "R$ " if not is_percent else ""
        if val_float > 0: return f"🟢 +{prefix}{val_float:.2f}{suffix}"
        if val_float < 0: return f"🔴 {prefix}{val_float:.2f}{suffix}"
        return f"⚪ {prefix}0.00{suffix}"
    except: return "-"

# =============================================================================
# 🚀 MOTOR DE BUSCA OTIMIZADO PARA NUVEM (BLINDADO)
# =============================================================================
@st.cache_data(ttl=600, show_spinner=False)
def buscar_mercado(ticker: str, categoria_sugerida: str = None):
    ticker = ticker.upper().strip()
    
    # 1. Identificação da Categoria
    is_us = (categoria_sugerida == "Exterior (EUA)")
    is_crypto = ticker.endswith("-BRL") or ticker.endswith("-USD") or categoria_sugerida == "Criptomoedas"
    
    # Formatação do Ticker
    t_yahoo = ticker if (is_us or is_crypto) else f"{ticker}.SA"
    categoria = categoria_sugerida if categoria_sugerida else ("FIIs" if ticker.endswith("11") else "Ações")

    try:
        dat = yf.Ticker(t_yahoo)
        
        # ---------------------------------------------------------
        # PASSO 1: PEGANDO O PREÇO DE FORMA SEGURA (SEM USAR .INFO)
        # ---------------------------------------------------------
        # BLINDAGEM APLICADA: 5 dias para evitar falha no final de semana + actions=False
        df_hist = dat.history(period="5d", actions=False, auto_adjust=False)
        
        if df_hist.empty:
            return None
            
        preco = _safe_float(df_hist['Close'].iloc[-1])
        
        # Variáveis padrão
        p_vp, p_l, dy_raw, rend_ultimo, variacao_dia = 0.0, 0.0, 0.0, 0.0, 0.0

        # ---------------------------------------------------------
        # PASSO 2: INDICADORES APENAS PARA AÇÕES E FIIS
        # Criptomoedas quebram o .info, então nós pulamos elas!
        # ---------------------------------------------------------
        if not is_crypto:
            try:
                info = dat.info
                p_vp = _safe_float(info.get('priceToBook'))
                p_l = _safe_float(info.get('trailingPE') or info.get('forwardPE'))
                variacao_dia = _safe_float(info.get('regularMarketChangePercent'))
                dy_raw = _safe_float(info.get('dividendYield'))
                rend_ultimo = _safe_float(info.get('lastDividendValue'))
                
                # Se rend_ultimo vier zerado (comum em FIIs), buscamos no histórico seguro
                if rend_ultimo == 0:
                    hist_completo = dat.history(period="1y")
                    if 'Dividends' in hist_completo.columns:
                        divs = hist_completo[hist_completo['Dividends'] > 0]
                        if not divs.empty:
                            rend_ultimo = _safe_float(divs['Dividends'].iloc[-1])
            except Exception:
                # Se o .info der pau, não tem problema! O "pass" aqui salva a gente.
                # Como já pegamos o Preço lá em cima, o app não vai quebrar.
                pass

        # Cálculos Finais
        dy_12m = f"{dy_raw * 100:.2f}%" if dy_raw > 0 else "-"
        dy_m = (rend_ultimo / preco * 100) if rend_ultimo > 0 and preco > 0 else 0.0

        if preco > 0:
            return {
                "Ticker": ticker,
                "Categoria": categoria,
                "Preço": preco,
                "Var_Dia": variacao_dia,
                "DY_12M": dy_12m,
                "DY_Mensal": f"{dy_m:.2f}%",
                "Rend": rend_ultimo,
                "P_VP": p_vp,
                "P_L": p_l,
                "Status": classificar_ativo(categoria, p_vp, p_l)
            }
            
    except Exception as e:
        # Se quiser ver o erro escondido no futuro, é só colocar st.error(e) aqui
        pass
    
    return None
