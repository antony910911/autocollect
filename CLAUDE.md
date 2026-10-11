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
| `lessons/dna-to-culture/` | 從 DNA 到最適培養（16 章） | 從 DNA 到最適培養：建模與視覺化 |

### 寫教材的規矩（重要）

- **數字要是真的算出來的**。圖和表裡的數值由 `code/` 的程式產生，結果存成 JSON，章節引用那份 JSON。不要憑印象寫數字。
- **誠實**。模擬資料要標明是模擬；推論要標明是推論（例如各課的「創新思路」章整章標示為推論）；模型失準、參數無法辨識、外推不可信這類負面結果要照實寫出來，那通常是最有價值的教學點。
- **參考文獻放每章最後**，格式 `1. 作者 (年). 標題. *期刊*, 卷, 頁. https://doi.org/...`。CI 會逐筆到 Crossref 核對標題與年份，**寫錯會讓 build 失敗**，所以不確定的文獻寧可不放 DOI（只放網址），也不要猜 DOI 或猜標題。
- **圖要檢查**。畫完一定要用 Read 看一次 PNG，常見問題是標籤重疊、文字超出畫布、對數軸負號變成亂碼（用 `FuncFormatter` 自己格式化）。
- **版面要檢查**。推送前跑一次 overlap 檢查（見下方指令），確認 Folio 頁面上的文字框與圖片不會疊在一起。

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
```

Folio 的上傳由 GitHub Actions（`.github/workflows/lessons.yml`）做，**本機沒有 `FOLIO_SYNC_TOKEN`**，所以推送到分支後要去確認 Actions 的兩個 job（核對 DOI、上傳到 Folio）都成功。

### 環境限制

- **沒有對外網路**（除了 WebSearch 工具）。不能下載 BiGG、Yeast8 等模型檔，也不能連 Crossref——DOI 核對只能靠 CI。需要下載模型的程式要寫成「使用者在自己電腦上執行」。
- Chromium 在 `/opt/pw-browsers/chromium`，`svgkit.render()` 已處理。
- 中文字型用 `WenQuanYi Zen Hei`，matplotlib 要加 `DejaVu Sans` 當 fallback，否則上下標與負號會變方框。

## 使用者的實際研究題目

寫 `lessons/dna-to-culture/` 相關內容時，這些背景要納入考量：

- **菌株**：*Rhodotorula toruloides*（紅酵母，舊名 *Rhodosporidium toruloides*）**IFO 8766**。
  - 它是 **IFO 0559（交配型 A）× IFO 0880（交配型 a）的二倍體接合株**，也是這個種的模式菌株；其他編號：NBRC 8766、CBS 6016、DSM 4444。
  - 使用者用的參考基因體是 JGI MycoCosm 的 `Rhoto_IFO0880_4`。**兩個親本的基因體 JGI 都有**（IFO 0880 與 IFO 0559），可以分開兩套單倍型。
- **基改**：把**蘋果的 α-farnesene 合成酶（AFS）以隨機嵌入**放進這株菌。所以插入位置與拷貝數都還不確定。
- **這代表什麼**（已寫進第 15、16 章）：
  - 是**真核生物**，細菌的工具鏈（Prokka／Bakta、CheckM2、GTDB-Tk、CarveMe、gapseq）都不適用。
  - 是**產油酵母，不是釀酒酵母**：Crabtree 陰性、氮限制（高 C/N）觸發油脂累積、菌體紅色會干擾 OD600、可直接用木糖與乙酸。不要套用 *S. cerevisiae* 的經驗。
  - 代謝模型要用 **rhto-GEM**（Tiukova et al. 2019，建在 IFO 0880 上），不是 Yeast8。
  - α-farnesene 是倍半萜，從 FPP 做；競爭者是油脂（搶乙醯輔酶 A）、ERG9／麥角固醇與類胡蘿蔔素（搶 FPP）。
  - 產物揮發，要用十二烷等有機相覆蓋收集，否則量到的產量嚴重低估。

## Git

- 開發分支：`claude/ammonia-nitrogen-degradation-a0nidi`（不要推到其他分支）。
- commit 訊息用繁體中文，第一行簡述、空行後列重點。
- 除非使用者明確要求，**不要開 pull request**。
