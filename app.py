import streamlit as st
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
from openai import OpenAI
import random
import xml.etree.ElementTree as ET
import json

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
    price TEXT,
    link TEXT,
    content TEXT,
    created_at TEXT
)
""")
conn.commit()

# ================= SCRAPER =================

def get_all_sitemap_urls():
    sitemap_url = SITE_URL + "/sitemap.xml"
    response = requests.get(sitemap_url, timeout=15)
    root = ET.fromstring(response.content)

    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    urls = []

    # Caso seja sitemap index
    if "sitemapindex" in root.tag:
        for sitemap in root.findall('ns:sitemap', namespace):
            loc = sitemap.find('ns:loc', namespace)
            if loc is not None:
                sub_sitemap = requests.get(loc.text, timeout=15)
                sub_root = ET.fromstring(sub_sitemap.content)
                for url in sub_root.findall('ns:url', namespace):
                    loc2 = url.find('ns:loc', namespace)
                    if loc2 is not None:
                        urls.append(loc2.text)
    else:
        for url in root.findall('ns:url', namespace):
            loc = url.find('ns:loc', namespace)
            if loc is not None:
                urls.append(loc.text)

    return urls


def filter_product_urls(urls):
    return [u for u in urls if "/produto" in u.lower()]


def extract_product_data(product_url):
    try:
        response = requests.get(product_url, timeout=15)
        soup = BeautifulSoup(response.text, "lxml")

        # Busca JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
            except:
                continue

            if isinstance(data, dict) and data.get("@type") == "Product":
                title = data.get("name", "Produto")
                price = None

                offers = data.get("offers")
                if isinstance(offers, dict):
                    price = offers.get("price")

                return {
                    "title": title,
                    "price": price,
                    "link": product_url
                }

        # fallback simples
        title = soup.title.string if soup.title else "Produto"
        return {
            "title": title,
            "price": None,
            "link": product_url
        }

    except:
        return None


def generate_post(product):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    prompt = f"""
Crie um post altamente persuasivo para Instagram vendendo:

Produto: {product['title']}
Preço: {product['price']}
Link: {product['link']}
Loja: Ferramentas Valfre

Inclua:
- Benefícios claros
- Problema que resolve
- Prova social
- Chamada forte para ação
- Emojis estratégicos
- Hashtags nichadas para ferramentas

Tom comercial agressivo e profissional.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ================= UI =================

st.sidebar.header("⚙ Configurações")

if st.sidebar.button("🔄 Escanear Site Inteiro"):
    with st.spinner("Escaneando sitemap..."):
        all_urls = get_all_sitemap_urls()
        product_urls = filter_product_urls(all_urls)
        st.session_state.products = product_urls
        st.success(f"{len(product_urls)} produtos encontrados!")

if "products" not in st.session_state:
    st.session_state.products = []

st.header("📦 Produtos Disponíveis")

if st.session_state.products:
    selected_url = random.choice(st.session_state.products)
    product_data = extract_product_data(selected_url)

    if product_data:
        st.success(product_data["title"])
        st.write(product_data["link"])
        st.write(f"Preço: {product_data['price']}")

        if st.button("🚀 Gerar Post"):
            with st.spinner("Gerando conteúdo..."):
                post = generate_post(product_data)

                cursor.execute(
                    "INSERT INTO posts (product, price, link, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        product_data["title"],
                        str(product_data["price"]),
                        product_data["link"],
                        post,
                        datetime.now().isoformat()
                    )
                )
                conn.commit()

                st.markdown("## 📌 Post Gerado")
                st.write(post)
else:
    st.warning("Clique em 'Escanear Site Inteiro' para buscar produtos.")

# ================= HISTÓRICO =================

st.header("📊 Histórico")

cursor.execute("SELECT product, created_at FROM posts ORDER BY id DESC LIMIT 10")
history = cursor.fetchall()

for item in history:
    st.write(f"🛠 {item[0]} — {item[1]}")
