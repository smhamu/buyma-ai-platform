from scripts.seed_luxury_brands import LUXURY_BRANDS


def test_seed_contains_nine_unique_expected_brands():
    codes = [item["brand_code"] for item in LUXURY_BRANDS]
    assert len(codes) == 9
    assert len(set(codes)) == 9
    assert {"hermes", "chanel", "gucci", "prada", "saint_laurent", "bottega_veneta", "loewe", "dior", "celine"} == set(codes)


def test_seed_uses_conservative_policies_and_expected_tiers():
    by_code = {item["brand_code"]: item for item in LUXURY_BRANDS}
    assert by_code["hermes"]["luxury_tier"] == "ultra_luxury"
    assert by_code["chanel"]["luxury_tier"] == "ultra_luxury"
    assert by_code["hermes"]["online_purchase_policy"] == "research_only"
    assert by_code["gucci"]["online_purchase_policy"] == "unknown"
