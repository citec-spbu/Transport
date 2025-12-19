from typing import Optional, Literal

class UserContext:
    def __init__(self, type: Literal["user", "guest", "anonymous"], email: Optional[str] = None, guest_token: Optional[str] = None):
        self.type = type
        self.email = email
        self.guest_token = guest_token