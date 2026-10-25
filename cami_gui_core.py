'''Logic of the CaMI GUI that does not depend on Tk: loading files,
selecting the series, parsing user input and computing the measures.'''
import os

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
                     lengths=(1, 1, 1), tau=1, delay=0, units='bits', n_surrogates=0, seed=None):
    '''Mutual information, CaMI, transfer entropy (both directions) and directionality index.

    tau=None selects tau automatically. With n_surrogates > 0, 'p_values' holds the
    surrogate-test p-value of each measure.
    '''
    import cami
    if len(x) != len(y):
        raise ValueError('X and Y must have the same length (X: %d, Y: %d)' % (len(x), len(y)))
    if (x_divs is None) != (y_divs is None) or (x_divs is not None and len(x_divs) != len(y_divs)):
        raise ValueError('X and Y need the same number of divisions')
    params = dict(x_divs=x_divs, y_divs=y_divs, symbolic_type=symbolic_type, n_symbols=n_symbols,
                  symbolic_length=tuple(lengths), tau=tau, delay=delay, units=units)
    reverse = dict(params, x_divs=y_divs, y_divs=x_divs, delay=-delay)
    cami_xy, cami_yx = cami.cami(x, y, two_sided=True, **params)
    te_xy, te_yx = cami.transfer_entropy(x, y, two_sided=True, **params)
    results = {
        'mutual_info': cami.mutual_info(x, y, **params),
        'cami_xy': cami_xy,
        'cami_yx': cami_yx,
        'te_xy': te_xy,
        'te_yx': te_yx,
        'directionality': cami_xy - cami_yx,
    }
    if n_surrogates:
        def p_value(measure, a, b, kw):
            return cami.surrogate_test(a, b, measure=measure, n_surrogates=n_surrogates, seed=seed, **kw)['p_value']
        results['p_values'] = {
            'mutual_info': p_value('mutual_info', x, y, params),
            'cami_xy': p_value('cami', x, y, params),
            'cami_yx': p_value('cami', y, x, reverse),
            'te_xy': p_value('transfer_entropy', x, y, params),
            'te_yx': p_value('transfer_entropy', y, x, reverse),
        }
    return results


def export_results(results, path):
    '''Writes the measures (and p-values, if computed) to a CSV file.'''
    p_values = results.get('p_values', {})
    table = pd.DataFrame([(name, value, p_values.get(name, np.nan))
                          for name, value in results.items() if name != 'p_values'],
                         columns=['measure', 'value', 'p_value'])
    table.to_csv(path, index=False)
