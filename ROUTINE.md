# 每週分析任務（Claude Code 排程執行）

這份文件是 Claude Code 每週排程任務的工作說明。GitHub Actions 已在週一早上收集好資料；這個任務負責為**每個主題**寫分析、驗證引用、提交報告。

## 主題

| 主題 | `--topic` | 資料夾 `<資料夾>` | 報告 |
|---|---|---|---|
| 生質能 | `bioenergy` | `data` | `reports/<週次>.md` |
| 法尼烯（α／β-farnesene） | `farnesene` | `data/farnesene` | `reports/farnesene/<週次>.md` |

主題清單定義在 `config/topics.yaml`；若那裡有新的主題，同樣照下面步驟處理。

## 步驟

1. 更新程式碼並安裝套件：
   ```bash
   git checkout main && git pull origin main
   pip install -r requirements.txt
   ```
   之後的指令都用安裝套件的那個 Python 執行（若 `python` 版本與 `pip` 不同，改用對應版本，例如 `python3.13`）。
2. 確認本週週次（台北時間）：`TZ=Asia/Taipei date +%G-W%V`，以下以 `<週次>` 表示。
3. **依序處理每個主題**（一個主題完成並推送後，再做下一個）：
   1. 若 `<資料夾>/raw/<週次>.json` 不存在，代表 GitHub Actions 尚未收集：不要自己收集資料，記下「本週資料尚未收集」並跳到下一個主題。
   2. 若 `<資料夾>/analysis/<週次>.md` 已存在，代表這個主題本週已完成，跳到下一個主題。
   3. 完整閱讀分析包 `<資料夾>/packs/<週次>.md`。分隔線 `---` 之前是分析指示，之後是讀者背景、統計、上一期週報與本週資料。
   4. 嚴格依照**該主題分析包裡的**分析指示撰寫分析（兩個主題的章節不同），存成 `<資料夾>/analysis/<週次>.md`。
      - 只能根據分析包中的資料撰寫事實，每個事實標註 `[S#]`。
      - 不要上網搜尋補充資料，也不要引用分析包以外的來源。
      - 不要寫參考來源清單，程式會自動產生。
   5. 驗證並組成報告：
      ```bash
      python -m autocollect build --topic <主題> --week <週次> --analysis <資料夾>/analysis/<週次>.md
      ```
      若結束代碼不是 0，或輸出列出「無效編號」或「未附來源」，回到分析檔修正（補上正確來源，或刪除沒有來源支持的敘述），再重跑，直到沒有無效編號，且未附來源條列不超過 3 條。
   6. 提交並推送：
      ```bash
      git add <資料夾>/analysis reports
      git commit -m "週報分析 <主題> <週次>"
      git pull --rebase origin main && git push origin main
      ```
      推送因網路失敗時，依 2、4、8、16 秒間隔重試最多 4 次。推送被拒絕（權限）時，回報錯誤原文，不要用其他方式繞過。
4. 用每個主題 3–5 行回報：本週資料筆數、最重要的 3 個發現、提出的新題目名稱、品質檢查結果。
