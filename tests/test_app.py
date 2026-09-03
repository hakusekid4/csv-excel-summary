"""Streamlit 画面のテスト。ブラウザを使わずに画面を実行して、エラーなく表示されることを確認する。"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app" / "app.py"


def test_app_runs_with_sample_data() -> None:
    at = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert not at.exception, at.exception
    # サンプルデータが読み込まれ、概要の数値と 3 つのタブが出ている
    assert any("sample_sales.csv" in h.value for h in at.subheader)
    assert len(at.metric) == 4
    assert len(at.tabs) == 3
    assert at.sidebar.selectbox[0].value == "店舗"  # まとめる列の初期値


def test_app_changes_group_and_period() -> None:
    at = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    at.sidebar.selectbox[0].set_value("商品名").run()
    at.sidebar.radio[0].set_value("件数").run()
    assert not at.exception, at.exception
    assert at.sidebar.selectbox[0].value == "商品名"
