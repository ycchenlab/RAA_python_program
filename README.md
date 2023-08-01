
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
# specify the bounds of XY coordinates and Y coordinates will * 2 (0<=x<4 and -2<y<2).

N = 4 ; A = []
for i in range(1,N):
    A += [(i,),(i-1,i),(i,),]
tmp.setProgram(A)
# the program is  N qubits GHZ state.

ts = tmp.solve()
# solve the result and save it to ts.json in ./results

animateFPQA('./results/' + str(ts) + '.json')
# animate the results
```
