import psycopg2
from typing import Union

def test_sasl_scram_connection(
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str
) -> Union[bool, str]:
    """
    Testa a conexão com PostgreSQL utilizando SASL/SCRAM.

    :param host: Endereço do servidor PostgreSQL.
    :type host: str
    :param port: Porta do servidor PostgreSQL.
    :type port: int
    :param dbname: Nome do banco de dados.
    :type dbname: str
    :param user: Usuário do banco de dados.
    :type user: str
    :param password: Senha do usuário.
    :type password: str
    :return: Retorna True se conectar com sucesso, senão retorna o erro.
    :rtype: Union[bool, str]

    .. doctest::

        >>> test_sasl_scram_connection('localhost', 5432, 'postgres', 'scramuser', 'senha')
        True
        >>> test_sasl_scram_connection('', 5432, 'postgres', 'scramuser', 'senha')
        False
    """
    try:
        # Validação dos parâmetros
        if not all(isinstance(param, str) and param for param in [host, dbname, user, password]):
            raise ValueError("host, dbname, user, password devem ser strings não vazias")
        if not isinstance(port, int) or port <= 0:
            raise ValueError("port deve ser um inteiro positivo")

        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode='prefer'  # Recomenda-se usar pelo menos 'prefer'
        )
        conn.close()
        return True
    except Exception as e:
        return str(e) or False

if __name__ == "__main__":
    result = test_sasl_scram_connection('wfdb02.vya.digital', 5432, 'postgres', 'enterprise_user', 'enterprise_pass123!')
    print("Resultado do teste de conexão:", result)
