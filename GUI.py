import time
import tkinter as tk
from tkinter import font
from solve import FPQA
from animation import animateFPQA
import cv2
import subprocess

# 主視窗
root = tk.Tk()
root.title('RAA Quantum circuit')
root.geometry("1200x550+150+100")

# 主框架 畫面上藍色一大片
main_frame = tk.Frame(root,bg="#3F51B5")
main_frame.pack(fill=tk.BOTH, expand=1)


#用來裝所有小frame的畫面左側的白色區域
frame_container = tk.Frame(main_frame,bg="#FBFBFF",)
frame_container.pack(side='left', fill='y')

#字體
lato_font = font.Font(family="Helvetica", size=10, weight="normal")
lato_font_2 = font.Font(family="Helvetica", size=9, weight="normal")

#x_num橫軸可以放多少個gate
#y_num縱軸可以放多少個gate
#interface_num用來記錄輸入的qubit數
#data_matrix用來存gate位置資料
x_num = 20
y_num = 10
interface_num = -1
data_matrix = []


#含有event的代表按下enter及可執行
def update_button_command(event):
    global interface_num
    global data_matrix
    # 得到輸入的值
    text = update_entry.get()
    float_number = float(text)
    integer_number = int(float_number)
    interface_num = integer_number
    data_matrix = [["" for _ in range(x_num)] for _ in range(interface_num)]
    #將要得線和q[i]顯示出來
    for i in range(y_num):
        variable_name = f"qubit_label{i}"
        exec(f"{variable_name}.lower()")
        variable_name = f"gates_sequence_line{i}"
        exec(f"{variable_name}.lower()")
        for j in range(x_num):
            variable_name = f"gates_sequence_button{i*x_num+j}"
            exec(f"{variable_name}.config(text='', command=None)")
            exec(f"{variable_name}.lower()")
            if i * x_num + j == x_num*y_num-1:
                break
            variable_name = f"CZ_line{i * x_num + j}"
            exec(f"{variable_name}.lower()")
    if integer_number > y_num:
        integer_number = y_num
    for i in range(integer_number):
        variable_name = f"gates_sequence_line{i}"
        exec(f"{variable_name}.lift()")
        variable_name = f"qubit_label{i}"
        exec(f"{variable_name}.lift()")

def update_button_command_():
    global interface_num
    global data_matrix
    text = update_entry.get()
    float_number = float(text)
    integer_number = int(float_number)
    interface_num = integer_number
    data_matrix = [["" for _ in range(x_num)] for _ in range(interface_num)]
    for i in range(y_num):
        variable_name = f"qubit_label{i}"
        exec(f"{variable_name}.lower()")
        variable_name = f"gates_sequence_line{i}"
        exec(f"{variable_name}.lower()")
        for j in range(x_num):
            variable_name = f"gates_sequence_button{i*x_num+j}"
            exec(f"{variable_name}.config(text='', command=None)")
            exec(f"{variable_name}.lower()")
            if i * x_num + j == x_num*y_num-1:
                break
            variable_name = f"CZ_line{i * x_num + j}"
            exec(f"{variable_name}.lower()")
    if integer_number > y_num:
        integer_number = y_num
    for i in range(integer_number):
        variable_name = f"gates_sequence_line{i}"
        exec(f"{variable_name}.lift()")
        variable_name = f"qubit_label{i}"
        exec(f"{variable_name}.lift()")

#製造 y_num個標籤q[i]放到最下層
for i in range(y_num):
    variable_name = f"qubit_label{i}"
    label = tk.Label(root,bg="#C4E1FF")
    exec(f"{variable_name} = label")
    exec(f"{variable_name}.config(text='q[{i}]')")
    exec(f"{variable_name}.place(x=270, y=200 + {i}*50)")
    exec(f"{variable_name}.lower()")
