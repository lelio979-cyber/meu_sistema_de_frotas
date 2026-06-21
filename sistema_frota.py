
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import date, datetime, timedelta

# =========================
# CONFIGURAÇÕES
# =========================
DATABASE_URL = "sqlite:///frota.db"
SECRET_KEY = "troque_esta_chave_por_uma_segura"
ALGORITHM = "HS256"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# =========================
# MODELOS
# =========================
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))
    email = Column(String(100), unique=True)
    senha_hash = Column(String(255))
    perfil = Column(String(30))

class Veiculo(Base):
    __tablename__ = "veiculos"
    id = Column(Integer, primary_key=True)
    placa = Column(String(20), unique=True)
    marca = Column(String(50))
    modelo = Column(String(50))
    ano = Column(Integer)
    km_atual = Column(Float, default=0)
    status = Column(String(30), default="DISPONIVEL")

class Motorista(Base):
    __tablename__ = "motoristas"
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))
    cpf = Column(String(20))
    cnh = Column(String(30))

class Abastecimento(Base):
    __tablename__ = "abastecimentos"
    id = Column(Integer, primary_key=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"))
    litros = Column(Float)
    valor = Column(Float)
    km = Column(Float)

class Manutencao(Base):
    __tablename__ = "manutencoes"
    id = Column(Integer, primary_key=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"))
    descricao = Column(String(300))
    custo = Column(Float)
    status = Column(String(30), default="ABERTA")

Base.metadata.create_all(bind=engine)

# =========================
# SCHEMAS
# =========================
class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    perfil: str = "ADMIN"

class LoginSchema(BaseModel):
    email: str
    senha: str

class VeiculoCreate(BaseModel):
    placa: str
    marca: str
    modelo: str
    ano: int

class MotoristaCreate(BaseModel):
    nome: str
    cpf: str
    cnh: str

class AbastecimentoCreate(BaseModel):
    veiculo_id: int
    litros: float
    valor: float
    km: float

class ManutencaoCreate(BaseModel):
    veiculo_id: int
    descricao: str
    custo: float

# =========================
# FUNÇÕES
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_senha(senha):
    return pwd_context.hash(senha)

def verificar_senha(senha, senha_hash):
    return pwd_context.verify(senha, senha_hash)

def criar_token(email, perfil):
    return jwt.encode(
        {"sub": email, "perfil": perfil, "exp": datetime.utcnow() + timedelta(hours=8)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def usuario_logado(
    credenciais: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        return jwt.decode(
            credenciais.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# =========================
# API
# =========================
app = FastAPI(title="Sistema de Gestão de Frotas")

@app.get("/")
def home():
    return {"sistema": "Gestao de Frotas", "status": "Online"}

@app.post("/usuarios")
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    novo = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hash_senha(usuario.senha),
        perfil=usuario.perfil
    )
    db.add(novo)
    db.commit()
    return {"mensagem": "Usuário criado"}

@app.post("/login")
def login(dados: LoginSchema, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = criar_token(usuario.email, usuario.perfil)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/veiculos")
def criar_veiculo(
    veiculo: VeiculoCreate,
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado)
):
    novo = Veiculo(**veiculo.dict())
    db.add(novo)
    db.commit()
    return {"mensagem": "Veículo cadastrado"}

@app.get("/veiculos")
def listar_veiculos(
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado)
):
    return db.query(Veiculo).all()

@app.post("/motoristas")
def criar_motorista(
    motorista: MotoristaCreate,
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado)
):
    novo = Motorista(**motorista.dict())
    db.add(novo)
    db.commit()
    return {"mensagem": "Motorista cadastrado"}

@app.get("/motoristas")
def listar_motoristas(
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado)
):
    return db.query(Motorista).all()

@app.post("/abastecimentos")
def criar_abastecimento(
    item: AbastecimentoCreate,
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado)
):
    db.add(Abastecimento(**item.dict()))
    db.commit()
    return {"mensagem": "Abastecimento registrado"}

@app.post("/manutencoes")
def criar_manutencao(
    item: ManutencaoCreate,
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado)
):
    manut = Manutencao(**item.dict())
    db.add(manut)

    veiculo = db.query(Veiculo).filter(Veiculo.id == item.veiculo_id).first()
    if veiculo:
        veiculo.status = "EM MANUTENCAO"

    db.commit()
    return {"mensagem": "Manutenção registrada"}

@app.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado)
):
    total_veiculos = db.query(Veiculo).count()
    manutencao = db.query(Veiculo).filter(
        Veiculo.status == "EM MANUTENCAO"
    ).count()

    abastecimentos = db.query(Abastecimento).all()
    custo_combustivel = sum(x.valor for x in abastecimentos)

    manutencoes = db.query(Manutencao).all()
    custo_manutencao = sum(x.custo for x in manutencoes)

    return {
        "total_veiculos": total_veiculos,
        "veiculos_em_manutencao": manutencao,
        "custo_combustivel": custo_combustivel,
        "custo_manutencao": custo_manutencao
    }

# Executar:
# pip install fastapi uvicorn sqlalchemy python-jose passlib bcrypt
# uvicorn sistema_frota:app --reload
# Docs: http://127.0.0.1:8000/docs
