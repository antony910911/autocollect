---
name: genome-compare
description: 要比對兩份基因體組裝（野生株 vs 基改株）、找出插入的外源 DNA、確認轉殖基因的拷貝數與整合位置、或把設計的構築序列對回定序結果時使用。
---

# 定序組裝的比對與解讀

工具在 `lessons/dna-to-culture/code/genome_tools.py`。這份 SKILL 除了流程，更重要的是**四個會產生「看起來很合理但完全錯誤」結論的坑**——每一個我們都實際踩過。

## 四個坑（先讀這段）

### ① 取序列忘記記錄股向

探針命中負股時，必須取**反向互補**再轉譯。

```python
if strand > 0:
    cds = seq[i:i + len(ref)]
else:
    cds = rc(seq[i + 60 - len(ref):i + 60])   # 60 = 探針長度
```

忘記這件事會得到一整份假突變清單——我們第一輪就這樣，12 個拷貝「每個都有 313–383 bp 突變」「都在第 81 個密碼子提前終止」。數量和位置都很合理，所以看不出是錯的。修正後真實結果是 **11 個拷貝逐鹼基零差異**。

**股向要當成資料的一部分記下來，不要事後推。**

### ② 用 GC 當外來 DNA 的唯一判準

密碼子最佳化過的基因，GC 會和宿主一樣高：

| | GC |
|---|---|
| 宿主基因體 | 61.3% |
| 蘋果原生 AFS | 約 42% |
| **實際插入的 AFS** | **63.3%** |

用 GC 篩會整個漏掉它，同時把一堆 AT-rich 低複雜度重複標成「可能是外來 DNA」（轉譯出來是 `KKKKKK`、`GGGGGG`，而且兩株都有）。

**要用三個條件並用：連續的新增區段 ＋ 完整 ORF ＋ 保守模體。**

### ③ 模體掃描沒有和背景比

模體只有 5–6 bp，隨機序列本來就會出現。「P1 有 0 個 GATA 位點」聽起來像結論，但宿主基因體隨機抓 1 kb 也有 **47.6%** 的機會是 0——完全沒有資訊。

`code/promoter_scan.py` 會自動從宿主基因體抽 2,000 段同長度片段當背景。**沒有背景分布就不要下結論。**

### ④ 送 BLAST 前沒切掉載體殘跡

從構築切出來的「啟動子」前面可能接著 pUC／M13 的 lac 區段和選殖位。帶著去 BLAST 只會命中一整頁的選殖載體。

切之前先找這些標記：`GGAAACGACAATCTGATC`（M13）、`GTCACGACGTTGTAAAACGACGGCCAGT`（M13 -20）、常見限制酶位點。NCBI 的 VecScreen 也可以自動檢查。

## 流程

```bash
cd lessons/dna-to-culture/code

# 1. 組裝品質（contig 數、N50、GC、N 含量）
python genome_tools.py stats WT.fasta MUT.fasta

# 2. k-mer 比對：找出「只有其中一邊有」的連續區段
python genome_tools.py compare WT.fasta MUT.fasta --out novel.fasta

# 3. 看那些區段有沒有完整 ORF 與保守模體
python genome_tools.py orfs novel.fasta --prot candidates.faa

# 4. 用側翼序列定位插入點
python genome_tools.py cassette WT.fasta MUT.fasta novel.fasta

# 5. 有構築序列的話——這一步最有價值
python genome_tools.py construct construct.fasta MUT.fasta

# 6. 啟動子的模體掃描（會自動抓背景）
python promoter_scan.py --construct construct.fasta --genome MUT.fasta
```

### 為什麼第 5 步最有價值

沒有構築序列只能說「有一個 5,385 bp 的重複單元」；有了構築才能說「那是 T-DNA，骨架進去 2–3 份，第 3 個拷貝斷在第 530 個密碼子」。

**所以做基改之前就要把構築序列存好。**

### 為什麼用 k-mer 錨點而不是一般比對

串聯重複會讓比對軟體在重複單元之間跳動，接合點位置不可信。用「構築上唯一出現的 k-mer」當錨點逐鹼基追蹤，斷點可以定到單一鹼基（實測 74,947 個錨點、19 段片段）。

## 解讀的原則

- **拷貝數只有下限。** 組裝會把高度相同的重複壓縮。要定量得把原始讀段比回單一拷貝算深度。
- **蛋白質身分是推定的。** 這個環境連不上資料庫，所有身分判定靠模體與逐字比對已知序列。
  **一定要在報告裡寫「需要 BLASTp 確認」**，並把序列切成獨立 FASTA 給使用者。
- **序列回答不了表現量與酵素活性。** 要 RT-qPCR 和產物量測。
- **資料和實驗紀錄對不上時，先懷疑標籤。** 這次「WT 檔案裡有 12 個轉殖拷貝、基改檔案裡 0 個」，
  最可能的解釋是樣品或檔名交換。**在使用者用 PCR 釐清之前，只能說「帶有插入的那一份」。**

## 產出

給使用者的東西放成獨立 FASTA，附上要拿去做什麼：

| 檔案 | 用途 |
|---|---|
| `*_prot.fasta` | 貼到 BLASTp 確認身分 |
| `*_cds.fasta` | 設計 PCR／qPCR 引子 |
| `insertion_junction.fasta` | 定點 PCR 驗證插入位置 |
| `promoter_*.fasta`（切乾淨的） | BLASTn 查啟動子來源 |

報告要有「方法與限制」一節，寫清楚哪些是逐字比對確認的、哪些是模體推定的、哪些查不到。
