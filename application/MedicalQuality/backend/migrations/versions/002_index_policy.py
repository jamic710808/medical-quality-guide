"""規則資格版本與獨立知識索引發布清單。"""

from alembic import op
import sqlalchemy as sa
from medical_quality.models import KnowledgeIndex

revision = "002_index_policy"
down_revision = "001_initial"


def upgrade():
    if "policy_version" not in {c["name"] for c in sa.inspect(op.get_bind()).get_columns("rules")}:
        op.add_column("rules", sa.Column("policy_version", sa.Integer(), nullable=False, server_default="1"))
    KnowledgeIndex.__table__.create(op.get_bind(), checkfirst=True)
    op.execute("GRANT SELECT, INSERT, UPDATE ON knowledge_indices TO mq_app, mq_worker")


def downgrade():
    raise RuntimeError("索引及資格歷史只能經審閱遷移，不提供破壞性降級。")
