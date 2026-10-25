# cami-gui
Graphical User Interface for CaMI-Python: User-friendly way of measuring mutual information, transfer entropy, causal mutual information and directionality index

![Layout of the software](https://github.com/artvalencio/cami-gui/blob/main/full_layout.jpg?raw=true)

------------------------------------------------------------------------------

Requirements:

- CaMI package for Python (version 1.5.0 or later):  pip install git+https://github.com/artvalencio/cami-python
- numpy, pandas and Pillow

All at once:  pip install -r requirements.txt

------------------------------------------------------------------------------

Running:

    python cami_gui.py

1. Load the X and Y data (csv, Excel, Stata, SAS, SPSS, npy, json or HDF5) and
   choose the row or column holding each series and where its values start.
2. Choose the partition (any automatic encoding, or your own divisions),
   symbolic lengths, tau (or automatic tau), delay and units.
3. Optionally tick the surrogate test to obtain p-values for each measure.
4. Calculate; the results window can export the values to a CSV file.

------------------------------------------------------------------------------

Performance: calculating all measures takes ~3 ms instead of ~180 ms for
10^5 points; with 99 surrogates the significance tests take ~0.6 s instead
of ~15 s and run in the background with a progress bar and a Cancel button.
Loading a file reads only a preview, then only the chosen column or row.

------------------------------------------------------------------------------

Running the tests:

    pip install pytest
    pytest

The logic that does not need a window lives in cami_gui_core.py; window tests
are skipped automatically when no display is available.

------------------------------------------------------------------------------

Licence and acknoledgements

Open source licence: GNU GPL v3

Developer: Arthur Valencio

Institute of Computing/University of Campinas and Research, Innovation and Dissemination Center for Neuromathematics

Funding: FAPESP (S. Paulo Research Foundation), Brazil (2018-onwards).

Acknowledgements: Arthur Valencio is supported by the FAPESP grant 2018/09900-8 and acknowledges this work as part of the activities of the FAPESP Research 	     Innovation and Dissemination Center for Neuromathematics (grant 2013/07699-0, S. Paulo Research Foundation).

Licence text:

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

-----------------------------------------------------------------------------

Contact:

Arthur Valencio

e-mail: arthuric(at)unicamp.br

address:

Institute of Computing, Unicamp

Av. Albert Einstein, 1251

Cidade Universitaria

Campinas/SP, Brazil

CEP 13083-852 
