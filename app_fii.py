# --- ABA 6: CRIPTOMOEDAS ---
with tab_cripto:
    if not df_g.empty:
        criptos = df_g[df_g["Categoria"] == "Criptomoedas"].copy()
        if not criptos.empty:
            criptos.fillna({"Status": "⚡ Volátil", "Var_Dia": 0.0}, inplace=True)
            m1, m2, col_vaz, col_pie_cripto = st.columns([1,1,1,1.2])
            m1.metric("🪙 Patrimônio Cripto", f"R$ {criptos['Total_Atual'].sum():,.2f}")
            lp_cripto = (criptos["Total_Atual"] - criptos["Custo_Pos"]).sum(); ct_cripto = criptos["Custo_Pos"].sum()
            m2.metric("📈 Valorização", f"R$ {lp_cripto:,.2f}", f"{lp_cripto/ct_cripto*100:+.2f}%" if ct_cripto > 0 else "")
            
            with col_pie_cripto:
                fig_cripto = px.pie(criptos, values="Total_Atual", names="Ticker", hole=0.4, color_discrete_sequence=["#eab308", "#ca8a04", "#854d0e"])
                fig_cripto.update_layout(**PLOTLY_DARK, height=200, showlegend=False)
                fig_cripto.update_traces(textposition="inside", textinfo="percent+label", textfont_color="white")
                st.plotly_chart(fig_cripto, use_container_width=True)

            criptos["L/P (R$)"] = criptos["Total_Atual"] - criptos["Custo_Pos"]
            criptos["L/P (%)"] = criptos.apply(lambda r: (r["L/P (R$)"] / r["Custo_Pos"] * 100) if r["Custo_Pos"] > 0 else 0, axis=1)

            # RECUPERANDO A COLUNA DE CUSTO TOTAL DA FRAÇÃO E VARIÁVEIS DO V7
            df_vcripto = criptos[["Ticker","Qtd","Preco_Medio","Custo_Pos","Preço","Var_Dia","Total_Atual","L/P (R$)","L/P (%)","Status"]].copy()
            
            df_vcripto.rename(columns={
                "Preco_Medio": "PM (1 Moeda)", 
                "Custo_Pos": "Total Investido (R$)", # <- O valor da fração que você pagou
                "Preço": "Preço Atual", 
                "Var_Dia": "Var. Dia %", 
                "Total_Atual": "Patrimônio (R$)"
            }, inplace=True)
            
            df_vcripto["Var. Dia %"] = df_vcripto["Var. Dia %"].apply(lambda x: formatar_delta(x, True))
            df_vcripto["L/P (R$)"] = df_vcripto["L/P (R$)"].apply(lambda x: formatar_delta(x))
            df_vcripto["L/P (%)"]  = df_vcripto["L/P (%)"].apply(lambda x: formatar_delta(x, True))
            
            df_vcripto["Total Investido (R$)"] = df_vcripto["Total Investido (R$)"].apply(lambda x: f"R$ {x:,.2f}")
            df_vcripto["PM (1 Moeda)"] = df_vcripto["PM (1 Moeda)"].apply(lambda x: f"R$ {x:,.2f}")
            df_vcripto["Preço Atual"] = df_vcripto["Preço Atual"].apply(lambda x: f"R$ {x:,.2f}")
            df_vcripto["Patrimônio (R$)"] = df_vcripto["Patrimônio (R$)"].apply(lambda x: f"R$ {x:,.2f}")
            
            df_vcripto["Qtd"] = df_vcripto["Qtd"].apply(formatar_qtd)
            
            st.dataframe(df_vcripto, hide_index=True, use_container_width=True)
        else: 
            st.info("Nenhuma Criptomoeda registrada.")
    else: 
        st.info("Sua carteira está vazia.")
