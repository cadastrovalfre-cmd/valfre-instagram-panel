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

# ================= SITEMAP READER =================

def read_sitemap(url):
    response = requests.get(url, timeout=20)
    root = ET.fromstring(response.content)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = []

    # sitemap index
    if "sitemapindex" in root.tag:
        for sitemap in root.findall('ns:sitemap', namespace):
            loc = sitemap.find('ns:loc', namespace)
            if loc is not None:
                urls += read_sitemap(loc.text)

    # normal sitemap
    elif "urlset" in root.tag:
        for url in root.findall('ns:url', namespace):
            loc = url.find('ns:loc', namespace)
            if loc is not None:
                urls.append(loc.text)

    return urls


# ================= PRODUCT VALIDATION =================

def is_real_product(url):
    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
            except:
                continue

            if isinstance(data, dict) and data.get("@type") == "Product":
                return True

        return False

    except:
        return False


def extract_product_data(url):
    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")

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
                    "link": url
                }

        return None

    except:
        return None


# ================= AI =================

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
- Hashtags nichadas

Tom comercial forte e profissional.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ================= UI =================

st.sidebar.header("⚙ Configurações")

if st.sidebar.button("🔄 Escanear Site Inteiro"):
    with st.spinner("Lendo sitemap completo..."):
        sitemap_url = SITE_URL + "/sitemap.xml"
        all_urls = read_sitemap(sitemap_url)

        product_urls = []

        for url in all_urls:
            if is_real_product(url):
                product_urls.append(url)

        st.session_state.products = product_urls
        st.success(f"{len(product_urls)} produtos reais encontrados!")

if "products" not in st.session_state:
    st.session_state.products = []

st.header("📦 Produtos Disponíveis")

if st.session_state.products:
    selected_url = random.choice(st.session_state.products)
    product = extract_product_data(selected_url)

    if product:
        st.success(product["title"])
        st.write(product["link"])
        st.write(f"Preço: {product['price']}")

        if st.button("🚀 Gerar Post"):
            with st.spinner("Gerando conteúdo..."):
                post = generate_post(product)

                cursor.execute(
                    "INSERT INTO posts (product, price, link, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        product["title"],
                        str(product["price"]),
                        product["link"],
                        post,
                        datetime.now().isoformat()
                    )
                )
                conn.commit()

                st.markdown("## 📌 Post Gerado")
                st.write(post)

else:
    st.warning("Clique em 'Escanear Site Inteiro'.")

# ================= HISTORY =================

st.header("📊 Histórico")

cursor.execute("SELECT product, created_at FROM posts ORDER BY id DESC LIMIT 10")
history = cursor.fetchall()

for item in history:
    st.write(f"🛠 {item[0]} — {item[1]}")
