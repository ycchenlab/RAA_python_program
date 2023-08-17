目前動畫部分有一個bug：y軸最下面那一排的移動動畫跑不出來，目前尚未解決，但計算部分是沒有問題的

為了讓整體動畫運行順利，我將solve裡面的coord_D -= (coord_U -1)變成了coord_D -= (coord_U -2)，
並且更改animation當中的COORD_D = data['coord_d'] - 1、AOD_D = data['coord_d'] - 1，也因此在設定Y軸大小時請輸入3以上的數字

同時檔案內都有保留原本的程式碼(用#做成文字檔)
若想要原先上下空間(one qubit gate/two qubit gate)大小相同的運算，將上述程式碼改回即可。