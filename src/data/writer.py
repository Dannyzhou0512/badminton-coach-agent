import json
import os
from datetime import datetime, timezone


SCHEMA_VERSION = "0.1.0"


class JsonlDetectionWriter:
    """Write detection records incrementally as JSON Lines."""

    def __init__(self, output_path):
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        self._file = open(output_path, "w", encoding="utf-8")

    def write(self, record):
        self._file.write(json.dumps(record, ensure_ascii=False) + "\n")

    def close(self):
        self._file.close()


def write_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_metadata(model_name, model_version, video_path, config):
    return {
        "schema_version": SCHEMA_VERSION,
        "model_name": model_name,
        "model_version": model_version,
        "video_path": os.path.abspath(video_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": config,
    }