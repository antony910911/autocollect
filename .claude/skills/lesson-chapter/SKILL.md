---
name: lesson-chapter
description: 要在 lessons/ 下面新增或修改一章圖解教材、加一張圖、或把分析結果寫成教材內容時使用。涵蓋從算數字、畫圖、檢查版面到推上去確認 CI 的完整流程。
---

# 寫一章圖解教材

這個 repo 的教材有一套固定流程。照做可以避免「數字沒有來源」「圖上文字疊在一起」「CI 失敗」這三類最常見的返工。

## 先確認

1. 讀 `CLAUDE.md`（應該已自動載入）——語言、分支、規矩都在裡面。
2. 確認要寫進哪一個分區：`lessons/<課程>/`。新分區才需要 `course.yaml`。
3. 章節檔名用 `NN-slug.md`，`NN` 兩位數，排序就是章節順序。

## 流程

### 1. 數字先算出來，不要先寫文章

**這是最重要的一條。** 所有出現在圖和表裡的數值，都要由 `lessons/<課程>/code/` 的程式產生，結果存成 JSON，章節和圖都引用那份 JSON。

```
code/xxx.py  →  code/xxx.json  →  章節引用 ＋ 圖讀取
```

程式要能重跑。如果輸入資料不在 repo 裡（使用者的未發表資料），在程式的 docstring 裡寫清楚怎麼指定路徑重跑，並在章節裡說明。

**不要憑印象寫數字。** 寧可少寫一個數字，也不要寫一個查不到來源的。

### 2. 畫圖

兩種：

| 類型 | 工具 | 放哪 | 檔名 |
|---|---|---|---|
| 示意圖（概念、流程、架構） | `lessons/_tools/svgkit.py` | `figures/src/diagrams.py` | `figNN-M-名字.png` |
| 數據圖（有座標軸的） | matplotlib | `figures/src/charts.py` 或 `code/make_figures.py` | `fdNN-M-名字.png` |

畫完一定要**用 Read 看一次 PNG**。常見問題：

- **文字超出方塊**：`svgkit` 不會自動換行，要自己按實際寬度斷行（用 `_w()` 量），**不要按字數切**——按字數會把 `R. toruloides` 切成 `R. t` ＋ `oruloides`。
- **標籤互相重疊**：兩個靠近的標籤各自錨定在同一區，先算寬度再決定要不要移位或改成引線。
- **Markdown 不會生效**：`svgkit` 的字串裡寫 `**粗體**` 會原樣印出來，要用 `weight=700` 和 `color=`。
- **對數軸負號變亂碼**：用 `FuncFormatter(lambda v, _: f"{v:g}")`，並把 minor formatter 設成 `NullFormatter()`。
- **圖號要和章節順序一致**：讀者先看到的圖編號要比較小。

### 3. 寫章節

- 繁體中文（臺灣用語），`# 第 N 章　標題`（全形空格）。
- 圖用 `![圖 N-M　說明](figures/檔名.png)` 插在對應段落。
- **誠實標示**：模擬資料要寫是模擬，推論要寫是推論，沒核對過的來源要寫沒核對過。
  負面結果（模型失準、參數不可辨識、分析沒有結論）照實寫——那通常是最有價值的教學點。
- 每章結尾放「## 本章重點」，3–7 條。
- 有引用就放「## 參考文獻」在最後（格式見 `cite-check` 技能）。

### 4. 檢查（三樣都要跑）

```bash
python -m autocollect lessons --dir lessons/<課程> --dry-run   # 看頁面會長怎樣
python lessons/_tools/check_layout.py lessons/<課程>           # 版面有沒有疊
python -m pytest -q tests                                      # 測試
```

版面檢查如果報重疊，多半是某個文字區塊太長被低估——把它拆成兩段，或縮短。

### 5. 更新索引

- `lessons/<課程>/README.md` 的章節表加一列。
- 章數變了要更新 `CLAUDE.md` 的「現有教材」表。

### 6. 推上去並確認 CI

```bash
git add -A
git commit    # 繁體中文，第一行簡述、空行後列重點
git push -u origin claude/ammonia-nitrogen-degradation-a0nidi
```

**不要開 PR**，除非使用者明講。

推完之後**一定要確認 Actions 的兩個 job 都成功**（核對 DOI、上傳到 Folio）。本機沒有 `FOLIO_SYNC_TOKEN`，上傳只會在 CI 裡發生。等待方式：用背景指令輪詢 GitHub API 直到 `conclusion` 不為空，**不要接 `| tail`**（會把輸出緩衝住）。

CI 失敗最常見的原因是 DOI 核對不過——看 `cite-check`。

## 常見錯誤

| 錯誤 | 後果 |
|---|---|
| 先寫文章再補數字 | 數字和程式對不上，之後查不出哪個對 |
| 畫完沒有用 Read 看 | 文字疊在一起，上傳後才發現 |
| 跳過版面檢查 | Folio 頁面上圖壓到字 |
| 猜 DOI | CI 失敗 |
| 推完就走 | 上傳可能失敗而沒人知道 |