title_label = tk.Label(frame_container, text="RAA quantum circuit ( Lab330 )", bg="#FBFBFF",font=("Helvetica", 13,"bold"),width=25, height=2)
title_label.grid(row=0)
# title_label.config(='primary',)

group1_lableframe = tk.LabelFrame(frame_container, bg="#FBFBFF",text='build a circuit', padx=10, pady=10,)
group1_lableframe.grid(row=1, padx=5, pady=5, sticky="ew")


update_label = tk.Label(group1_lableframe,bg="#FBFBFF", text="Enter number of 1~10")
update_label.grid(row=0,columnspan=2)
update_button = tk.Button(group1_lableframe,text="Update",bg="#3F51B5",fg="white", command = update_button_command_,font=lato_font)
update_button.grid(row=1, column=1,padx=10)
update_entry = tk.Entry(group1_lableframe, width=10,bg='#ECECFF')
update_entry.grid(row=1, column=0,padx=17)
update_entry.bind("<Return>", update_button_command)


#輸入邊界
group2_lableframe = tk.LabelFrame(frame_container,bg="#FBFBFF", text='boundary', padx=10, pady=10,)
group2_lableframe.grid(row=2, padx=5, pady=5, sticky="ew")
bound_label = tk.Label(group2_lableframe,bg="#FBFBFF", text="Enter AOD and SLM boundaries")
bound_label.grid(row=0,columnspan=2)
for i in range(2):
    variable_name = f"architecture_label{i}"
    label = tk.Label(group2_lableframe,bg="#FBFBFF")
    exec(f"{variable_name} = label")
    exec(f"{variable_name}.grid(row=1+i, column=0)")
    variable_name = f"architecture_entry{i}"
    entry = tk.Entry(group2_lableframe,width=5,bg="#ECECFF")
    exec(f"{variable_name} = entry")
    exec(f"{variable_name}.grid(row=1+i, column=1)")

architecture_label0.config(text = "X")
architecture_label1.config(text = "Y  ( ≥3 )")


#gate
group3_lableframe = tk.LabelFrame(frame_container, bg="#FBFBFF",text='gate', padx=10, pady=10,)
group3_lableframe.grid(row=3, padx=5, pady=5, sticky="ew")
gate_label = tk.Label(group3_lableframe, bg="#FBFBFF",text="Put the gate into the line")
gate_label.grid(row=0,columnspan=3,pady=5)
for i in range(4):
    variable_name = f"gates_label{i}"
    label = tk.Label(group3_lableframe,bg="#FBFBFF")
    exec(f"{variable_name} = label")
    exec(f"{variable_name}.grid(row=1+i,column=0,padx=20)")
    variable_name = f"gates_entry{i}"
    entry = tk.Entry(group3_lableframe,width=4,bg='#ECECFF')
    exec(f"{variable_name} = entry")
    exec(f"{variable_name}.grid(row=1+i,column=1)")
    variable_name = f"gates_button{i}"
    button = tk.Button(group3_lableframe, text="Add",bg='#3F51B5',fg='white',font=lato_font_2)
    exec(f"{variable_name} = button")
    exec(f"{variable_name}.grid(row=1+i,column=2,padx=30)")
gates_entry4 = tk.Entry(group3_lableframe,width=4,bg="#ECECFF")
gates_entry4.grid(row=5,column=1)

gates_label0.config(text = "Rx")
gates_label1.config(text = "Ry")
gates_label2.config(text = "Rz")
gates_label3.config(text = "CZ")

#製造 y_num個線條放到最下層
for i in range(y_num):
    variable_name = f"gates_sequence_line{i}"
    label = tk.Label(root)
    exec(f"{variable_name} = label")
    exec(f"{variable_name}.place(x=310, y=210 + i*50, width=1050, height=1)")
    exec(f"{variable_name}.config(bg='#FFF7FB')")
    exec(f"{variable_name}.lower()")

