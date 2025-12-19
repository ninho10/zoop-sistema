from db import get_db_connection, add_column
import mysql.connector

def add_photo_columns():
    """
    Adiciona colunas photo2 e photo3 ao banco de dados se não existirem.
    """
    print("Iniciando migração de banco de dados...")
    
    # Tenta adicionar usando a função utilitária existente
    # Nota: add_column do db.py é genérica, vamos usá-la.
    if add_column('photo2'):
        print("Coluna 'photo2' criada.")
    else:
        print("Coluna 'photo2' provavelmente já existe ou erro.")

    if add_column('photo3'):
        print("Coluna 'photo3' criada.")
    else:
        print("Coluna 'photo3' provavelmente já existe ou erro.")

if __name__ == "__main__":
    add_photo_columns()
