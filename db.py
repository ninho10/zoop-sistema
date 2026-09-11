import mysql.connector
from mysql.connector import Error, pooling
import os

# Configuração de Conexão com o Banco de Dados
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'produtos_zoop.vpshost4282.mysql.dbaas.com.br'),
    'database': os.getenv('DB_NAME', 'produtos_zoop'),
    'user': os.getenv('DB_USER', 'produtos_zoop'),
    'password': os.getenv('DB_PASSWORD', 'Zoop#@!123')
}

# Cria um pool de conexões para evitar lentidão
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="zoop_pool",
        pool_size=5,
        pool_reset_session=True,
        connect_timeout=10,
        **DB_CONFIG
    )
except Error as e:
    print(f"Erro ao inicializar o pool de conexões: {e}")
    connection_pool = None

def get_db_connection():
    """
    Estabelece uma conexão com o banco de dados MySQL usando o pool de conexões.
    """
    if not connection_pool:
        return None
        
    try:
        connection = connection_pool.get_connection()
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Erro ao pegar conexão do pool: {e}")
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
        
        # Cria usuário William solicitado
        cursor.execute("SELECT * FROM users WHERE email = 'e_william@cliostyle.com.br'")
        william = cursor.fetchone()
        if not william:
             sql_william = """INSERT INTO users (name, company, ramal, email, password, is_approved, is_admin) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s)"""
             val_william = ("William", "Clio", "0000", "e_william@cliostyle.com.br", "Clio#@!466", True, True)
             cursor.execute(sql_william, val_william)
             print("Usuário William criado.")
        
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

def delete_column(column_name):
    """
    Remove uma coluna da tabela de produtos.
    """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"ALTER TABLE products DROP COLUMN {column_name}")
            conn.commit()
            print(f"Coluna {column_name} removida com sucesso.")
            return True
        except Error as e:
            print(f"Erro ao remover coluna: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

if __name__ == "__main__":
    init_db()
