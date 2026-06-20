import streamlit as st
import sqlite3
import pandas as pd

# --- ARQUITETURA DE BANCO DE DADOS (SCHEMA) ---
def init_db():
    conn = sqlite3.connect("sgf_fleet_elite.db")
    cursor = conn.cursor()
    
    # 1. Usuários e Permissões
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (login TEXT PRIMARY KEY, senha TEXT, modulos TEXT)")
    
    # 2. Veículos e Documentação
    cursor.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, modelo TEXT, km_atual INTEGER, crlv TEXT)")
    
    # 3. Manutenção (OS)
    cursor.execute("CREATE TABLE IF NOT EXISTS manutencao (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, servico TEXT, custo REAL, aprovado INTEGER DEFAULT 0)")
    
    # 4. Multas (CTB)
    cursor.execute("CREATE TABLE IF NOT EXISTS multas (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, codigo_infracao TEXT, valor REAL, motorista_id INTEGER)")
    
    # 5. Motoristas
    cursor.execute("CREATE TABLE IF NOT EXISTS motoristas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cnh TEXT)")
    
    # 6. Auditoria
    cursor.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, acao TEXT, tabela TEXT, data_hora TIMESTAMP)")
    
    conn.commit()
    conn.close()

# --- CAMADA DE NEGÓCIO ---
# Aqui implementaremos a lógica: "Se o veículo tem OS pendente, não pode sair".
# Aqui implementaremos a lógica: "Se o código da multa for inserido, o valor puxa do dicionário CTB".
