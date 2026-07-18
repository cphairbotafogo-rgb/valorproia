# ValorPro IA — Correções Aplicadas

## 🔴 Críticas (segurança e dinheiro)

1. **Senhas em texto puro no banco** — O cadastro salvava `"senha": nova_senha` sem hash, e a troca de senha também. Agora tudo usa `generate_password_hash` (Werkzeug). Contas antigas são migradas para hash automaticamente no primeiro login bem-sucedido, sem quebrar ninguém.

2. **Trial dava acesso Premium completo** — O cadastro criava o usuário com `status="ativo"` e `tipo="trial"`, mas `verificar_acesso()` via `status == "ativo"` e retornava `"premium"` direto. Resultado: **todo mundo do teste grátis usava as abas pagas (ValorPro IA, IR, Metas) sem pagar**. Corrigido: o tipo `trial` é verificado antes, com contagem de horas restantes baseada na data de expiração.

3. **Chaves do Supabase hardcoded no `migrar.py`** — URL e chave estavam commitadas no repositório. Agora vêm de variáveis de ambiente. **Recomendo rotacionar essa chave no painel do Supabase**, já que ela ficou exposta no Git.

4. **`migrar.py` transformava vendas em compras** — O script enviava `abs(qtd)` para o banco, mas o app inteiro trata venda como quantidade negativa. Toda venda migrada inflava a carteira. Corrigido: o sinal é preservado.

5. **Preço médio errado após vendas** (`banco.py`) — O `consolidar()` somava `Qtd × Preço` de compras E vendas, abatendo o custo pelo preço de venda em vez do preço médio. Exemplo real: comprar 100 a R$10 + 100 a R$12 e vender 50 a R$15 dava PM de R$9,67 — o correto (regra da Receita) é R$11,00. Reescrito com cálculo cronológico. Testado e validado.

6. **Preço médio do IR também errado** — A aba IR usava `'Preco_Pago':'mean'` (média simples dos preços, ignorando quantidades e vendas). O relatório de Bens e Direitos saía com valores incorretos. Agora usa o mesmo motor de consolidação correto.

## 🟠 Privacidade entre usuários

7. **Chat da IA era global** — `historico_ia.json` era um arquivo único: o histórico de conversa de um cliente aparecia para o outro. Agora é por usuário.

8. **Sessão não era limpa** — Ao deslogar e outro usuário logar no mesmo navegador, `df_geral`, `mensagens_ia` e `chat_ia` do usuário anterior continuavam na sessão. Agora login e logout limpam tudo.

9. **Preços manuais compartilhados** — `precos_manuais.csv` era global; agora é por usuário.

10. **Editar/apagar operações sem filtro de dono** — Os `update`/`delete` na tabela `operacoes` filtravam só por `id`. Adicionei `.eq("usuario_id", ...)` como defesa em profundidade.

## 🟡 Bugs funcionais

11. **Dividendos lançados "sumiam"** — O lançamento gravava em `dividendos_<usuario>.csv`, mas a leitura vinha de `meus_dividendos.csv` (constante global do `banco.py` importada via `import *`). O registro nunca aparecia na tela. Agora proventos ficam na tabela `proventos` do Supabase (rodar `migracao.sql`).

12. **Evolução Patrimonial zerava a cada deploy** — Snapshots em CSV local no Streamlit Cloud (disco efêmero). Agora ficam na tabela `snapshots_patrimonio`.

13. **`df_proventos` não existia** — A Visão Global somava uma variável nunca definida; o `try/except` escondia o `NameError`. Substituído pelo total real de proventos da nuvem.

14. **Senha errada não mostrava mensagem nenhuma** — Faltava o `else` no login. Adicionado "Senha incorreta".

15. **`st.caption` inalcançável** — Estava depois de `st.rerun()` na sidebar. Movido para antes do botão.

16. **`import *` duplicado** — `banco.py` e `motor.py` definiam `buscar_mercado`, `classificar_ativo` etc., e o `app_fii.py` redefinia tudo de novo. Qual versão valia dependia da ordem dos imports. Agora os imports são explícitos (`consolidar`, `carregar_log_precos`, `carregar_precos_manuais`, `descobrir_setor`).

## 🟢 Melhorias

17. **Fuso horário de Brasília** — O servidor do Streamlit Cloud roda em UTC; datas de operações, snapshots e ano-base do IR agora usam `America/Sao_Paulo`.
18. **Cache de cotações de 60s → 300s** — O TTL de 1 minuto forçava scraping do Fundamentus a cada rerun, deixando o app lento e arriscando bloqueio.
19. **Validação no cadastro** — E-mail com formato mínimo e senha com pelo menos 6 caracteres.
20. **`utcnow()` deprecado** — Substituído por `datetime.now(ZoneInfo("UTC"))`.

## ⚠️ O risco que sobrou (importante)

O app usa a **chave anon do Supabase sem Supabase Auth** — o login é feito consultando a tabela `usuarios` diretamente do front. Como não existe sessão autenticada, o RLS não tem como saber quem é o usuário, então as tabelas precisam ficar abertas para `anon`. Na prática, **quem extrair a chave anon consegue ler/escrever nas tabelas via API**. Com as senhas agora em hash o estrago de um vazamento cai muito, mas a correção definitiva é migrar para o **Supabase Auth + RLS por `auth.uid()`** (mesmo padrão `auth_salao_id()` que você já usa no Luarys). Posso fazer essa migração como próximo passo se quiser.

## 📋 Checklist de deploy

1. Rodar `migracao.sql` no SQL Editor do Supabase.
2. Substituir os 4 arquivos Python.
3. (Recomendado) Rotacionar a chave anon exposta no `migrar.py` antigo e atualizar o `secrets.toml`.
4. Redeploy no Streamlit Cloud.
