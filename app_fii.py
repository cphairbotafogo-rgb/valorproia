# =============================================================================
# 1. IMPORTAÇÕES
# =============================================================================
import os
import json
import time
import math
import base64
import logging # NOVO: Para registrar erros sem quebrar o app
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import yfinance as yf

# NOVO: Importação para verificar senhas criptografadas
from werkzeug.security import check_password_hash 

from banco import *
from motor import *

try:
    from supabase import create_client, Client
except ImportError:
    st.error("⚠️ Biblioteca do Supabase não encontrada! Rode 'pip install supabase'.")
    st.stop()

# =============================================================================
# 2. CONFIGURAÇÃO DA PÁGINA
# =============================================================================
URL_LOGO_OFICIAL = "https://dcvbigplgruvaojmutth.supabase.co/storage/v1/object/public/logos/ChatGPT%20Image%2028%20de%20abr.%20de%202026,%2022_55_53.png"

st.set_page_config(
    page_title="ValorPró IA",
    page_icon=URL_LOGO_OFICIAL,
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 3. CONEXÃO COM O SUPABASE (AGORA SEGURO)
# =============================================================================
try:
    URL_SUPABASE  = st.secrets["SUPABASE_URL"]
    CHAVE_SUPABASE = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL_SUPABASE, CHAVE_SUPABASE)
except Exception as e:
    st.error(f"🚨 Falha ao carregar credenciais do Supabase: {e}")
    st.stop()

# =============================================================================
# 4. FUNÇÃO DE VERIFICAÇÃO DE ACESSO
# =============================================================================
try:
    EMAIL_ADMIN = st.secrets["ADMIN_EMAIL"]
    SENHA_ADMIN = st.secrets["ADMIN_PASSWORD"]
except KeyError:
    st.error("🚨 Credenciais de administrador ausentes no secrets.toml")
    st.stop()
    
ID_ADMIN = "75f81617-e3f0-49d9-8b18-9fe6f6e0ad7b" # Pode manter exposto, é apenas um identificador

def verificar_acesso(dados: dict) -> tuple:
    email      = dados.get("e-mail", "")
    status     = dados.get("status", "inativo")
    exp_str    = dados.get("expiracao")

    if email == EMAIL_ADMIN:
        return True, "admin"

    if status != "ativo":
        return False, "inativo"

    if exp_str:
        try:
            exp = date.fromisoformat(str(exp_str))
            if exp < date.today():
                try:
                    supabase.table("usuarios").update({"status": "inativo"}).eq("e-mail", email).execute()
                except Exception as e:
                    logging.error(f"Erro ao inativar usuário expirado ({email}): {e}")
                return False, "expirado"
        except Exception as e:
            logging.error(f"Data de expiração inválida para {email}: {e}")
            return False, "data_invalida"

    return True, "premium"

# =============================================================================
# 5. TELA DE LOGIN (COM HASH DE SENHA)
# =============================================================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado  = False
    st.session_state.usuario_logado = ""
    st.session_state.usuario_id   = ""
    st.session_state.tipo_acesso  = ""

if not st.session_state.autenticado:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        try:
            st.image(URL_LOGO_OFICIAL, use_container_width=True)
        except Exception:
            st.markdown("### 🏦 ValorPro IA")

        with st.form("login_form"):
            email_input = st.text_input("E-mail")
            u = email_input.strip().lower() if email_input else ""
            p = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)

            if entrar:
                if not u:
                    st.warning("Preencha o e-mail.")
                elif u == EMAIL_ADMIN and p == SENHA_ADMIN:
                    st.session_state.autenticado    = True
                    st.session_state.usuario_logado = u
                    st.session_state.usuario_id     = ID_ADMIN
                    st.session_state.tipo_acesso    = "premium"
                    st.rerun()
                else:
                    try:
                        # Busca apenas pelo e-mail
                        resp = supabase.table("usuarios").select("*").eq("e-mail", u).execute()
                        if resp.data:
                            dados = resp.data[0]
                            senha_banco = dados.get("senha")
                            
                            # Verifica hash ou fallback para texto plano
                            if check_password_hash(senha_banco, p) or senha_banco == p:
                                tem_acesso, motivo = verificar_acesso(dados)
                                if tem_acesso:
                                    st.session_state.autenticado    = True
                                    st.session_state.usuario_logado = u
                                    st.session_state.usuario_id     = dados.get("id")
                                    st.session_state.tipo_acesso    = dados.get("tipo", "premium")
                                    st.rerun()
                                elif motivo == "expirado":
                                    st.error("⏰ Seu acesso expirou. Renove o plano para continuar.")
                                    st.link_button("🔄 Renovar Acesso", "https://pay.kiwify.com.br/TZUz54c", use_container_width=True)
                                elif motivo == "inativo":
                                    st.error("❌ Conta inativa. Entre em contato com o suporte.")
                                else:
                                    st.error("❌ Problema ao verificar o acesso.")
                            else:
                                st.error("❌ Senha incorreta.")
                        else:
                            st.error("❌ E-mail não encontrado.")
                    except Exception as e:
                        st.error(f"🚨 Erro de conexão com o banco de dados: {e}")

        # Área de compra de planos
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🛒 Quero Comprar Acesso", expanded=True):
            st.markdown("### 🚀 Escolha o seu plano Premium!")
            st.markdown("---")
            col_plan1, col_plan2, col_plan3 = st.columns(3)

            with col_plan1:
                st.markdown("<h4 style='text-align:center;color:#94a3b8;'>Plano Mensal</h4>", unsafe_allow_html=True)
                st.markdown("<h2 style='text-align:center;color:#f8fafc;'>R$ 29,90</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center;font-size:13px;color:#94a3b8;'>Acesso por 30 dias.</p>", unsafe_allow_html=True)
                st.link_button("💳 Assinar Mensal", "https://pay.kiwify.com.br/TZUz54c", use_container_width=True)

            with col_plan2:
                st.markdown("<h4 style='text-align:center;color:#3b82f6;'>Plano Trimestral</h4>", unsafe_allow_html=True)
                st.markdown("<h2 style='text-align:center;color:#3b82f6;'>R$ 69,90</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center;font-size:13px;color:#94a3b8;'>Apenas R$ 23,30 por mês.</p>", unsafe_allow_html=True)
                st.link_button("💳 Assinar Trimestral", "https://pay.kiwify.com.br/HkrQfua", use_container_width=True)

            with col_plan3:
                st.markdown("<h4 style='text-align:center;color:#10b981;'>Plano Anual 🔥</h4>", unsafe_allow_html=True)
                st.markdown("<h2 style='text-align:center;color:#10b981;'>R$ 197,00</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center;font-size:13px;color:#94a3b8;'>O mais vantajoso! (R$ 16,41/mês)</p>", unsafe_allow_html=True)
                st.link_button("💳 Assinar Anual", "https://pay.kiwify.com.br/ux4MJHh", use_container_width=True)

    st.stop()

# =============================================================================
# 6. LOGO NA SIDEBAR (pós-login)
# =============================================================================
try:
    st.sidebar.image(URL_LOGO_OFICIAL, use_container_width=True)
except Exception:
    st.sidebar.markdown("🏦 **VALOR PRO IA**")

# =============================================================================
# 7. ARQUIVOS POR USUÁRIO
# =============================================================================
user_id       = st.session_state.get("usuario_logado", "admin")
user_id_clean = "".join(filter(str.isalnum, str(user_id)))

DB_FILE        = f"investimentos_{user_id_clean}.csv"
SNAPSHOT_FILE  = f"history_{user_id_clean}.csv"
PROVENTOS_FILE = f"proventos_{user_id_clean}.csv"
DB_METAS       = f"metas_financeiras_{user_id_clean}.csv"
DIVIDENDOS_FILE = f"dividendos_{user_id_clean}.csv"

# =============================================================================
# 8. CONFIGURAÇÃO DA IA (GEMINI)
# =============================================================================
CHAVE_API_GOOGLE = st.secrets.get("GEMINI_CHAVE", "")
ia_pronta = False
if CHAVE_API_GOOGLE:
    try:
        genai.configure(api_key=CHAVE_API_GOOGLE)
        modelo_escolhido = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelo_escolhido = m.name
                break
        if modelo_escolhido:
            model = genai.GenerativeModel(modelo_escolhido)
            ia_pronta = True
    except Exception:
        ia_pronta = False

# =============================================================================
# 9. FUNÇÕES UTILITÁRIAS
# =============================================================================
def _safe_float(val, default=0.0):
    try:
        if val is None: return default
        if isinstance(val, (int, float)): return float(val)
        s = str(val).replace("R$", "").replace("%", "").strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return default

def formatar_qtd(valor):
    if pd.isna(valor) or valor == "": return "0"
    try:
        return f"{float(valor):.8f}".rstrip('0').rstrip('.')
    except Exception:
        return str(valor)

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
    except Exception:
        return "-"

# =============================================================================
# 10. MOTOR DE BUSCA: YFINANCE + BINANCE + FUNDAMENTUS
# =============================================================================
def _yf_fetch_full(ticker: str):
    try:
        data = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=True)
        if data is None or data.empty: return 0.0, 0.0
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        if "Close" not in data.columns: return 0.0, 0.0
        close = data["Close"].dropna()
        if close.empty: return 0.0, 0.0
        preco = float(close.iloc[-1])
        var_dia = 0.0
        if len(close) > 1:
            preco_ant = float(close.iloc[-2])
            if preco_ant > 0:
                var_dia = ((preco / preco_ant) - 1) * 100
        return preco, var_dia
    except Exception:
        return 0.0, 0.0

