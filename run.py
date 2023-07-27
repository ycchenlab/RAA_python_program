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

tmp.setProgram([(0,1), (1,), (1,2), (2,3)])

ts = tmp.solve()
# solve the result and save it to ts.json in ./results

animateFPQA('./results/' + str(ts) + '.json')
# animate the results