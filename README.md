# CaMI GUI

Graphical user interface for [CaMI-Python](https://github.com/artvalencio/cami-python):
a user-friendly way to measure the mutual information, transfer entropy, Causal
Mutual Information and directionality index between two time-series, with
optional significance tests.

![Main window and results window (example values)](https://github.com/artvalencio/cami-gui/blob/main/full_layout.jpg?raw=true)

## Requirements and installation

- Python 3.9 or later, with Tk (included in the python.org installers; on Linux, e.g. `sudo apt install python3-tk`)
- [CaMI-Python](https://github.com/artvalencio/cami-python) 1.5.0 or later
- numpy, pandas and Pillow; reading Excel files also needs openpyxl, and HDF5 files need tables

All at once:

```
pip install -r requirements.txt
```

## Running

```
python cami_gui.py
```

1. **Load the data.** Use *Load first variable data (X)* and *Load second
   variable data (Y)*. Readable files are csv, Excel, Stata, SAS, SPSS, npy, json
   and HDF5. A preview of the first rows opens: choose the row or column holding
   the series and the row/column where its numeric values start (e.g. 2 to skip
   a header). Only the preview and the chosen series are read from the file.
2. **Choose the encoding.** Set the number of symbols and either an automatic
   partition (equal-width or equal-points, on the values, their growth or their
   concavity) or your own divisions (comma-separated, increasing).
3. **Choose the parameters.** Symbolic lengths (past of X, past of Y, future of
   Y), tau (or automatic: first zero of the auto-correlation), transmission
   delay (Y responds to X after this many steps) and units (bits, nat or ban).
4. **Optionally test significance.** Tick *surrogate test* and choose the
   number of surrogates. Each measure gets a p-value from surrogate data in
   which the cause is shifted in time. These tests run in the background with a
   progress bar and a Cancel button.
5. **Calculate.** The results window shows the measures (and p-values) and can
   export them to a CSV file.

## Measures

With symbolic words of the past of X, the past of Y and the future of Y:

- Mutual information: MI = I(X_past ; Y_past)
- Causal Mutual Information: CaMI(X→Y) = I(X_past ; Y_past, Y_future)
- Transfer entropy: TE(X→Y) = CaMI(X→Y) − MI
- Directionality index: DI = CaMI(X→Y) − CaMI(Y→X), positive when information flows from X to Y

## Performance

For 10^5 points, calculating all measures takes about 3 ms (previously about
180 ms). With 99 surrogates the significance tests take about 0.6 s (previously
about 15 s, with the window frozen).

## Code structure and tests

- `cami_gui.py`: the Tk window (`CamiApp`); it only collects input and shows results.
- `cami_gui_core.py`: file loading, series selection, input parsing, the
  calculation and the background `Job`, independent of Tk.

```
pip install pytest
pytest              # window tests are skipped without a display
pytest -m slow      # timing tests
```

## Licence and acknowledgements

Open source licence: GNU GPL v3 (see `LICENSE`).

Developer: Arthur Valencio, Institute of Computing/University of Campinas and Research, Innovation and Dissemination Center for Neuromathematics

Funding: FAPESP (S. Paulo Research Foundation), Brazil (2018-onwards).

Acknowledgements: Arthur Valencio is supported by the FAPESP grant 2018/09900-8 and acknowledges this work as part of the activities of the FAPESP Research Innovation and Dissemination Center for Neuromathematics (grant 2013/07699-0, S. Paulo Research Foundation).

```
CaMI GUI: Graphical User Interface for CaMI-Python

Copyright (C) 2022  Arthur Valencio

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

## Contact

Arthur Valencio — e-mail: arthuric(at)unicamp.br

Institute of Computing, Unicamp, Av. Albert Einstein, 1251, Cidade Universitaria, Campinas/SP, Brazil, CEP 13083-852
