from solve import FPQA
from animation import animateFPQA


#用來測試的檔案
tmp = FPQA()
tmp.setArchitecture([0,5,0,3])
data = [('Rx',(0,)),('Ry',(0,)),('Rx',(1,)),('Ry',(1,)),('Rx',(2,)),('Ry',(2,)),('CZ',(1,0)),('Rx',(1,)),('Ry',(1,)),('CZ',(1,2)),('Rx',(2,)),('Ry',(2,))]
tmp.setProgram(data)
ts = tmp.solve(data)
# animateFPQA('./results/' + str(ts) + '.json')