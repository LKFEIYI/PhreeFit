"""Post-processing views for comparing completed optimization tasks."""

from dataclasses import dataclass
from datetime import datetime
import os
import re

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


_CTIME_PATTERN = re.compile(
    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) "
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
    r"\d{1,2} \d{2}:\d{2}:\d{2} \d{4}$"
)


@dataclass(frozen=True)
class OptimizationRecord:
    timestamp: datetime
    task: str
    r2: float
    adjusted_r2: float
    bic: float
    rmse: float
    variance_y: float
    log_text: str

    @property
    def display_time(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")


def _parse_log_block(timestamp, lines):
    task = None
    metrics = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("Task:"):
            task = stripped.partition(":")[2].strip() or "(unnamed)"
        if (stripped.startswith("R2") and "adj. R2" in stripped
                and "BIC" in stripped and "RMSE" in stripped and "V(Y)" in stripped):
            for value_line in lines[index + 1:]:
                values = value_line.strip().split()
                if not values:
                    continue
                try:
                    metrics = tuple(float(value) for value in values[:5])
                except (TypeError, ValueError):
                    metrics = None
                break

    if task is None or metrics is None or len(metrics) != 5:
        return None
    log_text = timestamp.strftime("%a %b %d %H:%M:%S %Y")
    if lines:
        log_text += "\n" + "\n".join(lines).strip("\n")
    return OptimizationRecord(timestamp, task, *metrics, log_text)


def read_optimization_history(log_path):
    """Read successful optimization records from a PhreeFit log."""
    if not os.path.isfile(log_path):
        return []

    records = []
    current_time = None
    current_lines = []
    with open(log_path, "r", encoding="utf-8", errors="replace") as log_file:
        for raw_line in log_file:
            line = raw_line.rstrip("\n")
            collapsed = " ".join(line.strip().split())
            if _CTIME_PATTERN.match(collapsed):
                if current_time is not None:
                    record = _parse_log_block(current_time, current_lines)
                    if record is not None:
                        records.append(record)
                current_time = datetime.strptime(collapsed, "%a %b %d %H:%M:%S %Y")
                current_lines = []
            elif current_time is not None:
                current_lines.append(line)

    if current_time is not None:
        record = _parse_log_block(current_time, current_lines)
        if record is not None:
            records.append(record)
    return sorted(records, key=lambda record: record.timestamp, reverse=True)


class BicComparisonDialog(QDialog):
    def __init__(self, records, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BIC comparison")
        self.resize(900, 560)

        layout = QVBoxLayout(self)
        axis = pg.DateAxisItem(orientation="bottom")
        plot = pg.PlotWidget(axisItems={"bottom": axis})
        plot.setBackground("w")
        plot.showGrid(x=True, y=True, alpha=0.25)
        plot.setLabel("bottom", "Time")
        plot.setLabel("left", "BIC")
        layout.addWidget(plot)

        chronological = sorted(records, key=lambda record: record.timestamp)
        x_values = [record.timestamp.timestamp() for record in chronological]
        y_values = [record.bic for record in chronological]
        plot.plot(
            x_values,
            y_values,
            pen=pg.mkPen("#0072B2", width=2),
        )
        scatter = pg.ScatterPlotItem(
            x=x_values,
            y=y_values,
            data=chronological,
            symbol="o",
            size=8,
            pen=pg.mkPen("#0072B2", width=1.5),
            brush=pg.mkBrush("w"),
            hoverable=True,
            hoverSize=11,
            hoverPen=pg.mkPen("#D55E00", width=2),
            hoverBrush=pg.mkBrush("#FFF3E0"),
            tip=lambda x, y, data: (
                f"Task: {data.task}\n"
                f"Time: {data.display_time}"
            ),
        )
        plot.addItem(scatter)
        self.scatter = scatter

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class LogDetailsDialog(QDialog):
    def __init__(self, records, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selected log records")
        self.resize(900, 650)

        layout = QVBoxLayout(self)
        log_view = QTextEdit()
        log_view.setReadOnly(True)
        log_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        separator = "\n\n" + "=" * 80 + "\n\n"
        log_view.setPlainText(separator.join(record.log_text for record in records))
        layout.addWidget(log_view)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class HistoryComparisonDialog(QDialog):
    def __init__(self, records, log_path, parent=None):
        super().__init__(parent)
        self.records = records
        self.checkboxes = []
        self.setWindowTitle("Optimization history")
        self.resize(1080, 620)

        layout = QVBoxLayout(self)
        path_label = QLabel("Log: " + log_path)
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(path_label)

        self.table = QTableWidget(len(records), 8)
        self.table.setHorizontalHeaderLabels(
            ("Select", "Time", "Task", "R2", "adj. R2", "BIC", "RMSE", "V(Y)")
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        for row, record in enumerate(records):
            checkbox = QCheckBox()
            checkbox_container = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_container)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.addWidget(checkbox)
            self.table.setCellWidget(row, 0, checkbox_container)
            self.checkboxes.append(checkbox)

            values = (
                record.display_time,
                record.task,
                f"{record.r2:.5f}",
                f"{record.adjusted_r2:.5f}",
                f"{record.bic:.5f}",
                f"{record.rmse:.3e}",
                f"{record.variance_y:.3e}",
            )
            for column, value in enumerate(values, start=1):
                self.table.setItem(row, column, QTableWidgetItem(value))
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        show_button = QPushButton("Show")
        compare_button = QPushButton("Compare")
        close_button = QPushButton("Close")
        show_button.clicked.connect(self.show_selected)
        compare_button.clicked.connect(self.compare_selected)
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(show_button)
        button_layout.addWidget(compare_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def selected_records(self):
        return [
            record
            for record, checkbox in zip(self.records, self.checkboxes)
            if checkbox.isChecked()
        ]

    def show_selected(self):
        selected = self.selected_records()
        if not selected:
            QMessageBox.information(self, "Show", "Please select at least one record.")
            return
        details = LogDetailsDialog(selected, self)
        details.exec()

    def compare_selected(self):
        selected = self.selected_records()
        if not selected:
            QMessageBox.information(self, "Compare", "Please select at least one record.")
            return
        comparison = BicComparisonDialog(selected, self)
        comparison.exec()
