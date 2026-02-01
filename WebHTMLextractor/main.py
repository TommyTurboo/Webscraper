import argparse
import sys
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
    parser.add_argument('--input', default=str(default_input), help='Path to URL list')
    parser.add_argument('--output', default=str(default_output), help='Output directory')
    
    args = parser.parse_args()

    # Initialiseer en start de engine
    engine = ScrapeEngine(
        input_file=args.input,
        output_dir=args.output,
        headless=args.headless
    )
    
    engine.run()

if __name__ == "__main__":
    main()
