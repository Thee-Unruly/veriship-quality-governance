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
    
    # Create audit table for tracking changes
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(50), nullable=False),  # INSERT, UPDATE, DELETE
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_audit_logs_user_id', 'user_id'),
        sa.Index('ix_audit_logs_table_name', 'table_name'),
        sa.Index('ix_audit_logs_created_at', 'created_at'),
    )
    
    # Enable RLS extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # ===== PROJECTS TABLE =====
    # Enable RLS
    op.execute('ALTER TABLE projects ENABLE ROW LEVEL SECURITY')
    
    # Policy: Users can view projects they're assigned to
    op.execute('''
        CREATE POLICY projects_select_policy ON projects
        FOR SELECT
        USING (
            id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    # Policy: Users can insert projects they create (via admin or lead role)
    op.execute('''
        CREATE POLICY projects_insert_policy ON projects
        FOR INSERT
        WITH CHECK (true)  -- Application layer handles authorization
    ''')
    
    # Policy: Users can update projects they're assigned to
    op.execute('''
        CREATE POLICY projects_update_policy ON projects
        FOR UPDATE
        USING (
            id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    # Policy: Users can delete projects they're assigned to
    op.execute('''
        CREATE POLICY projects_delete_policy ON projects
        FOR DELETE
        USING (
            id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    # ===== REQUIREMENTS TABLE =====
    op.execute('ALTER TABLE requirements ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY requirements_select_policy ON requirements
        FOR SELECT
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    op.execute('''
        CREATE POLICY requirements_insert_policy ON requirements
        FOR INSERT
        WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY requirements_update_policy ON requirements
        FOR UPDATE
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    op.execute('''
        CREATE POLICY requirements_delete_policy ON requirements
        FOR DELETE
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    # ===== TEST_CASES TABLE =====
    op.execute('ALTER TABLE test_cases ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY test_cases_select_policy ON test_cases
        FOR SELECT
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    op.execute('''
        CREATE POLICY test_cases_insert_policy ON test_cases
        FOR INSERT
        WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY test_cases_update_policy ON test_cases
        FOR UPDATE
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    op.execute('''
        CREATE POLICY test_cases_delete_policy ON test_cases
        FOR DELETE
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    # ===== DEFECTS TABLE =====
    op.execute('ALTER TABLE defects ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY defects_select_policy ON defects
        FOR SELECT
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    op.execute('''
        CREATE POLICY defects_insert_policy ON defects
        FOR INSERT
        WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY defects_update_policy ON defects
        FOR UPDATE
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    op.execute('''
        CREATE POLICY defects_delete_policy ON defects
        FOR DELETE
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    # ===== RELEASES TABLE =====
    op.execute('ALTER TABLE releases ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY releases_select_policy ON releases
        FOR SELECT
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    op.execute('''
        CREATE POLICY releases_insert_policy ON releases
        FOR INSERT
        WITH CHECK (true)
    ''')
    
    op.execute('''
        CREATE POLICY releases_update_policy ON releases
        FOR UPDATE
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    op.execute('''
        CREATE POLICY releases_delete_policy ON releases
        FOR DELETE
        USING (
            project_id IN (
                SELECT project_id FROM user_project_assignment 
                WHERE user_id = current_user_id()
            )
        )
    ''')
    
    # ===== AUDIT LOGS TABLE =====
    # Users can only view audit logs for their projects
    op.execute('ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY')
    
    op.execute('''
        CREATE POLICY audit_logs_select_policy ON audit_logs
        FOR SELECT
        USING (true)  -- Application layer handles filtering
    ''')
    
    op.execute('''
        CREATE POLICY audit_logs_insert_policy ON audit_logs
        FOR INSERT
        WITH CHECK (true)
    ''')


def downgrade() -> None:
    """Disable RLS policies."""
    
    # Drop RLS policies
    op.execute('ALTER TABLE projects DISABLE ROW LEVEL SECURITY')
    op.execute('DROP POLICY IF EXISTS projects_select_policy ON projects')
    op.execute('DROP POLICY IF EXISTS projects_insert_policy ON projects')
    op.execute('DROP POLICY IF EXISTS projects_update_policy ON projects')
    op.execute('DROP POLICY IF EXISTS projects_delete_policy ON projects')
    
    op.execute('ALTER TABLE requirements DISABLE ROW LEVEL SECURITY')
    op.execute('DROP POLICY IF EXISTS requirements_select_policy ON requirements')
    op.execute('DROP POLICY IF EXISTS requirements_insert_policy ON requirements')
    op.execute('DROP POLICY IF EXISTS requirements_update_policy ON requirements')
    op.execute('DROP POLICY IF EXISTS requirements_delete_policy ON requirements')
    
    op.execute('ALTER TABLE test_cases DISABLE ROW LEVEL SECURITY')
    op.execute('DROP POLICY IF EXISTS test_cases_select_policy ON test_cases')
    op.execute('DROP POLICY IF EXISTS test_cases_insert_policy ON test_cases')
    op.execute('DROP POLICY IF EXISTS test_cases_update_policy ON test_cases')
    op.execute('DROP POLICY IF EXISTS test_cases_delete_policy ON test_cases')
    
    op.execute('ALTER TABLE defects DISABLE ROW LEVEL SECURITY')
    op.execute('DROP POLICY IF EXISTS defects_select_policy ON defects')
    op.execute('DROP POLICY IF EXISTS defects_insert_policy ON defects')
    op.execute('DROP POLICY IF EXISTS defects_update_policy ON defects')
    op.execute('DROP POLICY IF EXISTS defects_delete_policy ON defects')
    
    op.execute('ALTER TABLE releases DISABLE ROW LEVEL SECURITY')
    op.execute('DROP POLICY IF EXISTS releases_select_policy ON releases')
    op.execute('DROP POLICY IF EXISTS releases_insert_policy ON releases')
    op.execute('DROP POLICY IF EXISTS releases_update_policy ON releases')
    op.execute('DROP POLICY IF EXISTS releases_delete_policy ON releases')
    
    op.execute('ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY')
    op.execute('DROP POLICY IF EXISTS audit_logs_select_policy ON audit_logs')
    op.execute('DROP POLICY IF EXISTS audit_logs_insert_policy ON audit_logs')
    
    # Drop audit table
    op.drop_table('audit_logs')
