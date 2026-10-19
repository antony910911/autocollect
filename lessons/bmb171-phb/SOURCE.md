# Bacillus thuringiensis BMB171：PHB 代謝模型分析筆記

> 來源：一份 114 則訊息的 ChatGPT 對話（標題「Bacillus thuringiensis PHA分析」）。
> 本筆記分成三段：**① 精簡摘要**（只想知道結論看這段）、**② 完整操作手冊**（要自己重跑看這段）、**③ 附錄：常見錯誤與排解**。

---

# 第一部分　精簡摘要

## 一句話重點

從 NCBI 下載 *B. thuringiensis* BMB171 基因體，確認它帶有完整的 **phaP–phaQ–phaR–phaB–phaC** 基因簇，再用 CarveMe + COBRApy 建出可計算的代謝模型；模型預測 **把生長壓到最大生長速率的 10–25%，可保留理論 PHB 產率的 86–94%（約 0.51–0.56 g-PHB/g-glucose）**，而生長超過約 55–60% μmax 之後 PHB 產率會急遽崩落。

## 這份分析走過的完整路徑

```text
NCBI 下載 BMB171 基因體
        ↓
關鍵字 + Biopython 篩出 15 個候選 CDS
        ↓
判讀基因簇（phaP-phaQ-phaR-phaB-phaC，phaZ 另在他處）
        ↓
CarveMe 建 Gram-positive draft GEM
        ↓
MEMOTE 品質檢查
        ↓
人工校正：補 PhaB、PhaR/PhaC、PHB demand（curated v1）
        ↓
培養基定義 → O₂ 飽和點掃描 → 氮源健檢
        ↓
【踩到坑】發現 PHB 可繞過 PhaB → 立體異構物問題
        ↓
curated v2：建立專屬的 (R)-3HB-CoA
        ↓
三組 knockout 驗證（PhaB / PhaR / PhaC → PHB 全歸零）✓
        ↓
NH₄ × Growth × PHB 矩陣
        ↓
Growth–PHB trade-off 曲線
        ↓
【下一步】pFBA / FVA → 找碳流競爭點 → 反推培養與改造策略
```

## 關鍵發現

### 1. 基因層面

BMB171 的核心 PHA 基因集中在染色體約 **1,295,466–1,299,230 bp**，排列成方向相反的兩個模組：

```text
← phaP ─42 bp─ ← phaQ ──198 bp── phaR → ─150 bp─ phaB → ─84 bp─ phaC →
```

| 基因 | Locus tag | Protein ID | 角色 |
|---|---|---|---|
| phaP | — | — | phasin，顆粒表面蛋白 |
| phaQ | — | — | PHB-responsive repressor（高優先度調控候選） |
| phaR | BMB171_RS06645 | WP_000566942.1 | PHA synthase 次單元（與 PhaC 一組） |
| phaB | BMB171_RS06650 | WP_000250409.1 | acetoacetyl-CoA reductase（註解沒寫 gene name，靠 product + 位置推定） |
| phaC | BMB171_RS06655 | WP_000206336.1 | class III PHA synthase 次單元 |
| phaZ | 約 3.180 Mb | — | 胞內 PHB depolymerase，與合成簇分離 |

重點三則：
- **PhaR 與 PhaC 必須視為一組**。Bacillus 的 PHA synthase 要兩個次單元才有活性，未來做過表現不能只動 phaC。
- **phaZ 離得很遠**，意味培養後期菌體可能把 PHB 再吃回去 → 「最佳收穫時間」會是實驗的關鍵變因。
- **spo0A 有找到、sigH 沒抓到**。文獻上破壞這兩者會嚴重降低 PHB，但它們比較適合當「生長階段標誌」，不是優先敲除目標。

### 2. 模型層面（最重要的數字）

基準條件：glucose uptake = 10、O₂ = 60、NH₄ 充足。

| 項目 | 數值 |
|---|---|
| 最大生長速率 μmax | **0.443536 h⁻¹** |
| O₂ 飽和點 | 約 **50 mmol/gDW/h**（給到 60 以上生長不再上升） |
| 最大 PHB flux（不要求生長） | **12.5 mmol PHB-repeat/gDW/h** |
| 理論莫耳產率 | 1.25 mol PHB-repeat / mol glucose |
| 理論質量產率 | **0.5973 g-PHB/g-glucose** |
| 氮需求 | q(NH₄) ≈ **10.7682 × μ**（μmax 時約 4.776 mmol/gDW/h） |

### 3. Growth–PHB trade-off（這張表是整份分析的核心產出）

| Growth / μmax | Growth flux | PHB flux | PHB yield (g/g glucose) | 佔理論上限 | O₂ uptake |
|---:|---:|---:|---:|---:|---:|
| 0% | 0 | 12.50 | **0.597** | 100% | 3.75 |
| 10% | 0.0444 | 11.78 | **0.563** | 94% | 5.24 |
| 25% | 0.1109 | 10.71 | **0.512** | 86% | 7.47 |
| 50% | 0.2218 | 8.92 | **0.426** | 71% | 11.18 |
| 55% | — | 8.56 | 0.409 | 68% | 11.93 |
| 60% | — | 8.00 | 0.382 | 64% | 13.78 |
| 75% | 0.3327 | 5.00 | **0.239** | 40% | 27.22 |
| 90% | 0.3992 | 2.00 | 0.096 | 16% | 40.67 |
| 100% | 0.4435 | ≈0 | ≈0 | 0% | 49.63 |

**轉折點在 55–60% μmax。** 在此之前每增加 5% μmax，PHB 約掉 0.36；超過之後每 5% 掉約 1.0，同時 O₂ 需求急升。推測是碳與還原力在此開始大量轉向 biomass、TCA 與呼吸作用。

### 4. 關於「氮限制」的正確理解

模型顯示 **NH₄ 幾乎完全只用在 biomass formation，不直接參與 PHB 合成**。所以：

> 氮限制之所以有效，是「限制氮 → 限制 μ → 把 acetyl-CoA / NADPH 讓給 PHB」，**不是**低氮直接去啟動 phaABC。

