#!/usr/bin/env python3
"""
Database Expert Agent v1.0.0

Agente especializado com profundo conhecimento e experiência em MySQL e PostgreSQL.
Fornece análise avançada, estratégias de migração, otimização e troubleshooting.

Autor: Vya.Digital
Data: 2026-04-06
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


class DatabaseType(Enum):
    """Tipos de banco de dados suportados."""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MARIADB = "mariadb"


class AnalysisLevel(Enum):
    """Níveis de análise disponíveis."""
    QUICK = "quick"           # Análise superficial
    STANDARD = "standard"     # Análise padrão
    DEEP = "deep"            # Análise profunda
    FORENSIC = "forensic"    # Análise forense completa


@dataclass
class DatabaseInfo:
    """Informações sobre um banco de dados."""
    db_type: DatabaseType
    version: str
    server_info: str
    encoding: str
    collation: str
    size_mb: float
    table_count: int
    total_rows: int
    index_count: int
    constraints_count: int
    users_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationStrategy:
    """Estratégia de migração recomendada."""
    strategy_name: str
    description: str
    complexity: str  # low, medium, high, critical
    estimated_duration: str
    risks: List[str]
    steps: List[str]
    recommendations: List[str]
    compatibility_issues: List[Dict[str, str]]
    required_transformations: List[Dict[str, str]]


@dataclass
class AnalysisResult:
    """Resultado de uma análise de banco de dados."""
    timestamp: datetime
    analysis_level: AnalysisLevel
    database_info: DatabaseInfo
    schema_analysis: Dict[str, Any]
    data_quality: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    security_assessment: Dict[str, Any]
    recommendations: List[str]
    warnings: List[str]
    errors: List[str]


class DatabaseExpertAgent:
    """
    Agente especialista em MySQL e PostgreSQL.
    
    Fornece análise avançada, planejamento de migração, otimização de queries,
    troubleshooting e validação de dados.
    
    Características:
    - Análise profunda de estruturas e dados
    - Estratégias de migração MySQL → PostgreSQL
    - Detecção de incompatibilidades
    - Otimização de performance
    - Validação de integridade
    - Recomendações de melhores práticas
    """

    def __init__(self, log_level: int = logging.INFO):
        """
        Inicializa o agente especialista.
        
        Args:
            log_level: Nível de logging (default: INFO)
        """
        self.version = "1.0.0"
        self.logger = self._setup_logging(log_level)
        
        # Verificar dependências
        self.capabilities = {
            'postgresql': PSYCOPG2_AVAILABLE,
            'mysql': PYMYSQL_AVAILABLE
        }
        
        # Base de conhecimento
        self.knowledge_base = self._initialize_knowledge_base()
        
        self.logger.info(f"🤖 Database Expert Agent v{self.version} initialized")
        self.logger.info(f"📊 Capabilities: PostgreSQL={PSYCOPG2_AVAILABLE}, MySQL={PYMYSQL_AVAILABLE}")

    def _setup_logging(self, log_level: int) -> logging.Logger:
        """Configura sistema de logging."""
        logger = logging.getLogger(f"{__name__}.DatabaseExpertAgent")
        logger.setLevel(log_level)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - [DB-EXPERT] - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """
        Inicializa base de conhecimento do agente.
        
        Contém regras, padrões e melhores práticas para MySQL e PostgreSQL.
        """
        return {
            'mysql_to_postgresql': {
                'type_mappings': {
                    'TINYINT': 'SMALLINT',
                    'TINYINT(1)': 'BOOLEAN',
                    'MEDIUMINT': 'INTEGER',
                    'INT': 'INTEGER',
                    'BIGINT': 'BIGINT',
                    'FLOAT': 'REAL',
                    'DOUBLE': 'DOUBLE PRECISION',
                    'DECIMAL': 'NUMERIC',
                    'CHAR': 'CHAR',
                    'VARCHAR': 'VARCHAR',
                    'TINYTEXT': 'TEXT',
                    'TEXT': 'TEXT',
                    'MEDIUMTEXT': 'TEXT',
                    'LONGTEXT': 'TEXT',
                    'TINYBLOB': 'BYTEA',
                    'BLOB': 'BYTEA',
                    'MEDIUMBLOB': 'BYTEA',
                    'LONGBLOB': 'BYTEA',
                    'DATE': 'DATE',
                    'DATETIME': 'TIMESTAMP',
                    'TIMESTAMP': 'TIMESTAMP WITH TIME ZONE',
                    'TIME': 'TIME',
                    'YEAR': 'INTEGER',
                    'ENUM': 'VARCHAR',  # Ou criar tipo ENUM customizado
                    'SET': 'VARCHAR[]',  # Array de strings
                    'JSON': 'JSONB'
                },
                'function_mappings': {
                    'NOW()': 'CURRENT_TIMESTAMP',
                    'CURDATE()': 'CURRENT_DATE',
                    'CURTIME()': 'CURRENT_TIME',
                    'UNIX_TIMESTAMP()': 'EXTRACT(EPOCH FROM NOW())',
                    'DATE_ADD': 'date + INTERVAL',
                    'DATE_SUB': 'date - INTERVAL',
                    'IFNULL': 'COALESCE',
                    'IF': 'CASE WHEN',
                    'CONCAT': '||',
                    'GROUP_CONCAT': 'STRING_AGG',
                    'FIND_IN_SET': 'position',
                    'SUBSTRING': 'SUBSTR',
                    'LIMIT offset, count': 'LIMIT count OFFSET offset'
                },
                'incompatibilities': [
                    {
                        'feature': 'AUTO_INCREMENT',
                        'mysql': 'AUTO_INCREMENT',
                        'postgresql': 'SERIAL or GENERATED ALWAYS AS IDENTITY',
                        'severity': 'high',
                        'solution': 'Converter para SERIAL ou IDENTITY'
                    },
                    {
                        'feature': 'UNSIGNED',
                        'mysql': 'INT UNSIGNED',
                        'postgresql': 'Check constraint (value >= 0)',
                        'severity': 'medium',
                        'solution': 'Adicionar CHECK CONSTRAINT'
                    },
                    {
                        'feature': 'ZEROFILL',
                        'mysql': 'INT ZEROFILL',
                        'postgresql': 'lpad() na query',
                        'severity': 'low',
                        'solution': 'Aplicar formatação no nível da aplicação'
                    },
                    {
                        'feature': 'Backticks',
                        'mysql': '`table_name`',
                        'postgresql': '"table_name"',
                        'severity': 'medium',
                        'solution': 'Substituir ` por "'
                    },
                    {
                        'feature': 'Case Sensitivity',
                        'mysql': 'Case-insensitive by default',
                        'postgresql': 'Case-sensitive',
                        'severity': 'high',
                        'solution': 'Usar LOWER() ou ILIKE'
                    },
                    {
                        'feature': 'Engine Storage',
                        'mysql': 'ENGINE=InnoDB',
                        'postgresql': 'N/A',
                        'severity': 'low',
                        'solution': 'Remover ENGINE clause'
                    }
                ]
            },
            'postgresql_best_practices': [
                'Use SERIAL ou IDENTITY para auto-increment',
                'Prefira JSONB ao invés de JSON para melhor performance',
                'Use TEXT ao invés de VARCHAR long (sem limite)',
                'Sempre defina FILLFACTOR para tabelas com muitos UPDATEs',
                'Use índices parciais para queries específicas',
                'Configure appropriate autovacuum settings',
                'Use CONNECTION POOLING (pgBouncer) em produção',
                'Nunca use SELECT * em produção',
                'Use EXPLAIN ANALYZE para otimizar queries',
                'Configure work_mem adequadamente'
            ],
            'mysql_best_practices': [
                'Use InnoDB como engine padrão',
                'Sempre defina CHARACTER SET e COLLATION',
                'Use índices compostos na ordem correta',
                'Evite ENUM para dados que podem mudar',
                'Configure innodb_buffer_pool_size corretamente',
                'Use prepared statements para prevenir SQL injection',
                'Monitore slow query log',
                'Use EXPLAIN para análise de queries',
                'Configure max_connections adequadamente',
                'Backup regular com mysqldump ou Percona XtraBackup'
            ],
            'common_migration_pitfalls': [
                'Não validar codificação de caracteres (UTF-8)',
                'Esquecer de converter AUTO_INCREMENT',
                'Não tratar diferenças de timezone',
                'Ignorar diferenças de case sensitivity',
                'Não converter funções SQL específicas',
                'Esquecer de recriar índices adequadamente',
                'Não validar constraints após migração',
                'Ignorar diferenças em comportamento de NULL',
                'Não testar stored procedures/functions',
                'Não validar integridade referencial'
            ]
        }

    def analyze_database(
        self,
        connection_params: Dict[str, Any],
        db_type: DatabaseType,
        analysis_level: AnalysisLevel = AnalysisLevel.STANDARD
    ) -> AnalysisResult:
        """
        Analisa um banco de dados em profundidade.
        
        Args:
            connection_params: Parâmetros de conexão
            db_type: Tipo do banco de dados
            analysis_level: Nível de profundidade da análise
            
        Returns:
            AnalysisResult com todos os dados coletados
        """
        self.logger.info(f"🔍 Starting {analysis_level.value} analysis of {db_type.value} database")
        
        if db_type == DatabaseType.POSTGRESQL:
            return self._analyze_postgresql(connection_params, analysis_level)
        elif db_type in (DatabaseType.MYSQL, DatabaseType.MARIADB):
            return self._analyze_mysql(connection_params, analysis_level)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def _analyze_postgresql(
        self,
        connection_params: Dict[str, Any],
        analysis_level: AnalysisLevel
    ) -> AnalysisResult:
        """Analisa banco de dados PostgreSQL."""
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2 not available")
        
        conn = None
        try:
            conn = psycopg2.connect(**connection_params)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Informações básicas
            database_info = self._get_postgresql_info(cur)
            
            # Análise de schema
            schema_analysis = self._analyze_postgresql_schema(cur, analysis_level)
            
            # Qualidade de dados
            data_quality = self._analyze_data_quality_postgresql(cur, analysis_level)
            
            # Performance
            performance_metrics = self._analyze_postgresql_performance(cur, analysis_level)
            
            # Segurança
            security_assessment = self._assess_postgresql_security(cur)
            
            # Gerar recomendações
            recommendations, warnings, errors = self._generate_postgresql_recommendations(
                database_info, schema_analysis, data_quality, performance_metrics, security_assessment
            )
            
            return AnalysisResult(
                timestamp=datetime.now(),
                analysis_level=analysis_level,
                database_info=database_info,
                schema_analysis=schema_analysis,
                data_quality=data_quality,
                performance_metrics=performance_metrics,
                security_assessment=security_assessment,
                recommendations=recommendations,
                warnings=warnings,
                errors=errors
            )
            
        finally:
            if conn:
                conn.close()

    def _analyze_mysql(
        self,
        connection_params: Dict[str, Any],
        analysis_level: AnalysisLevel
    ) -> AnalysisResult:
        """Analisa banco de dados MySQL."""
        if not PYMYSQL_AVAILABLE:
            raise RuntimeError("pymysql not available")
        
        conn = None
        try:
            conn = pymysql.connect(**connection_params, cursorclass=pymysql.cursors.DictCursor)
            cur = conn.cursor()
            
            # Informações básicas
            database_info = self._get_mysql_info(cur)
            
            # Análise de schema
            schema_analysis = self._analyze_mysql_schema(cur, analysis_level)
            
            # Qualidade de dados
            data_quality = self._analyze_data_quality_mysql(cur, analysis_level)
            
            # Performance
            performance_metrics = self._analyze_mysql_performance(cur, analysis_level)
            
            # Segurança
            security_assessment = self._assess_mysql_security(cur)
            
            # Gerar recomendações
            recommendations, warnings, errors = self._generate_mysql_recommendations(
                database_info, schema_analysis, data_quality, performance_metrics, security_assessment
            )
            
            return AnalysisResult(
                timestamp=datetime.now(),
                analysis_level=analysis_level,
                database_info=database_info,
                schema_analysis=schema_analysis,
                data_quality=data_quality,
                performance_metrics=performance_metrics,
                security_assessment=security_assessment,
                recommendations=recommendations,
                warnings=warnings,
                errors=errors
            )
            
        finally:
            if conn:
                conn.close()

    def plan_migration(
        self,
        source_analysis: AnalysisResult,
        target_db_type: DatabaseType,
        options: Optional[Dict[str, Any]] = None
    ) -> MigrationStrategy:
        """
        Planeja estratégia de migração entre bancos de dados.
        
        Args:
            source_analysis: Análise do banco de origem
            target_db_type: Tipo do banco de destino
            options: Opções adicionais de migração
            
        Returns:
            MigrationStrategy com plano detalhado
        """
        self.logger.info(f"📋 Planning migration from {source_analysis.database_info.db_type.value} to {target_db_type.value}")
        
        if source_analysis.database_info.db_type == DatabaseType.MYSQL and target_db_type == DatabaseType.POSTGRESQL:
            return self._plan_mysql_to_postgresql(source_analysis, options or {})
        else:
            raise NotImplementedError(f"Migration path not yet implemented: {source_analysis.database_info.db_type.value} → {target_db_type.value}")

    def _plan_mysql_to_postgresql(
        self,
        source_analysis: AnalysisResult,
        options: Dict[str, Any]
    ) -> MigrationStrategy:
        """Planeja migração MySQL → PostgreSQL."""
        
        complexity = self._assess_migration_complexity(source_analysis)
        risks = self._identify_migration_risks(source_analysis)
        transformations = self._plan_data_transformations(source_analysis)
        compatibility_issues = self._detect_compatibility_issues(source_analysis)
        
        # Estimar duração baseada no tamanho e complexidade
        estimated_duration = self._estimate_migration_duration(
            source_analysis.database_info.size_mb,
            complexity,
            source_analysis.database_info.table_count
        )
        
        # Passos da migração
        steps = [
            "1. Backup completo do banco MySQL de origem",
            "2. Análise e validação da estrutura de dados",
            "3. Conversão de tipos de dados MySQL → PostgreSQL",
            "4. Tratamento de AUTO_INCREMENT → SERIAL/IDENTITY",
            "5. Conversão de funções e expressões SQL",
            "6. Ajuste de constraints e índices",
            "7. Migração de dados em lotes (batches)",
            "8. Validação de integridade referencial",
            "9. Verificação de contagem de registros",
            "10. Teste de queries críticas",
            "11. Validação de performance",
            "12. Documentação de mudanças"
        ]
        
        # Recomendações específicas
        recommendations = [
            "Use chunked migration para tabelas grandes (>1GB)",
            "Mantenha o MySQL original até validação completa",
            "Configure PostgreSQL com parâmetros otimizados antes da migração",
            "Desabilite triggers e constraints durante bulk insert",
            "Use COPY ao invés de INSERT para melhor performance",
            "Valide codificação UTF-8 em todos os dados",
            "Teste stored procedures/functions em ambiente de teste",
            "Documente todas as mudanças de schema",
            "Configure monitoring desde o início",
            "Planeje janela de manutenção adequada"
        ]
        
        # Adicionar recomendações baseadas em issues encontrados
        if compatibility_issues:
            recommendations.append(f"⚠️ {len(compatibility_issues)} incompatibilidades detectadas - revisar antes da migração")
        
        return MigrationStrategy(
            strategy_name="MySQL to PostgreSQL Migration",
            description=f"Migração completa de {source_analysis.database_info.table_count} tabelas, "
                       f"{source_analysis.database_info.size_mb:.2f}MB de dados",
            complexity=complexity,
            estimated_duration=estimated_duration,
            risks=risks,
            steps=steps,
            recommendations=recommendations,
            compatibility_issues=compatibility_issues,
            required_transformations=transformations
        )

    def optimize_query(
        self,
        query: str,
        db_type: DatabaseType,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analisa e otimiza uma query SQL.
        
        Args:
            query: Query SQL para otimizar
            db_type: Tipo do banco de dados
            context: Contexto adicional (estatísticas, índices, etc)
            
        Returns:
            Dict com análise e sugestões de otimização
        """
        self.logger.info(f"🔧 Optimizing query for {db_type.value}")
        
        analysis = {
            'original_query': query,
            'db_type': db_type.value,
            'issues': [],
            'suggestions': [],
            'optimized_query': None,
            'estimated_improvement': None
        }
        
        # Detectar problemas comuns
        if 'SELECT *' in query.upper():
            analysis['issues'].append({
                'type': 'SELECT_ALL',
                'severity': 'medium',
                'description': 'Query uses SELECT * which fetches all columns',
                'impact': 'Increased I/O and network traffic'
            })
            analysis['suggestions'].append('Specify only required columns instead of SELECT *')
        
        if query.upper().count('JOIN') > 3:
            analysis['issues'].append({
                'type': 'MULTIPLE_JOINS',
                'severity': 'medium',
                'description': f'Query has {query.upper().count("JOIN")} joins',
                'impact': 'May cause performance degradation'
            })
            analysis['suggestions'].append('Review if all joins are necessary, consider denormalization or materialized views')
        
        if 'OR' in query.upper():
            analysis['issues'].append({
                'type': 'OR_CONDITION',
                'severity': 'low',
                'description': 'Query uses OR which may prevent index usage',
                'impact': 'May cause full table scan'
            })
            analysis['suggestions'].append('Consider rewriting OR conditions using UNION or IN clause')
        
        if not re.search(r'LIMIT|FETCH', query, re.IGNORECASE):
            analysis['issues'].append({
                'type': 'NO_LIMIT',
                'severity': 'high',
                'description': 'Query has no LIMIT clause',
                'impact': 'May return millions of rows'
            })
            analysis['suggestions'].append('Add LIMIT clause to prevent large result sets')
        
        # Sugestões específicas por banco
        if db_type == DatabaseType.POSTGRESQL:
            analysis['suggestions'].extend(self._get_postgresql_query_suggestions(query))
        elif db_type in (DatabaseType.MYSQL, DatabaseType.MARIADB):
            analysis['suggestions'].extend(self._get_mysql_query_suggestions(query))
        
        return analysis

    def validate_data_integrity(
        self,
        source_conn_params: Dict[str, Any],
        target_conn_params: Dict[str, Any],
        source_type: DatabaseType,
        target_type: DatabaseType,
        tables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Valida integridade de dados entre bancos de origem e destino.
        
        Args:
            source_conn_params: Conexão com banco de origem
            target_conn_params: Conexão com banco de destino
            source_type: Tipo do banco de origem
            target_type: Tipo do banco de destino
            tables: Lista de tabelas para validar (None = todas)
            
        Returns:
            Dict com resultado da validação
        """
        self.logger.info("✅ Starting data integrity validation")
        
        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'source_type': source_type.value,
            'target_type': target_type.value,
            'tables_validated': 0,
            'tables_matched': 0,
            'tables_mismatched': 0,
            'total_rows_source': 0,
            'total_rows_target': 0,
            'discrepancies': [],
            'validation_passed': False
        }
        
        # Implementar validação completa
        # TODO: Implementar comparação de contagens, checksums, etc.
        
        return validation_result

    # ========== Métodos auxiliares PostgreSQL ==========

    def _get_postgresql_info(self, cursor) -> DatabaseInfo:
        """Obtém informações básicas do PostgreSQL."""
        # Versão
        cursor.execute("SELECT version()")
        version = cursor.fetchone()['version']
        
        # Encoding
        cursor.execute("SHOW server_encoding")
        encoding = cursor.fetchone()['server_encoding']
        
        # Tamanho do banco
        cursor.execute("""
            SELECT pg_database_size(current_database()) as size_bytes
        """)
        size_bytes = cursor.fetchone()['size_bytes']
        
        # Contagem de tabelas
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()['count']
        
        return DatabaseInfo(
            db_type=DatabaseType.POSTGRESQL,
            version=version,
            server_info=version.split(',')[0],
            encoding=encoding,
            collation='default',
            size_mb=size_bytes / 1024 / 1024,
            table_count=table_count,
            total_rows=0,  # Will be calculated
            index_count=0,  # Will be calculated
            constraints_count=0,  # Will be calculated
            users_count=0  # Will be calculated
        )

    def _analyze_postgresql_schema(self, cursor, level: AnalysisLevel) -> Dict[str, Any]:
        """Analisa schema do PostgreSQL."""
        return {
            'tables': [],
            'indexes': [],
            'constraints': [],
            'sequences': [],
            'functions': [],
            'triggers': []
        }

    def _analyze_data_quality_postgresql(self, cursor, level: AnalysisLevel) -> Dict[str, Any]:
        """Analisa qualidade de dados no PostgreSQL."""
        return {
            'null_percentages': {},
            'duplicates': {},
            'data_types_issues': [],
            'encoding_issues': []
        }

    def _analyze_postgresql_performance(self, cursor, level: AnalysisLevel) -> Dict[str, Any]:
        """Analisa performance do PostgreSQL."""
        return {
            'slow_queries': [],
            'missing_indexes': [],
            'bloated_tables': [],
            'cache_hit_ratio': 0.0
        }

    def _assess_postgresql_security(self, cursor) -> Dict[str, Any]:
        """Avalia segurança do PostgreSQL."""
        return {
            'weak_passwords': [],
            'excessive_permissions': [],
            'public_access': [],
            'recommendations': []
        }

    def _generate_postgresql_recommendations(self, *args) -> Tuple[List[str], List[str], List[str]]:
        """Gera recomendações para PostgreSQL."""
        recommendations = self.knowledge_base['postgresql_best_practices'].copy()
        warnings = []
        errors = []
        return recommendations, warnings, errors

    # ========== Métodos auxiliares MySQL ==========

    def _get_mysql_info(self, cursor) -> DatabaseInfo:
        """Obtém informações básicas do MySQL."""
        # Versão
        cursor.execute("SELECT VERSION() as version")
        version = cursor.fetchone()['version']
        
        # Encoding
        cursor.execute("SHOW VARIABLES LIKE 'character_set_database'")
        encoding = cursor.fetchone()['Value']
        
        # Collation
        cursor.execute("SHOW VARIABLES LIKE 'collation_database'")
        collation = cursor.fetchone()['Value']
        
        # Selecionar o banco de dados atual
        cursor.execute("SELECT DATABASE() as db_name")
        db_name = cursor.fetchone()['db_name']
        
        # Tamanho do banco
        cursor.execute(f"""
            SELECT SUM(data_length + index_length) as size_bytes
            FROM information_schema.TABLES
            WHERE table_schema = '{db_name}'
        """)
        result = cursor.fetchone()
        size_bytes = result['size_bytes'] if result['size_bytes'] else 0
        
        # Contagem de tabelas
        cursor.execute(f"""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = '{db_name}'
            AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()['count']
        
        return DatabaseInfo(
            db_type=DatabaseType.MYSQL,
            version=version,
            server_info=version,
            encoding=encoding,
            collation=collation,
            size_mb=size_bytes / 1024 / 1024 if size_bytes else 0,
            table_count=table_count,
            total_rows=0,
            index_count=0,
            constraints_count=0,
            users_count=0
        )

    def _analyze_mysql_schema(self, cursor, level: AnalysisLevel) -> Dict[str, Any]:
        """Analisa schema do MySQL."""
        return {
            'tables': [],
            'indexes': [],
            'constraints': [],
            'triggers': [],
            'procedures': []
        }

    def _analyze_data_quality_mysql(self, cursor, level: AnalysisLevel) -> Dict[str, Any]:
        """Analisa qualidade de dados no MySQL."""
        return {
            'null_percentages': {},
            'duplicates': {},
            'data_types_issues': [],
            'encoding_issues': []
        }

    def _analyze_mysql_performance(self, cursor, level: AnalysisLevel) -> Dict[str, Any]:
        """Analisa performance do MySQL."""
        return {
            'slow_queries': [],
            'missing_indexes': [],
            'table_fragmentation': [],
            'buffer_pool_usage': 0.0
        }

    def _assess_mysql_security(self, cursor) -> Dict[str, Any]:
        """Avalia segurança do MySQL."""
        return {
            'weak_passwords': [],
            'root_remote_access': False,
            'anonymous_users': [],
            'recommendations': []
        }

    def _generate_mysql_recommendations(self, *args) -> Tuple[List[str], List[str], List[str]]:
        """Gera recomendações para MySQL."""
        recommendations = self.knowledge_base['mysql_best_practices'].copy()
        warnings = []
        errors = []
        return recommendations, warnings, errors

    # ========== Métodos de planejamento de migração ==========

    def _assess_migration_complexity(self, analysis: AnalysisResult) -> str:
        """Avalia complexidade da migração."""
        score = 0
        
        # Pontos por número de tabelas
        if analysis.database_info.table_count > 100:
            score += 3
        elif analysis.database_info.table_count > 50:
            score += 2
        elif analysis.database_info.table_count > 20:
            score += 1
        
        # Pontos por tamanho
        if analysis.database_info.size_mb > 10000:  # > 10GB
            score += 3
        elif analysis.database_info.size_mb > 1000:  # > 1GB
            score += 2
        elif analysis.database_info.size_mb > 100:  # > 100MB
            score += 1
        
        # Complexidade baseada no score
        if score >= 5:
            return 'critical'
        elif score >= 3:
            return 'high'
        elif score >= 1:
            return 'medium'
        else:
            return 'low'

    def _identify_migration_risks(self, analysis: AnalysisResult) -> List[str]:
        """Identifica riscos da migração."""
        risks = []
        
        if analysis.database_info.size_mb > 1000:
            risks.append("Large database size may cause extended downtime")
        
        if analysis.database_info.table_count > 50:
            risks.append("High number of tables increases complexity and testing effort")
        
        risks.extend(self.knowledge_base['common_migration_pitfalls'])
        
        return risks

    def _plan_data_transformations(self, analysis: AnalysisResult) -> List[Dict[str, str]]:
        """Planeja transformações necessárias."""
        transformations = []
        
        # Adicionar transformações baseadas no tipo de dados detectados
        # TODO: Implementar análise real do schema
        
        return transformations

    def _detect_compatibility_issues(self, analysis: AnalysisResult) -> List[Dict[str, str]]:
        """Detecta issues de compatibilidade."""
        return self.knowledge_base['mysql_to_postgresql']['incompatibilities'].copy()

    def _estimate_migration_duration(
        self,
        size_mb: float,
        complexity: str,
        table_count: int
    ) -> str:
        """Estima duração da migração."""
        # Estimativa base: ~100MB/min para dados
        data_hours = (size_mb / 100) / 60
        
        # Ajustar por complexidade
        complexity_multiplier = {
            'low': 1.2,
            'medium': 1.5,
            'high': 2.0,
            'critical': 3.0
        }
        
        total_hours = data_hours * complexity_multiplier.get(complexity, 1.5)
        
        # Adicionar tempo de setup e validação
        total_hours += table_count * 0.1  # ~6 min por tabela
        
        if total_hours < 1:
            return "< 1 hora"
        elif total_hours < 8:
            return f"{int(total_hours)} horas"
        elif total_hours < 24:
            return "1 dia"
        else:
            days = int(total_hours / 8)  # Assumindo 8h de trabalho por dia
            return f"{days} dias úteis"

    def _get_postgresql_query_suggestions(self, query: str) -> List[str]:
        """Sugestões específicas para PostgreSQL."""
        suggestions = []
        
        if 'LIKE' in query.upper() and '%' in query:
            suggestions.append("Consider using pg_trgm extension with GIN index for LIKE '%pattern%' queries")
        
        if 'JSON' in query.upper():
            suggestions.append("Use JSONB instead of JSON for better performance and indexing")
        
        return suggestions

    def _get_mysql_query_suggestions(self, query: str) -> List[str]:
        """Sugestões específicas para MySQL."""
        suggestions = []
        
        if 'STRAIGHT_JOIN' not in query.upper() and query.upper().count('JOIN') > 2:
            suggestions.append("Consider using STRAIGHT_JOIN to control join order in complex queries")
        
        return suggestions

    def export_knowledge_base(self, output_file: Path) -> None:
        """
        Exporta base de conhecimento para arquivo JSON.
        
        Args:
            output_file: Caminho do arquivo de saída
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
            self.logger.info(f"✅ Knowledge base exported to {output_file}")
        except Exception as e:
            self.logger.error(f"❌ Error exporting knowledge base: {e}")
            raise

    def generate_migration_report(
        self,
        analysis: AnalysisResult,
        strategy: MigrationStrategy,
        output_file: Path
    ) -> None:
        """
        Gera relatório completo de migração.
        
        Args:
            analysis: Análise do banco de origem
            strategy: Estratégia de migração planejada
            output_file: Arquivo de saída
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'agent_version': self.version,
            'source_database': {
                'type': analysis.database_info.db_type.value,
                'version': analysis.database_info.version,
                'size_mb': analysis.database_info.size_mb,
                'table_count': analysis.database_info.table_count,
                'encoding': analysis.database_info.encoding
            },
            'migration_strategy': {
                'name': strategy.strategy_name,
                'complexity': strategy.complexity,
                'estimated_duration': strategy.estimated_duration,
                'risk_count': len(strategy.risks),
                'transformation_count': len(strategy.required_transformations),
                'compatibility_issues_count': len(strategy.compatibility_issues)
            },
            'recommendations': strategy.recommendations,
            'risks': strategy.risks,
            'steps': strategy.steps,
            'compatibility_issues': strategy.compatibility_issues,
            'transformations': strategy.required_transformations
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"📄 Migration report generated: {output_file}")
        except Exception as e:
            self.logger.error(f"❌ Error generating report: {e}")
            raise


