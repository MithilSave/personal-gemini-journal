import firebase_admin
from firebase_admin import auth
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

if not firebase_admin._apps:
    firebase_admin.initialize_app()

security = HTTPBearer()

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Decodes and cryptographically validates the Firebase JWT ID Token.
    Returns the authenticated user's unique UID.
    """
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed: UID missing from token payload"
            )
        return uid
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {str(e)}"
        )
