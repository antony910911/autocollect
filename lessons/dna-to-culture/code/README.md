# 從 DNA 到最適培養：計算程式

教材「從 DNA 到最適培養：建模與視覺化」第 4–9 章的圖和數字都來自這裡。用的是 COBRApy 內建的大腸桿菌核心模型，不需要網路。

```bash
pip install -r requirements.txt
python dfba.py           # 產生 pFBA 查表 tables.json（約 10 秒）
python experiments.py    # 跑全部計算實驗，結果寫到 results.json（約 2 分鐘）
python protocol.py       # 把最適條件換算成操作單，寫到 protocol.json
python make_figures.py   # 依結果畫圖
cd ../simulator && python build.py   # 產生互動模擬器 index.html
```

| 檔案 | 內容 |
|---|---|
| `gem.py` | 載入模型、FBA／pFBA、影子價格、基因剔除 |
| `dfba.py` | 動態通量平衡分析（每步解線性規劃或查表）、溫度與 pH 基點模型、遲滯期 |
| `experiments.py` | 1 FBA（供氧、碳源、相平面、基因剔除、流量圖）2 批次培養與生長曲線擬合 3 兩階段與敏感度 4 溫度 × pH 5 一次改一個因子／隨機／貝氏最適化 |
| `protocol.py` | 第 10 章：供氧換算 kLa 與容器、接種量、取樣時程、OD 切換門檻與查核對照表、蒙地卡羅容許範圍、異常處置表 |
| `make_figures.py` | 畫教材的圖 |
| `map_layout.json` | 中心代謝流量圖的版面（第 4 章圖與模擬器共用） |
| `tables.json`、`results.json`、`protocol.json` | 最近一次的計算結果（教材引用的就是這份） |

## 換成你的菌

1. 用 CarveMe 或 gapseq 從你的基因體產生模型（SBML 檔），在 `gem.py` 的 `load()` 改成 `cobra.io.read_sbml_model("你的模型.xml")`。
2. 修改 `gem.py` 裡的 `BIOMASS`、`EXCHANGE`、`MAP_RXNS` 成你的模型的反應名稱。
3. 用你的實驗數據修改 `dfba.Params` 的吸收速率、耗氧上限、溫度與 pH 基點值。
4. 修改 `protocol.py` 最上方的換算常數：`OD_TO_GDW`（你的檢量線）、`VESSELS`（你實測的 kLa）。
5. 依序執行上面五個指令。
