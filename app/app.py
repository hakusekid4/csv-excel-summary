"""Streamlit の画面。ファイルをアップロード → 列を選ぶ → 集計表とグラフ → Excel ダウンロード。

起動: streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# app/ から src/ を import できるようにプロジェクトのルートをパスに足す
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.analyzer import (
    AGG_FUNCS,
    PERIOD_FREQS,
    basic_stats,
    detect_columns,
    summarize_by_category,
    summarize_by_period,
)
from src.charts import bar_chart, line_chart
from src.exporter import to_excel_bytes
from src.loader import LoadError, detect_kind, list_sheets, load_table

SAMPLE_PATH = ROOT / "data" / "sample_sales.csv"

st.set_page_config(page_title="CSV/Excel 集計ツール", page_icon="📊", layout="wide")
st.title("📊 CSV/Excel 集計ツール")
st.caption("ファイルを入れて列を選ぶだけで、項目別の集計・期間別の推移・グラフ・Excel 出力ができます。")


# ---------- 1. ファイルの読み込み ----------
def load_from_sidebar():
    """サイドバーでファイルを受け取り、DataFrame とファイル名を返す。未選択なら (None, None)。"""
    st.sidebar.header("1. ファイルを選ぶ")
    uploaded = st.sidebar.file_uploader("CSV または Excel", type=["csv", "txt", "tsv", "xlsx", "xlsm", "xls"])
    use_sample = st.sidebar.checkbox("サンプルデータで試す", value=uploaded is None)

    if uploaded is not None:
        try:
            sheet: str | int = 0
            if detect_kind(uploaded.name) == "excel":
                sheets = list_sheets(uploaded)
                if len(sheets) > 1:
                    sheet = st.sidebar.selectbox("シート", sheets)
            return load_table(uploaded, filename=uploaded.name, sheet=sheet), uploaded.name
        except LoadError as e:
            st.error(str(e))
            return None, None
    if use_sample and SAMPLE_PATH.exists():
        return load_table(SAMPLE_PATH), SAMPLE_PATH.name
    return None, None


df, filename = load_from_sidebar()
if df is None:
    st.info("左のサイドバーからファイルを選ぶか、「サンプルデータで試す」にチェックを入れてください。")
    st.stop()

cols = detect_columns(df)
if not cols.numeric:
    st.error("数値の列が見つかりませんでした。金額や数量などの数値列があるファイルを選んでください。")
    st.stop()

# ---------- 2. 集計の設定 ----------
st.sidebar.header("2. 集計の設定")
group_choices = cols.category + cols.date  # 日付列でまとめることもできる
group_col = st.sidebar.selectbox("まとめる列(店舗・商品など)", group_choices or list(df.columns))
value_col = st.sidebar.selectbox("集計する数値列(金額など)", cols.numeric, index=len(cols.numeric) - 1)
agg = st.sidebar.radio("集計方法", list(AGG_FUNCS), horizontal=True)
date_col = st.sidebar.selectbox("日付列(推移を見る場合)", ["(使わない)"] + cols.date)
period = st.sidebar.radio("推移の単位", list(PERIOD_FREQS), horizontal=True)
top_n = st.sidebar.slider("グラフに出す上位件数", 5, 50, 15)

# ---------- 3. 概要 ----------
stats = basic_stats(df, value_col)
st.subheader(f"概要: {filename}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("行数", f"{len(df):,}")
m2.metric(f"{value_col} の合計", f"{stats['合計']:,.0f}")
m3.metric(f"{value_col} の平均", f"{stats['平均']:,.1f}")
m4.metric(f"{value_col} の最大", f"{stats['最大']:,.0f}")

# ---------- 4. 集計結果 ----------
by_cat = summarize_by_category(df, group_col, value_col, agg)
trend = None
if date_col != "(使わない)":
    trend = summarize_by_period(df, date_col, value_col, agg, period)

tab1, tab2, tab3 = st.tabs(["項目別", "推移", "元データ"])
with tab1:
    left, right = st.columns([1, 1.4])
    left.dataframe(by_cat, width="stretch", hide_index=True)
    right.altair_chart(
        bar_chart(by_cat.head(top_n), group_col, agg, f"{group_col}別 {value_col}の{agg}(上位 {top_n} 件)"),
        width="stretch",
    )
with tab2:
    if trend is None:
        st.info("サイドバーで日付列を選ぶと、月・週・日ごとの推移が表示されます。")
    else:
        left, right = st.columns([1, 1.4])
        left.dataframe(trend, width="stretch", hide_index=True)
        right.altair_chart(
            line_chart(trend, "期間", agg, f"{period}ごとの {value_col}の{agg}"), width="stretch"
        )
with tab3:
    st.write(f"{len(df):,} 行 × {len(df.columns)} 列")
    st.dataframe(df, width="stretch", hide_index=True)

# ---------- 5. Excel ダウンロード ----------
st.sidebar.header("3. 結果を保存")
sheets = {"項目別集計": by_cat}
if trend is not None:
    sheets["期間別推移"] = trend
sheets["元データ"] = df
st.sidebar.download_button(
    "Excel でダウンロード",
    data=to_excel_bytes(sheets),
    file_name=f"集計_{Path(filename).stem}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    width="stretch",
)
