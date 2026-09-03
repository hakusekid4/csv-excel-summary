"""集計のロジック。画面(Streamlit)や CLI から呼ばれる、pandas だけで動く部分。

画面と分けておくと、テストが書きやすく、CLI からも同じ結果が得られる。
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import pandas as pd

# 集計方法の表示名 → pandas の関数名
AGG_FUNCS: dict[str, str] = {"合計": "sum", "平均": "mean", "件数": "count"}
# 期間単位の表示名 → pandas の頻度記号
PERIOD_FREQS: dict[str, str] = {"月": "ME", "週": "W", "日": "D"}


@dataclass
class ColumnInfo:
    """列の種類ごとの列名リスト。"""

    numeric: list[str] = field(default_factory=list)  # 数値列(金額、数量など)
    category: list[str] = field(default_factory=list)  # 文字列列(店舗、商品など)
    date: list[str] = field(default_factory=list)  # 日付として解釈できる列


def _looks_like_date(series: pd.Series, threshold: float = 0.8) -> bool:
    """列の値の 8 割以上が日付として解釈できれば True。"""
    sample = series.dropna().astype(str).head(200)
    if sample.empty:
        return False
    with warnings.catch_warnings():
        # 日付でない列を試すときに出る「形式を推定できない」警告は不要なので黙らせる
        warnings.simplefilter("ignore")
        parsed = pd.to_datetime(sample, errors="coerce")
    return parsed.notna().mean() >= threshold


def detect_columns(df: pd.DataFrame) -> ColumnInfo:
    """各列を「数値」「文字列」「日付」に自動で振り分ける。"""
    info = ColumnInfo()
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            info.date.append(col)
        elif pd.api.types.is_numeric_dtype(s):
            info.numeric.append(col)
        elif _looks_like_date(s):
            info.date.append(col)
        else:
            info.category.append(col)
    return info


def summarize_by_category(
    df: pd.DataFrame, group_col: str, value_col: str, agg: str = "合計", top_n: int | None = None
) -> pd.DataFrame:
    """項目(店舗・商品など)ごとに値を集計し、大きい順に並べて構成比をつける。

    引数:
        group_col: まとめる列(例: 店舗)
        value_col: 集計する数値列(例: 金額)
        agg: "合計" / "平均" / "件数"
        top_n: 上位 n 件だけ返す(None なら全部)
    戻り値:
        列 = [group_col, agg, "構成比(%)"] の DataFrame
    """
    if agg not in AGG_FUNCS:
        raise ValueError(f"集計方法は {list(AGG_FUNCS)} から選んでください: {agg}")
    values = pd.to_numeric(df[value_col], errors="coerce")
    work = pd.DataFrame({group_col: df[group_col].fillna("(未入力)").astype(str), value_col: values})
    result = work.groupby(group_col, sort=False)[value_col].agg(AGG_FUNCS[agg]).reset_index()
    result = result.rename(columns={value_col: agg}).sort_values(agg, ascending=False)
    total = result[agg].sum()
    result["構成比(%)"] = (result[agg] / total * 100).round(1) if total else 0.0
    if top_n is not None:
        result = result.head(top_n)
    return result.reset_index(drop=True)


def summarize_by_period(
    df: pd.DataFrame, date_col: str, value_col: str, agg: str = "合計", period: str = "月"
) -> pd.DataFrame:
    """日付列をもとに月・週・日ごとの推移を出し、前期比(%)をつける。

    戻り値:
        列 = ["期間", agg, "前期比(%)"] の DataFrame(期間順)
    """
    if period not in PERIOD_FREQS:
        raise ValueError(f"期間単位は {list(PERIOD_FREQS)} から選んでください: {period}")
    dates = pd.to_datetime(df[date_col], errors="coerce")
    values = pd.to_numeric(df[value_col], errors="coerce")
    work = pd.DataFrame({"date": dates, "value": values}).dropna(subset=["date"])
    grouped = work.set_index("date")["value"].resample(PERIOD_FREQS[period]).agg(AGG_FUNCS[agg])
    fmt = {"月": "%Y-%m", "週": "%Y-%m-%d", "日": "%Y-%m-%d"}[period]
    result = pd.DataFrame({"期間": grouped.index.strftime(fmt), agg: grouped.to_numpy()})
    prev = result[agg].shift(1)
    result["前期比(%)"] = ((result[agg] - prev) / prev * 100).round(1)
    return result.reset_index(drop=True)


def basic_stats(df: pd.DataFrame, value_col: str) -> dict[str, float]:
    """件数・合計・平均・最大・最小をまとめて返す(画面の上部に表示する用)。"""
    values = pd.to_numeric(df[value_col], errors="coerce").dropna()
    if values.empty:
        return {"件数": 0, "合計": 0.0, "平均": 0.0, "最大": 0.0, "最小": 0.0}
    return {
        "件数": int(values.count()),
        "合計": float(values.sum()),
        "平均": float(values.mean()),
        "最大": float(values.max()),
        "最小": float(values.min()),
    }
