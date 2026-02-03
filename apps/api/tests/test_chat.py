from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


client = TestClient(app)


def test_chat_response_shape():
    settings.llm_disabled = True

    load_response = client.post(
        "/api/datasets/uci",
        json={"dataset_id": "iris", "session_id": "test-session"},
    )
    assert load_response.status_code == 200

    response = client.post(
        "/api/chat",
        json={"session_id": "test-session", "message": "Plot sepal length"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["session_id"] == "test-session"
    assert payload["assistant_message"]
    assert payload["plot_json"]
    assert payload["title"]
    assert payload["summary"]
    assert payload["code"]
