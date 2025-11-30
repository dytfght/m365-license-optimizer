"""
Example usage of analytics models and services
"""
import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.core.database import get_db_session
from src.models.analytics import MetricType, SnapshotType
from src.schemas.analytics import (
    AnalyticsSnapshotCreate,
)
from src.services.analytics_service import AnalyticsService


async def create_sample_metrics(analytics_service: AnalyticsService, tenant_id: UUID):
    """Create sample analytics metrics"""
    print("Creating sample analytics metrics...")

    # License optimization metrics
    period_start = datetime.utcnow() - timedelta(days=30)
    period_end = datetime.utcnow()

    metrics = await analytics_service.create_license_optimization_metrics(
        tenant_client_id=tenant_id,
        period_start=period_start,
        period_end=period_end,
        license_utilization=75.5,
        total_cost=15000.00,
        potential_savings=2500.00,
        efficiency_score=7.8,
    )

    for metric in metrics:
        print(
            f"✅ Created metric: {metric.metric_name} = {metric.value} {metric.unit or ''}"
        )

    # User activity metrics
    user_metrics = await analytics_service.create_user_activity_metrics(
        tenant_client_id=tenant_id,
        period_start=period_start,
        period_end=period_end,
        active_users=850,
        inactive_users=150,
        disabled_users=25,
        guest_users=50,
    )

    for metric in user_metrics:
        print(
            f"✅ Created user metric: {metric.metric_name} = {metric.value} {metric.unit or ''}"
        )

    return metrics + user_metrics


async def create_sample_snapshots(analytics_service: AnalyticsService, tenant_id: UUID):
    """Create sample analytics snapshots"""
    print("\nCreating sample analytics snapshots...")

    # License inventory snapshot
    license_data = {
        "total_licenses": 1000,
        "assigned_licenses": 750,
        "available_licenses": 250,
        "license_types": {
            "E3": {"total": 500, "assigned": 400, "cost": 20000},
            "E5": {"total": 300, "assigned": 250, "cost": 15000},
            "F3": {"total": 200, "assigned": 100, "cost": 5000},
        },
        "optimization_opportunities": [
            {
                "user_id": "user123",
                "current_license": "E5",
                "recommended_license": "E3",
                "savings": 15.00,
            },
            {
                "user_id": "user456",
                "current_license": "E3",
                "recommended_license": "F3",
                "savings": 8.00,
            },
        ],
    }

    license_snapshot = AnalyticsSnapshotCreate(
        tenant_client_id=tenant_id,
        snapshot_type=SnapshotType.LICENSE_INVENTORY,
        snapshot_date=datetime.utcnow(),
        snapshot_data=license_data,
        snapshot_metadata={"source": "automated_analysis", "version": "1.0"},
    )

    created_license_snapshot = await analytics_service.create_snapshot(license_snapshot)
    print(f"✅ Created license inventory snapshot: {created_license_snapshot.id}")

    # User inventory snapshot
    user_data = {
        "total_users": 1075,
        "active_users": 850,
        "inactive_users": 150,
        "disabled_users": 25,
        "guest_users": 50,
        "department_breakdown": {
            "IT": {"total": 150, "active": 140, "inactive": 10},
            "Sales": {"total": 200, "active": 180, "inactive": 20},
            "Marketing": {"total": 100, "active": 85, "inactive": 15},
        },
        "last_activity_summary": {
            "last_7_days": 800,
            "last_30_days": 950,
            "last_90_days": 1050,
        },
    }

    user_snapshot = AnalyticsSnapshotCreate(
        tenant_client_id=tenant_id,
        snapshot_type=SnapshotType.USER_INVENTORY,
        snapshot_date=datetime.utcnow(),
        snapshot_data=user_data,
        snapshot_metadata={
            "source": "graph_api",
            "sync_date": datetime.utcnow().isoformat(),
        },
    )

    created_user_snapshot = await analytics_service.create_snapshot(user_snapshot)
    print(f"✅ Created user inventory snapshot: {created_user_snapshot.id}")

    # Service usage snapshot
    usage_data = {
        "exchange": {
            "active_users": 750,
            "total_emails_sent": 50000,
            "total_emails_received": 80000,
        },
        "sharepoint": {
            "active_users": 600,
            "total_files": 25000,
            "total_storage_gb": 500,
        },
        "teams": {"active_users": 700, "total_meetings": 1200, "total_messages": 45000},
        "onedrive": {
            "active_users": 650,
            "total_files": 15000,
            "total_storage_gb": 200,
        },
        "office_web": {
            "active_users": 500,
            "word_sessions": 3000,
            "excel_sessions": 2500,
            "powerpoint_sessions": 1500,
        },
    }

    usage_snapshot = AnalyticsSnapshotCreate(
        tenant_client_id=tenant_id,
        snapshot_type=SnapshotType.SERVICE_USAGE,
        snapshot_date=datetime.utcnow(),
        snapshot_data=usage_data,
        snapshot_metadata={"source": "usage_analytics", "period": "D30"},
    )

    created_usage_snapshot = await analytics_service.create_snapshot(usage_snapshot)
    print(f"✅ Created service usage snapshot: {created_usage_snapshot.id}")

    return [created_license_snapshot, created_user_snapshot, created_usage_snapshot]


