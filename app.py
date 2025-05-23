import logging
from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, SECRET_KEY

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Supabase configuration
# Create Supabase clients
logger.info(f"Initializing Supabase clients with URL: {SUPABASE_URL}")
logger.info(f"Using anon key: {SUPABASE_ANON_KEY[:10]}...{SUPABASE_ANON_KEY[-10:]}")  # Log only part of the key for security
logger.info(f"Using service key: {SUPABASE_SERVICE_KEY[:10]}...{SUPABASE_SERVICE_KEY[-10:]}")

supabase_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_service = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/debug-config')
def debug_config():
# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Transaction model
class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'receita' or 'despesa'
    vencimento = db.Column(db.Date, nullable=False)
    pago = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('User', backref=db.backref('transacoes', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form.get('cpf')
        senha = request.form.get('senha')
        
        try:
            user = User.query.filter_by(cpf=cpf).first()
            if user and user.senha == senha:
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('CPF ou senha inválidos')
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            flash('Erro ao fazer login. Por favor, tente novamente.')
    
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        cpf = request.form.get('cpf')
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        
        # Clean CPF
        cpf = ''.join(filter(str.isdigit, cpf))
        
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(cpf=cpf).first()
            if existing_user:
                flash('CPF já cadastrado')
                return redirect(url_for('cadastro'))
                
            # Create new user
            new_user = User(
                cpf=cpf,
                nome=nome,
                senha=senha  # In production, hash this password
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Cadastro realizado com sucesso! Faça login para continuar.')
            return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            flash('Erro ao criar usuário. Por favor, tente novamente.')
            return redirect(url_for('cadastro'))
    
    return render_template('cadastro.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get all transactions
    transactions = Transacao.query.filter_by(usuario_id=current_user.id).all()
    
    # Calculate totals
    receitas = sum(t.valor for t in transactions if t.tipo == 'receita')
    despesas = sum(t.valor for t in transactions if t.tipo == 'despesa')
    despesas_pendentes = sum(t.valor for t in transactions if t.tipo == 'despesa' and not t.pago)
    
    return render_template('dashboard.html', 
                         receitas=receitas,
                         despesas=despesas,
                         despesas_pendentes=despesas_pendentes,
                         transactions=transactions,
                         nome=current_user.nome)

@app.route('/transacoes', methods=['GET', 'POST'])
@login_required
def transacoes():
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        categoria = request.form.get('categoria')
        valor = float(request.form.get('valor'))
        tipo = request.form.get('tipo')
        vencimento = request.form.get('vencimento')
        pago = request.form.get('pago') == 'on'
        
        new_transacao = Transacao(
            usuario_id=current_user.id,
            descricao=descricao,
            categoria=categoria,
            valor=valor,
            tipo=tipo,
            vencimento=vencimento,
            pago=pago
        )
        db.session.add(new_transacao)
        db.session.commit()
        supabase_anon.table('transacoes').insert({
            'usuario_id': current_user.id,
            'descricao': descricao,
            'categoria': categoria,
            'valor': valor,
            'tipo': tipo,
            'vencimento': vencimento,
            'pago': pago
        }).execute()
        
        return redirect(url_for('dashboard'))
    
    return render_template('transacoes.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
