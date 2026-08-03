def test_root_endpoint(client):
    """Tests that root endpoint GET / returns 200 OK and expected greeting."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "CodeSage AI is running 🚀"}


def test_health_endpoint(client, mocker):
    """Tests that GET /health returns 200 OK and does not invoke external services."""
    mock_requests = mocker.patch("requests.get")
    mock_genai = mocker.patch("google.genai.Client")

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "codesage-ai"}

    # Verify no external API calls were made
    mock_requests.assert_not_called()
    mock_genai.assert_not_called()
