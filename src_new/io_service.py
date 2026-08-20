"""File and configuration I/O for PhreeFit.

Functions in this module do not open dialogs and do not access UI widgets.  The
window/controller decides which path to use and how an error is shown.
"""

from dataclasses import dataclass
import csv
import json
import os
import tempfile
import time
from typing import Any, Optional

import numpy as np
from PySide6.QtCore import QStandardPaths

from . import main_cal as mc


SETTINGS_FORMAT = "PhreeFit settings"
SETTINGS_VERSION = 1


class DataColumn:
    """Small column view with the subset of the former Series API we need."""

    def __init__(self, values):
        self._values = list(values)

    @property
    def values(self):
        return np.asarray(self._values)

    def to_list(self):
        return list(self._values)

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def __getitem__(self, index):
        return self._values[index]


class DataTable:
    """A lightweight two-dimensional table used by IO, grouping and Qt."""

    def __init__(self, columns, rows):
        self.columns = list(columns)
        self.rows = [list(row) for row in rows]
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("CSV rows do not match the number of columns")

    @property
    def shape(self):
        return len(self.rows), len(self.columns)

    def value(self, row, column):
        return self.rows[row][column]

    def column(self, name):
        try:
            column_index = self.columns.index(name)
        except ValueError as error:
            raise KeyError(name) from error
        return DataColumn(row[column_index] for row in self.rows)

    def __getitem__(self, name):
        return self.column(name)

    def rename_columns(self, columns):
        if len(columns) != len(self.columns):
            raise ValueError("New column count does not match table")
        self.columns = list(columns)

    def pop_column(self, name):
        column_index = self.columns.index(name)
        self.columns.pop(column_index)
        values = []
        for row in self.rows:
            values.append(row.pop(column_index))
        return DataColumn(values)

    def groupby(self, name):
        return GroupedData(self, name)


class GroupedData:
    """Ordered groups compatible with the accesses used by main_cal.py."""

    def __init__(self, table, column_name):
        self._table = table
        try:
            column_index = table.columns.index(column_name)
        except ValueError as error:
            raise KeyError(column_name) from error
        self.groups = {}
        for row_index, row in enumerate(table.rows):
            self.groups.setdefault(row[column_index], []).append(row_index)

    def get_group(self, key):
        if key not in self.groups:
            raise KeyError(key)
        rows = [self._table.rows[index] for index in self.groups[key]]
        return DataTable(self._table.columns, rows)


@dataclass
class ExperimentData:
    table: DataTable
    ph: np.ndarray
    mix_data: Any
    errors: Optional[np.ndarray]
    multi_is: bool


def read_database(path: str) -> str:
    with open(path, "r", encoding="UTF-8") as database_file:
        return database_file.read()


def _parse_csv_value(value):
    value = value.strip()
    if value.lower() in {"", "nan", "na", "n/a", "null", "none"}:
        return None
    try:
        return float(value)
    except ValueError:
        return value