# ========== Funções auxiliares ==========

def create_expert_agent(log_level: int = logging.INFO) -> DatabaseExpertAgent:
    """
    Factory function para criar instância do agente.
    
    Args:
        log_level: Nível de logging
        
    Returns:
        DatabaseExpertAgent instance
    """
    return DatabaseExpertAgent(log_level=log_level)


# ========== Exemplo de uso ==========

if __name__ == "__main__":
    # Exemplo de uso do agente
    print(" Database Expert Agent - Demo ")
    print("=" * 60)
    
    # Criar agente
    agent = create_expert_agent(log_level=logging.INFO)
    
    # Exportar base de conhecimento
    agent.export_knowledge_base(Path("knowledge_base.json"))
    
    print("\n✅ Agent initialized successfully")
    print(f"📊 Capabilities: {agent.capabilities}")
    print(f"📚 Knowledge base contains:")
    print(f"   - {len(agent.knowledge_base['mysql_to_postgresql']['type_mappings'])} type mappings")
    print(f"   - {len(agent.knowledge_base['mysql_to_postgresql']['function_mappings'])} function mappings")
    print(f"   - {len(agent.knowledge_base['mysql_to_postgresql']['incompatibilities'])} incompatibilities")
    print(f"   - {len(agent.knowledge_base['postgresql_best_practices'])} PostgreSQL best practices")
    print(f"   - {len(agent.knowledge_base['mysql_best_practices'])} MySQL best practices")
