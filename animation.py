def animateFPQA(file_name):
    import json
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.animation import FuncAnimation
    from matplotlib.animation import FFMpegWriter
    import numpy as np
    plt.rcParams['animation.ffmpeg_path'] = '/usr/bin/ffmpeg'


    file_object = open(file_name)
    data = json.load(file_object)

    # some constants for animation
    FPS = 30    # default value of `interval` in FuncAnimation effectively FPS=10
    R_QUBIT = 8
    R_SITE = 4*R_QUBIT + R_QUBIT//2
    SITE_SEP = 20*R_QUBIT
    V_MOVE = SITE_SEP // FPS
    INTERACTION = FPS
    TRANSFER = FPS
    STATIONARY_FRAMES = INTERACTION + TRANSFER

    # prepare data, ?define an IR
    # QAOA16 on 4x8 canvas
    one_qubit_gate = data['g_1s']
    N_QUBIT = data['n_q']
    N_LAYER = data['n_t']
    COORD_R = data['coord_r']
    COORD_L = data['coord_l']
    COORD_U = data['coord_u']
    #原本
    #COORD_D = data['coord_d']
    COORD_D = data['coord_d'] - 1
    AOD_L = data['aod_l']
    AOD_R = data['aod_r']
    AOD_U = data['aod_u']
    #原本
    #AOD_D = data['aod_d']
    AOD_D = data['coord_d'] - 1
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
    for t in range(N_LAYER-1):
        max_dx_pts = 0
        for col in range(AOD_L, AOD_R):
            max_dx_pts = max(max_dx_pts, mov_col_pts[t][col], -mov_col_pts[t][col])
        max_dy_pts = 0
        for row in range(AOD_D, AOD_U):
            max_dy_pts = max(max_dy_pts, mov_row_pts[t][row], -mov_row_pts[t][row])
        finishing = frame_splits[-1] + max( 1-(-max_dx_pts // V_MOVE), 
                                            1-(-max_dy_pts // V_MOVE) )
        frame_splits.append(finishing)
        frame_splits.append(finishing + STATIONARY_FRAMES)
                
    # creating animation from here now, first set up the canvas and initial pos
    px = 1/plt.rcParams['figure.dpi'] 
    fig = plt.figure( figsize=((X_UPPER-X_LOWER)*px,
                            (Y_UPPER-Y_LOWER)*px ))
    ax = plt.axes()
    ax.set_xlim([X_LOWER, X_UPPER])
    ax.set_xticks([SITE_SEP*i for i in range(AOD_L, AOD_R)])
    ax.set_xticklabels([i for i in range(AOD_L, AOD_R)])
    ax.set_ylim([Y_LOWER, Y_UPPER])
    y_middle = (Y_LOWER + Y_UPPER) / 2
    ax.axhline(y_middle, linestyle='dashed', color='lightgray', linewidth=1)
    ax.set_yticks([SITE_SEP*i for i in range(COORD_D, COORD_U)])
    ax.set_yticklabels([i for i in range(COORD_D, COORD_U)])
    y_label_x = X_LOWER - 45  # 調整 x 座標位置
    y_label_2 = Y_UPPER - (Y_UPPER - Y_LOWER) * 0.25 # 調整 y 座標位置
    y_label_1 = Y_LOWER + (Y_UPPER - Y_LOWER) * 0.25
    plt.text(y_label_x, y_label_2, "two qubit gate", fontsize=12, ha='center', va='center', rotation='vertical')
    plt.text(y_label_x, y_label_1, "one qubit gate", fontsize=12, ha='center', va='center', rotation='vertical')
    qubit_scatter = list()
    annotations = list()
    col_lines = list()
    row_lines = list()

    # computing 'snapshots' of atom configurations            
    def init():
        return

    def qubitPosition(begin, end, n_frame):
        if begin == end:
            return begin
        direction = 1 if end>begin else -1
        suppose_pts = begin + direction*V_MOVE*n_frame
        if (suppose_pts - begin) * (end - suppose_pts) < 0:
            return end
        else:
            return suppose_pts


    def snapshot(frame):
        if frame == 0:
            for q in layers[0]['qubits']:
                if q['a'] == 1:
                    q_x_pts, q_y_pts = col_pts[0][q['c']], row_pts[0][q['r']]
                    q_color = 'r'
                elif q['a'] == 0:
                    q_color = 'b'
                    q_x_pts, q_y_pts = SITE_SEP*q['x'], SITE_SEP*q['y']
                qubit_scatter.append(ax.scatter([q_x_pts], [q_y_pts],
                                                s=16*R_QUBIT^2, marker='o',
                                                facecolors='none', edgecolors='k'))
                annotations.append(plt.annotate(q['id'],
                            xy=(q_x_pts, q_y_pts), xytext=(q_x_pts, q_y_pts),
                            ha='center', va='center',
                            size=R_QUBIT, family='monospace', color=q_color))

        tmp = 0
        for i, split in enumerate(frame_splits):
            if split <= frame and frame_splits[i+1]>frame:
                tmp = i
                break

        num = 0
        # stantionary        
        if tmp%2 == 0:
            tmp = tmp // 2
            if frame == frame_splits[tmp*2]:
                # print(f"frame {frame} tmp {tmp}")
                # Rydberg interaction
                for int_site in interactions[tmp]:
                    print(int_site)
                    if int_site[1] >= 0:
                        ax.add_patch(patches.Rectangle( (-R_SITE+SITE_SEP*int_site[0],
                                                        -R_SITE+SITE_SEP*int_site[1]),
                                                    2*R_SITE, 2*R_SITE,
                                                    facecolor="g", alpha=0.2))
                        text_x = -R_SITE + SITE_SEP * int_site[0] + R_SITE  # X 坐標
                        text_y = -R_SITE + SITE_SEP * int_site[1] + R_SITE
                        ax.text(text_x, text_y, "CZ", color="black", ha="center", va="center", fontsize=18,weight='bold')
                    else:
                        ax.add_patch(patches.Rectangle((-R_SITE + SITE_SEP * int_site[0],
                                                        -R_SITE+SITE_SEP*int_site[1]),
                                                       2 * R_SITE, 2 * R_SITE,
                                                       facecolor="r", alpha=0.2))
                        if one_qubit_gate[num] == 'Rx' :
                            print('Rx')
                            text_x = -R_SITE + SITE_SEP * int_site[0] + R_SITE  # X 坐標
                            text_y = -R_SITE + SITE_SEP * int_site[1] + R_SITE  # Y 坐標
                            ax.text(text_x, text_y, "Rx", color="black", ha="center", va="center", fontsize=18,weight='bold')
                            num += 1
                        elif one_qubit_gate[num] == 'Ry' :
                            print('Ry')
                            text_x = -R_SITE + SITE_SEP * int_site[0] + R_SITE  # X 坐標
                            text_y = -R_SITE + SITE_SEP * int_site[1] + R_SITE  # Y 坐標
                            ax.text(text_x, text_y, "Ry", color="black", ha="center", va="center", fontsize=18,weight='bold')
                            num += 1
                        elif one_qubit_gate[num] == 'Rz' :
                            print('Rz')
                            text_x = -R_SITE + SITE_SEP * int_site[0] + R_SITE  # X 坐標
                            text_y = -R_SITE + SITE_SEP * int_site[1] + R_SITE  # Y 坐標
                            ax.text(text_x, text_y, "Rz", color="black", ha="center", va="center", fontsize=18,weight='bold')
                            num += 1

            if frame == frame_splits[tmp*2] + INTERACTION:
                clear_num = -1
                while ax.patches:
                    ax.patches.pop()
                    text_obj = ax.texts[clear_num]
                    text_obj.set_visible(False)
                    clear_num -= 1


            if frame == frame_splits[tmp*2] + INTERACTION + 1:
                for i, q in enumerate(layers[tmp]['qubits']):
                    if q['transfer']:
                        q_color = 'r' if q['a'] == 1 else 'b'
                        annotations[i].remove()
                        annotations[i] = plt.annotate(q['id'],
                        xy=(-1000, -1000), xytext=(-1000, -1000),
                        ha='center', va='center',
                        size=R_QUBIT, family='monospace')
                        ax.add_patch(patches.Rectangle( (-R_SITE+SITE_SEP*q['x'],
                                                    -R_SITE+SITE_SEP*q['y']), 
                                                2*R_SITE, 2*R_SITE,
                                                facecolor='w', alpha=1))


            if frame == frame_splits[tmp*2] + STATIONARY_FRAMES - 1:
                clear_num = -1
                while ax.patches:
                    ax.patches.pop()
                    text_obj = ax.texts[clear_num]
                    text_obj.set_visible(False)
                    clear_num -= 1

        # atoms are moving
        else:
            last_split = frame_splits[tmp]
            tmp = tmp // 2
            for i, q in enumerate(layers[tmp]['qubits']):
                if q['a'] == 1:
                    new_x = qubitPosition(col_pts[tmp][q['c']], col_pts[tmp+1][q['c']],
                                        frame-last_split)
                    new_y = qubitPosition(row_pts[tmp][q['r']], row_pts[tmp+1][q['r']],
                                        frame-last_split)

                    new_color = 'r'
                else:
                    new_x = SITE_SEP*q['x']
                    new_y = SITE_SEP*q['y']
                    new_color = 'b'
                qubit_scatter[i].set_offsets([(new_x, new_y)])
                annotations[i].remove()
                annotations[i] = plt.annotate(q['id'],
                    xy=(new_x, new_y), xytext=(new_x, new_y),
                    ha='center', va='center',
                    size=R_QUBIT, family='monospace', color=new_color)

            for line in col_lines:
                tmpline = line.pop(0)
                tmpline.remove()
            for line in row_lines:
                tmpline = line.pop(0)
                tmpline.remove()
            col_lines.clear()
            row_lines.clear()
            for col in range(AOD_L, AOD_R):
                if col_coords[tmp][col] != -1 and col_coords[tmp+1][col] != -1:
                    new_x = qubitPosition(col_pts[tmp][col], col_pts[tmp+1][col],
                                        frame-last_split)
                    tmp_line = ax.plot([new_x, new_x],
                                        [Y_LOWER, Y_UPPER], '--r', alpha=0.2)
                    col_lines.append(tmp_line)
            for row in range(AOD_D, AOD_U):
                # print(row_coords)
                if row_coords[tmp][row] != -1 and row_coords[tmp+1][row] != -1:
                    new_y = qubitPosition(row_pts[tmp][row], row_pts[tmp+1][row],
                                        frame-last_split)
                    # print(f"frame: {frame}, row: {row}, last_split: {last_split}, tmp: {tmp}, row_pts[tmp][row]: {row_pts[tmp][row]},"
                    #       f" row_pts[tmp+1][row]: {row_pts[tmp + 1][row]}")
                    tmp_line = ax.plot([X_LOWER, X_UPPER],
                                        [new_y, new_y], '--r', alpha=0.2)
                    row_lines.append(tmp_line)

        return qubit_scatter,

    anim = FuncAnimation(fig, snapshot, init_func=init, frames=frame_splits[-1],
                        interval = 1000/FPS)

    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, FFMpegWriter

    plt.rcParams['animation.ffmpeg_path'] = r'C:\FFMPEG\ffmpeg-6.0-full_build\bin\ffmpeg.exe'
    anim.save(file_name.replace('.json', '.mp4'), writer=FFMpegWriter(FPS))
    # anim.save(file_name.replace('.json', '.gif'), writer='imagemagick', fps=FPS)
    file_object.close()
