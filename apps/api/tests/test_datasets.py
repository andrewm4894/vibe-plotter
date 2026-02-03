from app.datasets import load_uci_dataset, preview_dataframe


def test_load_uci_dataset():
    df = load_uci_dataset("iris")
    preview = preview_dataframe(df)
    assert preview["row_count"] > 0
    assert "sepal_length" in preview["columns"]
