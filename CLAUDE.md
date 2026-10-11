# 專案說明（Claude Code 每次開啟自動載入）

這個 repo 有兩條主線：

1. **生質能週報**（`autocollect/`、`reports/`）：每週自動收集資料，產生每個事實都附來源的分析報告，上傳到 Folio。細節見 `README.md` 與 `ROUTINE.md`。
2. **圖解教材**（`lessons/`）：主題式教材，推送到 Folio 筆記本「Claude圖解教材」，一門教材一個分區、一章一頁。

使用者是中文使用者，**所有教材內容、圖表文字、commit 訊息都用繁體中文（臺灣用語）**。

## 教材的做法（最常用到的部分）

### 目錄與設定

```
lessons/<課程名>/
  course.yaml          # 放進哪本筆記本、哪個分區、頁面 id 前綴
  README.md            # 導讀（會成為分區的第一頁）
  01-xxx.md … NN-xxx.md
  figures/             # 圖（PNG）
    src/diagrams.py    # SVG 示意圖 → Chromium 轉 PNG
    src/charts.py      # matplotlib 圖
  code/                # 可執行的計算程式（圖和數字的來源）
```

`course.yaml` 用 `find_by_name: true` 依名稱找使用者自己建的筆記本，不要另外建新的。

### 現有教材

| 資料夾 | 主題 | 分區 |
|---|---|---|
| `lessons/ammonia/` | 氨氮降解 | 氨氮降解基礎教材 |
| `lessons/aiot/` | 沼氣與廢水處理 AIoT 入門 | 沼氣與廢水處理 AIoT |
| `lessons/aiot-advanced/` | 沼氣 AIoT 進階建模 | 沼氣 AIoT 進階：建模實作 |
| `lessons/dna-to-culture/` | 從 DNA 到最適培養（18 章） | 從 DNA 到最適培養：建模與視覺化 |
| `lessons/using-claude/` | 把 Claude 用好（11 章，給研究者的實戰手冊） | 把 Claude 用好：給研究者的實戰手冊 |

### 寫教材的規矩（重要）

- **數字要是真的算出來的**。圖和表裡的數值由 `code/` 的程式產生，結果存成 JSON，章節引用那份 JSON。不要憑印象寫數字。
- **誠實**。模擬資料要標明是模擬；推論要標明是推論（例如各課的「創新思路」章整章標示為推論）；模型失準、參數無法辨識、外推不可信這類負面結果要照實寫出來，那通常是最有價值的教學點。
- **參考文獻放每章最後**，格式 `1. 作者 (年). 標題. *期刊*, 卷, 頁. https://doi.org/...`。CI 會逐筆到 Crossref 核對標題與年份，**寫錯會讓 build 失敗**，所以不確定的文獻寧可不放 DOI（只放網址），也不要猜 DOI 或猜標題。
- **圖要檢查**。畫完一定要用 Read 看一次 PNG。常見問題：
  - 標籤重疊、文字超出方塊或畫布
  - 對數軸負號變成亂碼（用 `FuncFormatter` 自己格式化）
  - **`svgkit` 不會自動換行**。長句要自己按「實際寬度」斷行（用 `_w()` 量），
    不要按字數切——按字數會把 `R. toruloides` 切成 `R. t` ＋ `oruloides`。
  - `svgkit` 不支援 Markdown，字串裡的 `**粗體**` 會原樣印出來。
- **版面要檢查**。推送前跑 `python lessons/_tools/check_layout.py`，
  確認 Folio 頁面上的文字框與圖片不會疊在一起。

### 常用指令

```bash
# 預覽要上傳的頁面（不會真的上傳）
python -m autocollect lessons --dir lessons/<課程> --dry-run

# 跑測試
python -m pytest -q tests

# 產生圖
python lessons/<課程>/figures/src/diagrams.py [圖名 ...]
python lessons/<課程>/figures/src/charts.py
python lessons/<課程>/code/make_figures.py

# 版面檢查（推送前一定要跑）
python lessons/_tools/check_layout.py              # 全部
python lessons/_tools/check_layout.py lessons/<課程>
```

Folio 的上傳由 GitHub Actions（`.github/workflows/lessons.yml`）做，**本機沒有 `FOLIO_SYNC_TOKEN`**，所以推送到分支後要去確認 Actions 的兩個 job（核對 DOI、上傳到 Folio）都成功。

### 環境限制

- **沒有對外網路，只有 WebSearch 工具可用**。`curl` 會被閘道擋（403），`WebFetch` 對期刊網站、
  NCBI 等網域直接 DNS 失敗。所以：
  - 不能下載 BiGG、Yeast8、rhto-GEM 等模型檔 → 這類程式要寫成「使用者在自己電腦上執行」
  - 不能跑 BLAST、不能連 Crossref → DOI 核對只能靠 CI
  - 不能讀論文全文 → 只能靠 WebSearch 的摘要，**而且要在教材裡標明沒核對過全文**
- **背景指令不要接 `| tail`**。`tail` 會把輸出整個緩衝住，工作跑了十分鐘你也看不到進度。
  用 `python -u` 直接輸出，或重導到檔案再讀。
- Chromium 在 `/opt/pw-browsers/chromium`，`svgkit.render()` 已處理。
- 中文字型用 `WenQuanYi Zen Hei`，matplotlib 要加 `DejaVu Sans` 當 fallback，否則上下標與負號會變方框。