#製造x_num*y_num個空白gate
for i in range(y_num):
    for j in range(x_num):
        variable_name = f"gates_sequence_button{i*x_num+j}"
        button = tk.Button(root)
        exec(f"{variable_name} = button")
        exec(f"{variable_name}.place(x=340+50*j, y=193+i*50, height=35, width=37)")
        exec(f"{variable_name}.lower()")
        variable_name = f"CZ_line{i*x_num+j}"
        ####線
        label = tk.Label(root, bg='#02DF82')
        exec(f"{variable_name} = label")
        exec(f"{variable_name}.place(x=358+j*50, y=210+i*50, width=3, height=50)")
        exec(f"{variable_name}.lower()")
# 按下會消失的功能
def button_command(j, i):
    def gate_delete():
        variable_name = f"gates_sequence_button{x_num * j + i}"
        exec(f"global {variable_name}")
        exec(f"{variable_name}.config(text = '', command='')")
        exec(f"{variable_name}.lower()")
        data_matrix[j][i] = ''
    return gate_delete
# CZ 按下會消失的功能
def CZ_button_command(initial_pos, final_pos, i):
    def gate_delete():
        variable_name = f"gates_sequence_button{x_num * initial_pos + i}"
        data_matrix[initial_pos][i] = ''
        exec(f"{variable_name}.config(text = '', command=None)")
        exec(f"{variable_name}.lower()")
        variable_name = f"gates_sequence_button{x_num * final_pos + i}"
        data_matrix[final_pos][i] = ''
        exec(f"{variable_name}.config(text = '', command=None)")
        exec(f"{variable_name}.lower()")
        for l in range(initial_pos + 1, final_pos):
            data_matrix[l][i] = ''
        for l in range(initial_pos, final_pos):
            variable_name = f"CZ_line{x_num * l + i}"
            exec(f"{variable_name}.lower()")
    return gate_delete

# 輸入gate到想要的位置
def gates_button0_command(event):
    global gates_sequence_numbers
    global data_matrix
    global interface_num
    text = gates_entry0.get()
    float_number = float(text)
    integer_number = int(float_number)
    if integer_number >= interface_num:
        return 0
    number = 0
    for i in range(x_num - 1, -1, -1):
        if data_matrix[integer_number][i] == "":
            number = i
        else:
            break
    variable_name = f"gates_sequence_button{x_num*integer_number + number}"
    data_matrix[integer_number][number] = 'Rx'
    exec(f"{variable_name}.config(text = 'Rx',font=lato_font, bg='#FF5151', command = button_command(integer_number, number))")
    exec(f"{variable_name}.lift()")
def gates_button1_command(event):
    global gates_sequence_numbers
    global data_matrix
    global interface_num
    text = gates_entry1.get()
    float_number = float(text)
    integer_number = int(float_number)
    if integer_number >= interface_num: return 0
    number = 0
    for i in range(x_num - 1, -1, -1):
        if data_matrix[integer_number][i] == "":
            number = i
        else:
            break
    variable_name = f"gates_sequence_button{x_num*integer_number + number}"
    data_matrix[integer_number][number] = 'Ry'
    exec(f"{variable_name}.config(text = 'Ry' ,font=lato_font,bg='#FF5151', command = button_command(integer_number, number))")
    exec(f"{variable_name}.lift()")
def gates_button2_command(event):
    global gates_sequence_numbers
    global data_matrix
    text = gates_entry2.get()
    float_number = float(text)
    integer_number = int(float_number)
    if integer_number >= interface_num: return 0
    number = 0
    for i in range(x_num - 1, -1, -1):
        if data_matrix[integer_number][i] == "":
            number = i
        else:
            break
    variable_name = f"gates_sequence_button{x_num * integer_number + number}"
    data_matrix[integer_number][number] = 'Rz'
    exec(f"{variable_name}.config(text = 'Rz',font=lato_font, bg='#FF5151', command = button_command(integer_number, number))")
    exec(f"{variable_name}.lift()")

