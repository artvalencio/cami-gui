import numpy as np
import pandas as pd
import pytest

import cami
import cami_gui_core as core


@pytest.fixture
def table():
    """Header row, then 60 rows x 3 columns of numbers."""
    rng = np.random.default_rng(0)
    values = rng.random((60, 3))
    return pd.DataFrame([['a', 'b', 'c']] + values.tolist()), values


# --- loading files -----------------------------------------------------------

def test_load_csv_without_header(tmp_path):
    path = tmp_path / 'data.csv'
    path.write_text('1,2\n3,4\n')
    pd.testing.assert_frame_equal(core.load_table(str(path)), pd.DataFrame([[1, 2], [3, 4]]))


def test_load_is_case_insensitive_and_reads_npy(tmp_path):
    path = tmp_path / 'DATA.NPY'
    with open(path, 'wb') as fh:  # np.save(path) would append '.npy'
        np.save(fh, np.arange(6).reshape(3, 2))
    np.testing.assert_array_equal(core.load_table(str(path)).values, np.arange(6).reshape(3, 2))


def test_load_json(tmp_path):
    path = tmp_path / 'data.json'
    pd.DataFrame({'x': [1.0, 2.0]}).to_json(path)
    assert core.load_table(str(path))['x'].tolist() == [1.0, 2.0]


@pytest.mark.parametrize('name', ['data.sql', 'data.txt', ''])
def test_unsupported_files_are_rejected(name):
    with pytest.raises(ValueError, match='not supported'):
        core.load_table(name)


# --- selecting the series ----------------------------------------------------

def test_select_column_after_header(table):
    df, values = table
    np.testing.assert_array_equal(core.select_series(df, 'column', 2, start=2), values[:, 1])


def test_select_row(table):
    df, values = table
    # row 3 of the file, from its 2nd entry on
    np.testing.assert_array_equal(core.select_series(df, 'row', 3, start=2), values[1, 1:])


def test_select_works_with_named_columns():
    df = pd.DataFrame({'time': [1, 2, 3], 'value': [0.1, 0.2, 0.3]})
    np.testing.assert_array_equal(core.select_series(df, 'column', 2, start=1), [0.1, 0.2, 0.3])


@pytest.mark.parametrize('along,index,start', [('column', 4, 1), ('row', 0, 1), ('column', 1, 100), ('diagonal', 1, 1)])
def test_invalid_selection_is_rejected(table, along, index, start):
    with pytest.raises(ValueError):
        core.select_series(table[0], along, index, start)


# --- table preview -----------------------------------------------------------

@pytest.mark.parametrize('n_rows,n_cols', [(5, 2), (9, 9), (10, 10), (80, 15)])
def test_preview_shows_all_rows_and_columns_up_to_limits(n_rows, n_cols):
    df = pd.DataFrame(np.arange(n_rows * n_cols).reshape(n_rows, n_cols))
    headers, rows = core.preview(df, max_rows=50, max_cols=10)
    assert headers == ['Rows'] + [str(i) for i in range(1, min(n_cols, 10) + 1)]
    assert len(rows) == min(n_rows, 50)
    assert rows[-1][0] == min(n_rows, 50)
    assert rows[0][1:] == df.iloc[0, :10].tolist()


# --- partition divisions -----------------------------------------------------

def test_parse_divisions():
    assert core.parse_divisions(' 0.2, 0.5 ,1e-1') == [0.2, 0.5, 0.1]


@pytest.mark.parametrize('text', ['', 'abc', '0.2,,0.4'])
def test_invalid_divisions_are_rejected(text):
    with pytest.raises(ValueError, match='division'):
        core.parse_divisions(text)


# --- calculation -------------------------------------------------------------

@pytest.fixture
def xy():
    rng = np.random.default_rng(1)
    x = rng.random(3000)
    return x, np.roll(x, 1)


def test_compute_measures_matches_cami(xy):
    x, y = xy
    res = core.compute_measures(x, y, n_symbols=3, symbolic_type='equal-points', lengths=(2, 1, 1), tau=1, delay=0, units='bits')
    cami_xy, cami_yx = cami.cami(x, y, n_symbols=3, symbolic_type='equal-points', symbolic_length=(2, 1, 1), two_sided=True)
    te_xy, te_yx = cami.transfer_entropy(x, y, n_symbols=3, symbolic_type='equal-points', symbolic_length=(2, 1, 1), two_sided=True)
    assert res == pytest.approx({
        'mutual_info': cami.mutual_info(x, y, n_symbols=3, symbolic_type='equal-points', symbolic_length=(2, 1, 1)),
        'cami_xy': cami_xy, 'cami_yx': cami_yx, 'te_xy': te_xy, 'te_yx': te_yx,
        'directionality': cami_xy - cami_yx})


def test_compute_measures_with_user_divisions(xy):
    x, y = xy
    res = core.compute_measures(x, y, x_divs=[0.5], y_divs=[0.5])
    assert res['cami_xy'] == pytest.approx(cami.cami(x, y, x_divs=[0.5], y_divs=[0.5]))


def test_division_counts_must_match(xy):
    with pytest.raises(ValueError, match='same number of divisions'):
        core.compute_measures(*xy, x_divs=[0.3, 0.6], y_divs=[0.5])


