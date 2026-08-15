from app.main import app


def test_brand_pagination_and_sort_validation_are_in_openapi():
    operation = app.openapi()["paths"]["/brands"]["get"]
    params = {item["name"]: item for item in operation["parameters"]}
    assert params["page"]["schema"]["minimum"] == 1
    assert params["page_size"]["schema"]["maximum"] == 100
    assert set(params["sort_by"]["schema"]["enum"]) == {"brand_name", "luxury_tier", "created_at", "updated_at"}


def test_supplier_and_research_pagination_have_bounded_page_size():
    schema = app.openapi()
    for path in ("/suppliers", "/product-research-candidates"):
        params = {item["name"]: item for item in schema["paths"][path]["get"]["parameters"]}
        assert params["page"]["schema"]["minimum"] == 1
        assert params["page_size"]["schema"]["maximum"] == 100
