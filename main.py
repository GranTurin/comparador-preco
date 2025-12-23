import flet as ft
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO DO SEU SUPABASE ---
SUPABASE_URL = "https://mvozbjdmfkezdlzipstw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im12b3piamRtZmtlemRsemlwc3R3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY0NTEzMDksImV4cCI6MjA4MjAyNzMwOX0.pd76MIzgkfrbwvN0GlZxqIviKLEG49VCWRiXR4-13Bg"

# Conexão com a nuvem
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main(page: ft.Page):
    page.title = "Gestor de Preços Gran Turin"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450  # Formato de celular no PC
    page.expand = True

    # --- ELEMENTOS DE INTERFACE ---
    txt_whatsapp_num = ft.TextField(label="WhatsApp (DDD+Número)", border_radius=10, value="55")
    dd_prod = ft.Dropdown(label="Produto", expand=True)
    dd_merc = ft.Dropdown(label="Mercado", expand=True)
    txt_valor = ft.TextField(label="Preço R$", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
    
    txt_novo_prod = ft.TextField(label="Nome do Produto", expand=True)
    txt_alvo_cadastro = ft.TextField(label="Preço Alvo R$", expand=True, value="0.00")
    dd_cat_prod = ft.Dropdown(label="Categoria", expand=True)
    txt_novo_merc = ft.TextField(label="Novo Mercado", expand=True)
    txt_nova_cat = ft.TextField(label="Nova Categoria", expand=True)

    coluna_compara = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)
    lista_visu_cats = ft.Column()
    lista_visu_prods = ft.Column()
    lista_visu_mercs = ft.Column()

    # --- LOGICA DE DADOS (CLOUD) ---
    def carregar_dados(e=None):
        try:
            # Carregar Categorias
            res_cats = supabase.table("categorias").select("*").order("nome").execute()
            dd_cat_prod.options = [ft.dropdown.Option(c['nome']) for c in res_cats.data]
            lista_visu_cats.controls = [
                ft.ListTile(title=ft.Text(c['nome']), 
                trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, id=c['id']: deletar_item("categorias", id))) 
                for c in res_cats.data
            ]
            
            # Carregar Produtos
            res_prods = supabase.table("lista_produtos").select("*").order("nome").execute()
            dd_prod.options = [ft.dropdown.Option(p['nome']) for p in res_prods.data]
            lista_visu_prods.controls = []
            for p in res_prods.data:
                alvo = p.get('preco_alvo') or 0.0
                lista_visu_prods.controls.append(
                    ft.ListTile(title=ft.Text(p['nome']), subtitle=ft.Text(f"{p['categoria']} | Alvo: R$ {alvo:.2f}"),
                    trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, id=p['id']: deletar_item("lista_produtos", id)))
                )
            
            # Carregar Mercados
            res_mercs = supabase.table("lista_mercados").select("*").order("nome").execute()
            dd_merc.options = [ft.dropdown.Option(m['nome']) for m in res_mercs.data]
            lista_visu_mercs.controls = [
                ft.ListTile(title=ft.Text(m['nome']), 
                trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, id=m['id']: deletar_item("lista_mercados", id))) 
                for m in res_mercs.data
            ]
            page.update()
        except Exception as ex:
            print(f"Erro: {ex}")

    def deletar_item(tabela, id_item):
        supabase.table(tabela).delete().eq("id", id_item).execute()
        carregar_dados()
        atualizar_comparativo()

    def salvar_preco(e):
        if dd_prod.value and dd_merc.value and txt_valor.value:
            res = supabase.table("lista_produtos").select("categoria").eq("nome", dd_prod.value).execute()
            cat = res.data[0]['categoria']
            supabase.table("precos").insert({
                "produto": dd_prod.value, 
                "mercado": dd_merc.value, 
                "valor": float(txt_valor.value.replace(",", ".")), 
                "categoria": cat
            }).execute()
            txt_valor.value = ""
            atualizar_comparativo()

    def atualizar_comparativo(e=None):
        coluna_compara.controls.clear()
        res_precos = supabase.table("precos").select("*").execute()
        if not res_precos.data: 
            page.update()
            return
        
        cats_unificadas = sorted(list(set([p['categoria'] for p in res_precos.data])))
        
        for c_nome in cats_unificadas:
            coluna_compara.controls.append(ft.Container(content=ft.Text(c_nome, color="white", weight="bold"), bgcolor="bluegrey", padding=10, border_radius=5))
            
            prods_na_cat = sorted(list(set([p['produto'] for p in res_precos.data if p['categoria'] == c_nome])))
            for p_nome in prods_na_cat:
                res_alvo = supabase.table("lista_produtos").select("preco_alvo").eq("nome", p_nome).execute()
                alvo = res_alvo.data[0]['preco_alvo'] if res_alvo.data else 0.0
                
                precos_prod = [p for p in res_precos.data if p['produto'] == p_nome]
                precos_prod.sort(key=lambda x: x['valor'])
                
                cards = []
                for i, p_item in enumerate(precos_prod):
                    vencedor = (i == 0)
                    oferta = (p_item['valor'] <= alvo if alvo > 0 else False)
                    cards.append(ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.STAR, color="amber" if oferta else "transparent", size=20),
                            ft.Text(f"{p_item['mercado']}", expand=True, weight="bold" if vencedor else "normal"),
                            ft.Text(f"R$ {p_item['valor']:.2f}", weight="bold", color="green" if vencedor else "black"),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, on_click=lambda e, idx=p_item['id']: (supabase.table("precos").delete().eq("id", idx).execute(), atualizar_comparativo()))
                        ]),
                        padding=10, bgcolor="amber100" if oferta else ("green50" if vencedor else "white"),
                        border=ft.border.all(1, "amber" if oferta else "grey300"), border_radius=8
                    ))
                coluna_compara.controls.append(ft.Column([ft.Text(f"📦 {p_nome} (Alvo: R$ {alvo:.2f})", weight="bold"), *cards]))
        page.update()

    # --- INTERFACE (ABAS) ---
    aba_precos = ft.Container(padding=20, content=ft.Column([
        ft.Row([ft.Text("📊 Comparativo Cloud", size=24, weight="bold"), 
                ft.IconButton(ft.Icons.REFRESH, tooltip="Sincronizar", on_click=lambda _: (carregar_dados(), atualizar_comparativo()))], 
                alignment="spaceBetween"),
        txt_whatsapp_num,
        ft.Row([dd_prod, dd_merc]),
        ft.Row([txt_valor, ft.ElevatedButton("Salvar Preço", on_click=salvar_preco, icon=ft.Icons.SAVE)]),
        ft.Divider(),
        coluna_compara
    ]))

    aba_cadastros = ft.Container(padding=20, content=ft.Column([
        ft.ExpansionTile(title=ft.Text("1. Categorias"), controls=[ft.Row([txt_nova_cat, ft.IconButton(ft.Icons.ADD, on_click=lambda _: (supabase.table("categorias").insert({"nome": txt_nova_cat.value.upper()}).execute(), (setattr(txt_nova_cat, 'value', ''), carregar_dados())))]) , lista_visu_cats]),
        ft.ExpansionTile(title=ft.Text("2. Produtos"), controls=[ft.Row([txt_novo_prod, txt_alvo_cadastro, dd_cat_prod, ft.IconButton(ft.Icons.ADD, on_click=lambda _: (supabase.table("lista_produtos").insert({"nome": txt_novo_prod.value.upper(), "categoria": dd_cat_prod.value, "preco_alvo": float(txt_alvo_cadastro.value)}).execute(), (setattr(txt_novo_prod, 'value', ''), setattr(txt_alvo_cadastro, 'value', '0.00'), carregar_dados())))]) , lista_visu_prods]),
        ft.ExpansionTile(title=ft.Text("3. Mercados"), controls=[ft.Row([txt_novo_merc, ft.IconButton(ft.Icons.ADD, on_click=lambda _: (supabase.table("lista_mercados").insert({"nome": txt_novo_merc.value.upper()}).execute(), (setattr(txt_novo_merc, 'value', ''), carregar_dados())))]) , lista_visu_mercs]),
    ], scroll=ft.ScrollMode.ALWAYS))

    page.add(ft.Tabs(expand=True, tabs=[ft.Tab(text="Preços", content=aba_precos), ft.Tab(text="Cadastros", content=aba_cadastros)]))
    carregar_dados(); atualizar_comparativo()

ft.app(target=main)
