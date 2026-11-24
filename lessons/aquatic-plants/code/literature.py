"""物種表、實場案例表、文獻清單——教材裡的表格全部從這裡長出來。

這份檔案本身不做運算（運算在 tolerance.py 與 sizing.py），它的工作是
**把每一筆事實綁上來源與可信度**，避免章節裡出現查不到出處的句子。

欄位：
    conf  abstract  = 摘要／資料庫紀錄裡明確寫出的
          secondary = 回顧文章、搜尋摘要或政府網頁的轉述
          inference = 我們自己推的（一定要在章節裡標明）
    ref   對應 REFS 裡的 key；REFS 只對「DOI 已在搜尋結果中看到原文字串」的那些填 doi，
          其餘留空（寧可只給網址，也不要猜 DOI——CI 會到 Crossref 核對，猜錯會讓 build 失敗）

執行：python lessons/aquatic-plants/code/literature.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

# ── 物種表 ───────────────────────────────────────────────────────
# form: float（浮水）/ submerged（沉水或漂浮莖）/ emergent（挺水）/ algae
# tw: native（原生）/ exotic（外來）/ invasive（外來且已列為入侵或危害紀錄）/ crop（作物）/ mixed（屬內兩者都有）
SPECIES = [
    dict(zh="青萍", sp="Lemna aequinoctialis", form="float", tw="native",
         n_evidence="浮萍屬偏好吸收 NH4+；Lemna minor 的銨吸收 Km 約 1.88 mg/L、Vmax 0.082 mg/(g FW·h)",
         conf="secondary", ref="r_lemna_kinetics",
         pros="繁殖極快、容易撈取、蛋白質高（乾重 25–45%）",
         cons="游離氨敏感；風一吹就堆到池邊；需要遮風",
         why="台灣低海拔水田、池塘到處都有，取材容易，是最適合當第一個篩選對象的本土浮萍"),
    dict(zh="紫萍", sp="Spirodela polyrhiza", form="float", tw="native",
         n_evidence="總氨氮與 pH 對生長速率的影響已被系統性量測（Caicedo et al. 2000）",
         conf="abstract", ref="r_caicedo2000",
         pros="葉片較大、好撈；澱粉可累積到乾重 6 成以上（做乙醇）",
         cons="同樣怕游離氨", why="有現成的毒性曲線可以對照，實驗設計不用從零開始"),
    dict(zh="無根萍", sp="Wolffia globosa", form="float", tw="native",
         n_evidence="沒查到氨氮耐受度的定量資料", conf="secondary", ref="r_efsa_wolffia",
         pros="世界最小的開花植物；已有以人類食品（Mankai）送審的案例",
         cons="太小，採收與固液分離困難；EFSA 對錳含量有安全疑慮，食品化卡住",
         why="如果目標是「氮變成食物」，這是唯一有送審紀錄的屬"),
    dict(zh="大萍（水芙蓉）", sp="Pistia stratiotes", form="float", tw="invasive",
         n_evidence="能有效降低富營養化逕流的氮磷；沒查到氨氮的 EC50 或耐受門檻",
         conf="abstract", ref="r_lu2010",
         pros="生長快、根系大、好撈", cons="外來入侵種，必須圍封；怕寒",
         why="取材容易、文獻多，但耐受度資料缺口大——反而是值得補的題目"),
    dict(zh="布袋蓮", sp="Pontederia crassipes", form="float", tw="invasive",
         n_evidence="最適條件下吸氮可達 2.161 g N/m²/d；改用沼液當氮源只剩 0.124–0.602",
         conf="abstract", ref="r_reddy_tucker",
         pros="單位面積吸氮最高、生物量最大、文獻最多",
         cons="外來入侵種；含水量高、收割處理量大；怕寒；塞住河道",
         why="上限參考值。但要注意那個 2.161 是「最適條件」，不是你會遇到的條件"),
    dict(zh="滿江紅", sp="Azolla spp.", form="float", tw="mixed",
         n_evidence="與 Anabaena 共生固氮；二級放流水中 100 ppm N 的去除率只有 36%",
         conf="abstract", ref="r_azolla_golzary",
         pros="固氮、可當綠肥與飼料（粗蛋白 23–37%）；稻田裡有幾百年的使用史",
         cons="會固氮代表它不缺氮——拿來「移除氮」效率不見得好；怕高溫強光",
         why="適合「氮回收成肥料／飼料」這條路，不適合「把氮降到放流標準」",
         tw_note="台灣的滿江紅屬有原生種也有外來種（例如 *A. filiculoides*），要用學名確認"),
    dict(zh="粉綠狐尾藻", sp="Myriophyllum aquaticum", form="submerged", tw="invasive",
         n_evidence="可在銨 >26 mM（約 364 mg N/L）的畜牧廢水中存活；中試濕地 600 天氨氮平均去除 98.3%",
         conf="abstract", ref="r_myrio_regnet",
         pros="目前查到最耐高濃度氨氮的水生植物；把吸進去的銨在體內轉成硝酸鹽避毒",
         cons="在台灣是入侵種，逸出風險高；屬沉水／漂浮莖，收割不如浮萍容易",
         why="如果你的水是高濃度氨氮（沼液、垃圾滲出水），這是第一名的候選"),
    dict(zh="香蒲", sp="Typha orientalis", form="emergent", tw="native",
         n_evidence="總氨氮 200 mg/L 以下生長影響小，100–200 mg/L 區間甚至被促進",
         conf="abstract", ref="r_wang2016",
         pros="本土、耐受度高、根系供氧好，人工濕地主力",
         cons="佔地大；植物吸收佔比低，主要靠根圈微生物",
         why="長期穩定運轉的首選，而且是原生種，不用擔心逸散"),
    dict(zh="美人蕉", sp="Canna indica", form="emergent", tw="exotic",
         n_evidence="與香蒲同列最耐的兩種（門檻約 200 mg/L TAN）", conf="abstract", ref="r_wang2016",
         pros="耐受度高、花期長，景觀接受度高", cons="外來觀賞種；冬季地上部枯萎",
         why="需要「看起來像花園」的場合（社區、校園）首選"),
    dict(zh="水蔥", sp="Schoenoplectus validus", form="emergent", tw="native",
         n_evidence="總氨氮超過 100 mg/L 明顯受抑制", conf="secondary", ref="r_wang2016",
         pros="本土、好種", cons="耐受度明顯比香蒲與美人蕉差",
         why="當對照組用——同一個實驗裡放一個比較不耐的，才看得出處理有沒有效"),
    dict(zh="鳶尾", sp="Iris tectorum", form="emergent", tw="exotic",
         n_evidence="與水蔥同列較不耐的兩種", conf="secondary", ref="r_wang2016",
         pros="觀賞價值高", cons="耐受度差", why="同上，當對照"),
    dict(zh="風車草／莎草屬", sp="Cyperus spp.", form="emergent", tw="native",
         n_evidence="中型試驗中生長優於香蒲，作者歸因於較高的氨耐受度",
         conf="abstract", ref="r_mesocosm2019",
         pros="生長快、台灣常見", cons="只有一篇間接比較，沒有門檻數字",
         why="值得正面測一次氨氮耐受度——這是文獻缺口"),
    dict(zh="空心菜", sp="Ipomoea aquatica", form="emergent", tw="crop",
         n_evidence="浮床試驗氨氮去除 91.8%，但對照（無植物）也有 88.5%，差異不顯著；"
                    "總氮反而比對照低（48.2% vs 62.1%，植株第 19 天後被蟲害腐爛）",
         conf="abstract", ref="r_ipomoea_fb",
         pros="可收成販賣、生長極快、台灣接受度高",
         cons="食用作物碰廢水有衛生與法規問題；那篇的負面結果值得注意",
         why="「有產值」這條路的首選，但一定要自己做無植物對照"),
    dict(zh="水芹菜", sp="Oenanthe javanica", form="emergent", tw="crop",
         n_evidence="沒查到氨氮耐受度的定量資料", conf="secondary", ref="r_tw_forest",
         pros="本土、冬季也能長（補上浮萍冬天停擺的缺口）、市場熟悉",
         cons="資料缺口大", why="台灣冬季低溫時的候選；要自己建立耐受度曲線"),
    dict(zh="茭白筍", sp="Zizania latifolia", form="emergent", tw="crop",
         n_evidence="沒查到氨氮耐受度的定量資料", conf="secondary", ref="r_tw_forest",
         pros="台灣既有的水生經濟作物，栽培體系成熟",
         cons="需要菰黑穗菌感染才形成筍，水質變動可能影響品質",
         why="如果要說服農民，用他已經會種的作物比較容易"),
    dict(zh="香根草", sp="Chrysopogon zizanioides", form="emergent", tw="exotic",
         n_evidence="水耕試驗把銨從 39.52 降到 4.85 mg/L；以未稀釋垃圾滲出水灌溉時，"
                    "存活強烈取決於滲出水組成",
         conf="abstract", ref="r_vetiver_leachate",
         pros="生物量巨大、根深、耐汙染物；不會因種子逸散",
         cons="不是水生植物，要用水耕或浸潤床；耐受度要逐案評估",
         why="垃圾滲出水、高鹽高金屬的場合值得測"),
    dict(zh="微藻（小球藻等）", sp="Chlorella spp.", form="algae", tw="n/a",
         n_evidence="吸收快、可回收生質；光合作用拉高 pH 反而促進氨揮發",
         conf="secondary", ref="r_cai2013",
         pros="速率高、可回收蛋白／油脂", cons="採收困難；pH 上升造成氨揮發與游離氨毒性",
         why="當「上限對照」：如果連藻都不行，問題在水質不在植物"),
]

# ── 實場與中試案例 ───────────────────────────────────────────────
CASES = [
    dict(key="mirzapur", zh="孟加拉 Mirzapur 浮萍塘", year="1993 起", scale="實場",
         what="0.6–0.7 ha 蛇行渠（500 m、7 個彎）處理醫院與社區污水，約 125 m³/d、2,000–3,000 人",
         result="長期運轉資料是浮萍塘最主要的實場參考；搜尋結果沒有給氮去除的數字",
         conf="secondary", ref="r_duckweed_unep"),
    dict(key="swine_pond", zh="全尺度浮萍塘處理豬糞廢水", year="2012", scale="實場",
         what="兩座塘串聯", result="TKN 去除 4.4 g N/m²/d；產 68 t 乾重/ha/年、粗蛋白 35%",
         conf="abstract", ref="r_duckweed_full"),
    dict(key="pig_pilot", zh="豬糞液浮萍中試（歐盟計畫）", year="2025", scale="中試",
         what="以稀釋的液相與硝化／脫硝出水培養", result="氮去除 1.2 g N/m²/d、產 8 t 乾重/ha/年、蛋白 2.8 t/ha/年",
         conf="abstract", ref="r_duckweed_pilot"),
    dict(key="myrio_cw", zh="粉綠狐尾藻三級表面流濕地", year="2017", scale="中試",
         what="單一物種栽種、處理養豬廢水、連續 600 天",
         result="氮負荷 9 kg N/ha/d 下氨氮平均去除 98.3%；植物吸收佔進水總氮 17.9–42.2%",
         conf="abstract", ref="r_myrio_cw"),
    dict(key="nasa_disney", zh="NASA／迪士尼世界布袋蓮系統", year="1970–80 年代", scale="實場原型",
         what="污水廠旁的布袋蓮塘，後來還試過把收割的植體與污泥拿去產甲烷",
         result="搜尋結果給出 69% 總氮、92% 氨氮等數字，但無法確認對應哪一份報告",
         conf="secondary", ref="r_nasa_hyacinth"),
    dict(key="sandiego", zh="美國聖地牙哥 1 MGD 水生植物廠", year="1984", scale="實場",
         what="布袋蓮＋微生物濾床的混合式設計（約 3,785 m³/d）",
         result="搜尋結果沒有給全廠的氮去除數字", conf="secondary", ref="r_nasa_hyacinth"),
    dict(key="tw_xinhai1", zh="新海一期人工濕地（新北大漢溪）", year="2012（101 年度）", scale="實場",
         what="處理水量 6,000 CMD", result="BOD 58%、SS 47%、氨氮 81%",
         conf="secondary", ref="r_tw_epa_wetland"),
    dict(key="tw_xinhai23", zh="新海二期、三期人工濕地", year="2012（101 年度）", scale="實場",
         what="同一群濕地的其他期", result="氨氮去除率各 44%",
         conf="secondary", ref="r_tw_epa_wetland"),
    dict(key="tw_daniaopi", zh="打鳥埤、城林人工濕地", year="2012（101 年度）", scale="實場",
         what="同一群濕地", result="氨氮去除率 97%（打鳥埤）、78%（城林）",
         conf="secondary", ref="r_tw_epa_wetland"),
    dict(key="tw_typhoon", zh="新海二期：颱風前後", year="2007", scale="實場",
         what="柯羅莎颱風前後比較",
         result="颱風前氨氮去除 98.9%，颱風後掉到約 35.1%（地上部被沖走、底泥殘留）",
         conf="secondary", ref="r_tw_thesis"),
    dict(key="tw_lujiaoxi", zh="鹿角溪人工濕地（新北樹林）", year="—", scale="實場",
         what="設計處理 12,000 CMD", result="官方描述的是設計目標「削減 70% 以上」，不是實測值",
         conf="secondary", ref="r_tw_wra"),
    dict(key="tw_float", zh="彰化埤塘浮島（台灣）", year="2021", scale="實場試驗",
         what="人工浮島結合智慧監測",
         result="氨氮 83%、亞硝酸氮 87%、硝酸氮 70%；七月硝化作用使亞硝酸鹽一度衝到 13 mg/L",
         conf="abstract", ref="r_tw_float"),
    dict(key="monsees", zh="解耦式魚菜共生（德國）", year="2017", scale="中試",
         what="耦合式（單迴路）對解耦式（雙迴路）並列比較",
         result="解耦式果實產量高約 36%，魚的產量兩者相當",
         conf="abstract", ref="r_monsees2017"),
    dict(key="digestate_hydro", zh="厭氧消化液硝化後做水耕", year="—", scale="實驗室",
         what="未處理 vs 硝化後的消化液種萵苣",
         result="未處理組被部分硝化產生的亞硝酸毒害而矮化；硝化後與標準養液無顯著差異",
         conf="abstract", ref="r_digestate_nitrif"),
    dict(key="acidophilic", zh="酸性硝化沼液", year="2023", scale="實驗室",
         what="在 pH 約 3 的條件下硝化沼液",
         result="溶出超過 70% 的磷，萵苣鮮重與商用養液相當",
         conf="abstract", ref="r_acidophilic"),
    dict(key="urine", zh="尿液硝化＋蒸餾（VUNA）", year="2011 起", scale="中試／實場",
         what="分離尿液先硝化穩定氮、再蒸餾濃縮",
         result="氮損失低於 3%；另有研究用硝化尿液在 NFT 番茄上取代 100% 的氮而產量不減",
         conf="abstract", ref="r_udert"),
]

# ── 文獻 ─────────────────────────────────────────────────────────
# doi 只填「搜尋結果裡看到原文 DOI 字串」的；其餘用 url。年份與標題要和章節寫的一致。
REFS = {
    "r_wang2016": dict(
        cite="Wang et al. (2016). The inhibition and adaptability of four wetland plant "
             "species to high concentration of ammonia wastewater and nitrogen removal efficiency in "
             "constructed wetlands. *Bioresource Technology*, 202, 198–205.",
        doi="10.1016/j.biortech.2015.11.049",
        note="作者縮寫沒查證，只確認第一作者姓氏"),
    "r_myrio_regnet": dict(
        cite="Wang C, Zhang S, Li W, et al. (2019). Complex regulatory network allows Myriophyllum "
             "aquaticum to thrive under high-concentration ammonia toxicity. *Scientific Reports*, 9, 4801.",
        doi="10.1038/s41598-019-41236-8"),
    "r_myrio_cw": dict(
        cite="Sun H, Liu F, Xu S, et al. (2017). Myriophyllum aquaticum Constructed Wetland Effectively "
             "Removes Nitrogen in Swine Wastewater. *Frontiers in Microbiology*, 8, 1932.",
        doi="10.3389/fmicb.2017.01932"),
    "r_korner2001": dict(
        cite="Körner S, Das SK, Veenstra S, Vermaat JE (2001). The effect of pH variation at the "
             "ammonium/ammonia equilibrium in wastewater and its toxicity to *Lemna gibba*. "
             "*Aquatic Botany*, 71, 71–78.",
        doi="10.1016/S0304-3770(01)00158-9"),
    "r_caicedo2000": dict(
        cite="Caicedo JR, van der Steen NP, Arce O, Gijzen HJ (2000). Effect of total ammonia nitrogen "
             "concentration and pH on growth rates of duckweed (*Spirodela polyrrhiza*). "
             "*Water Research*, 34, 3829–3835.",
        doi="10.1016/S0043-1354(00)00128-7"),
    "r_lemna_high_nh4": dict(
        cite="Wang et al. (2015). Effects of high ammonium level on biomass "
             "accumulation of common duckweed *Lemna minor* L. *Environmental Science and Pollution "
             "Research*.",
        doi="10.1007/s11356-014-3353-2", note="作者與卷頁沒查證"),
    "r_lemna_kinetics": dict(
        cite="Cedergreen N, Madsen TV (2002). Nitrogen uptake by the floating macrophyte *Lemna minor*. "
             "*New Phytologist*.",
        doi="10.1046/j.1469-8137.2002.00463.x"),
    "r_lemna_ph_ctrl": dict(
        cite="Walsh É, Margassery LM, Coughlan NE, et al. (2022). Online Control of *Lemna minor* L. "
             "Phytoremediation: Using pH to Minimize the Nitrogen Outlet Concentration. *Plants*, 11, 1456.",
        doi="10.3390/plants11111456",
        note="作者名單沒核對過（CI 只核對標題與年份）"),
    "r_aber_ph": dict(
        cite="Lowering pH enables duckweed (*Lemna minor* L.) growth on toxic concentrations of "
             "high-nutrient agricultural wastewater（Aberystwyth University 研究紀錄；期刊與年份未查證）",
        url="https://research.aber.ac.uk/en/publications/lowering-ph-enables-duckweed-lemna-minor-l-growth-on-toxic-concen/",
        doi=None),
    "r_abr_lemna": dict(
        cite="Nitrogen and phosphorus removal from anaerobic baffled reactor effluent using *Lemna minor* "
             "and fertiliser value of the biomass for ryegrass production (2025). *Environmental "
             "Monitoring and Assessment*, 197.",
        doi="10.1007/s10661-025-14592-4"),
    "r_duckweed_pilot": dict(
        cite="A Pilot-Scale Evaluation of Duckweed Cultivation for Pig Manure Treatment and Feed "
             "Production (2025). *Plants*, 14, 2680.",
        doi="10.3390/plants14172680"),
    "r_duckweed_full": dict(
        cite="Mohedano RA, Costa RHR, Tavares FA, Belli Filho P (2012). High nutrient removal rate from "
             "swine wastes and protein biomass production by full-scale duckweed ponds. "
             "*Bioresource Technology*, 112, 98–104.",
        doi="10.1016/j.biortech.2012.02.083"),
    "r_lemna_urban": dict(
        cite="Synchronized urban wastewater treatment and biomass production using duckweed "
             "*Lemna gibba* L. (2014). *Ecological Engineering*.",
        url="https://www.sciencedirect.com/science/article/abs/pii/S0925857413005557", doi=None),
    "r_duckweed_unep": dict(
        cite="UNEP IETC。Duckweed-based wastewater treatment（Mirzapur, Bangladesh 案例）。",
        url="http://www.unep.or.jp/ietc/Publications/TechPublications/TechPub-8e/duckweed.asp", doi=None),
    "r_reddy_tucker": dict(
        cite="Reddy KR, Tucker JC (1983). Productivity and nutrient uptake of water hyacinth, "
             "*Eichhornia crassipes* I. Effect of nitrogen source. *Economic Botany*, 37, 237–247.",
        doi="10.1007/BF02858790"),
    "r_lu2010": dict(
        cite="Lu Q, He ZL, Graetz DA, Stoffella PJ, Yang X (2010). Phytoremediation to remove nutrients "
             "and improve eutrophic stormwaters using water lettuce (*Pistia stratiotes* L.). "
             "*Environmental Science and Pollution Research*, 17, 84–96.",
        doi="10.1007/s11356-008-0094-0"),
    "r_ting2018": dict(
        cite="Ting WHT, Tan IAW, Salleh SF, Wahab NA (2018). Application of water hyacinth "
             "(*Eichhornia crassipes*) for phytoremediation of ammoniacal nitrogen: A review. "
             "*Journal of Water Process Engineering*, 22, 239–249.",
        doi="10.1016/j.jwpe.2018.02.011"),
    "r_azolla_golzary": dict(
        cite="Golzary A, et al.。Wastewater Treatment by *Azolla filiculoides*: A Study on Color, Odor, "
             "COD, Nitrate, and Phosphate Removal。",
        url="https://agris.fao.org/search/en/records/663cc858d0c460b11a24fb7b", doi=None),
    "r_azolla_review": dict(
        cite="Role of Azolla in sustainable agriculture and climate resilience: a comprehensive review "
             "(2025). *Frontiers in Plant Science*.",
        url="https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1661720/full",
        doi=None),
    "r_ipomoea_fb": dict(
        cite="Effect of *Ipomoea aquatica* floating-bed on the quantity and distribution of nitrogen "
             "cycling bacteria and nitrogen removal。",
        url="https://pure.ecnu.edu.cn/en/publications/effect-of-ipomoea-aquatica-floating-bed-on-the-quantity-and-distr/",
        doi=None),
    "r_vetiver_leachate": dict(
        cite="Phytoremediatory efficiency of *Chrysopogon zizanioides* in the treatment of landfill "
             "leachate: a case study (2019). *Environmental Science and Pollution Research*.",
        url="https://pubmed.ncbi.nlm.nih.gov/30756356/", doi=None),
    "r_mesocosm2019": dict(
        cite="Microbial removal and plant uptake of nitrogen in constructed wetlands: mesocosm tests on "
             "influencing factors (2019). *Environmental Science and Pollution Research*, 26, 212–222.",
        doi="10.1007/s11356-018-3543-4"),
    "r_vymazal2007": dict(
        cite="Vymazal J (2007). Removal of nutrients in various types of constructed wetlands. "
             "*Science of the Total Environment*, 380, 48–65.",
        doi="10.1016/j.scitotenv.2006.09.014"),
    "r_vymazal_hybrid": dict(
        cite="Vymazal J (2013). The use of hybrid constructed wetlands for wastewater treatment with "
             "special attention to nitrogen removal: A review of a recent development. "
             "*Water Research*, 47, 4795–4811.",
        url="https://www.sciencedirect.com/science/article/pii/S0043135413004375", doi=None),
    "r_brix1997": dict(
        cite="Brix H (1997). Do macrophytes play a role in constructed treatment wetlands? "
             "*Water Science and Technology*, 35(5), 11–17.",
        doi="10.1016/S0273-1223(97)00047-4"),
    "r_ftw_review": dict(
        cite="Application of floating treatment wetlands for stormwater runoff: A critical review of the "
             "recent developments with emphasis on heavy metals and nutrient removal。",
        url="https://www.researchgate.net/publication/349737859", doi=None),
    "r_ftw_lagoon": dict(
        cite="Field Evaluation of a Constructed Floating Wetland for Nutrients and PFAS Attenuation in a "
             "Treatment Lagoon。*ACS ES&T Water*。",
        url="https://pubs.acs.org/aewcaa/article/6/4/2278/5146861/", doi=None),
    "r_headley2012": dict(
        cite="Headley TR, Tanner CC (2012). Constructed wetlands with floating emergent macrophytes: an "
             "innovative stormwater treatment technology. *Critical Reviews in Environmental Science and "
             "Technology*, 42, 2261–2310.",
        doi="10.1080/10643389.2011.574108"),
    "r_tw_epa_wetland": dict(
        cite="行政院環境保護署（現環境部）。淡水河流域 5 處人工濕地（新海、浮洲、打鳥埤、城林、鹿角溪）"
             "101 年度水質淨化成效。環保電子報附件。",
        url="https://enews.moenv.gov.tw/File/18B1FAD90A675052", doi=None),
    "r_tw_wra": dict(
        cite="經濟部水利署。國內案例：新北市樹林區鹿角溪人工濕地自然淨化工程。",
        url="https://www.wra.gov.tw/News_Content.aspx?n=25153&s=88319", doi=None),
    "r_tw_thesis": dict(
        cite="大漢溪畔表面流人工濕地除氮機制相關碩士論文（臺灣博碩士論文知識加值系統）。",
        url="https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi?o=dnclcdr&s=id=%22103NCHU5105069%22.&searchmode=basic",
        doi=None,
        note="颱風前後那組數字與單位面積削減速率那組來自不同論文，沒有核對過是哪一本；"
             "引用前請自己到論文系統查原文"),
    "r_tw_float": dict(
        cite="Evaluation of the Water Quality and Farming Growth Benefits of an Intelligence Aquaponics "
             "System (2021). *Sustainability*, 13, 4210.",
        doi="10.3390/su13084210", note="DOI 由 MDPI 的卷期編號推得，作者名單未核對"),
    "r_tw_forest": dict(
        cite="濕地植物的去污功能與選種（《台灣林業》專文；林業及自然保育署網站）。",
        url="https://www.forest.gov.tw/MagazineFile/5102", doi=None),
    "r_monsees2017": dict(
        cite="Monsees H, Kloas W, Wuertz S (2017). Decoupled systems on trial: Eliminating bottlenecks to "
             "improve aquaponic processes. *PLOS ONE*, 12, e0183056.",
        doi="10.1371/journal.pone.0183056"),
    "r_goddek2016": dict(
        cite="Goddek S, et al. (2016). Navigating towards Decoupled Aquaponic "
             "Systems: A System Dynamics Design Approach. *Water*, 8, 303.",
        doi="10.3390/w8070303"),
    "r_goddek2020": dict(
        cite="Goddek S, et al. (2020). Improving nutrient and water use efficiencies "
             "in multi-loop aquaponics systems. *Aquaculture International*, 28, 2481–2490.",
        doi="10.1007/s10499-020-00600-6", note="卷頁未核對"),
    "r_osu_smallscale": dict(
        cite="Oklahoma State University Extension / SRAC-5007。Principles of Small-Scale Aquaponics。",
        url="https://extension.okstate.edu/fact-sheets/print-publications/srac/principles-of-small-scale-aquaponics-srac-5007.pdf",
        doi=None),
    "r_osu_nutrient": dict(
        cite="Hartleb C。Nutrient Dynamics in Aquaponics（Ohio State University South Centers 簡報）。",
        url="https://southcenters.osu.edu/sites/southc/files/site-library/site-documents/abc2/june2017/Hartleb%20ABC-2%20Nutrients.pdf",
        doi=None),
    "r_ebeling2006": dict(
        cite="Ebeling JM, Timmons MB, Bisogni JJ (2006). Engineering analysis of the stoichiometry of "
             "photoautotrophic, autotrophic, and heterotrophic removal of ammonia–nitrogen in aquaculture "
             "systems. *Aquaculture*, 257, 346–358.",
        url="https://ag.arizona.edu/azaqua/ista/ISTA7/RecircWorkshop/", doi=None),
    "r_uvi": dict(
        cite="Rakocy JE, Bailey DS, Shultz RC, Danaher JJ。A Commercial-Scale Aquaponic System Developed "
             "at the University of the Virgin Islands。",
        url="https://tag2grow.org/wp-content/uploads/2021/09/UVI-Aquaponics.pdf", doi=None),
    "r_digestate_nitrif": dict(
        cite="The applicability of anaerobically treated domestic wastewater as a nutrient medium in "
             "hydroponic lettuce cultivation: Nitrogen toxicity and health risk assessment。"
             "*Science of the Total Environment*。",
        url="https://www.sciencedirect.com/science/article/abs/pii/S0048969721015503", doi=None),
    "r_acidophilic": dict(
        cite="Acidophilic nitrification of biogas digestates accelerates sustainable hydroponics by "
             "enhancing phosphorus dissolution (2023). *Environmental Technology & Innovation*。",
        url="https://www.sciencedirect.com/science/article/abs/pii/S2589014X23000622", doi=None),
    "r_tomato_digestate": dict(
        cite="Organic Waste-Based Fertilizer in Hydroponics Increases Tomato Fruit Size but Reduces Fruit "
             "Quality。*Frontiers in Plant Science*。",
        url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8261069/", doi=None),
    "r_udert": dict(
        cite="Udert KM, Wächter M (2012). Complete nutrient recovery from source-separated urine by "
             "nitrification and distillation. *Water Research*, 46, 453–464.",
        url="https://www.eawag.ch/fileadmin/Domain1/Abteilungen/eng/projekte/vuna/doc/VUNA_Handbook_Urine_Treatment.pdf",
        doi=None),
    "r_oecd221": dict(
        cite="OECD (2006). Test No. 221: *Lemna* sp. Growth Inhibition Test. OECD Guidelines for the "
             "Testing of Chemicals, Section 2.",
        url="https://www.oecd.org/en/publications/test-no-221-lemna-sp-growth-inhabition-test_9789264016194-en.html",
        doi=None),
    "r_efsa_wolffia": dict(
        cite="EFSA NDA Panel (2021). Safety of *Wolffia globosa* powder as a Novel food pursuant to "
             "Regulation (EU) 2015/2283。",
        url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8693246/", doi=None),
    "r_bmp_wh": dict(
        cite="Biochemical methane potential test of untreated and hot air oven pretreated water hyacinth: "
             "A comparative study。*Journal of Cleaner Production*。",
        url="https://www.sciencedirect.com/science/article/abs/pii/S0959652617316876", doi=None),
    "r_duckweed_starch": dict(
        cite="High starch duckweed biomass production and its highly-efficient conversion to bioethanol "
             "(2023). *Environmental Technology & Innovation*。",
        url="https://ui.adsabs.harvard.edu/abs/2023EnvTI..3203296G", doi=None),
    "r_cwmfc": dict(
        cite="Constructed wetland–microbial fuel cell 系統回顧（RSC Advances, 2024）。",
        url="https://pubs.rsc.org/en/content/articlepdf/2024/ra/d4ra04658g", doi=None),
    "r_cai2013": dict(
        cite="Cai T, Park SY, Li Y (2013). Nutrient recovery from wastewater streams by microalgae: "
             "Status and prospects. *Renewable and Sustainable Energy Reviews*, 19, 360–369.",
        doi="10.1016/j.rser.2012.11.030"),
    "r_pellegrini2018": dict(
        cite="Pellegrini MOO, Horn CN, Almeida RF (2018). Total evidence phylogeny of Pontederiaceae "
             "(Commelinales) sheds light on the necessity of its recircumscription and synopsis of "
             "*Pontederia* L. *PhytoKeys*, 108, 25–83.",
        doi="10.3897/phytokeys.108.27652"),
    "r_moa_alien": dict(
        cite="農業部。外來種介紹：大萍（水芙蓉）、布袋蓮。",
        url="https://www.moa.gov.tw/ws.php?id=2613", doi=None),
    "r_tw_effluent": dict(
        cite="放流水標準（中華民國 108 年 4 月 29 日修正）。氨氮限值適用於排放於自來水水質水量保護區內者。",
        url="https://www.epb.taichung.gov.tw/media/521086/放流水標準.pdf", doi=None),
    "r_tw_digestate": dict(
        cite="水污染防治措施及檢測申報管理辦法第 70 條之 1（沼渣沼液農地肥分使用）。",
        url="https://kmweb.moa.gov.tw/subject/subject.php?id=16984", doi=None),
    "r_nasa_hyacinth": dict(
        cite="NASA Technical Reports Server。Sewage treatment with water hyacinths（1970–80 年代技術移轉紀錄）。",
        url="https://ntrs.nasa.gov/api/citations/20020091873/downloads/20020091873.pdf", doi=None),
    "r_wur_manure": dict(
        cite="Timmerman M, Hoving IE。Purifying manure effluents with duckweed（Wageningen 報告）。",
        url="https://edepot.wur.nl/374052", doi=None),
    "r_life_lemna": dict(
        cite="LIFE LEMNA 計畫（以浮萍處理豬糞沼液的歐盟示範計畫）。",
        url="https://www.life-lemna.eu/the-project/description/", doi=None),
}


def build() -> dict:
    used = {s["ref"] for s in SPECIES} | {c["ref"] for c in CASES}
    missing = sorted(used - set(REFS))
    assert not missing, f"這些 ref key 沒有對應的文獻：{missing}"
    return dict(species=SPECIES, cases=CASES, refs=REFS,
                counts=dict(species=len(SPECIES), cases=len(CASES), refs=len(REFS),
                            with_doi=sum(1 for r in REFS.values() if r.get("doi"))))


if __name__ == "__main__":
    d = build()
    (OUT / "literature.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    print(d["counts"])
    for s in SPECIES:
        print(f'{s["zh"]:<12} {s["form"]:<10} {s["tw"]:<9} [{s["conf"]}]')
