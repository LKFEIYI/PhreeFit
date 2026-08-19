# PhreeFit refactored source

This directory is an isolated refactoring of `src`. The original source files
are not imported or modified.

## Layout

- `PhreeFit.py`: application entry point
- `main_window.py`: main-window orchestration, signal wiring, and results handling
- `controllers.py`: fitted-parameter state and optimization worker lifecycle
- `io_service.py`: database/CSV/configuration/result/JSON file I/O
- `ui/main_window_ui.py`: widget construction and native Qt layouts
- `workers.py`: background optimization thread
- `table_model.py`: lightweight data-table-to-Qt model
- `main_cal.py`: calculation code copied from the current `src/main_cal.py`

## Run

From the project root with the `phreefit` environment active:

```bash
python -m src_new
```

or:

```bash
python src_new/PhreeFit.py
```

For packaging, use `src_new/PhreeFit.py` as the entry script. If `main_cal.py`
is compiled with Cython, place the resulting extension module inside
`src_new` so the package-relative import resolves it.

The application menu contains `History > Save settings` and
`History > Load settings`. A settings file stores shared configuration plus
separate `titration` and `advanced` sections. Loading a file restores the UI
and reloads the referenced database and data files. The save dialog defaults
to the current output directory.

The Titration and Advanced pages use `QSplitter`, `QScrollArea`, and Qt layout
managers rather than scaling fixed widget coordinates. Widget object names are
unchanged so existing settings files remain compatible.
