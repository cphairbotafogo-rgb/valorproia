# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import google.generativeai as genai
import json
import os
import base64

# === IMPORTANDO A NOSSA ARQUITETURA MODULARIZADA ===
from banco import *
from motor import *

try:
    from supabase import create_client, Client
except ImportError:
    st.error("⚠️ Biblioteca do Supabase não encontrada! Rode 'pip install supabase'.")
    st.stop()

# =============================================================================
# 🌐 1. CONEXÃO COM A NUVEM (SUPABASE)
# =============================================================================
# COLOQUE SUAS CHAVES DO SUPABASE ABAIXO:
URL_SUPABASE = st.secrets["SUPABASE_URL"]
CHAVE_SUPABASE = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(URL_SUPABASE, CHAVE_SUPABASE)

import streamlit as st
from datetime import datetime

# =============================================================================
# 🔒 FUNÇÃO DE BLOQUEIO FREEMIUM (Coloque antes das suas abas)
# =============================================================================
def exibir_bloqueio_premium(funcionalidade):
    st.markdown(f"""
        <div style="text-align: center; padding: 40px; border: 2px dashed #1e3a8a; border-radius: 15px; background-color: #f8f9fa;">
            <h2 style="color: #1e3a8a;">🔒 {funcionalidade}</h2>
            <p style="font-size: 18px;">Esta funcionalidade é exclusiva para usuários <b>Premium</b>.</p>
            <p>Assine agora para liberar o acesso total ao terminal institucional.</p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")
    st.link_button("🚀 Liberar Acesso Premium", "https://pay.kiwify.com.br/SEU_LINK_GERAL", use_container_width=True, type="primary")
    st.stop()

# =============================================================================
# 🔐 NOVA TELA DE LOGIN COM VITRINE (Substitua a sua def tela_login() antiga por esta)
# =============================================================================
def tela_login():
    # === 🔑 SUA CHAVE MESTRA ===
    EMAIL_ADMIN = "ripeixotooficial@outlook.com" # <--- MUDE AQUI
    
    st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>📈 ValorPro IA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.7;'>Terminal Institucional Nuvem V8</p>", unsafe_allow_html=True)
    st.write("")
    
    aba_login, aba_planos = st.tabs(["🔐 Acessar Terminal", "🛒 Planos Premium"])
    
    with aba_login:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                u = st.text_input("Usuário (E-mail)").strip().lower()
                p = st.text_input("Senha", type="password")
                entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
                
                if entrar:
                    with st.spinner("Autenticando..."):
                        try:
                            # O 'supabase' precisa estar inicializado antes (você já tem isso no topo do seu código)
                            resposta = supabase.table("usuarios").select("*").eq("email", u).eq("senha", p).execute()
                            
                            if len(resposta.data) > 0:
                                dados = resposta.data[0]
                                st.session_state.autenticado = True
                                st.session_state.usuario_logado = u
                                st.session_state.usuario_id = dados['id']
                                
                                # --- 🚦 LÓGICA DO FREEMIUM ---
                                hoje = datetime.now().date()
                                exp = dados.get('expiracao')
                                
                                # Se é o dono OU pagou e está na validade -> PREMIUM
                                if u == EMAIL_ADMIN.lower():
                                    st.session_state.tipo_acesso = "premium"
                                elif exp and datetime.strptime(exp, "%Y-%m-%d").date() >= hoje:
                                    st.session_state.tipo_acesso = "premium"
                                else:
                                    st.session_state.tipo_acesso = "gratis"
                                
                                st.rerun()
                            else:
                                st.error("E-mail ou senha incorretos.")
                        except Exception as e:
                            st.error(f"Erro de conexão com o banco de dados: {e}")

    with aba_planos:
        st.markdown("<h3 style='text-align: center;'>Invista no seu Futuro com o ValorPro IA</h3>", unsafe_allow_html=True)
        st.write("---")
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("""<div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center; background: #f9f9f9; margin-bottom: 15px;">
            <h3>Mensal</h3><h2>R$ 29,90</h2><p>Acesso por 30 dias</p></div>""", unsafe_allow_html=True)
            st.link_button("💳 Assinar Mensal", "https://pay.kiwify.com.br/LINK_AQUI", use_container_width=True)

        with c2:
            st.markdown("""<div style="border: 2px solid #1e3a8a; border-radius: 10px; padding: 20px; text-align: center; background: #fff; position: relative; margin-bottom: 15px;">
            <span style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #1e3a8a; color: white; padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">⭐ MAIS VENDIDO</span>
            <h3>Trimestral</h3><h2>R$ 69,90</h2><p>Acesso por 90 dias</p></div>""", unsafe_allow_html=True)
            st.link_button("💳 Assinar Trimestral", "https://pay.kiwify.com.br/LINK_AQUI", use_container_width=True, type="primary")

        with c3:
            st.markdown("""<div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center; background: #f9f9f9; margin-bottom: 15px;">
            <h3>Anual</h3><h2>R$ 197,00</h2><p>Acesso por 365 dias</p></div>""", unsafe_allow_html=True)
            st.link_button("💳 Assinar Anual", "https://pay.kiwify.com.br/LINK_AQUI", use_container_width=True)

        st.write("---")
        st.info("💡 A liberação é feita automaticamente após a confirmação do pagamento.")

# =============================================================================
# 🧠 2. CONFIGURAÇÃO DA IA (GEMINI)
# =============================================================================
CHAVE_API_GOOGLE = st.secrets["GEMINI_CHAVE"]
if CHAVE_API_GOOGLE:
    genai.configure(api_key=CHAVE_API_GOOGLE)

# =============================================================================
# 🔐 3. SEGURANÇA E LOGIN (NUVEM)
# =============================================================================
st.set_page_config(page_title="ValorPro IA", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_logado = ""
    st.session_state.usuario_id = ""

def tela_login():
    # === 🔑 CONFIGURAÇÃO DO DONO (MUDE PARA O SEU E-MAIL) ===
    EMAIL_ADMIN = "aripeixotooficial@outlook.com" 
    
    st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>📈 ValorPro IA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.7;'>Terminal Institucional Nuvem V8</p>", unsafe_allow_html=True)
    st.write("")
    
    aba_login, aba_planos = st.tabs(["🔐 Acessar Terminal", "🛒 Planos de Assinatura"])
    
    with aba_login:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                u = st.text_input("Usuário (E-mail)").strip().lower()
                p = st.text_input("Senha", type="password")
                entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
                
                if entrar:
                    with st.spinner("Autenticando..."):
                        try:
                            resposta = supabase.table("usuarios").select("*").eq("email", u).eq("senha", p).execute()
                            if len(resposta.data) > 0:
                                dados = resposta.data[0]
                                
                                # --- VERIFICAÇÃO DE ACESSO ---
                                # 1. Se for o DONO, entra direto
                                if u == EMAIL_ADMIN.lower():
                                    st.session_state.autenticado = True
                                    st.session_state.usuario_logado = u
                                    st.session_state.usuario_id = dados['id']
                                    st.rerun()
                                
                                # 2. Se for cliente, verifica validade
                                elif 'expiracao' in dados and dados['expiracao']:
                                    from datetime import datetime
                                    data_exp = datetime.strptime(dados['expiracao'], "%Y-%m-%d").date()
                                    if datetime.now().date() > data_exp:
                                        st.error(f"❌ Assinatura expirada em {data_exp.strftime('%d/%m/%Y')}")
                                        st.info("Escolha um plano na aba ao lado para renovar.")
                                        st.stop()
                                
                                # Tudo OK
                                st.session_state.autenticado = True
                                st.session_state.usuario_logado = u
                                st.session_state.usuario_id = dados['id']
                                st.rerun()
                            else:
                                st.error("E-mail ou senha incorretos.")
                        except Exception as e:
                            st.error(f"Erro no banco: {e}")

    with aba_planos:
        st.markdown("<h3 style='text-align: center;'>Invista no seu Futuro com o ValorPro IA</h3>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        # PLANO MENSAL
        with c1:
            st.markdown("""<div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center; background: #f9f9f9;">
            <h3>Mensal</h3><h2>R$ 29,90</h2><p>Acesso 30 dias</p></div>""", unsafe_allow_html=True)
            st.link_button("💳 Assinar Mensal", "https://pay.kiwify.com.br/LINK_MENSAL", use_container_width=True)

        # PLANO TRIMESTRAL (Destaque)
        with c2:
            st.markdown("""<div style="border: 2px solid #1e3a8a; border-radius: 10px; padding: 20px; text-align: center; background: #fff;">
            <span style="color: #1e3a8a; font-weight: bold;">⭐ MAIS VENDIDO</span><h3>Trimestral</h3><h2>R$ 69,90</h2><p>Acesso 90 dias</p></div>""", unsafe_allow_html=True)
            st.link_button("💳 Assinar Trimestral", "https://pay.kiwify.com.br/LINK_TRIMESTRAL", use_container_width=True, type="primary")

        # PLANO ANUAL
        with c3:
            st.markdown("""<div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center; background: #f9f9f9;">
            <h3>Anual</h3><h2>R$ 197,00</h2><p>Acesso 365 dias</p></div>""", unsafe_allow_html=True)
            st.link_button("💳 Assinar Anual", "https://pay.kiwify.com.br/LINK_ANUAL", use_container_width=True)

        st.write("---")
        st.info("💡 A liberação é feita automaticamente após a confirmação do Pix.")

# =============================================================================
# 🎨 4. DESIGN E ESTILOS NATIVOS
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
div[data-testid="metric-container"] { border-radius: 12px; padding: 16px 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid rgba(128,128,128,0.2); background-color: var(--secondary-background-color); }
div[data-testid="metric-container"] label { font-size: 12px !important; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.8; }
div[data-testid="metric-container"] [data-testid="stMetricValue"], div[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-family: 'DM Mono', monospace !important; }
[data-testid="stTabs"] [role="tablist"] { flex-wrap: wrap; }
[data-testid="stTabs"] button[role="tab"] { font-weight: 500 !important; font-size: 13px !important; transition: all 0.2s ease; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #1e3a8a, #3b82f6) !important; border: none !important; color: white !important; font-weight: 600 !important; border-radius: 8px !important; transition: all 0.2s ease !important; }
.stButton > button[kind="primary"]:hover { background: linear-gradient(135deg, #1e3a8a, #2563eb) !important; box-shadow: 0 0 20px rgba(37,99,235,0.4) !important; transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)

TOP_20_FII = ["MXRF11","HGLG11","XPML11","BTLG11","VISC11","KNIP11","KNCR11","XPLG11","HGRU11","CPTS11","IRDM11","HGBS11","ALZR11","TRXF11","VGHF11","KNSC11","VGIR11","RBRR11","MCCI11","KNRI11"]
TOP_20_ACOES = ["PETR4","VALE3","ITUB4","BBDC4","BBAS3","B3SA3","ABEV3","WEGE3","RENT3","SUZB3","ELET3","RADL3","JBSS3","EQTL3","SBSP3","EMBR3","RAIL3","PRIO3","HAPV3","BBSE3"]
LISTA_CRIPTO = ["BTC-BRL", "ETH-BRL", "SOL-BRL", "USDT-BRL", "DOGE-BRL", "XRP-BRL"]
LISTA_EUA = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK-B", "JNJ", "V", "VOO", "IVV", "QQQ"]
LISTA_COMPLETA_B3 = sorted(list(set(TOP_20_ACOES + TOP_20_FII + ["ALPA4", "ALSO3", "ALUP11", "AMBP3", "ARZZ4", "ASAI3", "AURE3", "AZUL4", "BBDC3", "BEEF3", "BPAC11", "BRAP4", "BRFS3", "BRKM5", "CASH3", "CCRO3", "CEAB3", "CGAS4", "CIEL3", "CMIG4", "COGN3", "CPFE6", "CPLE6", "CRFB3", "CSAN3", "CSMG3", "CSNA3", "CVCB3", "CXSE3", "CYRE3", "DIRR3", "EGIE3", "ELET6", "ENBR3", "ENEV3", "ENGI11", "EZTC3", "FLRY3", "GGBR4", "GOAU4", "GOLL4", "HYPE3", "IGTI11", "INTB3", "ITSA4", "JHSF3", "KLBN11", "LWSA3", "MGLU3", "MRFG3", "MRVE3", "MULT3", "NTCO3", "PCAR3", "PETR3", "PETZ3", "POMO4", "PSSA3", "QUAL3", "RAPT4", "RDOR3", "RECV3", "RRRP3", "SANB11", "SANB4", "SAPR11", "SAPR4", "SLCE3", "SMFT3", "SOMA3", "TAEE11", "TIMS3", "TOTS3", "TRPL4", "UGPA3", "USIM4", "VIVT3", "YDUQ3", "ARRI11", "BRCR11", "BRCO11", "BTAL11", "CACR11", "CVBI11", "DEVA11", "FEXC11", "GGRC11", "HCTR11", "HGCR11", "HSML11", "JSRE11", "KFOF11", "KNCA11", "MALL11", "PLCR11", "PVBI11", "RBRL11", "RBRP11", "RBVA11", "RBRF11", "RECR11", "RECT11", "SARE11", "SNCI11", "TGAR11", "URPR11", "VCJR11", "VGIP11", "VILG11", "VINO11", "VRTA11", "XPCI11", "XPPR11", "XPSF11"])))

def get_image_base64(path):
    try:
        with open(path, "rb") as img_file: return base64.b64encode(img_file.read()).decode()
    except: return None

col_logo, col_titulo, col_clock = st.columns([0.6, 2.5, 1])

with col_logo:
    img_b64 = get_image_base64("logo.png")
    if img_b64: st.markdown(f'<img src="data:image/png;base64,{img_b64}" width="80">', unsafe_allow_html=True)
    else: st.markdown("<h1 style='color: #1e3a8a;'>📈</h1>", unsafe_allow_html=True)

with col_titulo:
    st.markdown("""<div style="padding: 16px 0 0 0;"><span style="font-size:32px;font-weight:700; color: #1e3a8a;">ValorPro IA</span><span style="font-size:14px;opacity:0.7;margin-left:15px; color: #1e3a8a;">Terminal Institucional V8</span></div>""", unsafe_allow_html=True)

with col_clock:
    html_clock = """<style>@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@500&family=DM+Sans:wght@500&display=swap');body{margin:0;padding:0;background:transparent;}.clock-wrap{font-family:'DM Sans',sans-serif; background:linear-gradient(135deg,#161b27,#1a2235); border:1px solid #1e3a5f;border-radius:10px; padding:10px 16px;display:flex;align-items:center; justify-content:space-between;margin-top:4px; box-shadow:0 4px 20px rgba(0,0,0,0.2);}.dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;}.dot.open{background:#22c55e;box-shadow:0 0 8px rgba(34,197,94,0.6);animation:pulse 2s infinite;}.dot.closed{background:#ef4444;box-shadow:0 0 8px rgba(239,68,68,0.5);}@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}.status-txt{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin-left:8px;}.time-txt{font-family:'DM Mono',monospace;font-size:18px;font-weight:500;color:#f0f9ff;}</style><div class="clock-wrap"><div style="display:flex;align-items:center;gap:0"><div class="dot" id="dot"></div><span class="status-txt" id="stxt">--</span></div><div class="time-txt" id="ttxt">--:--:--</div></div><script>function tick(){var n=new Date(),h=n.getHours(),m=n.getMinutes(),s=n.getSeconds(),dw=n.getDay();document.getElementById('ttxt').textContent=(h<10?'0':'')+h+':'+(m<10?'0':'')+m+':'+(s<10?'0':'')+s;var open=dw>=1&&dw<=5&&h>=10&&h<17;document.getElementById('dot').className='dot '+(open?'open':'closed');document.getElementById('stxt').textContent=open?'B3 ABERTA':'B3 FECHADA';}setInterval(tick,1000);tick();</script>"""
    st.components.v1.html(html_clock, height=58)

st.divider()

# =============================================================================
# 📥 FUNÇÃO DE CARREGAR DADOS DA NUVEM E ADAPTAR PARA O MOTOR ANTIGO
# =============================================================================
def carregar_dados_nuvem():
    # 👉 A TRAVA DE SEGURANÇA (Se não tiver logado, nem tenta buscar no banco)
    if "usuario_id" not in st.session_state or st.session_state.usuario_id == "":
        return pd.DataFrame()

    try:
        res = supabase.table("operacoes").select("*").eq("usuario_id", st.session_state.usuario_id).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['data_operacao'] = pd.to_datetime(df['data_operacao'])
            # Renomeia as colunas do banco para as colunas exatas que o seu motor.py exige
            df = df.rename(columns={
                'ticker': 'Ticker', 
                'quantidade': 'Qtd', 
                'preco_unitario': 'Preco_Pago', 
                'data_operacao': 'Data',
                'tipo': 'Tipo'
            })
            # Recuperando Categoria na hora de ler (pra manter a lógica local)
            def define_cat(t):
                if t in LISTA_EUA: return "Exterior (EUA)"
                elif t in LISTA_CRIPTO: return "Criptomoedas"
                
                acoes_falsos_fiis = ['TAEE11', 'KLBN11', 'SANB11', 'ALUP11', 'BPAC11', 'ENGI11', 'SULA11']
                if str(t).endswith('11') and t not in acoes_falsos_fiis:
                    return "FIIs"
                else:
                    return "Ações"
                    
            if 'Categoria' not in df.columns:
                df['Categoria'] = df['Ticker'].apply(define_cat)
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da nuvem: {e}")
        return pd.DataFrame()
            df['data_operacao'] = pd.to_datetime(df['data_operacao'])
            # Renomeia as colunas do banco para as colunas exatas que o seu motor.py exige
            df = df.rename(columns={
                'ticker': 'Ticker', 
                'quantidade': 'Qtd', 
                'preco_unitario': 'Preco_Pago', 
                'data_operacao': 'Data',
                'tipo': 'Tipo'
            })
            # Recuperando Categoria na hora de ler (pra manter a lógica local)
            def define_cat(t):
                if t in LISTA_EUA: return "Exterior (EUA)"
                elif t in LISTA_CRIPTO: return "Criptomoedas"
                
                acoes_falsos_fiis = ['TAEE11', 'KLBN11', 'SANB11', 'ALUP11', 'BPAC11', 'ENGI11', 'SULA11']
                if str(t).endswith('11') and t not in acoes_falsos_fiis:
                    return "FIIs"
                else:
                    return "Ações"
                    
            if 'Categoria' not in df.columns:
                df['Categoria'] = df['Ticker'].apply(define_cat)
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da nuvem: {e}")
        return pd.DataFrame()

if "df_geral" not in st.session_state: st.session_state.df_geral = carregar_dados_nuvem()
df_geral = st.session_state.df_geral

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.usuario_logado}")
    
    with st.expander("🔐 Alterar Login e Senha"):
        n_usr = st.text_input("Novo Usuário:", value=st.session_state.usuario_logado)
        n_pwd = st.text_input("Nova Senha:", type="password")
        c_pwd = st.text_input("Confirme a Senha:", type="password")
        
        if st.button("Atualizar Credenciais", use_container_width=True):
            if n_pwd == c_pwd and n_pwd != "":
                try:
                    supabase.table("usuarios").update({"email": n_usr, "senha": n_pwd}).eq("id", st.session_state.usuario_id).execute()
                    st.success("✅ Atualizado! Faça login novamente.")
                    time.sleep(1.5)
                    st.session_state.autenticado = False
                    st.rerun()
                except Exception as e:
                    st.error("Erro ao atualizar credenciais na nuvem.")
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
    st.markdown("### 🛒 Lançar Operação (Nuvem)")
    classe_ativo = st.selectbox("Classe:", ["Bolsa (Ações/FIIs)", "Renda Fixa (CDB/Tesouro)", "Criptomoedas", "Exterior (EUA)"])
    tipo = st.radio("Tipo:", ["Compra", "Venda"], horizontal=True)
    data_op = st.date_input("Data:", datetime.now())

    if classe_ativo == "Bolsa (Ações/FIIs)":
        opcao_t = st.selectbox("Ativo:", ["Digitar código..."] + LISTA_COMPLETA_B3)
        t_in = st.text_input("Código B3:").upper().strip() if opcao_t == "Digitar código..." else opcao_t
    elif classe_ativo == "Criptomoedas":
        opcao_t = st.selectbox("Ativo:", ["Digitar código..."] + LISTA_CRIPTO)
        t_in = st.text_input("Código (Ex: ETH-BRL):").upper().strip() if opcao_t == "Digitar código..." else opcao_t
    elif classe_ativo == "Exterior (EUA)":
        opcao_t = st.selectbox("Ativo:", ["Digitar código..."] + LISTA_EUA)
        t_in = st.text_input("Ticker EUA (Ex: AAPL):").upper().strip() if opcao_t == "Digitar código..." else opcao_t
    else:
        t_in = st.text_input("Nome (Ex: CDB Bradesco):").upper().strip()

    col_q, col_p = st.columns(2)
    with col_q: 
        if classe_ativo in ["Criptomoedas", "Exterior (EUA)"]: q_in = st.number_input("Qtd:", min_value=0.00000001, step=0.01, format="%.8f")
        else: q_in = st.number_input("Qtd:", min_value=1.0, step=1.0)
    with col_p: 
        p_label = "Preço Pago (em R$):" if classe_ativo == "Exterior (EUA)" else "Preço Unitário:"
        p_in = st.number_input(p_label, min_value=0.0, step=0.01, format="%.2f")

    st.write("")
    if st.button("💾 Salvar na Nuvem", use_container_width=True):
        if t_in:
            with st.spinner("Salvando no Supabase..."):
                q_f = q_in if tipo == "Compra" else -q_in
                
                # Inserção direta na tabela operacoes do Supabase
                nova_op = {
                    "usuario_id": st.session_state.usuario_id,
                    "ticker": t_in.upper(),
                    "tipo": tipo,
                    "quantidade": float(q_f),
                    "preco_unitario": float(p_in),
                    "data_operacao": data_op.strftime('%Y-%m-%d')
                }
                try:
                    supabase.table("operacoes").insert(nova_op).execute()
                    st.session_state.df_geral = carregar_dados_nuvem()
                    st.success(f"✅ {t_in.upper()} salvo com sucesso!")
                    time.sleep(1.2); st.rerun()
                except Exception as e:
                    st.error(f"Falha ao salvar no banco: {e}")
        else: st.error("Digite um código válido.")

    st.divider()
    st.markdown("### ⚙️ Configurações")
    cdi_anual = st.number_input("CDI atual (% a.a.):", min_value=0.1, max_value=30.0, value=10.5, step=0.1) / 100
    ibov_anual = st.number_input("Meta Ibovespa (% a.a.):", min_value=0.1, max_value=50.0, value=12.0, step=0.1) / 100

