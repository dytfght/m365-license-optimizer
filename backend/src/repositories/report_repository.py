"""
Report Repository - Data access layer for reports
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.report import Report
from .base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository for Report operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(Report, session)

    async def get_by_analysis_id(self, analysis_id: UUID) -> List[Report]:
        """Get all reports for an analysis"""
        
        result = await self.session.execute(
            select(Report)
            .where(Report.analysis_id == analysis_id)
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_tenant_id(self, tenant_id: UUID) -> List[Report]:
        """Get all reports for a tenant"""
        
        result = await self.session.execute(
            select(Report)
            .where(Report.tenant_client_id == tenant_id)
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_type(self, report_type: str) -> List[Report]:
        """Get reports by type (PDF/EXCEL)"""
        
        result = await self.session.execute(
            select(Report)
            .where(Report.report_type == report_type.upper())
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_reports(self, tenant_id: Optional[UUID] = None) -> List[Report]:
        """Get reports that haven't expired"""
        
        now = datetime.utcnow()
        
        query = select(Report).where(
            or_(
                Report.expires_at.is_(None),
                Report.expires_at > now
            )
        ).order_by(Report.created_at.desc())
        
        if tenant_id:
            query = query.where(Report.tenant_client_id == tenant_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expired_reports(self, tenant_id: Optional[UUID] = None) -> List[Report]:
        """Get reports that have expired"""
        
        now = datetime.utcnow()
        
        query = select(Report).where(
            and_(
                Report.expires_at.is_not(None),
                Report.expires_at <= now
            )
        ).order_by(Report.expires_at.asc())
        
        if tenant_id:
            query = query.where(Report.tenant_client_id == tenant_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_reports(
        self, 
        days: int = 30, 
        tenant_id: Optional[UUID] = None,
        report_type: Optional[str] = None
    ) -> List[Report]:
        """Get reports from the last N days"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(Report).where(Report.created_at >= cutoff_date)
        
        if tenant_id:
            query = query.where(Report.tenant_client_id == tenant_id)
        
        if report_type:
            query = query.where(Report.report_type == report_type.upper())
        
        query = query.order_by(Report.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_reports_by_tenant(self, tenant_id: UUID) -> int:
        """Count total reports for a tenant"""
        
        result = await self.session.execute(
            select(func.count(Report.id))
            .where(Report.tenant_client_id == tenant_id)
        )
        return result.scalar()

    async def count_reports_by_analysis(self, analysis_id: UUID) -> int:
        """Count total reports for an analysis"""
        
        result = await self.session.execute(
            select(func.count(Report.id))
            .where(Report.analysis_id == analysis_id)
        )
        return result.scalar()

    async def get_reports_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[UUID] = None,
        report_type: Optional[str] = None
    ) -> List[Report]:
        """Get reports within a date range"""
        
        query = select(Report).where(
            and_(
                Report.created_at >= start_date,
                Report.created_at <= end_date
            )
        ).order_by(Report.created_at.desc())
        
        if tenant_id:
            query = query.where(Report.tenant_client_id == tenant_id)
        
        if report_type:
            query = query.where(Report.report_type == report_type.upper())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_expired_reports(self, batch_size: int = 100) -> int:
        """Delete reports that have expired and return count"""
        
        now = datetime.utcnow()
        
        # Get expired reports
        result = await self.session.execute(
            select(Report)
            .where(
                and_(
                    Report.expires_at.is_not(None),
                    Report.expires_at <= now
                )
            )
            .limit(batch_size)
        )
        expired_reports = list(result.scalars().all())
        
        deleted_count = 0
        for report in expired_reports:
            try:
                await self.session.delete(report)
                deleted_count += 1
            except Exception as e:
                # Log error but continue with other reports
                print(f"Error deleting report {report.id}: {e}")
        
        if deleted_count > 0:
            await self.session.commit()
        
        return deleted_count