"""
Chart Generator - Creates charts for reports (donut, bar charts)
"""
import io
from typing import Any, Dict, List

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")  # Use non-GUI backend

import structlog

logger = structlog.get_logger(__name__)


class ChartGenerator:
    """Generate various charts for reports using matplotlib/seaborn"""

    # Microsoft color palette
    MICROSOFT_COLORS = [
        "#0078D4",  # Blue
        "#00BCF2",  # Cyan
        "#8764B8",  # Purple
        "#FF8C00",  # Orange
        "#107C10",  # Green
        "#E3008C",  # Pink
        "#8E8E93",  # Gray
        "#FF6900",  # Dark Orange
        "#00B7C3",  # Teal
        "#F2C811",  # Yellow
    ]

    def __init__(self):
        # Set default style
        plt.style.use("default")
        # Set color palette

        # Configure matplotlib for better quality
        plt.rcParams["figure.dpi"] = 150
        plt.rcParams["savefig.dpi"] = 150
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Arial"]

    async def create_donut_chart(
        self,
        data: List[Dict[str, Any]],
        title: str = "License Distribution",
        size: tuple = (6, 4),
        dpi: int = 150,
    ) -> bytes:
        """Create a donut chart for license distribution"""

        logger.info("creating_donut_chart", title=title, data_points=len(data))

        if not data:
            logger.warning("no_data_for_donut_chart")
            return b""

        # Prepare data
        labels = []
        sizes = []
        colors = []

        for i, item in enumerate(data):
            label = item.get("license_name", f"License {i+1}")
            user_count = item.get("user_count", 0)
            percentage = item.get("percentage", 0)

            if user_count > 0:  # Only include non-zero items
                labels.append(f"{label}\n{percentage:.1f}%")
                sizes.append(user_count)
                colors.append(self.MICROSOFT_COLORS[i % len(self.MICROSOFT_COLORS)])

        if not sizes:
            logger.warning("no_valid_data_for_donut_chart")
            return b""

        # Create figure
        fig, ax = plt.subplots(figsize=size, dpi=dpi)

        # Create donut chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="",
            startangle=90,
            wedgeprops=dict(width=0.5),  # Donut effect
            textprops={"fontsize": 9, "fontweight": "bold", "color": "white"},
        )

        # Style the chart
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(8)

        # Title
        ax.set_title(
            title,
            fontsize=12,
            fontweight="bold",
            color=self.MICROSOFT_COLORS[0],
            pad=20,
        )

        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis("equal")

        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(
            img_buffer,
            format="PNG",
            bbox_inches="tight",
            dpi=dpi,
            facecolor="white",
            edgecolor="none",
        )
        img_buffer.seek(0)

        plt.close(fig)  # Close to free memory

        logger.info(
            "donut_chart_created_successfully", size_bytes=len(img_buffer.getvalue())
        )

        return img_buffer.getvalue()

    async def create_bar_chart(
        self,
        data: List[Dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str = "Bar Chart",
        x_label: str = "",
        y_label: str = "",
        horizontal: bool = False,
        size: tuple = (8, 4),
        dpi: int = 150,
    ) -> bytes:
        """Create a bar chart"""

        logger.info("creating_bar_chart", title=title, data_points=len(data))

        if not data:
            logger.warning("no_data_for_bar_chart")
            return b""

        # Create figure
        fig, ax = plt.subplots(figsize=size, dpi=dpi)

        # Prepare data
        x_values = [item.get(x_field, f"Item {i}") for i, item in enumerate(data)]
        y_values = [item.get(y_field, 0) for item in data]

        # Create bar chart
        if horizontal:
            bars = ax.barh(x_values, y_values, color=self.MICROSOFT_COLORS[0])
            ax.set_xlabel(y_label, fontsize=10, color=self.MICROSOFT_COLORS[0])
            ax.set_ylabel(x_label, fontsize=10, color=self.MICROSOFT_COLORS[0])
        else:
            bars = ax.bar(x_values, y_values, color=self.MICROSOFT_COLORS[0])
            ax.set_xlabel(x_label, fontsize=10, color=self.MICROSOFT_COLORS[0])
            ax.set_ylabel(y_label, fontsize=10, color=self.MICROSOFT_COLORS[0])

        # Style the bars
        for bar in bars:
            bar.set_edgecolor("none")
            bar.set_linewidth(0)

        # Add value labels on bars
        for i, (x, y) in enumerate(zip(x_values, y_values)):
            if horizontal:
                ax.text(
                    y + max(y_values) * 0.01,
                    i,
                    f"{y:,.0f}",
                    va="center",
                    fontsize=9,
                    color=self.MICROSOFT_COLORS[0],
                )
            else:
                ax.text(
                    i,
                    y + max(y_values) * 0.01,
                    f"{y:,.0f}",
                    ha="center",
                    fontsize=9,
                    color=self.MICROSOFT_COLORS[0],
                )

        # Title
        ax.set_title(
            title,
            fontsize=12,
            fontweight="bold",
            color=self.MICROSOFT_COLORS[0],
            pad=20,
        )

        # Style axes
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color(self.MICROSOFT_COLORS[0])
        ax.spines["left"].set_color(self.MICROSOFT_COLORS[0])

        # Grid
        ax.grid(True, axis="y", alpha=0.3, color=self.MICROSOFT_COLORS[0])
        ax.set_axisbelow(True)

        # Rotate x labels if needed
        if len(x_values) > 5 and not horizontal:
            plt.xticks(rotation=45, ha="right")

        # Tight layout
        plt.tight_layout()

        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(
            img_buffer,
            format="PNG",
            bbox_inches="tight",
            dpi=dpi,
            facecolor="white",
            edgecolor="none",
        )
        img_buffer.seek(0)

        plt.close(fig)  # Close to free memory

        logger.info(
            "bar_chart_created_successfully", size_bytes=len(img_buffer.getvalue())
        )

        return img_buffer.getvalue()

    async def create_savings_chart(
        self,
        departments_data: List[Dict[str, Any]],
        title: str = "Économies par département",
        size: tuple = (8, 4),
        dpi: int = 150,
    ) -> bytes:
        """Create a chart showing savings by department"""

        logger.info("creating_savings_chart", departments=len(departments_data))

        if not departments_data:
            logger.warning("no_department_data_for_chart")
            return b""

        # Sort by savings (descending)
        sorted_depts = sorted(
            departments_data, key=lambda x: x.get("annual_savings", 0), reverse=True
        )

        # Take top 10
        top_depts = sorted_depts[:10]

        # Prepare data
        dept_names = [dept.get("name", f"Dept {i}") for i, dept in enumerate(top_depts)]
        savings = [dept.get("annual_savings", 0) for dept in top_depts]

        # Create figure
        fig, ax = plt.subplots(figsize=size, dpi=dpi)

        # Create horizontal bar chart
        ax.barh(dept_names, savings, color=self.MICROSOFT_COLORS[0])

        # Add value labels
        for i, (dept, saving) in enumerate(zip(dept_names, savings)):
            ax.text(
                saving + max(savings) * 0.01,
                i,
                f"{saving:,.0f}€",
                va="center",
                fontsize=9,
                color=self.MICROSOFT_COLORS[0],
            )

        # Title and labels
        ax.set_title(
            title,
            fontsize=12,
            fontweight="bold",
            color=self.MICROSOFT_COLORS[0],
            pad=20,
        )
        ax.set_xlabel(
            "Économies annuelles (€)", fontsize=10, color=self.MICROSOFT_COLORS[0]
        )

        # Style
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color(self.MICROSOFT_COLORS[0])
        ax.spines["left"].set_color(self.MICROSOFT_COLORS[0])

        # Grid
        ax.grid(True, axis="x", alpha=0.3, color=self.MICROSOFT_COLORS[0])
        ax.set_axisbelow(True)

        # Tight layout
        plt.tight_layout()

        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(
            img_buffer,
            format="PNG",
            bbox_inches="tight",
            dpi=dpi,
            facecolor="white",
            edgecolor="none",
        )
        img_buffer.seek(0)

        plt.close(fig)  # Close to free memory

        logger.info(
            "savings_chart_created_successfully", size_bytes=len(img_buffer.getvalue())
        )

        return img_buffer.getvalue()

    async def create_usage_trend_chart(
        self,
        usage_data: List[Dict[str, Any]],
        services: List[str] = ["Exchange", "OneDrive", "SharePoint", "Teams", "Office"],
        title: str = "Évolution de l'usage par service",
        size: tuple = (10, 6),
        dpi: int = 150,
    ) -> bytes:
        """Create a line chart showing usage trends over time"""

        logger.info("creating_usage_trend_chart", services=len(services))

        if not usage_data:
            logger.warning("no_usage_data_for_trend_chart")
            return b""

        # Prepare data
        df = pd.DataFrame(usage_data)

        if df.empty:
            logger.warning("empty_dataframe_for_trend_chart")
            return b""

        # Create figure
        fig, ax = plt.subplots(figsize=size, dpi=dpi)

        # Plot lines for each service
        for i, service in enumerate(services):
            if service in df.columns:
                ax.plot(
                    df.index,
                    df[service],
                    label=service,
                    color=self.MICROSOFT_COLORS[i % len(self.MICROSOFT_COLORS)],
                    linewidth=2,
                    marker="o",
                    markersize=4,
                )

        # Title and labels
        ax.set_title(
            title,
            fontsize=14,
            fontweight="bold",
            color=self.MICROSOFT_COLORS[0],
            pad=20,
        )
        ax.set_xlabel("Date", fontsize=12, color=self.MICROSOFT_COLORS[0])
        ax.set_ylabel("Usage Score", fontsize=12, color=self.MICROSOFT_COLORS[0])

        # Legend
        ax.legend(loc="upper right", frameon=False, fontsize=10)

        # Grid
        ax.grid(True, alpha=0.3, color=self.MICROSOFT_COLORS[0])
        ax.set_axisbelow(True)

        # Style axes
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color(self.MICROSOFT_COLORS[0])
        ax.spines["left"].set_color(self.MICROSOFT_COLORS[0])

        # Tight layout
        plt.tight_layout()

        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(
            img_buffer,
            format="PNG",
            bbox_inches="tight",
            dpi=dpi,
            facecolor="white",
            edgecolor="none",
        )
        img_buffer.seek(0)

        plt.close(fig)  # Close to free memory

        logger.info(
            "usage_trend_chart_created_successfully",
            size_bytes=len(img_buffer.getvalue()),
        )

        return img_buffer.getvalue()

    async def create_kpi_dashboard(
        self,
        kpis: Dict[str, Any],
        title: str = "Tableau de bord KPI",
        size: tuple = (12, 8),
        dpi: int = 150,
    ) -> bytes:
        """Create a KPI dashboard with multiple metrics"""

        logger.info("creating_kpi_dashboard", title=title)

        # Create figure with subplots
        fig = plt.figure(figsize=size, dpi=dpi)

        # KPI 1: Savings summary (large text)
        ax1 = fig.add_subplot(2, 3, 1)
        ax1.text(
            0.5,
            0.7,
            f"{kpis.get('monthly_savings', 0):,.0f}",
            fontsize=36,
            fontweight="bold",
            color=self.MICROSOFT_COLORS[0],
            ha="center",
            va="center",
        )
        ax1.text(
            0.5,
            0.3,
            "Économie mensuelle (€)",
            fontsize=12,
            color=self.MICROSOFT_COLORS[2],
            ha="center",
            va="center",
        )
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis("off")

        # KPI 2: User distribution (donut)
        ax2 = fig.add_subplot(2, 3, 2)
        license_dist = kpis.get("license_distribution", [])
        if license_dist:
            sizes = [item.get("user_count", 0) for item in license_dist]
            labels = [item.get("license_name", "") for item in license_dist]
            colors = self.MICROSOFT_COLORS[: len(sizes)]

            wedges, texts, autotexts = ax2.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=90,
                wedgeprops=dict(width=0.5),
            )  # type: ignore[misc]
            ax2.set_title(
                "Répartition licences", fontsize=10, color=self.MICROSOFT_COLORS[0]
            )
        ax2.axis("equal")

        # KPI 3: Department savings (bar)
        ax3 = fig.add_subplot(2, 3, 3)
        dept_data = kpis.get("departments", [])
        if dept_data:
            depts = [dept.get("name", "") for dept in dept_data[:5]]
            savings = [dept.get("annual_savings", 0) for dept in dept_data[:5]]

            ax3.barh(depts, savings, color=self.MICROSOFT_COLORS[0])
            ax3.set_title(
                "Économies par département", fontsize=10, color=self.MICROSOFT_COLORS[0]
            )
            ax3.grid(True, axis="x", alpha=0.3)

        # KPI 4: Activity levels (gauge)
        ax4 = fig.add_subplot(2, 3, 4)
        activity_data = kpis.get("activity_levels", {})
        if activity_data:
            services = list(activity_data.keys())
            levels = list(activity_data.values())

            # Create simple gauge-like visualization
            for i, (service, level) in enumerate(zip(services, levels)):
                color = (
                    self.MICROSOFT_COLORS[4]
                    if level > 0.7
                    else self.MICROSOFT_COLORS[1]
                    if level > 0.3
                    else self.MICROSOFT_COLORS[6]
                )
                ax4.barh(i, level, color=color, height=0.8)

            ax4.set_yticks(range(len(services)))
            ax4.set_yticklabels(services)
            ax4.set_title(
                "Niveaux d'activité", fontsize=10, color=self.MICROSOFT_COLORS[0]
            )
            ax4.set_xlim(0, 1)

        # KPI 5: Savings trend (line)
        ax5 = fig.add_subplot(2, 3, 5)
        trend_data = kpis.get("savings_trend", [])
        if trend_data:
            dates = [item.get("date") for item in trend_data]
            savings = [item.get("savings", 0) for item in trend_data]

            ax5.plot(
                dates, savings, color=self.MICROSOFT_COLORS[0], linewidth=2, marker="o"
            )
            ax5.set_title(
                "Évolution des économies", fontsize=10, color=self.MICROSOFT_COLORS[0]
            )
            ax5.grid(True, alpha=0.3)

        # KPI 6: Risk assessment (text)
        ax6 = fig.add_subplot(2, 3, 6)
        risk_level = kpis.get("risk_level", "Moyen")
        risk_color = {
            "Faible": self.MICROSOFT_COLORS[4],
            "Moyen": self.MICROSOFT_COLORS[1],
            "Élevé": self.MICROSOFT_COLORS[5],
        }

        ax6.text(
            0.5,
            0.7,
            risk_level,
            fontsize=24,
            fontweight="bold",
            color=risk_color.get(risk_level, self.MICROSOFT_COLORS[0]),
            ha="center",
            va="center",
        )
        ax6.text(
            0.5,
            0.3,
            "Niveau de risque",
            fontsize=10,
            color=self.MICROSOFT_COLORS[2],
            ha="center",
            va="center",
        )
        ax6.set_xlim(0, 1)
        ax6.set_ylim(0, 1)
        ax6.axis("off")

        # Global title
        fig.suptitle(
            title, fontsize=16, fontweight="bold", color=self.MICROSOFT_COLORS[0]
        )

        # Tight layout
        plt.tight_layout()

        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(
            img_buffer,
            format="PNG",
            bbox_inches="tight",
            dpi=dpi,
            facecolor="white",
            edgecolor="none",
        )
        img_buffer.seek(0)

        plt.close(fig)  # Close to free memory

        logger.info(
            "kpi_dashboard_created_successfully", size_bytes=len(img_buffer.getvalue())
        )

        return img_buffer.getvalue()

    def get_chart_colors(self, count: int) -> List[str]:
        """Get a list of Microsoft colors for charts"""
        return (
            self.MICROSOFT_COLORS[:count]
            if count <= len(self.MICROSOFT_COLORS)
            else self.MICROSOFT_COLORS * (count // len(self.MICROSOFT_COLORS))
            + self.MICROSOFT_COLORS[: count % len(self.MICROSOFT_COLORS)]
        )