也因此，**不能**從這份結果直接講「最佳培養 C/N = 50」。表中的 `Metabolic_C_N_ratio` 是細胞代謝攝取的 mol-C/mol-N，不是培養基配方的重量 C/N。要換算成配方還得考慮底物攝取速率、菌體濃度、發酵時間、氮鹽的 N 含量、yeast extract 等有機氮、殘氮、fed-batch 進料方式。

正確的講法是：

> 模型預測維持約 10–25% 最大生長速率時，可保留 86–94% 的理論 PHB 產率，對應代謝 C/N 約 50–126 mol-C/mol-N，可作為後續氮限制培養條件設計的**篩選區間**。

### 5. 可以寫進簡報的結論句

> COBRApy 模型預測 BMB171 在低生長狀態下具有較高 PHB 碳流；10–25% μmax 可維持約 86–94% 理論 PHB 產率，而生長高於約 55–60% μmax 後 PHB 產率快速下降並伴隨氧需求顯著增加，顯示可能存在代謝碳流轉換區間。

## 兩個候選製程策略

```text
策略 A：最大 PHB 累積
  生長限制在 10–25% μmax
  → PHB yield ≈ 0.51–0.56 g/g

策略 B：兼顧菌體與 PHB
  約 50% μmax
  → PHB yield ≈ 0.43 g/g

Fed-batch 實作構想：
  Stage 1：高 μ 快速長菌
  Stage 2：降低有效氮供應 → μ 降到 10–25% μmax → 碳流轉向 PHB
（比一開始就極端斷氮合理得多）
```

## 待辦清單

- [ ] 跑 **pFBA**，比較 10% / 25% / 50% / 75% μmax 的碳流分配
- [ ] 重點看 `ACACT1r`、`PHAB_NADPH`、`CS`（citrate synthase）、`PTAr`/`ACKr`（acetate overflow）、PPP 的 NADPH 供應
- [ ] 回答核心問題：**55–60% μmax 附近到底是哪一條碳流突然增加？**
- [ ] 跑 **FVA**，避免把單一 FBA 解誤認成唯一代謝路徑
- [ ] 補找 **phaA** 與 **sigH**（目前 15 個候選中沒抓到 sigH）
- [ ] 把 `enoyl-CoA hydratase` 的 phaJ 候選做 BLASTP + 保守位點 + 結構域 + 基因鄰域確認
- [ ] 把代謝 C/N 換算成可操作的培養基配方
- [ ] 設計小規模培養驗證：不同 N 供應 × 取樣時間 × PHB 定量（注意 phaZ 的後期降解）
- [ ] 若要擴大：比較多株 Bt 的 pathway 差異（comparative genomics）

## 名詞速查

| 名詞 | 白話解釋 |
|---|---|
| **GEM** | Genome-scale metabolic model，用整個基因體推出來的全代謝網路模型 |
| **FBA** | Flux Balance Analysis，在質量守恆與上下限約束下求「最大化某個目標」的通量解 |
| **pFBA** | 在維持最佳目標值的前提下，再最小化總通量 → 得到最精簡、最可能的代謝路徑 |
| **FVA** | Flux Variability Analysis，算每條反應在接近最佳解時可以落在哪個通量範圍 |
| **flux** | 通量，單位 mmol/gDW/h（每克乾重菌體每小時幾毫莫耳） |
| **μmax** | 模型在該培養基下能達到的最大比生長速率 |
| **exchange reaction** | `EX_xxx_e`，模型與外界交換物質的介面，設上限等於設培養基 |
| **demand reaction** | `DM_xxx`，把某代謝物「抽走」的虛擬反應，用來模擬產物累積 |
| **GPR** | Gene–Protein–Reaction rule，哪些基因負責哪條反應；knockout 靠它 |
| **gap filling** | 自動補反應讓模型能生長，但補進來的反應**不一定有基因證據** |
| **CarveMe** | 從 protein FASTA 自動裁切出 draft GEM 的工具 |
| **MEMOTE** | GEM 品質檢測工具，產出 HTML 報告 |
| **BiGG** | 通用的代謝物／反應命名系統，CarveMe 用的就是它 |

---

# 第二部分　完整操作手冊

> 全部在 **Windows + WSL2 Ubuntu** 下操作。專案根目錄為 `~/Bt_PHA_analysis`。

## Step 0　建立環境

兩個 conda 環境分開，避免套件衝突。

**環境一：基因體分析（btpha）**

```bash
conda create -n btpha \
  -c conda-forge -c bioconda \
  ncbi-datasets-cli python=3.12 biopython pandas blast diamond seqkit -y

conda activate btpha
```

確認：

```bash
datasets version
dataformat version
python --version
blastp -version
diamond version
```

**環境二：代謝模型（btcobra）**

```bash
conda create -n btcobra \
  -c conda-forge -c bioconda \
  python=3.10 cobra diamond pyscipopt memote pandas openpyxl -y

conda activate btcobra
conda install -c bioconda carveme diamond pyscipopt -y
```

確認 CarveMe 真的裝好（**不要**用 `sudo apt install carve`，那是別的同名軟體）：

```bash
conda list carveme
command -v carve          # 應顯示 .../envs/btcobra/bin/carve
carve --help | head -n 20
```

**建立資料夾**

```bash
mkdir -p ~/Bt_PHA_analysis/{00_metadata,01_all_genomes,02_reference_genomes,03_candidate_genes,04_homology,05_synteny,06_comparative,07_pathway,08_culture_hypotheses,scripts,logs}
mkdir -p ~/Bt_PHA_analysis/09_GEM/{draft,curated,reports,scripts}
cd ~/Bt_PHA_analysis
```

原則：**原始下載資料保持不動，不要直接在下載資料夾裡改檔案。**

## Step 1　下載參考菌株基因體

不要一開始就抓全部 Bt genome。先用 2–3 株把流程跑通。

**BMB171**（主力參考株，有完整基因體、已被用於 PHB 與 phaC/spo0A/sigH 研究；但它是去除質體、無晶體蛋白的衍生株，不能代表所有商業 Bt）：

```bash
conda activate btpha
cd ~/Bt_PHA_analysis

datasets download genome accession GCA_000092165.1 \
  --include genome,protein,cds,gff3,gbff,seq-report \
  --filename 02_reference_genomes/BMB171.zip

unzip -q 02_reference_genomes/BMB171.zip -d 02_reference_genomes/BMB171
```

