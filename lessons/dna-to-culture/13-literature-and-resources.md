# 第 13 章　國內外文獻與資源

這一章是閱讀地圖與工具箱：先讀什麼、每篇能學到什麼、有哪些免費的資料庫和軟體可以直接用。

## 11.1 閱讀順序建議

| 順序 | 讀什麼 | 為什麼 |
|---|---|---|
| 1 | A1–A3 綜述 | 建立全貌：代謝模型是什麼、能做什麼 |
| 2 | B 類方法論文（挑和你要用的工具相關的） | 了解工具的假設與限制 |
| 3 | C 類動態與分階段 | 對應你的「分階段調參數」問題 |
| 4 | D 類 AI 最適化 | 決定實驗策略 |
| 5 | E 類資料庫論文 | 需要查資料時再讀 |

## 11.2 國外文獻

### A. 綜述與入門（先讀這些）

| 編號 | 文獻 | 重點 |
|---|---|---|
| A1 | Orth, Thiele & Palsson (2010) [1] | 四頁讀懂 FBA，有圖解，最好的入門 |
| A2 | Gu et al. (2019) [2] | 基因體尺度代謝模型的現況與應用，含工業菌的例子 |
| A3 | Fang, Lloyd & Palsson (2020) [3] | 代謝模型的新應用方向 |
| A4 | Lewis, Nagarajan & Palsson (2012) [4] | 各種限制式分析方法的整理，當工具書用 |

### B. 建模方法與工具

| 編號 | 文獻 | 重點 |
|---|---|---|
| B1 | Thiele & Palsson (2010) [5] | 高品質重建的 96 步標準流程 |
| B2 | COBRA Toolbox v3（Heirendt et al., 2019）[6]、COBRApy（Ebrahim et al., 2013）[7] | 最常用的兩套分析軟體（MATLAB 與 Python） |
| B3 | CarveMe（Machado et al., 2018）[8] | 從基因體快速自動建模 |
| B4 | gapseq（Zimmermann et al., 2021）[9] | 自動建模，碳源與發酵產物預測較準 |
| B5 | ModelSEED（Henry et al., 2010）[10] | 高通量建模，KBase 網頁平台的核心 |
| B6 | MEMOTE（Lieven et al., 2020）[11] | 模型品質檢查的標準 |
| B7 | BiGG Models（King et al., 2016）[12] | 手工整理的高品質模型資料庫 |

### C. 動態模擬與分階段培養

| 編號 | 文獻 | 重點 |
|---|---|---|
| C1 | Mahadevan et al. (2002) [13] | dFBA 原始論文，用大腸桿菌的雙峰生長示範 |
| C2 | Varma & Palsson (1994) [14] | 第一批用 FBA 定量預測乙酸分泌的研究，本教材參數的來源 |
| C3 | Klamt, Mahadevan & Hädicke (2018) [15] | 兩階段什麼時候勝過單階段：速率與產率的取捨 |
| C4 | Venayak et al. (2015) [16] | 用基因工程做動態代謝控制 |
| C5 | COMETS 2（Dukovski et al., 2021）[17] | 多菌種、有空間的動態模擬，做混菌時參考 |

### D. AI 與實驗最適化

| 編號 | 文獻 | 重點 |
|---|---|---|
| D1 | Shahriari et al. (2016) [18] | 貝氏最適化綜述 |
| D2 | HamediRad et al. (2019) [19] | BioAutomata：機器人＋貝氏最適化 |
| D3 | Zhang, Aida & Ying (2023) [20] | 主動學習最適化選擇性培養基 |
| D4 | Radivojević et al. (2020) [21] | ART：合成生物學的機器學習推薦工具 |
| D5 | Zampieri et al. (2019) [22] | 機器學習與代謝模型的結合方式 |

### E. 資料庫與從基因體預測生長條件

| 編號 | 文獻 | 重點 |
|---|---|---|
| E1 | BacDive（Reimer et al., 2022）[23] | 八萬多株細菌與古菌的培養、代謝資料 |
| E2 | MediaDive（Koblitz et al., 2023）[24] | 三千多種標準化培養基配方 |
| E3 | Li et al. (2019) [25] | 從基因體預測最適生長溫度 |
| E4 | Ramoneda et al. (2023) [26] | 從基因體理解與預測 pH 偏好 |

## 11.3 免費工具與資料庫