## 使用者的實際研究題目

寫 `lessons/dna-to-culture/` 相關內容時，這些背景要納入考量：

- **菌株**：*Rhodotorula toruloides*（紅酵母，舊名 *Rhodosporidium toruloides*）**IFO 8766**。
  - 它是 **IFO 0559（交配型 A）× IFO 0880（交配型 a）的二倍體接合株**，也是這個種的模式菌株；其他編號：NBRC 8766、CBS 6016、DSM 4444。
  - 使用者用的參考基因體是 JGI MycoCosm 的 `Rhoto_IFO0880_4`。**兩個親本的基因體 JGI 都有**（IFO 0880 與 IFO 0559），可以分開兩套單倍型。
- **基改**：把**蘋果的 α-farnesene 合成酶（AFS）**以農桿菌隨機嵌入（ATMT）放進這株菌。

### 定序比對已經確定的事（第 17 章，不用重跑）

- 兩份組裝 99.836% 的 31-mer 共有，是同一株菌。
- **標示為 `Rt_WT` 的那一份帶有轉殖陣列，標示為 `A13_4` 的完全沒有**（AFS 的 31-mer 存在比例 0.00%）。
  兩種可能：樣品／檔名交換，或 A13_4 丟失了構築。**使用者尚未用 PCR 釐清**，
  所以談到這兩株時要說「帶有插入的那一份」，不要說「基改株」。
- 構築 11,647 bp 環狀：T-DNA 5,447 bp（LB 125 → RB 5,597），骨架 6,050 bp。
- 染色體上是 Contig3 943,094–1,019,311 的 **76,217 bp 串聯陣列**：
  T-DNA 進去 11–12 份、骨架 2–3 份；**12 個 AFS 拷貝中 11 個與設計逐鹼基零差異**，
  拷貝 #3 斷在陣列接合點（CDS 第 1,587 bp ＝ 第 530 個密碼子）。
- 插入點在無插入株的 Contig4 942,770–942,830（兩側側翼只隔 60 bp，單一位點、無重排）。
- **兩個啟動子的身分未知**——不在宿主基因體裡，也不是 35S／nos／trpC。
  這件事卡住「限氮階段 AFS 還有沒有在表現」，進而卡住分階段培養的設計。
  要用 BLASTn（序列要先切掉前面 216 bp 的 pUC 載體殘跡）或不同 C/N 下的 RT-qPCR 解決。
- **這代表什麼**（已寫進第 15、16 章）：
  - 是**真核生物**，細菌的工具鏈（Prokka／Bakta、CheckM2、GTDB-Tk、CarveMe、gapseq）都不適用。
  - 是**產油酵母，不是釀酒酵母**：Crabtree 陰性、氮限制（高 C/N）觸發油脂累積、菌體紅色會干擾 OD600、可直接用木糖與乙酸。不要套用 *S. cerevisiae* 的經驗。
  - 代謝模型要用 **rhto-GEM**（Tiukova et al. 2019，建在 IFO 0880 上），不是 Yeast8。
  - α-farnesene 是倍半萜，從 FPP 做；競爭者是油脂（搶乙醯輔酶 A）、ERG9／麥角固醇與類胡蘿蔔素（搶 FPP）。
  - 產物揮發，要用十二烷等有機相覆蓋收集，否則量到的產量嚴重低估。

## 這個 repo 的技能（`.claude/skills/`）

| 技能 | 什麼時候會用到 |
|---|---|
| `lesson-chapter` | 新增或修改一章教材、加一張圖 |
| `cite-check` | 加參考文獻、查證數字出處（CI 會核對 DOI） |
| `genome-compare` | 比對兩份基因體組裝、把構築對回定序結果 |

技能的完整內容在各自的 `SKILL.md`。下面「序列分析的規矩」是 `genome-compare` 的摘要，
放在這裡是因為它值得每次都看到。

## 序列分析的規矩（都是實際踩過的坑）

- **取序列一定要記錄股向**。探針命中負股時要取反向互補再轉譯。忘記這件事會產生
  一整份「看起來很合理」的假突變清單（我們第一輪就這樣，每個拷貝都「有 313–383 bp 突變」）。
- **GC 不能當外來 DNA 的唯一判準**。密碼子最佳化過的基因 GC 會和宿主一樣高
  （這個案子：宿主 61.3%、插入的 AFS 63.3%）。要用「連續新增區段 ＋ 完整 ORF ＋ 保守模體」三者並用。
- **模體掃描一定要和背景比**。模體只有 5–6 bp，隨機序列本來就會出現。
  沒有背景分布就沒有意義（`code/promoter_scan.py` 會自動抽 2,000 段宿主序列當背景）。
- **送資料庫比對前先切掉載體殘跡**。帶著 pUC／M13 去 BLAST 只會命中一堆選殖載體。
- **串聯重複用一般比對軟體會在單元之間跳動**。要用「構築上唯一的 k-mer」當錨點逐鹼基追蹤
  （`genome_tools.py construct`），接合點才定得準。

## Git

- 開發分支：`claude/ammonia-nitrogen-degradation-a0nidi`（不要推到其他分支）。
- commit 訊息用繁體中文，第一行簡述、空行後列重點。
- 除非使用者明確要求，**不要開 pull request**。
