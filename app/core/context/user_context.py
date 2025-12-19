from typing import Optional, Literal
from uuid import UUID

class UserContext:
    def __init__(self, type: Literal["user", "guest", "anonymous"], user_id: Optional[UUID] = None, guest_token: Optional[str] = None):
        self.type = type
        self.user_id = user_id
        self.guest_token = guest_token