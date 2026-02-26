from pathlib import Path
import yaml

class RetrieverConfig:
        def __init__(self, path: str):
            config_path = Path(path)
            with open(config_path, "r", encoding="utf-8") as f:
                self.config_dict = yaml.safe_load(f)