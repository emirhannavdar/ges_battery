from pydantic import BaseModel, Field, ConfigDict

class _PTFItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    date: str
    hour: str
    price: float = Field(ge=0)

class PTFData(BaseModel):
    items: list[_PTFItem]

class _KPTFItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    date: str
    hour: str
    marketTradePrice: float

class KPTFData(BaseModel):
    items: list[_KPTFItem]