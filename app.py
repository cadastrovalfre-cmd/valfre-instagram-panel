import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import sqlite3
from datetime import datetime
from openai import OpenAI

# ================= CONFIG =================

st.set_page_config(page_title="Valfre Instagram Auto", layout="wide")
st.title("🤖 Valfre Instagram Auto Generator")

SITE_URL = st.secrets.get("SITE_URL", "https://www.ferramentasvalfre.com.br")

# ================= DATABASE =================

conn = sqlite3.connect("valfre.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT,
    content TEXT,
    created_at TEXT
)
""")
conn.commit()

# ================= FUNCTIONS =================

def get_products():
    try:
        response = requests.get(SITE_URL, timeout=15)
        soup = BeautifulSoup(response.text, "lxml")

        produtos = soup.find_all("a")

        lista = []
        for p in produtos:
            href = p.get("href")
            texto = p.get_text(strip=True)

            if href and texto and len(texto) > 5:
                if "/produto" in href.lower() or "/p/" in href.lower():
                    lista.append({
                        "title": texto,
                        "link": href if href.startswith("http") else SITE_URL + href
                    })

        return lista
    except:
        return []

def generate_post(product):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    prompt = f"""
    Crie um post altamente persuasivo para Instagram vendendo:

    Produto: {product['title']}
    Loja: Ferramentas Valfre
    Site: {product['link']}

    Inclua:
    - Benefícios claros
    - Problema que resolve
    - Chamada forte para ação
    - Emojis estratégicos
    - Hashtags nichadas de ferramentas

    Tom comercial agressivo e profissional.
    """

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return resposta.choices[0].message.content

# ================= UI =================

if "posts_cache" not in st.session_state:
    st.session_state.posts_cache = get_products()

st.sidebar.header("⚙ Configurações")
if st.sidebar.button("🔄 Atualizar Produtos"):
    st.session_state.posts_cache = get_products()
    st.success("Produtos atualizados!")

st.header("📦 Produtos encontrados")

if not st.session_state.posts_cache:
    st.warning("Nenhum produto encontrado. Verifique o site.")
else:
    produto_escolhido = random.choice(st.session_state.posts_cache)

    st.success(f"Produto selecionado: {produto_escolhido['title']}")
    st.write(produto_escolhido["link"])

    if st.button("🚀 Gerar Post Agora"):
        with st.spinner("Gerando post..."):
            post = generate_post(produto_escolhido)

            cursor.execute(
                "INSERT INTO posts (product, content, created_at) VALUES (?, ?, ?)",
                (produto_escolhido["title"], post, datetime.now().isoformat())
            )
            conn.commit()

            st.markdown("## 📌 Post Gerado")
            st.write(post)

st.header("📊 Histórico")

cursor.execute("SELECT product, created_at FROM posts ORDER BY id DESC LIMIT 10")
historico = cursor.fetchall()

for h in historico:
    st.write(f"🛠 {h[0]} — {h[1]}")
