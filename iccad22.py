from solve import FPQA
import argparse
from qaoa_graphs import graphs
from animation import animateFPQA

parser = argparse.ArgumentParser()
parser.add_argument('size', metavar='S', type=int, help='display an integer')
parser.add_argument('id', metavar='I', type=int)
parser.add_argument('no_transfer', metavar='NAT', type=int)
args = parser.parse_args()

tmp = FPQA()
tmp.setArchitecture([0, 16, 0, 16])
tmp.setProgram(graphs[str(args.size)][args.id])
tmp.setPureGraph()
tmp.setCommutation()
prefix = 'qaoa_' + str(args.size) + '_'
if args.no_transfer:
    tmp.setNoTransfer()
    prefix += 'noTransfer_'
prefix += str(args.id) + '_'
tmp.addPrefix(prefix)
tmp.solve()
# animateFPQA('./results/' + str(ts) + '.json')
