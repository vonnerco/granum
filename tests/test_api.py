import os
from pathlib import Path

from fastapi.testclient import TestClient

from src.config import Settings
from src.main import create_app


class MockLLMClient:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def enhance(self, raw_text: str):
        if self.should_fail:
            raise RuntimeError('Mocked LLM failure')

        return type(
            'LLMResult',
            (),
            {
                'enhanced_text': f'Work completed:\n- {raw_text}\n\nOutcome/Follow-up:\n- Follow-up scheduled.',
                'model_used': 'mock-gemini',
                'prompt_tokens': 20,
                'completion_tokens': 15,
            },
        )()


def _settings_for(db_path: Path) -> Settings:
    return Settings(
        database_url=f'sqlite+aiosqlite:///{db_path.as_posix()}',
        google_generative_ai_api_key='test-key',
        llm_model='mock-model',
    )


def test_enhance_success_and_history_logging(tmp_path: Path):
    db_file = tmp_path / 'api_success.db'
    app = create_app(settings=_settings_for(db_file), llm_client=MockLLMClient())

    with TestClient(app) as client:
        response = client.post('/enhance', json={'text': 'completed mowing and edging'})
        assert response.status_code == 200
        body = response.json()
        assert body['model_used'] == 'mock-gemini'
        assert body['token_usage']['prompt_tokens'] == 20
        assert body['token_usage']['completion_tokens'] == 15
        assert body['latency_ms'] >= 0

        history = client.get('/history?page=1&page_size=10')
        assert history.status_code == 200
        history_body = history.json()
        assert history_body['total'] == 1
        assert history_body['items'][0]['status'] == 'success'


def test_enhance_failure_is_logged(tmp_path: Path):
    db_file = tmp_path / 'api_failure.db'
    app = create_app(settings=_settings_for(db_file), llm_client=MockLLMClient(should_fail=True))

    with TestClient(app) as client:
        response = client.post('/enhance', json={'text': 'customer requested revisit'})
        assert response.status_code == 502
        assert 'Failed to enhance text' in response.json()['detail']

        history = client.get('/history?page=1&page_size=10')
        assert history.status_code == 200
        item = history.json()['items'][0]
        assert item['status'] == 'failure'
        assert 'Mocked LLM failure' in item['error_message']


def test_validation_error_rejected_before_llm_and_logged(tmp_path: Path):
    db_file = tmp_path / 'api_validation.db'
    app = create_app(settings=_settings_for(db_file), llm_client=MockLLMClient())

    with TestClient(app) as client:
        response = client.post('/enhance', json={})
        assert response.status_code == 422
        detail = response.json()['detail']
        assert detail == 'Invalid request payload.'

        history = client.get('/history?page=1&page_size=10')
        assert history.status_code == 200
        item = history.json()['items'][0]
        assert item['model_used'] == 'validation'
        assert item['status'] == 'failure'


def test_history_pagination(tmp_path: Path):
    db_file = tmp_path / 'api_pagination.db'
    app = create_app(settings=_settings_for(db_file), llm_client=MockLLMClient())

    with TestClient(app) as client:
        for idx in range(3):
            res = client.post('/enhance', json={'text': f'note {idx}'})
            assert res.status_code == 200

        page1 = client.get('/history?page=1&page_size=2').json()
        page2 = client.get('/history?page=2&page_size=2').json()

        assert page1['total'] == 3
        assert len(page1['items']) == 2
        assert len(page2['items']) == 1
