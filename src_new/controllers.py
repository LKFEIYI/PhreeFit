"""Shared GUI controllers and explicit fitted-parameter state."""

from dataclasses import dataclass
import time

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QMessageBox


@dataclass(frozen=True)
class FitParameter:
    """Represent one fixed value or one bounded optimization variable."""

    initial: float
    lower: float
    upper: float
    fixed: bool = False

    @classmethod
    def from_text(cls, initial, lower, upper, fixed=False):
        return cls(float(initial), float(lower), float(upper), bool(fixed))

    @property
    def in_bounds(self):
        return self.fixed or (self.lower <= self.upper and self.lower <= self.initial <= self.upper)

    @property
    def bounds_ordered(self):
        return self.lower <= self.upper

    @property
    def calculation_value(self):
        return self.initial if self.fixed else (self.lower, self.upper)


class OptimizationController(QObject):
    """Own worker lifecycle, cancellation, status timing, and GUI lock state."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.started_at = None
        self.outcome = None
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_status)

    def busy(self):
        return self.window.work is not None or self.window.work2 is not None

    def active_worker(self):
        return self.window.work if self.window.work is not None else self.window.work2

    def set_controls(self, running=False, mode=None):
        window = self.window
        window.pushButton_opt.setEnabled(not running)
        window.pushButton_opt_2.setEnabled(not running)
        window.comboBox_mdl.setEnabled(not running)
        window.comboBox_mdl_2.setEnabled(not running)
        window.checkBox.setEnabled(not running)
        window.radioButton_mode_adsorption.setEnabled(not running)
        window.radioButton_mode_titration.setEnabled(not running)
        window.pushButton_stp.setEnabled(running and mode == "titration")
        window.pushButton_stp_2.setEnabled(running and mode == "advanced")

    def start(self, worker, mode):
        if self.busy():
            QMessageBox.information(
                self.window,
                "Optimization running",
                "Please stop or wait for the current optimization before starting another one.",
            )
            return False

        if mode == "titration":
            self.window.work = worker
            worker.signals.connect(self.window.display_results)
        else:
            self.window.work2 = worker
            worker.signals.connect(self.window.display_results2)

        worker.finished.connect(self._worker_finished)
        self.set_controls(True, mode)
        self.started_at = time.monotonic()
        self.outcome = None
        self.timer.start()
        self.update_status()
        worker.start()
        return True

    def set_outcome(self, outcome):
        self.outcome = outcome

    def _worker_finished(self):
        worker = self.sender()
        elapsed = 0.0 if self.started_at is None else time.monotonic() - self.started_at
        worker_message = getattr(worker, "msg", {})
        if worker_message.get("cancelled", False):
            outcome = "Cancelled"
        elif worker_message.get("successful") is True:
            outcome = "Completed"
        elif worker_message.get("successful") is False:
            outcome = "Failed"
        else:
            outcome = self.outcome or "Finished"

        task_name = getattr(worker, "task_name", "") or "(unnamed)"
        self.timer.stop()
        self.window.activity_status_label.setText(
            f"{outcome} | Task: {task_name} | Elapsed: {self.format_elapsed(elapsed)}"
        )
        self.started_at = None
        if worker is self.window.work:
            self.window.work = None
        if worker is self.window.work2:
            self.window.work2 = None
        if not self.busy():
            self.set_controls(False)
        worker.deleteLater()

    @staticmethod
    def format_elapsed(seconds):
        total_seconds = max(0, int(seconds))
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def update_status(self):
        worker = self.active_worker()
        if worker is None or self.started_at is None:
            return
        elapsed = time.monotonic() - self.started_at
        state = "Stopping" if worker.stop_requested() else "Optimizing"
        task_name = getattr(worker, "task_name", "") or "(unnamed)"
        method = getattr(worker, "method", self.window.method_selected)
        processes = getattr(worker, "processes", 1)
        self.window.activity_status_label.setText(
            f"{state} | Task: {task_name} | {method} | Processes: {processes} | "
            f"Elapsed: {self.format_elapsed(elapsed)}"
        )

    def request_stop(self, mode):
        worker = self.window.work if mode == "titration" else self.window.work2
        if worker is None or not worker.isRunning():
            return False
        worker.request_stop()
        if mode == "titration":
            self.window.pushButton_stp.setEnabled(False)
        else:
            self.window.pushButton_stp_2.setEnabled(False)
        self.update_status()
        return True

    def stop_all_and_wait(self, timeout_ms=5000):
        workers = [
            worker for worker in (self.window.work, self.window.work2)
            if worker is not None
        ]
        for worker in workers:
            if worker.isRunning():
                worker.request_stop()
        self.window.pushButton_stp.setEnabled(False)
        self.window.pushButton_stp_2.setEnabled(False)

        deadline = time.monotonic() + max(0, timeout_ms) / 1000
        for worker in workers:
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            if worker.isRunning() and not worker.wait(remaining_ms):
                return False
        return True
