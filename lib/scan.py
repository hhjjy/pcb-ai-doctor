"""
掃描功能模組

包含掃描路徑計算、checkpoint 功能、自動對焦
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional

from .coordinates import FOV_X, FOV_Y, work_to_platform


# 安全偏移量，確保邊緣不漏拍
SAFETY_MARGIN = 3  # mm


@dataclass
class ScanPosition:
    """單一掃描位置"""
    index: int
    platform_x: float
    platform_y: float
    work_x: float
    work_y: float


@dataclass
class ScanCheckpoint:
    """掃描進度 checkpoint"""
    last_index: int = 0
    last_x: float = 0
    last_y: float = 0
    timestamp: str = ""
    params: dict = field(default_factory=dict)

    def save(self, filepath):
        """儲存 checkpoint 到檔案"""
        self.timestamp = datetime.now().isoformat()
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath):
        """從檔案載入 checkpoint"""
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)


def calculate_scan_positions(
    pcb_x_min: float,
    pcb_x_max: float,
    pcb_y_min: float,
    pcb_y_max: float,
    overlap: float = 0.3,
    x_step: float = None,
    y_step: float = None,
    use_work_coords: bool = True
) -> Tuple[List[ScanPosition], dict]:
    """
    計算掃描位置列表

    根據 PCB 涵蓋範圍自動計算攝影機拍攝位置。
    攝影機視野左下角 = 攝影機位置，確保 PCB 完整涵蓋。

    Args:
        pcb_x_min, pcb_x_max: PCB 的 X 範圍 (工作區座標)
        pcb_y_min, pcb_y_max: PCB 的 Y 範圍 (工作區座標)
        overlap: 重疊率 (0~1)，預設 0.3 (30%)
        x_step: X 步進距離 (mm)，None 則自動計算
        y_step: Y 步進距離 (mm)，None 則自動計算
        use_work_coords: 輸入座標是否為工作區座標

    Returns:
        (positions, info) 元組：
        - positions: ScanPosition 列表
        - info: 包含計算資訊的字典
    """
    # 計算步進距離
    if x_step is None:
        x_step = FOV_X * (1 - overlap)
    if y_step is None:
        y_step = FOV_Y * (1 - overlap)

    # 轉換為平台座標（如果輸入是工作區座標）
    if use_work_coords:
        cam_x_start, cam_y_start = work_to_platform(pcb_x_min, pcb_y_min)
        pcb_x_max_platform, pcb_y_max_platform = work_to_platform(pcb_x_max, pcb_y_max)
    else:
        cam_x_start, cam_y_start = pcb_x_min, pcb_y_min
        pcb_x_max_platform, pcb_y_max_platform = pcb_x_max, pcb_y_max

    # 計算攝影機結束位置（確保 PCB 右上角被涵蓋）
    cam_x_end = pcb_x_max_platform - FOV_X + SAFETY_MARGIN
    cam_y_end = pcb_y_max_platform - FOV_Y + SAFETY_MARGIN

    # 如果範圍太小（小於一個 FOV），只拍一張
    if cam_x_end < cam_x_start:
        cam_x_end = cam_x_start
    if cam_y_end < cam_y_start:
        cam_y_end = cam_y_start

    # 生成位置列表
    positions = []
    index = 0

    # 預先計算座標原點偏移
    origin_x, origin_y = work_to_platform(0, 0)

    # 生成 Y 軸位置（均勻間距，自動判斷末端是否多走一步）
    n_y_float = (cam_y_end - cam_y_start) / y_step
    n_y = int(n_y_float)
    if n_y_float - n_y > 0.5:
        n_y += 1
    y_positions = [round(cam_y_start + i * y_step, 1) for i in range(n_y + 1)]

    for y in y_positions:
        # 生成 X 軸位置（均勻間距，自動判斷末端是否多走一步）
        n_x_float = (cam_x_end - cam_x_start) / x_step
        n_x = int(n_x_float)
        if n_x_float - n_x > 0.5:
            n_x += 1
        x_positions = [round(cam_x_start + i * x_step, 1) for i in range(n_x + 1)]

        for x in x_positions:
            work_x = x - origin_x
            work_y = y - origin_y

            positions.append(ScanPosition(
                index=index,
                platform_x=x,
                platform_y=y,
                work_x=round(work_x, 1),
                work_y=round(work_y, 1)
            ))
            index += 1

    # 計算資訊
    x_count = len(set(p.platform_x for p in positions))
    y_count = len(set(p.platform_y for p in positions))

    info = {
        'pcb_area': {
            'work': {'x_min': pcb_x_min, 'x_max': pcb_x_max, 'y_min': pcb_y_min, 'y_max': pcb_y_max},
            'platform': {
                'x_min': work_to_platform(pcb_x_min, 0)[0] if use_work_coords else pcb_x_min,
                'x_max': work_to_platform(pcb_x_max, 0)[0] if use_work_coords else pcb_x_max,
                'y_min': work_to_platform(0, pcb_y_min)[1] if use_work_coords else pcb_y_min,
                'y_max': work_to_platform(0, pcb_y_max)[1] if use_work_coords else pcb_y_max,
            }
        },
        'camera_range': {
            'x_start': cam_x_start,
            'x_end': cam_x_end,
            'y_start': cam_y_start,
            'y_end': cam_y_end,
        },
        'step': {'x': x_step, 'y': y_step},
        'overlap': overlap,
        'fov': {'x': FOV_X, 'y': FOV_Y},
        'grid': {'x_count': x_count, 'y_count': y_count},
        'total_images': len(positions),
    }

    return positions, info


def quick_autofocus(printer, camera, z_center=72, z_range=5, z_step=1, ascending=True):
    """
    快速自動對焦（單向掃描）

    Args:
        printer: PrinterController 實例
        camera: Camera 實例
        z_center: 對焦中心高度 (mm)
        z_range: 對焦搜尋範圍 ±(mm)
        z_step: Z 步進 (mm)
        ascending: True=由下往上, False=由上往下

    Returns:
        (best_z, best_score, best_frame, end_z) 元組
    """
    best_z, best_score, best_frame = z_center, 0, None
    z_min, z_max = z_center - z_range, z_center + z_range

    if ascending:
        z_values = [z_min + i * z_step for i in range(int((z_max - z_min) / z_step) + 1)]
        end_z = z_max
    else:
        z_values = [z_max - i * z_step for i in range(int((z_max - z_min) / z_step) + 1)]
        end_z = z_min

    for z in z_values:
        printer.move_z(z, speed=800)
        frame, score = camera.capture_with_score()
        if frame is not None and score > best_score:
            best_score, best_z, best_frame = score, z, frame.copy()

    return best_z, best_score, best_frame, end_z
