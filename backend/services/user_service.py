from ..models import User
from ..utils import hash_password, check_password, create_token

def register_user(wallet, password):
    """
    Register a new user.
    
    Args:
        wallet (str): The wallet address.
        password (str): The password.
        
    Returns:
        User: The created user.
        
    Raises:
        ValueError: If the wallet is already in use.
    """
    from ..models.base import SessionLocal
    
    db = SessionLocal()
    try:
        # Check if wallet is already in use
        existing = db.query(User).filter_by(wallet=wallet).first()
        if existing:
            raise ValueError("Wallet address already in use")
        
        # Create new user
        hashed = hash_password(password)
        new_user = User(wallet=wallet, hashed_password=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    finally:
        db.close()

def authenticate_user(wallet, password):
    """
    Authenticate a user.
    
    Args:
        wallet (str): The wallet address.
        password (str): The password.
        
    Returns:
        dict: A dictionary containing the access token and user information.
        
    Raises:
        ValueError: If the credentials are invalid.
    """
    from ..models.base import SessionLocal
    
    db = SessionLocal()
    try:
        # Get user by wallet
        user = db.query(User).filter_by(wallet=wallet).first()
        if not user or not check_password(user.hashed_password, password):
            raise ValueError("Invalid credentials")
        
        # Create token
        token = create_token(wallet)
        return {
            "access_token": token,
            "user": {
                "id": user.id,
                "wallet": user.wallet
            }
        }
    finally:
        db.close()

def get_user_by_wallet(wallet):
    """
    Get a user by wallet address.
    
    Args:
        wallet (str): The wallet address.
        
    Returns:
        User: The user.
    """
    from ..models.base import SessionLocal
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(wallet=wallet).first()
        return user
    finally:
        db.close()