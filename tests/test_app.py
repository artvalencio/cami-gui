import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_import_has_no_side_effects(tmp_path):
    # importing must not open windows or start the main loop, from any working directory
    code = 'import sys; sys.path.insert(0, %r); import cami_gui' % REPO
    result = subprocess.run([sys.executable, '-c', code], cwd=tmp_path, timeout=20, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.fixture
def app():
    tk = pytest.importorskip('tkinter')
    import cami_gui
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('no display')
    root.withdraw()
    yield cami_gui.CamiApp(root)
    root.destroy()


def test_main_window_builds(app):
    assert app.master.title() == 'CaMI'
    assert app.n_symbols.get() == '2'


def test_window_builds_from_another_working_directory(tmp_path, monkeypatch):
    tk = pytest.importorskip('tkinter')
    import cami_gui
    monkeypatch.chdir(tmp_path)
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('no display')
    root.withdraw()
    try:
        cami_gui.CamiApp(root)
    finally:
        root.destroy()


def test_units_menu_offers_every_unit(app):
    assert app.unit.get() == 'bits'
    menu = app.master.nametowidget(app.unit_menu['menu'])
    assert [menu.entrycget(i, 'label') for i in range(menu.index('end') + 1)] == ['bits', 'nat', 'ban']


def test_file_dialog_only_offers_supported_types():
    import cami_gui
    assert '*.sql' not in str(cami_gui.FILE_TYPES)


@pytest.fixture
def table():
    import numpy as np
    import pandas as pd
    return pd.DataFrame(np.arange(12, dtype=float).reshape(3, 4))


def test_selecting_a_row(app, table):
    app.data['x'] = table
    app.row_or_column.set(1)
    app.sel_data_row.set('2')
    app.sel_start.set('2')
    app.apply_selection('x')
    assert app.series['x'].tolist() == [5.0, 6.0, 7.0]


def test_selecting_a_column(app, table):
    app.data['y'] = table
    app.row_or_column.set(2)
    app.sel_data_column.set('3')
    app.sel_start.set('1')
    app.apply_selection('y')
    assert app.series['y'].tolist() == [2.0, 6.0, 10.0]


def test_calculation_errors_show_the_real_cause(app, monkeypatch):
    import numpy as np
    import cami_gui
    shown = []
    monkeypatch.setattr(cami_gui, 'showerror', lambda **kw: shown.append(kw['message']))
    app.series['x'], app.series['y'] = np.random.rand(100), np.random.rand(90)
    app.calc_cami()
    assert 'X: 100' in shown[0] and 'Y: 90' in shown[0]


def test_calculation_shows_results(app, monkeypatch):
    import numpy as np
    import cami_gui
    import cami_gui_core
    results = []
    monkeypatch.setattr(app, 'show_results', results.append)
    x = np.random.default_rng(0).random(2000)
    app.series['x'], app.series['y'] = x, np.roll(x, 1)
    app.div_type.set(3)
    app.xdiv_vals.set('0.5')
    app.ydiv_vals.set('0.5')
    app.calc_cami()
    assert results == [cami_gui_core.compute_measures(x, np.roll(x, 1), x_divs=[0.5], y_divs=[0.5])]
