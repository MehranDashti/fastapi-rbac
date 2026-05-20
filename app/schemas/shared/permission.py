from datetime import datetime

from pydantic import BaseModel


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    guard_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
