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


@pytest.fixture
def table_file(table, tmp_path):
    path = tmp_path / 'table.csv'
    table.to_csv(path, header=False, index=False)
    return str(path)


def test_selecting_a_row(app, table, table_file):
    app.files['x'].set(table_file)
    app.row_or_column.set(1)
    app.sel_data_row.set('2')
    app.sel_start.set('2')
    app.apply_selection('x')
    assert app.series['x'].tolist() == [5.0, 6.0, 7.0]


def test_selecting_a_column(app, table, table_file):
    app.files['y'].set(table_file)
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


@pytest.fixture
def captured(app, monkeypatch):
    """Records the keyword arguments of compute_measures and skips the results window."""
    import numpy as np
    import cami_gui
    calls = []

    def fake_compute(x, y, **kwargs):
        calls.append(kwargs)
        return {'mutual_info': 0.0, 'cami_xy': 0.0, 'cami_yx': 0.0, 'te_xy': 0.0, 'te_yx': 0.0, 'directionality': 0.0}

    monkeypatch.setattr(cami_gui.core, 'compute_measures', fake_compute)
    monkeypatch.setattr(app, 'show_results', lambda results: None)
    app.series['x'] = app.series['y'] = np.random.rand(100)
    return calls


def test_any_symbolic_type_can_be_chosen(app, captured):
    app.div_type.set(1)
    app.symbolic_type.set('equal-growth-points')
    app.calc_cami()
    assert captured[-1]['symbolic_type'] == 'equal-growth-points'
    assert captured[-1]['x_divs'] is None


def test_automatic_tau_option(app, captured):
    app.calc_cami()
    assert captured[-1]['tau'] == 1
    app.auto_tau.set(True)
    app.calc_cami()
    assert captured[-1]['tau'] is None


def test_significance_option(app, captured):
    app.calc_cami()
    assert captured[-1]['n_surrogates'] == 0
    app.significance.set(True)
    app.n_surrogates.set('19')
    app.calc_cami()
    app.job.join(timeout=30)
    app.poll_job()
    assert captured[-1]['n_surrogates'] == 19


def test_results_window_shows_p_values(app):
    import tkinter
    results = {'mutual_info': 0.1, 'cami_xy': 0.9, 'cami_yx': 0.01, 'te_xy': 0.8, 'te_yx': 0.0,
               'directionality': 0.89, 'p_values': {'mutual_info': 0.5, 'cami_xy': 0.01, 'cami_yx': 0.6,
                                                     'te_xy': 0.01, 'te_yx': 0.7}}
    window = app.show_results(results)
    texts = ' '.join(str(w.cget('text')) for w in window.winfo_children() if 'text' in w.keys())
    assert 'p = 0.010' in texts and 'p = 0.700' in texts
    assert isinstance(window, tkinter.Toplevel)


def test_export_results(app, monkeypatch, tmp_path):
    import numpy as np
    import pandas as pd
    import cami_gui
    path = tmp_path / 'out.csv'
    monkeypatch.setattr(cami_gui.fd, 'asksaveasfilename', lambda **kw: str(path))
    monkeypatch.setattr(app, 'show_results', lambda results: None)
    x = np.random.default_rng(0).random(500)
    app.series['x'], app.series['y'] = x, np.roll(x, 1)
    app.calc_cami()
    app.export_results()
    assert pd.read_csv(path)['measure'].tolist()[:2] == ['mutual_info', 'cami_xy']


@pytest.fixture
def coupled_series(app):
    import numpy as np
    x = np.random.default_rng(0).random(3000)
    app.series['x'], app.series['y'] = x, np.roll(x, 1)
    return app


def test_significance_runs_in_the_background_with_progress(coupled_series, monkeypatch):
    app = coupled_series
    shown = []
    monkeypatch.setattr(app, 'show_results', shown.append)
    app.significance.set(True)
    app.n_surrogates.set('19')
    app.calc_cami()
    assert app.job is not None
    assert app.progress_window.winfo_exists()
    app.job.join(timeout=60)
    app.poll_job()
    assert app.job is None
    assert shown and shown[0]['p_values']['cami_xy'] == pytest.approx(1 / 20)
    assert app.last_results is shown[0]


def test_significance_can_be_cancelled(coupled_series, monkeypatch):
    import cami_gui
    app = coupled_series
    shown, errors = [], []
    monkeypatch.setattr(app, 'show_results', shown.append)
    monkeypatch.setattr(cami_gui, 'showerror', lambda **kw: errors.append(kw))
    app.significance.set(True)
    app.n_surrogates.set('1000000')
    app.calc_cami()
    app.cancel_job()
    job = app.job
    job.join(timeout=60)
    app.poll_job()
    assert job.finished and shown == [] and errors == []
    assert app.job is None


def test_loading_keeps_only_a_preview(app, tmp_path, monkeypatch):
    import numpy as np
    import pandas as pd
    import cami_gui
    path = tmp_path / 'long.csv'
    pd.DataFrame(np.random.rand(500, 3)).to_csv(path, header=False, index=False)
    monkeypatch.setattr(cami_gui.fd, 'askopenfilename', lambda **kw: str(path))
    monkeypatch.setattr(app, 'pop_table', lambda df, x_or_y: None)
    app.load_data('x')
    assert app.data['x'].shape == (50, 3)
    app.row_or_column.set(2)
    app.sel_data_column.set('2')
    app.sel_start.set('1')
    app.apply_selection('x')
    assert len(app.series['x']) == 500
