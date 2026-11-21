from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PricingTier(StrictModel):
    leverage_threshold: Decimal = Field(gt=0)
    margin_bps: int = Field(ge=0)


class FlatMargin(StrictModel):
    margin_type: Literal["flat"]
    flat_margin_bps: int = Field(ge=0)
    pricing_grid: None = None


class GridMargin(StrictModel):
    margin_type: Literal["grid"]
    flat_margin_bps: None = None
    # A grid must retain at least two complete tiers.
    pricing_grid: list[PricingTier] = Field(min_length=2)

    @model_validator(mode="after")
    def thresholds_must_increase(self):
        thresholds = [tier.leverage_threshold for tier in self.pricing_grid]
        if any(current <= previous for previous, current in zip(thresholds, thresholds[1:])):
            raise ValueError("Pricing grid leverage thresholds must be strictly increasing")
        return self


Margin = Annotated[
    Union[FlatMargin, GridMargin],
    Field(discriminator="margin_type"),
]


class LoanTerms(StrictModel):
    borrower: str = Field(min_length=1, max_length=200)
    commitment_amount: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    effective_date: date
    maturity_date: date
    maximum_leverage_ratio: Decimal | None = Field(default=None, gt=0)
    minimum_interest_coverage_ratio: Decimal | None = Field(default=None, gt=0)
    margin: Margin

    @field_validator("borrower")
    @classmethod
    def borrower_must_not_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Borrower must not be blank")
        return value.strip()

    @model_validator(mode="after")
    def maturity_after_effective_date(self):
        if self.maturity_date <= self.effective_date:
            raise ValueError("Maturity date must be after effective date")
        return self