def gates_button3_command(event):
    global gates_sequence_numbers
    global data_matrix
    text = gates_entry3.get()
    float_number = float(text)
    integer_number = int(float_number)
    if integer_number >= interface_num: return 0
    target_text = gates_entry4.get()
    target_float_number = float(target_text)
    target_integer_number = int(target_float_number)
    if target_integer_number >= interface_num: return 0
    larger_num = integer_number
    if target_integer_number < larger_num:
        integer_number = target_integer_number
        target_integer_number = larger_num
    max_num = 0
    for i in range(x_num - 1, -1, -1):
        column = [row[i] for row in data_matrix]
        All_empty = all(value == "" for value in column)
        if All_empty:
            max_num = i
        else:
            break
    data_matrix[integer_number][max_num] = 'CZ'
    data_matrix[target_integer_number][max_num] = 'CZ'
    for i in range(integer_number+1, target_integer_number):
        data_matrix[i][max_num] = '|'
    for i in range(integer_number, target_integer_number):
        variable_name = f"CZ_line{x_num*i + max_num}"
        exec(f"{variable_name}.lift()")
    variable_name = f"gates_sequence_button{x_num*integer_number + max_num}"
    exec(f"{variable_name}.config(text = 'CZ',font=lato_font)")
    exec(f"{variable_name}.config(bg='#02DF82')")
    exec(f"{variable_name}.config(command = CZ_button_command(integer_number, target_integer_number, max_num))")
    exec(f"{variable_name}.lift()")
    variable_name = f"gates_sequence_button{x_num*target_integer_number + max_num}"
    exec(f"{variable_name}.config(text = 'CZ',font=lato_font)")
    exec(f"{variable_name}.config(bg='#02DF82')")
    exec(f"{variable_name}.config(command = CZ_button_command(integer_number, target_integer_number, max_num))")
    exec(f"{variable_name}.lift()")

def gates_button0_command_():
    global gates_sequence_numbers
    global data_matrix
    global interface_num
    text = gates_entry0.get()
    float_number = float(text)
    integer_number = int(float_number)
    if integer_number >= interface_num:
        return 0
    number = 0
    for i in range(x_num - 1, -1, -1):
        if data_matrix[integer_number][i] == "":
            number = i
        else:
            break
    variable_name = f"gates_sequence_button{x_num*integer_number + number}"
    data_matrix[integer_number][number] = 'Rx'
    exec(f"{variable_name}.config(text = 'Rx', font=lato_font,bg='#FF5151', command = button_command(integer_number, number))")
    exec(f"{variable_name}.lift()")
def gates_button1_command_():
    global gates_sequence_numbers
    global data_matrix
    global interface_num
    text = gates_entry1.get()
    float_number = float(text)
    integer_number = int(float_number)
    if integer_number >= interface_num: return 0
    number = 0
    for i in range(x_num - 1, -1, -1):
        if data_matrix[integer_number][i] == "":
            number = i
        else:
            break
    variable_name = f"gates_sequence_button{x_num*integer_number + number}"
    data_matrix[integer_number][number] = 'Ry'
    exec(f"{variable_name}.config(text = 'Ry',font=lato_font, bg='#FF5151', command = button_command(integer_number, number))")
    exec(f"{variable_name}.lift()")
def gates_button2_command_():
    global gates_sequence_numbers
    global data_matrix
    text = gates_entry2.get()
    float_number = float(text)
    integer_number = int(float_number)
    if integer_number >= interface_num: return 0
    number = 0
    for i in range(x_num - 1, -1, -1):
        if data_matrix[integer_number][i] == "":
            number = i
        else:
            break
    variable_name = f"gates_sequence_button{x_num * integer_number + number}"
    data_matrix[integer_number][number] = 'Rz'
    exec(f"{variable_name}.config(text = 'Rz',font=lato_font, bg='#FF5151', command = button_command(integer_number, number))")
    exec(f"{variable_name}.lift()")