# =============================================================================
# ⚙️ MOTOR DE CÁLCULO E CONSOLIDAÇÃO (Mantido Intacto)
# =============================================================================
df_g = pd.DataFrame()
if not df_geral.empty:
    with st.spinner("Sincronizando carteira Global..."):
        df_cart = consolidar(df_geral)
        mask_bolsa = df_cart["Categoria"].isin(["FIIs","Fiagro","FII","Ações","Acao","BDR","Criptomoedas", "Exterior (EUA)"])
        lista_busca = df_cart[mask_bolsa][["Ticker", "Categoria"]].values.tolist()
        
        m_data = buscar_multiplos(lista_busca) if lista_busca else []
        if m_data:
            df_mkt = pd.DataFrame(m_data).drop(columns=["Categoria"], errors="ignore")
            df_g = pd.merge(df_cart, df_mkt, on="Ticker", how="left")
        else: df_g = df_cart.copy()

        for col in ["Preço","P_VP","P_L","Rend","Var_Dia"]:
            if col not in df_g.columns: df_g[col] = 0.0
        for col in ["DY_12M", "DY_Mensal"]:
            if col not in df_g.columns: df_g[col] = "-"
        if "Status" not in df_g.columns: df_g["Status"] = "Offline"
        
        df_g["Preço"] = pd.to_numeric(df_g["Preço"], errors="coerce").fillna(0.0)
        df_g["Preço"] = df_g.apply(lambda r: r["Preco_Medio"] if r["Preço"] == 0.0 else r["Preço"], axis=1)
        df_g.fillna({"P_VP": 0.0, "P_L": 0.0, "Rend": 0.0, "Var_Dia": 0.0, "DY_12M": "-", "DY_Mensal": "-", "Status": "Offline"}, inplace=True)
        
        precos_manuais = carregar_precos_manuais()
