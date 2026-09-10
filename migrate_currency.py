from db import add_column

def add_currency_column():
    """
    Adiciona coluna currency ao banco de dados.
    """
    print("Iniciando migração de banco de dados (currency)...")
    
    # Adiciona coluna currency com valor padrão 'Real'
    if add_column('currency', 'VARCHAR(20) DEFAULT "Real"'):
        print("Coluna 'currency' criada.")
    else:
        print("Coluna 'currency' provavelmente já existe ou erro.")

if __name__ == "__main__":
    add_currency_column()