async def demonstrate_analytics_queries(
    analytics_service: AnalyticsService, tenant_id: UUID
):
    """Demonstrate various analytics queries"""
    print("\nDemonstrating analytics queries...")

    # Get analytics summary
    summary = await analytics_service.get_tenant_analytics_summary(tenant_id)
    print("📊 Analytics Summary:")
    print(f"  - Total metrics: {summary.total_metrics}")
    print(f"  - Total snapshots: {summary.total_snapshots}")
    print(f"  - Available metric types: {len(summary.metric_types)}")
    print(f"  - Available snapshot types: {len(summary.snapshot_types)}")

    # Get dashboard KPIs
    kpis = await analytics_service.get_dashboard_kpis(tenant_id, period_days=30)
    print(f"\n📈 Dashboard KPIs ({len(kpis.kpis)} metrics):")
    for kpi in kpis.kpis[:5]:  # Show first 5 KPIs
        trend_info = f" ({kpi.trend} {kpi.change_percentage:.1f}%)" if kpi.trend else ""
        print(f"  - {kpi.metric_name}: {kpi.value} {kpi.unit or ''}{trend_info}")

    # Get metrics by type
    license_metrics = await analytics_service.get_metrics_by_tenant(
        tenant_id, metric_type=MetricType.LICENSE_UTILIZATION
    )
    print(f"\n📋 License Utilization Metrics: {len(license_metrics)} found")

    # Get snapshots by type
    inventory_snapshots = await analytics_service.get_snapshots_by_tenant(
        tenant_id, snapshot_type=SnapshotType.LICENSE_INVENTORY
    )
    print(f"📋 License Inventory Snapshots: {len(inventory_snapshots)} found")

    return summary, kpis


async def demonstrate_filtering(analytics_service: AnalyticsService, tenant_id: UUID):
    """Demonstrate filtering capabilities"""
    print("\nDemonstrating filtering capabilities...")

    from src.schemas.analytics import AnalyticsMetricFilter, AnalyticsSnapshotFilter

    # Filter metrics
    metric_filter = AnalyticsMetricFilter(
        tenant_client_id=tenant_id,
        metric_type=MetricType.LICENSE_COST,
        period_start=datetime.utcnow() - timedelta(days=60),
    )

    filtered_metrics = await analytics_service.filter_metrics(metric_filter)
    print(f"🔍 Filtered metrics: {len(filtered_metrics)} found")

    # Filter snapshots
    snapshot_filter = AnalyticsSnapshotFilter(
        tenant_client_id=tenant_id,
        snapshot_type=SnapshotType.USER_INVENTORY,
        snapshot_date=datetime.utcnow() - timedelta(days=7),
    )

    filtered_snapshots = await analytics_service.filter_snapshots(snapshot_filter)
    print(f"🔍 Filtered snapshots: {len(filtered_snapshots)} found")

    return filtered_metrics, filtered_snapshots


async def main():
    """Main example function"""
    print("🚀 Starting Analytics Example")
    print("=" * 50)

    # Use a sample tenant ID
    sample_tenant_id = uuid4()

    async with get_db_session() as session:
        analytics_service = AnalyticsService(session)

        try:
            # Create sample data
            metrics = await create_sample_metrics(analytics_service, sample_tenant_id)
            snapshots = await create_sample_snapshots(
                analytics_service, sample_tenant_id
            )

            # Demonstrate queries
            summary, kpis = await demonstrate_analytics_queries(
                analytics_service, sample_tenant_id
            )

            # Demonstrate filtering
            filtered_metrics, filtered_snapshots = await demonstrate_filtering(
                analytics_service, sample_tenant_id
            )

            print("\n" + "=" * 50)
            print("✅ Analytics example completed successfully!")
            print(f"✅ Created {len(metrics)} metrics")
            print(f"✅ Created {len(snapshots)} snapshots")
            print("✅ Generated analytics summary and KPIs")
            print("✅ Demonstrated filtering capabilities")

        except Exception as e:
            print(f"❌ Error during analytics example: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