**ATCC 35646**（phaZ / PHB 降解參考）：

```bash
datasets download genome accession GCF_000167695.1 \
  --include genome,protein,cds,gff3,gbff,seq-report \
  --filename 02_reference_genomes/ATCC35646.zip

unzip -q 02_reference_genomes/ATCC35646.zip -d 02_reference_genomes/ATCC35646
```

檢查檔案：

```bash
find 02_reference_genomes -type f | sort
```

| 檔案 | 用途 |
|---|---|
| `*_genomic.fna` | 全基因體 DNA |
| `protein.faa` | 全部預測蛋白質序列（CarveMe 要用這個） |
| `genomic.gff` | 基因座標與註解 |
| `genomic.gbff` | 完整 GenBank 註解（基因名、product、protein_id、translation） |
| `cds_from_genomic.fna` | CDS 核酸序列 |
| `sequence_report.jsonl` | chromosome / plasmid 資訊 |

（延伸：要全 Bt 名單時先只抓 metadata）

```bash
datasets summary genome taxon "Bacillus thuringiensis" \
  --assembly-level complete,chromosome --assembly-source RefSeq \
  --annotated --exclude-atypical --exclude-multi-isolate \
  --as-json-lines > 00_metadata/Bt_genomes.jsonl
```

## Step 2　找出 PHA 相關基因

**先快速 grep 看一眼**（`phaP`、`phaC` 這些是基因名稱，**不是指令**，必須放在 grep 的引號裡）：

```bash
GBFF=$(find 02_reference_genomes/BMB171 -type f -name "*.gbff" | head -n 1)
echo "$GBFF"

grep -niE -C 8 \
'phaP|phaQ|phaR|phaB|phaC|phaZ|spo0A|sigH|polyhydroxyalkanoate|polyhydroxybutyrate|hydroxybutyrate|phasin|acetoacetyl[- ]CoA reductase|acetyl[- ]CoA acetyltransferase|PHA synthase|PHB depolymerase' \
"$GBFF" > 03_candidate_genes/BMB171_PHA_hits.txt
```

**再用 Biopython 做結構化擷取**（這才是正式產出）：

```bash
cat > scripts/extract_BMB171_PHA_candidates.py <<'PY'
#!/usr/bin/env python3
from pathlib import Path
from Bio import SeqIO
import csv, re

gbff_files = list(Path("02_reference_genomes/BMB171").rglob("*.gbff"))
if not gbff_files:
    raise FileNotFoundError("找不到 BMB171 的 GBFF 檔案")
gbff = gbff_files[0]

target_genes = {"phaa","phab","phac","phap","phaq","phar","phaj","phaz",
                "spo0a","sigh","abrb","ccpa","cody"}

product_pattern = re.compile(
    r"poly.*hydroxyalkano|poly.*hydroxybutyrate|phasin|"
    r"acetoacetyl[- ]CoA reductase|acetyl[- ]CoA acetyltransferase|"
    r"enoyl[- ]CoA hydratase|PHA synthase|PHB depolymerase|"
    r"polyhydroxyalkanoate depolymerase|sigma factor H|sporulation.*Spo0A|"
    r"transition state regulatory protein AbrB|catabolite control protein A|"
    r"transcriptional pleiotropic repressor CodY",
    re.IGNORECASE)

rows = []
for record in SeqIO.parse(gbff, "genbank"):
    for feature in record.features:
        if feature.type != "CDS":
            continue
        q = feature.qualifiers
        gene = q.get("gene", [""])[0]
        locus_tag = q.get("locus_tag", [""])[0]
        old_locus_tag = q.get("old_locus_tag", [""])[0]
        product = q.get("product", [""])[0]
        protein_id = q.get("protein_id", [""])[0]
        note = " ".join(q.get("note", []))
        search_text = " ".join([gene, locus_tag, old_locus_tag, product, note])

        if gene.lower() not in target_genes and not product_pattern.search(search_text):
            continue

        rows.append({
            "record_id": record.id,
            "start_bp": int(feature.location.start) + 1,
            "end_bp": int(feature.location.end),
            "strand": feature.location.strand,
            "gene": gene, "locus_tag": locus_tag, "old_locus_tag": old_locus_tag,
            "product": product, "protein_id": protein_id,
        })

output = Path("03_candidate_genes/BMB171_PHA_candidate_genes.tsv")
with output.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["record_id","start_bp","end_bp","strand",
        "gene","locus_tag","old_locus_tag","product","protein_id"], delimiter="\t")
    w.writeheader(); w.writerows(rows)

print(f"使用的 GBFF：{gbff}")
print(f"候選 CDS 數量：{len(rows)}")
print(f"輸出檔案：{output}")
PY

python scripts/extract_BMB171_PHA_candidates.py
```

**結果：15 個候選 CDS。**

快速看內容：

```bash
python - <<'PY'
import pandas as pd
df = pd.read_csv("03_candidate_genes/BMB171_PHA_candidate_genes.tsv", sep="\t")
print(df[["gene","locus_tag","start_bp","end_bp","strand","product","protein_id"]].to_string(index=False))
PY
```

要在 Windows 看：

```bash
explorer.exe .            # 注意最後是「空格 + 句點」，且不能在 less 裡面執行
```

Excel 看不到 `.tsv` 的話，複製一份成 `.txt`，再用「資料 → 從文字/CSV」，編碼選 **65001 UTF-8**、分隔符號選 **定位點/Tab**。

## Step 3　判讀基因簇

把 15 個候選依 `start_bp` 排序，分成三類觀察：

1. **合成與顆粒**：phaA、phaB、phaC、phaR、phaP、phaQ、phaJ
2. **降解**：phaZ
3. **調控**：spo0A、sigH、abrB、ccpA、codY

觀察重點：座標是否相鄰、strand 是否相同、是否形成 `phaR–phaB–phaC`、是否形成 `phaP–phaQ`、phaZ 在哪、哪些列 `gene` 空白但 `product` 是 PHA 相關。

結果見第一部分的基因簇圖。

**取得正式的 protein ID**（模型要用，不能用占位字串）：

