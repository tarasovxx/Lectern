import unittest
from unittest.mock import AsyncMock, patch
import httpx
from backend import pipeline
from backend.speech_service import SpeechServiceClient, map_timeline


class SpeechAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_whole_file_multipart_and_mapping(self):
        requests = []
        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={"timeline": [{"start": 1.25, "end": 4.75, "text": "hello", "speaker_id": 2, "source_speaker": "S2", "role": "student", "display_name": "Student 2"}], "analytics": {"speakers": []}})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await SpeechServiceClient("http://speech:8000", client=client).transcribe(b"whole recording", "lesson.wav", "audio/wav")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].url.path, "/transcribe")
        self.assertIn(b"whole recording", requests[0].content)
        line = map_timeline(result)[0]
        self.assertEqual((line["start_ms"], line["end_ms"], line["source_speaker"], line["role"]), (1250, 4750, "S2", "student"))
        self.assertEqual(line["speaker_id"], 2)

    async def test_local_success_and_error_never_chunk_or_call_ml(self):
        result = {"timeline": [{"start": 0, "end": 2, "text": "hello", "source_speaker": "S0"}], "analytics": {"speaker_count": 1}}
        for error in (None, RuntimeError("speech unavailable")):
            with self.subTest(error=error), patch.object(pipeline, "TRANSCRIPTION_BACKEND", "local"), patch.object(pipeline, "GENERATE_MATERIALS", False), patch.object(pipeline, "update_generation") as update, patch.object(pipeline.SpeechServiceClient, "transcribe", AsyncMock(return_value=result, side_effect=error)), patch.object(pipeline, "split_audio_into_chunks") as split, patch.object(pipeline, "MLServiceClient") as ml:
                await pipeline.run_generation_pipeline("job", b"audio", "lesson.wav", "audio/wav")
                split.assert_not_called()
                ml.assert_not_called()
                final = update.call_args.args[1]
                self.assertEqual(final["status"], "failed" if error else "completed")
                if not error:
                    self.assertEqual(final["transcript"][0]["end_ms"], 2000)
                    self.assertEqual(final["analytics"]["local_speech"], result["analytics"])

    async def test_local_generation_enabled_preserves_original_speakers_and_end_times(self):
        result = {"timeline": [{"start": 0, "end": 2, "text": "hello", "source_speaker": "S0"}], "analytics": {"speaker_count": 1}}
        state = {}
        def update(_id, fields):
            state.update(fields)
        generated = ([{"start_ms": 0, "text": "rewritten"}], [], [{"content": "summary"}], [{"question_text": "quiz"}], {}, "")
        with patch.object(pipeline, "TRANSCRIPTION_BACKEND", "local"), patch.object(pipeline, "GENERATE_MATERIALS", True), patch.object(pipeline, "ML_API_KEY", "test-key"), patch.object(pipeline, "update_generation", side_effect=update), patch.object(pipeline, "get_generation", side_effect=lambda _id: state.copy()), patch.object(pipeline.SpeechServiceClient, "transcribe", AsyncMock(return_value=result)), patch.object(pipeline, "build_summary_quiz_and_speech_analysis", AsyncMock(return_value=generated)) as generate:
            await pipeline.run_generation_pipeline("job", b"audio", "lesson.wav", "audio/wav")
            generate.assert_awaited_once()
            self.assertEqual(state["status"], "completed")
            self.assertEqual(state["transcript"][0]["source_speaker"], "S0")
            self.assertEqual(state["transcript"][0]["end_ms"], 2000)
            self.assertEqual(state["analytics"]["local_speech"], result["analytics"])

    async def test_demo_uses_synthetic_fixture_without_network_or_models(self):
        with patch.object(pipeline, "TRANSCRIPTION_BACKEND", "demo"), patch.object(pipeline, "GENERATE_MATERIALS", False), patch.object(pipeline, "update_generation") as update, patch.object(pipeline, "SpeechServiceClient") as speech, patch.object(pipeline, "MLServiceClient") as ml:
            await pipeline.run_generation_pipeline("job", b"upload", "lesson.mp4", "video/mp4")
            speech.assert_not_called()
            ml.assert_not_called()
            final = update.call_args.args[1]
            self.assertEqual(final["status"], "completed")
            self.assertTrue(final["analytics"]["synthetic"])
            self.assertIn("синтетический", final["transcript"][0]["text"].lower())


