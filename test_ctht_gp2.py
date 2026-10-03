#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHƯƠNG TRÌNH TEST CÔNG TẮC HÀNH TRÌNH 2 DÂY THEO ĐÚNG SƠ ĐỒ CỔNG TAY DOBOT
Quét đồng thời cả GP2 (Hàng dưới) và GP1 (Hàng trên)
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

def cs(payload):
    return (0x100 - (sum(payload) % 0x100)) % 0x100

def get_di(ser, pin):
    plen = 2 + 1
    payload = bytes([133, 0, pin])
    pkt = bytes([0xAA, 0xAA, plen]) + payload + bytes([cs(payload)])
    ser.reset_input_buffer()
    ser.write(pkt)
    ser.flush()
    t0 = time.time()
    buf = bytearray()
    while time.time() - t0 < 0.08:
        if ser.in_waiting:
            buf.extend(ser.read(ser.in_waiting))
        while True:
            idx = buf.find(b"\xAA\xAA")
            if idx == -1:
                buf.clear()
                break
            if len(buf) < idx + 4:
                break
            ln = buf[idx + 2]
            tot = 3 + ln + 1
            if len(buf) < idx + tot:
                break
            rep = buf[idx : idx + tot]
            buf = buf[idx + tot :]
            if rep[3] == 133 and len(rep) >= 7 and rep[5] == pin:
                return rep[6]
        time.sleep(0.002)
    return None

def main():
    port = auto_detect_port()
    if not port:
        print("[-] Lỗi: Không tìm thấy cổng kết nối Dobot.")
        sys.exit(1)

    ser = serial.Serial(port, 115200, timeout=0.1)
    time.sleep(0.2)
    ser.reset_input_buffer()

    print("=" * 80)
    print("      KIỂM TRA CÔNG TẮC HÀNH TRÌNH THEO ĐÚNG SƠ ĐỒ GP2 & GP1")
    print("=" * 80)
    print(" [GP2 - HÀNG DƯỚI]:")
    print("   * Chân 1: GND (Mass)")
    print("   * Chân 2: EIO 13 (REV)")
    print("   * Chân 3: EIO 14 (PWM)  <-- KHUYÊN DÙNG CẮM CHÂN 1 VÀ CHÂN 3")
    print("   * Chân 4: EIO 15 (ADC)")
    print(" [GP1 - HÀNG TRÊN]:")
    print("   * Chân 2: EIO 10 (REV) | Chân 3: EIO 11 (PWM) | Chân 4: EIO 12 (ADC)")
    print("-" * 80)
    print(">>> DÙNG TAY BẤM GIỮ VÀ NHẢ CÔNG TẮC HÀNH TRÌNH <<<")
    print("-" * 80)

    # Pins to monitor
    gp2_pins = [(13, "GP2-Chân 2 (EIO13)"), (14, "GP2-Chân 3 (EIO14)"), (15, "GP2-Chân 4 (EIO15)")]
    gp1_pins = [(10, "GP1-Chân 2 (EIO10)"), (11, "GP1-Chân 3 (EIO11)"), (12, "GP1-Chân 4 (EIO12)")]
    all_pins = gp2_pins + gp1_pins

    prev = {p: get_di(ser, p) for p, _ in all_pins}
    count = 0

    try:
        while True:
            curr = {}
            for p, name in all_pins:
                val = get_di(ser, p)
                curr[p] = val
                if val is not None and prev.get(p) is not None and val != prev[p]:
                    print("\a", end="")
                    print(f"\n⚡ [THÀNH CÔNG! PHÁT HIỆN TÍN HIỆU TẠI {name}]: {prev[p]} -> {val}")
                    print("-" * 80)
                prev[p] = val

            # Display GP2 row and GP1 row
            gp2_str = f"GP2 (Hàng dưới): Chân 2={curr.get(13, '-')} | Chân 3={curr.get(14, '-')} | Chân 4={curr.get(15, '-')}"
            gp1_str = f"GP1 (Hàng trên): Chân 2={curr.get(10, '-')} | Chân 3={curr.get(11, '-')} | Chân 4={curr.get(12, '-')}"
            print(f"\r[T={count*0.1:.1f}s] {gp2_str}  ||  {gp1_str}   ", end="", flush=True)
            count += 1
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n[+] Đã dừng.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