# O TRUQUE: Força tudo que tem "TESOURO" no nome a virar Renda Fixa na marra
        df_g.loc[df_g["Ticker"].str.contains("TESOURO", case=False, na=False), "Categoria"] = "Renda Fixa"

        mask_rf = df_g["Categoria"] == "Renda Fixa"
        
        # O escudo: Só tenta calcular se existir Renda Fixa na carteira
        if mask_rf.any():
            df_g.loc[mask_rf, "Preço"] = pd.to_numeric(df_g.loc[mask_rf, "Preco_Medio"], errors="coerce").fillna(0.0)
            if precos_manuais:
                df_g.loc[mask_rf, "Preço"] = df_g.loc[mask_rf, "Ticker"].map(precos_manuais).fillna(df_g.loc[mask_rf, "Preco_Medio"])

        df_g["Total_Atual"] = df_g["Qtd"] * df_g["Preço"]
        df_g["Custo_Pos"] = df_g["Qtd"] * df_g["Preco_Medio"]

        df_g["Setor"] = df_g.apply(lambda r: descobrir_setor(r["Ticker"], r["Categoria"]), axis=1)

        hoje_str = datetime.now().strftime("%Y-%m-%d")
        snap_df = pd.DataFrame([{"Data": hoje_str, "Aportado": df_g["Custo_Pos"].sum(), "Mercado": df_g["Total_Atual"].sum()}])
        if os.path.exists(SNAPSHOT_FILE):
            df_snap_old = pd.read_csv(SNAPSHOT_FILE)
            pd.concat([df_snap_old[df_snap_old["Data"] != hoje_str], snap_df], ignore_index=True).to_csv(SNAPSHOT_FILE, index=False)
        else: snap_df.to_csv(SNAPSHOT_FILE, index=False)

