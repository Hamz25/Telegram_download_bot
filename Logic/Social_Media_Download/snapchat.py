import os
import subprocess
import logging
from typing import Optional

from Logic.utils.path import generate_target_dir

logger = logging.getLogger(__name__)


def download_snapchat(url: str) -> Optional[str]:
    target_dir = generate_target_dir("snapchat")
    os.makedirs(target_dir, exist_ok=True)

    outtmpl = os.path.join(target_dir, "snap_%(autonumber)03d.%(ext)s")
    command = ["yt-dlp", "-o", outtmpl, url]

    try:
        # FIXED: capture_output/text were missing before, so e.stderr was
        # always None on failure - every error message ever logged by this
        # function was "Download failed: None".
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        logger.info(f"[Snapchat] Success, target dir: {target_dir}")
        return target_dir

    except subprocess.CalledProcessError as e:
        logger.error(f"[Snapchat] Download failed: {e.stderr.strip() if e.stderr else 'unknown error'}")
        return None
    except subprocess.TimeoutExpired:
        logger.error("[Snapchat] Download timed out after 120s")
        return None