# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import pandas as pd
import streamlit as st

# =============================================================================
# 🧠 INTELIGÊNCIA DE SETORES (ROTA 4)
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
# FUNÇÕES UTILITÁRIAS E SCRAPING
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
        if p_vp < 0.80: return "💎 Muito Barato"
        if p_vp < 0.95: return "✅ Barato"
        if p_vp <= 1.05: return "⚖️ Justo"
        if p_vp <= 1.20: return "⚠️ Caro"
        return "🚨 Muito Caro"
    else:
        if p_l <= 0: return "⚪ Sem dados"
        if p_l < 5: return "💎 Muito Barata"
        if p_l < 10: return "✅ Barata"
        if p_l <= 15: return "⚖️ Justa"
        if p_l <= 25: return "⚠️ Cara"
        return "🚨 Muito Cara"

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

@st.cache_data(ttl=300, show_spinner=False)
def buscar_mercado(ticker: str, categoria_sugerida: str = None):
    ticker = ticker.upper().strip()
    is_crypto = ticker.endswith("-BRL") or ticker.endswith("-USD")
    is_us = (categoria_sugerida == "Exterior (EUA)")
    
    if categoria_sugerida in ["Ações", "Acao", "BDR"]: is_fii = False
    else: is_fii = (categoria_sugerida in ["FIIs", "Fiagro", "FII"]) if categoria_sugerida else ticker.endswith("11")
        
    if is_crypto: categoria = "Criptomoedas"
    elif is_us: categoria = "Exterior (EUA)"
    elif is_fii: categoria = "FIIs"
    else: categoria = "Ações"

    preco = p_vp = p_l = rend_ultimo = dy_m = 0.0
    dy_12m = "0,00%"
    variacao_dia = 0.0
    headers = {'User-Agent': 'Mozilla/5.0'}

    usd_brl = 1.0
    if is_us:
        try: usd_brl = _safe_float(requests.get("https://query2.finance.yahoo.com/v7/finance/quote?symbols=BRL=X", headers=headers, timeout=4).json()["quoteResponse"]["result"][0]["regularMarketPrice"])
        except: usd_brl = 5.0 

    if is_crypto:
        try:
            symbol_binance = ticker.replace("-", "") 
            r_bin = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_binance}", timeout=4)
            if r_bin.status_code == 200:
                data = r_bin.json()
                preco = _safe_float(data.get("lastPrice")); variacao_dia = _safe_float(data.get("priceChangePercent"))
        except: pass

    try:
        symbol = ticker if (is_crypto or is_us) else f"{ticker}.SA"
        url = f"https://query2.finance.yahoo.com/v7/finance/quote?symbols={symbol}&fields=regularMarketPrice,priceToBook,trailingPE,forwardPE,regularMarketChangePercent,dividendYield"
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            d = r.json().get("quoteResponse", {}).get("result", [])[0]
            if preco == 0.0: preco = _safe_float(d.get("regularMarketPrice")) * (usd_brl if is_us else 1)
            p_vp = _safe_float(d.get("priceToBook")); p_l = _safe_float(d.get("trailingPE") or d.get("forwardPE"))
            if variacao_dia == 0.0: variacao_dia = _safe_float(d.get("regularMarketChangePercent"))
            dy_raw = _safe_float(d.get("dividendYield"))
            if dy_raw > 0: dy_12m = f"{dy_raw * 100:.2f}%"
    except: pass

    if not is_crypto and not is_us:
        url_cat = "fundos-imobiliarios" if is_fii else "acoes"
        try:
            r3 = requests.get(f"https://statusinvest.com.br/{url_cat}/{ticker.lower()}", headers=headers, timeout=5)
            if r3.status_code == 200 and "não encontramos" not in r3.text.lower():
                soup = BeautifulSoup(r3.text, "html.parser")
                def _ext_text(termos):
                    termos_lower = [t.lower() for t in (termos if isinstance(termos, list) else [termos])]
                    for tag in soup.find_all(["h3", "h4", "span", "div"]):
                        texto = tag.get_text(strip=True).lower()
                        if any(t == texto or (t in texto and len(texto) < 40) for t in termos_lower):
                            strong = tag.find_next("strong")
                            if strong: return strong.get_text(strip=True)
                    return ""
                def _ext_float(termos):
                    raw = _ext_text(termos)
                    if raw: return _safe_float(raw.replace("R$", "").replace("%", "").replace(".", "").replace(",", ".").strip())
                    return 0.0

                if preco == 0.0: preco = _ext_float(["valor atual", "cotação"])
                if p_vp == 0.0: p_vp = _ext_float(["p/vp", "preço sobre o valor patrimonial", "vpa"])
                if p_l == 0.0: p_l = _ext_float(["p/l"])
                rend_si = _ext_float(["último rendimento", "rendimento"])
                if rend_si > 0: rend_ultimo = rend_si
                if dy_12m == "0,00%" or dy_12m == "-":
                    dy_text = _ext_text(["dividend yield"])
                    if dy_text: dy_12m = dy_text
                
                if variacao_dia == 0.0:
                    for div in soup.find_all(title=True):
                        if "variação" in div["title"].lower() or "variacao" in div["title"].lower():
                            b_tag = div.find("b")
                            if b_tag:
                                raw_var = b_tag.get_text(strip=True).replace("%", "").replace(".", "").replace(",", ".")
                                val = _safe_float(raw_var)
                                if "down" in b_tag.get("class", []) or "-" in raw_var: val = -abs(val)
                                variacao_dia = val
                                break
        except: pass

        if p_vp == 0.0 or p_l == 0.0:
            try:
                r4 = requests.get(f"https://www.fundamentus.com.br/detalhes.php?papel={ticker}", headers=headers, timeout=5)
                if r4.status_code == 200:
                    soup_f = BeautifulSoup(r4.text, "html.parser")
                    def _ext_fund(label):
                        span = soup_f.find("span", string=label)
                        if span:
                            td_val = span.find_parent("td").find_next_sibling("td")
                            if td_val: return _safe_float(td_val.get_text(strip=True).replace("%", "").replace(".", "").replace(",", "."))
                        return 0.0
                    if p_vp == 0.0: p_vp = _ext_fund("P/VP")
                    if p_l == 0.0: p_l = _ext_fund("P/L")
            except: pass

    if preco > 0.0 or p_vp > 0.0 or is_crypto:
        dy_m = (rend_ultimo / preco * 100) if rend_ultimo > 0 and preco > 0 else 0.0
        return {"Ticker": ticker, "Categoria": categoria, "Preço": preco, "Var_Dia": variacao_dia, "DY_12M": dy_12m, "DY_Mensal": f"{dy_m:.2f}%", "Rend": rend_ultimo, "P_VP": p_vp, "P_L": p_l, "Status": classificar_ativo(categoria, p_vp, p_l)}
    return None

def buscar_multiplos(itens):
    resultados = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {}
        for item in itens:
            if isinstance(item, tuple) or isinstance(item, list): futures[ex.submit(buscar_mercado, item[0], item[1])] = item[0]
            else: futures[ex.submit(buscar_mercado, item)] = item
        for fut in as_completed(futures):
            res = fut.result()
            if res: resultados.append(res)
    return resultados