| 類別 | 名稱 | 網址 |
|---|---|---|
| 分析軟體 | COBRApy | https://opencobra.github.io/cobrapy/ |
| 自動建模 | CarveMe | https://github.com/cdanielmachado/carveme |
| 自動建模 | gapseq | https://github.com/jotech/gapseq |
| 網頁平台 | KBase | https://www.kbase.us |
| 模型資料庫 | BiGG Models | http://bigg.ucsd.edu |
| 模型品質 | MEMOTE | https://memote.io |
| 代謝圖 | Escher [27] | https://escher.github.io |
| 菌株資料 | BacDive | https://bacdive.dsmz.de |
| 培養基 | MediaDive | https://mediadive.dsmz.de |
| 代謝路徑 | KEGG | https://www.kegg.jp |
| 本教材程式 | code/、simulator/ | 在 GitHub 專案的 lessons/dna-to-culture/ |

## 11.4 臺灣的資源與研究現況

**資源**：

| 單位 | 能提供什麼 |
|---|---|
| 食品工業發展研究所生物資源保存及研究中心（BCRC） | 菌種保存與購買；菌株的建議培養條件；寄存自己的菌株 |
| 農業科技研究院 | 細菌全基因體定序與分析服務（組裝、分型、抗藥基因、親緣分析）[28] |
| 國立臺灣海洋大學海洋基因體中心 | 長讀定序與註解服務 [29] |
| 國家高速網路與計算中心 | 大量計算需求時可用的雲端運算資源 |
| 各大學的基因體或生物資訊核心設施 | 定序、分析諮詢 |

**研究現況**：

- 臺灣在發酵、微藻、益生菌培養的「實驗最適化」研究很多，常用反應曲面法。
- 但「從基因體建代謝模型，再用來設計培養條件，並做成視覺化介面」的整合研究或平台，我在公開資料中**沒有找到**。

這代表兩件事：

1. 方法本身都是公開、成熟的，沒有技術門檻阻止你開始；
2. 把它整合起來用在你的菌株上，在國內是少見的做法，有發表與申請計畫的價值。

（我的搜尋範圍是公開網頁與期刊資料庫，可能有未公開或以中文發表的研究沒有找到。建議也到臺灣博碩士論文知識加值系統，用「代謝模型」、「通量平衡分析」搜尋。）

## 本章重點

- 入門先讀 Orth 等人（2010）與 Gu 等人（2019）兩篇綜述。
- 工具全部免費：COBRApy、CarveMe、gapseq、KBase、MEMOTE、Escher、BacDive、MediaDive。
- 臺灣有定序服務與菌種中心，但少見「基因體→代謝模型→培養最適化→介面」的整合，這是機會。

## 參考文獻