```bash
python - <<'PY'
from pathlib import Path
from Bio import SeqIO

root = Path.home() / "Bt_PHA_analysis"
gbff = list((root / "02_reference_genomes" / "BMB171").rglob("*.gbff"))[0]
targets = {"BMB171_RS06645", "BMB171_RS06650", "BMB171_RS06655"}

print(f"使用的 GBFF：{gbff}\n")
for record in SeqIO.parse(gbff, "genbank"):
    for feature in record.features:
        if feature.type != "CDS":
            continue
        q = feature.qualifiers
        locus_tag = q.get("locus_tag", [""])[0]
        if locus_tag not in targets:
            continue
        print("=" * 70)
        print(f"Locus tag  : {locus_tag}")
        print(f"Gene       : {q.get('gene',[''])[0] or '未標示'}")
        print(f"Product    : {q.get('product',[''])[0] or '未標示'}")
        print(f"Protein ID : {q.get('protein_id',[''])[0] or '未標示'}")
        print(f"Coordinates: {int(feature.location.start)+1}-{int(feature.location.end)}")
        print(f"Strand     : {feature.location.strand}")
PY
```

得到：

```text
BMB171_RS06645 → PhaR → WP_000566942.1
BMB171_RS06650 → acetoacetyl-CoA reductase（= PhaB）→ WP_000250409.1
BMB171_RS06655 → PhaC → WP_000206336.1
```

> 在 COBRApy 的 GPR 字串裡，小數點要換成底線：`WP_000250409_1`。

## Step 4　建立 draft GEM（CarveMe）

```bash
conda activate btcobra
cd ~/Bt_PHA_analysis

PROT=$(find ~/Bt_PHA_analysis/02_reference_genomes/BMB171 -type f -name "protein.faa" | head -n 1)
echo "$PROT"

carve "$PROT" \
  -u grampos \
  --fbc2 \
  --solver scip \
  -o ~/Bt_PHA_analysis/09_GEM/draft/BMB171_carveme_draft.xml
```

- `-u grampos`：使用 Gram-positive universal model
- `--fbc2`：輸出 SBML-FBC2（COBRApy 可直接讀）
- `--solver scip`：沒有 CPLEX / Gurobi 時用開源 SCIP（較慢）

**第一版先不要 gap filling。** 先觀察：能不能產生 biomass、哪些反應被 blocked、PHA pathway 有沒有被收錄、transporter 合不合理。之後只根據「實際證明可生長的培養基」再補。gap filling 會加入沒有基因證據的反應。

檢查：

```bash
ls -lh ~/Bt_PHA_analysis/09_GEM/draft/BMB171_carveme_draft.xml
```

## Step 5　MEMOTE 品質檢查

```bash
memote report snapshot \
  --filename ~/Bt_PHA_analysis/09_GEM/reports/BMB171_MEMOTE.html \
  09_GEM/draft/BMB171_carveme_draft.xml
```

會檢查 mass balance、charge balance、annotation、blocked reactions、biomass consistency。

## Step 6　在 draft 裡找 PHA 反應

先用關鍵字粗篩會得到 **269 條**（太多、太雜），所以改用 BiGG metabolite ID 精準篩，收斂到 **47 條**。

查核心代謝物是否存在：

```text
accoa_c      acetyl-CoA
aacoa_c      acetoacetyl-CoA
3hbcoa__R_c  (R)-3-hydroxybutyryl-CoA   ← 關鍵
coa_c  nadph_c  nadp_c  h_c
```

**結論：CarveMe 建立了 acetyl-CoA → acetoacetyl-CoA 的入口（`ACACT1r`），但抓錯了 PhaB，而且完全沒有 PhaR/PhaC 聚合反應與 PHB demand。必須人工補齊。**

## Step 7　人工校正 v1（curated）

原則：**不覆蓋 CarveMe 原始模型**，另存新檔。

```bash
cat > 09_GEM/scripts/curate_BMB171_PHA_model.py <<'PY'
#!/usr/bin/env python3
from cobra.io import read_sbml_model, write_sbml_model
from cobra import Metabolite, Reaction

INPUT  = "09_GEM/draft/BMB171_carveme_draft.xml"
OUTPUT = "09_GEM/curated/BMB171_PHA_curated.xml"

PHAB_GENE = "WP_000250409_1"
PHAR_GENE = "WP_000566942_1"
PHAC_GENE = "WP_000206336_1"

model = read_sbml_model(INPUT)

def get_metabolite(model, ids, name_keywords):
    for mid in ids:
        if mid in model.metabolites:
            return model.metabolites.get_by_id(mid)
    for m in model.metabolites:
        n = (m.name or "").lower()
        if any(k in n for k in name_keywords):
            return m
    raise KeyError(f"找不到：{ids}")

accoa = get_metabolite(model, ["accoa_c"], ["acetyl-coa"])
aacoa = get_metabolite(model, ["aacoa_c"], ["acetoacetyl-coa"])
coa   = get_metabolite(model, ["coa_c"],   ["coenzyme a"])
nadph = get_metabolite(model, ["nadph_c"], ["nadph"])
nadp  = get_metabolite(model, ["nadp_c"],  ["nadp"])
h     = get_metabolite(model, ["h_c"],     ["proton"])
hbcoa = get_metabolite(model, ["3hbcoa__R_c","3hbcoa_R_c","3hbcoa_c"],
                       ["3-hydroxybutyryl-coa","3-hydroxybutanoyl-coa"])

# PhaA：沿用 CarveMe 的 ACACT1r，不自行新增

# PhaB：acetoacetyl-CoA + NADPH + H+ -> (R)-3HB-CoA + NADP+
if "PHAB_NADPH" in model.reactions:
    model.remove_reactions(["PHAB_NADPH"], remove_orphans=False)
phab = Reaction("PHAB_NADPH")
phab.name = "Acetoacetyl-CoA reductase (NADPH-dependent PhaB)"
phab.lower_bound, phab.upper_bound = 0, 1000
phab.add_metabolites({aacoa: -1, nadph: -1, h: -1, hbcoa: 1, nadp: 1})
phab.gene_reaction_rule = PHAB_GENE
model.add_reactions([phab])

# PHB 重複單元 pseudo-metabolite
PHB_ID = "phb_repeat_c"
if PHB_ID in model.metabolites:
    phb = model.metabolites.get_by_id(PHB_ID)
else:
    phb = Metabolite(PHB_ID, formula="C4H6O2", charge=0,
                     name="Poly(3-hydroxybutyrate) repeat unit", compartment="c")
    model.add_metabolites([phb])

# PhaR/PhaC：(R)-3HB-CoA -> PHB repeat + CoA
RID = "PHAC_PHB_POLYMERIZATION"
if RID in model.reactions:
    model.remove_reactions([RID], remove_orphans=False)
phac = Reaction(RID)
phac.name = "PHB polymerization by PhaR/PhaC"
phac.lower_bound, phac.upper_bound = 0, 1000
phac.add_metabolites({hbcoa: -1, coa: 1, phb: 1})
phac.gene_reaction_rule = f"{PHAR_GENE} and {PHAC_GENE}"
model.add_reactions([phac])

# PHB accumulation demand
DEMAND_ID = "DM_phb_repeat_c"
if DEMAND_ID not in model.reactions:
    model.add_boundary(phb, type="demand", reaction_id=DEMAND_ID)

print("PhaB mass balance:", phab.check_mass_balance())
print("PhaC mass balance:", phac.check_mass_balance())

write_sbml_model(model, OUTPUT)
print("已輸出：", OUTPUT)
PY

python 09_GEM/scripts/curate_BMB171_PHA_model.py
```

