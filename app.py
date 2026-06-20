import sqlite3

def get_connection():
    conn = sqlite3.connect('frotas_elite.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            placa TEXT PRIMARY KEY, 
            modelo TEXT,
            foto TEXT,
            doc TEXT
        )
    """)
    conn.commit()
    conn.close()
