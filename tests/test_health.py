"""Kiểm tra endpoint /api/health và khởi động server (docs/ARCHITECTURE.md mục 4)."""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.main import app


def test_health_reports_ok_with_default_mini_dataset():
    """Mặc định khi khởi động nạp mini.json: dataset_loaded=True, dataset_id='mini'."""
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["dataset_loaded"] is True
        assert data["dataset_id"] == "mini"


def test_startup_fails_when_graph_file_not_found(monkeypatch):
    """Khi file đồ thị không tồn tại: khởi động TestClient raise RuntimeError có tên file."""
    monkeypatch.setenv("SAIGO_GRAPH", "tests/fixtures/khong_ton_tai.json")
    with pytest.raises(RuntimeError, match="Không tìm thấy file đồ thị tại.*khong_ton_tai.json"):
        with TestClient(app):
            pass


def test_startup_fails_when_graph_corrupt(tmp_path, monkeypatch):
    """Khi file đồ thị sai định dạng: khởi động TestClient raise RuntimeError có lý do."""
    bad_file = tmp_path / "bad_mini.json"
    bad_file.write_text('{"format": "saigo-graph/bad"}', encoding="utf-8")
    monkeypatch.setenv("SAIGO_GRAPH", str(bad_file))
    with pytest.raises(RuntimeError, match="Lỗi khi nạp file đồ thị tại.*bad_mini.json"):
        with TestClient(app):
            pass