def test_length_mismatch_reports_both_lengths(xy):
    x, y = xy
    with pytest.raises(ValueError, match='3000.*2990'):
        core.compute_measures(x, y[:2990])


# --- features ----------------------------------------------------------------

def test_every_symbolic_type_is_offered(xy):
    assert core.SYMBOLIC_TYPES == ['equal-divs', 'equal-points', 'equal-growth', 'equal-growth-points',
                                   'equal-concavity', 'equal-concavity-points']
    for symbolic_type in core.SYMBOLIC_TYPES:
        assert np.isfinite(core.compute_measures(*xy, symbolic_type=symbolic_type)['cami_xy'])


def test_automatic_tau(xy):
    x, y = xy
    assert core.compute_measures(x, y, tau=None)['cami_xy'] == pytest.approx(cami.cami(x, y, tau=None))


def test_significance_p_values(xy):
    x, y = xy
    res = core.compute_measures(x, y, n_surrogates=19, seed=0)
    assert set(res['p_values']) == {'mutual_info', 'cami_xy', 'cami_yx', 'te_xy', 'te_yx'}
    assert res['p_values']['cami_xy'] == pytest.approx(1 / 20)
    assert res['p_values']['cami_yx'] > 0.05
    assert 'p_values' not in core.compute_measures(x, y)


def test_results_are_exported_to_csv(xy, tmp_path):
    res = core.compute_measures(*xy, n_surrogates=4, seed=0)
    path = tmp_path / 'results.csv'
    core.export_results(res, str(path))
    table = pd.read_csv(path, index_col='measure')
    assert table.loc['cami_xy', 'value'] == pytest.approx(res['cami_xy'])
    assert table.loc['te_yx', 'p_value'] == pytest.approx(res['p_values']['te_yx'])
    assert table.loc['directionality', 'value'] == pytest.approx(res['directionality'])


# --- performance ---------------------------------------------------------------

def test_progress_is_reported_over_all_significance_tests(xy):
    calls = []
    core.compute_measures(*xy, n_surrogates=4, seed=0, progress=lambda done, total: calls.append((done, total)))
    assert calls == [(k, 20) for k in range(1, 21)]


def test_job_runs_in_the_background_and_reports_progress(xy):
    job = core.Job(core.compute_measures, *xy, n_surrogates=4, seed=0)
    job.join(timeout=30)
    assert job.finished and job.error is None
    assert job.result['p_values']['cami_xy'] == pytest.approx(1 / 5)
    assert (job.done, job.total) == (20, 20)


def test_job_can_be_cancelled(xy):
    job = core.Job(core.compute_measures, *xy, n_surrogates=10**6, seed=0)
    job.cancel()
    job.join(timeout=30)
    assert job.finished and job.result is None and isinstance(job.error, core.Cancelled)


@pytest.fixture(scope='module')
def big_csv(tmp_path_factory):
    rng = np.random.default_rng(0)
    values = rng.random((200_000, 8))
    path = tmp_path_factory.mktemp('data') / 'big.csv'
    pd.DataFrame(values).to_csv(path, header=False, index=False)
    return str(path), values


def test_preview_reads_only_the_first_rows(big_csv):
    path, values = big_csv
    preview = core.preview_table(path, max_rows=50)
    assert preview.shape == (50, 8)
    np.testing.assert_allclose(preview.values, values[:50])


@pytest.mark.parametrize('along,index,start', [('column', 3, 1), ('column', 8, 10), ('row', 5, 2)])
def test_load_series_reads_only_the_selection(big_csv, along, index, start):
    path, values = big_csv
    expected = values[start - 1:, index - 1] if along == 'column' else values[index - 1, start - 1:]
    np.testing.assert_allclose(core.load_series(path, along, index, start), expected)


@pytest.mark.parametrize('suffix', ['.npy', '.json'])
def test_load_series_other_formats(tmp_path, suffix):
    values = np.arange(30.0).reshape(10, 3)
    path = str(tmp_path / ('data' + suffix))
    if suffix == '.npy':
        np.save(path, values)
    else:
        pd.DataFrame(values).to_json(path)
    np.testing.assert_allclose(core.load_series(path, 'column', 2, 3), values[2:, 1])
    np.testing.assert_allclose(core.preview_table(path).values, values)


@pytest.mark.slow
def test_preview_and_column_reading_are_fast(big_csv):
    import time
    path, __ = big_csv
    start = time.perf_counter()
    core.preview_table(path)
    core.load_series(path, 'column', 2, 1)
    full = time.perf_counter() - start
    start = time.perf_counter()
    core.load_table(path)
    assert full < time.perf_counter() - start


@pytest.mark.slow
def test_compute_measures_time(xy):
    import time
    x = np.random.default_rng(0).random(10**5)
    y = 0.6 * np.roll(x, 1) + 0.4 * np.random.default_rng(1).random(10**5)
    core.compute_measures(x, y, lengths=(2, 2, 1))
    start = time.perf_counter()
    core.compute_measures(x, y, lengths=(2, 2, 1))
    assert time.perf_counter() - start < 0.08
    start = time.perf_counter()
    core.compute_measures(x, y, lengths=(2, 2, 1), n_surrogates=99, seed=0)
    assert time.perf_counter() - start < 2.0
