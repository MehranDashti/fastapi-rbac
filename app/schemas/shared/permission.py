from datetime import datetime

from pydantic import BaseModel


class PermissionResponse(BaseModel):
    id: int
    name: str
    display_name: str
    guard_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
