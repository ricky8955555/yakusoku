import os
from pathlib import Path

working_dir = Path(os.getcwd())

module_path = Path(__file__).parent / "modules"
data_path = working_dir / "data"
config_path = working_dir / "config"
