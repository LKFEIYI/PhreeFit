"""Main-window controller: signal wiring, UI state, and event handlers."""

import multiprocessing
import os
import time

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QInputDialog, QLineEdit, QMainWindow,
    QMessageBox, QRadioButton, QTextEdit,
)

from . import main_cal as mc
from .io_service import (
    ConfigFile,
    SETTINGS_FORMAT,
    SETTINGS_VERSION,
    deserialize_surface,
    json_value,
    load_settings_file,
    read_advanced_data,
    read_database,
    read_titration_data,
    save_settings_file,
    serialize_surface,
    write_log,
    write_results,
)
from .post_plot import HistoryComparisonDialog, read_optimization_history
from .table_model import TableModel
from .ui.main_window_ui import ResponsiveLayoutManager, Ui_MainWindow
from .workers import WorkThreadAdvanced


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.responsive_layout = ResponsiveLayoutManager(self)
        self._initialize_runtime_state()
        self._connect_signals()

    def _initialize_runtime_state(self):
        self.method_selected = "Differential evolution"
        self.op_obj = []
        self.opad = []
        self.surf_eq = None
        self.database = None
        self.database_path = None
        self.titration_data_path = None
        self.advanced_data_path = None
        self.error_list_titration = None
        self.error_list_advanced = None
        self.multi_is = False
        self.multi_is_ad = False
        self.last_settings_mode = "titration"
        self.work = None
        self.work2 = None

        pg.setConfigOptions(leftButtonPan=False)
        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")
        # The raster paint path is more stable than OpenGL in frozen macOS apps.
        pg.setConfigOption("useOpenGL", False)
        self.w_plt = pg.PlotWidget()
        self.verticalLayout.addWidget(self.w_plt)
        self.plot_item = self.w_plt.getPlotItem()
        self.plot_legend = self.plot_item.addLegend()
        self.species_view = pg.ViewBox()
        self.plot_item.scene().addItem(self.species_view)
        self.plot_item.getAxis("right").linkToView(self.species_view)
        self.species_view.setXLink(self.plot_item.vb)
        self.species_view.setMouseEnabled(x=False, y=True)
        self.plot_item.vb.sigResized.connect(self._sync_species_view)
        self.plot_item.hideAxis("right")
        self._sync_species_view()
        plot_font = QFont()
        plot_font.setPixelSize(16)
        plot_font.setFamily("Arial")
        self.w_plt.getAxis("left").setStyle(tickFont=plot_font, tickTextOffset=8)
        self.w_plt.getAxis("bottom").setStyle(tickFont=plot_font, tickTextOffset=8)
        self.w_plt.getAxis("right").setStyle(tickFont=plot_font, tickTextOffset=8)

        self.label_change_1()
        self.label_change_2()

        self.config_file = ConfigFile()
        self.config_file.load_config_file()
        self.database_folder = self.config_file.database_directory
        self.output_folder = self.config_file.output_directory
        self.data_folder = self.config_file.data_directory
        self.history_folder = self.output_folder

    def _connect_signals(self):
        self.pushButton_db.clicked.connect(self.load_database)
        self.pushButton_rd.clicked.connect(self.showOpendialog)
        self.pushButton_opt.clicked.connect(self.optimize_data)
        self.pushButton_addsf.clicked.connect(self.check_sp)
        self.pushButton_review.clicked.connect(self.show_surface)
        self.pushButton_cls.clicked.connect(self.clear_sp)
        self.actionTitration.triggered.connect(self.titration_view)
        self.actionPlot.triggered.connect(self.plot_view)
        self.pushButton_stp.clicked.connect(self.stop_thread)

        self.actionAdvanced.triggered.connect(self.advanced_view)
        self.pushButton_db_2.clicked.connect(self.load_database)
        self.pushButton_rd_2.clicked.connect(self.showOpendialog2)
        self.pushButton_addsf_2.clicked.connect(self.update_surface)
        self.pushButton_delsf.clicked.connect(self.del_surf)
        self.pushButton_addreact.clicked.connect(self.add_reaction)
        self.pushButton_delreact.clicked.connect(self.del_reaction)
        self.pushButton_cls_4.clicked.connect(self.clear_all)
        self.pushButton_opt_2.clicked.connect(self.advanced_opt)
        self.pushButton_stp_2.clicked.connect(self.stop_thread2)

        self.actiondifferential_evolution.triggered.connect(self.differential_evolution)
        self.actionDual_annealing.triggered.connect(self.dual_annealing)
        self.actionnelder_mead.triggered.connect(self.nelder_mead)
        self.checkBox.stateChanged.connect(self.label_change_2)
        self.checkBox.stateChanged.connect(self._reload_advanced_data_for_mode)
        self.radioButton_fx_2.toggled.connect(self.label_change_2)
        self.radioButton_ds_2.toggled.connect(self.label_change_2)
        self.radioButton_ds.toggled.connect(self.label_change_1)
        self.radioButton_fx_2.toggled.connect(self.label_change_1)

        self.actionDatabase_folder.triggered.connect(self.set_database_folder)
        self.actionOutput_folder.triggered.connect(self.set_output_folder)
        self.actionData_folder.triggered.connect(self.set_data_folder)
        self.actionEnabled.triggered.connect(self.enable_surf_eq)
        self.actionDisabled.triggered.connect(self.disable_surf_eq)
        self.actionSave_settings.triggered.connect(self.save_settings)
        self.actionLoad_settings.triggered.connect(self.load_settings)
        self.actionCompare_results.triggered.connect(self.compare_history)

    def _optimization_busy(self):
        """Keep a worker busy until its QThread.finished signal is handled."""
        return self.work is not None or self.work2 is not None

    def _set_optimization_controls(self, running=False, mode=None):
        self.pushButton_opt.setEnabled(not running)
        self.pushButton_opt_2.setEnabled(not running)
        self.comboBox_mdl.setEnabled(not running)
        self.comboBox_mdl_2.setEnabled(not running)
        self.checkBox.setEnabled(not running)
        self.pushButton_stp.setEnabled(running and mode == "titration")
        self.pushButton_stp_2.setEnabled(running and mode == "advanced")

    def _start_optimization_worker(self, worker, mode):
        if self._optimization_busy():
            QMessageBox.information(
                self,
                "Optimization running",
                "Please stop or wait for the current optimization before starting another one.",
            )
            return False

        if mode == "titration":
            self.work = worker
            worker.signals.connect(self.display_results)
        else:
            self.work2 = worker
            worker.signals.connect(self.display_results2)

        worker.finished.connect(self._optimization_worker_finished)
        self._set_optimization_controls(True, mode)
        worker.start()
        return True

    def _optimization_worker_finished(self):
        worker = self.sender()
        if worker is self.work:
            self.work = None
        if worker is self.work2:
            self.work2 = None

        if not self._optimization_busy():
            self._set_optimization_controls(False)
        worker.deleteLater()

    def _sync_species_view(self):
        self.species_view.setGeometry(self.plot_item.vb.sceneBoundingRect())
        self.species_view.linkedViewChanged(
            self.plot_item.vb,
            self.species_view.XAxis,
        )

    def compare_history(self):
        output_folder = self._configured_history_folder()
        log_path = os.path.join(output_folder, "phreefit_log.txt")
        try:
            records = read_optimization_history(log_path)
        except (OSError, UnicodeError, ValueError) as error:
            QMessageBox.warning(self, "History", "Unable to read the log:\n" + str(error))
            return
        if not records:
            QMessageBox.information(
                self,
                "History",
                "No completed optimization records were found in the current output path.",
            )
            return
        dialog = HistoryComparisonDialog(records, log_path, self)
        dialog.exec()

    def _configured_history_folder(self):
        """Use the Output path persisted in the user configuration for History."""
        self.config_file.load_config_file()
        self.output_folder = self.config_file.output_directory
        self.history_folder = self.output_folder
        return self.history_folder

    def showOpendialog(self):
        path = QFileDialog.getOpenFileName(self, "Open data", dir=self.data_folder)[0]
        if not path:
            QMessageBox.information(self, "warning", "Please choose a file")
            return
        try:
            self._load_titration_data(path)
        except Exception as error_msg:
            write_log(str(error_msg), self.output_folder)
            QMessageBox.warning(self, "Error", "Please choose a correct csv file")

    def showOpendialog2(self):
        path = QFileDialog.getOpenFileName(self, "Open data", dir=self.data_folder)[0]
        if not path:
            QMessageBox.information(self, "Warning", "Please choose a file")
            return
        try:
            self._load_advanced_data(path)
        except Exception as error_msg:
            write_log(str(error_msg), self.output_folder)
            QMessageBox.warning(self, "Error", "Please choose a correct csv file")

    def load_database(self):
        path = QFileDialog.getOpenFileName(self, "Open database", dir=self.database_folder)[0]
        if not path:
            return
        try:
            self._load_database_file(path)
        except Exception as error_msg:
            write_log(str(error_msg), self.output_folder)
            QMessageBox.warning(self, "Error", "Please choose a correct database file")

    def _load_titration_data(self, path):
        data = read_titration_data(path)
        self.error_list_titration = data.errors
        self.multi_is = data.multi_is
        self.mix_data = data.mix_data
        self.ph_res = data.ph
        self.tableView.setModel(TableModel(data.table))
        self.titration_data_path = os.path.abspath(path)
        self.data_folder = os.path.dirname(self.titration_data_path)

    def _load_advanced_data(self, path):
        data = read_advanced_data(path, titration=self.checkBox.isChecked())
        self.error_list_advanced = data.errors
        self.multi_is_ad = data.multi_is
        self.mix_data_ad = data.mix_data
        self.ph_res_ad = data.ph
        self.tableView_2.setModel(TableModel(data.table))
        self.advanced_data_path = os.path.abspath(path)
        self.data_folder = os.path.dirname(self.advanced_data_path)

    def _reload_advanced_data_for_mode(self, _state=None):
        """Reinterpret the current Advanced CSV when Titration mode changes."""
        if not self.advanced_data_path:
            return
        path = self.advanced_data_path
        try:
            self._load_advanced_data(path)
        except Exception as error_msg:
            self._clear_advanced_data(path)
            write_log(str(error_msg), self.output_folder)
            QMessageBox.warning(
                self,
                "Advanced data",
                "Unable to reload the current data for the selected mode:\n" + str(error_msg),
            )

    def _load_database_file(self, path):
        self.database = read_database(path)
        self.database_path = os.path.abspath(path)
        self.database_folder = os.path.dirname(self.database_path)

    def _serialize_widgets(self, page):
        excluded_text_edits = {"textEdit_res", "textEdit_sf", "textEdit_res_2", "textEdit_sf_2"}
        return {
            "line_edits": {widget.objectName(): widget.text() for widget in page.findChildren(QLineEdit)},
            "text_edits": {
                widget.objectName(): widget.toPlainText()
                for widget in page.findChildren(QTextEdit)
                if widget.objectName() not in excluded_text_edits and not widget.isReadOnly()
            },
            "checkboxes": {widget.objectName(): widget.isChecked() for widget in page.findChildren(QCheckBox)},
            "radio_buttons": {
                widget.objectName(): widget.isChecked() for widget in page.findChildren(QRadioButton)
            },
            "combo_boxes": {
                widget.objectName(): {
                    "index": widget.currentIndex(),
                    "text": widget.currentText(),
                }
                for widget in page.findChildren(QComboBox)
            },
        }

    def _restore_widgets(self, settings):
        for name, value in settings.get("line_edits", {}).items():
            widget = getattr(self, name, None)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
        for name, value in settings.get("text_edits", {}).items():
            widget = getattr(self, name, None)
            if isinstance(widget, QTextEdit) and not widget.isReadOnly():
                widget.setPlainText(str(value))
        for name, value in settings.get("checkboxes", {}).items():
            widget = getattr(self, name, None)
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))

        radio_settings = settings.get("radio_buttons", {})
        for checked in (False, True):
            for name, value in radio_settings.items():
                widget = getattr(self, name, None)
                if isinstance(widget, QRadioButton) and bool(value) == checked:
                    widget.setChecked(checked)

        for name, value in settings.get("combo_boxes", {}).items():
            widget = getattr(self, name, None)
            if not isinstance(widget, QComboBox) or not isinstance(value, dict):
                continue
            index = widget.findText(str(value.get("text", "")))
            if index < 0:
                index = int(value.get("index", -1))
            if 0 <= index < widget.count():
                widget.setCurrentIndex(index)

    def _settings_snapshot(self):
        active_mode = self.last_settings_mode
        if self.stackedWidget.currentIndex() == 0:
            active_mode = "titration"
        elif self.stackedWidget.currentIndex() == 2:
            active_mode = "advanced"
        return {
            "format": SETTINGS_FORMAT,
            "version": SETTINGS_VERSION,
            "active_mode": active_mode,
            "common": {
                "database_path": self.database_path,
                "algorithm": self.method_selected,
                "pre_equilibrate_enabled": self.actionEnabled.isChecked(),
                "surface_equilibrium": json_value(self.surf_eq),
                "directories": {
                    "data": self.data_folder,
                    "database": self.database_folder,
                    "output": self.output_folder,
                },
            },
            "titration": {
                "data_path": self.titration_data_path,
                "widgets": self._serialize_widgets(self.page),
                "surfaces": [serialize_surface(surface) for surface in self.op_obj],
            },
            "advanced": {
                "data_path": self.advanced_data_path,
                "widgets": self._serialize_widgets(self.page_3),
                "surfaces": [serialize_surface(surface) for surface in self.opad],
            },
        }

    def save_settings(self):
        self._configured_history_folder()
        snapshot = self._settings_snapshot()
        active_mode = snapshot["active_mode"]
        default_path = os.path.join(self.output_folder, active_mode + "_settings.json")
        path = QFileDialog.getSaveFileName(self, "Save settings", default_path, "JSON files (*.json)")[0]
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            save_settings_file(path, snapshot)
            QMessageBox.information(self, "History", "Settings saved successfully")
        except Exception as error_msg:
            write_log(str(error_msg), self.output_folder)
            QMessageBox.warning(self, "Error", "Unable to save settings:\n" + str(error_msg))

    def _restore_algorithm(self, algorithm):
        if algorithm == self.actionDual_annealing.text():
            self.dual_annealing()
        elif algorithm == self.actionnelder_mead.text():
            self.nelder_mead()
        else:
            self.differential_evolution()

    def _clear_titration_data(self, requested_path=None):
        self.titration_data_path = requested_path
        self.error_list_titration = None
        self.multi_is = False
        self.mix_data = None
        self.ph_res = None
        self.tableView.setModel(None)

    def _clear_advanced_data(self, requested_path=None):
        self.advanced_data_path = requested_path
        self.error_list_advanced = None
        self.multi_is_ad = False
        self.mix_data_ad = None
        self.ph_res_ad = None
        self.tableView_2.setModel(None)

    def load_settings(self):
        history_folder = self._configured_history_folder()
        path = QFileDialog.getOpenFileName(self, "Load settings", history_folder, "JSON files (*.json)")[0]
        if not path:
            return
        try:
            settings = load_settings_file(path)
            common = settings.get("common", {})
            titration = settings.get("titration", {})
            advanced = settings.get("advanced", {})

            directories = common.get("directories", {})
            for attribute, key in (("data_folder", "data"), ("database_folder", "database"),
                                   ("output_folder", "output")):
                directory = directories.get(key)
                if directory and os.path.isdir(directory):
                    setattr(self, attribute, directory)

            self._restore_widgets(titration.get("widgets", {}))
            check_box_was_blocked = self.checkBox.blockSignals(True)
            try:
                self._restore_widgets(advanced.get("widgets", {}))
            finally:
                self.checkBox.blockSignals(check_box_was_blocked)
            self.op_obj = [deserialize_surface(item) for item in titration.get("surfaces", [])]
            self.opad = [deserialize_surface(item) for item in advanced.get("surfaces", [])]

            surface_equilibrium = common.get("surface_equilibrium")
            self.surf_eq = tuple(surface_equilibrium) if isinstance(surface_equilibrium, list) else surface_equilibrium
            pre_equilibrate = bool(common.get("pre_equilibrate_enabled", False))
            self.actionEnabled.setChecked(pre_equilibrate)
            self.actionDisabled.setChecked(not pre_equilibrate)
            self._restore_algorithm(common.get("algorithm", "Differential evolution"))

            load_warnings = []
            database_path = common.get("database_path")
            self.database_path = database_path
            if database_path:
                try:
                    self._load_database_file(database_path)
                except Exception as error_msg:
                    self.database = None
                    load_warnings.append("Database: " + str(error_msg))
            else:
                self.database = None

            titration_path = titration.get("data_path")
            if titration_path:
                try:
                    self._load_titration_data(titration_path)
                except Exception as error_msg:
                    self._clear_titration_data(titration_path)
                    load_warnings.append("Titration data: " + str(error_msg))
            else:
                self._clear_titration_data()

            advanced_path = advanced.get("data_path")
            if advanced_path:
                try:
                    self._load_advanced_data(advanced_path)
                except Exception as error_msg:
                    self._clear_advanced_data(advanced_path)
                    load_warnings.append("Advanced data: " + str(error_msg))
            else:
                self._clear_advanced_data()

            self.label_change_1()
            self.label_change_2()
            self.show_surface()
            self.show_surface2()
            if settings.get("active_mode") == "advanced":
                self.advanced_view()
            else:
                self.titration_view()

            self.config_file.update_config_file([self.data_folder, self.database_folder, self.output_folder])
            self.history_folder = self.output_folder
            if load_warnings:
                QMessageBox.warning(
                    self,
                    "History",
                    "Settings restored, but some files could not be loaded:\n" + "\n".join(load_warnings),
                )
            else:
                QMessageBox.information(self, "History", "Settings loaded successfully")
        except Exception as error_msg:
            write_log(str(error_msg), self.output_folder)
            QMessageBox.warning(self, "Error", "Unable to load settings:\n" + str(error_msg))

    def add_surface(self):
        tem_sp = mc.SurfaceSpecies2()
        temp_name = self.lineEdit_sname.text().strip().capitalize()
        tem_sp.add_surface(surfacename=temp_name, surface_ms=temp_name + "OH", mass=self.lineEdit_smass.text(),
                           sites=(float(self.lineEdit_sitelb.text()), float(self.lineEdit_siteub.text())),
                           area=self.lineEdit_sarea.text(), sites_initial=float(self.lineEdit_isite.text()),
                           c1_initial=float(self.lineEdit_icap.text()),
                           c1=(float(self.lineEdit_caplb.text()), float(self.lineEdit_capub.text())), c2=0)
        if self.checkBox_pro.isChecked() == True:
            if float(self.lineEdit_ikp.text())<float(self.lineEdit_plb.text()) or float(self.lineEdit_ikp.text())>float(self.lineEdit_pub.text()):
                QMessageBox.information(None, "warning", "The initial guess of log_k should be within the bounds",
                                    QMessageBox.Yes | QMessageBox.No)

            tem_sp.add_reactions(reactions=tem_sp.surface_name + "OH" + " + H+ = " + tem_sp.surface_name + "OH2+",
                                     k_initial=float(self.lineEdit_ikp.text()),
                                     k=(float(self.lineEdit_plb.text()), float(self.lineEdit_pub.text())), z0d=True,
                                     ztotal=1, z1=1)

        if self.checkBox_dpro.isChecked() == True:
            if float(self.lineEdit_ikdp.text())<float(self.lineEdit_dplb.text()) or float(self.lineEdit_ikdp.text())>float(self.lineEdit_dpub.text()):
                QMessageBox.information(None, "warning", "The initial guess of log_k should be within the bounds",
                                        QMessageBox.Yes | QMessageBox.No)

            tem_sp.add_reactions(reactions=tem_sp.surface_name + "OH" + " = " + tem_sp.surface_name + "O-" + " + H+",
                                     k_initial=float(self.lineEdit_ikdp.text()),
                                     k=(float(self.lineEdit_dplb.text()), float(self.lineEdit_dpub.text())), z0d=True,
                                     ztotal=1, z1=1)
        return tem_sp

    def check_sp(self):
        sp_name = []
        for obj in self.op_obj:
            sp_name.append(obj.surface_name)
        if self.lineEdit_sname.text().strip().capitalize() != "":
            if sp_name.count(self.lineEdit_sname.text().strip().capitalize()) == 0:
                self.op_obj.append(self.add_surface())

            else:
                self.op_obj.pop(sp_name.index(self.lineEdit_sname.text().strip().capitalize()))
                self.op_obj.append(self.add_surface())

    def show_surface(self):
        surface_reaction = ""
        if self.actionEnabled.isChecked() == True and self.surf_eq is not None:
            surface_reaction += "The surface will equilibrate with a solution before titration ( pH: " + str(
                self.surf_eq[0]) + ", " \
                                + "IS:" + str(self.surf_eq[1]) + ")\n"
        for obj in self.op_obj:
            surface_reaction += obj.surface_name + "\n"
            surface_reaction += str(obj.sfinitial[0]) + " bounds: " + str(obj.surface_sites[0]) + " - " + str(
                obj.surface_sites[1]) + "\n"
            for react in obj.surface_reactions.keys():
                surface_reaction += react + "\n"
                surface_reaction += "\t" + "initial_log_k: " + str(obj.surface_reactions[react][4]) + "\n"
                surface_reaction += "\t" + "log_k bounds: " + str(obj.surface_reactions[react][0][0]) + " - " + str(
                    obj.surface_reactions[react][0][1]) + "\n"
        self.textEdit_sf.setText(surface_reaction)

    def optimize_data(self):
        if self._optimization_busy():
            QMessageBox.information(
                self,
                "Optimization running",
                "Please stop or wait for the current optimization before starting another one.",
            )
            return
        try:
            # print(self.output_folder)
            task_name = QInputDialog.getText(None, "Task name", "Input here")[0]
            self.config_file.update_config_file([self.data_folder,self.database_folder,self.output_folder])
            num_process = max(1, min(int(self.lineEdit_cycle.text()), multiprocessing.cpu_count()))
            pt = mc.Adsorption(self.comboBox_mdl.currentText())
            if self.multi_is == False:
                Na = [float(self.lineEdit_cs.text())]
            elif self.multi_is == True:
                Na = list(self.mix_data.groups.keys())
            initial_ph = float(self.lineEdit_ph.text())
            initial_volume = float(self.lineEdit_vol.text())
            pt.species_definition(self.database, None)
            pt.initial_solution(Na, initial_pH=initial_ph, cation="Na", anion="Cl", metal={})
            pt.set_type_acid(type_acid=self.comboBox_ad.currentText(), type_base=self.comboBox_bs.currentText())
            if self.radioButton_fx.isChecked() == True:
                type_solution = "fix_pH"
                pt.mix_solution(type_solution=type_solution, base_pH=float(self.lineEdit_base.text()),
                                acid_pH=float(self.lineEdit_acid.text()))
            elif self.radioButton_ds.isChecked() == True:
                type_solution = "dissolution"
                pt.mix_solution(type_solution=type_solution, base_mass=float(self.lineEdit_base.text()),
                                acid_mass=float(self.lineEdit_acid.text()))
            else:
                QMessageBox.information(None, "warning", "Please check your input in dissolution",
                                        QMessageBox.Yes | QMessageBox.No)
            if self.actionEnabled.isChecked() == True and self.surf_eq != None:
                pt.equilibrate_solution(self.surf_eq[1], self.surf_eq[0])
            for i in range(0, len(self.op_obj)):
                # print(self.op_obj[i].surface_name)
                if i == len(self.op_obj) - 1:
                    pt.add_surface(self.op_obj[i])
                else:
                    self.op_obj[i].reset_cap(1, 1)
                    pt.add_surface(self.op_obj[i])
            pt.selected_output({})
            pt.mix_action(initial_volume=initial_volume, mix_volume=self.mix_data)
            pt.get_bounds()
            worker = WorkThreadAdvanced()
            worker.set_pa(pt, self.ph_res, int(self.lineEdit_iter.text()), int(self.lineEdit_temp.text()), mix=0,
                          method=self.method_selected, process_num=num_process, task=task_name,
                          error_list=self.error_list_titration)
            self._start_optimization_worker(worker, "titration")
        except Exception as e:
            write_log(str(e), self.output_folder)
            if not self._optimization_busy():
                self._set_optimization_controls(False)

    def display_results(self, ssss):
        self.pushButton_stp.setEnabled(False)

        if ssss.get("cancelled", False):
            self.textEdit_res.append(ssss["Task"] + '\n' + ssss["error"] + "\n")
            write_log(ssss["Task"] + '\n' + ssss["error"], self.output_folder)
        elif ssss["successful"] == True:
            if ssss["iterations"] < int(self.lineEdit_iter.text()) and self.method_selected == "Differential evolution":
                QMessageBox.information(None, "warning", "The iterations of DE method is rather few, please rerun or change some settings",
                                        QMessageBox.Yes | QMessageBox.No)
            log_temp = self.comboBox_mdl.currentText()
            self.textEdit_res.append(ssss["Task"] + '\n' + ssss["eva"] + "\n" + ssss["time"] + "\n")
            log_temp += ssss["surface"]
            write_log(ssss["Task"] + '\n' + ssss["eva"] + log_temp + "\n" + ssss["time"], self.output_folder)
            write_results(self.ph_res, ssss["model"],ssss["speciation"], self.output_folder)
            self.plot_res(
                ssss["model"],
                titration=True,
                view=False,
                speciation=ssss.get("speciation"),
                surface_species=ssss.get("surface_species"),
                surface_species_groups=ssss.get("surface_species_groups"),
            )
        else:
            self.textEdit_res.append(ssss["Task"]+'\n'+ssss["error"] + "\n")
            write_log(ssss["Task"]+'\n'+ssss["error"], self.output_folder)

    def clear_sp(self):
        self.op_obj.clear()

    def plot_view(self):
        self.stackedWidget.setCurrentIndex(1)

    def titration_view(self):
        self.last_settings_mode = "titration"
        self.stackedWidget.setCurrentIndex(0)

    @staticmethod
    def _extract_surface_species(speciation, surface_species):
        if speciation is None or len(speciation) < 2 or not surface_species:
            return {}

        headers = [str(header).strip() for header in speciation[0]]

        def normalize_header(header):
            normalized = header.strip()
            if normalized.casefold().endswith("(mol/kgw)"):
                normalized = normalized[:-len("(mol/kgw)")].strip()
            return normalized.casefold()

        normalized_headers = {normalize_header(header): index for index, header in enumerate(headers)}
        series = {}
        for species in surface_species:
            species_name = str(species).strip()
            candidates = (species_name, "m_" + species_name)
            column_index = next(
                (normalized_headers[normalize_header(name)]
                 for name in candidates if normalize_header(name) in normalized_headers),
                None,
            )
            if column_index is None:
                continue

            values = []
            for row in speciation[1:]:
                try:
                    values.append(float(row[column_index]))
                except (IndexError, TypeError, ValueError):
                    values.append(float("nan"))
            series[species_name] = values
        return series

    @staticmethod
    def _surface_species_styles(surface_species, surface_species_groups):
        species_symbols = ("o", "s", "t", "t1", "t2", "t3", "d", "p")
        species_colors = (
            "#E69F00",  # orange
            "#7B2CBF",  # violet
            "#009E73",  # blue-green
            "#A65628",  # brown
            "#CC79A7",  # reddish purple
            "#6B8E23",  # olive
            "#264653",  # dark blue-green
            "#F4A261",  # light orange
            "#0072B2",  # blue
            "#D55E00",  # vermillion
        )
        groups = surface_species_groups or [
            {"surface_name": "surface", "species": surface_species or []}
        ]
        styles = {}
        ordered_species = []
        surface_symbols = {}
        surface_color_indexes = {}
        for group in groups:
            surface_name = str(group.get("surface_name") or "surface").strip().casefold()
            if surface_name not in surface_symbols:
                surface_symbols[surface_name] = species_symbols[len(surface_symbols) % len(species_symbols)]
                surface_color_indexes[surface_name] = 0
            symbol = surface_symbols[surface_name]
            for species in group.get("species", []):
                species_name = str(species).strip()
                if not species_name or species_name in styles:
                    continue
                color_index = surface_color_indexes[surface_name]
                styles[species_name] = (
                    symbol,
                    species_colors[color_index % len(species_colors)],
                )
                surface_color_indexes[surface_name] += 1
                ordered_species.append(species_name)
        return ordered_species, styles

    def _plot_surface_species(self, speciation, surface_species, surface_species_groups, x_segments):
        ordered_species, species_styles = self._surface_species_styles(
            surface_species,
            surface_species_groups,
        )
        species_series = self._extract_surface_species(speciation, ordered_species)
        expected_points = sum(len(segment) for segment in x_segments)
        species_series = {
            name: values[-expected_points:]
            for name, values in species_series.items()
            if expected_points and len(values) >= expected_points
        }
        if not species_series:
            self.plot_item.hideAxis("right")
            return

        self.plot_item.showAxis("right")
        label_style = {"font": "Arial", "color": "#000", "font-size": "16pt"}
        self.plot_item.getAxis("right").setLabel("Surface species (mol/kgw)", **label_style)
        for species_name, values in species_series.items():
            symbol, color = species_styles[species_name]
            pen = pg.mkPen(
                color,
                width=2,
                style=Qt.PenStyle.DashLine,
            )
            offset = 0
            first_curve = None
            for x_values in x_segments:
                count = len(x_values)
                curve = pg.PlotDataItem(
                    x_values,
                    values[offset:offset + count],
                    pen=pen,
                    symbol=symbol,
                    symbolSize=7,
                    symbolPen=pg.mkPen(color, width=1.5),
                    symbolBrush=pg.mkBrush("w"),
                )
                self.species_view.addItem(curve)
                if first_curve is None:
                    first_curve = curve
                offset += count
            if first_curve is not None:
                self.plot_legend.addItem(first_curve, species_name)

        self.species_view.enableAutoRange(axis=self.species_view.YAxis, enable=True)
        self._sync_species_view()

    def plot_res(self, model_res, titration=False, view=False, speciation=None, surface_species=None,
                 surface_species_groups=None):
        r_symbol = ('o', 's', 't', 't1', 't2', 't3', 'd', '+', 'x', 'p')
        r_color = ('b', 'g', 'r', 'c', 'm', 'y', 'k', 'd', 'l', 's')
        self.w_plt.clear()
        self.species_view.clear()
        self.plot_legend.clear()
        x_label = "volume"
        y_label = "pH"
        label_style = {"font": "Arial", "color": "#000", "font-size": "16pt"}
        if titration == False:
            self.w_plt.getAxis("left").setLabel(self.lineEdit_output.text() + " mol/L", **label_style)
            self.w_plt.getAxis("bottom").setLabel("pH", **label_style)
            x_label = "pH"
            y_label = "amounts"
        else:
            self.w_plt.getAxis("left").setLabel("pH", **label_style)
            self.w_plt.getAxis("bottom").setLabel("Volume (mL)", **label_style)
        if view == False:  # titration view
            multi_is = self.multi_is
            x_data = self.mix_data
            y_data = self.ph_res
        else:  # ad view
            multi_is = self.multi_is_ad
            x_data = self.mix_data_ad
            y_data = self.ph_res_ad
        if multi_is == False:
            x_segments = [list(x_data)]
            self.w_plt.plot(x_data, y_data, pen=None, symbol=r_symbol[0], symbolBrush=r_color[0],
                            name="exp_data")
            self.w_plt.plot(x_data, model_res, pen=pg.mkPen(color="r", width=2), name="model")
        else:
            na = list(x_data.groups.keys())
            x_segments = []
            j = 0
            for i in range(0, len(na)):
                x1 = x_data.get_group(na[i])[x_label].to_list()
                x_segments.append(x1)
                self.w_plt.plot(x1, x_data.get_group(na[i])[y_label].to_list(),
                                pen=None, symbol=r_symbol[i], symbolBrush=r_color[i], name=str(na[i]))
                self.w_plt.plot(x1, model_res[j:j + len(x1)], pen=pg.mkPen(color=r_color[i], width=2), name=str(na[i]))
                j += len(x1)
        self._plot_surface_species(
            speciation,
            surface_species,
            surface_species_groups,
            x_segments,
        )

    def stop_thread(self):
        if self.work is not None and self.work.isRunning():
            self.work.request_stop()
            self.pushButton_stp.setEnabled(False)

    def advanced_view(self):
        self.last_settings_mode = "advanced"
        self.stackedWidget.setCurrentIndex(2)

    def add_surface2(self):
        tem_sp = mc.SurfaceSpecies2()
        current_sname = self.lineEdit_sname_2.text().strip().capitalize()

        if self.checkBox_site.isChecked() == True:
            site = float(self.lineEdit_isite_2.text())
        else:
            if float(self.lineEdit_isite_2.text())<float(self.lineEdit_sitelb_2.text()) or float(self.lineEdit_isite_2.text())>float(self.lineEdit_siteub_2.text()):
                QMessageBox.information(None, "warning", "The initial guess of sites should be within the bounds",
                                    QMessageBox.Yes | QMessageBox.No)
            site = (float(self.lineEdit_sitelb_2.text()), float(self.lineEdit_siteub_2.text()))
        if self.checkBox_c1.isChecked() == True:
            c1 = float(self.lineEdit_ic1.text())
        else:
            if float(self.lineEdit_ic1.text())<float(self.lineEdit_ic1lb.text()) or float(self.lineEdit_ic1.text())>float(self.lineEdit_ic1ub.text()):
                QMessageBox.information(None, "warning", "The initial guess of C1 should be within the bounds",
                                    QMessageBox.Yes | QMessageBox.No)
            c1 = (float(self.lineEdit_ic1lb.text()), float(self.lineEdit_ic1ub.text()))
        if self.checkBox_c2.isChecked() == True:
            c2 = float(self.lineEdit_ic2.text())
        else:
            if float(self.lineEdit_ic2.text())<float(self.lineEdit_ic2lb.text()) or float(self.lineEdit_ic2.text())>float(self.lineEdit_ic2ub.text()):
                QMessageBox.information(None, "warning", "The initial guess of C2 should be within the bounds",
                                    QMessageBox.Yes | QMessageBox.No)
            c2 = (float(self.lineEdit_ic2lb.text()), float(self.lineEdit_ic2ub.text()))
        surface_formula = self.lineEdit_sformula.text()
        surface_formula = surface_formula[0].upper() + surface_formula[1:]
        tem_sp.add_surface(surfacename=current_sname, surface_ms=surface_formula,
                           mass=self.lineEdit_smass_2.text(),
                           sites=site, area=self.lineEdit_sarea_2.text(), c1=c1, c2=c2,
                           sites_initial=float(self.lineEdit_isite_2.text()),
                           c1_initial=float(self.lineEdit_ic1.text()), c2_initial=float(self.lineEdit_ic2.text()))
        return tem_sp

    def update_surface(self):
        sp_name = []
        for obj in self.opad:
            sp_name.append(obj.surface_name)
        current_sname = self.lineEdit_sname_2.text().strip().capitalize()
        # avoid input a blank space as surface name
        if current_sname != "":
            if sp_name.count(current_sname) == 0:
                self.opad.append(self.add_surface2())

            else:
                self.opad.pop(sp_name.index(current_sname))
                self.opad.append(self.add_surface2())

    def del_surf(self):
        current_sname = self.lineEdit_sname_2.text().strip().capitalize()
        for i in range(0, len(self.opad)):
            if self.opad[i].surface_name == current_sname:
                self.opad.pop(i)

    def add_reaction(self):
        reaction = self.lineEdit_reaction.text().strip()
        sp_name = []
        for obj in self.opad:
            sp_name.append(obj.surface_name)
        for name in sp_name:
            if reaction.find(name) != -1:
                if self.checkBox_logk.isChecked() == True:
                    logk = float(self.lineEdit_ik.text())
                else:
                    if float(self.lineEdit_ik.text()) < float(self.lineEdit_iklb.text()) or float(self.lineEdit_ik.text()) > float(self.lineEdit_ikub.text()):
                        QMessageBox.information(None, "warning", "The initial guess of k should be within the bounds",
                                                QMessageBox.Yes | QMessageBox.No)
                    logk = (float(self.lineEdit_iklb.text()), float(self.lineEdit_ikub.text()))
                if self.checkBox_z1.isChecked() == True:
                    z1 = float(self.lineEdit_iz1.text())
                else:
                    if float(self.lineEdit_iz1.text()) < float(self.lineEdit_iz1lb.text()) or float(self.lineEdit_iz1.text()) > float(self.lineEdit_iz1ub.text()):
                        QMessageBox.information(None, "warning", "The initial guess of z1 should be within the bounds",
                                                QMessageBox.Yes | QMessageBox.No)
                    z1 = (float(self.lineEdit_iz1lb.text()), float(self.lineEdit_iz1ub.text()))
                if self.comboBox_charge.currentIndex() == 0:
                    z0d = True
                else:
                    z0d = False
                self.opad[sp_name.index(name)].add_reactions(reactions=reaction, k=logk, z0d=z0d, z1=z1,
                                                             ztotal=float(self.lineEdit_totalz.text()),
                                                             k_initial=float(self.lineEdit_ik.text()),
                                                             z1_initial=float(self.lineEdit_iz1.text()))
                break
        self.show_surface2()

    def del_reaction(self):
        reaction = self.lineEdit_reaction.text().strip()
        for obj in self.opad:
            for rec in list(obj.surface_reactions.keys()):
                if rec == reaction:
                    del obj.surface_reactions[rec]
                    # break
        self.show_surface2()

    def show_surface2(self):
        surface_reaction = ""
        if self.actionEnabled.isChecked() == True and self.surf_eq is not None:
            surface_reaction += "The surface will equilibrate with a solution before titration ( pH: " + str(
                self.surf_eq[0]) + ", " \
                                + "IS:" + str(self.surf_eq[1]) + ")\n"
        for obj in self.opad:
            surface_reaction += obj.surface_name + "\n"
            if self.comboBox_mdl_2.currentText() == "CCM":
                surface_reaction += str(obj.surface_sites) + " ccm: " + str(obj.surface_C1) + "\n"
            elif self.comboBox_mdl_2.currentText() == "CDMUSIC":
                surface_reaction += str(obj.surface_sites) + " c1: " + str(obj.surface_C1) + " " + \
                                    " c2: " + str(obj.surface_C2) + "\n"
            else:
                surface_reaction += str(obj.surface_sites) + "\n"
            for react in obj.surface_reactions.keys():
                surface_reaction += react + "\n"
                surface_reaction += "\t" + "log_k: " + str(obj.surface_reactions[react][0]) + "\n"
                if self.comboBox_mdl_2.currentText() == "CDMUSIC":
                    if obj.surface_reactions[react][2] == True:
                        location = "z0+z1"
                    else:
                        location = "z1+zd"
                    surface_reaction += "\t" + "z1: " + str(
                        obj.surface_reactions[react][1]) + " location:" + location + " " + str(
                        obj.surface_reactions[react][3]) + "\n"
        self.textEdit_sf_2.setText(surface_reaction)

    def clear_all(self):
        self.opad.clear()
        self.show_surface2()

    def advanced_opt(self):
        if self._optimization_busy():
            QMessageBox.information(
                self,
                "Optimization running",
                "Please stop or wait for the current optimization before starting another one.",
            )
            return
        try:
            self.config_file.update_config_file([self.data_folder, self.database_folder, self.output_folder])
            task_name = QInputDialog.getText(None, "Task name", "Input here")[0]
            num_process = max(1, min(int(self.lineEdit_cycle_2.text()), multiprocessing.cpu_count()))
            problem = mc.Adsorption(self.comboBox_mdl_2.currentText())
            if self.multi_is_ad == False:
                Na = [float(self.lineEdit_cs_2.text())]
            elif self.multi_is_ad == True:
                Na = list(self.mix_data_ad.groups.keys())
            initial_ph = float(self.lineEdit_ph_4.text())
            initial_volume = float(self.lineEdit_ph_5.text())
            metal_name = self.lineEdit_reactant.text()
            if metal_name.strip() == "":
                metal = {}
            else:
                metal_amounts = float(self.lineEdit_moles.text())
                metal = {metal_name: metal_amounts}
            target_com = self.lineEdit_output.text()
            problem.species_definition(self.database, None)
            problem.initial_solution(Na, initial_pH=initial_ph, cation=self.lineEdit_cation.text(),
                                     anion=self.lineEdit_anion.text(),
                                     metal=metal)
            problem.selected_output(output={self.comboBox.currentText(): target_com})
            problem.set_type_acid(type_acid=self.comboBox_ad_2.currentText(),
                                  type_base=self.comboBox_bs_2.currentText())
            for items in self.opad:
                problem.add_surface(items)
            if self.checkBox.isChecked() == True:
                problem.selected_output({}) #reset the output
                if self.radioButton_fx_2.isChecked() == True:
                    type_solution = "fix_pH"
                    problem.mix_solution(type_solution=type_solution, base_pH=float(self.lineEdit_base_2.text()),
                                         acid_pH=float(self.lineEdit_acid_2.text()))
                elif self.radioButton_ds_2.isChecked() == True:
                    type_solution = "dissolution"
                    problem.mix_solution(type_solution=type_solution, base_mass=float(self.lineEdit_base_2.text()),
                                         acid_mass=float(self.lineEdit_acid_2.text()))
                if self.actionEnabled.isChecked() == True and self.surf_eq != None:
                    problem.equilibrate_solution(self.surf_eq[1], self.surf_eq[0])
                problem.mix_action(initial_volume=initial_volume, mix_volume=self.mix_data_ad)
                problem.get_bounds()
                worker = WorkThreadAdvanced()
                worker.set_pa(problem, self.ph_res_ad, int(self.lineEdit_iter_2.text()),
                              int(self.lineEdit_temp_2.text()), mix=0, method=self.method_selected,
                              process_num=num_process, task=task_name,
                              error_list=self.error_list_advanced)
                self._start_optimization_worker(worker, "advanced")
            else:
                sep_ph = len(Na) * [float(self.lineEdit_base_2.text())]
                if self.checkBox_7.isChecked() == True:
                    mix = 2
                else:
                    mix = 1
                    problem.eq_ph(ph_list=self.mix_data_ad, eq_phase=self.textEdit.toPlainText(), ph_sep=sep_ph,
                                  auto_p=False)
                problem.get_bounds()
                worker = WorkThreadAdvanced()
                worker.set_pa(problem, self.ph_res_ad, int(self.lineEdit_iter_2.text()),
                              int(self.lineEdit_temp_2.text()),
                              mix=mix, ph_list=self.mix_data_ad, eq=self.textEdit.toPlainText(),
                              method=self.method_selected, process_num=num_process, task=task_name,
                              error_list=self.error_list_advanced)
                self._start_optimization_worker(worker, "advanced")
        except Exception as e:
            write_log(str(e), self.output_folder)
            if not self._optimization_busy():
                self._set_optimization_controls(False)

    def display_results2(self, ssss):
        self.pushButton_stp_2.setEnabled(False)

        if ssss.get("cancelled", False):
            self.textEdit_res_2.append(ssss["Task"] + '\n' + ssss["error"] + "\n")
            write_log(ssss["Task"] + '\n' + ssss["error"], self.output_folder)
        elif ssss["successful"] == True:
            if ssss["iterations"] < int(self.lineEdit_iter_2.text()) and self.method_selected == "Differential evolution":
                QMessageBox.information(None, "warning", "The iterations of DE method is rather few, please rerun or change some settings",
                                        QMessageBox.Yes | QMessageBox.No)
            log_temp = self.comboBox_mdl_2.currentText()
            self.textEdit_res_2.append(ssss["Task"] + '\n' + ssss["eva"] + "\n" + ssss["time"] + "\n")
            log_temp += ssss["surface"]
            write_log(ssss["Task"] + '\n' + ssss["eva"] + log_temp + "\n" + ssss["time"], self.output_folder)
            write_results(self.ph_res_ad, ssss["model"],ssss["speciation"], self.output_folder)
            self.plot_res(
                ssss["model"],
                ssss["type"],
                view=True,
                speciation=ssss.get("speciation"),
                surface_species=ssss.get("surface_species"),
                surface_species_groups=ssss.get("surface_species_groups"),
            )
        else:
            self.textEdit_res_2.append(ssss["Task"]+'\n'+ssss["error"] + "\n")
            write_log(ssss["Task"]+'\n'+ssss["error"], self.output_folder)

    def stop_thread2(self):
        if self.work2 is not None and self.work2.isRunning():
            self.work2.request_stop()
            self.pushButton_stp_2.setEnabled(False)

    def dual_annealing(self):
        self.actiondifferential_evolution.setChecked(False)
        self.actionDual_annealing.setChecked(True)
        self.actionnelder_mead.setChecked(False)
        self.method_selected = self.actionDual_annealing.text()
        self.lineEdit_cycle_2.setEnabled(False)
        self.lineEdit_cycle.setEnabled(False)

    def differential_evolution(self):
        self.actionDual_annealing.setChecked(False)
        self.actiondifferential_evolution.setChecked(True)
        self.actionnelder_mead.setChecked(False)
        self.method_selected = self.actiondifferential_evolution.text()
        self.lineEdit_cycle_2.setEnabled(True)
        self.lineEdit_cycle.setEnabled(True)

    def nelder_mead(self):
        self.actionnelder_mead.setChecked(True)
        self.actionDual_annealing.setChecked(False)
        self.actiondifferential_evolution.setChecked(False)
        self.method_selected=self.actionnelder_mead.text()
        self.lineEdit_cycle_2.setEnabled(False)
        self.lineEdit_cycle.setEnabled(False)

    def label_change_2(self):
        if self.checkBox.isChecked() and self.radioButton_ds_2.isChecked():
            self.label_13.setText("mol/L")
            self.label_16.setText("mol/L")
        elif self.checkBox.isChecked() and self.radioButton_fx_2.isChecked():
            self.label_13.setText("pH value")
            self.label_16.setText("pH value")
        elif self.checkBox.isChecked() == False:
            self.label_13.setText("Sep pH")
        else:
            self.label_13.setText("mol/L")
            self.label_16.setText("mol/L")

    def label_change_1(self):

        if self.radioButton_ds.isChecked():
            self.label_12.setText("mol/L")
            self.label_15.setText("mol/L")
        elif self.radioButton_fx.isChecked():
            self.label_12.setText("pH value")
            self.label_15.setText("pH value")
        else:
            self.label_12.setText("mol/L")
            self.label_15.setText("mol/L")

    def set_database_folder(self):
        self.database_folder = QFileDialog.getExistingDirectory(None, "Open database", dir=self.database_folder)

    def set_data_folder(self):
        self.data_folder = QFileDialog.getExistingDirectory(None, "Open data", dir=self.data_folder)

    def set_output_folder(self):
        selected_folder = QFileDialog.getExistingDirectory(None, "Output to:", dir=self.output_folder)
        if not selected_folder:
            return
        self.output_folder = selected_folder
        self.history_folder = selected_folder
        self.config_file.update_config_file([
            self.data_folder,
            self.database_folder,
            self.output_folder,
        ])

    def enable_surf_eq(self):
        if self.stackedWidget.currentIndex() == 2 and self.checkBox.isChecked() == False:
            QMessageBox.information(None, "warning", "This function is ony valid for titration",
                                    QMessageBox.Yes | QMessageBox.No)
            self.disable_surf_eq()
        else:
            self.actionEnabled.setChecked(True)
            self.actionDisabled.setChecked(False)
            ph, ok1 = QInputDialog.getDouble(None, "Input pH", "pH: 0-14", decimals=3)
            surf_eq_prep = []
            if ok1:
                if ph >= 0 and ph <= 14:
                    surf_eq_prep.append(ph)
                    ionic_strength, ok2 = QInputDialog.getDouble(None, "Input IS", "IS (mol/L)", decimals=2)
                    if ok2:
                        surf_eq_prep.append(ionic_strength)
                        self.surf_eq = surf_eq_prep
                    else:
                        self.disable_surf_eq()
                        QMessageBox.information(None, "warning", "Input error, try again",
                                                QMessageBox.Yes | QMessageBox.No)
                else:
                    self.disable_surf_eq()
                    QMessageBox.information(None, "warning", "pH should be 1-14",
                                            QMessageBox.Yes | QMessageBox.No)

    def disable_surf_eq(self):
        self.surf_eq = None
        self.actionEnabled.setChecked(False)
        self.actionDisabled.setChecked(True)


    def closeEvent(self, event):
        result = QMessageBox.question(
            self,
            "Confirm Exit...",
            "Are you sure you want to exit ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            workers = [worker for worker in (self.work, self.work2) if worker is not None]
            for worker in workers:
                if worker.isRunning():
                    worker.request_stop()
            self.pushButton_stp.setEnabled(False)
            self.pushButton_stp_2.setEnabled(False)

            deadline = time.monotonic() + 5.0
            still_running = []
            for worker in workers:
                remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
                if worker.isRunning() and not worker.wait(remaining_ms):
                    still_running.append(worker)

            if still_running:
                QMessageBox.information(
                    self,
                    "Optimization stopping",
                    "The optimization is still stopping. Please wait a moment and close the application again.",
                )
                event.ignore()
            else:
                event.accept()
        else:
            event.ignore()
