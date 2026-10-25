'''Logic of the CaMI GUI that does not depend on Tk: loading files,
selecting the series, parsing user input and computing the measures.'''
import os
import threading

import numpy as np
import pandas as pd

SYMBOLIC_TYPES = ['equal-divs', 'equal-points', 'equal-growth', 'equal-growth-points',
                  'equal-concavity', 'equal-concavity-points']

READERS = {
    '.csv': lambda path: pd.read_csv(path, header=None),
    '.xls': lambda path: pd.read_excel(path, header=None),
    '.xlsx': lambda path: pd.read_excel(path, header=None),
    '.dta': pd.read_stata,
    '.xport': pd.read_sas,
    '.sas7bdat': pd.read_sas,
    '.sav': pd.read_spss,
    '.npy': lambda path: pd.DataFrame(np.load(path)),
    '.json': pd.read_json,
    '.h5': pd.read_hdf,
}

FILE_TYPES = (('All readable types', tuple('*' + ext for ext in READERS)),
              ('Comma-separated values', '*.csv'),
              ('Excel file', ('*.xlsx', '*.xls')),
              ('Stata file', '*.dta'),
              ('SAS file', ('*.xport', '*.sas7bdat')),
              ('SPSS file', '*.sav'),
              ('Numpy array', '*.npy'),
              ('JavaScript Object Notation (JSON)', '*.json'),
              ('Hierarchical Data Format (HDF5)', '*.h5'))


def load_table(path):
    '''Reads a data file into a DataFrame, choosing the reader by file extension.'''
    ext = os.path.splitext(path)[1].lower()
    if ext not in READERS:
        raise ValueError('No data given or data type not supported: %r' % (path,))
    return READERS[ext](path)


def select_series(df, along, index, start=1):
    '''Takes column (or row) `index` from entry `start` on; both are 1-based.'''
    n_rows, n_cols = df.shape
    if along == 'column':
        if not 1 <= index <= n_cols or not 1 <= start <= n_rows:
            raise ValueError('Column %d / start %d outside a table of %d rows x %d columns' % (index, start, n_rows, n_cols))
        values = df.iloc[start - 1:, index - 1]
    elif along == 'row':
        if not 1 <= index <= n_rows or not 1 <= start <= n_cols:
            raise ValueError('Row %d / start %d outside a table of %d rows x %d columns' % (index, start, n_rows, n_cols))
        values = df.iloc[index - 1, start - 1:]
    else:
        raise ValueError("along must be 'column' or 'row'")
    return pd.to_numeric(values, errors='coerce').to_numpy(dtype=float)


def preview(df, max_rows=50, max_cols=10):
    '''Column headers and rows (with 1-based row numbers) for the data preview table.'''
    n_cols = min(df.shape[1], max_cols)
    headers = ['Rows'] + [str(i) for i in range(1, n_cols + 1)]
    rows = [[n] + df.iloc[n - 1, :n_cols].tolist() for n in range(1, min(df.shape[0], max_rows) + 1)]
    return headers, rows


def parse_divisions(text):
    '''Parses comma-separated partition divisions, e.g. "0.2, 0.5".'''
    try:
        values = [float(item) for item in text.split(',')]
    except ValueError:
        raise ValueError('Partition divisions must be numbers separated by commas, got %r' % (text,)) from None
    return values


def compute_measures(x, y, n_symbols=2, symbolic_type='equal-divs', x_divs=None, y_divs=None,
                     lengths=(1, 1, 1), tau=1, delay=0, units='bits', n_surrogates=0, seed=None, progress=None):
    '''Mutual information, CaMI, transfer entropy (both directions) and directionality index.

    tau=None selects tau automatically. With n_surrogates > 0, 'p_values' holds the
    surrogate-test p-value of each measure, and progress(done, total) is called
    after each surrogate (total = 5 * n_surrogates).
    '''
    import cami
    if len(x) != len(y):
        raise ValueError('X and Y must have the same length (X: %d, Y: %d)' % (len(x), len(y)))
    if (x_divs is None) != (y_divs is None) or (x_divs is not None and len(x_divs) != len(y_divs)):
        raise ValueError('X and Y need the same number of divisions')
    params = dict(x_divs=x_divs, y_divs=y_divs, symbolic_type=symbolic_type, n_symbols=n_symbols,
                  symbolic_length=tuple(lengths), tau=tau, delay=delay, units=units)
    results = cami.measures(x, y, **params)  # one pass for all six measures
    if n_surrogates:
        # Y->X tests run with y as the cause: swapping the divisions and negating the
        # delay pairs exactly the same samples as the X->Y call
        reverse = dict(params, x_divs=y_divs, y_divs=x_divs, delay=-delay)
        tests = [('mutual_info', 'mutual_info', x, y, params), ('cami_xy', 'cami', x, y, params),
                 ('cami_yx', 'cami', y, x, reverse), ('te_xy', 'transfer_entropy', x, y, params),
                 ('te_yx', 'transfer_entropy', y, x, reverse)]
        results['p_values'] = {}
        # progress is reported over all five tests: test k covers [k*n, (k+1)*n)
        for k, (name, measure, a, b, kw) in enumerate(tests):
            report = None if progress is None else                 (lambda done, total, k=k: progress(k * n_surrogates + done, len(tests) * n_surrogates))
            results['p_values'][name] = cami.surrogate_test(a, b, measure=measure, n_surrogates=n_surrogates,
                                                            seed=seed, progress=report, **kw)['p_value']
    return results


