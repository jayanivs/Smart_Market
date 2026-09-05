from typing import Optional
from fastapi import Header

def get_current_user_id(x_user_id: Optional[str] = Header(default="1")) -> int:
    """
    Extracts the user ID from the X-User-Id header.
    Defaults to 1 for backward compatibility and demo mode.
    """
    try:
        return int(x_user_id) if x_user_id else 1
    except (ValueError, TypeError):
        return 1
