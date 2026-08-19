"""Post-processing views for comparing completed optimization tasks."""

from dataclasses import dataclass
from datetime import datetime
from collections import Counter
import os
import re
import shutil
import tempfile
import time

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
    QLineEdit,
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


def _read_timed_blocks(path):
    if not os.path.isfile(path):
        return [], []
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as source:
        lines = source.readlines()

    prefix = []
    blocks = []
    current_time = None
    current_lines = []
    for line in lines:
        collapsed = " ".join(line.strip().split())
        if _CTIME_PATTERN.match(collapsed):
            if current_time is not None:
                blocks.append((current_time, current_lines))
            current_time = datetime.strptime(collapsed, "%a %b %d %H:%M:%S %Y")
            current_lines = [line]
        elif current_time is None:
            prefix.append(line)
        else:
            current_lines.append(line)
    if current_time is not None:
        blocks.append((current_time, current_lines))
    return prefix, blocks


def _write_with_backup(path, prefix, blocks, backup_suffix):
    if not os.path.isfile(path):
        return None
    backup_path = path + ".bak-" + backup_suffix
    counter = 1
    while os.path.exists(backup_path):
        backup_path = path + ".bak-" + backup_suffix + f"-{counter}"
        counter += 1
    shutil.copy2(path, backup_path)

    file_directory = os.path.dirname(os.path.abspath(path))
    descriptor, temporary_path = tempfile.mkstemp(prefix=".phreefit-history-", dir=file_directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as destination:
            destination.writelines(prefix)
            for _timestamp, block_lines in blocks:
                destination.writelines(block_lines)
        os.chmod(temporary_path, os.stat(path).st_mode)
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)
    return backup_path


def delete_history_records(log_path, results_path, selected_records):
    """Remove selected log blocks and their nearest result blocks, with backups."""
    selected_signatures = Counter(
        (record.timestamp, record.task) for record in selected_records
    )
    log_prefix, log_blocks = _read_timed_blocks(log_path)
    retained_log_blocks = []
    deleted_log_count = 0
    for timestamp, block_lines in log_blocks:
        content_lines = [line.rstrip("\r\n") for line in block_lines[1:]]
        record = _parse_log_block(timestamp, content_lines)
        signature = (timestamp, record.task) if record is not None else None
        if signature is not None and selected_signatures[signature] > 0:
            selected_signatures[signature] -= 1
            deleted_log_count += 1
        else:
            retained_log_blocks.append((timestamp, block_lines))

    results_prefix, result_blocks = _read_timed_blocks(results_path)
    available_indexes = set(range(len(result_blocks)))
    matched_result_indexes = set()
    for record in selected_records:
        candidates = [
            (abs((result_blocks[index][0] - record.timestamp).total_seconds()), index)
            for index in available_indexes
        ]
        if not candidates:
            continue
        difference, result_index = min(candidates)
        if difference <= 3:
            matched_result_indexes.add(result_index)
            available_indexes.remove(result_index)
    retained_result_blocks = [
        block for index, block in enumerate(result_blocks)
        if index not in matched_result_indexes
    ]

    if deleted_log_count == 0:
        return 0, 0, []
    backup_suffix = time.strftime("%Y%m%d-%H%M%S")
    backups = [
        _write_with_backup(log_path, log_prefix, retained_log_blocks, backup_suffix)
    ]
    if matched_result_indexes and os.path.isfile(results_path):
        backups.append(
            _write_with_backup(results_path, results_prefix, retained_result_blocks, backup_suffix)
        )
    return deleted_log_count, len(matched_result_indexes), [path for path in backups if path]


