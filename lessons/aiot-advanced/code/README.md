# 沼氣廠建模練習程式

教材「沼氣 AIoT 進階：建模實作」第 3–8 章用到的程式。全部用模擬資料，不需要真實廠的數據就能跑。

```bash
pip install -r requirements.txt
python plant.py          # 產生模擬沼氣廠 480 天資料，印出事件期間的數值
python experiments.py    # 跑五個練習，結果寫到 results.json（約 20 秒）
python make_figures.py   # 依實際結果畫教材的圖
```

| 檔案 | 內容 |
|---|---|
| `am2.py` | AM2 兩步驟厭氧消化模型（Bernard et al., 2001），RK4 積分、pH 與氣體計算 |
| `plant.py` | 模擬廠：原料變異、兩次過量進料、pH 電極漂移、換原料；產生每小時量測與每週兩次實驗室數據 |
| `experiments.py` | 1 產氣預測、2 VFA 軟感測、3 EKF 數位孿生、4 預警與感測器漂移、5 進料建議 |
| `make_figures.py` | 畫教材的圖 |
| `results.json` | 最近一次執行的數字（教材引用的就是這份） |

## 換成你們廠的資料

1. 把每日資料整理成 CSV：日期、甲烷或沼氣量、CH₄%、pH、進料量、進料 COD（或 TS/VS）。
2. 實驗室資料另一個 CSV：採樣時間、VFA（或 FOS/TAC）。
3. 仿照 `plant.daily_table()` 的欄位名稱讀進來，`experiments.exp_forecast()` 與 `exp_soft_sensor()` 就能直接用。
4. EKF 需要先用自己廠的資料校正 AM2 參數，建議找有建模經驗的合作者。