def _motor_fundamentos_br(ticker, is_fii):
    import re
    p_vp = p_l = rend = 0.0
    dy = "0,00%"
    try:
        url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            html = r.text
            m_pvp = re.search(r'P/VP.*?<td[^>]*>\s*<span[^>]*>\s*([0-9,.-]+)', html, re.IGNORECASE | re.DOTALL)
            if m_pvp: p_vp = _safe_float(m_pvp.group(1))
            if not is_fii:
                m_pl = re.search(r'P/L.*?<td[^>]*>\s*<span[^>]*>\s*([0-9,.-]+)', html, re.IGNORECASE | re.DOTALL)
                if m_pl: p_l = _safe_float(m_pl.group(1))
            m_dy = re.search(r'Div\. Yield.*?<td[^>]*>\s*<span[^>]*>\s*([0-9,.-]+)%?', html, re.IGNORECASE | re.DOTALL)
            if m_dy:
                v_dy = m_dy.group(1)
                dy = f"{v_dy}%" if "%" not in v_dy else v_dy
    except Exception as e:
        logging.error(f"Erro ao extrair Fundamentus para {ticker}: {e}")

    if is_fii:
        try:
            tk = yf.Ticker(f"{ticker}.SA")
            divs = tk.dividends
            if not divs.empty: rend = float(divs.iloc[-1])
        except Exception as e:
            logging.warning(f"Yahoo Finance falhou ao buscar dividendos para {ticker}: {e}")
            
        if rend == 0.0:
            try:
                r_si = requests.get(
                    f"https://statusinvest.com.br/fundos-imobiliarios/{ticker.lower()}",
                    headers={'User-Agent': 'Mozilla/5.0'}, timeout=5
                )
                if r_si.status_code == 200:
                    import re as re2
                    m_rend = re2.search(r'Último rendimento.*?<strong[^>]*>[^0-9]*([0-9]+,[0-9]+)', r_si.text, re2.IGNORECASE | re2.DOTALL)
                    if m_rend: rend = _safe_float(m_rend.group(1))
            except Exception as e:
                logging.error(f"StatusInvest falhou ao buscar rendimento para {ticker}: {e}")

    return p_vp, p_l, dy, rend

