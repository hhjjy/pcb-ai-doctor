"""Per-scan output directory and file name constants.

New numbered-prefix layout (v2):
    scans/{board}/
    ├── 0_meta/          params.json, checkpoint.json, scan_log.csv
    ├── 1_focus/         autofocus data
    ├── 2_scan/          y_*/ tile images
    ├── 3_stitch/        stitched output
    ├── 4_detect/        chunks, detection results
    ├── 5_identify/      crops, datasheets
    └── 6_pinout/        SVG overlays, pinout pages
"""

# --- directory names ---
DIR_META = "0_meta"
DIR_FOCUS = "1_focus"
DIR_SCAN = "2_scan"
DIR_STITCH = "3_stitch"
DIR_DETECT = "4_detect"
DIR_IDENTIFY = "5_identify"
DIR_PINOUT = "6_pinout"
DIR_CHUNKS = "chunks"
DIR_CHUNKS_NOBG = "chunks_nobg"

# --- file names ---
FILE_PARAMS = "params.json"
FILE_CHECKPOINT = "checkpoint.json"
FILE_SCAN_LOG = "scan_log.csv"
