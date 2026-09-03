"""analyzer.py のテスト: 列の判定、項目別集計、期間別推移。"""

import pandas as pd
import pytest

from src.analyzer import basic_stats, detect_columns, summarize_by_category, summarize_by_period


def test_detect_columns(sales_df) -> None:
    info = detect_columns(sales_df)
    assert info.date == ["日付"]
    assert info.category == ["店舗"]
    assert info.numeric == ["金額"]


def test_summarize_by_category_sum(sales_df) -> None:
    result = summarize_by_category(sales_df, "店舗", "金額")
    assert list(result.columns) == ["店舗", "合計", "構成比(%)"]
    assert result.iloc[0]["店舗"] == "A店"  # 450 > 350 なので A 店が先
    assert result.iloc[0]["合計"] == 450
    assert result["構成比(%)"].sum() == pytest.approx(100.0, abs=0.2)


def test_summarize_by_category_count_and_top_n(sales_df) -> None:
    result = summarize_by_category(sales_df, "店舗", "金額", agg="件数", top_n=1)
    assert len(result) == 1
    assert result.iloc[0]["件数"] == 3


def test_summarize_by_category_handles_missing_and_text(sales_df) -> None:
    df = sales_df.copy()
    df.loc[0, "店舗"] = None
    df["金額"] = df["金額"].astype(str)  # 文字列で入っていても数値に直す
    result = summarize_by_category(df, "店舗", "金額")
    assert "(未入力)" in set(result["店舗"])


def test_invalid_agg(sales_df) -> None:
    with pytest.raises(ValueError):
        summarize_by_category(sales_df, "店舗", "金額", agg="中央値")


def test_summarize_by_period_month(sales_df) -> None:
    result = summarize_by_period(sales_df, "日付", "金額")
    assert list(result["期間"]) == ["2025-01", "2025-02", "2025-03"]
    assert list(result["合計"]) == [300, 300, 200]
    assert pd.isna(result.iloc[0]["前期比(%)"])
    assert result.iloc[2]["前期比(%)"] == pytest.approx(-33.3)


def test_summarize_by_period_fills_empty_month() -> None:
    df = pd.DataFrame({"日付": ["2025-01-01", "2025-03-01"], "金額": [1, 2]})
    result = summarize_by_period(df, "日付", "金額")
    assert list(result["期間"]) == ["2025-01", "2025-02", "2025-03"]
    assert result.iloc[1]["合計"] == 0


def test_basic_stats(sales_df) -> None:
    s = basic_stats(sales_df, "金額")
    assert s["件数"] == 5
    assert s["合計"] == 800
    assert s["最大"] == 300
