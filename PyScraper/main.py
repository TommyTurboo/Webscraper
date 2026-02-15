import argparse
import sys
import shutil
from pathlib import Path

# Basis directory bepalen (waar main.py staat)
BASE_DIR = Path(__file__).parent

# Voeg src toe aan python path
sys.path.append(str(BASE_DIR / "src"))

from core.engine import ScrapeEngine

def main():
    parser = argparse.ArgumentParser(description="WebHTMLextractor - Modular Scraper")
    
    # Gebruik paden relatief aan BASE_DIR
    default_input = BASE_DIR / "data" / "input" / "urls.txt"
    default_output = BASE_DIR / "data" / "output"
    
    parser.add_argument('--headless', action='store_true', help='Run without visible browser')
    parser.add_argument('--fresh', action='store_true', help='Delete browser profile before starting')
    parser.add_argument('--input', default=str(default_input), help='Path to URL list')
    parser.add_argument('--output', default=str(default_output), help='Output directory')
    
    args = parser.parse_args()

    if args.fresh:
        profile_path = BASE_DIR / "browser_profile"
        if profile_path.exists():
            print(f"🧹 Cleaning browser profile at {profile_path}...")
            try:
                shutil.rmtree(profile_path)
                print("✨ Profile cleared.")
            except Exception as e:
                print(f"⚠️ Could not delete profile: {e}")

    # Initialiseer en start de engine
    engine = ScrapeEngine(
        input_file=args.input,
        output_dir=args.output,
        headless=args.headless
    )
    
    engine.run()

if __name__ == "__main__":
    main()
