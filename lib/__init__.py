"""
3D Printer PCB Scanner Library

工作區座標系統：
  原點 (0, 0) = 平台座標 (20, 22)
  範圍：X: 0~200mm, Y: 0~198mm
"""

from .printer import PrinterController, find_serial_port
from .camera import Camera, CameraSource, calculate_focus_score
from .coordinates import (
    WORK_ORIGIN_X,
    WORK_ORIGIN_Y,
    WORK_MAX_X,
    WORK_MAX_Y,
    FOV_X,
    FOV_Y,
    STEPS_PER_MM_X,
    STEPS_PER_MM_Y,
    work_to_platform,
    platform_to_work,
    validate_work_area,
)
from .scan import (
    calculate_scan_positions,
    ScanCheckpoint,
    quick_autofocus,
)
from .paths import (
    DIR_META,
    DIR_FOCUS,
    DIR_SCAN,
    DIR_STITCH,
    DIR_DETECT,
    DIR_IDENTIFY,
    DIR_PINOUT,
    DIR_CHUNKS,
    DIR_CHUNKS_NOBG,
    FILE_PARAMS,
    FILE_CHECKPOINT,
    FILE_SCAN_LOG,
)

__all__ = [
    # printer
    'PrinterController',
    'find_serial_port',
    # camera
    'Camera',
    'CameraSource',
    'calculate_focus_score',
    # coordinates
    'WORK_ORIGIN_X',
    'WORK_ORIGIN_Y',
    'WORK_MAX_X',
    'WORK_MAX_Y',
    'FOV_X',
    'FOV_Y',
    'STEPS_PER_MM_X',
    'STEPS_PER_MM_Y',
    'work_to_platform',
    'platform_to_work',
    'validate_work_area',
    # scan
    'calculate_scan_positions',
    'ScanCheckpoint',
    'quick_autofocus',
    # paths
    'DIR_META',
    'DIR_FOCUS',
    'DIR_SCAN',
    'DIR_STITCH',
    'DIR_DETECT',
    'DIR_IDENTIFY',
    'DIR_PINOUT',
    'DIR_CHUNKS',
    'DIR_CHUNKS_NOBG',
    'FILE_PARAMS',
    'FILE_CHECKPOINT',
    'FILE_SCAN_LOG',
]
