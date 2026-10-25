"""Benchmarks for the GUI computation (uses the sibling cami-python checkout if present).

    python benchmarks/run.py LABEL
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SIBLING = os.path.join(REPO, '..', 'cami-python')
sys.path[:0] = [REPO] + ([os.path.abspath(SIBLING)] if os.path.isdir(SIBLING) else [])
import cami_gui_core as core  # noqa: E402

RESULTS = os.path.join(HERE, 'results.json')


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else 'latest'
    x = np.random.default_rng(0).random(10**5)
    y = 0.6 * np.roll(x, 1) + 0.4 * np.random.default_rng(1).random(10**5)
    cases = {
        'compute_measures N=1e5 L=(2,2,1)': lambda: core.compute_measures(x, y, lengths=(2, 2, 1)),
        'compute_measures + 99 surrogates': lambda: core.compute_measures(x, y, lengths=(2, 2, 1), n_surrogates=99, seed=0),
    }
    stored = json.load(open(RESULTS)) if os.path.exists(RESULTS) else {}
    baseline = stored.get('baseline', {})
    results = {}
    for name, func in cases.items():
        func()
        times = []
        for __ in range(3):
            start = time.perf_counter()
            func()
            times.append(time.perf_counter() - start)
        results[name] = {'time_ms': round(min(times) * 1000, 2)}
        base = baseline.get(name)
        compare = '  (baseline %9.1f ms, %5.1fx faster)' % (base['time_ms'], base['time_ms'] / results[name]['time_ms']) \
            if base and label != 'baseline' else ''
        print('%-36s %9.1f ms%s' % (name, results[name]['time_ms'], compare), flush=True)
    stored[label] = results
    with open(RESULTS, 'w') as fh:
        json.dump(stored, fh, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
