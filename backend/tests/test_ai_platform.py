import pytest
from app.services.llm_registry import llm_registry
from app.services.prompt_service import prompt_service


def test_llm_registry_providers():
    """Tests LLM registry provider registration and listing."""
    providers = llm_registry.list_providers()
    assert len(providers) >= 3
    names = [p["name"] for p in providers]
    assert "gemini" in names
    assert "openai" in names
    assert "claude" in names


def test_prompt_service_rendering():
    """Tests prompt service rendering with template variables."""
    rendered = prompt_service.render_prompt(
        template_name="default_pr_review",
        variables={"repository": "Tejas190605/codexproj", "pr_number": 42, "pr_title": "Fix Auth Bug", "diff": "+ print('fix')"}
    )
    assert "Tejas190605/codexproj" in rendered["user_prompt"]
    assert "#42" in rendered["user_prompt"]
    assert "system_prompt" in rendered


def test_ai_providers_api_endpoint(client):
    """Tests GET /api/ai/providers."""
    res = client.get("/api/ai/providers")
    assert res.status_code == 200
    json_resp = res.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) >= 3


def test_ai_prompts_api_endpoint(client):
    """Tests GET /api/ai/prompts."""
    res = client.get("/api/ai/prompts")
    assert res.status_code == 200
    json_resp = res.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) >= 1
    assert json_resp[0]["name"] == "default_pr_review"


def test_ai_model_settings_api_endpoints(client):
    """Tests GET and PUT /api/ai/settings/{owner}/{repo}."""
    # GET default
    get_res = client.get("/api/ai/settings/Tejas190605/codexproj")
    assert get_res.status_code == 200
    assert get_res.json()["owner_repo"] == "Tejas190605/codexproj"

    # PUT update
    put_res = client.put(
        "/api/ai/settings/Tejas190605/codexproj",
        json={
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": "0.1",
            "max_tokens": 8192,
            "review_depth": "deep"
        }
    )
    assert put_res.status_code == 200
    assert put_res.json()["provider"] == "openai"
    assert put_res.json()["model"] == "gpt-4o"


def test_ai_usage_and_evaluations_api_endpoints(client):
    """Tests GET /api/ai/usage and /api/ai/evaluations API endpoints."""
    usage_res = client.get("/api/ai/usage")
    assert usage_res.status_code == 200
    assert "summary" in usage_res.json()

    eval_res = client.get("/api/ai/evaluations")
    assert eval_res.status_code == 200
    assert isinstance(eval_res.json(), list)

    trigger_res = client.post(
        "/api/ai/evaluations/run",
        json={"run_name": "Regression Test Run", "provider": "gemini", "model": "gemini-2.5-flash"}
    )
    assert trigger_res.status_code == 200
    assert trigger_res.json()["run_name"] == "Regression Test Run"
