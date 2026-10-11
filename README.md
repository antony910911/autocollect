# autocollect：生質能國內外新知週報

每週自動收集生質能相關的國內外新聞、產業媒體與學術論文，再交給 Claude 寫成一份**每個事實都附來源**的分析報告，內容包括：

1. 本週重點摘要
2. 國際技術與產業動態（依技術路徑分類：熱化學、生化、SAF、生質甲醇／氫、BECCS／生物炭、原料、政策市場）
3. 台灣國內動態
4. 國際趨勢與共識（分成「正在形成的共識」與「仍有爭議」，附信心程度）
5. 技術成熟度與商業化訊號表
6. **可開發的新題目建議**（以能在台灣落地、有產業價值為優先；可以推論，但會分開標示「來源支持的訊號」和「推論」）
7. 下週追蹤清單

報告存放在 [`reports/`](reports/)，每週一份，例如 `reports/2026-W41.md`。

## 怎麼確保「有憑有據」

- 所有資料先由程式從固定來源收集，編號為 `[S1]`、`[S2]`…，Claude 只能引用這些編號。
- 產生報告後，程式會**逐一檢查引用**：不存在的編號會在內文標成 `⚠️來源編號不存在`；事實章節中沒附來源的條列也會列在報告最後的「品質檢查」。
- 報告末尾附「參考來源」（有被引用的，可直接點連結）與「附錄」（本週收集的全部資料），可以自己核對。
- 「本週資料概況」中的國家、機構、關鍵字統計都是程式算的，不是模型生成。

## 資料來源

在 [`config/sources.yaml`](config/sources.yaml) 修改，不必改程式：

