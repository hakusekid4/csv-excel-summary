"""テスト共通のダミーデータ。"""

import pandas as pd
import pytest


@pytest.fixture
def sales_df() -> pd.DataFrame:
    """店舗 2 つ × 3 か月の小さな売上データ。"""
    return pd.DataFrame(
        {
            "日付": ["2025-01-10", "2025-01-20", "2025-02-05", "2025-03-01", "2025-03-15"],
            "店舗": ["A店", "B店", "A店", "A店", "B店"],
            "金額": [100, 200, 300, 50, 150],
        }
    )