兩個 mass balance 都要印出 `{}`（空字典 = 完全平衡）。

## Step 8　定義培養基

COBRApy 用 `model.medium` 設定 exchange 上限。這段之後會重複用到，建議存成片段：

```python
medium = {
    "EX_glc__D_e": 10.0,    # 葡萄糖，固定基準
    "EX_nh4_e":   100.0,    # 氮源（之後要掃描的就是它）
    "EX_pi_e":    100.0,
    "EX_o2_e":     60.0,    # 氧氣充足
    "EX_so4_e":   100.0,
    "EX_h2o_e":  1000.0,
    "EX_h_e":    1000.0,
    "EX_k_e":      10.0, "EX_na1_e": 10.0, "EX_cl_e": 10.0,
    "EX_mg2_e":    10.0, "EX_ca2_e": 10.0,
    "EX_fe2_e": 1.0, "EX_fe3_e": 1.0, "EX_mn2_e": 1.0, "EX_zn2_e": 1.0,
    "EX_cu2_e": 0.1, "EX_cobalt2_e": 0.1, "EX_mobd_e": 0.1,
}
medium = {rid: v for rid, v in medium.items() if rid in model.reactions}
model.medium = medium
```

> 最後那一行過濾很重要：模型裡沒有的 exchange reaction 直接丟進去會報錯。

## Step 9　氧氣飽和點掃描

固定 glucose = 10、NH₄ = 100，把 `EX_o2_e` 掃 5 / 10 / 20 / 30 / 40 / 60 / 80 / 100，目標設 `Growth`。

結果：

```text
O2 = 5   → Growth 0.278
O2 = 20  → Growth 0.334
O2 = 40  → Growth 0.408
O2 = 60  → Growth 0.4435  (實際只吃 49.89)
O2 = 80  → Growth 0.4435
O2 = 100 → Growth 0.4435
```

**結論：O₂ 飽和點約 50，之後一律用 `EX_o2_e = 60` 當「氧氣充足」基準。**

## Step 10　氮源健檢（很重要，不要跳過）

O₂ 掃描時出現一個怪現象：**Growth 上升，NH₄ 消耗反而下降**。若 NH₄ 是唯一氮源且元素守恆，理論上不該如此。所以要先查：模型有沒有從別的地方偷到氮？

檢查三件事：
1. 實際被攝取的 exchange 裡有沒有其他含 N 物質（amino acid、urea、nitrate）
2. 有通量的內部反應裡，有沒有 N 元素不平衡的
3. biomass reaction 的元素組成

**結果：乾淨。** 外界含氮攝取只有 `EX_nh4_e`，活躍反應沒有 N 不平衡。

> `Growth` 這條 pseudo-reaction 印出 `'N': -10.768, 'C': -38.83 ...` 的負值是**正常的**，它本來就是把前驅物抽走形成 1 g biomass，不是需要左右平衡的酵素反應。

## Step 11　【關鍵坑】立體異構物旁路 → curated v2

第一次跑最大 PHB 得到 12.5，但是：

```text
PHAB_NADPH = 0        ← PhaB 根本沒被用到！
```

**原因：** BiGG 的 `3hbcoa_c` 指的是 **(S)**-3-hydroxybutanoyl-CoA，不是 PHB 合成需要的 **(R)** 型。而 `ECOAH1`（`3hbcoa_c ⇌ b2coa_c + h2o_c`，β-oxidation 的 enoyl-CoA hydratase）可以反向產生同一個 `3hbcoa_c`，於是模型直接繞過我們補的 PhaB。`HACD1_1` 用的 `3hbycoa_c` 也是 S 型表示。

所以解法不是把 `ECOAH1` 關掉，而是**建立一個專屬的 (R)-3HB-CoA 代謝物**，讓 PHB 路徑和 β-oxidation 徹底分開：