| 類型 | 來源 | 說明 |
|---|---|---|
| 新聞 | Google News RSS | 中文（台灣）、英文、日文關鍵字搜尋 |
| 產業媒體 | Bioenergy International、Biofuels Digest、IEA Bioenergy、Biomass Magazine、Bioplastics News 等 | 以 Google News 依網站搜尋；European Biogas Association、Bioenergy Insight 用 RSS |
| 學術論文 | [OpenAlex](https://openalex.org)（失敗時改用 Crossref） | 含摘要、作者機構與國家，用來看「誰在研究什麼」；需設定 Secret `OPENALEX_API_KEY` |

每週送進分析的資料有上限，並依類型分配名額（預設產業媒體 40、新聞 200、論文 120，可在設定檔調整），論文會平均取自每組關鍵字的前幾名。同一則消息被多個關鍵字抓到時會合併；在先前週報出現過的資料會自動排除（紀錄在 `data/history.json`），所以每週只看到新東西。每週的原始資料存在 `data/raw/`。

**請先修改 `config/sources.yaml` 最上方的 `researcher_profile`**，寫下你的單位、專長、設備與目標產業，新題目建議才會貼近你能做的方向。

## 運作方式（不需要 API 金鑰）

```
週一 06:47  GitHub Actions（免費）
            收集資料 → data/raw/<週次>.json
            產生分析包 → data/packs/<週次>.md
            先產生「資料整理版」報告 → reports/<週次>.md
                 │
週一 08:xx  Claude Code 每週排程任務（使用 Claude 訂閱額度）
            依 ROUTINE.md：閱讀分析包 → 寫分析 data/analysis/<週次>.md
            → 程式驗證引用 → 完整報告覆蓋 reports/<週次>.md → 提交
                 │
週一 分析提交後  GitHub Actions 自動把報告寫進 Folio 筆記本「生質能週報 › 每週週報」，一週一頁、最新的在最上面
```

- GitHub Actions 排程在 [`.github/workflows/weekly-report.yml`](.github/workflows/weekly-report.yml)；想立刻收集一次，到 **Actions → 生質能週報資料收集 → Run workflow**。
- 排程任務的工作說明在 [`ROUTINE.md`](ROUTINE.md)。
- （選用）在 repo 的 **Settings → Secrets and variables → Actions → Variables** 新增 `OPENALEX_MAILTO`，填你的 email，OpenAlex 會給較寬鬆的速率限制。

## 同步到 Folio

設定一次：repo 的 **Settings → Secrets and variables → Actions → New repository secret**，名稱 `FOLIO_SYNC_TOKEN`，值是你在 Cloudflare 設定的 Folio 同步密碼。

- 分析一提交就會由 [`.github/workflows/folio.yml`](.github/workflows/folio.yml) 上傳；週一 14:07 會再補傳一次。也可以到 **Actions → 週報同步到 Folio → Run workflow** 手動上傳指定週次。
- Folio 頁面包含分析、統計、參考來源與品質檢查（網址以文字顯示，因為 Folio 文字框不保留連結）；全部資料的附錄只留在 GitHub。
- 筆記本、分區、頁面只在第一次建立：之後你在 Folio 裡改名、換顏色、移動頁面都不會被覆蓋。同一週重新上傳只會更新報告文字框，你在頁面上加的手寫和文字框會保留。
- 如果你把「生質能週報」筆記本整本刪掉，之後的頁面不會再出現；要恢復請告訴我改用新的筆記本 id。
- Folio 網址不是 `https://folio.antony910912.workers.dev` 時，新增 Variable `FOLIO_URL`。

## 教材（lessons/）

- [`lessons/ammonia/`](lessons/ammonia/)：氨氮降解入門，9 章加導讀、20 張圖與各章參考文獻。
- [`lessons/aiot/`](lessons/aiot/)：沼氣與廢水處理的 AIoT 入門，8 章加導讀、13 張圖，含國內外案例與創新思路。
- [`lessons/aiot-advanced/`](lessons/aiot-advanced/)：沼氣廠 AIoT 進階建模實作，10 章加導讀、15 張圖；附可執行的模擬廠與五個建模練習程式（`code/`）。
- [`lessons/dna-to-culture/`](lessons/dna-to-culture/)：從微生物 DNA 到最適培養條件，14 章加導讀、34 張圖；附 COBRApy 代謝模型計算（`code/`）與可離線開啟的互動培養模擬器（`simulator/index.html`）。
- 三者都放在 Folio 筆記本「Claude圖解教材」，各自一個分區。
- 每門教材的資料夾有一個 `course.yaml`，設定放在 Folio 的哪本筆記本、哪個分區；設定 `find_by_name: true` 時，會先找 Folio 裡同名的筆記本（例如你自己建的「claude圖解教材」），找到就放進去。
- 推送到任何分支、只要改到 `lessons/` 就會由 [`.github/workflows/lessons.yml`](.github/workflows/lessons.yml) 執行兩件事：到 Crossref 核對每一筆 DOI（標題與年份要對得上），以及依 `course.yaml` 寫進 Folio，一章一頁、文字與圖交錯排列。
- 圖片以內容雜湊為 id，沒改過的圖不會重傳。重新發布會重排頁面上由程式產生的文字框與圖片；你自己加的手寫與文字框不受影響。
- 共用工具在 `lessons/_tools/`（`svgkit.py` 畫示意圖、`check_refs.py` 核對 DOI）。圖由各教材 `figures/src/` 的程式產生（`charts.py` 用 matplotlib、`diagrams.py` 用 SVG 再以 Chromium 轉 PNG）。
- 本機預覽要上傳的頁面：`python -m autocollect lessons --dry-run`；查看 Folio 上有哪些筆記本：`FOLIO_SYNC_TOKEN=... python -m autocollect lessons --list`；上傳：`FOLIO_SYNC_TOKEN=... python -m autocollect lessons`。

## 本機執行

```bash
pip install -r requirements.txt
python -m autocollect collect                      # 收集資料、產生分析包
python -m autocollect build --analysis data/analysis/2026-W41.md   # 驗證引用並組成報告
FOLIO_SYNC_TOKEN=... python -m autocollect folio  # 上傳最新一期到 Folio
```

### 另一種方式：使用 Anthropic API（需付費）

設定 `ANTHROPIC_API_KEY` 後，`python -m autocollect run` 會一次完成收集、分析與組成報告（預設模型 `claude-opus-5-5`，可用環境變數 `AUTOCOLLECT_MODEL` 更換）。每週費用估計約 1 美元上下。

## 調整分析方式

分析的指示寫在 [`prompts/weekly_analysis.md`](prompts/weekly_analysis.md)，可以直接修改章節、新題目的評估欄位或語氣。

## 測試

```bash
pip install pytest
python -m pytest
```
