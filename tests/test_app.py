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
