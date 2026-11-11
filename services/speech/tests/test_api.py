from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import main

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'WORK_DIR', tmp_path / 'work')
    monkeypatch.setattr(main, 'UPLOAD_DIR', tmp_path / 'uploads')
    monkeypatch.setattr(main, 'RESULT_DIR', tmp_path / 'results')
    main.jobs.clear()
    return TestClient(main.app, raise_server_exceptions=False)

@pytest.mark.parametrize('fail', [False, True])
def test_request_cleanup(client, monkeypatch, tmp_path, fail):
    workspaces = []
    class Pipeline:
        def process(self, src, work_dir):
            workspaces.append(Path(work_dir))
            assert Path(src).read_bytes() == b'audio'
            Path(work_dir, 'checkpoint.json').write_text('private')
            if fail:
                raise RuntimeError('model failed')
            return {'timeline': [{'start': 0, 'end': 1, 'speaker_id': 'S0', 'text': 'test'}]}
    monkeypatch.setattr(main, 'get_pipeline', lambda: Pipeline())
    for _ in range(2):
        response = client.post('/transcribe', files={'file': ('sample.wav', b'audio')})
        assert response.status_code == (500 if fail else 200)
        if not fail:
            assert response.json()['timeline'][0]['speaker_id'] == 'S0'
    assert workspaces[0] != workspaces[1]
    assert not list(tmp_path.rglob('*.*'))
    assert main.jobs == {}

def test_health_does_not_load_models(client, monkeypatch):
    def forbidden():
        raise AssertionError('health loaded models')
    monkeypatch.setattr(main, 'get_pipeline', forbidden)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['models_loaded'] is False
    assert response.json()['backend'] == 'local'

def test_oversized_upload_is_removed(client, monkeypatch, tmp_path):
    monkeypatch.setattr(main, 'MAX_BYTES', 2)
    response = client.post('/transcribe', files={'file': ('sample.wav', b'audio')})
    assert response.status_code == 413
    assert not list(tmp_path.rglob('*.*'))
    assert main.jobs == {}
