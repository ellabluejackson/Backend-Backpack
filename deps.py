from fastapi import Depends, Header, HTTPException

from security import decode_access_token, parse_bearer_authorization


def get_current_user_id(authorization: str | None = Header(default=None)) -> int:
    token = parse_bearer_authorization(authorization)
    claims = decode_access_token(token)
    try:
        return int(claims.get("sub", "0"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token subject")
