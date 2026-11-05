from pentest_platform.controllers.deps import get_actor, get_reports
from pentest_platform.domain.entities import ReportSnapshot
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

REPORT = ReportSnapshot(id="report-1", engagement_id="eng-1", version=1, status="PREVIEW", snapshot={})


class StubReports:
    def list_reports(self, actor, engagement_id):
        return [REPORT]

    def create_snapshot(self, actor, engagement_id, partial):
        return REPORT

    def get_report(self, actor, report_id):
        return REPORT

    def approve(self, actor, report_id):
        REPORT.status = "FINAL_COMPLETE"
        return REPORT

    def render(self, actor, report_id):
        REPORT.pdf_key = "reports/report-1.pdf"
        return REPORT, b"%PDF-1.4"

    def download(self, actor, report_id):
        return "report.pdf", b"%PDF-1.4"

    def preview(self, actor, report_id):
        return b"%PDF-1.4"


def test_report_lifecycle_endpoints():
    client = make_client({get_actor: lambda: actor(), get_reports: lambda: StubReports()})
    created = client.post("/api/v1/engagements/eng-1/reports", json={"partial": False})
    assert created.status_code == 201
    approved = client.post("/api/v1/reports/report-1/approve")
    assert approved.json()["status"] == "FINAL_COMPLETE"
    rendered = client.post("/api/v1/reports/report-1/render")
    assert rendered.status_code == 200
    downloaded = client.get("/api/v1/reports/report-1/download")
    assert downloaded.headers["content-type"] == "application/pdf"


def test_report_preview_is_inline_pdf():
    client = make_client({get_actor: lambda: actor(), get_reports: lambda: StubReports()})
    preview = client.get("/api/v1/reports/report-1/preview")
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "application/pdf"
