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
| 產業媒體 | Bioenergy International、Biofuels Digest、IEA Bioenergy、Biomass Magazine、European Biogas Association 等 RSS | |
| 學術論文 | [OpenAlex](https://openalex.org) | 含摘要、作者機構與國家，用來看「誰在研究什麼」 |

同一則消息被多個關鍵字抓到時會合併；在先前週報出現過的資料會自動排除（紀錄在 `data/history.json`），所以每週只看到新東西。每週的原始資料存在 `data/raw/`。

**請先修改 `config/sources.yaml` 最上方的 `researcher_profile`**，寫下你的單位、專長、設備與目標產業，新題目建議才會貼近你能做的方向。

## 設定步驟（GitHub Actions 每週自動執行）

1. 到 repo 的 **Settings → Secrets and variables → Actions**：
   - 新增 Secret `ANTHROPIC_API_KEY`（到 <https://console.anthropic.com> 申請）。
   - （選用）新增 Variable `OPENALEX_MAILTO`，填你的 email，OpenAlex 會給較寬鬆的速率限制。
   - （選用）新增 Variable `AUTOCOLLECT_MODEL` 換模型，預設 `claude-opus-5-5`。
2. 排程預設為**每週一早上 06:47（台北時間）**，可在 [`.github/workflows/weekly-report.yml`](.github/workflows/weekly-report.yml) 修改。
3. 想立刻跑一次：到 **Actions → 生質能週報 → Run workflow**。
4. 報告會自動 commit 到 `reports/`。在 GitHub 上 Watch 這個 repo 就能收到通知；執行失敗時 GitHub 也會寄信通知。

沒有設定 API 金鑰時，工具仍會產出「資料整理版」報告（統計 + 全部資料清單），只是沒有 AI 分析。

## 本機執行

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python -m autocollect run              # 收集 + 分析
python -m autocollect run --no-ai      # 只收集
python -m autocollect run --reuse-raw  # 用本週已收集的資料重跑分析（例如改了提示詞之後）
```

## 調整分析方式

分析的指示寫在 [`prompts/weekly_analysis.md`](prompts/weekly_analysis.md)，可以直接修改章節、新題目的評估欄位或語氣。

每週成本估計：約 8–10 萬輸入 tokens、2–3 萬輸出 tokens（含模型思考），以 Claude Opus 5.5 計價約 1 美元上下。

## 測試

```bash
pip install pytest
python -m pytest
```