@st.cache_data(ttl=60, show_spinner=False)
def buscar_mercado(ticker: str, categoria_sugerida: str = None):
    ticker    = ticker.upper().strip()
    is_crypto = ticker.endswith("-BRL") or ticker.endswith("-USD")
    is_us     = (categoria_sugerida == "Exterior (EUA)")
    is_fii    = (categoria_sugerida in ["FIIs", "Fiagro", "FII"]) if categoria_sugerida else ticker.endswith("11")

    categoria = "Criptomoedas" if is_crypto else ("Exterior (EUA)" if is_us else ("FIIs" if is_fii else "Ações"))
    preco = variacao_dia = p_vp = p_l = rend_ultimo = 0.0
    dy_12m = "0,00%"

    if is_crypto:
        symbol_binance = ticker.replace("-", "")
        try:
            r_bin = requests.get(f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={symbol_binance}", timeout=4)
            if r_bin.status_code == 200:
                data = r_bin.json()
                preco       = _safe_float(data.get("lastPrice"))
                variacao_dia = _safe_float(data.get("priceChangePercent"))
        except Exception:
            pass
        if preco == 0.0:
            preco, variacao_dia = _yf_fetch_full(ticker)

    elif not is_us:
        symbol = f"{ticker}.SA"
        preco, variacao_dia = _yf_fetch_full(symbol)
        p_vp, p_l, dy_12m, rend_ultimo = _motor_fundamentos_br(ticker, is_fii)

    else:
        preco, variacao_dia = _yf_fetch_full(ticker)
        try:
            tk   = yf.Ticker(ticker)
            info = tk.info
            p_vp  = _safe_float(info.get('priceToBook', 0))
            p_l   = _safe_float(info.get('trailingPE', 0))
            dy_raw = _safe_float(info.get('dividendYield', 0))
            if dy_raw > 0:
                dy_12m = f"{dy_raw * 100:.2f}%"
        except Exception:
            pass

    if preco > 0 or is_crypto:
        dy_m = (rend_ultimo / preco * 100) if (rend_ultimo > 0 and preco > 0) else 0.0
        return {
            "Ticker": ticker, "Categoria": categoria, "Preço": preco,
            "Var_Dia": variacao_dia, "DY_12M": dy_12m, "DY_Mensal": f"{dy_m:.2f}%",
            "Rend": rend_ultimo, "P_VP": p_vp, "P_L": p_l,
            "Status": classificar_ativo(categoria, p_vp, p_l)
        }
    return None

def buscar_multiplos(itens):
    resultados = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {}
        for item in itens:
            if isinstance(item, (tuple, list)):
                futures[ex.submit(buscar_mercado, item[0], item[1])] = item[0]
            else:
                futures[ex.submit(buscar_mercado, item)] = item
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                resultados.append(res)
    return resultados

# =============================================================================
# 11. BLOQUEIO PREMIUM
# =============================================================================
def exibir_bloqueio_premium(funcionalidade):
    st.markdown(f"""
        <div style="text-align:center;padding:40px;border:2px dashed #1e3a8a;border-radius:15px;background-color:#f8f9fa;">
            <h2 style="color:#1e3a8a;">🔒 {funcionalidade}</h2>
            <p style="font-size:18px;">Esta funcionalidade é exclusiva para usuários <b>Premium</b>.</p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")
    st.link_button("🚀 Liberar Acesso Premium", "https://pay.kiwify.com.br/TZUz54c", use_container_width=True, type="primary")
    st.stop()

# =============================================================================
# 12. DESIGN E CSS
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
div[data-testid="metric-container"] { border-radius:12px;padding:16px 20px;box-shadow:0 4px 15px rgba(0,0,0,0.05);border:1px solid rgba(128,128,128,0.2);background-color:var(--secondary-background-color); }
div[data-testid="metric-container"] label { font-size:12px !important;text-transform:uppercase;letter-spacing:0.08em;opacity:0.8; }
div[data-testid="metric-container"] [data-testid="stMetricValue"],
div[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-family:'DM Mono',monospace !important; }
[data-testid="stTabs"] [role="tablist"] { flex-wrap:wrap; }
[data-testid="stTabs"] button[role="tab"] { font-weight:500 !important;font-size:13px !important;transition:all 0.2s ease; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#1e3a8a,#3b82f6) !important;border:none !important;color:white !important;font-weight:600 !important;border-radius:8px !important;transition:all 0.2s ease !important; }
.stButton > button[kind="primary"]:hover { background:linear-gradient(135deg,#1e3a8a,#2563eb) !important;box-shadow:0 0 20px rgba(37,99,235,0.4) !important;transform:translateY(-1px); }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 13. LISTAS DE ATIVOS
# =============================================================================
TOP_20_FII   = ["MXRF11","HGLG11","XPML11","BTLG11","VISC11","KNIP11","KNCR11","XPLG11","HGRU11","CPTS11","IRDM11","HGBS11","ALZR11","TRXF11","VGHF11","KNSC11","VGIR11","RBRR11","MCCI11","KNRI11"]
TOP_20_ACOES = ["PETR4","VALE3","ITUB4","BBDC4","BBAS3","B3SA3","ABEV3","WEGE3","RENT3","SUZB3","ELET3","RADL3","JBSS3","EQTL3","SBSP3","EMBR3","RAIL3","PRIO3","HAPV3","BBSE3"]
LISTA_CRIPTO = ["BTC-BRL","ETH-BRL","SOL-BRL","USDT-BRL","DOGE-BRL","XRP-BRL"]
LISTA_EUA    = ["AAPL","MSFT","GOOGL","AMZN","TSLA","META","NVDA","BRK-B","JNJ","V","VOO","IVV","QQQ"]
ACOES_FALSOS_FIIS = ['TAEE11','KLBN11','SANB11','ALUP11','BPAC11','ENGI11','SULA11']
LISTA_COMPLETA_B3 = sorted(list(set(
    TOP_20_ACOES + TOP_20_FII + [
        "ALPA4","ALSO3","ALUP11","AMBP3","ARZZ4","ASAI3","AURE3","AZUL4","BBDC3","BEEF3",
        "BPAC11","BRAP4","BRFS3","BRKM5","CASH3","CCRO3","CEAB3","CGAS4","CIEL3","CMIG4",
        "COGN3","CPFE6","CPLE6","CRFB3","CSAN3","CSMG3","CSNA3","CVCB3","CXSE3","CYRE3",
        "DIRR3","EGIE3","ELET6","ENBR3","ENEV3","ENGI11","EZTC3","FLRY3","GGBR4","GOAU4",
        "GOLL4","HYPE3","IGTI11","INTB3","ITSA4","JHSF3","KLBN11","LWSA3","MGLU3","MRFG3",
        "MRVE3","MULT3","NTCO3","PCAR3","PETR3","PETZ3","POMO4","PSSA3","QUAL3","RAPT4",
        "RDOR3","RECV3","RRRP3","SANB11","SANB4","SAPR11","SAPR4","SLCE3","SMFT3","SOMA3",
        "TAEE11","TIMS3","TOTS3","TRPL4","UGPA3","USIM4","VIVT3","YDUQ3",
        "ARRI11","BRCR11","BRCO11","BTAL11","CACR11","CVBI11","DEVA11","FEXC11","GGRC11",
        "HCTR11","HGCR11","HSML11","JSRE11","KFOF11","KNCA11","MALL11","PLCR11","PVBI11",
        "RBRL11","RBRP11","RBVA11","RBRF11","RECR11","RECT11","SARE11","SNCI11","TGAR11",
        "URPR11","VCJR11","VGIP11","VILG11","VINO11","VRTA11","XPCI11","XPPR11","XPSF11"
    ]
)))

# =============================================================================
# 14. CARREGAR DADOS DA NUVEM
# =============================================================================
def carregar_dados_nuvem():
    if not st.session_state.get("usuario_id"):
        return pd.DataFrame()
    try:
        res = supabase.table("operacoes").select("*").eq("usuario_id", st.session_state.usuario_id).execute()
        df  = pd.DataFrame(res.data)
        if not df.empty:
            df['data_operacao'] = pd.to_datetime(df['data_operacao'])
            df = df.rename(columns={
                'ticker':         'Ticker',
                'quantidade':     'Qtd',
                'preco_unitario': 'Preco_Pago',
                'data_operacao':  'Data',
                'tipo':           'Tipo'
            })

            def define_cat(t):
                t_str = str(t).strip().upper()
                if t_str.endswith('-BRL') or t_str.endswith('-USD') or t_str in LISTA_CRIPTO:
                    return "Criptomoedas"
                if t_str in LISTA_EUA:
                    return "Exterior (EUA)"
                if t_str.endswith('11') and t_str not in ACOES_FALSOS_FIIS:
                    return "FIIs"
                return "Ações"

            if 'Categoria' not in df.columns:
                df['Categoria'] = df['Ticker'].apply(define_cat)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da nuvem: {e}")
        return pd.DataFrame()

if "df_geral" not in st.session_state:
    st.session_state.df_geral = carregar_dados_nuvem()

df_geral = st.session_state.df_geral

# =============================================================================
# 15. SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.usuario_logado}")

    with st.expander("🔐 Alterar Senha"):
        n_usr = st.text_input("Novo E-mail:", value=st.session_state.usuario_logado)
        n_pwd = st.text_input("Nova Senha:", type="password")
        c_pwd = st.text_input("Confirme a Senha:", type="password")
        if st.button("Atualizar Credenciais", use_container_width=True):
            if n_pwd == c_pwd and n_pwd != "":
                try:
                    supabase.table("usuarios").update({"e-mail": n_usr, "senha": n_pwd}).eq("id", st.session_state.usuario_id).execute()
                    st.success("✅ Atualizado! Faça login novamente.")
                    time.sleep(1.5)
                    st.session_state.autenticado = False
                    st.rerun()
                except Exception:
                    st.error("Erro ao atualizar.")
            elif n_pwd != c_pwd:
                st.error("As senhas não conferem.")
            else:
                st.error("A senha não pode ser vazia.")

    if st.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

    st.divider()
    st.markdown("### 🔄 Sincronização")
    if st.button("⟳ Atualizar Cotações", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.session_state.df_geral = carregar_dados_nuvem()
        st.rerun()

    st.divider()
    st.markdown("### 🛒 Lançar Operação")
    classe_ativo = st.selectbox("Classe:", ["Bolsa (Ações/FIIs)", "Renda Fixa (CDB/Tesouro)", "Criptomoedas", "Exterior (EUA)"])
    tipo         = st.radio("Tipo:", ["Compra", "Venda"], horizontal=True)
    data_op      = st.date_input("Data:", datetime.now())

    if classe_ativo == "Bolsa (Ações/FIIs)":
        opcao_t = st.selectbox("Ativo:", ["Digitar código..."] + LISTA_COMPLETA_B3)
        t_in    = st.text_input("Código B3:").upper().strip() if opcao_t == "Digitar código..." else opcao_t
    elif classe_ativo == "Criptomoedas":
        opcao_t = st.selectbox("Ativo:", ["Digitar código..."] + LISTA_CRIPTO)
        t_in    = st.text_input("Código (Ex: ETH-BRL):").upper().strip() if opcao_t == "Digitar código..." else opcao_t
    elif classe_ativo == "Exterior (EUA)":
        opcao_t = st.selectbox("Ativo:", ["Digitar código..."] + LISTA_EUA)
        t_in    = st.text_input("Ticker EUA (Ex: AAPL):").upper().strip() if opcao_t == "Digitar código..." else opcao_t
    else:
        t_in = st.text_input("Nome (Ex: CDB Bradesco):").upper().strip()

    col_q, col_p = st.columns(2)
    with col_q:
        if classe_ativo in ["Criptomoedas", "Exterior (EUA)"]:
            q_in = st.number_input("Qtd:", min_value=0.00000001, step=0.01, format="%.8f")
        else:
            q_in = st.number_input("Qtd:", min_value=1.0, step=1.0)
    with col_p:
        p_label = "Preço Pago (em R$):" if classe_ativo == "Exterior (EUA)" else "Preço Unitário:"
        p_in    = st.number_input(p_label, min_value=0.0, step=0.01, format="%.2f")

    st.write("")
    if st.button("💾 Salvar na Nuvem", use_container_width=True):
        if t_in:
            with st.spinner("Salvando no Supabase..."):
                q_f = q_in if tipo == "Compra" else -q_in
                nova_op = {
                    "usuario_id":     st.session_state.usuario_id,
                    "ticker":         t_in.upper(),
                    "tipo":           tipo,
                    "quantidade":     float(q_f),
                    "preco_unitario": float(p_in),
                    "data_operacao":  data_op.strftime('%Y-%m-%d')
                }
                try:
                    supabase.table("operacoes").insert(nova_op).execute()
                    st.session_state.df_geral = carregar_dados_nuvem()
                    st.success(f"✅ {t_in.upper()} salvo!")
                    time.sleep(1.2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Falha ao salvar: {e}")
        else:
            st.error("Digite um código válido.")

    st.divider()
    st.markdown("### ⚙️ Configurações")
    cdi_anual  = st.number_input("CDI atual (% a.a.):", min_value=0.1, max_value=30.0, value=10.5, step=0.1) / 100
    ibov_anual = st.number_input("Meta Ibovespa (% a.a.):", min_value=0.1, max_value=50.0, value=12.0, step=0.1) / 100

# =============================================================================
# 16. MOTOR DE CONSOLIDAÇÃO
# =============================================================================
df_g = pd.DataFrame()
if not df_geral.empty:
    with st.spinner("Sincronizando carteira..."):
        df_cart = consolidar(df_geral)

        mask_bolsa  = df_cart["Categoria"].isin(["FIIs","Fiagro","FII","Ações","Acao","BDR","Criptomoedas","Exterior (EUA)"])
        lista_busca = df_cart[mask_bolsa][["Ticker","Categoria"]].values.tolist()

        m_data = buscar_multiplos(lista_busca) if lista_busca else []
        if m_data:
            df_mkt = pd.DataFrame(m_data).drop(columns=["Categoria"], errors="ignore")
            df_g   = pd.merge(df_cart, df_mkt, on="Ticker", how="left")
        else:
            df_g = df_cart.copy()

        for col in ["Preço","P_VP","P_L","Rend","Var_Dia"]:
            if col not in df_g.columns: df_g[col] = 0.0
        for col in ["DY_12M","DY_Mensal"]:
            if col not in df_g.columns: df_g[col] = "-"
        if "Status" not in df_g.columns:
            df_g["Status"] = "Offline"

        df_g["Preço"] = pd.to_numeric(df_g["Preço"], errors="coerce").fillna(0.0)
        df_g["Preço"] = df_g.apply(lambda r: r["Preco_Medio"] if r["Preço"] == 0.0 else r["Preço"], axis=1)
        df_g.fillna({"P_VP":0.0,"P_L":0.0,"Rend":0.0,"Var_Dia":0.0,"DY_12M":"-","DY_Mensal":"-","Status":"Offline"}, inplace=True)

        df_g.loc[df_g["Ticker"].str.contains("TESOURO", case=False, na=False), "Categoria"] = "Renda Fixa"

        try:
            precos_manuais = carregar_precos_manuais()
        except Exception:
            precos_manuais = {}

        mask_rf = df_g["Categoria"] == "Renda Fixa"
        if mask_rf.any():
            df_g.loc[mask_rf, "Preço"] = pd.to_numeric(df_g.loc[mask_rf, "Preco_Medio"], errors="coerce").fillna(0.0)
            if precos_manuais:
                df_g.loc[mask_rf, "Preço"] = df_g.loc[mask_rf, "Ticker"].map(precos_manuais).fillna(df_g.loc[mask_rf, "Preco_Medio"])

        df_g["Total_Atual"] = df_g["Qtd"] * df_g["Preço"]
        df_g["Custo_Pos"]   = df_g["Qtd"] * df_g["Preco_Medio"]
        df_g["Setor"]       = df_g.apply(lambda r: descobrir_setor(r["Ticker"], r["Categoria"]), axis=1)

        hoje_str = datetime.now().strftime("%Y-%m-%d")
        snap_df  = pd.DataFrame([{"Data": hoje_str, "Aportado": df_g["Custo_Pos"].sum(), "Mercado": df_g["Total_Atual"].sum()}])
        try:
            if os.path.exists(SNAPSHOT_FILE):
                df_snap_old = pd.read_csv(SNAPSHOT_FILE)
                pd.concat([df_snap_old[df_snap_old["Data"] != hoje_str], snap_df], ignore_index=True).to_csv(SNAPSHOT_FILE, index=False)
            else:
                snap_df.to_csv(SNAPSHOT_FILE, index=False)
        except Exception:
            pass

# =============================================================================
# 17. CABEÇALHO: LOGO + RELÓGIO
# =============================================================================
col_logo, col_clock = st.columns([3, 1])

with col_logo:
    st.image(URL_LOGO_OFICIAL, width=250)

with col_clock:
    import streamlit.components.v1 as components
    components.html("""
        <div style='text-align:right;padding-top:25px;'>
            <span style='font-family:"DM Mono",monospace;font-size:14px;font-weight:600;color:#f8fafc;background-color:#0f172a;padding:8px 16px;border-radius:8px;border:1px solid #1e293b;'>
                <span id='b3_dot' style='font-size:10px;vertical-align:middle;'>🔴</span>
                <span id='b3_status' style='font-size:11px;color:#94a3b8;margin-right:8px;vertical-align:middle;'>B3 FECHADA</span>
                <span id='relogio_vivo' style='vertical-align:middle;'></span>
            </span>
        </div>
        <script>
            function atualizarRelogio() {
                var agora = new Date();
                var h = agora.getHours(), dw = agora.getDay();
                document.getElementById('relogio_vivo').innerText =
                    String(h).padStart(2,'0')+':'+String(agora.getMinutes()).padStart(2,'0')+':'+String(agora.getSeconds()).padStart(2,'0');
                var dot = document.getElementById('b3_dot');
                var st  = document.getElementById('b3_status');
                if (dw >= 1 && dw <= 5 && h >= 10 && h < 17) {
                    dot.innerText='🟢'; st.innerText='B3 ABERTA'; st.style.color='#4ade80';
                } else {
                    dot.innerText='🔴'; st.innerText='B3 FECHADA'; st.style.color='#94a3b8';
                }
            }
            setInterval(atualizarRelogio, 1000);
            atualizarRelogio();
        </script>
    """, height=80)

# =============================================================================
# 18. ABAS PRINCIPAIS
# =============================================================================
tabs = st.tabs([
    "🌍 Visão Global","🏢 FIIs","📈 Ações","🌎 Exterior",
    "🛡️ Renda Fixa","🪙 Cripto","💰 Dividendos","⚖️ Rebalanceamento",
    "🔍 Radar","🧮 Simuladores","🤖 ValorPro IA","🧾 IR","🎯 Metas","📝 Histórico"
])
tab_glo,tab_fii,tab_aco,tab_ext,tab_rf,tab_cripto,tab_div,tab_reb,tab_rad,tab_sim,tab_ia,tab_ir,tab_metas,tab_edit = tabs

# =============================================================================
# ABA 1: VISÃO GLOBAL
# =============================================================================
with tab_glo:
    with st.expander("🌍 Configurar Painel de Moedas", expanded=False):
        dict_moedas = {
            "Dólar (USD)":"USDBRL=X","Euro (EUR)":"EURBRL=X",
            "Bitcoin (BTC)":"BTC-USD","Ethereum (ETH)":"ETH-USD",
            "Libra (GBP)":"GBPBRL=X","Solana (SOL)":"SOL-USD"
        }
        moedas_sel = st.multiselect("Moedas para monitorar:", options=list(dict_moedas.keys()),
                                    default=["Dólar (USD)","Bitcoin (BTC)","Solana (SOL)"])

    if moedas_sel:
        try:
            ticker_usd  = "USDBRL=X"
            tickers_dw  = list(set([dict_moedas[m] for m in moedas_sel] + [ticker_usd]))
            dados_brutos = yf.download(tickers_dw, period="2d", interval="15m")

            if isinstance(dados_brutos.columns, pd.MultiIndex):
                dados_m = dados_brutos.xs('Close', axis=1, level=0) if 'Close' in dados_brutos.columns.levels[0] else dados_brutos['Close']
            else:
                dados_m = dados_brutos['Close'] if 'Close' in dados_brutos.columns else dados_brutos

            if not dados_m.empty:
                cols_m = st.columns(len(moedas_sel))
                for i, nome in enumerate(moedas_sel):
                    ticker = dict_moedas[nome]
                    if ticker not in dados_m.columns: continue
                    serie  = dados_m[ticker].dropna()
                    val    = float(serie.iloc[-1]) if not serie.empty else 0.0
                    val_usd = 1.0
                    if ticker_usd in dados_m.columns:
                        s_usd = dados_m[ticker_usd].dropna()
                        val_usd = float(s_usd.iloc[-1]) if not s_usd.empty else 1.0
                    if "-" in ticker:
                        val = val * val_usd
                    with cols_m[i]:
                        st.markdown(f"""<div style="text-align:center;background-color:rgba(255,255,255,0.05);padding:10px;border-radius:10px;border:1px solid rgba(255,255,255,0.1);">
                            <p style="margin:0;font-size:13px;color:#94a3b8;font-weight:bold;">{nome}</p>
                            <h4 style="margin:0;font-size:19px;color:#f8fafc;">R$ {val:,.2f}</h4></div>""", unsafe_allow_html=True)
                st.divider()
        except Exception as e:
            st.error(f"🚨 Falha ao carregar moedas: {e}")

    if not df_geral.empty and not df_g.empty:
        total_alocado = df_g["Total_Atual"].sum()
        custo_total   = df_g["Custo_Pos"].sum()
        rent_v_global = ((total_alocado - custo_total) / custo_total * 100) if custo_total > 0 else 0.0

        try:
            total_pendente = df_proventos[df_proventos['Status'] == 'Pendente']['Valor'].sum()
        except Exception:
            total_pendente = 0.0

        st.markdown("#### 📊 Resumo de Patrimônio Alocado")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("🏢 FIIs",     f"R$ {df_g[df_g['Categoria'].isin(['FIIs','Fiagro'])]['Total_Atual'].sum():,.2f}")
        mc2.metric("📈 Ações",    f"R$ {df_g[df_g['Categoria'].isin(['Ações','BDR'])]['Total_Atual'].sum():,.2f}")
        mc3.metric("🌎 Exterior", f"R$ {df_g[df_g['Categoria']=='Exterior (EUA)']['Total_Atual'].sum():,.2f}")
        st.write("")
        mc4, mc5, mc6 = st.columns(3)
        mc4.metric("🛡️ Renda Fixa", f"R$ {df_g[df_g['Categoria']=='Renda Fixa']['Total_Atual'].sum():,.2f}")
        mc5.metric("🪙 Cripto",      f"R$ {df_g[df_g['Categoria']=='Criptomoedas']['Total_Atual'].sum():,.2f}")
        mc6.metric("💎 Total Geral", f"R$ {total_alocado + total_pendente:,.2f}", delta=f"{rent_v_global:+.2f}%")

        if total_pendente > 0:
            st.caption(f"ℹ️ Inclui **R$ {total_pendente:,.2f}** de proventos pendentes.")

        st.divider()
        st.markdown("#### 🔍 Detalhamento da Carteira")
        todas_cats = sorted(df_g['Categoria'].unique().tolist())
        cats_sel   = st.multiselect("Filtrar:", options=todas_cats, default=todas_cats)
        df_v_filt  = df_g[df_g['Categoria'].isin(cats_sel)].copy()

        col_p, col_t = st.columns([1.5, 2.5])
        with col_p:
            st.markdown("##### Distribuição")
            fig_p = px.pie(df_v_filt, values="Total_Atual", names="Ticker", hole=0.55)
            fig_p.update_layout(height=350, showlegend=True, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_p, use_container_width=True)
        with col_t:
            st.markdown("##### Ativos")
            st.dataframe(df_v_filt[["Ticker","Qtd","Preço","Total_Atual"]].sort_values("Total_Atual", ascending=False),
                         hide_index=True, use_container_width=True)

        st.markdown("---")
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown("### 📊 Rentabilidade vs Indicadores")
            total_aportado    = df_g["Custo_Pos"].sum()
            total_mercado     = df_g["Total_Atual"].sum()
            rent_carteira     = (total_mercado / total_aportado) - 1 if total_aportado > 0 else 0
            df_comp = pd.DataFrame({
                "Indicador":        ["Minha Carteira","CDI","B3 (Meta Ibov)"],
                "Rentabilidade (%)": [rent_carteira, cdi_anual, ibov_anual]
            })
            fig_comp = px.bar(df_comp, x="Indicador", y="Rentabilidade (%)", text="Rentabilidade (%)",
                              color="Indicador", color_discrete_sequence=["#3b82f6","#10b981","#f59e0b"])
            fig_comp.update_traces(texttemplate='%{text:.2%}', textposition='outside')
            fig_comp.update_layout(yaxis_tickformat='.1%', showlegend=False, margin=dict(t=30,b=0,l=0,r=0))
            st.plotly_chart(fig_comp, use_container_width=True)

        with col_graf2:
            st.markdown("### 📈 Evolução Patrimonial")
            if os.path.exists(SNAPSHOT_FILE):
                try:
                    df_hist = pd.read_csv(SNAPSHOT_FILE)
                    if len(df_hist) > 0:
                        fig_hist = px.line(df_hist, x="Data", y=["Aportado","Mercado"],
                                           markers=True, color_discrete_sequence=["#94a3b8","#10b981"])
                        fig_hist.update_layout(margin=dict(t=30,b=0,l=0,r=0), legend_title_text="Legenda")
                        st.plotly_chart(fig_hist, use_container_width=True)
                except Exception:
                    st.info("Histórico em construção.")
            else:
                st.info("O gráfico aparecerá após o primeiro salvamento.")
    else:
        st.info("Lance suas operações para ver o patrimônio.")

# =============================================================================
# ABA 2: FIIs
# =============================================================================
with tab_fii:
    with st.expander("ℹ️ Como usar a Análise de FIIs", expanded=False):
        st.markdown("Analise P/VP, Dividend Yield e rendimento mensal dos seus Fundos Imobiliários.")

    if not df_g.empty:
        f = df_g[df_g["Categoria"].isin(["FII","FIIs","Fiagro"])].copy()
        if not f.empty:
            f["Rend"]         = pd.to_numeric(f["Rend"], errors="coerce").fillna(0)
            f["Renda Mensal"] = f["Qtd"] * f["Rend"]

            m1, m2, m3, col_pie_fii = st.columns([1,1,1,1.2])
            m1.metric("💰 Patrimônio FIIs",  f"R$ {f['Total_Atual'].sum():,.2f}")
            m2.metric("💸 Renda Mensal Est.", f"R$ {f['Renda Mensal'].sum():,.2f}")
            lp_fii = (f["Total_Atual"] - f["Custo_Pos"]).sum()
            ct_fii = f["Custo_Pos"].sum()
            m3.metric("📈 Valorização", f"R$ {lp_fii:,.2f}", f"{lp_fii/ct_fii*100:+.2f}%" if ct_fii > 0 else "")

            with col_pie_fii:
                fig_pf = px.pie(f, values="Total_Atual", names="Ticker", hole=0.4,
                                color_discrete_sequence=px.colors.qualitative.Set2)
                fig_pf.update_traces(textposition='inside', textinfo='percent', insidetextorientation='horizontal')
                fig_pf.update_layout(height=220, margin=dict(t=10,b=10,l=10,r=10), showlegend=False)
                st.plotly_chart(fig_pf, use_container_width=True)

            f["L/P (R$)"] = f["Total_Atual"] - f["Custo_Pos"]
            f["L/P (%)"]  = f.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)

            df_vf = f[["Ticker","Setor","Qtd","Preco_Medio","Preço","Var_Dia","Total_Atual",
                        "L/P (R$)","L/P (%)","P_VP","Rend","Renda Mensal","DY_12M","DY_Mensal","Status"]].copy()
            df_vf.rename(columns={"Preco_Medio":"PM (R$)","Preço":"Atual","Var_Dia":"Var. Dia %",
                                   "Total_Atual":"Patrimônio","Rend":"Rend/Cota",
                                   "DY_12M":"DY 12M","DY_Mensal":"DY Mensal"}, inplace=True)
            df_vf["Var. Dia %"] = df_vf["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
            df_vf["L/P (R$)"]   = df_vf["L/P (R$)"].apply(formatar_delta)
            df_vf["L/P (%)"]    = df_vf["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_vf["Qtd"]        = df_vf["Qtd"].apply(formatar_qtd)
            st.dataframe(df_vf, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum FII registrado.")
    else:
        st.info("Sua carteira está vazia.")

# =============================================================================
# ABA 3: AÇÕES
# =============================================================================
with tab_aco:
    with st.expander("ℹ️ Como usar a Análise de Ações", expanded=False):
        st.markdown("Acompanhe P/L, P/VP e valorização das suas ações brasileiras.")

    if not df_g.empty:
        a = df_g[df_g["Categoria"].isin(["Acao","Ações","BDR"])].copy()
        if not a.empty:
            m1, m2, col_vaz, col_pie_aco = st.columns([1,1,1,1.2])
            lp_aco = (a["Total_Atual"] - a["Custo_Pos"]).sum()
            ct_aco = a["Custo_Pos"].sum()
            m1.metric("💰 Patrimônio Ações", f"R$ {a['Total_Atual'].sum():,.2f}")
            m2.metric("📈 Valorização", f"R$ {lp_aco:,.2f}", f"{lp_aco/ct_aco*100:+.2f}%" if ct_aco > 0 else "")

            with col_pie_aco:
                fig_pa = px.pie(a, values="Total_Atual", names="Ticker", hole=0.4,
                                color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pa.update_traces(textposition='inside', textinfo='percent', insidetextorientation='horizontal')
                fig_pa.update_layout(height=220, margin=dict(t=10,b=10,l=10,r=10), showlegend=False)
                st.plotly_chart(fig_pa, use_container_width=True)

            a["L/P (R$)"] = a["Total_Atual"] - a["Custo_Pos"]
            a["L/P (%)"]  = a.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)

            df_va = a[["Ticker","Setor","Qtd","Preco_Medio","Preço","Var_Dia","Total_Atual",
                        "L/P (R$)","L/P (%)","P_VP","P_L","DY_12M","Status"]].copy()
            df_va.rename(columns={"Preco_Medio":"PM (R$)","Preço":"Atual","Var_Dia":"Var. Dia %",
                                   "Total_Atual":"Patrimônio","P_VP":"P/VP","P_L":"P/L","DY_12M":"DY 12M"}, inplace=True)
            df_va["Var. Dia %"] = df_va["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
            df_va["L/P (R$)"]   = df_va["L/P (R$)"].apply(formatar_delta)
            df_va["L/P (%)"]    = df_va["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_va["Qtd"]        = df_va["Qtd"].apply(formatar_qtd)
            st.dataframe(df_va, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma Ação registrada.")
    else:
        st.info("Sua carteira está vazia.")

# =============================================================================
# ABA 4: EXTERIOR (EUA)
# =============================================================================
with tab_ext:
    with st.expander("ℹ️ Como usar a aba de Exterior", expanded=False):
        st.markdown("Acompanhe suas ações, ETFs e REITs americanos em reais.")

    if not df_g.empty:
        ext = df_g[df_g["Categoria"] == "Exterior (EUA)"].copy()
        if not ext.empty:
            ext.fillna({"Status":"🌎 Global","Var_Dia":0.0}, inplace=True)
            lp_ext = (ext["Total_Atual"] - ext["Custo_Pos"]).sum()
            ct_ext = ext["Custo_Pos"].sum()
            m1, m2, col_vaz, col_pie_ext = st.columns([1,1,1,1.2])
            m1.metric("🌎 Patrimônio EUA", f"R$ {ext['Total_Atual'].sum():,.2f}")
            m2.metric("📈 Valorização", f"R$ {lp_ext:,.2f}", f"{lp_ext/ct_ext*100:+.2f}%" if ct_ext > 0 else "")

            with col_pie_ext:
                fig_ext = px.pie(ext, values="Total_Atual", names="Ticker", hole=0.4,
                                 color_discrete_sequence=["#1d4ed8","#2563eb","#3b82f6","#60a5fa"])
                fig_ext.update_traces(textposition='inside', textinfo='percent', insidetextorientation='horizontal')
                fig_ext.update_layout(height=220, margin=dict(t=10,b=10,l=10,r=10), showlegend=False)
                st.plotly_chart(fig_ext, use_container_width=True)

            ext["L/P (R$)"] = ext["Total_Atual"] - ext["Custo_Pos"]
            ext["L/P (%)"]  = ext.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)

            df_vext = ext[["Ticker","Setor","Qtd","Preco_Medio","Preço","Var_Dia","Total_Atual","L/P (R$)","L/P (%)","Status"]].copy()
            df_vext.rename(columns={"Preco_Medio":"PM (R$)","Preço":"Atual (R$)",
                                     "Var_Dia":"Var. Dia %","Total_Atual":"Patrimônio (R$)"}, inplace=True)
            df_vext["Var. Dia %"] = df_vext["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
            df_vext["L/P (R$)"]   = df_vext["L/P (R$)"].apply(formatar_delta)
            df_vext["L/P (%)"]    = df_vext["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_vext["Qtd"]        = df_vext["Qtd"].apply(formatar_qtd)
            st.dataframe(df_vext, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma Ação do Exterior registrada.")
    else:
        st.info("Sua carteira está vazia.")

# =============================================================================
# ABA 5: RENDA FIXA
# =============================================================================
with tab_rf:
    with st.expander("ℹ️ Como usar a aba de Renda Fixa", expanded=False):
        st.markdown("Acompanhe CDBs, Tesouro Direto, LCI, LCA e outros títulos de renda fixa.")

    if not df_g.empty:
        crf = df_g[df_g["Categoria"] == "Renda Fixa"].copy()
        if not crf.empty:
            crf["L/P (R$)"] = crf["Total_Atual"] - crf["Custo_Pos"]
            crf["L/P (%)"]  = crf.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)
            df_vrf = crf[["Ticker","Qtd","Preco_Medio","Preço","Total_Atual","L/P (R$)","L/P (%)"]].copy()
            df_vrf.rename(columns={"Ticker":"Aplicação","Preco_Medio":"Custo Unit.",
                                    "Preço":"Valor Atual","Total_Atual":"Patrimônio (R$)"}, inplace=True)
            df_vrf["L/P (R$)"] = df_vrf["L/P (R$)"].apply(formatar_delta)
            df_vrf["L/P (%)"]  = df_vrf["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_vrf["Qtd"]      = df_vrf["Qtd"].apply(formatar_qtd)
            st.dataframe(df_vrf, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma Renda Fixa cadastrada.")
    else:
        st.info("Sua carteira está vazia.")

# =============================================================================
# ABA 6: CRIPTOMOEDAS
# =============================================================================
with tab_cripto:
    with st.expander("ℹ️ Como usar a aba de Criptomoedas", expanded=False):
        st.markdown("Acompanhe Bitcoin, Ethereum e outras criptos com cotação 24h.")

    if not df_g.empty:
        criptos = df_g[df_g["Categoria"] == "Criptomoedas"].copy()
        if not criptos.empty:
            criptos.fillna({"Status":"⚡ Volátil","Var_Dia":0.0}, inplace=True)
            lp_cripto = (criptos["Total_Atual"] - criptos["Custo_Pos"]).sum()
            ct_cripto = criptos["Custo_Pos"].sum()
            m1, m2, col_vaz, col_pie_cripto = st.columns([1,1,1,1.2])
            m1.metric("🪙 Patrimônio Cripto", f"R$ {criptos['Total_Atual'].sum():,.2f}")
            m2.metric("📈 Valorização", f"R$ {lp_cripto:,.2f}", f"{lp_cripto/ct_cripto*100:+.2f}%" if ct_cripto > 0 else "")

            with col_pie_cripto:
                fig_cripto = px.pie(criptos, values="Total_Atual", names="Ticker", hole=0.4,
                                    color_discrete_sequence=["#eab308","#ca8a04","#854d0e"])
                fig_cripto.update_traces(textposition='inside', textinfo='percent', insidetextorientation='horizontal')
                fig_cripto.update_layout(height=220, margin=dict(t=10,b=10,l=10,r=10),
                                         showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_cripto, use_container_width=True)

            criptos["L/P (R$)"] = criptos["Total_Atual"] - criptos["Custo_Pos"]
            criptos["L/P (%)"]  = criptos.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)

            df_vcripto = criptos[["Ticker","Qtd","Preco_Medio","Custo_Pos","Preço","Var_Dia",
                                   "Total_Atual","L/P (R$)","L/P (%)","Status"]].copy()
            df_vcripto.rename(columns={"Preco_Medio":"PM (1 Moeda)","Custo_Pos":"Total Investido (R$)",
                                        "Preço":"Preço Atual","Var_Dia":"Var. Dia %","Total_Atual":"Patrimônio (R$)"}, inplace=True)
            df_vcripto["Var. Dia %"]          = df_vcripto["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
            df_vcripto["L/P (R$)"]            = df_vcripto["L/P (R$)"].apply(formatar_delta)
            df_vcripto["L/P (%)"]             = df_vcripto["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_vcripto["Total Investido (R$)"] = df_vcripto["Total Investido (R$)"].apply(lambda x: f"R$ {x:,.2f}")
            df_vcripto["PM (1 Moeda)"]        = df_vcripto["PM (1 Moeda)"].apply(lambda x: f"R$ {x:,.2f}")
            df_vcripto["Preço Atual"]         = df_vcripto["Preço Atual"].apply(lambda x: f"R$ {x:,.2f}")
            df_vcripto["Patrimônio (R$)"]     = df_vcripto["Patrimônio (R$)"].apply(lambda x: f"R$ {x:,.2f}")
            df_vcripto["Qtd"]                 = df_vcripto["Qtd"].apply(formatar_qtd)
            st.dataframe(df_vcripto, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma Criptomoeda registrada.")
    else:
        st.info("Sua carteira está vazia.")

# =============================================================================
# ABA 7: DIVIDENDOS
# =============================================================================
with tab_div:
    with st.expander("ℹ️ Como usar o painel de Dividendos", expanded=False):
        st.markdown("Registre recebimentos, veja histórico e projete a bola de neve dos dividendos.")

    st.markdown("#### 💰 Registro de Renda Passiva")
    try:
        df_divs = carregar_dividendos()
    except Exception:
        df_divs = pd.DataFrame()

    with st.expander("➕ Lançar novo recebimento", expanded=df_divs.empty):
        cd1, cd2, cd3, cd4, cd5 = st.columns([1,1.2,1,1,0.8])
        with cd1: d_data = st.date_input("Data:", datetime.now(), key="div_dt")
        with cd2:
            opcao_d = st.selectbox("Ativo:", ["Digitar..."] + LISTA_COMPLETA_B3, key="div_sel")
            d_tick  = st.text_input("Código:", key="div_inp").upper() if opcao_d == "Digitar..." else opcao_d
        with cd3: d_val  = st.number_input("Valor Total (R$):", min_value=0.01, step=1.0, key="div_val")
        with cd4: d_tipo = st.selectbox("Tipo:", ["Rendimento FII","Dividendo","JCP","Outro"], key="div_tipo")
        with cd5:
            st.write(""); st.write("")
            if st.button("Lançar", use_container_width=True, key="div_btn"):
                if d_tick:
                    novo = pd.DataFrame([{"Data": d_data, "Ticker": d_tick.upper(), "Valor": d_val, "Tipo": d_tipo}])
                    df_div_ok = pd.concat([df_divs, novo], ignore_index=True) if not df_divs.empty else novo
                    try:
                        df_div_ok.to_csv(DIVIDENDOS_FILE, index=False)
                        st.success("✅ Registrado!")
                        time.sleep(0.8)
                        st.rerun()
                    except Exception:
                        pass
                else:
                    st.error("Preencha o ativo.")

    if not df_divs.empty:
        df_divs["Data"] = pd.to_datetime(df_divs["Data"])
        df_divs["Mês"]  = df_divs["Data"].dt.to_period("M").astype(str)
        total_div = df_divs["Valor"].sum()
        media_div = df_divs.groupby("Mês")["Valor"].sum().mean()

        dm1, dm2, dm3 = st.columns(3)
        dm1.metric("💰 Total Acumulado", f"R$ {total_div:,.2f}")
        dm2.metric("📆 Média Mensal",    f"R$ {media_div:,.2f}")
        dm3.metric("📋 Pagamentos",      str(len(df_divs)))

        df_grp  = df_divs.groupby(["Mês","Tipo"])["Valor"].sum().reset_index()
        fig_div = px.bar(df_grp, x="Mês", y="Valor", color="Tipo", text_auto=".2f",
                         color_discrete_sequence=["#3b82f6","#22c55e","#f59e0b","#a855f7"])
        fig_div.update_layout(height=300, title="Renda Passiva Mensal por Tipo", barmode="stack")
        st.plotly_chart(fig_div, use_container_width=True)

        with st.expander("📋 Extrato completo"):
            st.dataframe(df_divs.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum dividendo registrado.")

    st.divider()
    st.markdown("#### 🔮 Efeito Bola de Neve (Próximos 12 Meses)")
    renda_mensal_estimada = 0.0
    if not df_g.empty:
        df_renda = df_g[df_g["Categoria"].isin(["FIIs","Fiagro","FII"])].copy()
        if not df_renda.empty and "Rend" in df_renda.columns:
            renda_mensal_estimada = (pd.to_numeric(df_renda["Qtd"], errors="coerce") *
                                     pd.to_numeric(df_renda["Rend"], errors="coerce")).sum()

    if renda_mensal_estimada > 0:
        meses_proj  = [(datetime.now() + pd.DateOffset(months=i)).strftime("%b/%Y") for i in range(1, 13)]
        valores_proj = [renda_mensal_estimada * ((1.005)**i) for i in range(13)][1:]
        df_proj = pd.DataFrame({"Mês": meses_proj, "Renda Projetada (R$)": valores_proj})
        fig_proj = px.bar(df_proj, x="Mês", y="Renda Projetada (R$)", text_auto=".2f",
                          color_discrete_sequence=["#10b981"])
        fig_proj.update_layout(height=280)
        st.plotly_chart(fig_proj, use_container_width=True)
        st.info(f"💡 Projeção média de **R$ {renda_mensal_estimada:,.2f}** no próximo mês.")
    else:
        st.info("Adicione FIIs para ativar a projeção.")

# =============================================================================
# ABA 8: REBALANCEAMENTO
# =============================================================================
with tab_reb:
    with st.expander("ℹ️ Como usar o Rebalanceamento", expanded=False):
        st.markdown("Defina pesos por classe e veja onde aportar o próximo investimento.")

    st.markdown("#### ⚖️ Rebalanceamento Inteligente")
    if not df_geral.empty and not df_g.empty:
        cr1, cr2, cr3, cr4, cr5 = st.columns(5)
        with cr1: meta_aco    = st.number_input("Alvo Ações (%):",   0, 100, 30, key="rb_aco")
        with cr2: meta_fii    = st.number_input("Alvo FIIs (%):",    0, 100, 30, key="rb_fii")
        with cr3: meta_rf     = st.number_input("Alvo R. Fixa (%):", 0, 100, 20, key="rb_rf")
        with cr4: meta_ext    = st.number_input("Alvo EUA (%):",     0, 100, 10, key="rb_ext")
        with cr5: meta_cripto = st.number_input("Alvo Cripto (%):",  0, 100, 10, key="rb_cripto")

        aporte = st.number_input("💵 Novo aporte disponível (R$):", min_value=0.0, step=100.0, value=1000.0)
        soma   = meta_aco + meta_fii + meta_rf + meta_ext + meta_cripto

        if soma != 100:
            st.error(f"⚠️ A soma deve ser 100%. Atual: {soma}%")
        else:
            if st.button("🎯 Calcular Aporte Ideal", type="primary"):
                df_rb      = df_g.copy()
                atual_aco  = df_rb[df_rb["Categoria"].isin(["Ação","Ações","Acao","BDR"])]["Total_Atual"].sum()
                atual_fii  = df_rb[df_rb["Categoria"].isin(["FII","FIIs","Fiagro"])]["Total_Atual"].sum()
                atual_rf   = df_rb[df_rb["Categoria"] == "Renda Fixa"]["Total_Atual"].sum()
                atual_ext  = df_rb[df_rb["Categoria"] == "Exterior (EUA)"]["Total_Atual"].sum()
                atual_cripto = df_rb[df_rb["Categoria"] == "Criptomoedas"]["Total_Atual"].sum()

                pat_futuro  = atual_aco + atual_fii + atual_rf + atual_ext + atual_cripto + aporte
                alvo_aco    = pat_futuro * (meta_aco    / 100)
                alvo_fii    = pat_futuro * (meta_fii    / 100)
                alvo_rf     = pat_futuro * (meta_rf     / 100)
                alvo_ext    = pat_futuro * (meta_ext    / 100)
                alvo_cripto = pat_futuro * (meta_cripto / 100)

                falta_aco    = max(0, alvo_aco    - atual_aco)
                falta_fii    = max(0, alvo_fii    - atual_fii)
                falta_rf     = max(0, alvo_rf     - atual_rf)
                falta_ext    = max(0, alvo_ext    - atual_ext)
                falta_cripto = max(0, alvo_cripto - atual_cripto)
                total_falta  = falta_aco + falta_fii + falta_rf + falta_ext + falta_cripto

                st.markdown("---")
                if total_falta > 0:
                    st.success("🎯 Sugestão de aporte:")
                    rca1, rca2, rca3, rca4, rca5 = st.columns(5)
                    rca1.metric("📈 Ações",    f"R$ {(falta_aco    / total_falta) * aporte:,.2f}")
                    rca2.metric("🏢 FIIs",     f"R$ {(falta_fii    / total_falta) * aporte:,.2f}")
                    rca3.metric("🛡️ R. Fixa",  f"R$ {(falta_rf     / total_falta) * aporte:,.2f}")
                    rca4.metric("🌎 EUA",      f"R$ {(falta_ext    / total_falta) * aporte:,.2f}")
                    rca5.metric("🪙 Cripto",   f"R$ {(falta_cripto / total_falta) * aporte:,.2f}")

                    df_comp = pd.DataFrame({
                        "Classe": ["Ações","FIIs","Renda Fixa","EUA","Cripto"] * 2,
                        "Tipo":   ["Atual"] * 5 + ["Alvo"] * 5,
                        "Valor":  [atual_aco, atual_fii, atual_rf, atual_ext, atual_cripto,
                                   alvo_aco, alvo_fii, alvo_rf, alvo_ext, alvo_cripto]
                    })
                    fig_rb = px.bar(df_comp, x="Classe", y="Valor", color="Tipo", barmode="group",
                                    color_discrete_map={"Atual":"#3b82f6","Alvo":"#22c55e"})
                    fig_rb.update_layout(height=280, title="Comparativo Atual vs Alvo")
                    st.plotly_chart(fig_rb, use_container_width=True)
                else:
                    st.info("✅ Carteira já alinhada!")
    else:
        st.info("Cadastre ativos primeiro.")

# =============================================================================
# ABA 9: RADAR
# =============================================================================
with tab_rad:
    with st.expander("ℹ️ Como usar o Radar de Mercado", expanded=False):
        st.markdown("Pesquise qualquer ativo da B3 em tempo real e compare fundamentos.")

    st.markdown("#### 🔍 Central de Pesquisa")
    ativos_sel = st.multiselect("Selecione ativos:", LISTA_COMPLETA_B3)
    extras     = st.text_input("Outros códigos (separados por vírgula):")

    if st.button("🔎 Buscar", type="primary"):
        lista = list(set(ativos_sel + [t.strip().upper() for t in extras.split(",") if t.strip()]))
        if lista:
            with st.spinner("Buscando dados em tempo real..."):
                res = buscar_multiplos(lista)
            if res:
                df_res  = pd.DataFrame(res)
                fiis    = df_res[df_res["Categoria"].isin(["FIIs","Fiagro"])].copy()
                acos    = df_res[df_res["Categoria"].isin(["Ações","BDR"])].copy()
                criptos = df_res[df_res["Categoria"] == "Criptomoedas"].copy()

                if not fiis.empty:
                    st.markdown("##### 🏢 FIIs e Fiagros")
                    fiis.rename(columns={"Rend":"Rend/Cota","DY_12M":"DY 12M","DY_Mensal":"DY Mensal",
                                          "P_VP":"P/VP","Var_Dia":"Var. Dia %"}, inplace=True)
                    fiis["Var. Dia %"] = fiis["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
                    st.dataframe(fiis[["Ticker","Preço","Var. Dia %","P/VP","DY 12M","DY Mensal","Rend/Cota","Status"]],
                                 hide_index=True, use_container_width=True)
                if not acos.empty:
                    st.markdown("##### 📈 Ações e BDRs")
                    acos.rename(columns={"DY_12M":"DY 12M","P_VP":"P/VP","P_L":"P/L","Var_Dia":"Var. Dia %"}, inplace=True)
                    acos["Var. Dia %"] = acos["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
                    st.dataframe(acos[["Ticker","Preço","Var. Dia %","P/VP","P/L","DY 12M","Status"]],
                                 hide_index=True, use_container_width=True)
                if not criptos.empty:
                    st.markdown("##### 🪙 Criptomoedas")
                    criptos.rename(columns={"Var_Dia":"Var. Dia %"}, inplace=True)
                    criptos["Var. Dia %"] = criptos["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
                    st.dataframe(criptos[["Ticker","Preço","Var. Dia %","Status"]],
                                 hide_index=True, use_container_width=True)
            else:
                st.warning("Nenhum ativo encontrado.")
        else:
            st.warning("Selecione pelo menos um ativo.")

# =============================================================================
# ABA 10: SIMULADORES
# =============================================================================
with tab_sim:
    with st.expander("ℹ️ Como usar os Simuladores", expanded=False):
        st.markdown("Projete juros compostos, renda alvo e calcule DARFs de forma rápida.")

    st.markdown("#### 🧮 Laboratório de Projeções")
    s1, s2, s3, s4 = st.tabs(["⚡ Simulador Rápido","📈 Juros Compostos","🎯 Renda Alvo","🧾 Calc. DARF"])

    with s1:
        sc1, sc2 = st.columns([1.2, 1])
        with sc1:
            op_sim = st.selectbox("Ativo:", ["Digitar..."] + LISTA_COMPLETA_B3, key="sim_box")
            tk_sim = st.text_input("Código:", key="sim_txt").upper().strip() if op_sim == "Digitar..." else op_sim
        with sc2:
            tipo_s = st.radio("Basear em:", ["Montante (R$)","Quantidade (Cotas)"], horizontal=True)

        if tk_sim:
            with st.spinner(f"Buscando {tk_sim}..."):
                info_s = buscar_mercado(tk_sim)
            if info_s and info_s["Preço"] > 0:
                pc, rc = info_s["Preço"], info_s["Rend"]
                ia1, ia2 = st.columns(2)
                ia1.info(f"🏷️ Preço: **R$ {pc:.2f}**")
                ia2.info(f"💸 Dividendo: **R$ {rc:.4f}** ({info_s['DY_Mensal']} a.m.)")
                if tipo_s == "Montante (R$)":
                    val = st.number_input("Disponível (R$):", min_value=0.0, value=1000.0, step=100.0)
                    if val > 0:
                        q = int(val / pc)
                        st.write(f"💼 Cotas: **{q}** | Sobra: **R$ {val - q*pc:.2f}**")
                        if rc > 0: st.success(f"🚀 Renda Mensal: **R$ {q*rc:,.2f}**")
                else:
                    q = st.number_input("Meta de Cotas:", min_value=1, value=100)
                    st.write(f"💳 Desembolso: **R$ {q*pc:,.2f}**")
                    if rc > 0: st.success(f"🚀 Renda Mensal: **R$ {q*rc:,.2f}**")
            else:
                st.error("Ativo offline.")

    with s2:
        jc1, jc2, jc3 = st.columns(3)
        with jc1: ap_ini = st.number_input("Aporte Inicial (R$):", 0.0, value=1000.0, step=100.0)
        with jc2: ap_mes = st.number_input("Aporte Mensal (R$):",  0.0, value=500.0,  step=50.0)
        with jc3: tx_mes = st.number_input("Rendimento (% a.m.):", 0.1, value=0.8,    step=0.1)
        anos_j  = st.slider("Horizonte (anos):", 1, 35, 10)
        meses_j = anos_j * 12
        pat = ap_ini; inv = ap_ini; tx = tx_mes / 100
        hs_m, hs_i, hs_j = [], [], []
        for mes in range(1, meses_j + 1):
            pat += pat * tx + ap_mes; inv += ap_mes
            if mes % 12 == 0:
                hs_m.append(f"Ano {mes//12}"); hs_i.append(inv); hs_j.append(pat - inv)
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("💵 Investido Total",    f"R$ {inv:,.2f}")
        rc2.metric("📈 Juros Acumulados",   f"R$ {pat - inv:,.2f}")
        rc3.metric("🏆 Patrimônio Final",   f"R$ {pat:,.2f}")
        df_jc  = pd.DataFrame({"Ano": hs_m, "Investido": hs_i, "Juros": hs_j})
        fig_jc = px.bar(df_jc, x="Ano", y=["Investido","Juros"], barmode="stack",
                        color_discrete_map={"Investido":"#3b82f6","Juros":"#22c55e"})
        fig_jc.update_layout(height=300)
        st.plotly_chart(fig_jc, use_container_width=True)

    with s3:
        ra1, ra2, ra3 = st.columns(3)
        with ra1: meta_r  = st.number_input("Renda Alvo (R$/mês):",  min_value=10.0, value=1000.0, step=100.0)
        with ra2: preco_r = st.number_input("Preço da Cota (R$):",   min_value=1.0,  value=9.50,   step=0.50)
        with ra3: rend_r  = st.number_input("Dividendo Mensal (R$):", min_value=0.01, value=0.09,   step=0.01)
        if rend_r > 0:
            cotas_n = meta_r / rend_r
            st.success(f"🎯 Acumule **{int(cotas_n)} cotas**.")
            st.info(f"💼 Patrimônio Alvo: **R$ {cotas_n * preco_r:,.2f}**")

    with s4:
        st.markdown("#### 🧾 Simulador de Venda e Cálculo de DARF")
        sd1, sd2, sd3 = st.columns(3)
        with sd1: cat_venda    = st.selectbox("O que você vendeu?", ["Ações (B3)","FIIs","Criptomoedas"])
        with sd2: total_venda  = st.number_input("Total Vendido no Mês (R$):", min_value=0.0)
        with sd3: lucro_venda  = st.number_input("Lucro Líquido Realizado (R$):", min_value=0.0)

        if st.button("🧮 Calcular Imposto", type="primary"):
            imposto = 0.0; msg = ""
            if cat_venda == "Ações (B3)":
                if total_venda <= 20000:
                    msg = "✅ **ISENTO.** Vendas abaixo de R$ 20k no mês."
                else:
                    imposto = lucro_venda * 0.15
                    msg = f"🚨 **DARF DEVIDO (15%): R$ {imposto:,.2f}** | Cód 6015"
            elif cat_venda == "FIIs":
                imposto = lucro_venda * 0.20
                msg = f"🚨 **DARF DEVIDO (20%): R$ {imposto:,.2f}** | Cód 6015"
            elif cat_venda == "Criptomoedas":
                if total_venda <= 35000:
                    msg = "✅ **ISENTO.** Vendas abaixo de R$ 35k no mês."
                else:
                    imposto = lucro_venda * 0.15
                    msg = f"🚨 **DARF DEVIDO (15%): R$ {imposto:,.2f}**"
            st.markdown("---")
            if imposto > 0: st.error(msg)
            else: st.success(msg)

# =============================================================================
# ABA 11: VALORPRO IA
# =============================================================================
with tab_ia:
    with st.expander("ℹ️ Como conversar com a ValorPro IA", expanded=False):
        st.markdown("Faça perguntas sobre sua carteira, ativos ou estratégias de investimento.")

    st.markdown("#### 🤖 ValorPro IA Intelligence")
    ARQUIVO_CHAT = "historico_ia.json"

    if st.session_state.get('tipo_acesso') != "premium":
        exibir_bloqueio_premium("ValorPro IA Intelligence")
    else:
        col_ia1, col_ia2 = st.columns([4, 1])
        with col_ia2:
            if st.button("🗑️ Apagar Histórico", use_container_width=True):
                st.session_state.mensagens_ia = []
                if "chat_ia" in st.session_state: del st.session_state["chat_ia"]
                try: os.remove(ARQUIVO_CHAT)
                except Exception: pass
                st.rerun()

        if "mensagens_ia" not in st.session_state:
            try:
                with open(ARQUIVO_CHAT, "r", encoding="utf-8") as f:
                    st.session_state.mensagens_ia = json.load(f)
            except Exception:
                st.session_state.mensagens_ia = []

        if "chat_ia" not in st.session_state and ia_pronta:
            try:
                hist_gemini = [
                    {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
                    for msg in st.session_state.mensagens_ia
                ]
                st.session_state.chat_ia = model.start_chat(history=hist_gemini)
            except Exception as e:
                st.error(f"Erro ao iniciar chat: {e}")

        for msg in st.session_state.mensagens_ia:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if ia_pronta:
            if prompt := st.chat_input("Converse com seu assessor financeiro..."):
                st.session_state.mensagens_ia.append({"role": "user", "content": prompt})
                try:
                    with open(ARQUIVO_CHAT, "w", encoding="utf-8") as f:
                        json.dump(st.session_state.mensagens_ia, f, ensure_ascii=False, indent=4)
                except Exception: pass

                with st.chat_message("user"): st.markdown(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Analisando..."):
                        try:
                            ctx = df_g.to_string() if not df_g.empty else "Carteira vazia."
                            prompt_invisivel = (
                                "Instrução: Você é o ValorPro IA, assessor financeiro de elite. "
                                "Responda em Português do Brasil de forma clara e objetiva.\n\n"
                                f"[CARTEIRA DO CLIENTE]\n{ctx}\n\n"
                                f"Pergunta: {prompt}"
                            )
                            resposta = st.session_state.chat_ia.send_message(prompt_invisivel)
                            st.markdown(resposta.text)
                            st.session_state.mensagens_ia.append({"role": "assistant", "content": resposta.text})
                            try:
                                with open(ARQUIVO_CHAT, "w", encoding="utf-8") as f:
                                    json.dump(st.session_state.mensagens_ia, f, ensure_ascii=False, indent=4)
                            except Exception: pass
                        except Exception as e:
                            st.error(f"Erro na IA: {e}")
        else:
            st.warning("⚠️ Configure sua chave GEMINI_CHAVE nos secrets para ativar a IA.")

# =============================================================================
# ABA 12: IMPOSTO DE RENDA
# =============================================================================
with tab_ir:
    with st.expander("ℹ️ Como usar a aba de Imposto de Renda", expanded=False):
        st.markdown("Organize seus bens e direitos para a declaração anual com textos prontos.")

    st.markdown("#### 🧾 Gestão Fiscal de Bens e Direitos")
    col_ir1, col_ir2 = st.columns([2, 1])
    with col_ir2:
        st.info("""
        **📌 Regras de Isenção (Vendas/Mês)**
        * **Ações:** Isento até R$ 20.000,00
        * **Cripto:** Isento até R$ 35.000,00
        * **FIIs:** SEM ISENÇÃO (20% sobre lucro)
        """)
    with col_ir1:
        anos_disponiveis = [datetime.now().year, datetime.now().year - 1, datetime.now().year - 2]
        ano_base = st.selectbox("📅 Ano-Calendário:", anos_disponiveis)
        st.success(f"🕰️ Sistema configurado para o ano base **{ano_base}**.")

        if not df_geral.empty:
            data_limite  = pd.to_datetime(f"{ano_base}-12-31")
            df_ir_filtrado = df_geral[df_geral['Data'] <= data_limite].copy()

            if not df_ir_filtrado.empty:
                df_ir_calc = df_ir_filtrado.groupby('Ticker').agg(
                    {'Qtd':'sum','Preco_Pago':'mean','Categoria':'first'}
                ).reset_index()
                df_ir_calc = df_ir_calc[df_ir_calc['Qtd'] > 0.0001]

                if not df_ir_calc.empty:
                    df_ir_calc['Custo_Total'] = df_ir_calc['Qtd'] * df_ir_calc['Preco_Pago']

                    def gerar_pdf_valorpro(df_filtrado, ano, titulo_relatorio):
                        from fpdf import FPDF
                        pdf = FPDF()
                        pdf.add_page()
                        try:
                            url_logo = URL_LOGO_OFICIAL
                            pdf.image(url_logo, x=55, y=10, w=100)
                            pdf.ln(40)
                        except Exception:
                            pdf.set_font("Arial", 'B', 24)
                            pdf.set_text_color(30, 58, 138)
                            pdf.cell(0, 20, "VALORPRO IA", ln=True, align='C')
                            pdf.ln(5)

                        pdf.set_font("Arial", 'B', 15)
                        pdf.set_text_color(30, 58, 138)
                        pdf.cell(0, 10, f"{chr(187)} RELATORIO DE BENS E DIREITOS", ln=True, align='C')
                        pdf.set_font("Arial", '', 10)
                        pdf.set_text_color(120, 120, 120)
                        pdf.cell(0, 6, titulo_relatorio, ln=True, align='C')
                        pdf.set_draw_color(30, 58, 138)
                        pdf.set_line_width(0.6)
                        pdf.line(20, pdf.get_y() + 2, 190, pdf.get_y() + 2)
                        pdf.ln(10)
                        pdf.set_font("Arial", 'B', 11)
                        pdf.set_text_color(80, 80, 80)
                        pdf.cell(0, 10, f"Ano Base: {ano}", ln=True, align='C')
                        pdf.ln(5)

                        pdf.set_text_color(0, 0, 0)
                        for _, r in df_filtrado.iterrows():
                            pdf.set_font("Arial", 'B', 12)
                            pdf.cell(0, 8, f"{r['Ticker']} - {r['Categoria']}", ln=True, align='C')
                            pdf.set_font("Arial", '', 11)
                            texto = (f"Posicao de {formatar_qtd(r['Qtd'])} unidades, "
                                     f"custo medio de R$ {r['Preco_Pago']:,.2f} "
                                     f"e valor total de R$ {r['Custo_Total']:,.2f} em 31/12/{ano}.")
                            pdf.multi_cell(0, 6, texto, align='C')
                            pdf.ln(4)
                            pdf.set_draw_color(220, 220, 220)
                            pdf.set_line_width(0.2)
                            pdf.line(60, pdf.get_y(), 150, pdf.get_y())
                            pdf.ln(5)

                        pdf.ln(10)
                        pdf.set_font("Arial", 'I', 9)
                        pdf.set_text_color(140, 140, 140)
                        pdf.multi_cell(0, 5,
                            "REGRAS FISCAIS: Acoes (Isento ate R$ 20k/mes) | "
                            "Cripto (Isento ate R$ 35k/mes) | FIIs (20% fixo s/ lucro).", align='C')
                        return bytes(pdf.output())

                    st.download_button(
                        label=f"📄 Baixar Relatório Geral em PDF ({ano_base})",
                        data=gerar_pdf_valorpro(df_ir_calc, ano_base, "RELATORIO CONSOLIDADO COMPLETO"),
                        file_name=f"Relatorio_Geral_ValorPro_{ano_base}.pdf",
                        mime="application/pdf"
                    )

    st.divider()
    if not df_geral.empty and 'df_ir_calc' in locals() and not df_ir_calc.empty:
        st.markdown("#### 🎯 Fichas de Declaração")
        ativos_sel_ir = st.multiselect("Selecione os ativos:",
                                        options=df_ir_calc['Ticker'].tolist(),
                                        default=df_ir_calc['Ticker'].tolist()[:1])
        if ativos_sel_ir:
            df_para_pdf = df_ir_calc[df_ir_calc['Ticker'].isin(ativos_sel_ir)]
            st.download_button(
                label="📄 Gerar PDF dos Selecionados",
                data=gerar_pdf_valorpro(df_para_pdf, ano_base, "RELATORIO DE ATIVOS SELECIONADOS"),
                file_name=f"Relatorio_Custom_ValorPro_{ano_base}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            for ticker in ativos_sel_ir:
                dados = df_ir_calc[df_ir_calc['Ticker'] == ticker].iloc[0]
                texto_declaracao = (
                    f"Posição de {formatar_qtd(dados['Qtd'])} unidades de {dados['Ticker']} "
                    f"({dados['Categoria']}), com custo médio de R$ {dados['Preco_Pago']:,.2f} "
                    f"e valor total de R$ {dados['Custo_Total']:,.2f} em 31/12/{ano_base}."
                )
                with st.container():
                    st.markdown(f"### 🔷 {ticker} | *{dados['Categoria']}*")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Qtd",       formatar_qtd(dados['Qtd']))
                    c2.metric("P. Médio",  f"R$ {dados['Preco_Pago']:,.2f}")
                    c3.metric("Total Pago",f"R$ {dados['Custo_Total']:,.2f}")
                    st.markdown("**Texto para a Receita:**")
                    st.markdown(f"""<div style="background-color:rgba(59,130,246,0.1);border-left:4px solid #3b82f6;
                        padding:16px;border-radius:8px;font-size:15px;line-height:1.5;">{texto_declaracao}</div>""",
                        unsafe_allow_html=True)
                    st.write("---")
        else:
            st.warning("Selecione ativos para gerar o PDF.")

        with st.expander("📊 Tabela Resumo"):
            st.dataframe(df_ir_calc.rename(columns={'Preco_Pago':'Preço Médio','Custo_Total':'Custo Aquisição'}),
                         hide_index=True, use_container_width=True)
    else:
        st.info("Carteira vazia ou sem dados para o ano selecionado.")

# =============================================================================
# ABA 13: METAS
# =============================================================================
with tab_metas:
    with st.expander("ℹ️ Como usar as Metas", expanded=False):
        st.markdown("Defina seu patrimônio alvo e acompanhe o progresso rumo à independência financeira.")

    st.markdown("#### 🎯 Acompanhamento de Metas de Patrimônio")
    if not df_geral.empty and not df_g.empty:
        col_meta1, col_meta2 = st.columns([1, 1.5])
        patrimonio_atual = df_g["Total_Atual"].sum()

        with col_meta1:
            meta_patrimonio = st.number_input("Meta de Patrimônio (R$):", min_value=1000.0, value=100000.0, step=10000.0)
            progresso = min(patrimonio_atual / meta_patrimonio, 1.0)
            falta     = max(0, meta_patrimonio - patrimonio_atual)
            st.write("")
            st.metric("Patrimônio Atual", f"R$ {patrimonio_atual:,.2f}")
            st.metric("Falta para a Meta", f"R$ {falta:,.2f}")
            if progresso >= 1.0:
                st.success("🎉 PARABÉNS! Meta atingida ou ultrapassada!")
            else:
                st.info(f"Você conquistou {progresso * 100:.2f}% do objetivo.")

        with col_meta2:
            st.write(f"**Progresso: {progresso * 100:.2f}%**")
            st.progress(progresso)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=patrimonio_atual,
                domain={'x':[0,1],'y':[0,1]},
                title={'text':"Velocímetro de Riqueza"},
                number={'prefix':"R$ "},
                gauge={
                    'axis':{'range':[None, meta_patrimonio]},
                    'bar':{'color':"#1e3a8a"},
                    'steps':[
                        {'range':[0, meta_patrimonio*0.3],  'color':"rgba(239,68,68,0.2)"},
                        {'range':[meta_patrimonio*0.3, meta_patrimonio*0.7], 'color':"rgba(245,158,11,0.2)"},
                        {'range':[meta_patrimonio*0.7, meta_patrimonio],     'color':"rgba(34,197,94,0.2)"}
                    ]
                }
            ))
            fig_gauge.update_layout(height=280, margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)
    else:
        st.info("Sua carteira está vazia.")

