import pandas as pd
from supabase import create_client, Client
import time
from datetime import datetime

# 1. COLOQUE SUAS CHAVES AQUI:
URL_SUPABASE = "https://dcvbigplgruvaojmutth.supabase.co"
CHAVE_SUPABASE = "sb_publishable_faAlM9DLISD2Oxl--wiS7g_keLzPZI0"

supabase: Client = create_client(URL_SUPABASE, CHAVE_SUPABASE)
EMAIL_USUARIO = "admin"

try:
    print("Conectando ao banco de dados...")
    res_user = supabase.table("usuarios").select("id").eq("email", EMAIL_USUARIO).execute()
    usuario_id = res_user.data[0]['id']
    
    NOME_ARQUIVO = "minhas_transacoes.csv" 
    print(f"Lendo o arquivo {NOME_ARQUIVO}...")
    df_antigo = pd.read_csv(NOME_ARQUIVO)
    
    # TRUQUE DE MESTRE: Se a data estiver vazia (NaN), preenche com a data de hoje
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    df_antigo['Data'] = df_antigo['Data'].fillna(data_hoje)
    
    sucessos = 0
    print("Iniciando injeção de dados na nuvem...\n")
    
    for index, row in df_antigo.iterrows():
        qtd = float(row["Qtd"])
        tipo_op = "Compra" if qtd > 0 else "Venda"
        
        # Garante que não vai mandar a palavra 'nan'
        data_str = str(row["Data"])[:10]
        if data_str.lower() == "nan":
            data_str = data_hoje
            
        nova_op = {
            "usuario_id": usuario_id,
            "ticker": str(row["Ticker"]).upper(),
            "tipo": tipo_op,
            "quantidade": abs(qtd),
            "preco_unitario": float(row["Preco_Pago"]),
            "data_operacao": data_str
        }
        
        supabase.table("operacoes").insert(nova_op).execute()
        print(f"✅ Migrado: {tipo_op} de {abs(qtd)}x {row['Ticker']}")
        sucessos += 1
        time.sleep(0.1)
        
    print(f"\n🎉 SUCESSO ABSOLUTO! {sucessos} operações foram migradas para a Nuvem!")

except Exception as e:
    print(f"❌ Ocorreu um erro: {e}")