```bash
python - <<'PY'
from cobra.io import read_sbml_model, write_sbml_model
from cobra import Metabolite, Reaction

INPUT  = "09_GEM/curated/BMB171_PHA_curated.xml"
OUTPUT = "09_GEM/curated/BMB171_PHA_curated_v2.xml"
model = read_sbml_model(INPUT)

# 1. 建立真正的 (R)-3-hydroxybutyryl-CoA
R3HB_ID = "3hbcoa_R_c"
if R3HB_ID in model.metabolites:
    r3hbcoa = model.metabolites.get_by_id(R3HB_ID)
else:
    r3hbcoa = Metabolite(R3HB_ID, name="(R)-3-Hydroxybutanoyl-CoA",
                         formula="C25H38N7O18P3S", charge=-4, compartment="c")
    model.add_metabolites([r3hbcoa])

aacoa = model.metabolites.get_by_id("aacoa_c")
nadph = model.metabolites.get_by_id("nadph_c")
nadp  = model.metabolites.get_by_id("nadp_c")
h     = model.metabolites.get_by_id("h_c")
coa   = model.metabolites.get_by_id("coa_c")
phb   = model.metabolites.get_by_id("phb_repeat_c")

# 2. 移除舊的（接錯代謝物的）PhaB / PhaC
for rid in ["PHAB_NADPH", "PHAC_PHB_POLYMERIZATION"]:
    if rid in model.reactions:
        model.remove_reactions([rid], remove_orphans=False)

# 3. 重建 PhaB：aacoa + NADPH + H+ -> (R)-3HB-CoA + NADP+
phab = Reaction("PHAB_NADPH")
phab.name = "PhaB NADPH-dependent (R)-3-hydroxybutyryl-CoA formation"
phab.lower_bound, phab.upper_bound = 0, 1000
phab.add_metabolites({aacoa: -1, nadph: -1, h: -1, r3hbcoa: 1, nadp: 1})
phab.gene_reaction_rule = "WP_000250409_1"
model.add_reactions([phab])

# 4. 重建 PhaR/PhaC：(R)-3HB-CoA -> PHB + CoA
phac = Reaction("PHAC_PHB_POLYMERIZATION")
phac.name = "PHB polymerization from (R)-3-hydroxybutyryl-CoA by PhaR/PhaC"
phac.lower_bound, phac.upper_bound = 0, 1000
phac.add_metabolites({r3hbcoa: -1, coa: 1, phb: 1})
phac.gene_reaction_rule = "WP_000566942_1 and WP_000206336_1"
model.add_reactions([phac])

# 5. 確認 (R)-3HB-CoA 只連到這兩條反應
print("(R)-3HB-CoA connected reactions")
for rxn in r3hbcoa.reactions:
    print(rxn.id, "|", rxn.reaction, "| GPR:", rxn.gene_reaction_rule or "無")

print("\nPhaB mass balance:", phab.check_mass_balance())
print("PhaC mass balance:", phac.check_mass_balance())

write_sbml_model(model, OUTPUT)
print("\n已輸出：", OUTPUT)
PY
```

**驗收標準：** `(R)-3HB-CoA connected reactions` 只能出現 `PHAB_NADPH` 和 `PHAC_PHB_POLYMERIZATION`，**不可以**再看到 `ECOAH1` 或 `HACD1_1`；兩個 mass balance 都是 `{}`。

重跑最大 PHB，這次得到：

```text
ACACT1r                 = 12.5
PHAB_NADPH              = 12.5     ← 現在有通量了
PHAC_PHB_POLYMERIZATION = 12.5
DM_phb_repeat_c         = 12.5
```

每一步都是 12.5，代表沒有繞路。路徑：

```text
Glucose → Acetyl-CoA →(PhaA)→ Acetoacetyl-CoA →(PhaB+NADPH)→ (R)-3HB-CoA →(PhaR+PhaC)→ PHB
```

> 註：v1 和 v2 的最大 PHB 數字都是 12.5，但 v1 是透過錯誤路徑算出來的，**不可信**。數字一樣不代表模型一樣對。

## Step 12　Knockout 負控制驗證

```bash
python - <<'PY'
from cobra.io import read_sbml_model
model = read_sbml_model("09_GEM/curated/BMB171_PHA_curated_v2.xml")

medium = {
    "EX_glc__D_e": 10.0, "EX_nh4_e": 100.0, "EX_pi_e": 100.0,
    "EX_o2_e": 60.0, "EX_so4_e": 100.0, "EX_h2o_e": 1000.0, "EX_h_e": 1000.0,
    "EX_k_e": 10.0, "EX_na1_e": 10.0, "EX_cl_e": 10.0,
    "EX_mg2_e": 10.0, "EX_ca2_e": 10.0,
    "EX_fe2_e": 1.0, "EX_fe3_e": 1.0, "EX_mn2_e": 1.0, "EX_zn2_e": 1.0,
    "EX_cu2_e": 0.1, "EX_cobalt2_e": 0.1, "EX_mobd_e": 0.1,
}
model.medium = {k: v for k, v in medium.items() if k in model.reactions}
model.objective = "DM_phb_repeat_c"

def run_case(label, gene_id=None):
    with model:
        if gene_id:
            model.genes.get_by_id(gene_id).knock_out()
        s = model.optimize()
        print(f"\n===== {label} =====")
        print("Status =", s.status)
        print("PHB        =", s.fluxes["DM_phb_repeat_c"])
        print("PhaB flux  =", s.fluxes["PHAB_NADPH"])
        print("PhaRC flux =", s.fluxes["PHAC_PHB_POLYMERIZATION"])

run_case("WT")
run_case("PhaB knockout", "WP_000250409_1")
run_case("PhaR knockout", "WP_000566942_1")
run_case("PhaC knockout", "WP_000206336_1")
PY
```

**結果：**

| 條件 | PHB flux |
|---|---:|
| WT | **12.50** |
| PhaB KO | −5.7×10⁻¹⁵ ≈ **0** |
| PhaR KO | **0** |
| PhaC KO | **0** |

（−5.7×10⁻¹⁵ 是求解器浮點誤差，視為 0。）

> **模型結構驗證通過：PHB 生產已鎖定在經基因體確認的 PhaB → PhaR/PhaC 路徑，沒有可繞過核心基因的假性替代路徑。** 從這裡開始 `BMB171_PHA_curated_v2.xml` 才是正式分析模型。

## Step 13　NH₄ × Growth × PHB 矩陣

為什麼要加生長下限：只設 `MAX PHB` 的話，模型會選 `Growth = 0, NH4 = 0`——那只是化學計量極限，沒有製程意義。

