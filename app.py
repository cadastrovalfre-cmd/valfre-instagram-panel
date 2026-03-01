from openai import OpenAI
import streamlit as st
import requests
from bs4 import BeautifulSoup
import random

st.set_page_config(page_title="Valfre Instagram Auto", layout="wide")

st.title("🤖 Gerador Automático Instagram - Valfre")

api_key = st.text_input("API Key OpenAI", type="password")

if api_key:
    client = OpenAI(api_key=api_key)

    if st.button("🔄 Buscar Produto Aleatório do Site"):

        url = "https://www.ferramentasvalfre.com.br"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        produtos = soup.find_all("h2")

        if produtos:
            produto = random.choice(produtos).text

            st.success(f"Produto escolhido: {produto}")

            prompt = f"""
            Crie um post profissional para Instagram vendendo:
            {produto}

            Use tom comercial forte.
            Inclua chamada para ação.
            Inclua hashtags.
            """

            resposta = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            post = resposta.choices[0].message.content

            st.markdown("### 📌 Post Gerado:")
            st.write(post)

        else:
            st.error("Não foi possível encontrar produtos no site.")
