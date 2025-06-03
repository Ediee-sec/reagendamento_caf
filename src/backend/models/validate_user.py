from pathlib import Path
import hashlib
import os
import sys
sys.path.append(os.path.join(str(Path(__file__).resolve().parents[2])))
from src.backend.models.conn_db import ConnectionPostgres
def validate_user(email:str, password:str) -> bool:
    """
    Validate user credentials against the database.
    
    Args:
        email (str): User's email.
        password (str): User's password.
    
    Returns:
        bool: True if credentials are valid, False otherwise.
    """

    query = f"""
    SELECT EXISTS (
        SELECT 1 FROM users_caf
        WHERE email = '{email}' AND password = '{hashlib.md5(password.encode()).hexdigest()}'
    );
    """
    
    conn = ConnectionPostgres()
    result = conn.execute_query(query)
    
    if result and result[0][0]:
        return True
    return False