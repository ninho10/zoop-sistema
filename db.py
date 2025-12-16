import mysql.connector
from mysql.connector import Error

# Configuração de Conexão com o Banco de Dados
DB_CONFIG = {
    'host': 'produtos_zoop.vpshost4282.mysql.dbaas.com.br',
    'database': 'produtos_zoop',
    'user': 'produtos_zoop',
    'password': 'Zoop#@!123'
}

def get_db_connection():
    """
    Estabelece uma conexão com o banco de dados MySQL usando as configurações do DB_CONFIG.
    Retorna o objeto de conexão se bem-sucedido, ou None se falhar.
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def init_db():
    """
    Inicializa o banco de dados criando as tabelas necessárias se elas não existirem.
    Também cria o usuário administrador padrão.
    """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Cria a tabela de Usuários (users)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            company VARCHAR(255),
            ramal VARCHAR(50),
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            is_approved BOOLEAN DEFAULT FALSE,
            is_admin BOOLEAN DEFAULT FALSE
        )
        """)
        
        # Cria a tabela de Produtos (products)
        # Nota: Colunas dinâmicas serão adicionadas via ALTER TABLE posteriormente.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            photo VARCHAR(255),
            name VARCHAR(255),
            description TEXT,
            manufacturer VARCHAR(255),
            region VARCHAR(255),
            min_quantity INT,
            price DECIMAL(10, 2)
        )
        """)

        # Verifica se o administrador padrão já existe
        cursor.execute("SELECT * FROM users WHERE email = 'desenvolvimentoti@semaxbrasil.com.br'")
        admin = cursor.fetchone()
        
        if not admin:
            # Insere o administrador padrão
            sql = """INSERT INTO users (name, company, ramal, email, password, is_approved, is_admin) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            val = ("Admin", "Semax", "0000", "desenvolvimentoti@semaxbrasil.com.br", "*Pa190548", True, True)
            cursor.execute(sql, val)
            print("Usuário administrador padrão criado.")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Banco de dados inicializado com sucesso.")
    else:
        print("Falha ao conectar ao banco de dados.")

def add_column(column_name, column_type="VARCHAR(255)"):
    """
    Adiciona uma nova coluna à tabela de produtos dinamicamente.
    Utilizado para campos personalizados definidos pelo usuário.
    """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"ALTER TABLE products ADD COLUMN {column_name} {column_type}")
            conn.commit()
            print(f"Coluna {column_name} adicionada com sucesso.")
            return True
        except Error as e:
            print(f"Erro ao adicionar coluna: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

if __name__ == "__main__":
    init_db()
