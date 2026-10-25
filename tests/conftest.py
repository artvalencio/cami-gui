import os
import sys

# Prefer the sibling cami-python checkout (if present) over an installed copy
SIBLING = os.path.join(os.path.dirname(__file__), '..', '..', 'cami-python')
if os.path.isdir(os.path.join(SIBLING, 'cami')):
    sys.path.insert(0, os.path.abspath(SIBLING))
