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
    whatsapp_num = st.text_input("WhatsApp para envio (55 + DDD + Número)", value="55")

    try:
        res_prods = supabase.table("lista_produtos").select("nome").order("nome").execute()
        res_mercs = supabase.table("lista_mercados").select("nome").order("nome").execute()
        prods = [p['nome'] for p in res_prods.data] if res_prods.data else []
        mercs = [m['nome'] for m in res_mercs.data] if res_mercs.data else []
    except:
        prods, mercs = [], []

    with st.expander("➕ Lançar Novo Preço"):
        col1, col2 = st.columns(2)
        prod_sel = col1.selectbox("Produto", prods)
        merc_sel = col2.selectbox("Mercado", mercs)
        valor_input = st.number_input("Preço R$", min_value=0.0, step=0.01, format="%.2f")
        if st.button("Salvar Preço"):
            res_cat = supabase.table("lista_produtos").select("categoria").eq("nome", prod_sel).execute()
            cat = res_cat.data[0]['categoria'] if res_cat.data else "Geral"
            supabase.table("precos").insert({"produto": prod_sel, "mercado": merc_sel, "valor": valor_input, "categoria": cat}).execute()
            st.rerun()

    st.divider()

    # --- LÓGICA DA LISTA DE MELHORES PREÇOS PARA WHATSAPP ---
    res_precos = supabase.table("precos").select("*").execute()
    
    if res_precos.data:
        df = pd.DataFrame(res_precos.data)
        
        # Criar a mensagem de resumo
        texto_resumo = "*🛒 MELHORES PREÇOS ENCONTRADOS:*\n\n"
        
        # Agrupar para achar o menor preço de cada produto
        for p_nome in sorted(df['produto'].unique()):
            df_p = df[df['produto'] == p_nome]
            menor_linha = df_p.loc[df_p['valor'].idxmin()]
            texto_resumo += f"✅ *{p_nome}*\n📍 {menor_linha['mercado']}: R$ {menor_linha['valor']:.2f}\n\n"
        
        link_resumo = f"https://wa.me/{whatsapp_num}?text={urllib.parse.quote(texto_resumo)}"
        
        st.link_button("📲 Enviar Lista de Menores Preços", link_resumo, type="primary", use_container_width=True)
        st.divider()

        # LISTAGEM VISUAL (CARDS)
        for cat in sorted(df['categoria'].unique()):
            st.markdown(f"#### 📂 {cat}")
            df_cat = df[df['categoria'] == cat]
            
            for p_nome in sorted(df_cat['produto'].unique()):
                res_alvo = supabase.table("lista_produtos").select("preco_alvo").eq("nome", p_nome).execute()
                alvo = res_alvo.data[0]['preco_alvo'] if res_alvo.data else 0.0
                
                st.write(f"**📦 {p_nome}** (Alvo: R$ {alvo:.2f})")
                precos_prod = df_cat[df_cat['produto'] == p_nome].sort_values(by="valor")
                min_price = precos_prod['valor'].min()

                for _, row in precos_prod.iterrows():
                    venc = (row['valor'] == min_price)
                    oferta = (alvo > 0 and row['valor'] <= alvo)
                    bg = "#d4edda" if venc else "#ffffff"
                    if oferta: bg = "#fff3cd"
                    
                    st.markdown(f"""
                        <div style="background-color:{bg}; padding:12px; border-radius:8px; border:1px solid #eee; margin-bottom:10px; color: black;">
                            <div style="display: flex; justify-content: space-between;">
                                <span>{'🏆 ' if venc else ''}{'⭐ ' if oferta else ''}<b>{row['mercado']}</b></span>
                                <span style="color: green; font-weight: bold;">R$ {row['valor']:.2f}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Deletar", key=f"del_{row['id']}"):
                        supabase.table("precos").delete().eq("id", row['id']).execute()
                        st.rerun()
            st.divider()

with tab2:
    st.header("⚙️ Configurações")
    with st.expander("1. Categorias"):
        n_cat = st.text_input("Nome da Categoria").upper()
        if st.button("Adicionar Categoria") and n_cat:
            supabase.table("categorias").insert({"nome": n_cat}).execute()
            st.rerun()
            
    with st.expander("2. Produtos"):
        res_c = supabase.table("categorias").select("nome").execute()
        cs = [c['nome'] for c in res_c.data] if res_c.data else []
        p_n = st.text_input("Nome do Produto").upper()
        p_a = st.number_input("Preço Alvo (R$)", min_value=0.0)
        p_c = st.selectbox("Selecione a Categoria", cs)
        if st.button("Adicionar Produto"):
            supabase.table("lista_produtos").insert({"nome": p_n, "categoria": p_c, "preco_alvo": p_a}).execute()
            st.rerun()

    with st.expander("3. Mercados"):
        m_n = st.text_input("Nome do Mercado").upper()
        if st.button("Adicionar Mercado"):
            supabase.table("lista_mercados").insert({"nome": m_n}).execute()
            st.rerun()
