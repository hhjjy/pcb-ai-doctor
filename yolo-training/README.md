# YOLO PCB Component Detection Training

Train a YOLOv8n model to detect PCB components (IC, SOT-23, SOT-223, Module)
from chunk images, replacing/augmenting the Claude Vision API detection step.

## Data Source

From `origin/feature/yihua/demo-frontend-fix` branch, `scans/MMS_DEMO/`:
- **Back**: 15 chunks (3072x3072), 46 components (all IC)
- **Front**: 15 chunks (3072x3072), 28 components (IC/SOT-23/SOT-223/Module)
- Total: ~30 chunks, ~74 annotations

## Quick Start

```bash
# 1. Prepare dataset (extracts from git, converts to YOLO format)
python scripts/prepare_dataset.py

# 2. Train with Docker + GPU
docker compose up

# 3. Check results in runs/train/
```

## Class Mapping

| ID | Class   |
|----|---------|
| 0  | IC      |
| 1  | SOT-23  |
| 2  | SOT-223 |
| 3  | Module  |

## Notes

- Chunks are 3072x3072, YOLO resizes to 640x640 during training
- Using `chunks_nobg/` (background removed) for cleaner training signal
- YOLOv8n (nano) chosen for speed; upgrade to yolov8s if needed
- ~74 annotations is very small; consider augmentation or more data if mAP is low