class Cancelled(Exception):
    '''Raised inside a Job's work when it has been cancelled.'''


class Job:
    '''Runs func(*args, progress=..., **kwargs) in a background thread.

    done/total follow the progress reports, result or error hold the outcome,
    and cancel() makes the next progress report raise Cancelled.
    '''

    def __init__(self, func, *args, **kwargs):
        # done/total/result/error are written by the worker thread and only read by
        # the GUI thread (single attribute assignments, so no lock is needed)
        self.done, self.total = 0, 0
        self.result = self.error = None
        self._cancelled = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(func, args, kwargs), daemon=True)
        self._thread.start()

    def _progress(self, done, total):
        # called by the work after each step: the place where cancellation takes effect
        if self._cancelled.is_set():
            raise Cancelled()
        self.done, self.total = done, total

    def _run(self, func, args, kwargs):
        try:
            if self._cancelled.is_set():
                raise Cancelled()
            self.result = func(*args, progress=self._progress, **kwargs)
        except Exception as error:  # reported to the GUI thread
            self.error = error

    def cancel(self):
        self._cancelled.set()

    def join(self, timeout=None):
        self._thread.join(timeout)

    @property
    def finished(self):
        return not self._thread.is_alive()


def _extension(path):
    return os.path.splitext(path)[1].lower()


def preview_table(path, max_rows=50):
    '''The first rows of a data file, reading no more than needed where the format allows.'''
    ext = _extension(path)
    if ext == '.csv':
        return pd.read_csv(path, header=None, nrows=max_rows)
    if ext in ('.xls', '.xlsx'):
        return pd.read_excel(path, header=None, nrows=max_rows)
    if ext == '.npy':
        data = np.load(path, mmap_mode='r')
        return pd.DataFrame(np.array(data[:max_rows]))
    return load_table(path).head(max_rows)


def load_series(path, along, index, start=1):
    '''Reads only the chosen column (or row) of a data file, from entry start on (1-based).'''
    ext = _extension(path)
    if along not in ('column', 'row'):
        raise ValueError("along must be 'column' or 'row'")
    if ext in ('.csv', '.xls', '.xlsx') and index >= 1:
        reader = pd.read_csv if ext == '.csv' else pd.read_excel
        # parse only the needed column (usecols) or row (skiprows + nrows)
        if along == 'column':
            table = reader(path, header=None, usecols=[index - 1])
        else:
            table = reader(path, header=None, skiprows=index - 1, nrows=1)
            index = 1
        return select_series(table, along, 1 if along == 'column' else index, start)
    if ext == '.npy':
        data = np.load(path, mmap_mode='r')  # memory-mapped: only the selection is read
        if data.ndim == 1:
            data = data[:, None]
        if not 1 <= index <= data.shape[1 if along == 'column' else 0]:
            raise ValueError('%s %d is outside the data (%d rows x %d columns)' % (along.capitalize(), index, *data.shape))
        line = data[:, index - 1] if along == 'column' else data[index - 1]
        if not 1 <= start <= len(line):
            raise ValueError('start %d is outside the selected %s' % (start, along))
        return np.array(line[start - 1:], dtype=float)
    return select_series(load_table(path), along, index, start)


def export_results(results, path):
    '''Writes the measures (and p-values, if computed) to a CSV file.'''
    p_values = results.get('p_values', {})
    table = pd.DataFrame([(name, value, p_values.get(name, np.nan))
                          for name, value in results.items() if name != 'p_values'],
                         columns=['measure', 'value', 'p_value'])
    table.to_csv(path, index=False)
