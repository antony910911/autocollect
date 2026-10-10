# 每週分析任務（Claude Code 排程執行）

這份文件是 Claude Code 每週排程任務的工作說明。GitHub Actions 已在週一早上收集好資料；這個任務負責寫分析、驗證引用、提交報告。

## 步驟

1. 更新程式碼並安裝套件：
   ```bash
   git checkout main && git pull origin main
   pip install -r requirements.txt
   ```
2. 確認本週週次（台北時間）：`TZ=Asia/Taipei date +%G-W%V`，以下以 `<週次>` 表示。
   - 若 `data/raw/<週次>.json` 不存在，代表 GitHub Actions 尚未執行或失敗：不要自己收集資料，直接回報「本週資料尚未收集」並結束。
   - 若 `data/analysis/<週次>.md` 已存在，代表本週已完成，回報後結束。
3. 完整閱讀分析包 `data/packs/<週次>.md`。分隔線 `---` 之前是分析指示，之後是讀者背景、統計、上一期週報與本週資料。
4. 嚴格依照分析指示撰寫分析，存成 `data/analysis/<週次>.md`。
   - 只能根據分析包中的資料撰寫事實，每個事實標註 `[S#]`。
   - 不要上網搜尋補充資料，也不要引用分析包以外的來源。
   - 不要寫參考來源清單，程式會自動產生。
5. 驗證並組成報告：
   ```bash
   python -m autocollect build --week <週次> --analysis data/analysis/<週次>.md
   ```
   - 若結束代碼不是 0，或輸出列出「無效編號」或「未附來源」，回到分析檔修正（補上正確來源，或刪除沒有來源支持的敘述），再重跑，直到沒有無效編號，且未附來源條列不超過 3 條。
6. 提交並推送：
   ```bash
   git add data/analysis reports
   git commit -m "週報分析 <週次>"
   git push origin main
   ```
   推送因網路失敗時，依 2、4、8、16 秒間隔重試最多 4 次。
7. 用 3–5 行回報：本週資料筆數、最重要的 3 個發現、提出的新題目名稱、品質檢查結果。
