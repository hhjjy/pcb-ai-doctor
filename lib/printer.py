"""
3D 列印機控制模組

使用 M400 指令等待移動完成，取代固定的 time.sleep()
"""

import serial
import time
import glob


def find_serial_port():
    """自動尋找串口設備"""
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    if ports:
        return ports[0]
    raise Exception("找不到串口設備")


class PrinterController:
    """3D 列印機控制器"""

    def __init__(self, safe_z=85, port=None, calibrate=True):
        """
        初始化列印機控制器

        Args:
            safe_z: 安全高度 (mm)，移動 XY 前先升高到此高度
            port: 串口路徑，None 則自動偵測
            calibrate: 連線後自動套用 steps/mm 校準值
        """
        if port is None:
            port = find_serial_port()
        print(f"連接串口: {port}")
        self.ser = serial.Serial(port, 115200, timeout=5)
        self.safe_z = safe_z
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.homed = False
        time.sleep(2)  # 等待連線穩定

        if calibrate:
            self._apply_calibration()

    def _apply_calibration(self):
        """套用 steps/mm 校準值"""
        from .coordinates import STEPS_PER_MM_X, STEPS_PER_MM_Y
        cmd = f'M92 X{STEPS_PER_MM_X:.2f} Y{STEPS_PER_MM_Y:.2f}'
        self.send_gcode(cmd)

    def send_gcode(self, cmd, wait_time=0.1):
        """
        發送 G-code 指令

        Args:
            cmd: G-code 指令
            wait_time: 發送後等待時間 (秒)
        """
        self.ser.reset_input_buffer()
        self.ser.write((cmd + '\n').encode())
        time.sleep(wait_time)
        while True:
            line = self.ser.readline().decode(errors='ignore').strip()
            if 'ok' in line.lower() or not line:
                break

    def wait_for_moves(self):
        """等待所有移動完成 (M400)"""
        self.send_gcode('M400')

    def home(self):
        """歸零 (G28)"""
        print("歸零中...")
        self.send_gcode('G28')
        time.sleep(20)  # 歸零需要較長時間
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.homed = True
        print("歸零完成")

    def move_z(self, z, speed=1000, wait=True):
        """
        移動 Z 軸

        Args:
            z: 目標高度 (mm)
            speed: 移動速度 (mm/min)
            wait: 是否等待移動完成
        """
        self.send_gcode(f'G1 Z{z} F{speed}')
        if wait:
            self.wait_for_moves()
        self.position["z"] = z

    def move_xy(self, x, y, speed=3000, wait=True):
        """
        移動 XY 軸

        Args:
            x: 目標 X 座標 (mm)
            y: 目標 Y 座標 (mm)
            speed: 移動速度 (mm/min)
            wait: 是否等待移動完成
        """
        self.send_gcode(f'G1 X{x} Y{y} F{speed}')
        if wait:
            self.wait_for_moves()
        self.position["x"] = x
        self.position["y"] = y

    def safe_move_xy(self, x, y, speed=3000):
        """
        安全移動 XY - 先升高 Z 再移動

        Args:
            x: 目標 X 座標 (mm)
            y: 目標 Y 座標 (mm)
            speed: 移動速度 (mm/min)
        """
        self.move_z(self.safe_z)
        self.move_xy(x, y, speed)

    def jog(self, axis: str, distance: float, speed: int = 3000):
        """Relative move on a single axis. Returns new position dict."""
        self.send_gcode("G91")  # relative mode
        if axis == "z":
            self.send_gcode(f"G1 Z{distance} F{min(speed, 1000)}")
        else:
            self.send_gcode(f"G1 {axis.upper()}{distance} F{speed}")
        self.send_gcode("G90")  # back to absolute
        self.wait_for_moves()
        self.position[axis] += distance
        return dict(self.position)

    def close(self):
        """關閉串口連線"""
        self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
