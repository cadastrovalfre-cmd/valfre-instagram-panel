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

conn = sqlite3.connect("valfre.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT,
    link TEXT,
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

        products = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text(strip=True)

            if (
                title
                and len(title) > 6
                and ("/produto" in href.lower() or "/p/" in href.lower())
            ):
                link = href if href.startswith("http") else SITE_URL + href
                products.append({"title": title, "link": link})

        return list({p["link"]: p for p in products}.values())

    except Exception as e:
        st.error(f"Erro ao buscar produtos: {e}")
        return []


def generate_post(product):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    prompt = f"""
Crie um post altamente persuasivo para Instagram vendendo:

Produto: {product['title']}
Link: {product['link']}
Loja: Ferramentas Valfre

Inclua:
- Benefícios claros
- Problema que resolve
- Chamada forte para ação
- Emojis estratégicos
- Hashtags nichadas de ferramentas

Tom comercial forte e profissional.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ================= UI =================

st.sidebar.header("⚙ Configurações")

if st.sidebar.button("🔄 Atualizar Produtos"):
    st.session_state.products = get_products()
    st.success("Produtos atualizados!")

if "products" not in st.session_state:
    st.session_state.products = get_products()

st.header("📦 Produtos Encontrados")

if not st.session_state.products:
    st.warning("Nenhum produto encontrado.")
else:
    product = random.choice(st.session_state.products)

    st.success(f"Produto selecionado: {product['title']}")
    st.write(product["link"])

    if st.button("🚀 Gerar Post"):
        with st.spinner("Gerando conteúdo..."):
            post = generate_post(product)

            cursor.execute(
                "INSERT INTO posts (product, link, content, created_at) VALUES (?, ?, ?, ?)",
                (product["title"], product["link"], post, datetime.now().isoformat())
            )
            conn.commit()

            st.markdown("## 📌 Post Gerado")
            st.write(post)

# ================= HISTÓRICO =================

st.header("📊 Histórico")

cursor.execute("SELECT product, created_at FROM posts ORDER BY id DESC LIMIT 10")
history = cursor.fetchall()

for item in history:
    st.write(f"🛠 {item[0]} — {item[1]}")
