# 第 7 章　踩過的坑與排解

這一章是實際跑的時候撞到的問題。照原文整理，分成四類。

## 7.1 把輸出當成指令貼進終端機

這一類最常發生，而且最容易讓人以為是自己電腦壞了。

| 症狀 | 原因 | 解法 |
|---|---|---|
| 輸入 `phaC` 之後出現 `phaC: command not found`，Ubuntu 建議你 `sudo apt install php-cli` | 把**基因名稱**當成指令貼進終端機了 | 基因名要放在引號裡：`grep -ni 'phaC' "$GBFF"`。**絕對不要**照 Ubuntu 的建議去裝 PHP |
| 把範例輸出（`/product="..."`、`BMB171_RS06645`）整段貼進去執行 | 那是「你應該看到的畫面」，不是指令 | 只複製 ` ```bash ` 區塊裡面的內容。貼錯不會弄壞任何東西，就是會出一堆 command not found |
| `carve: command not found`，Ubuntu 建議 `sudo apt install carve` | CarveMe 還沒裝好；apt 裡那個 `carve` 是完全不同的軟體 | `conda install -c bioconda carveme diamond pyscipopt -y`，再用 `command -v carve` 確認路徑指向 `envs/btcobra/bin/carve` |

> **一個通則**：終端機建議你 `sudo apt install 某某` 的時候，先想一下那個東西是不是你真的要的。它只是在猜「哪個套件提供了這個指令名稱」，常常猜到完全不相干的東西。

## 7.2 模型與程式碼

| 症狀 | 原因 | 解法 |
|---|---|---|
| **最大 PHB 有數字，但 `PHAB_NADPH = 0`** | BiGG 的 `3hbcoa_c` 是 (S) 型，`ECOAH1` 可以反向生成它，模型就繞過 PhaB 了 | 建立專屬的 `3hbcoa_R_c`（第 5.5 節）。**這是整份分析最重要的一個坑** |
| 把 `WP_xxxxxxxxx.1` 放進模型 | 那是占位示意文字，不是真的 ID | 用第 4.4 節的 Biopython 查出真正的 protein ID |
| GPR 寫 `WP_000250409.1` 無效 | COBRApy 的 gene ID 不吃小數點 | 改成 `WP_000250409_1` |
| 設 medium 時出現 KeyError | 模型裡沒有那個交換反應 | 一定要加 `{k: v for k, v in medium.items() if k in model.reactions}` |
| `mass balance` 印出一堆元素而不是 `{}` | 反應式配平錯，或代謝物的 formula／charge 填錯 | 檢查 `add_metabolites` 的係數，以及代謝物的 `formula` 和 `charge` |
| `Growth` 的元素平衡全是負值 | 正常。它是 pseudo-reaction，本來就是把前驅物抽走 | 不需要修 |
| 剔除之後 PHB = −5.7E−15 | 求解器的浮點誤差 | 視為 0 |
| 某些組合 `infeasible` | 生長下限需要的氨氮超過你設的上限 | 這是約束正確運作的證據。想避開就提高 `NH4_limit`（第 6.5 節） |
| `No such file or directory: curate_BMB171_PHA_model.py` | heredoc 沒寫完整，或 nano 沒存檔 | 用 `ls -lh` 和 `tail -n 5` 確認檔案存在且結尾完整。nano 存檔是 `Ctrl+O` → Enter → `Ctrl+X` |

## 7.3 檔案與 Windows 互通

| 症狀 | 原因 | 解法 |
|---|---|---|
| `less` 裡面執行 `explorer.exe .` 出現 `No log file` | 你還在 less 裡面 | 先按 `q` 離開再執行 |
| Excel 開檔視窗看不到 `.tsv` | Excel 預設只篩 `.txt`／`.csv` | `cp xxx.tsv xxx.txt`，再用「資料 → 從文字/CSV」匯入，編碼選 **65001 UTF-8**、分隔符號選 **定位點/Tab** |
| Excel 裡空白欄位變成數字 `15` | 雙擊開啟造成的內容誤判 | 重新用「從文字/CSV」匯入，不要雙擊開啟 |
| `df.to_excel` 失敗 | 缺 `openpyxl` | CSV 還是會正常產生；要 Excel 就 `conda install openpyxl` |

### 要去 Windows 看檔案

```bash
explorer.exe .                                   # 開啟目前資料夾（注意最後是「空格 + 句點」）
cmd.exe /c start .                               # 備用寫法
\\wsl$\Ubuntu-24.04\home\<帳號>\Bt_PHA_analysis   # 直接貼進檔案總管網址列
wsl.exe -l -q                                    # 查發行版的正確名稱
```

複製結果到桌面：

```bash
WINUSER=$(cmd.exe /c echo %USERNAME% | tr -d '\r')
mkdir -p "/mnt/c/Users/$WINUSER/Desktop/Bt_PHA_results"
cp ~/Bt_PHA_analysis/03_candidate_genes/*.tsv "/mnt/c/Users/$WINUSER/Desktop/Bt_PHA_results/"
explorer.exe "/mnt/c/Users/$WINUSER/Desktop/Bt_PHA_results"
```

## 7.4 一個通則：數字正常不代表沒事

這份分析裡最貴的一個坑（第 5.5 節）有一個特徵：**它不報錯。**

模型照常收斂、照常給你 12.5、mass balance 照常是 `{}`。如果不是有人特地去看 `PHAB_NADPH` 的通量，整份分析會帶著一個錯誤的路徑一路算下去，而且**結果看起來完全合理**。

所以在這類工作裡，「跑得出來」不是驗收標準。要有明確的驗收條件：

| 做了什麼 | 驗收條件 |
|---|---|
| 補一條反應 | 它的通量 > 0 |
| 建一個新代謝物 | 列出它連到的反應，只能有你預期的那幾條 |
| 補一條路徑 | 剔掉路徑上的基因，產物要歸零 |
| 算出一個產率 | 和課本的化學計量上限比一下，差太多要解釋得出來 |

最後那一條就是第 1.2 節做的事——而且確實抓到東西了。
