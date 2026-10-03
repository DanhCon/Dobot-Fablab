#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BỘ ĐIỀU KHIỂN RAY TRƯỢT DOBOT MAGICIAN (SLIDING RAIL KIT) - CHUẨN TỌA ĐỘ
Hệ số chuẩn xác xác lập thực nghiệm:
  - Pulley GT2 20T: 80 xung / 1mm (PULSES_PER_MM = 80)
  - Động cơ: Stepper 1 (index 0)
  - Cảm biến hành trình: GP2 (EIO 14)
"""

import sys
import os
import time
import json
import struct
import argparse
import serial
import serial.tools.list_ports
import glob

PORT = "/dev/ttyUSB0"
RAIL_INDEX = 0             # Stepper 1 = index 0
PULSES_PER_MM = 80         # CHUẨN: 80 xung = 1mm (PULLEY GT2 20T)
RAIL_MAX_MM = 1000.0       # Hành trình ray tối đa 1000mm
DEFAULT_SPEED_MM_S = 40.0  # 40 mm/s (~3200 xung/s) - tốc độ chuẩn mượt mà
SWITCH_PIN = 14            # EIO 14 (Chân 3 cổng GP2)
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".rail_state.json")

def auto_detect_port():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    for p in ports:
        if "ttyUSB" in p or "ttyACM" in p:
            return p
    devs = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    return devs[-1] if devs else None

class DobotRail:
    def __init__(self, port=None):
        self.port = port or auto_detect_port() or PORT
        print(f"[+] Kết nối Dobot tại {self.port} (115200 baud)...")
        self.ser = serial.Serial(self.port, 115200, timeout=0.1)
        self.buf = bytearray()
        time.sleep(0.15)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.current_pos = self._load_state()
        self.init_queue()

        if self.current_pos is not None:
            print(f"[i] Vị trí ray hiện tại: {self.current_pos:.1f} mm ({self.current_pos/10:.1f} cm)")
        else:
            print("[i] Ray chưa xác định vị trí gốc (Gõ --home để về gốc 0mm).")

    def _load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    return json.load(f).get("current_pos", None)
            except Exception:
                pass
        return None

    def _save_state(self, pos):
        self.current_pos = pos
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({"current_pos": pos, "updated_at": time.time()}, f)
        except Exception:
            pass

    def _cs(self, payload: bytes) -> int:
        return (0x100 - (sum(payload) % 0x100)) % 0x100

    def _send(self, cmd_id: int, ctrl: int, params: bytes = b""):
        plen = 2 + len(params)
        payload = bytes([cmd_id, ctrl]) + params
        pkt = bytes([0xAA, 0xAA, plen]) + payload + bytes([self._cs(payload)])
        self.ser.write(pkt)
        self.ser.flush()

    def _read_pkt(self, want_id=None, timeout=0.08):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.ser.in_waiting:
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

    def init_queue(self):
        self._send(20, 1)   # ClearAllAlarmsState
        self._send(245, 1)  # SetQueuedCmdClear
        self._send(240, 1)  # SetQueuedCmdStartExec
        time.sleep(0.03)

    def is_switch_pressed(self) -> bool:
        """Đọc công tắc hành trình GP2 EIO14 (1 = Chạm, 0 = Nhả)"""
        self.ser.reset_input_buffer()
        self._send(133, 0, bytes([SWITCH_PIN]))
        rid, par = self._read_pkt(want_id=133, timeout=0.05)
        if par and len(par) >= 2 and par[0] == SWITCH_PIN:
            return (par[1] == 1)
        return False

    def stop(self):
        """Dừng khẩn cấp động cơ ray"""
        params = struct.pack("<B B i I", RAIL_INDEX, 0, 0, 0)
        self._send(20, 1)
        self._send(245, 1)
        self._send(240, 1)
        self._send(136, 3, params=params)
        self._send(240, 1)

    def jog_mm(self, dist_mm: float, speed_mm_s: float = DEFAULT_SPEED_MM_S):
        """
        Di chuyển ray dist_mm với tốc độ speed_mm_s (mm/s)
        dist_mm > 0: Chạy ra xa switch
        dist_mm < 0: Chạy về hướng switch
        """
        if abs(dist_mm) < 0.1:
            return True

        pulses = int(abs(dist_mm) * PULSES_PER_MM)
        safe_speed = max(5.0, min(80.0, speed_mm_s))
        speed_pulses = int(safe_speed * PULSES_PER_MM)

        # Hướng quay: -speed_pulses là chạy ra xa, +speed_pulses là lùi về switch
        dir_speed = -speed_pulses if dist_mm >= 0 else speed_pulses

        if dist_mm < 0 and self.is_switch_pressed():
            print("[-] Công tắc hành trình đang chạm, không thể lùi thêm!")
            return False

        params = struct.pack("<B B i I", RAIL_INDEX, 1, dir_speed, pulses)
        self._send(240, 1)
        self._send(136, 3, params=params)
        self._send(240, 1)

        t_duration = pulses / float(speed_pulses)
        t0 = time.time()
        interrupted = False

        if dist_mm < 0:
            while time.time() - t0 < t_duration:
                if self.is_switch_pressed():
                    self.stop()
                    print("\n[!] Chạm công tắc hành trình -> Phanh dừng ngay!")
                    interrupted = True
                    break
                time.sleep(0.05)
        else:
            time.sleep(t_duration + 0.15)

        if not interrupted and self.current_pos is not None:
            new_pos = max(0.0, min(RAIL_MAX_MM, self.current_pos + dist_mm))
            self._save_state(new_pos)

        return not interrupted

    def home(self, search_speed_mm_s: float = 30.0, max_search_mm: float = 1000.0):
        """Dò tìm gốc tọa độ 0.0mm"""
        print("=" * 70)
        print("           BẮT ĐẦU QUY TRÌNH HOMING RAY TRƯỢT")
        print("=" * 70)

        # 1. Nếu đang bị đè switch lúc bắt đầu
        if self.is_switch_pressed():
            print("[*] Công tắc đang bị đè, nhích nhẹ ra 20mm...")
            self.jog_mm(20.0, speed_mm_s=20.0)
            time.sleep(0.3)
            if self.is_switch_pressed():
                print("[-] Lỗi: Đã nhích ra nhưng công tắc vẫn báo chạm!")
                return False

        # 2. Dò tìm công tắc (bước 20mm)
        print("[*] Đang dò tìm công tắc hành trình...")
        step_mm = 20.0
        steps = int(max_search_mm / step_mm)
        found = False

        for i in range(steps):
            if self.is_switch_pressed():
                found = True
                break
            self.jog_mm(-step_mm, speed_mm_s=search_speed_mm_s)
            print(f"\r  -> Đang rà tìm... {(i+1)*step_mm:.0f}mm", end="", flush=True)

        if not found and not self.is_switch_pressed():
            print(f"\n[-] Quá hành trình {max_search_mm}mm mà không chạm switch!")
            self.stop()
            return False

        self.stop()
        print("\n[✓] Đã chạm công tắc hành trình!")
        time.sleep(0.3)

        # 3. Tinh chỉnh nhả switch (Fine Tuning)
        print("[*] Nhích nhẹ ra tìm điểm nhả chính xác (Fine Homing)...")
        for _ in range(40):
            if not self.is_switch_pressed():
                break
            self.jog_mm(1.0, speed_mm_s=8.0)
            time.sleep(0.05)

        self._save_state(0.0)
        print("=" * 70)
        print("🎉 [HOMING HOÀN TẤT] >>> Vị trí hiện tại: 0.0 mm (0.0 cm)!")
        print("=" * 70)
        return True

    def move_to_pos(self, target_mm: float, speed_mm_s: float = DEFAULT_SPEED_MM_S):
        """Di chuyển ray đến tọa độ tuyệt đối mm"""
        if self.current_pos is None:
            print("[-] Cần chạy Homing trước (--home) để xác định gốc 0mm!")
            return False

        if target_mm < 0.0 or target_mm > RAIL_MAX_MM:
            print(f"[-] Tọa độ mục tiêu {target_mm}mm nằm ngoài hành trình (0 - {RAIL_MAX_MM}mm)!")
            return False

        delta_mm = target_mm - self.current_pos
        if abs(delta_mm) < 0.2:
            print(f"[*] Ray đã ở sẵn vị trí: {target_mm:.1f} mm ({target_mm/10:.1f} cm).")
            return True

        print(f"[*] Di chuyển từ {self.current_pos:.1f} mm -> {target_mm:.1f} mm (Hành trình: {delta_mm:+.1f} mm / {delta_mm/10:+.1f} cm)...")
        ok = self.jog_mm(delta_mm, speed_mm_s=speed_mm_s)
        if ok:
            self._save_state(target_mm)
            print(f"[✓] Đã đến vị trí đích: {self.current_pos:.1f} mm ({self.current_pos/10:.1f} cm)")
        return ok

    def interactive_shell(self):
        """Bảng điều khiển tương tác trực tiếp"""
        print("\n" + "=" * 65)
        print("       BẢNG ĐIỀU KHIỂN RAY TƯƠNG TÁC (TRỰC TIẾP)")
        print("=" * 65)
        print("Lệnh hỗ trợ:")
        print("  home           : Về gốc 0mm")
        print("  <số_mm>        : Di chuyển tới tọa độ mm (vd: 100, 200, 50, 0)")
        print("  +<số_mm>       : Nhích tiến thêm mm (vd: +50, +10)")
        print("  -<số_mm>       : Nhích lùi bớt mm (vd: -50, -10)")
        print("  speed <v>      : Đổi tốc độ mm/s (khuyên dùng: 20 - 60)")
        print("  status         : Xem vị trí hiện tại")
        print("  stop           : Dừng khẩn cấp")
        print("  q / exit       : Thoát")
        print("-" * 65)

        speed = DEFAULT_SPEED_MM_S
        while True:
            try:
                pos_str = f"{self.current_pos:.1f}mm ({self.current_pos/10:.1f}cm)" if self.current_pos is not None else "Chưa Home"
                cmd = input(f"\n[Ray: {pos_str} | Speed: {speed:.0f}mm/s] > ").strip()
                if not cmd:
                    continue
                if cmd in ["exit", "quit", "q"]:
                    break
                elif cmd == "home":
                    self.home()
                elif cmd == "stop":
                    self.stop()
                    print("[!] Đã dừng ray.")
                elif cmd == "status":
                    sw = "CHẠM (1)" if self.is_switch_pressed() else "NHẢ (0)"
                    print(f"  * Tọa độ hiện tại: {pos_str}")
                    print(f"  * Công tắc hành trình (GP2 EIO14): {sw}")
                elif cmd.startswith("speed"):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        speed = max(5.0, min(80.0, float(parts[1])))
                        print(f"[+] Tốc độ mới: {speed:.1f} mm/s")
                elif cmd.startswith("+") or cmd.startswith("-"):
                    val = float(cmd)
                    print(f"[*] Nhích ray: {val:+.1f} mm ({val/10:+.1f} cm)...")
                    self.jog_mm(val, speed_mm_s=speed)
                else:
                    try:
                        val = float(cmd)
                        self.move_to_pos(val, speed_mm_s=speed)
                    except ValueError:
                        print("[-] Lệnh không hợp lệ. Ví dụ: 100, +50, home, exit.")
            except (KeyboardInterrupt, EOFError):
                break
        print("\n[+] Đã thoát.")

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

def main():
    parser = argparse.ArgumentParser(description="Bộ điều khiển ray trượt Dobot Magician (Stepper 1 + GP2 EIO14)")
    parser.add_argument("--home", action="store_true", help="Chạy quy trình dò tìm gốc tọa độ 0mm")
    parser.add_argument("--mm", type=float, default=None, help="Di chuyển đến tọa độ mm tuyệt đối")
    parser.add_argument("--jog", type=float, default=None, help="Nhích ray số mm tương đối (+ tiến, - lùi)")
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED_MM_S, help="Tốc độ di chuyển (mm/s), mặc định 40 mm/s")
    parser.add_argument("--status", action="store_true", help="Xem tọa độ hiện tại và trạng thái switch")
    parser.add_argument("--stop", action="store_true", help="Dừng khẩn cấp động cơ ray")
    parser.add_argument("-i", "--interactive", action="store_true", help="Mở giao diện điều khiển tương tác")
    args = parser.parse_args()

    rail = DobotRail()
    try:
        if args.stop:
            rail.stop()
            print("[!] Đã phát lệnh dừng động cơ ray.")
        elif args.home:
            ok = rail.home()
            if ok and args.mm is not None:
                rail.move_to_pos(args.mm, speed_mm_s=args.speed)
        elif args.mm is not None:
            rail.move_to_pos(args.mm, speed_mm_s=args.speed)
        elif args.jog is not None:
            rail.jog_mm(args.jog, speed_mm_s=args.speed)
        elif args.status:
            sw = "CHẠM (1)" if rail.is_switch_pressed() else "NHẢ (0)"
            pos_str = f"{rail.current_pos:.1f} mm ({rail.current_pos/10:.1f} cm)" if rail.current_pos is not None else "Chưa Home"
            print(f"\n[TRẠNG THÁI RAY]")
            print(f"  * Tọa độ hiện tại: {pos_str}")
            print(f"  * Công tắc hành trình (GP2 EIO14): {sw}\n")
        elif args.interactive:
            rail.interactive_shell()
        else:
            print("\nGợi ý các lệnh điều khiển:")
            print("  python3 dobot_rail_controller.py --home --mm 100     # Về gốc rồi chạy ra 100mm (10cm)")
            print("  python3 dobot_rail_controller.py --mm 200            # Chạy đến 200mm (20cm)")
            print("  python3 dobot_rail_controller.py -i                  # Mở chế độ tương tác trực tiếp")
    finally:
        rail.close()

if __name__ == "__main__":
    main()
