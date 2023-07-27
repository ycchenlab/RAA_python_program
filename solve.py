from base64 import standard_b64decode
from typing import Dict
from z3 import Int, Bool, sat, And, If, Implies, Optimize, Solver, Not, is_true, Real, Or, BitVecs, is_true
import datetime
import json


def collisionExtract(list_gate_qubits):
    # 完整 全部commute 才用的到
    """Extract collision relations between the gates,
    If two gates g_1 and g_2 both acts on a qubit (at different time),
    we say that g_1 and g_2 collide on that qubit, which means that
    (1,2) will be in collision list.
    Args:
        list_gate_qubits: a list of gates in OLSQ IR

    Returns:
        list_collision: a list of collisions between the gates
    """

    list_collision = list()
    # 會碰再一起的gate
    # We sweep through all the gates.  For each gate, we sweep through all the
    # gates after it, if they both act on some qubit, append them in the list.
    for g in range(len(list_gate_qubits)):
        for gg in range(g + 1, len(list_gate_qubits)):

            if list_gate_qubits[g][0] == list_gate_qubits[gg][0]:
                list_collision.append((g, gg))

            if len(list_gate_qubits[gg]) == 2:
                if list_gate_qubits[g][0] == list_gate_qubits[gg][1]:
                    list_collision.append((g, gg))

            if len(list_gate_qubits[g]) == 2:
                if list_gate_qubits[g][1] == list_gate_qubits[gg][0]:
                    list_collision.append((g, gg))
                if len(list_gate_qubits[gg]) == 2:
                    if list_gate_qubits[g][1] == list_gate_qubits[gg][1]:
                        list_collision.append((g, gg))

    return tuple(list_collision)


def maxDegree(list_gate_qubits, count_program_qubit):
    #完整
    cnt = [0 for _ in range(count_program_qubit)]
    for g in list_gate_qubits:
        cnt[g[0]] += 1
        if len(g) == 2:
            cnt[g[1]] += 1
    return max(cnt)
#這段程式碼的目的是計算 list_gate_qubits 中每個qubit的值出現的次數，並返回出現次數最多的值的次數。


def dependencyExtract(list_gate_qubits, count_program_qubit: int):
    # 完整
    # count_program_qubit：有幾個qubit  list_gate_qubits：two qubit gate 所用到的qubit
    """Extract dependency relations between the gates.
    If two gates g_1 and g_2 both acts on a qubit *and there is no gate
    between g_1 and g_2 that act on this qubit*, we then say that
    g2 depends on g1, which means that (1,2) will be in dependency list.
    Args:
        list_gate_qubits: a list of gates in OLSQ IR
        count_program_qubit: the number of logical/program qubit

    Returns:
        list_dependency: a list of dependency between the gates
    """

    list_dependency = []
    # 列出dependent gate
    list_last_gate = [-1 for i in range(count_program_qubit)]
    # list_last_gate：[-1,-1,-1....]
    # 紀錄最新作用在qubit上的gate
    # list_last_gate records the latest gate that acts on each qubit.
    # When we sweep through all the gates, this list is updated and the
    # dependencies induced by the update is noted.
    for i, qubits in enumerate(list_gate_qubits):
        if list_last_gate[qubits[0]] >= 0:
            list_dependency.append((list_last_gate[qubits[0]], i))
        # 检查当前门所用的第一个量子比特（索引为 qubits[0]）是否已经被其他门使用（list_last_gate[qubits[0]] >= 0）。
        # 如果该量子比特已经被其他门使用，则说明当前门依赖于之前的门。

        list_last_gate[qubits[0]] = i
        # 列出gate作用的qubit

        if len(qubits) == 2:
            if list_last_gate[qubits[1]] >= 0:
                list_dependency.append((list_last_gate[qubits[1]], i))
            list_last_gate[qubits[1]] = i
        # 用於two qubit gate
    return tuple(list_dependency)


