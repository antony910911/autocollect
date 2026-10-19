# 第 8 章　限制與下一步

## 8.1 引用這份分析時一定要保留的限制

原文自己列了七條，照錄並補上第 1.2 節查出來的那一條。

1. **基因體本身算不出最佳溫度、C/N、轉速或進料濃度。** 它只能告訴你這株菌具備哪些代謝能力、路徑完不完整、哪些競爭路徑會分走乙醯輔酶 A 或 NADPH。真正的高產條件還是要培養試驗、RT-qPCR、RNA-seq 或蛋白質體驗證。
2. **0.5973 g/g 是「目前這個模型、在這組培養基、不要求生長時的化學計量理論上限」**，不是實際發酵可達的產率。
3. **而且它比課本路徑的上限（0.4779 g/g）高 1.25 倍**——模型用了一條不丟 CO₂ 的路。那條路在真實的菌裡跑不跑得動，沒有驗證過（第 1.2 節）。
4. **`Metabolic_C_N_ratio` 是代謝攝取比，不是培養基配方的重量 C/N。**
5. **BMB171 是去除質體、沒有晶體蛋白的衍生株**，不能直接代表商業用的 Bt 菌株。
6. **CarveMe 的產物是草稿**，官方定位就是需要人工校正；gap filling 可能加入沒有基因證據的反應。
7. **`enoyl-CoA hydratase` 目前只能標為 phaJ 候選**，不能僅憑 product 名稱認定。
8. **60% μmax 的轉折目前仍是模型推論**，要靠 pFBA／FVA 找出實際是哪幾條反應在變。

## 8.2 可以寫進簡報的一句話

> COBRApy 模型預測 BMB171 在低生長狀態下具有較高的 PHB 碳流；10–25% μmax 可維持約 86–94% 理論 PHB 產率，而生長高於約 60% μmax 後 PHB 產率快速下降並伴隨氧需求顯著增加，顯示可能存在代謝碳流轉換區間。

（原文寫 55–60%，依第 1.4 節的逐段計算改成 60%。）

**如果要放數字，建議同時放兩個參考上限**：模型的 0.597 g/g 和課本路徑的 0.478 g/g。只放前面那個，讀者會以為你的實驗達成率很低。

## 8.3 下一步，按優先順序

### 第一優先：跑 pFBA，加上 0.55／0.60／0.65 三個點

程式在第 6.7 節，是現成的。要改兩個地方：

- `for fraction in [0.10, 0.25, 0.50]` 加上 `0.55, 0.60, 0.65`——不加就看不到轉折那一格
- `target_ids` 加上磷酸酮醇酶相關的反應

這一跑會同時回答兩個問題：**轉折是什麼造成的**，以及**那個多出來的碳從哪來**。

### 第二優先：跑 FVA

確認 pFBA 給的路徑是不是唯一解。如果某條關鍵反應的範圍很寬，那條「結論」就不能講得太死。

### 第三優先：補找 phaA 與 sigH

第 4.3 節的篩選是靠 gene name 和 product 名稱，兩個都沒命中就會漏。要補找得用同源性比對（BLASTP 或 DIAMOND），拿已知菌株的 PhaA／SigH 序列去打 BMB171 的 `protein.faa`。

phaA 特別重要，因為目前模型直接沿用了 CarveMe 的 `ACACT1r`，**等於接受了那條反應的 GPR**，而那個 GPR 不一定對應到 BMB171 真正的 phaA。要是 GPR 錯了，剔除驗證也會跟著錯。

### 第四優先：phaJ 的身分確認

目前只憑 product 名稱。要確認得做四件事：BLASTP、看保守位點、看結構域、看基因鄰域。

### 第五優先：設計培養驗證

這是唯一能把「模型預測」變成「已知事實」的方法。要掃的：

- **不同氮供應**（對應代謝 C/N 的 50–126 區間，但要先換算成配方）
- **不同取樣時間**——因為 phaZ 離合成簇很遠、不受同一組調控，後期降解是真實存在的風險（第 2.2 節）
- **PHB 定量方法**要先定好。GC 或比色法都可以，但要有標準品

