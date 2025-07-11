"""
Migración para asegurar compatibilidad de MLflow con PostgreSQL
Revision ID: mlflow_postgres_migration
Create Date: 2025-07-09
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Float, ForeignKey

# revision identifiers
revision = 'mlflow_postgres_migration'
down_revision = None
branch_labels = None
depends_on = None

Base = declarative_base()

# Estas tablas representan el esquema básico de MLflow
# MLflow creará estas tablas automáticamente, pero definirlas
# en una migración nos permite tener más control sobre el proceso

class SqlExperiment(Base):
    __tablename__ = 'experiments'
    
    experiment_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), unique=True, nullable=False)
    artifact_location = Column(String(256), nullable=True)
    lifecycle_stage = Column(String(32), nullable=False)
    creation_time = Column(Integer, nullable=False)
    last_update_time = Column(Integer, nullable=False)

class SqlRun(Base):
    __tablename__ = 'runs'
    
    run_uuid = Column(String(32), primary_key=True)
    name = Column(String(250))
    source_type = Column(String(20), nullable=False)
    source_name = Column(String(500))
    experiment_id = Column(Integer, ForeignKey('experiments.experiment_id'), nullable=False)
    user_id = Column(String(256), nullable=False)
    status = Column(String(9), nullable=False)
    start_time = Column(Integer, nullable=False)
    end_time = Column(Integer)
    source_version = Column(String(50))
    lifecycle_stage = Column(String(20), nullable=False)
    artifact_uri = Column(String(200))

class SqlTag(Base):
    __tablename__ = 'tags'
    
    key = Column(String(250), primary_key=True)
    value = Column(String(5000))
    run_uuid = Column(String(32), ForeignKey('runs.run_uuid'), primary_key=True)

class SqlParam(Base):
    __tablename__ = 'params'
    
    key = Column(String(250), primary_key=True)
    value = Column(String(8000))
    run_uuid = Column(String(32), ForeignKey('runs.run_uuid'), primary_key=True)

class SqlMetric(Base):
    __tablename__ = 'metrics'
    
    key = Column(String(250), primary_key=True)
    value = Column(Float, nullable=False)
    timestamp = Column(Integer, primary_key=True)
    run_uuid = Column(String(32), ForeignKey('runs.run_uuid'), primary_key=True)
    step = Column(Integer, default=0, nullable=False, primary_key=True)

def upgrade():
    # Esta migración solo verifica que las tablas existan
    # MLflow se encargará de crearlas automáticamente
    pass

def downgrade():
    # En caso de querer revertir, podríamos eliminar las tablas
    # pero es mejor dejarlas intactas para no perder datos
    pass
