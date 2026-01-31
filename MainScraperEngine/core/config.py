"""
╔════════════════════════════════════════════════════════════════╗
║  Configuration Loader - Load vendor YAML configs              ║
╚════════════════════════════════════════════════════════════════╝
"""
import yaml
from pathlib import Path
from typing import Dict


def load_configs(config_file: Path = None) -> Dict:
    """
    Laad vendor configuraties uit YAML.
    
    Args:
        config_file: Pad naar YAML config (optioneel, default = Vendor_YML.yaml)
    
    Returns:
        Dict: Vendor configuraties gesorteerd op prioriteit
    """
    if config_file is None:
        config_file = Path(__file__).parent.parent / "Vendor_YML.yaml"
    
    if not config_file.exists():
        raise FileNotFoundError(f"❌ Config bestand niet gevonden: {config_file}")
    
    with open(config_file, "r", encoding="utf-8") as f:
        configs = yaml.safe_load(f)
    
    # Sorteer op prioriteit (lager = eerder proberen)
    sorted_configs = dict(sorted(
        configs.items(), 
        key=lambda x: x[1].get("priority", 100)
    ))
    
    return sorted_configs
