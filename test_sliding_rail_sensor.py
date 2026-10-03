#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIỂM THỬ TÍN HIỆU CẢM BIẾN RAY TRƯỢT DOBOT (SLIDING RAIL KIT)
Cổng kết nối: Cảm biến quang chữ U cắm vào GP2 | Động cơ bước cắm vào Stepper 1.

Cách dùng:
  python3 test_sliding_rail_sensor.py                 # Chạy quét liên tục tín hiệu GP2 (Mặc định)
  python3 test_sliding_rail_sensor.py --pullup        # Chạy quét với điện trở kéo lên Pull-Up (mode 5)
  python3 test_sliding_rail_sensor.py --jog 10        # Nhích thử ray 10mm trên Stepper 1
  python3 test_sliding_rail_sensor.py --jog -10       # Nhích lui ray 10mm về hướng cảm biến
"""

import sys
import time
import struct
import glob
import argparse

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[-] Lỗi: Cần cài đặt thư viện pyserial: pip install pyserial")
    sys.exit(1)


PULSES_PER_MM = 200
RAIL_INDEX = 0  # Stepper 1 trên Dobot Magician


def auto_detect_port():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    for p in ports:
        if "ttyUSB" in p or "ttyACM" in p:
            return p
    devs = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    return devs[-1] if devs else None


class DobotRailSensorTester:
    def __init__(self, port=None, pullup=False):
        self.port = port or auto_detect_port()
        self.pullup = pullup
        if not self.port:
            raise ConnectionError("Không tìm thấy cổng USB Dobot (/dev/ttyUSB* hoặc /dev/ttyACM*)!")
        
        print(f"[+] Đang kết nối Dobot Magician tại: {self.port} (Baudrate 115200)...")
        self.ser = serial.Serial(
            port=self.port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.3
        )
        self.buf = bytearray()
        time.sleep(0.3)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        # 1. Reset lỗi và mở hàng đợi lệnh
        self.clear_alarms()
        
        # 2. Đọc Pose để kiểm tra kết nối
        pose = self.get_pose()
        if pose:
            print(f"[✓] Kết nối Dobot thành công! Tọa độ hiện tại: X={pose[0]:.1f}, Y={pose[1]:.1f}, Z={pose[2]:.1f}, R={pose[3]:.1f}")
        else:
            print("[!] Cảnh báo: Không đọc được Pose, nhưng vẫn tiếp tục kiểm tra.")

        # 3. Khởi tạo cấu hình các chân GP2
        self.init_gp2_pins()

    def _cs(self, payload: bytes) -> int:
        return (0x100 - (sum(payload) % 0x100)) % 0x100

    def _send(self, cmd_id: int, ctrl: int, params: bytes = b""):
        plen = 2 + len(params)
        payload = bytes([cmd_id, ctrl]) + params
        pkt = bytes([0xAA, 0xAA, plen]) + payload + bytes([self._cs(payload)])
        self.ser.write(pkt)
        self.ser.flush()

    def _read_pkt(self, want_id=None, timeout=0.12):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.ser.in_waiting > 0:
                self.buf.extend(self.ser.read(self.ser.in_waiting))
            while True:
                idx = self.buf.find(b"\xAA\xAA")
                if idx == -1:
                    self.buf.clear()
                    break
                if len(self.buf) < idx + 4:
                    break
                ln = self.buf[idx + 2]
                tot = 3 + ln + 1
                if len(self.buf) < idx + tot:
                    break
                pkt = self.buf[idx : idx + tot]
                self.buf = self.buf[idx + tot :]
                rid = pkt[3]
                par = pkt[5:-1]
                if want_id is None or rid == want_id:
                    return rid, par
            time.sleep(0.002)
        return None, None

    def clear_alarms(self):
        self._send(20, 1)   # ClearAllAlarmsState
        self._send(245, 1)  # SetQueuedCmdClear
        self._send(240, 1)  # SetQueuedCmdStartExec
        time.sleep(0.05)

    def get_pose(self):
        self._send(10, 0)
        rid, par = self._read_pkt(want_id=10, timeout=0.2)
        if par and len(par) >= 32:
            return struct.unpack("<8f", par[:32])
        return None

    def set_io_multiplexing(self, address: int, mode: int):
        """
        SetIOMultiplexing (ID 131)
        mode: 3=IOFunctionDI (Digital Input), 4=IOFunctionADC, 5=IOFunctionDIPU (Pull-Up)
        """
        self.ser.reset_input_buffer()
        self._send(131, 1, bytes([address, mode]))
        time.sleep(0.015)

    def get_io_di(self, address: int):
        """
        GetIODI (ID 132): Đọc mức logic Digital Input (0 hoặc 1).
        """
        self.ser.reset_input_buffer()
        self._send(132, 0, bytes([address]))
        rid, par = self._read_pkt(want_id=132, timeout=0.08)
        if par and len(par) >= 2:
            return par[1]  # 0 hoặc 1
        return None

    def get_io_adc(self, address: int):
        """
        GetIOADC (ID 134): Đọc giá trị điện áp Analog ADC (0 - 4095).
        """
        self.ser.reset_input_buffer()
        self._send(134, 0, bytes([address]))
        rid, par = self._read_pkt(want_id=134, timeout=0.08)
        if par and len(par) >= 3:
            return struct.unpack("<H", par[1:3])[0]
        return None

    def set_infrared_sensor(self, enable: bool = True, port: int = 1, version: int = 1):
        """
        SetInfraredSensor (ID 138): Bật cảm biến hồng ngoại trên cổng GP (port 1 = GP2).
        """
        self._send(138, 1, bytes([1 if enable else 0, port, version]))
        time.sleep(0.02)

    def get_infrared_sensor(self, port: int = 1):
        """
        GetInfraredSensor (ID 139): Đọc giá trị cảm biến quang.
        """
        self.ser.reset_input_buffer()
        self._send(139, 0, bytes([port]))
        rid, par = self._read_pkt(want_id=139, timeout=0.08)
        if par and len(par) >= 1:
            return par[0]
        return None

    def init_gp2_pins(self):
        mode_code = 5 if self.pullup else 3
        mode_name = "Digital Input + Pull-Up (mode 5)" if self.pullup else "Digital Input (mode 3)"
        print(f"\n[*] Đang cấu hình các chân cổng GP2 sang chế độ: {mode_name}...")
        for pin in [13, 14, 15, 2]:
            self.set_io_multiplexing(pin, mode_code)
        
        try:
            self.set_infrared_sensor(enable=True, port=1, version=1)
        except Exception:
            pass
        print(f"[✓] Đã cấu hình xong chân GP2 (EIO13, EIO14, EIO15, Pin 2).")

    def jog_stepper1(self, dist_mm: float, speed: int = 4000):
        """
        Nhích thử động cơ Stepper 1 (Ray trượt)
        dist_mm > 0: chạy ra xa | dist_mm < 0: chạy về hướng cảm biến đầu ray
        """
        pulses = int(abs(dist_mm) * PULSES_PER_MM)
        dir_speed = -int(speed) if dist_mm >= 0 else int(speed)
        print(f"[*] Nhích ray Stepper 1: {dist_mm:+.1f}mm (~{pulses} xung, tốc độ {dir_speed} xung/s)...")
        self.clear_alarms()
        params = struct.pack("<B B i I", RAIL_INDEX, 1, dir_speed, pulses)
        self._send(240, 1)
        self._send(136, 3, params=params)
        wait_s = max(0.8, abs(dist_mm) / 50.0 + 0.5)
        time.sleep(wait_s)
        print("[✓] Hoàn thành lệnh nhích ray Stepper 1.")

    def run_live_monitor(self):
        print("=" * 80)
        print("          BẮT ĐẦU THEO DÕI TÍN HIỆU CẢM BIẾN RAY TRƯỢT (GP2)")
        print("=" * 80)
        print("HƯỚNG DẪN KIỂM TRA:")
        print(" 1. Cảm biến quang chữ U ở đầu ray có 1 khe hở hồng ngoại.")
        print(" 2. Lấy 1 mảnh giấy hoặc ngón tay che vào khe chữ U của cảm biến.")
        print(" 3. Sau đó rút giấy ra (nhả cảm biến).")
        print(" 4. Quan sát các giá trị bên dưới xem chân nào thay đổi giữa 0 <-> 1:")
        print("    - GP2 (EIO 13) | GP2 (EIO 14) | GP2 (EIO 15) | GP2 (Chân 2)")
        print("    - Nhấn Ctrl + C để dừng kiểm tra.")
        print("-" * 80)

        pins = [13, 14, 15, 2]
        labels = {
            13: "GP2 (EIO13)",
            14: "GP2 (EIO14)",
            15: "GP2 (EIO15)",
             2: "GP2 (Pin 2)"
        }

        prev_di = {}
        for p in pins:
            prev_di[p] = self.get_io_di(p)

        loop_count = 0
        try:
            while True:
                current_di = {}
                state_changes = []

                for p in pins:
                    val = self.get_io_di(p)
                    current_di[p] = val
                    if val is not None and prev_di.get(p) is not None and val != prev_di[p]:
                        state_changes.append((labels[p], prev_di[p], val))
                    prev_di[p] = val

                # Đọc thêm giá trị ADC trên chân 13, 14, 15
                adc_13 = self.get_io_adc(13)
                adc_14 = self.get_io_adc(14)
                adc_15 = self.get_io_adc(15)

                # Đọc thêm Infrared Sensor GP2
                ir_val = self.get_infrared_sensor(port=1)

                # Nếu có sự kiện thay đổi trạng thái, in cảnh báo nổi bật
                if state_changes:
                    print("\a", end="") # Tiếng beep cảnh báo
                    for lbl, old_v, new_v in state_changes:
                        status_str = "🔴 [ĐÃ KÍCH HOẠT / CHE LẠI]" if new_v == 1 else "🟢 [ĐÃ NHẢ RA / THÔNG THOÁNG]"
                        print(f"\n⚡ >>> PHÁT HIỆN TÍN HIỆU THAY ĐỔI TẠI {lbl}: {old_v} -> {new_v} | {status_str}")
                    print("-" * 80)

                # Hiển thị thanh trạng thái thời gian thực
                status_parts = []
                for p in pins:
                    v = current_di[p]
                    v_str = str(v) if v is not None else "-"
                    tag = "🔴 ON" if v == 1 else "⚪ OFF"
                    status_parts.append(f"{labels[p]}: {v_str} ({tag})")

                adc_str = f"ADC13={adc_13 or 0} ADC14={adc_14 or 0} ADC15={adc_15 or 0}"
                ir_str = f"IR_GP2={ir_val if ir_val is not None else '-'}"
                
                line = " | ".join(status_parts) + f" | {adc_str} | {ir_str}"
                print(f"\r[T={loop_count*0.2:.1f}s] {line}", end="", flush=True)

                loop_count += 1
                time.sleep(0.2)

        except KeyboardInterrupt:
            print("\n\n[+] Đã dừng kiểm tra theo yêu cầu người dùng.")
        finally:
            self.close()

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[+] Đã đóng kết nối serial an toàn.")


def main():
    parser = argparse.ArgumentParser(description="Kiểm thử tín hiệu cảm biến ray trượt Dobot Sliding Rail Kit (GP2 & Stepper 1)")
    parser.add_argument("--pullup", action="store_true", help="Kích hoạt điện trở kéo lên Pull-Up (mode 5)")
    parser.add_argument("--jog", type=float, default=None, help="Nhích thử ray Stepper 1 số mm (ví dụ: --jog 10 hoặc --jog -10)")
    args = parser.parse_args()

    print("=" * 80)
    print("        DOBOT MAGICIAN - TEST TÍN HIỆU CẢM BIẾN RAY TRƯỢT (GP2)")
    print("================================================================================")
    try:
        tester = DobotRailSensorTester(pullup=args.pullup)
        if args.jog is not None:
            tester.jog_stepper1(args.jog)
        else:
            tester.run_live_monitor()
    except Exception as e:
        print(f"\n[-] Lỗi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
