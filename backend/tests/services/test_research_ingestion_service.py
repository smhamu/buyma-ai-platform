from types import SimpleNamespace

from app.services.research_ingestion_service import ResearchIngestionService


def test_automatic_fetch_is_disabled_by_default():
    supplier = SimpleNamespace(is_active=True, automated_fetch_enabled=False, ingestion_source_type="official_api", terms_status="allowed", robots_status="allowed")
    assert not ResearchIngestionService.automatic_fetch_allowed(supplier)


def test_prohibited_terms_and_disallowed_robots_fail_closed():
    base = dict(is_active=True, automated_fetch_enabled=True, ingestion_source_type="html_parser")
    assert not ResearchIngestionService.automatic_fetch_allowed(SimpleNamespace(**base, terms_status="prohibited", robots_status="allowed"))
    assert not ResearchIngestionService.automatic_fetch_allowed(SimpleNamespace(**base, terms_status="allowed", robots_status="disallowed"))


def test_approved_fetch_policy_can_be_enabled_explicitly():
    supplier = SimpleNamespace(is_active=True, automated_fetch_enabled=True, ingestion_source_type="official_api", terms_status="allowed", robots_status="allowed")
    assert ResearchIngestionService.automatic_fetch_allowed(supplier)