```bash
python - <<'PY'
from cobra.io import read_sbml_model
import pandas as pd, math

model = read_sbml_model("09_GEM/curated/BMB171_PHA_curated_v2.xml")

base_medium = {
    "EX_glc__D_e": 10.0, "EX_pi_e": 100.0, "EX_o2_e": 60.0, "EX_so4_e": 100.0,
    "EX_h2o_e": 1000.0, "EX_h_e": 1000.0,
    "EX_k_e": 10.0, "EX_na1_e": 10.0, "EX_cl_e": 10.0,
    "EX_mg2_e": 10.0, "EX_ca2_e": 10.0,
    "EX_fe2_e": 1.0, "EX_fe3_e": 1.0, "EX_mn2_e": 1.0, "EX_zn2_e": 1.0,
    "EX_cu2_e": 0.1, "EX_cobalt2_e": 0.1, "EX_mobd_e": 0.1,
}
base_medium = {k: v for k, v in base_medium.items() if k in model.reactions}

# 先求 μmax
with model:
    model.medium = {**base_medium, "EX_nh4_e": 100.0}
    model.objective = "Growth"
    mu_max = model.optimize().objective_value
print("mu_max =", mu_max)

nh4_levels = [10, 7.5, 5, 4, 3, 2, 1, 0.5, 0.2, 0.1, 0.05, 0]
growth_fractions = [0.00, 0.10, 0.25, 0.50, 0.75, 0.90]

rows = []
for nh4_limit in nh4_levels:
    for fraction in growth_fractions:
        with model:
            model.medium = {**base_medium, "EX_nh4_e": nh4_limit}
            model.reactions.get_by_id("Growth").lower_bound = fraction * mu_max
            model.objective = "DM_phb_repeat_c"
            s = model.optimize()

            if s.status == "optimal":
                glc = abs(s.fluxes["EX_glc__D_e"])
                nh4 = abs(s.fluxes["EX_nh4_e"])
                phb = s.fluxes["DM_phb_repeat_c"]
                # PHB repeat 86.09 g/mol；glucose 180.156 g/mol
                yield_gg = (phb * 86.09) / (glc * 180.156) if glc > 1e-9 else math.nan
                cn = (glc * 6) / nh4 if nh4 > 1e-9 else math.inf
                rows.append({
                    "NH4_limit": nh4_limit,
                    "Growth_fraction_of_mu_max": fraction,
                    "Growth_flux": s.fluxes["Growth"],
                    "PHB_flux": phb,
                    "PHB_yield_g_g_glucose": yield_gg,
                    "NH4_uptake": nh4,
                    "O2_uptake": abs(s.fluxes["EX_o2_e"]),
                    "Metabolic_C_N_ratio": cn,
                    "Status": s.status,
                })
            else:
                rows.append({"NH4_limit": nh4_limit,
                             "Growth_fraction_of_mu_max": fraction,
                             "Status": s.status})

df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv("09_GEM/reports/BMB171_NH4_Growth_PHB_matrix.csv", index=False)
try:
    df.to_excel("09_GEM/reports/BMB171_NH4_Growth_PHB_matrix.xlsx", index=False)
except Exception as e:
    print("Excel 輸出失敗，但 CSV 已產生：", e)
PY
```

**主要發現：只要 NH₄ 供應足以支撐指定的生長速率，PHB flux 與 yield 幾乎不再受 NH₄ 上限影響。** 氮限制是透過限制 biomass 間接把碳讓給 PHB。

另一個漂亮的內部一致性檢查：

```text
q(NH4) ≈ 10.7682 × μ

Growth 0.04435 → NH4 0.4776
Growth 0.11088 → NH4 1.1940
Growth 0.22177 → NH4 2.3880
Growth 0.33265 → NH4 3.5821
```

這個係數剛好對得上 biomass reaction 的 N 係數。所以當 `NH4_limit = 4` 時 90% μmax（需要 4.298）會 infeasible、`NH4_limit = 3` 時 75% μmax（需要 3.582）會 infeasible——**infeasible 在這裡是約束正確運作的證據，不是錯誤。**

## Step 14　Growth–PHB trade-off 曲線

把 `fractions` 改成 0.00 到 1.00 每 0.05 一格，NH₄ 固定 100（不限氮），其餘同上，輸出：

```text
09_GEM/reports/BMB171_Growth_PHB_tradeoff.csv / .xlsx
```

結果見第一部分的 trade-off 表。重點是 **55–60% μmax 的轉折**。

## Step 15　pFBA（下一步，尚未執行）

pFBA 在維持最佳目標值的前提下再最小化總通量，比單一 FBA 解更適合判讀「主要碳流」。

```bash
python - <<'PY'
from cobra.io import read_sbml_model
from cobra.flux_analysis import pfba
import pandas as pd

model = read_sbml_model("09_GEM/curated/BMB171_PHA_curated_v2.xml")

medium = {
    "EX_glc__D_e": 10.0, "EX_nh4_e": 100.0, "EX_pi_e": 100.0,
    "EX_o2_e": 60.0, "EX_so4_e": 100.0, "EX_h2o_e": 1000.0, "EX_h_e": 1000.0,
    "EX_k_e": 10.0, "EX_na1_e": 10.0, "EX_cl_e": 10.0,
    "EX_mg2_e": 10.0, "EX_ca2_e": 10.0,
    "EX_fe2_e": 1.0, "EX_fe3_e": 1.0, "EX_mn2_e": 1.0, "EX_zn2_e": 1.0,
    "EX_cu2_e": 0.1, "EX_cobalt2_e": 0.1, "EX_mobd_e": 0.1,
}
model.medium = {k: v for k, v in medium.items() if k in model.reactions}

model.objective = "Growth"
mu_max = model.optimize().objective_value
print("mu_max =", mu_max)

target_ids = ["Growth", "EX_glc__D_e", "EX_o2_e", "EX_nh4_e", "EX_co2_e",
              "ACACT1r", "PHAB_NADPH", "PHAC_PHB_POLYMERIZATION", "DM_phb_repeat_c",
              "PDH", "CS", "PTAr", "ACKr"]

rows = []
for fraction in [0.10, 0.25, 0.50]:
    with model:
        model.reactions.get_by_id("Growth").lower_bound = fraction * mu_max
        model.objective = "DM_phb_repeat_c"
        sol = pfba(model)
        for rid in target_ids:
            if rid in model.reactions:
                rows.append({"Growth_fraction": fraction, "Reaction_ID": rid,
                             "Reaction_name": model.reactions.get_by_id(rid).name,
                             "Flux": sol.fluxes[rid]})

pivot = pd.DataFrame(rows).pivot(index=["Reaction_ID","Reaction_name"],
                                 columns="Growth_fraction", values="Flux")
pivot.columns = ["10pct_mu_max", "25pct_mu_max", "50pct_mu_max"]
print(pivot.to_string())
pivot.to_excel("09_GEM/reports/BMB171_pFBA_key_fluxes.xlsx")
PY
```

