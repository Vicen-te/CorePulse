"""
Icon creation for ThermalCore.

Provides the app icon (from SVG or programmatic fallback)
and tree branch arrow icons for expand/collapse indicators.
"""

# Standard library
import os
import tempfile

# Third-party
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPolygonF
from PySide6.QtCore import Qt, QPointF

# Local
import utils.config as cfg


def create_app_icon() -> QIcon:
    """Load the app icon from the SVG asset, with a programmatic fallback."""
    icon_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "assets", "icons", "thermalcore.svg",
    )
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    # Fallback: simple programmatic icon
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#2b2b2b"))
    painter.drawRoundedRect(4, 4, 56, 56, 12, 12)
    painter.setBrush(QColor("#e95420"))
    painter.drawEllipse(22, 30, 20, 20)
    painter.drawRoundedRect(27, 12, 10, 30, 5, 5)
    painter.end()
    return QIcon(pixmap)


def create_branch_icons() -> tuple[str, str]:
    """
    Create triangle arrow icons for tree branches.

    Returns:
        Tuple of (closed_arrow_path, open_arrow_path) as temp file paths.
    """
    arrow_size = 12
    color = QColor(cfg.COLOR_TEXT_SECONDARY)

    # Right-pointing triangle (collapsed)
    closed_pix = QPixmap(arrow_size, arrow_size)
    closed_pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(closed_pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(color)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([
        QPointF(3, 1), QPointF(10, 6), QPointF(3, 11),
    ]))
    p.end()

    # Down-pointing triangle (expanded)
    open_pix = QPixmap(arrow_size, arrow_size)
    open_pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(open_pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(color)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([
        QPointF(1, 3), QPointF(11, 3), QPointF(6, 10),
    ]))
    p.end()

    tmp_dir = tempfile.mkdtemp(prefix="thermalcore_")
    closed_path = os.path.join(tmp_dir, "arrow_closed.png")
    open_path = os.path.join(tmp_dir, "arrow_open.png")
    closed_pix.save(closed_path)
    open_pix.save(open_path)
    return closed_path, open_path
