import streamlit as st

st.set_page_config(page_title="Valfre Instagram Panel", layout="wide")

st.title("🚀 Painel Instagram - Ferramentas Valfre")

menu = st.sidebar.selectbox(
    "Menu",
    ["Criar Post Produto", "Criar Post Engajamento", "Histórico"]
)

if menu == "Criar Post Produto":
    st.header("Criar Post de Produto")
    
    produto = st.text_input("Nome do Produto")
    descricao = st.text_area("Descrição do Post")
    
    if st.button("Gerar Post"):
        st.success("Post gerado com sucesso!")
        st.markdown("### 📌 Preview")
        st.markdown(f"**{produto}**")
        st.write(descricao)
        st.markdown("#FerramentasValfre #Bestfer #Ferramentas")

elif menu == "Criar Post Engajamento":
    st.header("Criar Post de Engajamento")
    
    mensagem = st.text_area("Mensagem")
    
    if st.button("Gerar"):
        st.success("Post criado!")
        st.markdown("### 📌 Preview")
        st.write(mensagem)

elif menu == "Histórico":
    st.header("Histórico de Posts")
    st.info("Em breve conectaremos ao banco de dados.")
