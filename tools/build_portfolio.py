"""Build the current portfolio PDFs and synchronize the static case cards.

The six-page Work Samples (both PDF editions and the Markdown) follow the portfolio site's edition and are not
rebuilt here; build_skills_portfolio.py, which produced the earlier edition, is kept for reference only."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
for name in ['build_repeatability_brief.py', 'build_case_studies.py', 'build_ai_method.py', 'build_review_demo.py', 'build_exhibit_pages.py', 'sync_web_copy.py']:
    subprocess.run([sys.executable, str(HERE/name)], check=True)
print('Current portfolio PDFs and web copy built successfully.')