class DemoUploadTests(unittest.TestCase):
    def test_runtime_config_reports_demo_mode_before_static_catchall(self):
        from fastapi.testclient import TestClient
        from backend import main
        with patch.object(pipeline, "TRANSCRIPTION_BACKEND", "demo"), patch.object(pipeline, "GENERATE_MATERIALS", False):
            response = TestClient(main.app).get("/api/config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"transcription_backend": "demo", "generate_materials": False})

    def test_upload_queue_completed_persisted_and_retry_without_ml(self):
        import tempfile
        from pathlib import Path
        from fastapi.testclient import TestClient
        from backend import main, queue_manager
        from backend.routes import teacher
        with tempfile.TemporaryDirectory() as tmp, patch.object(main, "DB_PATH", Path(tmp) / "app.db"), patch.object(teacher, "UPLOAD_DIR", Path(tmp)), patch.object(queue_manager, "UPLOAD_DIR", Path(tmp)), patch.object(queue_manager, "SEMAPHORE", None), patch.object(pipeline, "TRANSCRIPTION_BACKEND", "demo"), patch.object(pipeline, "GENERATE_MATERIALS", False), patch.object(pipeline, "MLServiceClient") as ml, patch.object(pipeline, "SpeechServiceClient") as speech:
            with TestClient(main.app) as client:
                response = client.post("/api/generations/upload", files={"file": ("lesson.wav", b"synthetic upload", "audio/wav")})
                self.assertEqual(response.status_code, 201)
                generation_id = response.json()["id"]
                generation = client.get(f"/api/generations/{generation_id}").json()
                self.assertEqual(generation["status"], "completed")
                self.assertEqual(generation["transcript"][0]["end_ms"], 5000)
                self.assertTrue(generation["analytics"]["synthetic"])
                self.assertFalse((Path(tmp) / generation_id).exists())
                retry = client.post(f"/api/generations/{generation_id}/retry")
                self.assertEqual(retry.status_code, 200)
                generation = client.get(f"/api/generations/{generation_id}").json()
                self.assertEqual(generation["status"], "completed")
                self.assertTrue(generation["analytics"]["synthetic"])
                ml.assert_not_called()
                speech.assert_not_called()

    def test_delete_requires_owner_before_cancelling_or_unlinking(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock
        from fastapi.testclient import TestClient
        from backend import main, queue_manager
        from backend.routes import teacher
        with tempfile.TemporaryDirectory() as tmp, patch.object(main, "DB_PATH", Path(tmp) / "app.db"), patch.object(teacher, "UPLOAD_DIR", Path(tmp)), patch.object(queue_manager, "UPLOAD_DIR", Path(tmp)), patch.object(queue_manager, "SEMAPHORE", None), patch.object(pipeline, "TRANSCRIPTION_BACKEND", "demo"), patch.object(pipeline, "GENERATE_MATERIALS", False), patch.dict(teacher.RUNNING_TASKS, {}, clear=True):
            with TestClient(main.app) as owner, TestClient(main.app) as other:
                response = owner.post("/api/generations/upload", files={"file": ("lesson.wav", b"demo", "audio/wav")})
                self.assertEqual(response.status_code, 201)
                generation_id = response.json()["id"]
                upload = Path(tmp) / generation_id
                upload.write_bytes(b"queued recording")
                task = Mock()
                teacher.RUNNING_TASKS[generation_id] = task
                response = other.delete(f"/api/generations/{generation_id}")
                self.assertEqual(response.status_code, 404)
                task.cancel.assert_not_called()
                self.assertEqual(upload.read_bytes(), b"queued recording")
                self.assertEqual(owner.get(f"/api/generations/{generation_id}").status_code, 200)
                response = owner.delete(f"/api/generations/{generation_id}")
                self.assertEqual(response.status_code, 200)
                task.cancel.assert_called_once()
                self.assertFalse(upload.exists())
                self.assertEqual(owner.get(f"/api/generations/{generation_id}").status_code, 404)
