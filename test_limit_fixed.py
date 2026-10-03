#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHƯƠNG TRÌNH THEO DÕI TÍN HIỆU CẢM BIẾN RAY TRƯỢT DOBOT MAGICIAN
Chuẩn giao thức: ID 131 (Cấu hình IO) + ID 133 (Đọc Digital Input)
Tập trung theo dõi các chân:
- GP2: EIO13, EIO14, EIO15
- SW / Communication: EIO19, EIO20
- GP1: EIO11, EIO12
"""

import sys
import time
import glob
import serial
import serial.tools.list_ports

def auto_detect_port():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    for p in ports:
        if "ttyUSB" in p or "ttyACM" in p:
            return p
    devs = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    return devs[-1] if devs else None

class DobotLimitTester:
    def __init__(self, port=None):
        self.port = port or auto_detect_port()
        if not self.port:
            raise ConnectionError("Không tìm thấy cổng USB Dobot!")
        print(f"[+] Kết nối Dobot tại {self.port} (115200)...")
        self.ser = serial.Serial(self.port, 115200, timeout=0.2)
        self.buf = bytearray()
        time.sleep(0.3)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.clear_alarms()

    def _cs(self, payload: bytes) -> int:
        return (0x100 - (sum(payload) % 0x100)) % 0x100

    def _send(self, cmd_id: int, ctrl: int, params: bytes = b""):
        plen = 2 + len(params)
        payload = bytes([cmd_id, ctrl]) + params
        pkt = bytes([0xAA, 0xAA, plen]) + payload + bytes([self._cs(payload)])
        self.ser.write(pkt)
        self.ser.flush()

    def _read_pkt(self, want_id=None, timeout=0.15):
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

    def clear_alarms(self):
        self._send(20, 1)
        self._send(245, 1)
        self._send(240, 1)
        time.sleep(0.05)

    def set_io_mode(self, pin: int, mode: int = 3):
        # mode 3: DI (Digital Input), mode 5: DI Pull-Up
        self.ser.reset_input_buffer()
        self._send(131, 1, bytes([pin, mode]))
        time.sleep(0.01)

    def get_io_di(self, pin: int):
        self.ser.reset_input_buffer()
        self._send(133, 0, bytes([pin]))
        rid, par = self._read_pkt(want_id=133, timeout=0.08)
        if par and len(par) >= 2 and par[0] == pin:
            return par[1]
        return None

    def monitor(self, pins=[13, 14, 15, 19, 20, 11, 12]):
        print("\n[*] Cấu hình chế độ Digital Input cho các chân:", pins)
        for p in pins:
            self.set_io_mode(p, mode=3)
        time.sleep(0.1)

        print("=" * 80)
        print(" BẮT ĐẦU THEO DÕI TÍN HIỆU CẢM BIẾN (LẤY TAY HOẶC GIẤY CHE / BẤM CẢM BIẾN)")
        print("=" * 80)
        print("Nhấn Ctrl + C để dừng.")
        print("-" * 80)

        prev = {}
        for p in pins:
            prev[p] = self.get_io_di(p)

        loop_cnt = 0
        try:
            while True:
                curr = {}
                changes = []
                for p in pins:
                    v = self.get_io_di(p)
                    curr[p] = v
                    if v is not None and prev.get(p) is not None and v != prev[p]:
                        changes.append((p, prev[p], v))
                    prev[p] = v

                if changes:
                    print("\a", end="")
                    for p, old_v, new_v in changes:
                        lbl = f"EIO {p}"
                        if p in [13, 14, 15]:
                            lbl += " (GP2 trên forearm)"
                        elif p in [11, 12]:
                            lbl += " (GP1 trên forearm)"
                        elif p in [19, 20]:
                            lbl += " (SW/Comm ở đế robot)"
                        print(f"\n⚡ [PHÁT HIỆN TÍN HIỆU ĐỔI] >>> {lbl}: {old_v} -> {new_v}")
                    print("-" * 80)

                line = " | ".join([f"EIO{p}: {curr.get(p, '-')}" for p in pins])
                print(f"\r[T={loop_cnt*0.1:.1f}s] {line}    ", end="", flush=True)
                loop_cnt += 1
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[+] Dừng kiểm tra.")
        finally:
            self.ser.close()

if __name__ == "__main__":
    t = DobotLimitTester()
    t.monitor()
