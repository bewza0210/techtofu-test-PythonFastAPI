from pydantic import BaseModel, Field
from typing import Optional

class Item(BaseModel):
    partName: str
    partNumber: str

class MasterPart(BaseModel):
    id: int
    partName: Optional[str] = Field(None, title="Part Name")
    partNumber: Optional[str] = Field(None, title="Part Number")
    updateDate: Optional[str] = Field(None, title="Update Date")