**判讀方式：**

| 看什麼 | 意義 |
|---|---|
| `ACACT1r` / `PHAB_NADPH` / `PHAC_...` | 往 PHB 的碳流 |
| `CS`（citrate synthase） | acetyl-CoA 進 TCA 的量 |
| `PTAr` / `ACKr` | acetyl-CoA 是否被分流成 acetate（overflow） |
| PPP 相關 | NADPH 供應是否足夠餵 PhaB |

若 Growth 從 10% → 50% 時 `PHB ↓` 而 `CS ↑`，代表 biomass 生長把 acetyl-CoA 吃去 TCA；若 `PTAr/ACKr` 很高，acetate overflow 就是下一個工程標的。

---

# 第三部分　附錄：常見錯誤與排解

| 症狀 | 原因 | 解法 |
|---|---|---|
| `phaC: command not found`，Ubuntu 建議 `sudo apt install php-cli` | 把「基因名稱」當成指令貼進終端機 | 基因名要放在 `grep -ni 'phaC' "$GBFF"` 的引號裡。**絕對不要**照 Ubuntu 建議安裝 PHP 套件 |
| 把範例輸出（`/product="..."`、`BMB171_RS06645`）整段貼進去執行 | 那是「預期看到的畫面」不是指令 | 只複製 ```bash 區塊裡面的內容。不會弄壞任何東西 |
| `carve: command not found`，Ubuntu 建議 `sudo apt install carve` | CarveMe 還沒裝；apt 的 `carve` 是完全不同的軟體 | `conda install -c bioconda carveme diamond pyscipopt -y`，再用 `command -v carve` 確認路徑指向 `envs/btcobra/bin/carve` |
| `WP_xxxxxxxxx.1` 放進模型 | 那是占位示意文字 | 用 Step 3 的 Biopython 查出真正的 protein ID |
| GPR 寫 `WP_000250409.1` 無效 | COBRApy 的 gene ID 不吃小數點 | 改成 `WP_000250409_1` |
| `No such file or directory: curate_BMB171_PHA_model.py` | heredoc 沒寫完整 / nano 沒存檔 | 用 `ls -lh` 和 `tail -n 5` 確認檔案存在且結尾完整；nano 存檔是 `Ctrl+O` → Enter → `Ctrl+X` |
| 設 medium 時 KeyError | 模型裡沒有那個 exchange reaction | 一定要加 `{k: v for k, v in medium.items() if k in model.reactions}` |
| 最大 PHB 有數字，但 `PHAB_NADPH = 0` | BiGG 的 `3hbcoa_c` 是 (S) 型，`ECOAH1` 可反向生成它繞過 PhaB | 建立專屬 `3hbcoa_R_c`（見 Step 11）。**這是整份分析最重要的一個坑** |
| `mass balance` 印出一堆元素而不是 `{}` | 反應式配平錯或 formula 填錯 | 檢查 `add_metabolites` 的係數與 metabolite 的 `formula`/`charge` |
| `Growth` 的元素平衡全是負值 | 正常，它是 pseudo-reaction | 不需要修 |
| knockout 後 PHB = −5.7×10⁻¹⁵ | 求解器浮點誤差 | 視為 0 |
| 某些組合 `infeasible` | 生長下限需要的 NH₄ 超過你設的上限 | 這是約束正確運作的證據。想避開就提高 `NH4_limit` |
| `less` 裡面執行 `explorer.exe .` 出現 `No log file` | 還在 less 內 | 先按 `q` 離開再執行 |
| Excel 開檔視窗看不到 `.tsv` | Excel 預設只篩 `.txt`/`.csv` | `cp xxx.tsv xxx.txt`，再用「資料 → 從文字/CSV」，編碼 65001 UTF-8、分隔符號選 Tab |
| Excel 裡空白欄位變成數字 `15` | 匯入/轉檔造成的內容異常 | 重新用「從文字/CSV」匯入，不要雙擊開啟 |
| `df.to_excel` 失敗 | 缺 `openpyxl` | CSV 仍會正常產生；要 Excel 就 `conda install openpyxl` |

### 要去 Windows 看檔案

```bash
explorer.exe .                                   # 開啟目前資料夾
cmd.exe /c start .                               # 備用寫法
\\wsl$\Ubuntu-24.04\home\<帳號>\Bt_PHA_analysis   # 直接貼進檔案總管網址列
wsl.exe -l -q                                    # 查發行版正確名稱
```

複製結果到桌面：

```bash
WINUSER=$(cmd.exe /c echo %USERNAME% | tr -d '\r')
mkdir -p "/mnt/c/Users/$WINUSER/Desktop/Bt_PHA_results"
cp ~/Bt_PHA_analysis/03_candidate_genes/*.tsv "/mnt/c/Users/$WINUSER/Desktop/Bt_PHA_results/"
explorer.exe "/mnt/c/Users/$WINUSER/Desktop/Bt_PHA_results"
```

---

# 第四部分　重要限制（引用時務必保留）

1. **基因體本身無法直接算出最佳溫度、C/N、轉速或進料濃度。** 它只能告訴你菌株具備哪些代謝能力、pathway 是否完整、哪些競爭路徑會分走 acetyl-CoA 或 NADPH。真正的高產條件仍需培養試驗、RT-qPCR、RNA-seq 或蛋白質體驗證。
2. **0.597 g/g 是「目前模型在既定培養基、無生長需求下的化學計量理論上限」**，不是實際醱酵可達產率。
3. **`Metabolic_C_N_ratio` 是代謝攝取比，不是培養基配方的重量 C/N。**
4. **BMB171 是去除質體、無晶體蛋白的衍生株**，不能直接代表所有商業 Bt 菌株。
5. **CarveMe 的產物是 draft，官方定位就是需要人工校正**；gap filling 可能加入沒有基因證據的反應。
6. 表中 `enoyl-CoA hydratase` 目前只能標為 **phaJ 候選**，不能僅憑 product 名稱認定。
7. 55–60% μmax 的轉折目前仍是**模型推論**，要靠 pFBA/FVA 找出實際是哪幾條反應在變。

## 產出檔案清單

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
