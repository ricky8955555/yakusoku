from datetime import date, datetime
from typing import Generic, TypeVar, cast

import aiohttp
import pydantic.alias_generators
from pydantic import BaseModel, ConfigDict, Field
from pydantic.dataclasses import dataclass

_T = TypeVar("_T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=pydantic.alias_generators.to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


@dataclass(frozen=True, kw_only=True)
class ApiError(Exception):
    code: str = Field(alias="errorCode")
    message: str = Field(alias="errorMessage")

    def __post_init__(self) -> None:
        super().__init__(self.code, self.message)


class _Response(BaseSchema):
    name: str
    description: str
    date: datetime
    type: str | None = None


class _ResponseData(BaseSchema, Generic[_T]):
    data: _T


class ConversionRateData(BaseSchema):
    conversion_rate: float
    crdhld_bill_amt: float
    fx_date: date
    trans_curr: str
    crdhld_bill_curr: str
    trans_amt: float
    bank_fee: float = 0


def _parse_response_data(data: str | bytes | bytearray, typ: type[_T]) -> _T:
    response = _Response.model_validate_json(data)
    if response.type == "error":
        target = cast(_ResponseData[ApiError], _ResponseData.__class_getitem__(ApiError))
        raise target.model_validate_json(data).data
    target = cast(_ResponseData[_T], _ResponseData.__class_getitem__(typ))
    return target.model_validate_json(data).data


async def conversion_rate(
    *,
    fx_date: date | None = None,
    trans_curr: str,
    crdhld_bill_curr: str,
    bank_fee: float = 0,
    trans_amt: float,
) -> ConversionRateData:
    url = "https://www.mastercard.com/settlement/currencyrate/conversion-rate"

    fx_date_param = fx_date.strftime("%4Y-%m-%d") if fx_date else "0000-00-00"
    params = {
        "fxDate": fx_date_param,
        "transCurr": trans_curr,
        "crdhldBillCurr": crdhld_bill_curr,
        "bankFee": bank_fee,
        "transAmt": trans_amt,
    }

    async with aiohttp.ClientSession() as client:
        async with client.get(url, params=params) as resp:
            json = await resp.read()

    data = _parse_response_data(json, ConversionRateData)
    return data
