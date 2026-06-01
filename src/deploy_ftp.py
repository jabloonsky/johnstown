"""
Deploys generated HTML reports to OVH Shared Hosting via SFTP.
Runs after main.py has built the output/ folder.

Uploads:
  - output/index.html         → /www/index.html        (main page, always overwritten)
  - output/report_YYYY-MM-DD  → /www/report_YYYY-MM-DD (daily report, new file each day)

Uses ftplib from Python stdlib — no extra dependencies.
Falls back gracefully and sends Discord alert on failure.
"""

import ftplib
import os
import sys
import time
import httpx
import asyncio
from pathlib import Path

OUTPUT_DIR  = Path(__file__).parent.parent / "output"
REMOTE_DIR  = "/www"          # OVH default web root for kamskid account


def get_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return val


def upload_file(ftp: ftplib.FTP, local_path: Path, remote_path: str, retries: int = 3):
    """Upload a single file with retry logic."""
    for attempt in range(1, retries + 1):
        try:
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            print(f"  ✓ Uploaded: {local_path.name} → {remote_path}")
            return
        except Exception as e:
            print(f"  ✗ Attempt {attempt}/{retries} failed for {local_path.name}: {e}")
            if attempt < retries:
                time.sleep(3 * attempt)   # 3s, 6s backoff
    raise RuntimeError(f"Failed to upload {local_path.name} after {retries} attempts")


def ensure_remote_dir(ftp: ftplib.FTP, remote_dir: str):
    """Create remote directory if it doesn't exist."""
    try:
        ftp.cwd(remote_dir)
    except ftplib.error_perm:
        ftp.mkd(remote_dir)
        ftp.cwd(remote_dir)


async def notify_discord(message: str, success: bool = True):
    webhook = os.environ.get("DISCORD_WEBHOOK")
    if not webhook:
        return
    color   = 0x4ade80 if success else 0xf87171
    payload = {"embeds": [{"description": message, "color": color}]}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(webhook, json=payload)
        except Exception:
            pass


def deploy():
    host = get_env("OVH_FTP_HOST")
    user = get_env("OVH_FTP_USER")
    pw   = get_env("OVH_FTP_PASS")

    # Collect files to upload
    files_to_upload = []

    index = OUTPUT_DIR / "index.html"
    if index.exists():
        files_to_upload.append((index, f"{REMOTE_DIR}/index.html"))

    # Upload all report HTML files
    for report in sorted(OUTPUT_DIR.glob("report_*.html")):
        files_to_upload.append((report, f"{REMOTE_DIR}/{report.name}"))

    if not files_to_upload:
        print("No files to upload — output/ is empty.")
        sys.exit(1)

    print(f"\n[FTP] Connecting to {host}...")
    print(f"[FTP] Files to upload: {len(files_to_upload)}")

    try:
        ftp = ftplib.FTP()
        ftp.connect(host=host, port=21, timeout=30)
        ftp.login(user=user, passwd=pw)
        ftp.set_pasv(True)   # Passive mode — required for most firewalls
        print(f"[FTP] Connected as {user}")

        # Make sure /www exists
        ensure_remote_dir(ftp, REMOTE_DIR)

        for local_path, remote_path in files_to_upload:
            upload_file(ftp, local_path, remote_path)

        ftp.quit()
        print(f"\n[FTP] Deploy complete — {len(files_to_upload)} file(s) uploaded ✓")

    except Exception as e:
        error_msg = f"❌ **OVH FTP Deploy FAILED**\n`{e}`"
        print(f"\n[FTP] FAILED: {e}")
        asyncio.run(notify_discord(error_msg, success=False))
        sys.exit(1)


if __name__ == "__main__":
    deploy()