1. Orth JD, Thiele I, Palsson BØ (2010). What is flux balance analysis? *Nature Biotechnology*, 28, 245–248. https://doi.org/10.1038/nbt.1614
2. Gu C, Kim GB, Kim WJ, Kim HU, Lee SY (2019). Current status and applications of genome-scale metabolic models. *Genome Biology*, 20, 121. https://doi.org/10.1186/s13059-019-1730-3
3. Fang X, Lloyd CJ, Palsson BO (2020). Reconstructing organisms in silico: genome-scale models and their emerging applications. *Nature Reviews Microbiology*, 18, 731–743. https://doi.org/10.1038/s41579-020-00440-4
4. Lewis NE, Nagarajan H, Palsson BO (2012). Constraining the metabolic genotype–phenotype relationship using a phylogeny of in silico methods. *Nature Reviews Microbiology*, 10, 291–305. https://doi.org/10.1038/nrmicro2737
5. Thiele I, Palsson BØ (2010). A protocol for generating a high-quality genome-scale metabolic reconstruction. *Nature Protocols*, 5, 93–121. https://doi.org/10.1038/nprot.2009.203
6. Heirendt L, Arreckx S, Pfau T, et al. (2019). Creation and analysis of biochemical constraint-based models using the COBRA Toolbox v.3.0. *Nature Protocols*, 14, 639–702. https://doi.org/10.1038/s41596-018-0098-2
7. Ebrahim A, Lerman JA, Palsson BO, Hyduke DR (2013). COBRApy: COnstraints-Based Reconstruction and Analysis for Python. *BMC Systems Biology*, 7, 74. https://doi.org/10.1186/1752-0509-7-74
8. Machado D, Andrejev S, Tramontano M, Patil KR (2018). Fast automated reconstruction of genome-scale metabolic models for microbial species and communities. *Nucleic Acids Research*, 46, 7542–7553. https://doi.org/10.1093/nar/gky537
9. Zimmermann J, Kaleta C, Waschina S (2021). gapseq: informed prediction of bacterial metabolic pathways and reconstruction of accurate metabolic models. *Genome Biology*, 22, 81. https://doi.org/10.1186/s13059-021-02295-1
10. Henry CS, DeJongh M, Best AA, Frybarger PM, Linsay B, Stevens RL (2010). High-throughput generation, optimization and analysis of genome-scale metabolic models. *Nature Biotechnology*, 28, 977–982. https://doi.org/10.1038/nbt.1672
11. Lieven C, Beber ME, Olivier BG, et al. (2020). MEMOTE for standardized genome-scale metabolic model testing. *Nature Biotechnology*, 38, 272–276. https://doi.org/10.1038/s41587-020-0446-y
12. King ZA, Lu J, Dräger A, et al. (2016). BiGG Models: A platform for integrating, standardizing and sharing genome-scale models. *Nucleic Acids Research*, 44, D515–D522. https://doi.org/10.1093/nar/gkv1049
13. Mahadevan R, Edwards JS, Doyle FJ (2002). Dynamic flux balance analysis of diauxic growth in *Escherichia coli*. *Biophysical Journal*, 83, 1331–1340. https://doi.org/10.1016/S0006-3495(02)73903-9
14. Varma A, Palsson BO (1994). Stoichiometric flux balance models quantitatively predict growth and metabolic by-product secretion in wild-type *Escherichia coli* W3110. *Applied and Environmental Microbiology*, 60, 3724–3731. https://doi.org/10.1128/aem.60.10.3724-3731.1994
15. Klamt S, Mahadevan R, Hädicke O (2018). When do two-stage processes outperform one-stage processes? *Biotechnology Journal*, 13, 1700539. https://doi.org/10.1002/biot.201700539
16. Venayak N, Anesiadis N, Cluett WR, Mahadevan R (2015). Engineering metabolism through dynamic control. *Current Opinion in Biotechnology*, 34, 142–152. https://doi.org/10.1016/j.copbio.2014.12.022
17. Dukovski I, Bajić D, Chacón JM, et al. (2021). A metabolic modeling platform for the computation of microbial ecosystems in time and space (COMETS). *Nature Protocols*, 16, 5030–5082. https://doi.org/10.1038/s41596-021-00593-3
18. Shahriari B, Swersky K, Wang Z, Adams RP, de Freitas N (2016). Taking the human out of the loop: a review of Bayesian optimization. *Proceedings of the IEEE*, 104, 148–175. https://doi.org/10.1109/JPROC.2015.2494218
19. HamediRad M, Chao R, Weisberg S, et al. (2019). Towards a fully automated algorithm driven platform for biosystems design. *Nature Communications*, 10, 5150. https://doi.org/10.1038/s41467-019-13189-z
20. Zhang S, Aida H, Ying BW (2023). Employing active learning in medium optimization for selective bacterial growth. *Applied Microbiology*, 3, 1355–1369. https://doi.org/10.3390/applmicrobiol3040091
21. Radivojević T, Costello Z, Workman K, Garcia Martin H (2020). A machine learning Automated Recommendation Tool for synthetic biology. *Nature Communications*, 11, 4879. https://doi.org/10.1038/s41467-020-18008-4
22. Zampieri G, Vijayakumar S, Yaneske E, Angione C (2019). Machine and deep learning meet genome-scale metabolic modeling. *PLoS Computational Biology*, 15, e1007084. https://doi.org/10.1371/journal.pcbi.1007084
23. Reimer LC, Sardà Carbasse J, Koblitz J, et al. (2022). BacDive in 2022: the knowledge base for standardized bacterial and archaeal data. *Nucleic Acids Research*, 50, D741–D746. https://doi.org/10.1093/nar/gkab961
24. Koblitz J, Halama P, Spring S, et al. (2023). MediaDive: the expert-curated cultivation media database. *Nucleic Acids Research*, 51, D1531–D1538. https://doi.org/10.1093/nar/gkac803
25. Li G, Rabe KS, Nielsen J, Engqvist MKM (2019). Machine learning applied to predicting microorganism growth temperatures and enzyme catalytic optima. *ACS Synthetic Biology*, 8, 1411–1420. https://doi.org/10.1021/acssynbio.9b00099
26. Ramoneda J, Stallard-Olivera E, Hoffert M, et al. (2023). Building a genome-based understanding of bacterial pH preferences. *Science Advances*, 9, eadf8998. https://doi.org/10.1126/sciadv.adf8998
27. King ZA, Dräger A, Ebrahim A, Sonnenschein N, Lewis NE, Palsson BO (2015). Escher: a web application for building, sharing, and embedding data-rich visualizations of biological pathways. *PLoS Computational Biology*, 11, e1004321. https://doi.org/10.1371/journal.pcbi.1004321
28. 農業科技研究院：細菌全基因體定序與分析服務介紹。https://agritechtaiwan.com/en-gb/a-powerful-genomebased-characterization-tool-launched-by-agricultural-technology-research-institute-taiwan
29. 國立臺灣海洋大學海洋基因體中心：定序服務價目。https://en-taogc.ntou.edu.tw/service/4