def _read_csv(path: str):
    with open(path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            columns = [column.strip() for column in next(reader)]
        except StopIteration as error:
            raise ValueError("The data file is empty") from error
        raw_rows = []
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(columns):
                raise ValueError(f"CSV row {row_number} has {len(row)} values; expected {len(columns)}")
            raw_rows.append([_parse_csv_value(value) for value in row])

    if not columns:
        raise ValueError("The data file has no columns")
    nonempty_columns = [
        index for index in range(len(columns))
        if any(row[index] is not None for row in raw_rows)
    ]
    columns = [columns[index] for index in nonempty_columns]
    rows = [
        [row[index] for index in nonempty_columns]
        for row in raw_rows
        if all(row[index] is not None for index in nonempty_columns)
    ]
    table = DataTable(columns, rows)
    errors = table.pop_column("errors").values if "errors" in table.columns else None
    if len(table.columns) not in (2, 3):
        raise ValueError("The data file must contain 2 or 3 data columns")
    return table, errors


def read_titration_data(path: str) -> ExperimentData:
    table, errors = _read_csv(path)
    multi_is = len(table.columns) == 3
    table.rename_columns(["pH", "volume", "IS"] if multi_is else ["pH", "volume"])
    mix_data = table.groupby("IS") if multi_is else table["volume"].values
    return ExperimentData(
        table=table,
        ph=table["pH"].values,
        mix_data=mix_data,
        errors=errors,
        multi_is=multi_is,
    )


def read_advanced_data(path: str, titration: bool) -> ExperimentData:
    table, errors = _read_csv(path)
    multi_is = len(table.columns) == 3
    if titration:
        second_column = "volume"
        ph = np.asarray([row[0] for row in table.rows])
        mix_data = np.asarray([row[1] for row in table.rows])
    else:
        second_column = "amounts"
        ph = np.asarray([row[1] for row in table.rows])
        mix_data = np.asarray([row[0] for row in table.rows])
    table.rename_columns(["pH", second_column, "IS"] if multi_is else ["pH", second_column])
    if multi_is:
        mix_data = table.groupby("IS")
    return ExperimentData(
        table=table,
        ph=ph,
        mix_data=mix_data,
        errors=errors,
        multi_is=multi_is,
    )


def json_value(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    return value


def _restore_parameter(value):
    return tuple(value) if isinstance(value, list) else value


def serialize_surface(surface):
    reactions = []
    for equation, values in surface.surface_reactions.items():
        reactions.append({
            "equation": equation,
            "k": json_value(values[0]),
            "z1": json_value(values[1]),
            "z0d": bool(values[2]),
            "ztotal": json_value(values[3]),
            "k_initial": json_value(values[4]),
            "z1_initial": json_value(values[5]),
        })
    return {
        "surface_name": surface.surface_name,
        "surface_formula": surface.surface_mp,
        "area": json_value(surface.surface_area),
        "mass": json_value(surface.surface_mass),
        "sites": json_value(surface.surface_sites),
        "c1": json_value(surface.surface_C1),
        "c2": json_value(surface.surface_C2),
        "initial": json_value(surface.sfinitial),
        "reactions": reactions,
    }


def deserialize_surface(settings):
    initial = settings.get("initial") or [0, 1, 1]
    if len(initial) < 3:
        initial = list(initial) + [1] * (3 - len(initial))
    surface = mc.SurfaceSpecies2()
    surface.add_surface(
        surfacename=settings.get("surface_name"),
        surface_ms=settings.get("surface_formula"),
        sites=_restore_parameter(settings.get("sites")),
        area=settings.get("area"),
        mass=settings.get("mass"),
        c1=_restore_parameter(settings.get("c1")),
        c2=_restore_parameter(settings.get("c2")),
        sites_initial=initial[0],
        c1_initial=initial[1],
        c2_initial=initial[2],
    )
    for reaction in settings.get("reactions", []):
        surface.add_reactions(
            reactions=reaction["equation"],
            k=_restore_parameter(reaction.get("k")),
            z1=_restore_parameter(reaction.get("z1")),
            z0d=bool(reaction.get("z0d", True)),
            ztotal=reaction.get("ztotal", 0),
            k_initial=reaction.get("k_initial", 0),
            z1_initial=reaction.get("z1_initial", 1),
        )
    return surface


def save_settings_file(path, settings):
    target = os.path.abspath(path)
    target_directory = os.path.dirname(target)
    os.makedirs(target_directory, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=target_directory,
                prefix=".phreefit-settings-", suffix=".tmp", delete=False) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(settings, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
        os.replace(temporary_path, target)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def load_settings_file(path):
    with open(path, "r", encoding="utf-8") as settings_file:
        settings = json.load(settings_file)
    if not isinstance(settings, dict):
        raise ValueError("The selected file is not a PhreeFit settings file")

    recognizable_sections = {"common", "titration", "advanced"}
    if not recognizable_sections.intersection(settings):
        raise ValueError("The selected file is not a PhreeFit settings file")

    format_name = settings.get("format")
    if format_name not in (None, SETTINGS_FORMAT):
        raise ValueError("The selected file is not a PhreeFit settings file")

    version = settings.get("version", SETTINGS_VERSION)
    try:
        version = int(version)
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid PhreeFit settings version") from error
    if version != SETTINGS_VERSION:
        raise ValueError("Unsupported PhreeFit settings version")

    normalized = dict(settings)
    normalized["format"] = SETTINGS_FORMAT
    normalized["version"] = SETTINGS_VERSION
    for section in recognizable_sections:
        value = normalized.get(section)
        if value is None:
            normalized[section] = {}
        elif not isinstance(value, dict):
            raise ValueError(f"Invalid '{section}' section in PhreeFit settings")
    return normalized


class ConfigFile:
    def __init__(self):
        self.data_directory = None
        self.database_directory = None
        self.output_directory = None
        config_directory = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        if not config_directory:
            config_directory = os.path.join(os.path.expanduser("~"), ".phreefit")
        os.makedirs(config_directory, exist_ok=True)
        self.config_file = os.path.join(config_directory, "config")

    @staticmethod
    def default_directories():
        user_directory = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        if not user_directory or not os.path.isdir(user_directory):
            user_directory = os.path.expanduser("~")
        output_directory = os.path.join(user_directory, "PhreeFit")
        os.makedirs(output_directory, exist_ok=True)
        return [user_directory, user_directory, output_directory]

    def create_config_file(self):
        self.update_config_file(self.default_directories())

    def load_config_file(self):
        if not os.path.isfile(self.config_file):
            self.create_config_file()
        with open(self.config_file, "r", encoding="utf-8") as config_stream:
            config_content = config_stream.readlines()

        if len(config_content) != 3:
            self.create_config_file()
            with open(self.config_file, "r", encoding="utf-8") as config_stream:
                config_content = config_stream.readlines()

        defaults = self.default_directories()
        config_changed = False
        for index in range(3):
            if not os.path.isdir(config_content[index].strip()):
                config_content[index] = defaults[index]
                config_changed = True
        self.data_directory = config_content[0].strip()
        self.database_directory = config_content[1].strip()
        self.output_directory = config_content[2].strip()
        if config_changed:
            self.update_config_file([
                self.data_directory,
                self.database_directory,
                self.output_directory,
            ])

    def update_config_file(self, path_list: list):
        with open(self.config_file, "w", encoding="utf-8") as config_stream:
            config_stream.write(path_list[0] + "\n")
            config_stream.write(path_list[1] + "\n")
            config_stream.write(path_list[2] + "\n")


def write_log(log_info: str, output_path: str):
    with open(os.path.join(output_path, "phreefit_log.txt"), "a", encoding="utf-8") as log_file:
        log_file.write("\n" + time.ctime() + "\n")
        log_file.write(log_info + "\n")


def write_results(exp_data, model_res, speciation, output_path: str):
    with open(os.path.join(output_path, "phreefit_results.txt"), "a", encoding="utf-8") as result_file:
        result_file.write("\n" + time.ctime() + "\n")
        result_file.write("Experimental data\tModeled data\n")
        for index in range(len(exp_data)):
            result_file.write(str(exp_data[index]) + "\t")
            result_file.write(str(model_res[index]) + "\n")
        result_file.write("Surface Speciation:\n")
        for species in np.array(speciation, dtype=str):
            result_file.write("\t".join(species[1:]) + "\n")
