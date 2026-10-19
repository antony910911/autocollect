# 第 4 章　自己重跑（一）：環境、基因體、找基因

從這一章開始是操作手冊。全部在 **Windows + WSL2 Ubuntu** 下做，專案根目錄 `~/Bt_PHA_analysis`。

> **這幾章的程式要在你自己的電腦上跑**，不能在這個 repo 裡跑——這裡沒有 BMB171 的基因體檔案，也沒有對外網路。

## 4.1 兩個 conda 環境

分開裝，避免套件衝突。

**環境一：基因體分析**

```bash
conda create -n btpha \
  -c conda-forge -c bioconda \
  ncbi-datasets-cli python=3.12 biopython pandas blast diamond seqkit -y

conda activate btpha
```

確認：`datasets version`、`dataformat version`、`python --version`、`blastp -version`、`diamond version`。

**環境二：代謝模型**

```bash
conda create -n btcobra \
  -c conda-forge -c bioconda \
  python=3.10 cobra diamond pyscipopt memote pandas openpyxl -y

conda activate btcobra
conda install -c bioconda carveme diamond pyscipopt -y
```

確認 CarveMe 真的裝好了：

```bash
conda list carveme
command -v carve          # 應該顯示 .../envs/btcobra/bin/carve
carve --help | head -n 20
```

> **不要用 `sudo apt install carve`。** apt 裡那個 `carve` 是完全不同的軟體。終端機看到 `carve: command not found` 的時候 Ubuntu 會好心建議你裝它，不要照做（第 7 章）。

**資料夾**

```bash
mkdir -p ~/Bt_PHA_analysis/{00_metadata,01_all_genomes,02_reference_genomes,03_candidate_genes,04_homology,05_synteny,06_comparative,07_pathway,08_culture_hypotheses,scripts,logs}
mkdir -p ~/Bt_PHA_analysis/09_GEM/{draft,curated,reports,scripts}
cd ~/Bt_PHA_analysis
```

**原則：原始下載的資料保持不動，不要直接在下載資料夾裡改檔案。** 之後任何一步出錯，你都還有一份乾淨的可以回去。

## 4.2 下載參考基因體

不要一開始就抓全部的 *B. thuringiensis* 基因體。先用 2–3 株把流程跑通。

**BMB171**（主力參考株）：

```bash
conda activate btpha
cd ~/Bt_PHA_analysis

datasets download genome accession GCA_000092165.1 \
  --include genome,protein,cds,gff3,gbff,seq-report \
  --filename 02_reference_genomes/BMB171.zip

unzip -q 02_reference_genomes/BMB171.zip -d 02_reference_genomes/BMB171
```

**ATCC 35646**（當 phaZ／PHB 降解的參考）：

```bash
datasets download genome accession GCF_000167695.1 \
  --include genome,protein,cds,gff3,gbff,seq-report \
  --filename 02_reference_genomes/ATCC35646.zip

unzip -q 02_reference_genomes/ATCC35646.zip -d 02_reference_genomes/ATCC35646
```

下載下來的檔案各有用途：

| 檔案 | 用途 |
|---|---|
| `*_genomic.fna` | 全基因體 DNA |
| `protein.faa` | 全部預測蛋白質序列——**CarveMe 要吃這個** |
| `genomic.gff` | 基因座標與註解 |
| `genomic.gbff` | 完整 GenBank 註解（gene name、product、protein_id、translation） |
| `cds_from_genomic.fna` | CDS 核酸序列 |
| `sequence_report.jsonl` | 染色體／質體資訊 |

> **BMB171 是去除質體、沒有晶體蛋白的衍生株。** 它基因體完整、文獻上被用在 PHB 與 phaC／spo0A／sigH 的研究，當參考株很合適——但**它不能代表商業用的 Bt 菌株**。這件事在引用結論時要講出來。

## 4.3 找出 PHA 相關基因

### 先 grep 看一眼

```bash
GBFF=$(find 02_reference_genomes/BMB171 -type f -name "*.gbff" | head -n 1)
echo "$GBFF"

grep -niE -C 8 \
'phaP|phaQ|phaR|phaB|phaC|phaZ|spo0A|sigH|polyhydroxyalkanoate|polyhydroxybutyrate|hydroxybutyrate|phasin|acetoacetyl[- ]CoA reductase|acetyl[- ]CoA acetyltransferase|PHA synthase|PHB depolymerase' \
"$GBFF" > 03_candidate_genes/BMB171_PHA_hits.txt
```

> `phaP`、`phaC` 這些是**基因名稱，不是指令**。一定要放在 grep 的引號裡。直接把 `phaC` 貼進終端機，Ubuntu 會回 `phaC: command not found` 並建議你 `sudo apt install php-cli`——那是 PHP，跟這件事一點關係都沒有。

### 再用 Biopython 做結構化擷取

grep 只是看一眼，正式的產出要這一支：

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

注意這支程式的篩選邏輯是「gene name 命中」**或**「product 名稱命中正則」。所以註解沒寫 gene name 的也會被抓到——phaB 就是這樣進來的。反過來說，**gene name 和 product 都沒命中的就會漏掉**，sigH 很可能是這樣漏的。

## 4.4 判讀基因簇

把 15 個候選依 `start_bp` 排序，分成三類看：

1. **合成與顆粒**：phaA、phaB、phaC、phaR、phaP、phaJ
2. **降解**：phaZ
3. **調控**：spo0A、sigH、abrB、ccpA、codY

要看的是：座標是不是相鄰、strand 是不是相同、有沒有形成 `phaR–phaB–phaC`、有沒有形成 `phaP–phaQ`、phaZ 在哪、哪幾列 gene 欄是空的但 product 是 PHA 相關。

結果見第 2 章。

### 取得正式的 protein ID

模型的 GPR 規則要用真的 protein ID，不能用占位字串：

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
BMB171_RS06650 → acetoacetyl-CoA reductase（＝ PhaB）→ WP_000250409.1
BMB171_RS06655 → PhaC → WP_000206336.1
```

> **COBRApy 的 gene id 不吃小數點。** 寫進 GPR 的時候要改成 `WP_000250409_1`。