class MetricsComparisonDialog(QDialog):
    def __init__(self, records, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model comparison")
        self.resize(900, 560)

        layout = QVBoxLayout(self)
        axis = pg.DateAxisItem(orientation="bottom")
        plot = pg.PlotWidget(axisItems={"bottom": axis})
        plot.setBackground("w")
        plot.showGrid(x=True, y=True, alpha=0.25)
        plot.setLabel("bottom", "Time")
        plot.setLabel("left", "adj. R²", color="#0072B2")
        layout.addWidget(plot)

        plot_item = plot.getPlotItem()
        legend = plot_item.addLegend()
        plot_item.getAxis("left").setPen(pg.mkPen("#0072B2"))
        plot_item.getAxis("left").setTextPen(pg.mkPen("#0072B2"))
        bic_view = pg.ViewBox()
        plot_item.showAxis("right")
        plot_item.scene().addItem(bic_view)
        plot_item.getAxis("right").linkToView(bic_view)
        plot_item.getAxis("right").setLabel("BIC", color="#D55E00")
        plot_item.getAxis("right").setPen(pg.mkPen("#D55E00"))
        plot_item.getAxis("right").setTextPen(pg.mkPen("#D55E00"))
        bic_view.setXLink(plot_item.vb)

        def sync_bic_view():
            bic_view.setGeometry(plot_item.vb.sceneBoundingRect())
            bic_view.linkedViewChanged(plot_item.vb, bic_view.XAxis)

        plot_item.vb.sigResized.connect(sync_bic_view)
        sync_bic_view()

        chronological = sorted(records, key=lambda record: record.timestamp)
        x_values = [record.timestamp.timestamp() for record in chronological]
        adjusted_r2_values = [record.adjusted_r2 for record in chronological]
        bic_values = [record.bic for record in chronological]
        adjusted_curve = plot.plot(
            x_values,
            adjusted_r2_values,
            pen=pg.mkPen("#0072B2", width=2),
            name="adj. R²",
        )
        bic_curve = pg.PlotDataItem(
            x_values,
            bic_values,
            pen=pg.mkPen("#D55E00", width=2, style=Qt.PenStyle.DashLine),
        )
        bic_view.addItem(bic_curve)
        legend.addItem(bic_curve, "BIC")

        point_tip = lambda x, y, data: (
            f"Task: {data.task}\n"
            f"Time: {data.display_time}\n"
            f"adj. R²: {data.adjusted_r2:.5f}\n"
            f"BIC: {data.bic:.5f}"
        )
        adjusted_scatter = pg.ScatterPlotItem(
            x=x_values,
            y=adjusted_r2_values,
            data=chronological,
            symbol="o",
            size=8,
            pen=pg.mkPen("#0072B2", width=1.5),
            brush=pg.mkBrush("w"),
            hoverable=True,
            hoverSize=11,
            hoverPen=pg.mkPen("#0072B2", width=2),
            hoverBrush=pg.mkBrush("#E3F2FD"),
            tip=point_tip,
        )
        plot.addItem(adjusted_scatter)
        bic_scatter = pg.ScatterPlotItem(
            x=x_values,
            y=bic_values,
            data=chronological,
            symbol="s",
            size=8,
            pen=pg.mkPen("#D55E00", width=1.5),
            brush=pg.mkBrush("w"),
            hoverable=True,
            hoverSize=11,
            hoverPen=pg.mkPen("#D55E00", width=2),
            hoverBrush=pg.mkBrush("#FFF3E0"),
            tip=point_tip,
        )
        bic_view.addItem(bic_scatter)

        best_adjusted = max(chronological, key=lambda record: record.adjusted_r2)
        adjusted_label = pg.TextItem(
            "Highest adj. R²\n" + best_adjusted.task,
            color="#0072B2",
            anchor=(0.5, 1.15),
        )
        adjusted_label.setPos(best_adjusted.timestamp.timestamp(), best_adjusted.adjusted_r2)
        plot.addItem(adjusted_label)

        best_bic = min(chronological, key=lambda record: record.bic)
        bic_label = pg.TextItem(
            "Lowest BIC\n" + best_bic.task,
            color="#D55E00",
            anchor=(0.5, -0.15),
        )
        bic_label.setPos(best_bic.timestamp.timestamp(), best_bic.bic)
        bic_view.addItem(bic_label)

        self.plot = plot
        self.bic_view = bic_view
        self.adjusted_curve = adjusted_curve
        self.bic_curve = bic_curve
        self.adjusted_scatter = adjusted_scatter
        self.bic_scatter = bic_scatter

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


class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, value):
        super().__init__(text)
        self.numeric_value = float(value)

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.numeric_value < other.numeric_value
        return super().__lt__(other)