**最小可行的一組實驗**：固定一個碳源濃度，掃三個 C/N，每個做四個時間點的 PHB 與菌體乾重。這組做完就能知道兩件事——氮限制的方向對不對，以及收穫時間窗在哪。

### 第六優先：比較多株 Bt

如果要擴大，可以做比較基因體學，看不同 Bt 菌株的 PHA 路徑差在哪。但在上面幾項做完之前，這一項的 CP 值不高。

## 8.4 產出檔案清單

```text
03_candidate_genes/BMB171_PHA_hits.txt
03_candidate_genes/BMB171_PHA_candidate_genes.tsv / .xlsx
09_GEM/draft/BMB171_carveme_draft.xml
09_GEM/reports/BMB171_MEMOTE.html
09_GEM/curated/BMB171_PHA_curated.xml        ← v1，有立體異構物問題，僅供對照
09_GEM/curated/BMB171_PHA_curated_v2.xml     ← 正式分析模型
09_GEM/reports/BMB171_NH4_Growth_PHB_matrix.csv / .xlsx
09_GEM/reports/BMB171_Growth_PHB_tradeoff.csv / .xlsx
09_GEM/reports/BMB171_pFBA_key_fluxes.xlsx   ← 待產出
```

**v1 留著不要刪。** 它是第 5.5 節那個坑的證物——兩個版本都給 12.5，但只有 v2 是對的。下次有人問「為什麼要多建一個代謝物」，把兩個模型並排跑一次就說完了。

## 8.5 用到的工具

沒有附 DOI，因為這個環境連不到 Crossref 核對，寧可只給網址也不要猜。

- **CarveMe**（從蛋白質 FASTA 自動建草稿 GEM）<https://github.com/cdanielmachado/carveme>
- **MEMOTE**（GEM 品質檢測）<https://github.com/opencobra/memote>
- **COBRApy**（代謝模型計算）<https://github.com/opencobra/cobrapy>
- **BiGG**（代謝物與反應的命名系統）<http://bigg.ucsd.edu>
- **NCBI Datasets CLI**（下載基因體）<https://www.ncbi.nlm.nih.gov/datasets/>
- **Biopython**（讀 GenBank 註解）<https://biopython.org>

原始素材：使用者上傳的 `BMB171_PHB_分析筆記.md`，整理自一份 ChatGPT 對話。
原檔留在這門教材的 `SOURCE.md`，`code/checks.py` 是對它做的查核。

## 8.6 名詞速查

| 名詞 | 白話解釋 |
|---|---|
| **GEM** | Genome-scale metabolic model，用整個基因體推出來的全代謝網路模型 |
| **FBA** | Flux Balance Analysis。在質量守恆與上下限的約束下，求「最大化某個目標」的通量解 |
| **pFBA** | 在維持最佳目標值的前提下，再最小化總通量 → 得到最精簡、最可能的代謝路徑 |
| **FVA** | Flux Variability Analysis。算每條反應在接近最佳解時可以落在哪個通量範圍 |
| **flux（通量）** | 單位 mmol/gDW/h，每克乾重菌體每小時幾毫莫耳 |
| **μmax** | 模型在該培養基下能達到的最大比生長速率 |
| **exchange reaction** | `EX_xxx_e`，模型與外界交換物質的介面。**設它的上限就等於設培養基** |
| **demand reaction** | `DM_xxx`，把某個代謝物「抽走」的虛擬反應，用來模擬產物累積 |
| **GPR** | Gene–Protein–Reaction rule，哪些基因負責哪條反應。剔除驗證就是靠它 |
| **gap filling** | 自動補反應讓模型能生長，但補進來的反應**不一定有基因證據** |
| **CarveMe** | 從蛋白質 FASTA 自動裁切出草稿 GEM 的工具 |
| **MEMOTE** | GEM 的品質檢測工具，產出 HTML 報告 |
| **BiGG** | 通用的代謝物／反應命名系統，CarveMe 用的就是它 |
