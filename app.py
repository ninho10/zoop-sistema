from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from db import get_db_connection, add_column, delete_column
import sys
import os
from werkzeug.utils import secure_filename

# --- CONFIGURAÇÃO INICIAL E DEPURAÇÃO ---
print("--- INICIANDO APP.PY (VERSÃO: APROVADO) ---")
print(f"Usando mysql.connector: {mysql.connector.__version__}")


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')  # Chave secreta para sessões

# --- CONFIGURAÇÃO DE UPLOAD DE ARQUIVOS ---
UPLOAD_FOLDER = 'static/uploads'  # Pasta onde os arquivos serão salvos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}  # Extensões permitidas
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Garantir que o diretório de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """
    Verifica se o arquivo tem uma extensão permitida.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- FUNÇÕES AUXILIARES ---

def get_product_columns():
    """
    Recupera os nomes de todas as colunas da tabela 'products' de forma dinâmica.
    Isso é usado para manipular campos personalizados criados pelo usuário.
    """
    conn = get_db_connection()
    columns = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM products")
        for col in cursor.fetchall():
            columns.append(col[0])  # Adiciona o nome da coluna à lista
        cursor.close()
        conn.close()
    return columns

# --- ROTAS PRINCIPAIS ---

@app.route('/')
def index():
    """
    Rota raiz. Redireciona para a lista de produtos se logado,
    ou para o login se não estiver autenticado.
    """
    if 'user_id' in session:
        return redirect(url_for('list_products'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Gerencia o login do usuário.
    """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        print(f"Tentativa de login para: {email}") # DEPURAÇÃO: Log de quem está tentando logar
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Consulta para buscar o usuário pelo email e senha
        sql = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(sql, (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            print(f"Usuário encontrado: {user}") # DEPURAÇÃO
            
            # Verifica se o usuário foi aprovado pelo administrador
            if 'is_approved' in user:
                if user['is_approved']:
                    # Define a sessão do usuário
                    session['user_id'] = user['id']
                    session['is_admin'] = user['is_admin']
                    session['user_email'] = user['email']
                    return redirect(url_for('add_product'))
                else:
                    flash('Seu cadastro ainda não foi aprovado.', 'warning')
            else:
                # Fallback caso a coluna não exista (erro de banco de dados)
                print("ERRO: coluna 'is_approved' faltando no dicionário do usuário!")
                if 'approved' in user and user['approved']:
                     session['user_id'] = user['id']
                     session['is_admin'] = user['is_admin']
                     session['user_email'] = user['email']
                     return redirect(url_for('add_product'))
                
        else:
            print("Usuário não encontrado ou senha errada") # DEPURAÇÃO
            flash('Email ou senha incorretos.', 'danger')
            
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    """
    Processa o cadastro de novos usuários.
    """
    name = request.form['name']
    company = request.form['company']
    ramal = request.form['ramal']
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Insere o novo usuário no banco de dados
            cursor.execute("INSERT INTO users (name, company, ramal, email, password) VALUES (%s, %s, %s, %s, %s)", 
                           (name, company, ramal, email, password))
            conn.commit()
            flash('Cadastro realizado! Aguarde aprovação.', 'success')
        except mysql.connector.Error as err:
            flash(f'Erro ao cadastrar: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    return redirect(url_for('login'))

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    """
    Rota para adicionar novos produtos.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        form_data = request.form.to_dict()
        columns = get_product_columns()
        
        data_to_insert = {}
        # Prepara os dados para inserção, ignorando o ID (auto-incremento)
        for col in columns:
            if col != 'id' and col in form_data:
                value = form_data[col]
                # Converte strings vazias ou apenas espaços para None (NULL no banco)
                if isinstance(value, str):
                     value = value.strip()
                
                if value == '':
                    data_to_insert[col] = None
                else:
                    data_to_insert[col] = value
        
        # Backend validation: Name is mandatory
        if not data_to_insert.get('name'):
            flash('O nome do produto é obrigatório.', 'warning')
            
            # Reconstruct logic to render template with error and preserve user input if possible (basic version here just re-renders)
            all_columns = get_product_columns()
            standard_columns = ['id', 'photo', 'photo2', 'photo3', 'name', 'description', 'manufacturer', 'region', 'min_quantity', 'price', 'currency']
            extra_columns = [col for col in all_columns if col not in standard_columns]
            return render_template('add_product.html', extra_columns=extra_columns)
        
        # Gerenciamento de Upload de Imagem
        print(f"DEPURAÇÃO: Verificando foto na requisição: {'photo' in request.files}")
        if 'photo' in request.files:
            file = request.files['photo']
            print(f"DEPURAÇÃO: Objeto arquivo: {file}")
            print(f"DEPURAÇÃO: Nome do arquivo: {file.filename}")
            
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    print(f"DEPURAÇÃO: Salvando arquivo em: {save_path}")
                    try:
                        file.save(save_path)
                        data_to_insert['photo'] = filename # Salva APENAS o nome do arquivo no banco
                        print("DEPURAÇÃO: Arquivo salvo com sucesso")
                    except Exception as e:
                        print(f"DEPURAÇÃO: Erro ao salvar arquivo: {e}")
                        flash(f'Erro ao salvar arquivo imagem: {e}', 'warning')
                else:
                    print(f"DEPURAÇÃO: Arquivo não permitido. Extensões: {ALLOWED_EXTENSIONS}")
                    flash(f'Imagem não salva. Tipo de arquivo não permitido: {file.filename}', 'warning')
        
        print(f"DEPURAÇÃO: chaves para inserir: {data_to_insert.keys()}")
        
        if data_to_insert:
             # Constrói a query SQL dinamicamente baseada nas colunas presentes
             cols = ', '.join(data_to_insert.keys())
             placeholders = ', '.join(['%s'] * len(data_to_insert))
             sql = f"INSERT INTO products ({cols}) VALUES ({placeholders})"
             val = list(data_to_insert.values())
             print(f"DEPURAÇÃO: SQL: {sql}")
             
             conn = get_db_connection()
             cursor = conn.cursor()
             try:
                 cursor.execute(sql, val)
                 conn.commit()
                 flash('Produto cadastrado com sucesso!', 'success')
             except mysql.connector.Error as err:
                 print(f"DEPURAÇÃO: Erro de banco: {err}")
                 flash(f'Erro ao cadastrar produto: {err}', 'danger')
             finally:
                 cursor.close()
                 conn.close()
        
        return redirect(url_for('list_products'))

    # Separa colunas padrão das colunas extras para exibição no formulário
    all_columns = get_product_columns()
    standard_columns = ['id', 'photo', 'photo2', 'photo3', 'name', 'description', 'manufacturer', 'region', 'min_quantity', 'price', 'currency']
    extra_columns = [col for col in all_columns if col not in standard_columns]
    
    return render_template('add_product.html', extra_columns=extra_columns)

@app.route('/products')
def list_products():
    """
    Lista todos os produtos e gerencia a busca.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search_query = request.args.get('q', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search_query:
        # Busca por nome, região ou descrição
        sql = "SELECT * FROM products WHERE name LIKE %s OR region LIKE %s OR description LIKE %s ORDER BY id DESC"
        val = (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
        cursor.execute(sql, val)
    else:
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    all_columns = get_product_columns()
    
    return render_template('list_products.html', products=products, columns=all_columns)

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    """
    Rota para editar um produto existente e criar novas colunas.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        # --- Lógica para criar nova coluna ---
        new_col_name = request.form.get('new_column_name')
        if new_col_name:
            # Sanitiza o nome da coluna (apenas letras, números e underline)
            new_col_name = "".join(x for x in new_col_name if x.isalnum() or x == '_')
            if new_col_name:
                add_column(new_col_name) # Chama função do db.py
                flash(f'Coluna "{new_col_name}" criada!', 'info')
                cursor.close()
                conn.close()
                return redirect(url_for('edit_product', id=id))

                return redirect(url_for('edit_product', id=id))

        # --- Lógica para excluir coluna ---
        delete_col_name = request.form.get('delete_column_name')
        if delete_col_name:
             # Verifica permissão do usuário
             if session.get('user_email') == 'desenvolvimentoti@semaxbrasil.com.br':
                 if delete_column(delete_col_name):
                     flash(f'Coluna "{delete_col_name}" excluída com sucesso!', 'success')
                 else:
                     flash(f'Erro ao excluir coluna "{delete_col_name}".', 'danger')
             else:
                 flash('Você não tem permissão para excluir colunas.', 'danger')
             
             cursor.close()
             conn.close()
             return redirect(url_for('edit_product', id=id))

        # --- Lógica de atualização do produto ---
        columns = get_product_columns()
        data_to_update = {}
        for col in columns:
            if col != 'id' and col in form_data:
                value = form_data[col]
                
                if isinstance(value, str):
                    value = value.strip()
                    
                if value == '':
                    data_to_update[col] = None
                else:
                    data_to_update[col] = value
        
        # Gerenciamento de Upload de Multiplas Imagens
        for photo_field in ['photo', 'photo2', 'photo3']:
            if photo_field in request.files:
                file = request.files[photo_field]
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        try:
                            file.save(save_path)
                            data_to_update[photo_field] = filename
                        except Exception as e:
                            flash(f'Erro ao salvar imagem {photo_field}: {e}', 'warning')
                    else:
                        flash(f'Tipo de arquivo não permitido: {file.filename}', 'warning')
        
        if data_to_update:
            # Constrói query UPDATE dinâmica
            set_clause = ', '.join([f"{col} = %s" for col in data_to_update.keys()])
            val = list(data_to_update.values())
            val.append(id)
            
            sql = f"UPDATE products SET {set_clause} WHERE id = %s"
            try:
                cursor.execute(sql, val)
                conn.commit()
                flash('Produto atualizado!', 'success')
            except mysql.connector.Error as err:
                flash(f'Erro ao atualizar: {err}', 'danger')
                
        cursor.close()
        conn.close()
        return redirect(url_for('list_products'))

    # Carrega dados do produto para exibição inicial
    cursor.execute("SELECT * FROM products WHERE id = %s", (id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()
    
    all_columns = get_product_columns()
    standard_columns = ['id', 'photo', 'photo2', 'photo3', 'name', 'description', 'manufacturer', 'region', 'min_quantity', 'price', 'currency']
    extra_columns = [col for col in all_columns if col not in standard_columns]
    
    return render_template('edit_product.html', product=product, extra_columns=extra_columns)

@app.route('/products/view/<int:id>')
def view_product(id):
    """
    Exibe os detalhes completos de um produto.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id = %s", (id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not product:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('list_products'))
    
    all_columns = get_product_columns()
    standard_columns = ['id', 'photo', 'photo2', 'photo3', 'name', 'description', 'manufacturer', 'region', 'min_quantity', 'price', 'currency']
    extra_columns = [col for col in all_columns if col not in standard_columns]
    
    return render_template('view_product.html', product=product, extra_columns=extra_columns)

@app.route('/products/delete/<int:id>')
def delete_product(id):
    """
    Exclui um produto pelo ID.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Produto excluído.', 'info')
    return redirect(url_for('list_products'))

@app.route('/logout')
def logout():
    """
    Encerra a sessão do usuário.
    """
    session.clear()
    return redirect(url_for('login'))

# --- ROTAS ADMINISTRATIVAS ---

@app.route('/users')
def manage_users():
    """
    ADMIN: Lista todos os usuários cadastrados.
    """
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('list_products'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('manage_users.html', users=users)

@app.route('/users/approve/<int:id>')
def approve_user(id):
    """
    ADMIN: Aprova um usuário pendente.
    """
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_approved = TRUE WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Usuário aprovado!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/users/delete_user/<int:id>')
def delete_user(id):
    """
    ADMIN: Exclui um usuário.
    """
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    # Impede que o admin exclua a si mesmo acidentalmente
    if id == session['user_id']:
         flash('Você não pode excluir a si mesmo.', 'warning')
    else:
        cursor.execute("DELETE FROM users WHERE id = %s", (id,))
        conn.commit()
        flash('Usuário excluído.', 'info')
        
    cursor.close()
    conn.close()
    return redirect(url_for('manage_users'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')





