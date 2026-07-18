# -*- coding: utf-8 -*-
"""
Script de migração: envia o CSV local de transações para a nuvem (Supabase).

⚠️ SEGURANÇA: as chaves NÃO ficam mais no código. Antes de rodar, defina:
    export SUPABASE_URL="https://SEU-PROJETO.supabase.co"
    export SUPABASE_KEY="sua_chave"
    export EMAIL_USUARIO="email_do_usuario_no_banco"

Uso:  python migrar.py
"""
import os
import sys
import time
from datetime import datetime

import pandas as pd
from supabase import create_client, Client

URL_SUPABASE   = os.environ.get("SUPABASE_URL", "")
CHAVE_SUPABASE = os.environ.get("SUPABASE_KEY", "")
EMAIL_USUARIO  = os.environ.get("EMAIL_USUARIO", "")
NOME_ARQUIVO   = os.environ.get("ARQUIVO_CSV", "minhas_transacoes.csv")

if not URL_SUPABASE or not CHAVE_SUPABASE or not EMAIL_USUARIO:
    print("❌ Defina as variáveis de ambiente SUPABASE_URL, SUPABASE_KEY e EMAIL_USUARIO antes de rodar.")
    sys.exit(1)

supabase: Client = create_client(URL_SUPABASE, CHAVE_SUPABASE)

try:
    print("Conectando ao banco de dados...")
    res_user = supabase.table("usuarios").select("id").eq("e-mail", EMAIL_USUARIO.strip().lower()).execute()
    if not res_user.data:
        print(f"❌ Usuário '{EMAIL_USUARIO}' não encontrado na tabela 'usuarios'.")
        sys.exit(1)
    usuario_id = res_user.data[0]["id"]

    print(f"Lendo o arquivo {NOME_ARQUIVO}...")
    df_antigo = pd.read_csv(NOME_ARQUIVO)

    # Se a data estiver vazia (NaN), preenche com a data de hoje
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    df_antigo["Data"] = df_antigo["Data"].fillna(data_hoje)

    sucessos = 0
    print("Iniciando envio de dados para a nuvem...\n")

    for _, row in df_antigo.iterrows():
        qtd = float(row["Qtd"])
        tipo_op = "Compra" if qtd > 0 else "Venda"

        data_str = str(row["Data"])[:10]
        if data_str.lower() == "nan":
            data_str = data_hoje

        nova_op = {
            "usuario_id":     usuario_id,
            "ticker":         str(row["Ticker"]).upper().strip(),
            "tipo":           tipo_op,
            "quantidade":     qtd,  # mantém o sinal: negativo = venda (padrão do app)
            "preco_unitario": float(row["Preco_Pago"]),
            "data_operacao":  data_str,
        }

        supabase.table("operacoes").insert(nova_op).execute()
        print(f"✅ Migrado: {tipo_op} de {abs(qtd)}x {row['Ticker']}")
        sucessos += 1
        time.sleep(0.1)

    print(f"\n🎉 Concluído! {sucessos} operações migradas para a nuvem.")

except Exception as e:
    print(f"❌ Ocorreu um erro: {e}")
