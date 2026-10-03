import time
from pydobot import Dobot
from pydobot.message import Message

PORT = '/dev/ttyUSB0'

# ID giao thuc Dobot (giong test_gp2.py dang chay duoc)
ID_SET_IO_MULTIPLEXING = 131
ID_GET_IO_DI = 133

# Theo Manual V2.3.1 Table 4.5/4.6:
# GP1 ADC = EIO12 (input, pull-up 1M), STOP KEY = EIO20 (input, pull-up 10K)
PINS = (12, 20)

try:
    device = Dobot(port=PORT, verbose=False)
    print(f"[INFO] Ket noi thanh cong toi Dobot tai {PORT}")
except Exception as e:
    print(f"[ERROR] Khong ket noi duoc toi Dobot: {e}")
    exit(1)

def setup_pin_input(pin):
    msg = Message()
    msg.id = ID_SET_IO_MULTIPLEXING
    msg.ctrl = 0x01
    msg.params = bytearray([pin, 4, 0])
    device._send_command(msg)

def read_di(pin):
    msg = Message()
    msg.id = ID_GET_IO_DI
    msg.ctrl = 0x00
    msg.params = bytearray([pin])
    res = device._send_command(msg)
    if res and len(res.params) >= 2:
        return res.params[1]
    return None

for p in PINS:
    setup_pin_input(p)
time.sleep(0.2)

print("\n" + "="*50)
print("[INFO] POLL GP1 (EIO12) + STOP KEY (EIO20)")
print(">>> NHAN/NHA switch, so nao doi theo tay la dung <<<")
print("="*50 + "\n")

prev = {}
try:
    while True:
        row = []
        for p in PINS:
            val = read_di(p)
            row.append(f"{p}={val}")
            if val is not None and prev.get(p) is not None and val != prev[p]:
                print(f"\n[EVENT] EIO{p}: {prev[p]} -> {val}")
            if val is not None:
                prev[p] = val
        print(f"\r{' | '.join(row)}    ", end="", flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n[INFO] Da dung chuong trinh kiem tra.")
finally:
    device.close()
