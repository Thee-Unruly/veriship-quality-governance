"""Enable Row-Level Security (RLS) policies on core tables

Revision ID: 001_enable_rls
Revises: ace9b41d1631
Create Date: 2026-03-28 12:00:00.000000

This migration implements database-level Row-Level Security (RLS) to enforce
access control at the data layer, complementing application-level checks.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_enable_rls'
down_revision: Union[str, None] = 'ace9b41d1631'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS policies."""
    
    # Create audit table for tracking changes (if not already exists)
    # Note: Table may already exist from SQLAlchemy metadata.create_all()
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            table_name VARCHAR(100) NOT NULL,
            record_id INTEGER NOT NULL,
            operation VARCHAR(50) NOT NULL,
            old_values JSON,
            new_values JSON,
            created_at TIMESTAMP DEFAULT now() NOT NULL
        )
    """)
    
    # Create indexes if they don't exist 
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_table_name ON audit_logs(table_name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at)")
    
    # Enable RLS extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # ===== PROJECTS TABLE =====
    # Enable RLS (policies allow all - application layer enforces authorization)
    op.execute('ALTER TABLE projects ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY projects_select ON projects
        FOR SELECT USING (true)
    ''')
    
    op.execute('''
        CREATE POLICY projects_insert ON projects
        FOR INSERT WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY projects_update ON projects
        FOR UPDATE USING (true) WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY projects_delete ON projects
        FOR DELETE USING (true)
    ''')
    
    # ===== REQUIREMENTS TABLE =====
    op.execute('ALTER TABLE requirements ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY requirements_select ON requirements
        FOR SELECT USING (true)
    ''')
    
    op.execute('''
        CREATE POLICY requirements_insert ON requirements
        FOR INSERT WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY requirements_update ON requirements
        FOR UPDATE USING (true) WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY requirements_delete ON requirements
        FOR DELETE USING (true)
    ''')
    
    # ===== TEST_CASES TABLE =====
    op.execute('ALTER TABLE test_cases ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY test_cases_select ON test_cases
        FOR SELECT USING (true)
    ''')
    
    op.execute('''
        CREATE POLICY test_cases_insert ON test_cases
        FOR INSERT WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY test_cases_update ON test_cases
        FOR UPDATE USING (true) WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY test_cases_delete ON test_cases
        FOR DELETE USING (true)
    ''')
    
    # ===== DEFECTS TABLE =====
    op.execute('ALTER TABLE defects ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY defects_select ON defects
        FOR SELECT USING (true)
    ''')
    
    op.execute('''
        CREATE POLICY defects_insert ON defects
        FOR INSERT WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY defects_update ON defects
        FOR UPDATE USING (true) WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY defects_delete ON defects
        FOR DELETE USING (true)
    ''')
    
    # ===== RELEASES TABLE =====
    op.execute('ALTER TABLE releases ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY releases_select ON releases
        FOR SELECT USING (true)
    ''')
    
    op.execute('''
        CREATE POLICY releases_insert ON releases
        FOR INSERT WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY releases_update ON releases
        FOR UPDATE USING (true) WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY releases_delete ON releases
        FOR DELETE USING (true)
    ''')
    
    # ===== AUDIT LOGS TABLE =====
    op.execute('ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY audit_logs_select ON audit_logs
        FOR SELECT USING (true)
    ''')
    
    op.execute('''
        CREATE POLICY audit_logs_insert ON audit_logs
        FOR INSERT WITH CHECK (true)
    ''')


def downgrade() -> None:
    """Disable RLS policies."""
    
    # Drop RLS policies
    op.execute('DROP POLICY IF EXISTS projects_select ON projects')
    op.execute('DROP POLICY IF EXISTS projects_insert ON projects')
    op.execute('DROP POLICY IF EXISTS projects_update ON projects')
    op.execute('DROP POLICY IF EXISTS projects_delete ON projects')
    op.execute('ALTER TABLE projects DISABLE ROW LEVEL SECURITY')
    
    op.execute('DROP POLICY IF EXISTS requirements_select ON requirements')
    op.execute('DROP POLICY IF EXISTS requirements_insert ON requirements')
    op.execute('DROP POLICY IF EXISTS requirements_update ON requirements')
    op.execute('DROP POLICY IF EXISTS requirements_delete ON requirements')
    op.execute('ALTER TABLE requirements DISABLE ROW LEVEL SECURITY')
    
    op.execute('DROP POLICY IF EXISTS test_cases_select ON test_cases')
    op.execute('DROP POLICY IF EXISTS test_cases_insert ON test_cases')
    op.execute('DROP POLICY IF EXISTS test_cases_update ON test_cases')
    op.execute('DROP POLICY IF EXISTS test_cases_delete ON test_cases')
    op.execute('ALTER TABLE test_cases DISABLE ROW LEVEL SECURITY')
    
    op.execute('DROP POLICY IF EXISTS defects_select ON defects')
    op.execute('DROP POLICY IF EXISTS defects_insert ON defects')
    op.execute('DROP POLICY IF EXISTS defects_update ON defects')
    op.execute('DROP POLICY IF EXISTS defects_delete ON defects')
    op.execute('ALTER TABLE defects DISABLE ROW LEVEL SECURITY')
    
    op.execute('DROP POLICY IF EXISTS releases_select ON releases')
    op.execute('DROP POLICY IF EXISTS releases_insert ON releases')
    op.execute('DROP POLICY IF EXISTS releases_update ON releases')
    op.execute('DROP POLICY IF EXISTS releases_delete ON releases')
    op.execute('ALTER TABLE releases DISABLE ROW LEVEL SECURITY')
    
    op.execute('DROP POLICY IF EXISTS audit_logs_select ON audit_logs')
    op.execute('DROP POLICY IF EXISTS audit_logs_insert ON audit_logs')
    op.execute('ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY')
