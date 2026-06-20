import sqlite3

def get_connection():
    conn = sqlite3.connect('frotas_elite.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    # Tabela de Veículos
    conn.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT)")
    # Tabela de Usuários (Nova)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            login TEXT PRIMARY KEY, 
            senha TEXT, 
            perfil TEXT
        )
    """)
    # Usuário padrão para teste
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin', 'admin')")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('user', '123', 'operador')")
    conn.commit()
    conn.close()
