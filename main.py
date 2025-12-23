import streamlit as st
from supabase import create_client, Client
import pandas as pd
import urllib.parse

# --- CONFIGURAÇÃO DO SUPABASE ---
SUPABASE_URL = "https://mvozbjdmfkezdlzipstw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im12b3piamRtZmtlemRsemlwc3R3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY0NTEzMDksImV4cCI6MjA4MjAyNzMwOX0.pd76MIzgkfrbwvN0GlZxqIviKLEG49VCWRiXR4-13Bg"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="Gestor Gran Turin", layout="centered")
st.title("📊 Gestor de Preços Gran Turin")

tab1, tab2 = st.tabs(["💰 Preços", "⚙️ Cadastros"])

with tab1:
    # Campo do WhatsApp
    whatsapp_num = st.text_input("WhatsApp para envio (DDD+Número)", value="55")

    # Carregar dados
    res_prods = supabase.table("lista_produtos").select("nome").order("nome").execute()
    res_mercs = supabase.table("lista_mercados").select("nome").order("nome").execute()
    prods = [p['nome'] for p in res_prods.data]
    mercs = [m['nome'] for m in res_mercs.data]

    with st.expander("➕ Lançar Novo Preço"):
        col1, col2 = st.columns(2)
        prod_sel = col1.selectbox("Produto", prods)
        merc_sel = col2.selectbox("Mercado", mercs)
        valor_input = st.number_input("Preço R$", min_value=0.0, step=0.01, format="%.2f")
        if st.button("Salvar Preço"):
            res_cat = supabase.table("lista_produtos").select("categoria").eq("nome", prod_sel).execute()
            cat = res_cat.data[0]['categoria']
            supabase.table("precos").insert({"produto": prod_sel, "mercado": merc_sel, "valor": valor_input, "categoria": cat}).execute()
            st.rerun()

    st.divider()

    # LISTAGEM
    res_precos = supabase.table("precos").select("*").execute()
    if res_precos.data:
        df = pd.DataFrame(res_precos.data)
        for cat in sorted(df['categoria'].unique()):
            st.markdown(f"### 📂 {cat}")
            df_cat = df[df['categoria'] == cat]
            
            for p_nome in sorted(df_cat['produto'].unique()):
                res_alvo = supabase.table("lista_produtos").select("preco_alvo").eq("nome", p_nome).execute()
                alvo = res_alvo.data[0]['preco_alvo'] if res_alvo.data else 0.0
                
                st.write(f"**📦 {p_nome}** (Alvo: R$ {alvo:.2f})")
                precos_prod = df_cat[df_cat['produto'] == p_nome].sort_values(by="valor")
                
                min_price = precos_prod['valor'].min()

                for _, row in precos_prod.iterrows():
                    venc = row['valor'] == min_price
                    oferta = (alvo > 0 and row['valor'] <= alvo)
                    
                    # Definição de Cores (CSS)
                    bg_color = "#d4edda" if venc else "white" # Verde se for o mais barato
                    if oferta: bg_color = "#fff3cd" # Amarelo se for oferta alvo
                    
                    # Layout da linha de preço
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color:{bg_color}; padding:10px; border-radius:10px; border:1px solid #ddd; margin-bottom:5px">
                            <span style="font-weight:bold">{'🏆 ' if venc else ''}{'⭐ ' if oferta else ''}{row['mercado']}</span>: 
                            <span style="color:green; font-weight:bold">R$ {row['valor']:.2f}</span>
                        </div>
                        """, unsafe_allow_value=True)
                        
                        c1, c2, _ = st.columns([1, 1, 3])
                        # Botão WhatsApp
                        texto_wa = urllib.parse.quote(f"Preço do {p_nome} no {row['mercado']}: R$ {row['valor']:.2f}")
                        link_wa = f"https://wa.me/{whatsapp_num}?text={texto_wa}"
                        c1.markdown(f"[📲 Enviar]({link_wa})")
                        
                        if c2.button("🗑️", key=f"del_{row['id']}"):
                            supabase.table("precos").delete().eq("id", row['id']).execute()
                            st.rerun()
            st.divider()

with tab2:
    # (Mantive a mesma lógica de cadastros do código anterior)
    st.header("Gerenciar Listas")
    with st.expander("1. Categorias"):
        n_cat = st.text_input("Nova Categoria").upper()
        if st.button("Add Categoria") and n_cat:
            supabase.table("categorias").insert({"nome": n_cat}).execute()
            st.rerun()
    with st.expander("2. Produtos"):
        res_c = supabase.table("categorias").select("nome").execute()
        cs = [c['nome'] for c in res_c.data]
        p_n = st.text_input("Nome Produto").upper()
        p_a = st.number_input("Alvo", min_value=0.0)
        p_c = st.selectbox("Categoria", cs)
        if st.button("Add Produto"):
            supabase.table("lista_produtos").insert({"nome": p_n, "categoria": p_c, "preco_alvo": p_a}).execute()
            st.rerun()
    with st.expander("3. Mercados"):
        m_n = st.text_input("Novo Mercado").upper()
        if st.button("Add Mercado"):
            supabase.table("lista_mercados").insert({"nome": m_n}).execute()
            st.rerun()
