from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

WEBSITE_DIRECTORY = PROJECT_ROOT / "src" / "personal_site_imported_frontend"