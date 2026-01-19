import csv
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

USERS_CSV = 'users.csv'

def get_or_create_csv():
    """Ensure CSV file exists with headers."""
    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'username', 'first_name', 'last_name', 'language', 'join_date'])
    return USERS_CSV

def user_exists(user_id: int) -> bool:
    """Check if user already exists in CSV."""
    csv_path = get_or_create_csv()
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['user_id'] and int(row['user_id']) == user_id:
                    return True
    except Exception as e:
        print(f"⚠️ Error checking user existence: {e}")
    return False

def save_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None, language: Optional[str] = None) -> bool:
    """
    Save user data to CSV if not already exists.
    
    Args:
        user_id: Telegram user ID
        username: Telegram username (without @)
        first_name: User's first name
        last_name: User's last name
        language: User's language code
        
    Returns:
        bool: True if user was saved (new), False if already existed
    """
    csv_path = get_or_create_csv()
    
    # Check if user already exists
    if user_exists(user_id):
        return False
    
    try:
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                user_id,
                username or '',
                first_name or '',
                last_name or '',
                language or 'en',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
        print(f"✅ New user saved: {user_id} (@{username})")
        return True
    except Exception as e:
        print(f"❌ Error saving user: {e}")
        return False

def get_all_users() -> List[Dict]:
    """
    Retrieve all users from CSV.
    
    Returns:
        List of dictionaries with user data
    """
    csv_path = get_or_create_csv()
    users = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['user_id']:
                    users.append(row)
    except Exception as e:
        print(f"⚠️ Error reading users: {e}")
    
    return users

def get_all_user_ids() -> List[int]:
    """
    Get all user IDs from CSV.
    
    Returns:
        List of user IDs
    """
    users = get_all_users()
    return [int(u['user_id']) for u in users if u['user_id']]

def get_user_count() -> int:
    """Get total number of registered users."""
    return len(get_all_users())