class HistoryComparisonDialog(QDialog):
    def __init__(self, records, log_path, results_path, parent=None):
        super().__init__(parent)
        self.records = records
        self.log_path = log_path
        self.results_path = results_path
        self.checkboxes = []
        self.setWindowTitle("Optimization history")
        self.resize(1080, 620)

        layout = QVBoxLayout(self)
        path_label = QLabel("Log: " + log_path)
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(path_label)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search task:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Task name or time")
        select_all_button = QPushButton("Select all")
        clear_selection_button = QPushButton("Clear selection")
        self.selection_label = QLabel("Selected: 0")
        filter_layout.addWidget(self.search_edit, 1)
        filter_layout.addWidget(select_all_button)
        filter_layout.addWidget(clear_selection_button)
        filter_layout.addWidget(self.selection_label)
        layout.addLayout(filter_layout)

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
            checkbox.stateChanged.connect(self.update_selection_count)

            time_item = QTableWidgetItem(record.display_time)
            task_item = QTableWidgetItem(record.task)
            task_item.setData(Qt.ItemDataRole.UserRole, record)
            self.table.setItem(row, 1, time_item)
            self.table.setItem(row, 2, task_item)
            numeric_values = (
                (record.r2, f"{record.r2:.5f}"),
                (record.adjusted_r2, f"{record.adjusted_r2:.5f}"),
                (record.bic, f"{record.bic:.5f}"),
                (record.rmse, f"{record.rmse:.3e}"),
                (record.variance_y, f"{record.variance_y:.3e}"),
            )
            for column, (value, text) in enumerate(numeric_values, start=3):
                self.table.setItem(row, column, NumericTableWidgetItem(text, value))
        self.table.setSortingEnabled(True)
        self.table.sortItems(1, Qt.SortOrder.DescendingOrder)
        self.table.cellDoubleClicked.connect(self.show_record_at_row)
        self.search_edit.textChanged.connect(self.filter_records)
        select_all_button.clicked.connect(lambda: self.set_visible_selection(True))
        clear_selection_button.clicked.connect(self.clear_selection)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        show_button = QPushButton("Show")
        compare_button = QPushButton("Compare")
        delete_button = QPushButton("Delete")
        delete_button.setStyleSheet("color: #b71c1c;")
        close_button = QPushButton("Close")
        show_button.clicked.connect(self.show_selected)
        compare_button.clicked.connect(self.compare_selected)
        delete_button.clicked.connect(self.delete_selected)
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(show_button)
        button_layout.addWidget(compare_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def selected_records(self):
        selected = []
        for row in range(self.table.rowCount()):
            container = self.table.cellWidget(row, 0)
            checkbox = container.findChild(QCheckBox) if container is not None else None
            record = self.table.item(row, 2).data(Qt.ItemDataRole.UserRole)
            if checkbox is not None and checkbox.isChecked():
                selected.append(record)
        return selected

    def update_selection_count(self, _state=None):
        self.selection_label.setText(f"Selected: {len(self.selected_records())}")

    def set_visible_selection(self, checked):
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            container = self.table.cellWidget(row, 0)
            checkbox = container.findChild(QCheckBox) if container is not None else None
            if checkbox is not None:
                checkbox.setChecked(checked)
        self.update_selection_count()

    def clear_selection(self):
        for row in range(self.table.rowCount()):
            container = self.table.cellWidget(row, 0)
            checkbox = container.findChild(QCheckBox) if container is not None else None
            if checkbox is not None:
                checkbox.setChecked(False)
        self.update_selection_count()

    def filter_records(self, text):
        query = text.strip().casefold()
        for row in range(self.table.rowCount()):
            record = self.table.item(row, 2).data(Qt.ItemDataRole.UserRole)
            searchable = f"{record.task} {record.display_time}".casefold()
            self.table.setRowHidden(row, bool(query and query not in searchable))

    def show_record_at_row(self, row, _column):
        record = self.table.item(row, 2).data(Qt.ItemDataRole.UserRole)
        details = LogDetailsDialog([record], self)
        details.exec()

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
        comparison = MetricsComparisonDialog(selected, self)
        comparison.exec()

    def delete_selected(self):
        selected = self.selected_records()
        if not selected:
            QMessageBox.information(self, "Delete", "Please select at least one record.")
            return
        task_list = "\n".join(
            f"• {record.task} — {record.display_time}" for record in selected[:10]
        )
        if len(selected) > 10:
            task_list += f"\n• ... and {len(selected) - 10} more"
        answer = QMessageBox.question(
            self,
            "Delete history records",
            "Delete the selected records from the log and results files?\n\n"
            + task_list
            + "\n\nBackup files will be created before deletion.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            deleted_logs, deleted_results, backups = delete_history_records(
                self.log_path,
                self.results_path,
                selected,
            )
        except Exception as error:
            QMessageBox.warning(self, "Delete", "Unable to delete the records:\n" + str(error))
            return
        if deleted_logs == 0:
            QMessageBox.warning(self, "Delete", "The selected log records were not found.")
            return

        for row in reversed(range(self.table.rowCount())):
            container = self.table.cellWidget(row, 0)
            checkbox = container.findChild(QCheckBox) if container is not None else None
            if checkbox is not None and checkbox.isChecked():
                self.table.removeRow(row)
        self.records = read_optimization_history(self.log_path)
        self.update_selection_count()
        backup_text = "\n".join(backups) if backups else "No backup was required."
        QMessageBox.information(
            self,
            "Delete completed",
            f"Deleted log records: {deleted_logs}\n"
            f"Deleted result records: {deleted_results}\n\n"
            f"Backups:\n{backup_text}",
        )
