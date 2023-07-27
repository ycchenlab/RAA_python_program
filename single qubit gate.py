# input ： two qubit gate and single qubit gate 要按照順序
# 創建一個 x * y 的下方區域
# 執行single qubit gate 的 qubit 需要移動到下方區域
from z3 import *

x = Int('x')
y = Int('y')
s = Solver()
s.add(x + y == 10)
s.add(x > 0)
s.add(y > 0)
if s.check() == sat:
    model = s.model()
    print("x =", model[x])
    print("y =", model[y])
else:
    print("Unsat")

l = Optimize()
l.add(x + y == 10)
l.add(x > 0)
l.add(y > 0)
l.minimize(x)
if l.check() == sat:
    model = l.model()
    print("x =", model[x])
    print("y =", model[y])
else:
    print("Unsat")
