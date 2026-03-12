"""
座標系統轉換模組

工作區座標 (Work Area Coordinates) - 使用者介面
  原點 (0, 0) = 平台座標 (20, 20)
  範圍：X: 0~200mm, Y: 0~200mm

平台座標 (Printer Coordinates) - 內部 G-code 使用
  原點 (0, 0) = 3D 列印機歸零點
  範圍：X: 0~220mm, Y: 0~220mm
"""

# 工作區原點在平台座標系的位置
WORK_ORIGIN_X = 20
WORK_ORIGIN_Y = 20

# 工作區最大範圍
WORK_MAX_X = 200
WORK_MAX_Y = 200

# 平台最大範圍
PLATFORM_MAX_X = 220
PLATFORM_MAX_Y = 220

# 步進馬達校準值 (steps/mm)
# 原廠預設 80，經方格墊校準後修正
# 詳見 docs/steps_per_mm_calibration.md
STEPS_PER_MM_X = 83.50
STEPS_PER_MM_Y = 83.50

# 視野大小 (Field of View)
FOV_X = 15  # mm (寬度)
FOV_Y = 25  # mm (高度)


def work_to_platform(work_x, work_y):
    """
    工作區座標 → 平台座標

    Args:
        work_x: 工作區 X 座標 (mm)
        work_y: 工作區 Y 座標 (mm)

    Returns:
        (platform_x, platform_y) 平台座標元組
    """
    platform_x = work_x + WORK_ORIGIN_X
    platform_y = work_y + WORK_ORIGIN_Y
    return platform_x, platform_y


def platform_to_work(platform_x, platform_y):
    """
    平台座標 → 工作區座標

    Args:
        platform_x: 平台 X 座標 (mm)
        platform_y: 平台 Y 座標 (mm)

    Returns:
        (work_x, work_y) 工作區座標元組
    """
    work_x = platform_x - WORK_ORIGIN_X
    work_y = platform_y - WORK_ORIGIN_Y
    return work_x, work_y


def validate_work_area(x_min, x_max, y_min, y_max):
    """
    驗證工作區範圍是否有效

    Args:
        x_min, x_max: X 軸範圍 (工作區座標)
        y_min, y_max: Y 軸範圍 (工作區座標)

    Raises:
        ValueError: 如果範圍無效
    """
    if x_min < 0 or x_max > WORK_MAX_X:
        raise ValueError(f"X 範圍超出工作區 (0~{WORK_MAX_X}mm): {x_min}~{x_max}")
    if y_min < 0 or y_max > WORK_MAX_Y:
        raise ValueError(f"Y 範圍超出工作區 (0~{WORK_MAX_Y}mm): {y_min}~{y_max}")
    if x_min >= x_max:
        raise ValueError(f"X 範圍無效: {x_min} >= {x_max}")
    if y_min >= y_max:
        raise ValueError(f"Y 範圍無效: {y_min} >= {y_max}")


def validate_platform_coords(platform_x, platform_y):
    """
    驗證平台座標是否有效

    Args:
        platform_x: 平台 X 座標 (mm)
        platform_y: 平台 Y 座標 (mm)

    Raises:
        ValueError: 如果座標超出範圍
    """
    if platform_x < 0 or platform_x > PLATFORM_MAX_X:
        raise ValueError(f"平台 X 座標超出範圍 (0~{PLATFORM_MAX_X}mm): {platform_x}")
    if platform_y < 0 or platform_y > PLATFORM_MAX_Y:
        raise ValueError(f"平台 Y 座標超出範圍 (0~{PLATFORM_MAX_Y}mm): {platform_y}")