def pushLeftDepth(list_gate_qubits, count_program_qubit):
    #完整
    push_forward_depth = [0 for i in range(count_program_qubit)]
    for qubits in list_gate_qubits:
        if len(qubits) == 1:
            push_forward_depth[qubits[0]] += 1
        else:
            tmp_depth = push_forward_depth[qubits[0]]
            if tmp_depth < push_forward_depth[qubits[1]]:
                tmp_depth = push_forward_depth[qubits[1]]
            push_forward_depth[qubits[1]] = tmp_depth + 1
            push_forward_depth[qubits[0]] = tmp_depth + 1
    return max(push_forward_depth)


class FPQA:
    # ifOpt=False：這是建構子的另一個參數，並且有一個預設值False。這表示，當建立物件時，您可以選擇是否提供這個參數，如果未提供，則參數會被設定為False。
    def __init__(self, ifOpt=False):
        # number of stage
        self.n_t = 1
        # number of qubit
        self.n_q = 0
        self.all_commutable = False
        self.satisfiable = False
        # if0pt 不知道是甚麼
        self.ifOpt = ifOpt
        self.all_aod = False
        self.no_transfer = False
        # pure graph 不知道是甚麼
        self.pure_graph = False
        self.result_json = {}
        self.result_json['prefix'] = ''
        # row_per_site：每個座標點是 row_per_site * row_per_site的方陣組成
        self.row_per_site = 3
        self.runtimes = {}

    def setArchitecture(self, bounds):
        # 完整
        # bounds = [left of X, right of X, top of Y, bottom of Y]
        self.aod_l, self.aod_r, self.aod_d, self.aod_u = bounds[:4]
        if len(bounds) == 8:
        # SLM的邊界
            self.coord_l, self.coord_r, self.coord_d, self.coord_u = bounds[4:]
        else:  # AOD and SLM bounds are the same
            self.coord_l, self.coord_r, self.coord_d, self.coord_u = bounds[:4]
        self.coord_d -= self.coord_u


    def setProgram(self, program):
        # assume program is a iterable of pairs of qubits in CZ gate
        # assume that the qubit indices used are consecutively 0, 1, ...
        # n_g ： number of gates
        self.n_g = len(program)
        self.n_2g = 0
        # tmp ：將輸入的two qubit gate 小的放前面大的放後面 ()
        tmp = []
        for pair in program:
            if len(pair) == 2:
                tmp = tmp + [(min(pair), max(pair))]
                self.n_2g += 1
            elif len(pair) == 1:
                tmp = tmp + [pair]
        self.g_q = tuple(tmp)
        # tmp = [(2,4),(3,5)...]
        #tuple 用於轉換資料結構為元組 資料較小
        # g_2s我多加的
        self.n_1g = self.n_g - self.n_2g
        self.g_2s = tuple(['Two qubit gate' for _ in range(self.n_2g)])
        self.g_s = tuple(['single qubit gate' for _ in range(self.n_g-self.n_2g)])
        # 找出有幾個qubit (n_q)
        for gate in program:
            # if isinstance(gate, (list, tuple)):
            self.n_q = max(gate[0], self.n_q)
            if len(gate) == 2 :
                self.n_q = max(gate[1], self.n_q)
            # else:
            #     self.n_q = max(gate, self.n_q)
        self.n_q += 1
        # line 66 回傳dependencies gate ex：[(0,1),(1,3)...]
        self.dependencies = dependencyExtract(self.g_q, self.n_q)
        # n_t為number of stages
        # line 90 回傳push_forward_depth ex.[3,2,2....]
        self.n_t = pushLeftDepth(self.g_q, self.n_q)

        # for graph state circuit
        self.gate_index = {}
        #問題
        for i in range(self.n_q):
            for j in range(i+1, self.n_q):
                self.gate_index[(i, j)] = -1
        for i in range(self.n_g):
            self.gate_index[self.g_q[i]] = i

    def setCommutation(self):
        # 如果所有gate可以commute的話才使用
        self.all_commutable = True
        self.collisions = collisionExtract(self.g_q)
        #作用在同一個qubit上的gate編號 ex.[(0,1)(0,5)....]
        self.n_t = maxDegree(self.g_q, self.n_q)

    def setAOD(self):
        self.all_aod = True

    def setDepth(self, depth):
        self.n_t = depth

    def setDepth(self, depth: Int):
        self.n_t = depth

    #不知道幹嘛用
    def setPureGraph(self):
        self.pure_graph = True

    # atom不能交換
    def setNoTransfer(self):
        self.no_transfer = True

    # 每個座標點有多大 參考paper fig 5.
    def setRowSite(self, row_per_site):
        self.row_per_site = row_per_site

    #不知道
    def addMetadata(self, metadata: Dict):
        self.result_json = {**metadata, **(self.result_json)}

    # 改檔案名稱
    def addPrefix(self, prefix):
        self.result_json["prefix"] = prefix

    def writeSettingJson(self):
        self.result_json['sat'] = self.satisfiable
        self.result_json['n_t'] = self.n_t
        self.result_json['n_q'] = self.n_q
        self.result_json['all_commutable'] = self.all_commutable
        self.result_json['if_Opt'] = self.ifOpt
        self.result_json['all_aod'] = self.all_aod
        self.result_json['no_transfer'] = self.no_transfer
        self.result_json['pure_graph'] = self.pure_graph
        self.result_json['aod_l'] = self.aod_l
        self.result_json['aod_r'] = self.aod_r
        self.result_json['aod_d'] = self.aod_d
        self.result_json['aod_u'] = self.aod_u
        self.result_json['coord_l'] = self.coord_l
        self.result_json['coord_r'] = self.coord_r
        self.result_json['coord_d'] = self.coord_d
        self.result_json['coord_u'] = self.coord_u
        self.result_json['row_per_site'] = self.row_per_site
        self.result_json['n_g'] = self.n_g
        self.result_json['g_q'] = self.g_q
        self.result_json['g_s'] = self.g_s
        self.result_json['g_2s'] = self.g_2s
        self.result_json['runtimes'] = self.runtimes

    def solve(self):
        self.t_s = datetime.datetime.now()
        # 計時用
        while not self.satisfiable:
            print(f"solving for depth {self.n_t}")
            self.t_s_tmp = datetime.datetime.now()

            # variables
            # a = [[T, F, T, ....]
            #      [T, T, F,....]...]
            a = [[Bool(f"arr_p{i}_t{j}") for j in range(self.n_t)]
                 for i in range(self.n_q)]
            # for col and row, the data does not matter if atom in SLM
            c = [[Int(f"col_p{i}_t{j}") for j in range(self.n_t)]
                 for i in range(self.n_q)]
            r = [[Int(f"row_p{i}_t{j}") for j in range(self.n_t)]
                 for i in range(self.n_q)]
            x = [[Int(f"x_p{i}_t{j}") for j in range(self.n_t)]
                 for i in range(self.n_q)]
            y = [[Int(f"y_p{i}_t{j}") for j in range(self.n_t)]
                 for i in range(self.n_q)]
            t = [Int(f"t_g{i}") for i in range(self.n_g)]
            print(t)

            if self.ifOpt:
                # ???
                # with issues right now
                fpqa = Optimize()
                d_x = [Real(f"mov_t_{i}") for i in range(self.n_t)]
                tot_mov = Real("total_time")
                for i in range(self.n_q):
                    for j in range(1, self.n_t):
                        fpqa.add(d_x[j] >= ((x[i][j]-x[i][j-1])**2)**0.25 +
                                 ((y[i][j]-y[i][j-1])**2)**0.25)
                fpqa.add(tot_mov >= sum([d_x[j] for j in range(1, self.n_t)]))
                fpqa.minimize(tot_mov)
            else:
                fpqa = Solver()
                # 使用Z3 解出問題，用add增加條件限制

            # if all are in AOD
            if self.all_aod:
                for i in range(self.n_q):
                    for j in range(self.n_t):
                        fpqa.add(a[i][j])

            # bounds
            for i in range(self.n_q):
                for j in range(self.n_t):
                    fpqa.add(x[i][j] >= self.coord_l, x[i][j] < self.coord_r)
                    fpqa.add(y[i][j] >= self.coord_d, y[i][j] < self.coord_u)
                    fpqa.add(c[i][j] >= self.aod_l)
                    fpqa.add(c[i][j] < self.aod_r)
                    fpqa.add(r[i][j] >= self.aod_d)
                    fpqa.add(r[i][j] < self.aod_u)
            for i in range(self.n_g):
                fpqa.add(t[i] < self.n_t)
                fpqa.add(t[i] >= 0)

            # dependency/collision
            # 不能同時跟兩個碰撞
            if self.all_commutable:
                for collision in self.collisions:
                    fpqa.add(t[collision[0]] != t[collision[1]])
            # dependency 的gate先後順係不能換
            else:
                for dependency in self.dependencies:
                    fpqa.add(t[dependency[0]] < t[dependency[1]])
            #完整

            # SLM sites are fixed
            # 完整
            for i in range(self.n_q):
                for j in range(self.n_t - 1):
                    # Implies 表示若達成裡面條件則執行
                    fpqa.add(Implies(Not(a[i][j]), x[i][j] == x[i][j+1]))
                    fpqa.add(Implies(Not(a[i][j]), y[i][j] == y[i][j+1]))

            # AOD columns/rows are moved together
            # 完整
            for i in range(self.n_q):
                for k in range(self.n_t-1):
                    fpqa.add(Implies(a[i][k], c[i][k+1] == c[i][k]))
                    fpqa.add(Implies(a[i][k], r[i][k+1] == r[i][k]))

            # 同一colume/row 的兩個qubit會在同一個位置
            # 完整
            for q0 in range(self.n_q):
                for q1 in range(q0+1, self.n_q):
                    for s in range(self.n_t-1):
                        fpqa.add(Implies(
                            And(a[q0][s], a[q1][s], c[q0][s] == c[q1][s]), x[q0][s+1] == x[q1][s+1]))
                        fpqa.add(Implies(
                            And(a[q0][s], a[q1][s], r[q0][s] == r[q1][s]), y[q0][s+1] == y[q1][s+1]))


            # AOD columns/rows cannot move across each other
            # 完整
            for i in range(self.n_q):
                for j in range(self.n_q):
                    for k in range(self.n_t - 1):
                        if i != j:
                            fpqa.add(Implies(And(a[i][k], a[j][k], c[i][k] < c[j][k]),
                                             x[i][k+1] <= x[j][k+1]))
                            fpqa.add(Implies(And(a[i][k], a[j][k], r[i][k] < r[j][k]),
                                             y[i][k+1] <= y[j][k+1]))

            # row/col constraints when atom transfer from SLM to AOD
            for i in range(self.n_q):
                for j in range(self.n_q):
                    for k in range(self.n_t):
                        if i != j:
                            fpqa.add(
                                Implies(x[i][k] < x[j][k], c[i][k] < c[j][k]))
                            fpqa.add(
                                Implies(y[i][k] < y[j][k], r[i][k] < r[j][k]))

            # not too many AOD columns/rows can be together, default 3
            # 完整
            for i in range(self.n_q):
                for j in range(self.n_q):
                    for k in range(self.n_t - 1):
                        if i != j:
                            fpqa.add(Implies(And(a[i][k], a[j][k], c[i][k]-c[j][k] > self.row_per_site - 1),
                                             x[i][k+1] > x[j][k+1]))
                            fpqa.add(Implies(And(a[i][k], a[j][k], r[i][k]-r[j][k] > self.row_per_site - 1),
                                             y[i][k+1] > y[j][k+1]))
            # not too many AOD columns/rows can be together, default 3, for initial stage
            for q in range(self.n_q):
                for qq in range(self.n_q):
                    if q != qq:
                        fpqa.add(Implies(And(a[q][0], a[qq][0], c[q][0]-c[qq][0] > self.row_per_site - 1),
                                         x[q][0] > x[qq][0]))
                        fpqa.add(Implies(And(a[q][0], a[qq][0], r[q][0]-r[qq][0] > self.row_per_site - 1),
                                         y[q][0] > y[qq][0]))

            # connectivity
            # 當two qubit gate作用時 p0和p1需在同一個位置
            for i in range(self.n_g):
                for j in range(self.n_t):
                    if len(self.g_q[i]) == 2:
                        p0 = self.g_q[i][0]
                        p1 = self.g_q[i][1]
                        fpqa.add(Implies(t[i] == j, x[p0][j] == x[p1][j]))
                        fpqa.add(Implies(t[i] == j, y[p0][j] == y[p1][j]))

            # 加入single qubit gate的條件
            # 只有執行 one qubit gate 的才能在下層
            # 做出一個 one qubit gate 的list

            for i in range(self.n_g):
                for j in range(self.n_t):
                    for k in range(self.n_q):

                        # q_list = [0 for _ in range(self.n_q)]
                        if len(self.g_q[i]) == 1:
                            p0 = self.g_q[i][0]
                            fpqa.add(Implies(t[i] == j, y[p0][j] < 0))
                            if k != p0:
                                fpqa.add(Implies(t[i] == j, y[k][j] >= 0))
                        else:
                            fpqa.add(Implies(t[i] == j, y[k][j] >= 0))
                            # q_list[p0] += 1
                            # print(q_list)

            if self.pure_graph:
                # global CZ switch (only works for graph state circuit)
                for i in range(self.n_q):
                    for j in range(i+1, self.n_q):
                        for k in range(self.n_t):
                            if self.gate_index[(i, j)] == -1:
                                fpqa.add(
                                    Or(x[i][k] != x[j][k], y[i][k] != y[j][k]))
                            else:
                                fpqa.add(Implies(And(x[i][k] == x[j][k],
                                                     y[i][k] == y[j][k]), t[self.gate_index[(i, j)]] == k))
                # bound number of atoms in each site, needed if not double counting
                #問題
                for i in range(self.n_q):
                    for j in range(i+1, self.n_q):
                        for k in range(self.n_t):
                            fpqa.add(Implies(And(a[i][k], a[j][k]), Or(c[i][k] != c[j][k],
                                                                       r[i][k] != r[j][k])))
                            fpqa.add(Implies(And(Not(a[i][k]), Not(a[j][k])), Or(x[i][k] != x[j][k],
                                                                                 y[i][k] != y[j][k])))
            else:
                # global CZ switch
                #問題
                fpqa.add(self.n_2g == sum([If(And(x[i][k] == x[j][k],
                                                 y[i][k] == y[j][k]), 1, 0) for i in range(self.n_q)
                                          for j in range(i+1, self.n_q) for k in range(self.n_t)]))

            # no atom transfer if two atoms meet
            for i in range(self.n_q):
                for j in range(i+1, self.n_q):
                    for k in range(1, self.n_t):
                        fpqa.add(Implies(And(x[i][k] == x[j][k], y[i][k] == y[j][k]), And(
                            a[i][k] == a[i][k-1], a[j][k] == a[j][k-1])))

            # if atom transfer is not allowed
            if self.no_transfer:
                for i in range(self.n_q):
                    for j in range(1, self.n_t):
                        fpqa.add(a[i][j] == a[i][0])

            # solve model
            # 如果存在解，則 if_sat 變數將被設置為 sat，否則為 unsat
            if_sat = fpqa.check()
            now = datetime.datetime.now()
            self.result_json['timestamp'] = datetime.datetime.timestamp(now)
            duration_this = now - self.t_s_tmp
            self.runtimes[self.n_t] = str(duration_this)

            if if_sat == sat:
                duration_total = now - self.t_s
                self.result_json['duration'] = str(duration_total)
                print(f"total time {duration_total}")
                self.satisfiable = True
            else:
                print(f"took time {duration_this}")
                self.n_t += 1
                if self.no_transfer:
                    if self.n_t > 1 + self.n_g:
                        self.writeSettingJson()
                        return
                else:
                    if self.n_t > self.n_g:
                        self.writeSettingJson()
                        return
            # 問題

        # get results
        model = fpqa.model()
        self.writeSettingJson()
        self.result_json['layers'] = []

        aod_q_tot = []
        slm_q_tot = []
        for k in range(self.n_t):
            print(f"\ntime step {k}:")
            layer = {}
            # 列出qubit資訊 ex.{'id': 0, 'a': 0, 'x': 0, 'y': 0, 'c': 0, 'r': 0, 'transfer': True}
            layer['qubits'] = []
            aod_q = []
            #列出AOD 的qiskit序號 ex. aod_q = [3, 4]
            slm_q = []
            for i in range(self.n_q):
                layer['qubits'].append({
                    'id': i,
                    'a': 1 if is_true(model[a[i][k]]) else 0,
                    'x': model[x[i][k]].as_long(),
                    'y': model[y[i][k]].as_long(),
                    'c': model[c[i][k]].as_long(),
                    'r': model[r[i][k]].as_long(),
                    'transfer': False})
                if is_true(model[a[i][k]]):
                    aod_q.append(i)
                    print(f"p_{i} is at AOD ({model[x[i][k]].as_long()}, " +
                          f"{model[y[i][k]].as_long()})" + f" col {model[c[i][k]].as_long()}, row {model[r[i][k]].as_long()}")
                    if k > 0 and (i not in aod_q_tot[k-1]):
                        # SLM change to AOD
                        print("!!!changed")
                        layer['qubits'][i]['transfer'] = True
                else:
                    slm_q.append(i)
                    print(f"p_{i} is at SLM ({model[x[i][k]].as_long()}, " +
                          f"{model[y[i][k]].as_long()})" + f" col {model[c[i][k]].as_long()}, row {model[r[i][k]].as_long()}")
                    if k > 0 and (i not in slm_q_tot[k-1]):
                        # AOD change to SLM
                        print("!!!changed")
                        layer['qubits'][i]['transfer'] = True
            aod_q_tot.append(aod_q)
            slm_q_tot.append(slm_q)

            xMovements = dict()
            yMovements = dict()
            # 列出 X、Y 方向的移動
            for i in aod_q:
                x_curr = model[x[i][k]].as_long()
                y_curr = model[y[i][k]].as_long()
                if k>0:
                    x_old = model[x[i][k-1]].as_long()
                    y_old = model[y[i][k-1]].as_long()
                    if x_curr != x_old:
                        xMovements[x_old] = x_curr
                    if y_curr != y_old:
                        yMovements[y_old] = y_curr
            if k>0:
                print(f"X Movements: {sorted(xMovements.items())}")
                print(f"Y Movements: {sorted(yMovements.items())}")

            layer['gates'] = []
            # 問題
            # 列出每一個階段gate作用的qubit
            for j in range(self.n_g):
                if model[t[j]].as_long() == k:
                    if len(self.g_q[j]) == 2:
                        print(f"Two qubit gate (p_{self.g_q[j][0]}, p_{self.g_q[j][1]})")
                        layer['gates'].append(
                            {'id': j, 'q0': self.g_q[j][0], 'q1': self.g_q[j][1]})
                    elif len(self.g_q[j]) == 1:
                        print(f"one qubit gate (p_{self.g_q[j][0]})")
                        layer['gates'].append(
                            {'id': j, 'q0': self.g_q[j][0]})
            self.result_json['layers'].append(layer)

        self.coords = list()
        self.gates = list()
        for k in range(self.n_t):
            self.coords.append(list())
            for i in range(self.n_q):
                tmp = list()
                tmp.append(str(i))
                if i in aod_q:
                    tmp.append('aod')
                else:
                    tmp.append('slm')
                tmp.append((model[x[i][k]].as_long(),
                            model[y[i][k]].as_long()))
                self.coords[k].append(tmp)

            self.gates.append(list())
            # 問題
            for j in range(self.n_g):
                if model[t[j]].as_long() == k:
                    self.gates[k].append(self.g_q[j])

        with open(f"./results/{self.result_json['prefix'] + str(self.result_json['timestamp'])}.json", 'w') as file_object:
            json.dump(self.result_json, file_object)
        file_object.close()

        return self.result_json['timestamp']
