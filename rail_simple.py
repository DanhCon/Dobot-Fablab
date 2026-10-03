#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dieu khien ray truot Dobot Sliding Rail Kit - ban chuan theo Manual V2.3.1.
- Motor ray -> Stepper2 (Table 4.2, dung chung video huong dan).
- Microswitch -> STOP KEY (EIO20) + GND o cong den Communication Interface
  (Table 4.5: input, pull-up 10K). Switch dung tiep diem NO.
- Doc EIO qua ID 131 mux + ID 133 DI, giong test_gp1.py / test_gp2.py.
- Chay motor qua ID 136 SetEMotorS [index, enable, speed, distance].

Cach dung:
  python3 rail_simple.py --home              # ve dau theo tung buoc 20mm, gap switch tu dung
  python3 rail_simple.py --mm 200            # di 200mm ra dich (sau khi da home)
  python3 rail_simple.py --mm -100 --speed 5000
  python3 rail_simple.py --stop              # dung khan
"""

import sys
import time
import struct
import argparse

try:
    from pydobot import Dobot
    from pydobot.message import Message
except ImportError:
    print("[-] Can cai pydobot: pip install pydobot")
    sys.exit(1)

PORT = '/dev/ttyUSB0'

ID_SET_IO_MUX = 131
ID_GET_IO_DI = 133
ID_EMOTOR_S = 136
ID_CLEAR_ALARM = 20
ID_QUEUE_CLEAR = 245
ID_QUEUE_START = 240

RAIL_INDEX = 1        # Stepper2 = ray (Manual Table 4.2 + video)
PULSES_PER_MM = 200   # calib lai: chay 200mm do thuoc thuc te roi sua ti le
RAIL_MAX_MM = 1000
HOME_SWITCH_EIO = 20  # STOP KEY, Table 4.5
HOME_STEP_MM = 20     # moi buoc ve home (doi dau neu nguoc chieu ray ban)
HOME_SPEED = 3000


def send(api, id, ctrl, params=b""):
    msg = Message()
    msg.id = id
    msg.ctrl = ctrl
    msg.params = bytearray(params)
    return api._send_command(msg)


def clear_alarms(api):
    send(api, ID_CLEAR_ALARM, 0x01)
    send(api, ID_QUEUE_CLEAR, 0x01)
    send(api, ID_QUEUE_START, 0x01)
    time.sleep(0.1)
    print("[+] Da xoa loi + mo queue (20/245/240)")


def stop_rail(api):
    params = struct.pack("<B B i I", RAIL_INDEX, 0, 0, 0)
    send(api, ID_QUEUE_START, 0x01)
    send(api, ID_EMOTOR_S, 0x03, params)
    send(api, ID_QUEUE_START, 0x01)
    print("[+] Da dung ray khan")


def rail_step(api, dist_mm, speed):
    pulses = int(abs(dist_mm) * PULSES_PER_MM)
    dir_speed = -int(speed) if dist_mm >= 0 else int(speed)
    params = struct.pack("<B B i I", RAIL_INDEX, 1, dir_speed, pulses)
    send(api, ID_QUEUE_START, 0x01)
    send(api, ID_EMOTOR_S, 0x03, params)
    wait = max(1.0, abs(dist_mm) / 80.0 + 1.0)
    time.sleep(wait)


def read_switch(api):
    send(api, ID_SET_IO_MUX, 0x01, bytes([HOME_SWITCH_EIO, 4, 0]))
    time.sleep(0.05)
    msg = Message()
    msg.id = ID_GET_IO_DI
    msg.ctrl = 0x00
    msg.params = bytearray([HOME_SWITCH_EIO])
    res = api._send_command(msg)
    if res and len(res.params) >= 2:
        return res.params[1]
    return None


def move_mm(api, pos, dist_mm, speed):
    if abs(dist_mm) > RAIL_MAX_MM:
        print(f"[-] Vuot hanh trinh: {dist_mm}")
        return pos
    if pos is not None:
        new_pos = pos + dist_mm
        if new_pos < -5 or new_pos > RAIL_MAX_MM + 5:
            print(f"[-] Se vuot 0-1000 (dang {pos:.1f}, muon {dist_mm:+.1f}). Home lai.")
            return pos
    rail_step(api, dist_mm, speed)
    print(f"[*] Da chay {dist_mm:+.1f}mm")
    if pos is not None:
        pos = max(0.0, min(float(RAIL_MAX_MM), pos + dist_mm))
        print(f"    Vi tri mem: {pos:.1f}mm")
    return pos


def home(api):
    print("[*] Ve HOME theo buoc ngan, gap switch (EIO20=0) se tu dung.")
    clear_alarms(api)
    send(api, ID_SET_IO_MUX, 0x01, bytes([HOME_SWITCH_EIO, 4, 0]))
    time.sleep(0.2)
    for i in range(60):
        v = read_switch(api)
        print(f"  buoc {i+1}: switch={v}", flush=True)
        if v == 0:
            print("[+] Da cham switch -> HOME (0mm).")
            clear_alarms(api)
            return 0.0
        rail_step(api, HOME_STEP_MM, HOME_SPEED)
    print("[-] 60 buoc chua gap switch, dung de kiem tra day switch.")
    stop_rail(api)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mm", type=float, default=None)
    ap.add_argument("--speed", type=int, default=10000)
    ap.add_argument("--home", action="store_true")
    ap.add_argument("--stop", action="store_true")
    args = ap.parse_args()

    try:
        api = Dobot(port=PORT, verbose=False)
        print(f"[+] Noi Dobot tai {PORT}")
    except Exception as e:
        print(f"[-] Loi ket noi: {e}")
        return

    try:
        if args.stop:
            stop_rail(api)
        elif args.home:
            home(api)
        elif args.mm is not None:
            clear_alarms(api)
            move_mm(api, None, args.mm, args.speed)
        else:
            print("Lenh: --home | --mm 200 | --mm -100 | --stop")
    finally:
        api.close()


if __name__ == "__main__":
    main()
