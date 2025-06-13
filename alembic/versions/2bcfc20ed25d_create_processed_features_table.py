from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision = '2bcfc20ed25d'
down_revision = '69159aeeae69'
branch_labels = None
depends_on = None

# Obtener el esquema si usás variables de entorno (opcional)
schema = os.environ.get("CHESS_TRAINER_SCHEMA", "public")


def upgrade():
    op.create_table(
        'processed_features',
        sa.Column('game_id', sa.String(), primary_key=True),
        sa.Column('date_processed', sa.DateTime(), nullable=False),
        schema=schema
    )


def downgrade():
    op.drop_table('processed_features', schema=schema)
