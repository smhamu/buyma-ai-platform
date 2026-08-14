from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


JPY = Decimal("1")
MONEY = Decimal("0.01")
RATE = Decimal("0.000001")


@dataclass(frozen=True)
class PriceCalculation:
    effective_supplier_price: Decimal
    export_price: Decimal | None
    supplier_cost_jpy: Decimal
    total_cost: Decimal
    buyma_fee: Decimal
    profit_amount: Decimal
    profit_rate: Decimal


class PriceCalculationService:
    @staticmethod
    def calculate(
        *,
        supplier_price: Decimal,
        vat_policy: str,
        vat_rate: Decimal | None,
        exchange_rate: Decimal,
        japan_shipping_cost: Decimal,
        estimated_import_cost: Decimal,
        estimated_other_cost: Decimal,
        buyma_price: Decimal,
        buyma_fee_rate: Decimal,
    ) -> PriceCalculation:
        export_price = None
        effective_price = supplier_price
        if vat_policy == "excluded_for_export" and vat_rate is not None:
            export_price = (supplier_price / (Decimal("1") + vat_rate)).quantize(
                MONEY, rounding=ROUND_HALF_UP
            )
            effective_price = export_price

        supplier_cost = (effective_price * exchange_rate).quantize(JPY, rounding=ROUND_HALF_UP)
        total_cost = (
            supplier_cost + japan_shipping_cost + estimated_import_cost + estimated_other_cost
        ).quantize(JPY, rounding=ROUND_HALF_UP)
        buyma_fee = (buyma_price * buyma_fee_rate).quantize(JPY, rounding=ROUND_HALF_UP)
        profit = (buyma_price - buyma_fee - total_cost).quantize(JPY, rounding=ROUND_HALF_UP)
        profit_rate = (profit / buyma_price).quantize(RATE, rounding=ROUND_HALF_UP)

        return PriceCalculation(
            effective_supplier_price=effective_price.quantize(MONEY, rounding=ROUND_HALF_UP),
            export_price=export_price,
            supplier_cost_jpy=supplier_cost,
            total_cost=total_cost,
            buyma_fee=buyma_fee,
            profit_amount=profit,
            profit_rate=profit_rate,
        )

    @staticmethod
    def meets_thresholds(
        calculation: PriceCalculation,
        *,
        min_profit_amount: Decimal | None = None,
        min_profit_rate: Decimal | None = None,
    ) -> bool:
        return (
            min_profit_amount is None or calculation.profit_amount >= min_profit_amount
        ) and (min_profit_rate is None or calculation.profit_rate >= min_profit_rate)
