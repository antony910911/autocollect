# 從 DNA 到最適培養：計算程式

教材「從 DNA 到最適培養：建模與視覺化」第 4–9 章的圖和數字都來自這裡。用的是 COBRApy 內建的大腸桿菌核心模型，不需要網路。

```bash
pip install -r requirements.txt
python dfba.py           # 產生 pFBA 查表 tables.json（約 10 秒）
python experiments.py    # 跑全部計算實驗，結果寫到 results.json（約 2 分鐘）
python protocol.py       # 把最適條件換算成操作單，寫到 protocol.json
python labdata.py        # 產生示範實驗數據（example-data/ 的兩個 CSV）
python calibrate.py      # 用實驗數據校正模型參數，寫到 calibration.json
python engineered.py     # 第 16 章：基改菌株的生產包絡線

# 有自己的定序資料時（第 2、15、16 章）
python genome_tools.py stats    WT.fasta MUT.fasta
python genome_tools.py compare  WT.fasta MUT.fasta --out novel.fasta
python genome_tools.py orfs     novel.fasta --prot novel_proteins.faa
python genome_tools.py cassette WT.fasta MUT.fasta novel.fasta
python genome_tools.py plan     --genome MUT.fasta --out annotate.sh
python make_figures.py   # 依結果畫圖
cd ../simulator && python build.py   # 產生互動模擬器 index.html
```

| 檔案 | 內容 |
|---|---|
| `gem.py` | 載入模型、FBA／pFBA、影子價格、基因剔除 |
| `dfba.py` | 動態通量平衡分析（每步解線性規劃或查表）、溫度與 pH 基點模型、遲滯期 |
| `experiments.py` | 1 FBA（供氧、碳源、相平面、基因剔除、流量圖）2 批次培養與生長曲線擬合 3 兩階段與敏感度 4 溫度 × pH 5 一次改一個因子／隨機／貝氏最適化 |
| `protocol.py` | 第 10 章：供氧換算 kLa 與容器、接種量、取樣時程、OD 切換門檻與查核對照表、蒙地卡羅容許範圍、異常處置表 |
| `labdata.py` | 產生示範用的實驗數據（真實參數刻意和預設值不同，用來示範校正） |
| `calibrate.py` | 第 11 章：讀 CSV、品質檢查、算衍生量、最小平方校正、驗證批次評估、參數可辨識性 |
| `example-data/` | `batches.csv`（條件，每批一列）與 `samples.csv`（量測，每次取樣一列）——可以直接當你的資料範本 |
| `genome_tools.py` | 第 2、15、16 章：組裝統計、野生株 vs 基改株的 k-mer 比對、找 ORF 與模體、定位插入點、產生完整註解流程的指令稿 |
| `engineered.py` | 第 16 章：把異源反應加進模型、算生產包絡線與成長耦合 |
| `annotation.py` | 第 17 章：讀定序廠的註解包（GFF／faa／xlsx）。`summary` 用 Pfam 家族計數獨立驗證拷貝數並看插入點旁邊有什麼；`fix-gff` 把轉殖基因修成單一 exon（RNA-seq 計數前必做）；`gem-map` 產生 rhto-GEM 基因對照的指令與腳本（比對要在你自己的電腦上跑）。需要 `openpyxl` |
| `blast_neighbours.py` | 第 17 章：讀 NCBI blastp 的 XML，回答「插入點旁邊那個基因是什麼」。算命中的分類分佈、起始密碼子對不對、保守核心落在哪一段、低複雜度區的組成，並標出 ppg4／mucin 這類由低複雜度區造成的誤標。**不連網**，XML 要自己去 NCBI 跑 |
| `rhto.py` | 第 20 章：把 rhto-GEM 跑起來。六個子指令——`check`（模型概況）、`find`（用名字查 id）、`medium`（設碳源與 C/N）、`afs`（加 α-farnesene 反應）、`envelope`（生產包絡線）、`scan`（掃 C/N 與 ERG9）。**一律用名字找 id、不寫死流水號。** 模型檔要自己下載；路徑寫 `textbook` 可以先用內建模型練手 |
| `rhto_afs.py` | 第 21 章：核對別人做好的「rhto-GEM ＋ AFS」模型，並補上它沒算的。重算配平／漏洞／生產包絡線，另外做葡萄糖吸收敏感度、ERG9 調降（**固定生長速率**才公平）、C/N 掃描、FPP 競爭者、拷貝數在 FBA 裡有沒有用。模型檔不在 repo 裡，執行時指定路徑 |
| `yeast.py` | 第 15 章：載入 Yeast8／rhto-GEM 等酵母菌模型、檢查、設厭氧、剔除基因（需自行下載模型，要在你自己的電腦上跑） |
| `workflow.py` | 第 19 章：把「C/N 要 20」換算成「秤幾公克葡萄糖、幾公克硫酸銨」。培養基、接種量、容器與 kLa、十二烷與內標、取樣時程、碳的理論上限。每個數字標了出處等級（算出來的／文獻／起始猜測） |
| `make_figures.py` | 畫教材的圖 |
| `map_layout.json` | 中心代謝流量圖的版面（第 4 章圖與模擬器共用） |
| `tables.json`、`results.json`、`protocol.json`、`calibration.json`、`annotation.json`、`workflow.json`、`blast_neighbours.json`、`rhto_demo.json`、`rhto_afs.json` | 最近一次的計算結果（教材引用的就是這份） |

## 換成你的菌

1. 用 CarveMe 或 gapseq 從你的基因體產生模型（SBML 檔），在 `gem.py` 的 `load()` 改成 `cobra.io.read_sbml_model("你的模型.xml")`。
2. 修改 `gem.py` 裡的 `BIOMASS`、`EXCHANGE`、`MAP_RXNS` 成你的模型的反應名稱。
3. 用你的實驗數據修改 `dfba.Params` 的吸收速率、耗氧上限、溫度與 pH 基點值。
4. 修改 `protocol.py` 最上方的換算常數：`OD_TO_GDW`（你的檢量線）、`VESSELS`（你實測的 kLa）。
5. 把你的實驗數據整理成 `example-data/` 那兩個 CSV 的格式，用 `calibrate.py` 校正參數（第 11 章）。
6. 依序執行上面幾個指令。