# =============================================================================
# ABA 14: HISTÓRICO E EDIÇÃO
# =============================================================================
with tab_edit:
    he1, he2 = st.tabs(["👁️ Visualizar Lançamentos","🏷️ Histórico de Marcação"])

    with he1:
        st.markdown("#### 📝 Auditoria e Gerenciamento")
        if not df_geral.empty:
            csv = df_geral.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Carteira em CSV", data=csv,
                               file_name="minha_carteira_nuvem.csv", mime="text/csv")

        st.info("💡 Edite os valores diretamente e clique em Salvar.")

        colunas_ocultas = ['usuario_id','criado_em']
        df_para_editar  = df_geral.drop(columns=[c for c in colunas_ocultas if c in df_geral.columns])
        colunas_bloqueadas = ["id"] if "id" in df_para_editar.columns else []

        df_editado = st.data_editor(
            df_para_editar,
            hide_index=True,
            use_container_width=True,
            key="editor_operacoes",
            disabled=colunas_bloqueadas
        )

        if st.button("💾 Salvar Alterações na Nuvem"):
            mudancas = st.session_state["editor_operacoes"].get("edited_rows", {})
            if mudancas:
                try:
                    sucesso = 0
                    for index, campos_alterados in mudancas.items():
                        row_id = int(df_para_editar.iloc[int(index)]['id'])
                        supabase.table("operacoes").update(campos_alterados).eq("id", row_id).execute()
                        sucesso += 1
                    st.success(f"✅ {sucesso} alteração(ões) salva(s)!")
                    st.session_state.df_geral = carregar_dados_nuvem()
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {e}")
            else:
                st.warning("⚠️ Nenhuma célula foi alterada.")

        st.divider()
        st.markdown("#### 🗑️ Apagar Lançamento")
        if 'id' in df_geral.columns:
            df_delete = df_geral.copy()
            df_delete['Data_Str']  = pd.to_datetime(df_delete['Data']).dt.strftime('%d/%m/%Y')
            df_delete['Descricao'] = (df_delete['Data_Str'] + " | " + df_delete['Tipo'] + " de " +
                                      df_delete['Qtd'].astype(str) + "x " + df_delete['Ticker'] +
                                      " (R$ " + df_delete['Preco_Pago'].astype(str) + ")")
            opcoes_delete = dict(zip(df_delete['id'], df_delete['Descricao']))

            with st.form("form_delete_op"):
                id_selecionado = st.selectbox("Selecione a operação para apagar:",
                                               options=list(opcoes_delete.keys()),
                                               format_func=lambda x: opcoes_delete[x])
                col_btn1, col_btn2 = st.columns([1, 3])
                with col_btn1:
                    btn_apagar = st.form_submit_button("🗑️ Excluir Definitivamente")
                if btn_apagar:
                    try:
                        supabase.table("operacoes").delete().eq("id", id_selecionado).execute()
                        st.success("✅ Lançamento apagado!")
                        st.session_state.df_geral = carregar_dados_nuvem()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao apagar: {e}")

    with he2:
        try:
            df_log = carregar_log_precos()
            if not df_log.empty:
                st.dataframe(df_log.sort_index(ascending=False), hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma reavaliação registrada ainda.")
        except Exception:
            st.info("Nenhuma reavaliação registrada ainda.")
