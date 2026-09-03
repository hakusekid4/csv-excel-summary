"""動作確認用のダミー売上データを data/ に作る(CSV と Excel の両方)。

実データは使わず、乱数で作る。seed を固定しているので毎回同じ内容になる。
使い方: python scripts/make_sample.py
"""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

STORES = ["渋谷店", "新宿店", "池袋店", "横浜店", "大宮店"]
PRODUCTS = {
    "ドリンク": [("コーヒー", 450), ("紅茶", 400), ("ジュース", 350)],
    "フード": [("サンドイッチ", 600), ("パスタ", 950), ("カレー", 900)],
    "デザート": [("ケーキ", 550), ("プリン", 380)],
}


def make_sample(rows: int = 600, seed: int = 42) -> pd.DataFrame:
    """rows 行の売上データを作る。列: 日付, 店舗, 商品カテゴリ, 商品名, 数量, 単価, 金額"""
    rng = random.Random(seed)
    days = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    records = []
    for _ in range(rows):
        category = rng.choice(list(PRODUCTS))
        name, price = rng.choice(PRODUCTS[category])
        qty = rng.randint(1, 5)
        records.append(
            {
                "日付": rng.choice(days).strftime("%Y-%m-%d"),
                "店舗": rng.choice(STORES),
                "商品カテゴリ": category,
                "商品名": name,
                "数量": qty,
                "単価": price,
                "金額": qty * price,
            }
        )
    return pd.DataFrame(records).sort_values("日付").reset_index(drop=True)


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    df = make_sample()
    df.to_csv(out_dir / "sample_sales.csv", index=False, encoding="utf-8-sig")
    df.to_excel(out_dir / "sample_sales.xlsx", index=False, sheet_name="売上")
    print(f"作成しました: {out_dir / 'sample_sales.csv'} / sample_sales.xlsx ({len(df)} 行)")
