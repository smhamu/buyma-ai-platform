from decimal import Decimal

from app.services.price_calculation_service import PriceCalculationService


def calculate(**overrides):
    values = {
        "supplier_price": Decimal("120.00"), "vat_policy": "included", "vat_rate": Decimal("0.20"),
        "exchange_rate": Decimal("160"), "japan_shipping_cost": Decimal("2000"),
        "estimated_import_cost": Decimal("1000"), "estimated_other_cost": Decimal("500"),
        "buyma_price": Decimal("30000"), "buyma_fee_rate": Decimal("0.077"),
    }
    values.update(overrides)
    return PriceCalculationService.calculate(**values)


def test_eur_to_jpy_and_all_costs_and_buyma_fee():
    result = calculate()
    assert result.export_price is None
    assert result.supplier_cost_jpy == Decimal("19200")
    assert result.total_cost == Decimal("22700")
    assert result.buyma_fee == Decimal("2310")
    assert result.profit_amount == Decimal("4990")
    assert result.profit_rate == Decimal("0.166333")


def test_confirmed_vat_export_uses_division_not_percentage_subtraction():
    result = calculate(vat_policy="excluded_for_export")
    assert result.export_price == Decimal("100.00")
    assert result.supplier_cost_jpy == Decimal("16000")


def test_unknown_vat_never_applies_vat_exclusion():
    result = calculate(vat_policy="unknown")
    assert result.export_price is None
    assert result.effective_supplier_price == Decimal("120.00")


def test_negative_profit_and_decimal_half_up_rounding():
    result = calculate(supplier_price=Decimal("100.005"), vat_rate=None, exchange_rate=Decimal("1"), japan_shipping_cost=Decimal("0"), estimated_import_cost=Decimal("0"), estimated_other_cost=Decimal("0"), buyma_price=Decimal("100"), buyma_fee_rate=Decimal("0.005"))
    assert result.supplier_cost_jpy == Decimal("100")
    assert result.buyma_fee == Decimal("1")
    assert result.profit_amount == Decimal("-1")


def test_profit_thresholds_are_configurable():
    result = calculate()
    assert PriceCalculationService.meets_thresholds(result, min_profit_amount=Decimal("4000"), min_profit_rate=Decimal("0.15"))
    assert not PriceCalculationService.meets_thresholds(result, min_profit_amount=Decimal("5000"))
