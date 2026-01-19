"""
Directory Path Management
Module for generating unique directory paths for different platforms.
Ensures no conflicts when multiple users download content simultaneously.
"""

import uuid
import os

# ============================================================================
# Directory Generation
# ============================================================================


def generate_target_dir(platform_name: str) -> str:
    """
    Generate a unique target directory for platform content downloads.

    Creates a unique directory path using platform name and random UUID
    to prevent filename collisions when multiple users download simultaneously.

    Args:
        platform_name: Name of the platform (e.g., 'tiktok', 'instagram')

    Returns:
        str: Full path to unique target directory

    Example:
        >>> path = generate_target_dir('tiktok')
        >>> # Returns: 'C:/absolute/path/downloads/tiktok_a1b2c3d4'
    """
    base_dir = os.path.abspath("downloads")  # Root directory

    # Create unique folder ID to avoid conflicts with concurrent users
    request_id = str(uuid.uuid4())

    target_dir = os.path.join(base_dir, f"{platform_name}_{request_id}")

    return target_dir