"""第 9 章用的模型價格表與「四階梯」成本估算。

價格是 2026-10 的 Anthropic 第一方 API 牌價（美元／每百萬 token）。這是會變的數字，
所以集中放在這裡，章節與圖都讀 models.json，要更新只改這一個檔案。

執行：python models.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
AS_OF = "2026-10"

# (顯示名稱, model id, 輸入 $/MTok, 輸出 $/MTok, 定位)
MODELS = [
    ("Haiku 5.5", "claude-haiku-5-5", 0.10, 0.50, "最便宜最快，適合分類、擷取這種簡單又大量的工作"),
    ("Sonnet 5.5", "claude-sonnet-5-5", 2.00, 10.00, "日常寫程式與代理工作的主力"),
    ("Opus 5.5", "claude-opus-5-5", 4.00, 20.00, "最強的日常款，難題與長流程用這個"),
    ("Fable 5.1", "claude-fable-5-1", 10.00, 50.00, "最吃力的推理與長時間自主工作"),
]

# 四階梯：讓模型「懂你的領域」的四種做法
LADDER = [
    {"step": "① 把資料放進提示裡", "en": "prompting / context",
     "data": "幾頁到幾十頁", "cost": "幾乎免費（只有 token 費）",
     "time": "幾分鐘", "keeps_up": "改資料＝改檔案，立刻生效",
     "use": "資料量小、常變動、你只有幾份文件"},
    {"step": "② 外掛檢索（RAG）", "en": "retrieval-augmented generation",
     "data": "幾百到幾十萬頁", "cost": "低（向量資料庫＋每次查詢的 token）",
     "time": "幾天", "keeps_up": "資料更新只要重建索引",
     "use": "**研究者 90% 的情況**：文獻庫、實驗紀錄、SOP"},
    {"step": "③ 微調（fine-tune）", "en": "fine-tuning",
     "data": "數千筆高品質問答對", "cost": "中（訓練＋之後每次推論都比較貴）",
     "time": "數週（大半花在整理資料）", "keeps_up": "資料更新要重新訓練",
     "use": "要固定的輸出格式或語氣，或領域詞彙太偏"},
    {"step": "④ 從頭訓練", "en": "pre-training",
     "data": "數十億到數兆 token", "cost": "數百萬美元起跳",
     "time": "數月～數年", "keeps_up": "要重來",
     "use": "幾乎不適用於單一實驗室"},
]


def main():
    rows = [{"name": n, "id": i, "in_usd_per_mtok": a, "out_usd_per_mtok": b, "note": c}
            for n, i, a, b, c in MODELS]
    # 一個具體例子：把一份 50 頁的論文（約 40,000 token）丟進去問 20 次要多少錢
    doc_tokens, n_questions, answer_tokens = 40_000, 20, 800
    for r in rows:
        no_cache = (doc_tokens * n_questions * r["in_usd_per_mtok"]
                    + answer_tokens * n_questions * r["out_usd_per_mtok"]) / 1e6
        # 快取讀取約為輸入價的 1/10（第一次寫入約 1.25 倍）
        cached = (doc_tokens * 1.25 * r["in_usd_per_mtok"]
                  + doc_tokens * (n_questions - 1) * r["in_usd_per_mtok"] * 0.1
                  + answer_tokens * n_questions * r["out_usd_per_mtok"]) / 1e6
        r["example_no_cache_usd"] = round(no_cache, 3)
        r["example_cached_usd"] = round(cached, 3)
        r["cache_saving_pct"] = round((1 - cached / no_cache) * 100, 1)

    out = {"as_of": AS_OF, "models": rows, "ladder": LADDER,
           "example": {"doc_tokens": doc_tokens, "questions": n_questions,
                       "answer_tokens": answer_tokens}}
    (HERE / "models.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    print(f"價格表（{AS_OF}，美元／每百萬 token）")
    print(f'{"模型":14s}{"輸入":>8s}{"輸出":>8s}   範例：{doc_tokens:,} token 的文件問 {n_questions} 次')
    for r in rows:
        print(f'{r["name"]:14s}{r["in_usd_per_mtok"]:8.2f}{r["out_usd_per_mtok"]:8.2f}   '
              f'不快取 ${r["example_no_cache_usd"]:.2f}　快取 ${r["example_cached_usd"]:.2f}　'
              f'省 {r["cache_saving_pct"]:.0f}%')
    print("\n寫入 models.json")


if __name__ == "__main__":
    main()
