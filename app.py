import streamlit as st
import banco  # Importa o arquivo banco.py que criamos antes

# Configuração da página
st.set_page_config(page_title="SGF-Pro Login", layout="centered")

def tela_login():
    st.title("🔐 Acesso ao Sistema")
    st.write("Por favor, entre com suas credenciais.")
    
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        # Aqui você pode colocar uma lógica mais segura futuramente
        if usuario == "admin" and senha == "admin":
            st.session_state['logado'] = True
            st.rerun() # Recarrega a página para liberar o sistema
        else:
            st.error("Usuário ou senha inválidos!")

def main():
    # Inicializa o estado de login
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False

    # Se não estiver logado, mostra o login
    if not st.session_state['logado']:
        tela_login()
    else:
        # SE ESTIVER LOGADO:
        st.sidebar.title("Navegação SGF-Pro")
        if st.sidebar.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()
            
        st.title("Bem-vindo ao SGF-Pro")
        st.write("Sistema desbloqueado com sucesso.")

if __name__ == "__main__":
    banco.init_db() # Garante que o banco esteja pronto
    main()
