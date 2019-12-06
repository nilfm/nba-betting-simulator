"""empty message

Revision ID: 765473082525
Revises: e048f166c7b3
Create Date: 2019-12-04 00:05:35.512505

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '765473082525'
down_revision = 'e048f166c7b3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('timestamp_games',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timestamp_games_timestamp'), 'timestamp_games', ['timestamp'], unique=False)
    op.create_table('timestamp_scores',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timestamp_scores_timestamp'), 'timestamp_scores', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_timestamp_scores_timestamp'), table_name='timestamp_scores')
    op.drop_table('timestamp_scores')
    op.drop_index(op.f('ix_timestamp_games_timestamp'), table_name='timestamp_games')
    op.drop_table('timestamp_games')
    # ### end Alembic commands ###