def gates_button3_command_():
    global gates_sequence_numbers
    global data_matrix
    text = gates_entry3.get()
    float_number = float(text)
    integer_number = int(float_number)
    if integer_number >= interface_num: return 0
    target_text = gates_entry4.get()
    target_float_number = float(target_text)
    target_integer_number = int(target_float_number)
    if target_integer_number >= interface_num: return 0
    larger_num = integer_number
    if target_integer_number < larger_num:
        integer_number = target_integer_number
        target_integer_number = larger_num
    max_num = 0
    for i in range(x_num - 1, -1, -1):
        column = [row[i] for row in data_matrix]
        All_empty = all(value == "" for value in column)
        if All_empty:
            max_num = i
        else:
            break
    data_matrix[integer_number][max_num] = 'CZ'
    data_matrix[target_integer_number][max_num] = 'CZ'
    for i in range(integer_number+1, target_integer_number):
        data_matrix[i][max_num] = '|'
    for i in range(integer_number, target_integer_number):
        variable_name = f"CZ_line{x_num*i + max_num}"
        exec(f"{variable_name}.lift()")
    variable_name = f"gates_sequence_button{x_num*integer_number + max_num}"
    exec(f"{variable_name}.config(text = 'CZ',font=lato_font)")
    exec(f"{variable_name}.config(bg='#02DF82')")
    exec(f"{variable_name}.config(command = CZ_button_command(integer_number, target_integer_number, max_num))")
    exec(f"{variable_name}.lift()")
    variable_name = f"gates_sequence_button{x_num*target_integer_number + max_num}"
    exec(f"{variable_name}.config(text = 'CZ',font=lato_font)")
    exec(f"{variable_name}.config(bg='#02DF82')")
    exec(f"{variable_name}.config(command = CZ_button_command(integer_number, target_integer_number, max_num))")
    exec(f"{variable_name}.lift()")


gates_button0.config(command = gates_button0_command_)
gates_button1.config(command = gates_button1_command_)
gates_button2.config(command = gates_button2_command_)
gates_button3.config(command = gates_button3_command_)

gates_entry0.bind("<Return>", gates_button0_command)
gates_entry1.bind("<Return>", gates_button1_command)
gates_entry2.bind("<Return>", gates_button2_command)
gates_entry3.bind("<Return>", gates_button3_command)
gates_entry4.bind("<Return>", gates_button3_command)
interface_num = 0
CZ_control=0

#刷新畫面，如果前面是空的讓gate往前移動
def refresh():
    global gate_delete
    global interface_num
    global CZ_control
    CZ_control_colume = -1
    initial_pos = 0
    final_pos = 0
    root.after(300, refresh)

    for i in range(x_num-1):
        for j in range(interface_num):
            if data_matrix[j][i] == "":
                if (data_matrix[j][i+1] == "Rx") or (data_matrix[j][i+1] == "Ry") or (data_matrix[j][i+1] == "Rz"):
                    variable_name = f"gates_sequence_button{x_num * j + i}"
                    data_matrix[j][i] = data_matrix[j][i+1]
                    data_matrix[j][i + 1] = ''
                    exec(f"{variable_name}.config(text = data_matrix[j][i], bg='#FF5151', command = button_command(j, i))")
                    exec(f"{variable_name}.lift()")
                    variable_name = f"gates_sequence_button{x_num * j + i + 1}"
                    exec(f"{variable_name}.config(text = '', command='')")
                    exec(f"{variable_name}.lower()")
                elif (data_matrix[j][i+1] == "CZ"):
                    if (CZ_control == 0) or (CZ_control_colume != i) :
                        CZ_control_colume = i
                        CZ_control = 1
                        initial_pos = j
                    elif (CZ_control == 1) and (CZ_control_colume == i):
                        CZ_control = 0
                        final_pos = j
                        column = [row[i] for row in data_matrix[initial_pos: final_pos+1]]
                        All_empty = all(value == "" for value in column)
                        if All_empty:
                            for k in range(initial_pos, final_pos):
                                variable_name = f"CZ_line{x_num * k + i}"
                                exec(f"{variable_name}.lift()")
                                variable_name = f"CZ_line{x_num * k + i + 1}"
                                exec(f"{variable_name}.lower()")
                            for k in range(initial_pos, final_pos+1):
                                data_matrix[k][i] = data_matrix[k][i + 1]
                                data_matrix[k][i + 1] = ''
                                variable_name = f"gates_sequence_button{x_num * k + i + 1}"
                                exec(f"{variable_name}.config(text = '', command='')")
                                exec(f"{variable_name}.lower()")
                            variable_name = f"gates_sequence_button{x_num * initial_pos + i}"
                            exec(f"{variable_name}.config(text = data_matrix[initial_pos][i], bg='#02DF82', command=CZ_button_command(initial_pos, final_pos, i))")
                            exec(f"{variable_name}.lift()")
                            variable_name = f"gates_sequence_button{x_num * final_pos + i}"
                            exec(f"{variable_name}.config(text = data_matrix[final_pos][i], bg='#02DF82', command=CZ_button_command(initial_pos, final_pos, i))")
                            exec(f"{variable_name}.lift()")

