
ICCAD 2022 paper Qubit Mapping for Reconfigurable Atom Arrays

An example (the running example in the paper) of using the tool:

```python
from solve import FPQA
# assuming this script is in the same directory with solve.py

from animation import animateFPQA
# animation tool


tmp = FPQA()
# initialize the solver object

tmp.setArchitecture([0, 4, 0, 2])
# specify the bounds of XY coordinates (0<=x<4 and 0<=y<2).
# if specyfied 8 numbers, the latter four are the bounds for
# AOD columns and rows. If unspecified, these bounds are set
# to the bounds of X and Y.

tmp.setProgram([(2, 4), (3, 5), (0, 1), (2, 3),
               (4, 5), (0, 2), (1, 3), (0, 4), (1, 5)])
# the program is a list of 2-tuples. We assume that the qubit
# indices start from 0 and is consecutive.

tmp.setPureGraph()
# Since QAOA for 3-regular graphs circuit can be represented
# as a graph. Setting this function is optinal, but makes solving faster.

tmp.setCommutation()
# Since all the ZZ-phase gates are commutable

ts = tmp.solve()
# solve the result and save it to ts.json in ./results

animateFPQA('./results/' + str(ts) + '.json')
# animate the results
```
