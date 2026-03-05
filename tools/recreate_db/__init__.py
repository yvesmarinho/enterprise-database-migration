"""
Database Recreator Module

Módulo para recriar bancos de dados MySQL e PostgreSQL de forma segura,
coletando metadados antes da exclusão e recriando com os mesmos parâmetros.

Uso básico:
    from recreate_db import DatabaseRecreator

    recreator = DatabaseRecreator('config.json', 'database_name')
    result = recreator.execute_full_recreation()
"""

from .recreate_database import DatabaseRecreator

__version__ = '1.0.0'
__author__ = 'Vya Digital - Database Migration Team'
__all__ = ['DatabaseRecreator']
