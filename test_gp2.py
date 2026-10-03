import time
from pydobot import Dobot
from pydobot.message import Message

PORT = '/dev/ttyUSB0'

# ID giao thức Dobot
ID_SET_IO_MULTIPLEXING = 131
ID_GET_IO_DI = 133

# Chân công tắc hành trình của Sliding Rail: STOP KEY (EIO20) + GND
# o cong den Communication Interface (Manual V2.3.1 Table 4.5)
RAIL_SWITCH_PIN = 20

try:
    device = Dobot(port=PORT, verbose=False)
    print(f"[INFO] Kết nối thành công tới Dobot tại {PORT}")
except Exception as e:
    print(f"[ERROR] Không kết nối được tới Dobot: {e}")
    exit(1)

def setup_pin_input(pin):
    """
    Cấu hình chân thành Digital Input:
    - address: pin number (14)
    - mode: 4 (Digital Input) hoặc 5 (Input Pull-up)
    - isQueued: 0 (Thực thi ngay)
    """
    msg = Message()
    msg.id = ID_SET_IO_MULTIPLEXING
    msg.ctrl = 0x01  # Thực thi tức thời
    msg.params = bytearray([pin, 4, 0])
    device._send_command(msg)

def read_limit_switch(pin):
    """Đọc mức logic trả về của Limit Switch"""
    msg = Message()
    msg.id = ID_GET_IO_DI
    msg.ctrl = 0x00
    msg.params = bytearray([pin])
    res = device._send_command(msg)
    if res and len(res.params) >= 2:
        return res.params[1]
    return None

# Cấu hình Pin 14
setup_pin_input(RAIL_SWITCH_PIN)
time.sleep(0.2)

print("\n" + "="*50)
print(f"[INFO] BẮT ĐẦU THEO DÕI LIMIT SWITCH (PIN {RAIL_SWITCH_PIN})")
print(">>> DÙNG TAY BẤM VÀ GIỮ CÔNG TẮC HÀNH TRÌNH <<<")
print("="*50 + "\n")

prev_val = None

try:
    while True:
        val = read_limit_switch(RAIL_SWITCH_PIN)
        
        # Nếu switch hoạt động, trạng thái sẽ nhảy giữa 0 và 1
        if val is not None:
            status_text = "PRESSED (ĐÃ BẤM / CHẠM)" if val == 0 else "RELEASED (ĐANG NHẢ)"
            # Nếu switch là loại Thường Đóng (NC), giá trị có thể đảo ngược lại
            
            print(f"\r[LIMIT SWITCH STATUS] Raw DI: {val}  -->  {status_text}    ", end="", flush=True)
            
            if prev_val is not None and val != prev_val:
                print(f"\n[EVENT] Thay đổi trạng thái: {prev_val} -> {val}")
            
            prev_val = val
        else:
            print("\r[ERROR] Không đọc được phản hồi từ cổng Serial...", end="", flush=True)

        time.sleep(0.05)  # 20 Hz để bắt kịp thao tác bấm tay

except KeyboardInterrupt:
    print("\n[INFO] Đã dừng chương trình kiểm tra.")

finally:
    device.close()