
from cmath import sqrt
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np
from math import sqrt, exp
import glob



QUBIT_FID_CZ_LAYER = 0.997
DELTA_N = 1.0
FACTOR = sqrt(6.0/(38.0*4*3.14*3.14*1.6*sqrt(2*DELTA_N)))
T_COHERENCE = 1500
SINGLE_QUBIT_FID = 0.9999

atom_json = {}

for size in range(8, 24, 2):
    atom_json_size = []
    for trial in range(10):

        path = f"./results/qaoa_{str(size)}_noTransfer_{str(trial)}*"
        for filename in glob.glob(path):
            file_object = open(filename, 'r')
            data = json.load(file_object)
        
        # some constants for animation
        FPS = 30    # default value of `interval` in FuncAnimation effectively FPS=10
        R_QUBIT = 8 # 16pts = minimum row saperation 2 micron
        PTS_PER_MICRON = 8
        R_SITE = 4*R_QUBIT + R_QUBIT//2
        SITE_SEP = R_SITE + 120 # 2.5x6 micron = 15 micron x 8pts per micron
        INTERACTION = FPS
        TRANSFER = FPS
        STATIONARY_FRAMES = INTERACTION + TRANSFER

        # prepare data, ?define an IR
        # QAOA16 on 4x8 canvas
        N_QUBIT = data['n_q']
        N_LAYER = data['n_t']
        COORD_R = data['coord_r']
        COORD_L = data['coord_l']
        COORD_U = data['coord_u']
        COORD_D = data['coord_d']
        AOD_L = data['aod_l']
        AOD_R = data['aod_r']
        AOD_U = data['aod_u']
        AOD_D = data['aod_d']
        layers = data['layers']


        X_LOWER = -R_SITE + SITE_SEP*COORD_L
        X_UPPER = R_SITE + SITE_SEP*(COORD_R-1)
        Y_LOWER = -R_SITE + SITE_SEP*COORD_D
        Y_UPPER = R_SITE + SITE_SEP*(COORD_U-1)


        def getColRowCoords(layers, t, col_or_row):
            if col_or_row == 'c':
                bounds = AOD_R - AOD_L
            elif col_or_row == 'r':
                bounds = AOD_U - AOD_D
            coords = [-1 for _ in range(bounds)]
            for q in range(N_QUBIT):
                if layers[t]['qubits'][q]['a'] == 1:
                    
                    if col_or_row == 'c':
                        q_col_row = layers[t]['qubits'][q]['c']
                        q_x_y = layers[t]['qubits'][q]['x']
                    elif col_or_row == 'r':
                        q_col_row = layers[t]['qubits'][q]['r']
                        q_x_y = layers[t]['qubits'][q]['y']

                    coords[q_col_row] = q_x_y
                else:
                    if t>0 and layers[t-1]['qubits'][q]['a'] == 1:
                        if col_or_row == 'c':
                            q_col_row = layers[t-1]['qubits'][q]['c']
                            q_x_y = layers[t]['qubits'][q]['x']
                        elif col_or_row == 'r':
                            q_col_row = layers[t-1]['qubits'][q]['r']
                            q_x_y = layers[t]['qubits'][q]['y']
                    
                        coords[q_col_row] = q_x_y

            return coords

        # preprocessing for t=0
        # compute the sites of columns and rows
        col_coords = list()
        row_coords = list()
        col_coords.append( getColRowCoords(layers, 0, 'c') )
        row_coords.append( getColRowCoords(layers, 0, 'r') )

        # compute the offsets of columns and rows, we can have -1, 0, 1, 2
        # convention: only SLM qubits have 0 value, the AOD qubits are as left and 
        # as top as possible. For t=0, AOD row and col are at -2
        col_offsets = list()
        row_offsets = list()

        def getUpdatedOffsets(coords, t, col_or_row):
            if col_or_row == 'c':
                bounds = COORD_R - COORD_L
                x_or_y = 'x'
            elif col_or_row == 'r':
                bounds = COORD_U - COORD_D
                x_or_y = 'y'
            
            offsets = [-1 for _ in range(len(coords[t]))]
            for coord in range(bounds):
                temp = -1
                for i, col in enumerate(coords[t]):
                    if col == coord:
                        offsets[i] = temp
                        temp += 1
                        if temp == 0:
                            temp += 1
            return offsets

        col_offsets.append( getUpdatedOffsets(col_coords, 0, 'c') )
        row_offsets.append( getUpdatedOffsets(row_coords, 0, 'r') )

        # change offsets to pts
        def offset2pts(offset):
            if offset == -2: return -3*R_QUBIT - R_QUBIT//2
            elif offset == -1: return -R_QUBIT - R_QUBIT//2
            elif offset == 1: return R_QUBIT + R_QUBIT//2
            elif offset == 2: return 3*R_QUBIT + R_QUBIT//2
            else: return 0

        def getInteractions(layers, t):
            interactions = list()
            for gate in layers[t]['gates']:
                q0 = gate['q0']
                q0_x, q0_y = layers[t]['qubits'][q0]['x'], layers[t]['qubits'][q0]['y']
                interactions.append( (q0_x, q0_y) )
            return interactions


        # preprocessing for t>0
        for t in range(1, N_LAYER):

            # compute the col/row coords
            col_coords.append( getColRowCoords(layers, t, 'c') )
            row_coords.append( getColRowCoords(layers, t, 'r') )

            # compute the col/row offsets
            col_offsets.append( getUpdatedOffsets(col_coords, t, 'c') )
            row_offsets.append( getUpdatedOffsets(row_coords, t, 'r') )

        # compute the sites with Rydberg interaction happening
        interactions = list()
        for t in range(N_LAYER):
            interactions.append( getInteractions(layers, t) )

        # compute pts for rows&cols
        col_pts = list()
        row_pts = list()
        for t in range(N_LAYER):
            col_pts.append([0 for _ in range(AOD_L, AOD_R)])
            for col in range(AOD_L, AOD_R):
                col_pts[t][col] = SITE_SEP*col_coords[t][col] + \
                                offset2pts(col_offsets[t][col])
            row_pts.append([0 for _ in range(AOD_D, AOD_U)])
            for row in range(AOD_D, AOD_U):
                row_pts[t][row] = SITE_SEP*row_coords[t][row] + \
                                offset2pts(row_offsets[t][row])

                
        # compute the movement in pts
        mov_col_pts = list()
        mov_row_pts = list()
        for t in range(N_LAYER-1):
            mov_col_pts.append([0 for _ in range(AOD_L, AOD_R)])
            for col in range(AOD_L, AOD_R):
                if col_coords[t+1][col] != -1 and col_coords[t][col] != -1:
                    mov_col_pts[t][col] = col_pts[t+1][col] - col_pts[t][col]
            mov_row_pts.append([0 for _ in range(AOD_D, AOD_U)])
            for row in range(AOD_D, AOD_U):
                if row_coords[t+1][row] != -1 and row_coords[t][row] != -1:
                    mov_row_pts[t][row] = row_pts[t+1][row] - row_pts[t][row]


        # compute the total number of frames
        frame_splits = list()
        frame_splits.append(0)
        frame_splits.append(STATIONARY_FRAMES)
        fidelity_cost = 1.0
        for t in range(N_LAYER-1):
            # print()
            max_mov_pts = 0
            for col in range(AOD_L, AOD_R):
                mov_col_pts_tmp = max(mov_col_pts[t][col], -mov_col_pts[t][col])
                # print(f"col {col}: {mov_col_pts_tmp/8} micron")
                for row in range(AOD_D, AOD_U):
                    mov_row_pts_tmp = max(mov_row_pts[t][row], -mov_row_pts[t][row])
                    # if col == AOD_L:
                        # print(f"row {row}: {mov_row_pts_tmp/8} micron")
                    max_mov_pts = max(max_mov_pts, sqrt(mov_col_pts_tmp*mov_col_pts_tmp + mov_row_pts_tmp*mov_row_pts_tmp))
            
            # print(max_mov_pts/PTS_PER_MICRON)
            fidelity_cost = fidelity_cost * exp(-1.0 * N_QUBIT * sqrt(max_mov_pts/PTS_PER_MICRON) * FACTOR / T_COHERENCE )
        
        print(fidelity_cost**3)
        atom_json_size.append( fidelity_cost * pow(QUBIT_FID_CZ_LAYER, N_QUBIT*N_LAYER) * pow(SINGLE_QUBIT_FID, 3*size) )

    atom_json[str(size)] = atom_json_size

with open("fpqa_proj.json", 'w') as file:
    json.dump(atom_json, file)
file.close()