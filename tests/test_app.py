import io
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import fitz

import app


class AppRouteTests(unittest.TestCase):
    def setUp(self):
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()

    def tearDown(self):
        if app.extraction_lock.locked():
            app.extraction_lock.release()

    def test_extract_requires_a_pdf(self):
        response = self.client.post("/api/extract", data={})

        self.assertEqual(response.status_code, 400)
        self.assertIn("at least one PDF", response.get_json()["error"])

    def test_extract_rejects_non_pdf_upload(self):
        response = self.client.post(
            "/api/extract",
            data={"file": (io.BytesIO(b"not a pdf"), "notes.txt")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("must be a PDF", response.get_json()["error"])

    def test_extract_rejects_unknown_local_file(self):
        response = self.client.post(
            "/api/extract",
            data={"files": "../outside.pdf"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid local PDF selection", response.get_json()["error"])

    def test_extract_rejects_concurrent_job(self):
        app.extraction_lock.acquire()

        response = self.client.post(
            "/api/extract",
            data={"file": (io.BytesIO(b"%PDF-1.4"), "sample.pdf")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("already running", response.get_json()["error"])

    def test_uploaded_pdf_is_processed_from_temporary_path(self):
        document = fitz.open()
        page = document.new_page()
        page.insert_text(
            (72, 72),
            "CCTV camera system requirement with enough text for classification "
            "and dynamic extraction processing.",
        )
        pdf_bytes = document.tobytes()
        document.close()

        class ImmediateThread:
            def __init__(self, target, daemon):
                self.target = target

            def start(self):
                self.target()

        with patch.object(app.threading, "Thread", ImmediateThread), patch.object(
            app.extract_to_excel, "generate_excel_table"
        ):
            response = self.client.post(
                "/api/extract",
                data={
                    "file": (io.BytesIO(pdf_bytes), "uploaded-spec.pdf"),
                    "no_filter": "true",
                },
                content_type="multipart/form-data",
            )

        status = app.get_execution_status()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["count"], 1)
        self.assertEqual(list(app.project_path.glob(".itb_upload_*")), [])

    def test_diagram_load_rejects_path_traversal(self):
        response = self.client.get(
            "/api/diagrams/load",
            query_string={"path": "../outside.mmd"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Invalid file path.")

    def test_filter_config_rejects_invalid_regex(self):
        response = self.client.put(
            "/api/filter-config",
            json={
                "keywords": ["["],
                "false_positive_patterns": [],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid regex", response.get_json()["error"])

    def test_filter_config_rejects_update_during_extraction(self):
        app.extraction_lock.acquire()

        response = self.client.put(
            "/api/filter-config",
            json={
                "keywords": ["cctv"],
                "false_positive_patterns": [],
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("while extraction is running", response.get_json()["error"])

    def test_filter_config_saves_and_activates_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "filter_config.json"
            with patch.object(app.extract_to_excel, "config_file", str(config_path)):
                response = self.client.put(
                    "/api/filter-config",
                    json={
                        "keywords": [r"\bwidget\b", r"\bwidget\b", ""],
                        "false_positive_patterns": [r"\btemporary\b"],
                    },
                )
                saved = json.loads(config_path.read_text(encoding="utf-8"))

                self.assertEqual(response.status_code, 200)
                self.assertEqual(saved["keywords"], [r"\bwidget\b"])
                self.assertEqual(
                    saved["false_positive_patterns"],
                    [r"\btemporary\b"],
                )
                self.assertTrue(app.extract_to_excel.is_telecom_clause("widget"))
                self.assertTrue(
                    app.extract_to_excel.is_false_positive("temporary")
                )

        app.extract_to_excel.reload_config_and_compile()


class AppHelperTests(unittest.TestCase):
    def test_resolve_project_file_accepts_project_file(self):
        resolved = app.resolve_project_file("templates/diagram_maker.html", ".html")

        self.assertTrue(resolved.is_file())
        self.assertEqual(resolved.parent.name, "templates")

    def test_ai_polishing_keeps_original_record_on_error(self):
        records = [
            {"Requirement": "CCTV camera required", "Item": "CCTV"},
            {"Requirement": "Telephone required", "Item": "Telephone"},
        ]

        class FakeGenAI:
            class Client:
                def __init__(self, api_key):
                    pass

                def close(self):
                    pass

        def fake_process(record, _model):
            if record["Item"] == "CCTV":
                return {
                    "IsRelevant": False,
                    "Category": "CCTV Surveillance System",
                    "Item": "CCTV",
                    "상세 내용": "",
                }
            raise RuntimeError("temporary AI failure")

        with patch.object(app, "genai", FakeGenAI), patch.object(
            app, "process_clause_with_gemini", side_effect=fake_process
        ):
            polished = app.polish_clauses_with_ai(records, "test-key")

        self.assertEqual(polished, [records[1]])

    def test_ui_logs_are_bounded(self):
        with app.logs_lock:
            app.ui_logs.clear()

        for index in range(app.MAX_UI_LOGS + 5):
            app.append_ui_log(f"log {index}")

        self.assertEqual(len(app.ui_logs), app.MAX_UI_LOGS)
        self.assertEqual(app.ui_logs[0], "log 5")


if __name__ == "__main__":
    unittest.main()
