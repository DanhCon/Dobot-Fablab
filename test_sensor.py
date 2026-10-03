#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test tin hieu cam bien ray Dobot Magician - ban sua dung.
Ma dung theo thu vien chuan pydobot: ID 131 SET_GET_EIO, ctrl 0, param [address].
Ban truoc dung nham ID 132 nen chi in ra dia chi 1..8.

Dung:
  python3 test_sensor.py
  -> de xe giua ray, che/mo mat cam bien dau, cot nao doi 0<->1 la cong do.
  -> Ctrl+C de thoat.
"""

import sys
import time
import glob

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[-] Can pyserial: pip install pyserial")
    sys.exit(1)


def auto_port():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    for p in ports:
        if "ttyUSB" in p or "ttyACM" in p:
            return p
    devs = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    return devs[-1] if devs else None


class SensorTester:
    def __init__(self, port=None):
        self.port = port or auto_port()
        if not self.port:
            raise ConnectionError("Khong thay cong USB Dobot!")
        print(f"[+] Noi Dobot tai {self.port}")
        self.ser = serial.Serial(port=self.port, baudrate=115200, timeout=0.5)
        self.buf = bytearray()
        time.sleep(0.3)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self._send(20, 1)
        self._send(245, 1)
        self._send(240, 1)

    def _cs(self, payload: bytes) -> int:
        return (0x100 - (sum(payload) % 0x100)) % 0x100

    def _send(self, id: int, ctrl: int, params: bytes = b""):
        plen = 2 + len(params)
        payload = bytes([id, ctrl]) + params
        pkt = bytes([0xAA, 0xAA, plen]) + payload + bytes([self._cs(payload)])
        self.ser.write(pkt)
        self.ser.flush()

    def _read(self, want_id=None, timeout=0.2):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.ser.in_waiting > 0:
                self.buf.extend(self.ser.read(self.ser.in_waiting))
            while True:
                i = self.buf.find(b"\xAA\xAA")
                if i == -1:
                    self.buf.clear()
                    break
                if len(self.buf) < i + 4:
                    break
                ln = self.buf[i + 2]
                tot = 3 + ln + 1
                if len(self.buf) < i + tot:
                    break
                pkt = self.buf[i:i + tot]
                self.buf = self.buf[i + tot:]
                rid = pkt[3]
                par = pkt[5:-1]
                if want_id is None or rid == want_id:
                    return rid, par
            time.sleep(0.005)
        return None, None

    def read_eio(self, addr: int):
        # ID 131 ctrl 0, param [addr]. Reply: [addr, value] hoac [value].
        self.ser.reset_input_buffer()
        self.buf.clear()
        self._send(131, 0, bytes([addr]))
        rid, par = self._read(want_id=131, timeout=0.2)
        if par is None:
            return None
        if len(par) >= 2 and par[0] == addr:
            return par[1]
        if len(par) >= 1:
            # neu chi 1 byte thi do la value (firmware cu)
            # nhung neu byte do trung addr thi chua chac -> tra ve + raw de nguoi dung tu nhin
            return par[-1]
        return None

    def loop(self):
        addrs = list(range(1, 13))
        print("Che/mo cam bien dau ray, cot nao doi 0<->1 la cong cam bien.")
        print("Dang quet ID 131 (EIO) dia chi 1-12.")
        print("-" * 80)
        try:
            while True:
                vals = []
                for a in addrs:
                    v = self.read_eio(a)
                    vals.append("-" if v is None else str(v))
                print(f"EIO 1-12: {vals}", flush=True)
                time.sleep(0.6)
        except KeyboardInterrupt:
            print("\nThoat.")
        finally:
            self.ser.close()


if __name__ == "__main__":
    try:
        t = SensorTester()
    except Exception as e:
        print(f"[-] Loi ket noi: {e}")
        sys.exit(1)
    t.loop()
