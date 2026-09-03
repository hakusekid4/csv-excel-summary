"""コマンドラインから集計を実行する入口。画面を使わずに 1 コマンドで Excel を出せる。

使い方の例:
    python -m src.main data/sample_sales.csv --group 店舗 --value 金額 --date 日付 --out 集計結果.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.analyzer import AGG_FUNCS, PERIOD_FREQS, summarize_by_category, summarize_by_period
from src.exporter import to_excel_bytes
from src.loader import LoadError, load_table


def build_parser() -> argparse.ArgumentParser:
    """コマンドライン引数の定義。"""
    p = argparse.ArgumentParser(description="CSV / Excel を項目別・期間別に集計して Excel に出力する")
    p.add_argument("file", help="入力ファイル(.csv / .xlsx)")
    p.add_argument("--group", required=True, help="まとめる列(例: 店舗)")
    p.add_argument("--value", required=True, help="集計する数値列(例: 金額)")
    p.add_argument("--date", help="日付列(指定すると期間別の推移も出す)")
    p.add_argument("--agg", default="合計", choices=list(AGG_FUNCS), help="集計方法")
    p.add_argument("--period", default="月", choices=list(PERIOD_FREQS), help="推移の単位")
    p.add_argument("--sheet", default=0, help="Excel のシート名(省略時は先頭)")
    p.add_argument("--out", default="summary.xlsx", help="出力する Excel のパス")
    return p


def run(argv: list[str] | None = None) -> Path:
    """引数を受け取って集計し、Excel を書き出す。戻り値は出力ファイルのパス。"""
    args = build_parser().parse_args(argv)
    df = load_table(args.file, sheet=args.sheet)
    for col in [args.group, args.value] + ([args.date] if args.date else []):
        if col not in df.columns:
            raise LoadError(f"列「{col}」がありません。ある列: {list(df.columns)}")

    sheets = {"項目別集計": summarize_by_category(df, args.group, args.value, args.agg)}
    if args.date:
        sheets["期間別推移"] = summarize_by_period(df, args.date, args.value, args.agg, args.period)
    sheets["元データ"] = df

    out = Path(args.out)
    out.write_bytes(to_excel_bytes(sheets))
    return out


if __name__ == "__main__":
    try:
        path = run()
        print(f"出力しました: {path}")
    except LoadError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
