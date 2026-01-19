import json
import os
from typing import Optional, List

ADMIN_FILE = 'admin_config.json'

def get_or_create_admin_file():
    """Ensure admin config file exists."""
    if not os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'admin_ids': [],
                'broadcast_enabled': True
            }, f, indent=2)
    return ADMIN_FILE

def load_admin_config() -> dict:
    """Load admin configuration from JSON file."""
    config_path = get_or_create_admin_file()
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading admin config: {e}")
        return {'admin_ids': [], 'broadcast_enabled': True}

def save_admin_config(config: dict):
    """Save admin configuration to JSON file."""
    config_path = get_or_create_admin_file()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving admin config: {e}")
        return False

def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    config = load_admin_config()
    return user_id in config.get('admin_ids', [])

def add_admin(user_id: int) -> bool:
    """
    Add user as admin.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        bool: True if added, False if already admin
    """
    config = load_admin_config()
    
    if user_id in config.get('admin_ids', []):
        return False  # Already admin
    
    config['admin_ids'].append(user_id)
    return save_admin_config(config)

def remove_admin(user_id: int) -> bool:
    """
    Remove user from admin list.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        bool: True if removed, False if wasn't admin
    """
    config = load_admin_config()
    
    if user_id not in config.get('admin_ids', []):
        return False  # Not admin
    
    config['admin_ids'].remove(user_id)
    return save_admin_config(config)

def get_all_admins() -> List[int]:
    """Get list of all admin IDs."""
    config = load_admin_config()
    return config.get('admin_ids', [])

def set_broadcast_enabled(enabled: bool) -> bool:
    """Enable or disable broadcast feature."""
    config = load_admin_config()
    config['broadcast_enabled'] = enabled
    return save_admin_config(config)

def is_broadcast_enabled() -> bool:
    """Check if broadcast feature is enabled."""
    config = load_admin_config()
    return config.get('broadcast_enabled', True)
