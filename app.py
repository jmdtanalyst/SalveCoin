from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from supabase import create_client, Client
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Supabase configuration
supabase_url = "https://jhhkysptvpxbtqqdzmkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpoaGt5c3B0dnB4YnRxcWR6bWt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMDY4NDEsImV4cCI6MjA2MzU4Mjg0MX0.A8mTOt8aGkwTVL9yEM10nIwbbG8e-kkd1W4d_1ALK7w"
supabase: Client = create_client(supabase_url, supabase_key)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id, cpf, nome):
        self.id = id
        self.cpf = cpf
        self.nome = nome

@login_manager.user_loader
def load_user(user_id):
    user_data = supabase.table('usuarios').select('*').eq('id', user_id).single()
    if user_data:
        return User(user_id, user_data['cpf'], user_data['nome'])
    return None

@app.route('/')
@login_required
def dashboard():
    # Get all transactions
    transactions = supabase.table('transacoes').select('*').eq('usuario_id', current_user.id).execute()
    
    # Calculate totals
    receitas = sum(t['valor'] for t in transactions.data if t['tipo'] == 'receita')
    despesas = sum(t['valor'] for t in transactions.data if t['tipo'] == 'despesa')
    despesas_pendentes = sum(t['valor'] for t in transactions.data if t['tipo'] == 'despesa' and not t['pago'])
    
    return render_template('dashboard.html', 
                         receitas=receitas,
                         despesas=despesas,
                         despesas_pendentes=despesas_pendentes,
                         transactions=transactions.data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form.get('cpf')
        senha = request.form.get('senha')
        
        user = supabase.table('usuarios').select('*').eq('cpf', cpf).single()
        if user and user['senha'] == senha:  # In production, use proper password hashing
            user_obj = User(user['id'], user['cpf'], user['nome'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        flash('CPF ou senha inválidos')
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        cpf = request.form.get('cpf')
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        
        # Check if user already exists
        existing_user = supabase.table('usuarios').select('*').eq('cpf', cpf).execute()
        if existing_user.data:
            flash('CPF já cadastrado')
            return redirect(url_for('cadastro'))
            
        # Create new user
        supabase.table('usuarios').insert({
            'cpf': cpf,
            'nome': nome,
            'senha': senha  # In production, hash this password
        }).execute()
        
        flash('Cadastro realizado com sucesso! Faça login para continuar.')
        return redirect(url_for('login'))
    return render_template('cadastro.html')

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
        
        supabase.table('transacoes').insert({
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
