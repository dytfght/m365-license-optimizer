"""
Alembic migration for LOT 10: Audit logs and GDPR fields.
Note: Run this migration with: alembic revision --autogenerate -m "lot10_audit_logs_gdpr"
"""

# This is a template - the actual migration should be generated with:
# cd backend && alembic revision --autogenerate -m "lot10_audit_logs_gdpr"

# Expected changes:
# 1. Create table optimizer.audit_logs with columns:
#    - id (UUID, primary key)
#    - created_at, updated_at (timestamps)
#    - level (varchar 20, indexed)
#    - message (text)
#    - endpoint (varchar 255, indexed)
#    - method (varchar 10)
#    - request_id (varchar 36, indexed)
#    - user_id (UUID, FK to optimizer.users, nullable)
#    - tenant_id (UUID, FK to optimizer.tenant_clients, nullable)
#    - ip_address (varchar 45)
#    - user_agent (varchar 500)
#    - response_status (integer, indexed)
#    - duration_ms (integer)
#    - extra_data (jsonb)
#    - action (varchar 100, indexed)
#
# 2. Add columns to optimizer.tenant_clients:
#    - gdpr_consent (boolean, default False)
#    - gdpr_consent_date (timestamp with timezone, nullable)

# To generate and run:
# cd backend
# alembic revision --autogenerate -m "lot10_audit_logs_gdpr"
# alembic upgrade head
