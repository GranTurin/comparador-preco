import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- CONFIGURAÇÃO DO SUPABASE ---
SUPABASE_URL = "https://mvozbjdmfkezdlzipstw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im12b3piamRtZmtlemRsemlwc3R3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY0NTEzMDksImV4cCI6MjA4MjAyNzMwOX0.pd76MIzgkfrbwvN0GlZxqIviKLEG49VCWRiXR4-13Bg"

# Conexão com a nuvem
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="Gestor Gran Turin", layout="centered")
st.title("📊 Gestor de Preços Gran Turin")

# --- ABAS ---
tab1, tab2 = st.tabs(["💰 Preços", "⚙️ Cadastros"])

# --- ABA 1: PREÇOS ---
with tab1:
    # Carregar dados para os selects
    res_prods = supabase.table("lista_produtos").select("nome").order("nome").execute()
    res_mercs = supabase.table("lista_mercados").select("nome").order("nome").execute()
    
    prods = [p['nome'] for p in res_prods.data]
    mercs = [m['nome'] for m in res_mercs.data]

    with st.expander("➕ Lançar Novo Preço", expanded=True):
        col1, col2 = st.columns(2)
        prod_sel = col1.selectbox("Produto", prods)
        merc_sel = col2.selectbox("Mercado", mercs)
        valor_input = st.number_input("Preço R$", min_value=0.0, step=0.01, format="%.2f")
        
        if st.button("Salvar Preço"):
            # Buscar categoria do produto
            res_cat = supabase.table("lista_produtos").select("categoria").eq("nome", prod_sel).execute()
            cat = res_cat.data[0]['categoria']
            
            supabase.table("precos").insert({
                "produto": prod_sel,
                "mercado": merc_sel,
                "valor": valor_input,
                "categoria": cat
            }).execute()
            st.success("Preço salvo!")
            st.rerun()

    st.divider()

    # --- LISTAGEM COMPARATIVA ---
    res_precos = supabase.table("precos").select("*").execute()
    if res_precos.data:
        df = pd.DataFrame(res_precos.data)
        cats = sorted(df['categoria'].unique())

        for cat in cats:
            st.subheader(f"📂 {cat}")
            df_cat = df[df['categoria'] == cat]
            
            produtos_na_cat = sorted(df_cat['produto'].unique())
            for p_nome in produtos_na_cat:
                # Buscar Preço Alvo
                res_alvo = supabase.table("lista_produtos").select("preco_alvo").eq("nome", p_nome).execute()
                alvo = res_alvo.data[0]['preco_alvo'] if res_alvo.data else 0.0
                
                st.write(f"**📦 {p_nome}** (Alvo: R$ {alvo:.2f})")
                
                precos_prod = df_cat[df_cat['produto'] == p_nome].sort_values(by="valor")
                
                for idx, row in precos_prod.iterrows():
                    venc = "🏆" if row['valor'] == precos_prod['valor'].min() else ""
                    oferta = "⭐" if (alvo > 0 and row['valor'] <= alvo) else ""
                    
                    col_m, col_v, col_d = st.columns([3, 2, 1])
                    col_m.write(f"{venc} {oferta} {row['mercado']}")
                    col_v.write(f"**R$ {row['valor']:.2f}**")
                    if col_d.button("🗑️", key=f"del_{row['id']}"):
                        supabase.table("precos").delete().eq("id", row['id']).execute()
                        st.rerun()
            st.divider()

# --- ABA 2: CADASTROS ---
with tab2:
    st.header("Gerenciar Listas")
    
    # Categorias
    with st.expander("1. Categorias"):
        nova_cat = st.text_input("Nova Categoria").upper()
        if st.button("Add Categoria") and nova_cat:
            supabase.table("categorias").insert({"nome": nova_cat}).execute()
            st.rerun()
        
        res_c = supabase.table("categorias").select("*").order("nome").execute()
        for c in res_c.data:
            col_a, col_b = st.columns([4, 1])
            col_a.write(c['nome'])
            if col_b.button("Excluir", key=f"cat_{c['id']}"):
                supabase.table("categorias").delete().eq("id", c['id']).execute()
                st.rerun()

    # Produtos
    with st.expander("2. Produtos"):
        res_cats_list = supabase.table("categorias").select("nome").execute()
        cats_list = [c['nome'] for c in res_cats_list.data]
        
        col_p1, col_p2 = st.columns(2)
        n_prod = col_p1.text_input("Nome Produto").upper()
        n_alvo = col_p2.number_input("Preço Alvo", min_value=0.0, step=0.1)
        n_cat = st.selectbox("Categoria do Produto", cats_list)
        
        if st.button("Add Produto") and n_prod:
            supabase.table("lista_produtos").insert({"nome": n_prod, "categoria": n_cat, "preco_alvo": n_alvo}).execute()
            st.rerun()

    # Mercados
    with st.expander("3. Mercados"):
        n_merc = st.text_input("Novo Mercado").upper()
        if st.button("Add Mercado") and n_merc:
            supabase.table("lista_mercados").insert({"nome": n_merc}).execute()
            st.rerun()