refresh()

#執行按鈕功能
def run():
    global data_matrix
    global interface_num
    data_matrix_T = [[row[i] for row in data_matrix] for i in range(len(data_matrix[0]))]
    control = 0
    control_colume = -1
    initial = 0
    final = 0
    architecture = []
    data = []
    architecture += [0, int(architecture_entry0.get())]
    architecture += [0, int(architecture_entry1.get())]

    # 创建 "running..." 标签
    running = tk.Label(main_frame, text="running...", bg='#F3F3FA', fg='black', relief=tk.RAISED, borderwidth=2,
                       width=40, height=3)
    running.pack(pady=100)
    root.update()

    for i in range(x_num):
        for j in range(interface_num):
            if (data_matrix_T[i][j] == "Rx"):
                data += [("Rx", (j,))]
            elif (data_matrix_T[i][j] == "Ry"):
                data += [("Ry", (j,))]
            elif (data_matrix_T[i][j] == "Rz"):
                data += [("Rz", (j,))]
            elif (data_matrix_T[i][j] == "CZ"):
                if (control == 0) or (control_colume != i):
                    control_colume = i
                    control = 1
                    initial = j
                elif (control == 1) and (control_colume == i):
                    control = 0
                    final = j
                    data += [("CZ", (initial, final))]

    tmp = FPQA()
    tmp.setArchitecture(architecture)
    tmp.setProgram(data)
    ts = tmp.solve(data)

    # 在操作完成后销毁 "running..." 标签
    running.destroy()

    animateFPQA('./results/' + str(ts) + '.json')
    def open_video_with_media_player(video_path):
        try:
            # 調用系統預設的媒體播放器來打開影片
            subprocess.call(['start', video_path], shell=True)  # 適用於 Windows
        except Exception as e:
            print("Error opening video:", e)

    # 在你的程式碼中適當的地方調用這個函數，並傳入影片檔案路徑
    video_path = './results/' + str(ts) + '.mp4'
    open_video_with_media_player(video_path)

    

# 執行按鈕
group4_lableframe = tk.LabelFrame(frame_container, text='execute program',bg="#FBFBFF", padx=5, pady=5)
group4_lableframe.grid(row=4, padx=5, pady=5, sticky="ew")
variable_name = f"run_button"
button = tk.Button(group4_lableframe, text="Run",fg='white',bg="#3F51B5",width=10,height=1,font=lato_font)
exec(f"{variable_name} = button")
exec(f"{variable_name}.config(command=run)")
exec(f"{variable_name}.grid(row=1,padx=70,pady=2)")

frame_container = tk.Frame(root)
frame_container.pack()





root.mainloop()