# =============================================================================
# 📑 ABAS DO SISTEMA (100% COMPLETAS E INTOCADAS)
# =============================================================================
tabs = st.tabs(["🌍 Visão Global", "🏢 FIIs", "📈 Ações", "🌎 Exterior", "🛡️ Renda Fixa", "🪙 Cripto", "💰 Dividendos", "⚖️ Rebalanceamento", "🔍 Radar", "🧮 Simuladores", "🤖 ValorPro IA", "🧾 IR", "🎯 Metas", "📝 Histórico"])
tab_glo, tab_fii, tab_aco, tab_ext, tab_rf, tab_cripto, tab_div, tab_reb, tab_rad, tab_sim, tab_ia, tab_ir, tab_metas, tab_edit = tabs

# --- ABA 1: VISÃO GLOBAL ---
with tab_glo:
    if not df_geral.empty and not df_g.empty:
        st.markdown("#### 🔍 Filtrar Visão de Patrimônio")
        cats_v_sel = st.multiselect("Selecione as classes:", options=sorted(df_g['Categoria'].unique().tolist()), default=sorted(df_g['Categoria'].unique().tolist()))
        df_v_filt = df_g[df_g['Categoria'].isin(cats_v_sel)].copy() if cats_v_sel else pd.DataFrame()

        if not df_v_filt.empty:
            total_glob = df_v_filt["Total_Atual"].sum(); total_inv = df_v_filt["Custo_Pos"].sum()
            rent_glob = ((total_glob - total_inv) / total_inv * 100) if total_inv > 0 else 0.0

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("🏢 FIIs", f"R$ {df_v_filt[df_v_filt['Categoria'].isin(['FIIs','Fiagro'])]['Total_Atual'].sum():,.2f}")
            mc2.metric("📈 Ações", f"R$ {df_v_filt[df_v_filt['Categoria'].isin(['Ações','BDR'])]['Total_Atual'].sum():,.2f}")
            mc3.metric("🌎 EUA", f"R$ {df_v_filt[df_v_filt['Categoria']=='Exterior (EUA)']['Total_Atual'].sum():,.2f}")
            
            st.write("") 
            mc4, mc5, mc6 = st.columns(3)
            mc4.metric("🛡️ R. Fixa", f"R$ {df_v_filt[df_v_filt['Categoria']=='Renda Fixa']['Total_Atual'].sum():,.2f}")
            mc5.metric("🪙 Cripto", f"R$ {df_v_filt[df_v_filt['Categoria']=='Criptomoedas']['Total_Atual'].sum():,.2f}")
            mc6.metric("💎 Sel.", f"R$ {total_glob:,.2f}", delta=f"{rent_glob:+.2f}%")

            st.divider()
            
            st.markdown("#### 📈 Evolução Patrimonial REAL")
            try:
                df_snap_view = pd.read_csv(SNAPSHOT_FILE)
                fig_evo = go.Figure()
                fig_evo.add_trace(go.Scatter(x=df_snap_view["Data"], y=df_snap_view["Aportado"], name="Total Aportado", line=dict(color="#3b82f6", dash="dot"), fill='tozeroy', fillcolor="rgba(59,130,246,0.1)"))
                fig_evo.add_trace(go.Scatter(x=df_snap_view["Data"], y=df_snap_view["Mercado"], name="Valor de Mercado", line=dict(color="#22c55e", width=3), fill='tonexty', fillcolor="rgba(34,197,94,0.15)"))
                fig_evo.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified")
                st.plotly_chart(fig_evo, use_container_width=True, theme="streamlit")
            except: pass

            st.divider()
            col_pie, col_tab = st.columns([1.5, 2.5])
            with col_pie:
                st.markdown("#### Raio-X da Alocação")
                aba_p1, aba_p2 = st.tabs(["📍 Por Ativo", "🧠 Por Setor"])
                with aba_p1:
                    fig_pie_v = px.pie(df_v_filt, values="Total_Atual", names="Ticker", hole=0.55, color_discrete_sequence=px.colors.qualitative.Safe)
                    fig_pie_v.update_traces(textposition='inside', textinfo='percent', insidetextorientation='horizontal')
                    fig_pie_v.update_layout(height=320, margin=dict(t=20, b=40, l=10, r=10), showlegend=True, legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"), uniformtext_minsize=12, uniformtext_mode='hide')
                    st.plotly_chart(fig_pie_v, use_container_width=True, theme="streamlit")
                with aba_p2:
                    fig_pie_setor = px.pie(df_v_filt, values="Total_Atual", names="Setor", hole=0.55, color_discrete_sequence=px.colors.qualitative.Set3)
                    fig_pie_setor.update_traces(textposition='inside', textinfo='percent', insidetextorientation='horizontal')
                    fig_pie_setor.update_layout(height=320, margin=dict(t=20, b=40, l=10, r=10), showlegend=True, legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"), uniformtext_minsize=12, uniformtext_mode='hide')
                    st.plotly_chart(fig_pie_setor, use_container_width=True, theme="streamlit")

            with col_tab:
                st.markdown("#### Ativos no Filtro")
                df_v_filt["L/P (R$)"] = df_v_filt["Total_Atual"] - df_v_filt["Custo_Pos"]
                df_v_filt["L/P (%)"] = df_v_filt.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)

                df_view_v = df_v_filt[["Ticker","Setor","Qtd","Preco_Medio","Preço","Total_Atual","L/P (R$)","L/P (%)"]].copy()
                df_view_v.rename(columns={"Preco_Medio":"PM (R$)","Preço":"Atual (R$)","Total_Atual":"Patrimônio (R$)"}, inplace=True)
                
                df_view_v["L/P (R$)"] = df_view_v["L/P (R$)"].apply(lambda x: formatar_delta(x))
                df_view_v["L/P (%)"]  = df_view_v["L/P (%)"].apply(lambda x: formatar_delta(x, True))
                df_view_v["Qtd"] = df_view_v["Qtd"].apply(formatar_qtd)

                st.dataframe(df_view_v.sort_values("Patrimônio (R$)", ascending=False), hide_index=True, use_container_width=True)
        else: st.warning("⚠️ Selecione ao menos uma classe.")

# --- ABA 2: MEUS FIIs ---
with tab_fii:
    if not df_g.empty:
        f = df_g[df_g["Categoria"].isin(["FII", "FIIs", "Fiagro"])].copy()
        if not f.empty:
            f["Rend"] = pd.to_numeric(f["Rend"], errors="coerce").fillna(0)
            f["Renda Mensal"] = f["Qtd"] * f["Rend"]
            
            m1, m2, m3, col_pie_fii = st.columns([1,1,1,1.2])
            m1.metric("💰 Patrimônio FIIs", f"R$ {f['Total_Atual'].sum():,.2f}")
            m2.metric("💸 Renda Mensal Est.", f"R$ {f['Renda Mensal'].sum():,.2f}")
            lp_fii = (f["Total_Atual"] - f["Custo_Pos"]).sum(); ct_fii = f["Custo_Pos"].sum()
            m3.metric("📈 Valorização", f"R$ {lp_fii:,.2f}", f"{lp_fii/ct_fii*100:+.2f}%" if ct_fii > 0 else "")
            
            with col_pie_fii:
                fig_pf = px.pie(f, values="Total_Atual", names="Ticker", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
                fig_pf.update_traces(textposition='inside', textinfo='percent', insidetextorientation='horizontal')
                fig_pf.update_layout(height=220, margin=dict(t=10, b=10, l=10, r=10), showlegend=False, uniformtext_minsize=12, uniformtext_mode='hide')
                st.plotly_chart(fig_pf, use_container_width=True, theme="streamlit")

            f["L/P (R$)"] = f["Total_Atual"] - f["Custo_Pos"]; f["L/P (%)"] = f.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)
            df_vf = f[["Ticker","Setor","Qtd","Preco_Medio","Preço","Total_Atual","L/P (R$)","L/P (%)","Rend","Renda Mensal","DY_12M"]].copy()
            df_vf.rename(columns={"Preco_Medio":"PM (R$)","Preço":"Atual","Total_Atual":"Patrimônio","Rend":"Rend/Cota"}, inplace=True)
            df_vf["L/P (R$)"] = df_vf["L/P (R$)"].apply(formatar_delta); df_vf["L/P (%)"] = df_vf["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_vf["Qtd"] = df_vf["Qtd"].apply(formatar_qtd)
            st.dataframe(df_vf, hide_index=True, use_container_width=True)

# --- ABA 3: MINHAS AÇÕES ---
with tab_aco:
    if not df_g.empty:
        a = df_g[df_g["Categoria"].isin(["Acao", "Ações", "BDR"])].copy()
        if not a.empty:
            m1, m2, col_vaz, col_pie_aco = st.columns([1,1,1,1.2])
            m1.metric("💰 Patrimônio Ações", f"R$ {a['Total_Atual'].sum():,.2f}")
            lp_aco = (a["Total_Atual"] - a["Custo_Pos"]).sum(); ct_aco = a["Custo_Pos"].sum()
            m2.metric("📈 Valorização", f"R$ {lp_aco:,.2f}", f"{lp_aco/ct_aco*100:+.2f}%" if ct_aco > 0 else "")
            
            with col_pie_aco:
                fig_pa = px.pie(a, values="Total_Atual", names="Ticker", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pa.update_traces(textposition='inside', textinfo='percent', insidetextorientation='horizontal')
                fig_pa.update_layout(height=220, margin=dict(t=10, b=10, l=10, r=10), showlegend=False, uniformtext_minsize=12, uniformtext_mode='hide')
                st.plotly_chart(fig_pa, use_container_width=True, theme="streamlit")

            a["L/P (R$)"] = a["Total_Atual"] - a["Custo_Pos"]; a["L/P (%)"] = a.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)
            df_va = a[["Ticker","Setor","Qtd","Preco_Medio","Preço","Total_Atual","L/P (R$)","L/P (%)","DY_12M"]].copy()
            df_va.rename(columns={"Preco_Medio":"PM (R$)","Preço":"Atual","Total_Atual":"Patrimônio"}, inplace=True)
            df_va["L/P (R$)"] = df_va["L/P (R$)"].apply(formatar_delta); df_va["L/P (%)"] = df_va["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_va["Qtd"] = df_va["Qtd"].apply(formatar_qtd)
            st.dataframe(df_va, hide_index=True, use_container_width=True)

# --- ABA 4: EXTERIOR (EUA) ---
with tab_ext:
    if not df_g.empty:
        ext = df_g[df_g["Categoria"] == "Exterior (EUA)"].copy()
        if not ext.empty:
            m1, m2, col_vaz, col_pie_ext = st.columns([1,1,1,1.2])
            m1.metric("🌎 Patrimônio EUA", f"R$ {ext['Total_Atual'].sum():,.2f}")
            lp_ext = (ext["Total_Atual"] - ext["Custo_Pos"]).sum(); ct_ext = ext["Custo_Pos"].sum()
            m2.metric("📈 Valorização", f"R$ {lp_ext:,.2f}", f"{lp_ext/ct_ext*100:+.2f}%" if ct_ext > 0 else "")
            
            with col_pie_ext:
                fig_ext = px.pie(ext, values="Total_Atual", names="Ticker", hole=0.4, color_discrete_sequence=["#1d4ed8", "#2563eb", "#3b82f6", "#60a5fa"])
                fig_ext.update_traces(textposition='inside', textinfo='percent', insidetextorientation='horizontal')
                fig_ext.update_layout(height=220, margin=dict(t=10, b=10, l=10, r=10), showlegend=False, uniformtext_minsize=12, uniformtext_mode='hide')
                st.plotly_chart(fig_ext, use_container_width=True, theme="streamlit")

            ext["L/P (R$)"] = ext["Total_Atual"] - ext["Custo_Pos"]; ext["L/P (%)"] = ext.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)
            df_vext = ext[["Ticker","Setor","Qtd","Preco_Medio","Preço","Total_Atual","L/P (R$)","L/P (%)"]].copy()
            df_vext.rename(columns={"Preco_Medio":"PM (R$)","Preço":"Atual (R$)","Total_Atual":"Patrimônio (R$)"}, inplace=True)
            df_vext["L/P (R$)"] = df_vext["L/P (R$)"].apply(formatar_delta); df_vext["L/P (%)"] = df_vext["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_vext["Qtd"] = df_vext["Qtd"].apply(formatar_qtd)
            st.dataframe(df_vext, hide_index=True, use_container_width=True)

# --- ABA 5: RENDA FIXA ---
with tab_rf:
    if not df_g.empty:
        crf = df_g[df_g["Categoria"] == "Renda Fixa"].copy()
        if not crf.empty:
            crf["L/P (R$)"] = crf["Total_Atual"] - crf["Custo_Pos"]; crf["L/P (%)"] = crf.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)
            df_vrf = crf[["Ticker","Qtd","Preco_Medio","Preço","Total_Atual","L/P (R$)","L/P (%)"]].copy()
            df_vrf.rename(columns={"Ticker":"Aplicação", "Preco_Medio":"Custo Unit.", "Preço":"Valor Atual", "Total_Atual":"Patrimônio (R$)"}, inplace=True)
            df_vrf["L/P (R$)"] = df_vrf["L/P (R$)"].apply(formatar_delta); df_vrf["L/P (%)"] = df_vrf["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_vrf["Qtd"] = df_vrf["Qtd"].apply(formatar_qtd)
            st.dataframe(df_vrf, hide_index=True, use_container_width=True)

# --- ABA 6: CRIPTOMOEDAS ---
with tab_cripto:
    if not df_g.empty:
        criptos = df_g[df_g["Categoria"] == "Criptomoedas"].copy()
        if not criptos.empty:
            criptos["L/P (R$)"] = criptos["Total_Atual"] - criptos["Custo_Pos"]; criptos["L/P (%)"] = criptos.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)
            df_vcripto = criptos[["Ticker","Qtd","Preco_Medio","Preço","Total_Atual","L/P (R$)","L/P (%)"]].copy()
            df_vcripto.rename(columns={"Preco_Medio":"PM Unitário", "Preço":"Preço Atual", "Total_Atual":"Patrimônio (R$)"}, inplace=True)
            df_vcripto["L/P (R$)"] = df_vcripto["L/P (R$)"].apply(formatar_delta); df_vcripto["L/P (%)"] = df_vcripto["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            df_vcripto["Qtd"] = df_vcripto["Qtd"].apply(formatar_qtd)
            st.dataframe(df_vcripto, hide_index=True, use_container_width=True)

# --- ABA 7: DIVIDENDOS ---
with tab_div:
    st.markdown("#### 💰 Registro de Renda Passiva")
    df_divs = carregar_dividendos()

    with st.expander("➕ Lançar novo recebimento", expanded=df_divs.empty):
        cd1, cd2, cd3, cd4, cd5 = st.columns([1,1.2,1,1,0.8])
        with cd1: d_data = st.date_input("Data:", datetime.now(), key="div_dt")
        with cd2:
            opcao_d = st.selectbox("Ativo:", ["Digitar..."] + LISTA_COMPLETA_B3, key="div_sel")
            d_tick = st.text_input("Código:", key="div_inp").upper() if opcao_d == "Digitar..." else opcao_d
        with cd3: d_val  = st.number_input("Valor Total (R$):", min_value=0.01, step=1.0, key="div_val")
        with cd4: d_tipo = st.selectbox("Tipo:", ["Rendimento FII","Dividendo","JCP","Outro"], key="div_tipo")
        with cd5:
            st.write(""); st.write("")
            if st.button("Lançar", use_container_width=True, key="div_btn"):
                if d_tick:
                    novo = pd.DataFrame([{"Data": d_data, "Ticker": d_tick.upper(), "Valor": d_val, "Tipo": d_tipo}])
                    df_div_ok = pd.concat([df_divs, novo], ignore_index=True) if not df_divs.empty else novo
                    df_div_ok.to_csv(DIVIDENDOS_FILE, index=False)
                    st.success("✅ Registrado!"); time.sleep(0.8); st.rerun()
                else: st.error("Preencha o ativo.")

    if not df_divs.empty:
        df_divs["Data"] = pd.to_datetime(df_divs["Data"])
        df_divs["Mês"]  = df_divs["Data"].dt.to_period("M").astype(str)
        total_div = df_divs["Valor"].sum()
        media_div = df_divs.groupby("Mês")["Valor"].sum().mean()

        dm1, dm2, dm3 = st.columns(3)
        dm1.metric("💰 Total Acumulado", f"R$ {total_div:,.2f}")
        dm2.metric("📆 Média Mensal", f"R$ {media_div:,.2f}")
        dm3.metric("📋 Pagamentos", str(len(df_divs)))

        df_grp = df_divs.groupby(["Mês","Tipo"])["Valor"].sum().reset_index()
        fig_div = px.bar(df_grp, x="Mês", y="Valor", color="Tipo", text_auto=".2f", color_discrete_sequence=["#3b82f6","#22c55e","#f59e0b","#a855f7"])
        fig_div.update_layout(height=300, title="Renda Passiva Mensal por Tipo", barmode="stack")
        st.plotly_chart(fig_div, use_container_width=True, theme="streamlit")
        
        with st.expander("📋 Extrato completo"): st.dataframe(df_divs.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
    else: st.info("Nenhum dividendo registrado.")

    st.divider()
    st.markdown("#### 🔮 Efeito Bola de Neve (Projeção para os Próximos 12 Meses)")
    renda_mensal_estimada = 0
    if not df_g.empty:
        df_renda = df_g[df_g["Categoria"].isin(["FIIs", "Fiagro", "FII"])].copy()
        if not df_renda.empty and "Rend" in df_renda.columns:
            renda_mensal_estimada = (pd.to_numeric(df_renda["Qtd"], errors="coerce") * pd.to_numeric(df_renda["Rend"], errors="coerce")).sum()
        
    if renda_mensal_estimada > 0:
        meses_proj = [(datetime.now() + pd.DateOffset(months=i)).strftime("%b/%Y") for i in range(1, 13)]
        valores_proj = [renda_mensal_estimada * ((1.005)**i) for i in range(13)][1:]
        df_proj = pd.DataFrame({"Mês": meses_proj, "Renda Projetada (R$)": valores_proj})
        
        fig_proj = px.bar(df_proj, x="Mês", y="Renda Projetada (R$)", text_auto=".2f", color_discrete_sequence=["#10b981"])
        fig_proj.update_layout(height=280)
        st.plotly_chart(fig_proj, use_container_width=True, theme="streamlit")
        st.info(f"💡 A projeção aponta uma média de **R$ {renda_mensal_estimada:,.2f}** no próximo mês.")
    else: st.info("Adicione FIIs na sua carteira para ativar a projeção da Bola de Neve.")

# --- ABA 8: REBALANCEAMENTO ---
with tab_reb:
    st.markdown("#### ⚖️ Rebalanceamento Inteligente")
    if not df_geral.empty and not df_g.empty:
        cr1, cr2, cr3, cr4, cr5 = st.columns(5)
        with cr1: meta_aco = st.number_input("Alvo Ações (%):", 0, 100, 30, key="rb_aco")
        with cr2: meta_fii = st.number_input("Alvo FIIs (%):", 0, 100, 30, key="rb_fii")
        with cr3: meta_rf  = st.number_input("Alvo R. Fixa (%):",0, 100, 20, key="rb_rf")
        with cr4: meta_ext = st.number_input("Alvo EUA (%):",0, 100, 10, key="rb_ext")
        with cr5: meta_cripto = st.number_input("Alvo Cripto (%):",0, 100, 10, key="rb_cripto")

        aporte = st.number_input("💵 Novo aporte disponível (R$):", min_value=0.0, step=100.0, value=1000.0)
        soma = meta_aco + meta_fii + meta_rf + meta_ext + meta_cripto

        if soma != 100: st.error(f"⚠️ A soma deve ser 100%. Atual: {soma}%")
        else:
            if st.button("🎯 Calcular Aporte Ideal", type="primary"):
                df_rb = df_g.copy()
                atual_aco  = df_rb[df_rb["Categoria"].isin(["Ação","Ações","Acao","BDR"])]["Total_Atual"].sum()
                atual_fii  = df_rb[df_rb["Categoria"].isin(["FII","FIIs","Fiagro"])]["Total_Atual"].sum()
                atual_rf   = df_rb[df_rb["Categoria"] == "Renda Fixa"]["Total_Atual"].sum()
                atual_ext  = df_rb[df_rb["Categoria"] == "Exterior (EUA)"]["Total_Atual"].sum()
                atual_cripto = df_rb[df_rb["Categoria"] == "Criptomoedas"]["Total_Atual"].sum()
                
                pat_futuro = atual_aco + atual_fii + atual_rf + atual_ext + atual_cripto + aporte
                alvo_aco = pat_futuro * (meta_aco / 100); alvo_fii = pat_futuro * (meta_fii / 100)
                alvo_rf  = pat_futuro * (meta_rf  / 100); alvo_ext = pat_futuro * (meta_ext / 100)
                alvo_cripto = pat_futuro * (meta_cripto / 100)

                falta_aco = max(0, alvo_aco - atual_aco); falta_fii = max(0, alvo_fii - atual_fii)
                falta_rf  = max(0, alvo_rf  - atual_rf); falta_ext = max(0, alvo_ext - atual_ext)
                falta_cripto = max(0, alvo_cripto - atual_cripto)
                total_falta = falta_aco + falta_fii + falta_rf + falta_ext + falta_cripto

                st.markdown("---")
                if total_falta > 0:
                    st.success("🎯 Sugestão de aporte (baseado no mercado atual):")
                    rca1, rca2, rca3, rca4, rca5 = st.columns(5)
                    rca1.metric("📈 Ações", f"R$ {(falta_aco/total_falta)*aporte:,.2f}")
                    rca2.metric("🏢 FIIs", f"R$ {(falta_fii/total_falta)*aporte:,.2f}")
                    rca3.metric("🛡️ R. Fixa", f"R$ {(falta_rf /total_falta)*aporte:,.2f}")
                    rca4.metric("🌎 EUA", f"R$ {(falta_ext /total_falta)*aporte:,.2f}")
                    rca5.metric("🪙 Cripto", f"R$ {(falta_cripto /total_falta)*aporte:,.2f}")

                    df_comp = pd.DataFrame({"Classe": ["Ações","FIIs","Renda Fixa","EUA","Cripto","Ações","FIIs","Renda Fixa","EUA","Cripto"], "Tipo": ["Atual","Atual","Atual","Atual","Atual","Alvo","Alvo","Alvo","Alvo","Alvo"], "Valor": [atual_aco, atual_fii, atual_rf, atual_ext, atual_cripto, alvo_aco, alvo_fii, alvo_rf, alvo_ext, alvo_cripto]})
                    fig_rb = px.bar(df_comp, x="Classe", y="Valor", color="Tipo", barmode="group", color_discrete_map={"Atual":"#3b82f6","Alvo":"#22c55e"})
                    fig_rb.update_layout(height=280, title="Comparativo Atual vs Alvo")
                    st.plotly_chart(fig_rb, use_container_width=True, theme="streamlit")
                else: st.info("✅ Carteira já alinhada com as metas!")
    else: st.info("Cadastre ativos primeiro.")

# --- ABA 9: RADAR ---
with tab_rad:
    st.markdown("#### 🔍 Central de Pesquisa e Oportunidades")
    ativos_sel = st.multiselect("Selecione ativos para analisar:", LISTA_COMPLETA_B3)
    extras     = st.text_input("Outros códigos (separados por vírgula):")

    if st.button("🔎 Buscar", type="primary"):
        lista = list(set(ativos_sel + [t.strip().upper() for t in extras.split(",") if t.strip()]))
        if lista:
            with st.spinner("Buscando dados em tempo real..."): res = buscar_multiplos(lista)
            if res:
                df_res = pd.DataFrame(res)
                fiis = df_res[df_res["Categoria"].isin(["FIIs","Fiagro"])].copy()
                acos = df_res[df_res["Categoria"].isin(["Ações","BDR"])].copy()
                criptos = df_res[df_res["Categoria"] == "Criptomoedas"].copy()
                
                if not fiis.empty:
                    st.markdown("##### 🏢 FIIs e Fiagros")
                    fiis.rename(columns={"Rend":"Rend/Cota","DY_12M":"DY 12M","DY_Mensal":"DY Mensal","P_VP":"P/VP","Var_Dia":"Var. Dia %"}, inplace=True)
                    fiis["Var. Dia %"] = fiis["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
                    st.dataframe(fiis[["Ticker","Preço","Var. Dia %","P/VP","DY 12M","DY Mensal","Rend/Cota","Status"]], hide_index=True, use_container_width=True)
                if not acos.empty:
                    st.markdown("##### 📈 Ações e BDRs")
                    acos.rename(columns={"DY_12M":"DY 12M","P_VP":"P/VP","P_L":"P/L","Var_Dia":"Var. Dia %"}, inplace=True)
                    acos["Var. Dia %"] = acos["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
                    st.dataframe(acos[["Ticker","Preço","Var. Dia %","P/VP","P/L","DY 12M","Status"]], hide_index=True, use_container_width=True)
                if not criptos.empty:
                    st.markdown("##### 🪙 Criptomoedas")
                    criptos.rename(columns={"Var_Dia":"Var. Dia %"}, inplace=True)
                    criptos["Var. Dia %"] = criptos["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
                    st.dataframe(criptos[["Ticker","Preço","Var. Dia %","Status"]], hide_index=True, use_container_width=True)
            else: st.warning("Nenhum ativo encontrado.")
        else: st.warning("Selecione ou digite pelo menos um ativo.")

# --- ABA 10: SIMULADORES ---
with tab_sim:
    st.markdown("#### 🧮 Laboratório de Projeções")
    s1, s2, s3, s4 = st.tabs(["⚡ Simulador Rápido", "📈 Juros Compostos", "🎯 Renda Alvo", "🧾 Calc. DARF"])
    
    with s1:
        sc1, sc2 = st.columns([1.2, 1])
        with sc1: op_sim = st.selectbox("Ativo:", ["Digitar..."] + LISTA_COMPLETA_B3, key="sim_box"); tk_sim = st.text_input("Código:", key="sim_txt").upper().strip() if op_sim == "Digitar..." else op_sim
        with sc2: tipo_s = st.radio("Basear em:", ["Montante (R$)", "Quantidade (Cotas)"], horizontal=True)

        if tk_sim:
            with st.spinner(f"Buscando {tk_sim}..."): info_s = buscar_mercado(tk_sim)
            if info_s and info_s["Preço"] > 0:
                pc, rc = info_s["Preço"], info_s["Rend"]
                ia1, ia2 = st.columns(2); ia1.info(f"🏷️ Preço: **R$ {pc:.2f}**"); ia2.info(f"💸 Dividendo: **R$ {rc:.4f}** ({info_s['DY_Mensal']} a.m.)")
                if tipo_s == "Montante (R$)":
                    val = st.number_input("Disponível (R$):", min_value=0.0, value=1000.0, step=100.0)
                    if val > 0: q = int(val / pc); st.write(f"💼 Cotas: **{q}** | Sobra: **R$ {val - q*pc:.2f}**"); st.success(f"🚀 Renda Mensal: **R$ {q*rc:,.2f}**" if rc > 0 else "")
                else:
                    q = st.number_input("Meta de Cotas:", min_value=1, value=100); st.write(f"💳 Desembolso: **R$ {q*pc:,.2f}**"); st.success(f"🚀 Renda Mensal: **R$ {q*rc:,.2f}**" if rc > 0 else "")
            else: st.error("Ativo offline.")
            
    with s2:
        jc1, jc2, jc3 = st.columns(3)
        with jc1: ap_ini = st.number_input("Aporte Inicial (R$):", 0.0, value=1000.0, step=100.0)
        with jc2: ap_mes = st.number_input("Aporte Mensal (R$):", 0.0, value=500.0, step=50.0)
        with jc3: tx_mes = st.number_input("Rendimento (% a.m.):",0.1, value=0.8, step=0.1)
        anos_j = st.slider("Horizonte (anos):", 1, 35, 10)
        meses_j = anos_j * 12; pat = ap_ini; inv = ap_ini; tx = tx_mes / 100; hs_m, hs_i, hs_j = [], [], []
        for mes in range(1, meses_j + 1):
            pat += pat * tx + ap_mes; inv += ap_mes
            if mes % 12 == 0: hs_m.append(f"Ano {mes//12}"); hs_i.append(inv); hs_j.append(pat - inv)
        rc1, rc2, rc3 = st.columns(3); rc1.metric("💵 Investido Total", f"R$ {inv:,.2f}"); rc2.metric("📈 Juros Acumulados", f"R$ {pat - inv:,.2f}"); rc3.metric("🏆 Patrimônio Final", f"R$ {pat:,.2f}")
        df_jc = pd.DataFrame({"Ano": hs_m, "Investido": hs_i, "Juros": hs_j})
        fig_jc = px.bar(df_jc, x="Ano", y=["Investido","Juros"], barmode="stack", color_discrete_map={"Investido":"#3b82f6","Juros":"#22c55e"})
        fig_jc.update_layout(height=300); st.plotly_chart(fig_jc, use_container_width=True, theme="streamlit")
        
    with s3:
        ra1, ra2, ra3 = st.columns(3)
        with ra1: meta_r = st.number_input("Renda Passiva Alvo (R$/mês):", min_value=10.0, value=1000.0, step=100.0)
        with ra2: preco_r = st.number_input("Preço da Cota (R$):", min_value=1.0, value=9.50, step=0.50)
        with ra3: rend_r = st.number_input("Dividendo Mensal (R$):", min_value=0.01, value=0.09, step=0.01)
        if rend_r > 0: cotas_n = meta_r / rend_r; st.success(f"🎯 Acumule **{int(cotas_n)} cotas**."); st.info(f"💼 Patrimônio Alvo Estimado: **R$ {cotas_n * preco_r:,.2f}**")
        
    with s4:
        st.markdown("Cálculo do DARF para Day Trade (20%)"); dd1, dd2 = st.columns(2)
        with dd1: bruto = st.number_input("Lucro Bruto (R$):", value=0.0, step=10.0); custos = st.number_input("Custos (R$):", min_value=0.0, value=0.0, step=5.0)
        with dd2: prej = st.number_input("Prejuízo Anterior (R$):", min_value=0.0, value=0.0, step=10.0); irrf = st.number_input("IRRF (R$):", min_value=0.0, value=0.0, step=1.0)
        if st.button("🧮 Calcular", type="primary"):
            liq = bruto - custos; st.write("---"); st.write(f"**Resultado Líquido:** R$ {liq:.2f}")
            if liq > 0:
                base = liq - prej
                if base > 0:
                    darf = (base * 0.20) - irrf
                    if darf <= 0: st.info("✅ Sem DARF.")
                    elif darf < 10: st.warning(f"⚠️ DARF R$ {darf:.2f} — Abaixo de R$ 10. Acumule.")
                    else: st.error(f"🚨 **DARF: R$ {darf:.2f}** | Cód 6015")
                else: st.warning(f"Lucro absorvido. Novo prejuízo acumulado: R$ {abs(base):.2f}")
            else: st.error(f"Mês no prejuízo.")

# --- ABA 11: CONSULTOR IA ---
with tab_ia:
    st.markdown("#### 🤖 ValorPro IA Intelligence")
    ARQUIVO_CHAT = "historico_ia.json"
    
    if CHAVE_API_GOOGLE != "COLE_SUA_CHAVE_AQUI" and CHAVE_API_GOOGLE.strip() != "":
        # Configuração da chave
        try:
            genai.configure(api_key=CHAVE_API_GOOGLE)
        except Exception as e:
            st.error(f"Erro ao configurar API: {e}")
            st.stop()

        col_ia1, col_ia2 = st.columns([4, 1])
        with col_ia2:
            if st.button("🗑️ Apagar Histórico", use_container_width=True):
                st.session_state.mensagens_ia = []
                if "chat_ia" in st.session_state: del st.session_state.chat_ia
                if os.path.exists(ARQUIVO_CHAT): os.remove(ARQUIVO_CHAT)
                st.rerun()

        if "mensagens_ia" not in st.session_state:
            if os.path.exists(ARQUIVO_CHAT):
                with open(ARQUIVO_CHAT, "r", encoding="utf-8") as f: 
                    st.session_state.mensagens_ia = json.load(f)
            else: 
                st.session_state.mensagens_ia = []
            
        if "chat_ia" not in st.session_state:
            try:
                # 🚀 O CAÇADOR: Usa a mesma lógica do Raio-X para nunca dar erro 404
                modelo_liberado = "gemini-1.5-flash" # Nome de segurança
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        modelo_liberado = m.name.replace("models/", "")
                        break # Pega o primeiro modelo que a sua chave aceita
                        
                model = genai.GenerativeModel(modelo_liberado)
                hist_gemini = [{"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]} for msg in st.session_state.mensagens_ia]
                st.session_state.chat_ia = model.start_chat(history=hist_gemini)
            except Exception as e: 
                st.error(f"Erro ao iniciar chat: {e}")

        for msg in st.session_state.mensagens_ia:
            with st.chat_message(msg["role"]): 
                st.markdown(msg["content"])

        if prompt := st.chat_input("Converse com seu assessor financeiro..."):
            st.session_state.mensagens_ia.append({"role": "user", "content": prompt})
            with open(ARQUIVO_CHAT, "w", encoding="utf-8") as f:
                json.dump(st.session_state.mensagens_ia, f, ensure_ascii=False, indent=4)
                
            with st.chat_message("user"): 
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analisando sua carteira e elaborando resposta..."):
                    try:
                        ctx = df_g.to_string() if "df_g" in locals() and not df_g.empty else "Carteira vazia."
                        
                        # INSTRUÇÃO DE PERSONALIDADE MESTRA
                        prompt_invisivel = (
                            f"Instrução de Personalidade: Você é o ValorPro IA, um assessor financeiro de elite, educado e prestativo. "
                            f"Se o usuário disser apenas 'oi', 'olá', ou fizer uma saudação simples, cumprimente-o cordialmente e pergunte o que ele gostaria de analisar hoje. "
                            f"Nunca traduza, corrija ou associe a palavra 'oi' a 'óleo' ou petróleo. Responda em Português do Brasil de forma clara.\n\n"
                            f"[DADOS ATUAIS DA CARTEIRA DO CLIENTE]\n{ctx}\n\n"
                            f"Mensagem do cliente: {prompt}"
                        )
                        
                        resposta = st.session_state.chat_ia.send_message(prompt_invisivel)
                        st.markdown(resposta.text)
                        
                        st.session_state.mensagens_ia.append({"role": "assistant", "content": resposta.text})
                        with open(ARQUIVO_CHAT, "w", encoding="utf-8") as f:
                            json.dump(st.session_state.mensagens_ia, f, ensure_ascii=False, indent=4)
                            
                    except Exception as e:
                        st.error(f"Erro na análise da IA: {e}")
    else:
        st.warning("⚠️ **A IA está dormindo. Configure sua chave API do Google para acordá-la.**") 


#ABA 12: IMPOSTO DE RENDA ---
with tab_ir:
    st.markdown("#### 🧾 Bens e Direitos & Histórico de Aquisição")
    st.info("📌 **Nota:** Esta tabela detalha cada compra individual para facilitar sua declaração e controle de valor real por data.")

    if not df_geral.empty and not df_g.empty:
        df_ir_detalhado = df_geral[['Data', 'Ticker', 'Categoria', 'Qtd', 'Preco_Pago']].copy()
        df_ir_detalhado['Custo_Aquisicao'] = df_ir_detalhado['Qtd'] * df_ir_detalhado['Preco_Pago']
        
        df_ir_display = pd.merge(df_ir_detalhado, df_g[['Ticker', 'Preço']], on='Ticker', how='left')
        df_ir_display['Valor_Atual_Lote'] = df_ir_display['Qtd'] * df_ir_display['Preço']
        
        categorias_puras = [str(c) for c in df_ir_display['Categoria'].unique() if pd.notnull(c)]
        cats_ir = sorted(categorias_puras)
        
        cats_ir_sel = st.multiselect("Filtrar por Classe:", options=cats_ir, default=cats_ir, key="ir_cat_filter_vfinal")
        
        df_ir_final = df_ir_display[df_ir_display['Categoria'].isin(cats_ir_sel)].copy() if cats_ir_sel else pd.DataFrame()

        if not df_ir_final.empty:
            st.markdown("##### 📅 Detalhamento por Data de Compra")
            
            df_view = df_ir_final[['Data', 'Ticker', 'Categoria', 'Qtd', 'Preco_Pago', 'Custo_Aquisicao', 'Valor_Atual_Lote']].copy()
            df_view.rename(columns={'Preco_Pago': 'Preço Pago (Un)', 'Custo_Aquisicao': 'Total Pago (R$)', 'Valor_Atual_Lote': 'Valor Hoje (R$)'}, inplace=True)

            st.dataframe(
                df_view.style.format({'Total Pago (R$)': 'R$ {:,.2f}', 'Valor Hoje (R$)': 'R$ {:,.2f}', 'Preço Pago (Un)': 'R$ {:,.2f}', 'Qtd': formatar_qtd }), 
                hide_index=True, use_container_width=True
            )

            st.divider()
            st.subheader("💡 Como declarar no Programa da Receita")
            df_grouped = df_ir_final.groupby('Ticker').agg({'Qtd': 'sum', 'Custo_Aquisicao': 'sum', 'Data': lambda x: list(x)}).reset_index()
            for _, g in df_grouped.iterrows():
                datas_u = sorted(list(set([d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d) for d in g['Data']])))
                with st.expander(f"📝 Texto para {g['Ticker']}"):
                    st.write(f"**Discriminação:** {formatar_qtd(g['Qtd'])} unidades de {g['Ticker']}, adquiridas em {', '.join(datas_u)}, pelo custo total de R$ {g['Custo_Aquisicao']:,.2f}.")
                    st.write(f"**Situação em 31/12:** R$ {g['Custo_Aquisicao']:,.2f}")
        else: st.warning("Selecione uma categoria no filtro.")
    else: st.info("Nenhum dado para exibir.")

# --- ABA 13: METAS ANALYTICS ---
with tab_metas:
    st.markdown("#### 🎯 Acompanhamento de Metas de Patrimônio")
    if not df_geral.empty and not df_g.empty:
        col_meta1, col_meta2 = st.columns([1, 1.5])
        patrimonio_atual = df_g["Total_Atual"].sum()
        
        with col_meta1:
            meta_patrimonio = st.number_input("Defina sua Meta de Patrimônio (R$):", min_value=1000.0, value=100000.0, step=10000.0)
            progresso = min(patrimonio_atual / meta_patrimonio, 1.0)
            falta = max(0, meta_patrimonio - patrimonio_atual)
            st.write(""); st.metric("Patrimônio Atual", f"R$ {patrimonio_atual:,.2f}"); st.metric("Falta para a Meta", f"R$ {falta:,.2f}")
            if progresso >= 1.0: st.success("🎉 PARABÉNS! Meta atingida ou ultrapassada!")
            else: st.info(f"Você já conquistou {progresso * 100:.2f}% do seu objetivo final.")
        
        with col_meta2:
            st.write(f"**Progresso: {progresso * 100:.2f}%**")
            st.progress(progresso)
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = patrimonio_atual, domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Velocímetro de Riqueza"}, number = {'prefix': "R$ "},
                gauge = {'axis': {'range': [None, meta_patrimonio]}, 'bar': {'color': "#1e3a8a"},
                    'steps': [{'range': [0, meta_patrimonio*0.3], 'color': "rgba(239, 68, 68, 0.2)"}, {'range': [meta_patrimonio*0.3, meta_patrimonio*0.7], 'color': "rgba(245, 158, 11, 0.2)"}, {'range': [meta_patrimonio*0.7, meta_patrimonio], 'color': "rgba(34, 197, 94, 0.2)"}]}
            ))
            fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True, theme="streamlit")
    else: st.info("Sua carteira está vazia.")

# --- ABA 14: HISTÓRICO E EDIÇÃO ---
with tab_edit:
    st.markdown("#### 📝 Auditoria e Gerenciamento")
    if not df_geral.empty:
        csv = df_geral.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Carteira em Excel (CSV)", data=csv, file_name="minha_carteira_nuvem.csv", mime="text/csv")
        
    he1, he2 = st.tabs(["✏️ Visualizar Lançamentos (Nuvem)", "📜 Histórico de Marcação"])
    with he1:
        st.info("Este é o espelho exato das suas operações salvas na nuvem do Supabase.")
        
        # Mostra a tabela limpa (sem mostrar os IDs feios do banco de dados)
        st.dataframe(df_geral.drop(columns=['id', 'usuario_id', 'criado_em'], errors='ignore'), hide_index=True, use_container_width=True)

        st.divider()
        st.markdown("#### 🗑️ Apagar Lançamento Incorreto")
        
        if 'id' in df_geral.columns:
            # Cria uma lista bonita para o usuário escolher o que apagar
            df_delete = df_geral.copy()
            # Transforma a data num formato legível caso não seja string
            df_delete['Data_Str'] = pd.to_datetime(df_delete['Data']).dt.strftime('%d/%m/%Y')
            df_delete['Descricao'] = df_delete['Data_Str'] + " | " + df_delete['Tipo'] + " de " + df_delete['Qtd'].astype(str) + "x " + df_delete['Ticker'] + " (R$ " + df_delete['Preco_Pago'].astype(str) + ")"
            
            # Cria um dicionário ligando o ID secreto à descrição bonita
            opcoes_delete = dict(zip(df_delete['id'], df_delete['Descricao']))
            
            with st.form("form_delete_op"):
                id_selecionado = st.selectbox("Selecione a operação que deseja apagar:", options=list(opcoes_delete.keys()), format_func=lambda x: opcoes_delete[x])
                
                col_btn1, col_btn2 = st.columns([1, 3])
                with col_btn1:
                    btn_apagar = st.form_submit_button("🗑️ Excluir Definitivamente")
                
                if btn_apagar:
                    try:
                        # Manda a ordem de exclusão para o Supabase baseada no ID único da linha
                        supabase.table("operacoes").delete().eq("id", id_selecionado).execute()
                        st.success("✅ Lançamento apagado com sucesso da Nuvem!")
                        st.session_state.df_geral = carregar_dados_nuvem() # Atualiza os dados
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao tentar apagar: {e}")

    with he2:
        df_log = carregar_log_precos()
        if not df_log.empty:
            st.dataframe(df_log.sort_index(ascending=False), hide_index=True, use_container_width=True)
        else: st.info("Nenhuma reavaliação de preço registrada ainda.")
