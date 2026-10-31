"""業務事實、版本、責任記錄與行級安全。"""

from alembic import op
from medical_quality.models import Base

revision = "001_initial"
down_revision = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(op.get_bind())
    case_policy = """(
      (current_setting('mq.role', true) = 'qc'
        AND group_id = ANY(string_to_array(current_setting('mq.groups', true), ',')))
      OR (current_setting('mq.role', true) = 'doctor'
        AND owner_id = current_setting('mq.actor', true))
      OR id = ANY(string_to_array(current_setting('mq.cases', true), ','))
    )"""
    op.execute("ALTER TABLE cases ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cases FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY case_scope ON cases USING ({case_policy}) WITH CHECK ({case_policy})")
    for table in ["documents", "findings", "tasks", "decisions", "signatures", "quality_runs"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        condition = f"EXISTS (SELECT 1 FROM cases WHERE cases.id = {table}.case_id)"
        op.execute(f"CREATE POLICY case_scope ON {table} USING ({condition}) WITH CHECK ({condition})")
    op.execute("ALTER TABLE evidence_items ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE evidence_items FORCE ROW LEVEL SECURITY")
    condition = """(EXISTS (SELECT 1 FROM cases WHERE cases.id = evidence_items.case_id)
      OR (case_id IS NULL AND data_role IN ('schema_reference','rule_reference','terminology')
          AND current_setting('mq.role',true) IN ('qc','doctor','expert','info','manager'))
      OR (case_id IS NULL AND data_role = 'business_evidence'
          AND current_setting('mq.role',true) = 'qc'))"""
    op.execute(f"CREATE POLICY evidence_scope ON evidence_items USING ({condition}) WITH CHECK ({condition})")
    # Read-only research parsing may be performed by the information team, while their
    # application routes still prohibit returning body/evidence payloads.
    op.execute("""CREATE POLICY evidence_ingest ON evidence_items FOR INSERT
        WITH CHECK (current_setting('mq.role',true) IN ('qc','info'))""")
    op.execute("GRANT USAGE ON SCHEMA public TO mq_app, mq_worker")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mq_app, mq_worker")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mq_app, mq_worker")
    # History is append-only for ordinary application and worker roles.
    for table in [
        "audit_events",
        "decisions",
        "signatures",
        "documents",
        "source_snapshots",
        "judgments",
        "arbitrations",
        "gate_decisions",
    ]:
        op.execute(f"REVOKE UPDATE, DELETE ON {table} FROM mq_app, mq_worker")


def downgrade():
    raise RuntimeError("包含醫療責任歷史；請使用經審閱的數據遷移，不提供破壞性降級。")
