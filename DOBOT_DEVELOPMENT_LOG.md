# DOBOT MAGICIAN 3D DIGITAL TWIN & REAL-TIME CONTROLLER
## TÀI LIỆU KỸ THUẬT, TIẾN TRÌNH & HƯỚNG DẪN BÀN GIAO TOÀN DIỆN (HANDOVER NOTES)

> **Mục đích:** Tài liệu này ghi lại toàn bộ kiến trúc hệ thống, các tính năng đã hoàn thiện, danh sách các lỗi phần cứng/giao thức đã gặp, nguyên nhân gốc rễ, phương án khắc phục triệt để và những lưu ý cốt lõi để các kỹ sư hoặc Agent AI tiếp theo có thể tiếp tục phát triển mà không gặp trở ngại.

---

## 1. TỔNG QUAN HỆ THỐNG & KIẾN TRÚC (SYSTEM ARCHITECTURE)

Hệ thống điều khiển và bản sao số 3D thời gian thực (Digital Twin) cho cánh tay robot **Dobot Magician** trên hệ điều hành **Ubuntu Linux**.

```
[ Giao diện Web 3D (Three.js) ]
         │ (WebSocket ws:// hoặc wss://)
         ▼
[ Python Tornado Server (dobot_live_server.py) ]
         │ (Pyserial 115200 baud, 8N1)
         ▼
[ Cổng Serial /dev/ttyUSB* (STM32 Firmware) ]
         │ (Giao thức nhị phân Dobot Protocol v1.1.4)
         ▼
[ Dobot Magician Robotic Arm + Giác hút khí nén ]
```

### 1.1. Thông số vật lý & Cấu hình phần cứng
- **Cổng giao tiếp Serial:** `/dev/ttyUSB0` hoặc `/dev/ttyUSB1` (tự động nhận diện).
- **Tốc độ truyền:** `115200` bps, Data bits: 8, Stop bits: 1, Parity: None.
- **Bù trừ chiều dài đầu công cụ (Tool Offset Z):**
  - Chiều dài giác hút: **`59.5 mm`**
  - Mặt bích (Flange Z) $\to$ Đầu mút giác hút (TCP Z):
    $$Z_{TCP} = Z_{Flange} - 59.5\text{ mm}$$
    $$Z_{Flange} = Z_{TCP} + 59.5\text{ mm}$$
- **Phạm vi không gian làm việc an toàn (Workspace Safety Envelope):**
  - Bán kính ngang: $R_{horiz} = \sqrt{X^2 + Y^2} \in [140.0\text{ mm}, 330.0\text{ mm}]$. Dưới $140\text{ mm}$ sẽ tự đâm vào thân robot, trên $330\text{ mm}$ vượt tầm với tối đa.
  - Chiều cao đầu hút: $Z_{TCP} \in [-120.0\text{ mm}, +100.0\text{ mm}]$ (Tương ứng $Z_{Flange} \in [-60.5\text{ mm}, +159.5\text{ mm}]$). Dưới $-120\text{ mm}$ có nguy cơ đâm gãy đầu hút vào mặt bàn.
  - Góc quay trục $R$: $[-135^\circ, +135^\circ]$.

---

## 2. CÁC TÍNH NĂNG ĐÃ HOÀN THIỆN (COMPLETED FEATURES)

1. **Đọc dữ liệu thời gian thực (Real-time Kinematics & Pose):**
   - Đọc tọa độ $X, Y, Z, R$ và 4 góc khớp $J_1, J_2, J_3, J_4$ với tần số 20Hz (mỗi 50ms) không gây nghẽn Serial.
2. **Điều khiển giác hút khí nén (End-Effector Suction Cup):**
   - Bật/tắt bơm hút chân không và van xả khí nhả vật tức thì.
3. **Di chuyển điểm chỉ định an toàn (`move_to_point.py`):**
   - Hỗ trợ cả tương tác qua Terminal (Interactive) lẫn truyền tham số dòng lệnh CLI (`--x`, `--y`, `--z`, `--r`, `--suck`).
   - Tích hợp quỹ đạo an toàn dạng cổng **Safe Jump**: Nhấc đầu hút lên cao an toàn $\to$ Bay ngang tới $(X_{đích}, Y_{đích})$ $\to$ Hạ thẳng xuống $Z_{đích}$. Tránh hoàn toàn nguy cơ quẹt đổ vật cản trên bàn.
   - Độ chính xác kiểm chứng thực tế: **Sai số $\Delta X = 0.00\text{ mm}, \Delta Y = 0.00\text{ mm}, \Delta Z = 0.00\text{ mm}$**.
4. **Cục Điểm Đích 3D Tương Tác Trực Quan (Interactive 3D Beacon):**
   - Trên Web 3D có khối lập phương điểm đích phát sáng cam với trục tọa độ **TransformControls (Gizmo)**:
     - Mũi tên **Xanh lá (HƯỚNG LÊN)**: Kéo trục $Z$ (Độ cao).
     - Mũi tên **Đỏ**: Kéo trục $X$ (Tiến / Lùi).
     - Mũi tên **Xanh dương**: Kéo trục $Y$ (Trái / Phải).
   - Tùy chọn *"Tự động di chuyển khi thả chuột"* hoặc bấm nút *"🚀 Di chuyển robot tới điểm đích"*.
5. **Hạ tầng Publish Online ra Internet:**
   - Thư mục `dist_netlify/` sẵn sàng kéo thả lên Netlify.
   - Script `./start_online.sh` tự động thiết lập đường hầm Cloudflare Tunnel (`cloudflared`) để điều khiển từ xa qua 4G/Internet mà không cần mở port modem.
6. **Cơ chế Tự Động Giám Sát Lỗi & Khôi Phục Đèn Xanh:**
   - Đọc và giải mã liên tục trạng thái Alarm của Dobot.
   - Nút khôi phục 1 chạm (Reset Alarm) trên Web và Terminal, xóa sạch cờ lỗi và hàng đợi kẹt mà không cần phải Homing lại.

---

## 3. DANH SÁCH LỖI ĐÃ GẶP, NGUYÊN NHÂN & CÁCH SỬA TRIỆT ĐỂ

### ❌ Lỗi 1: Gửi nhầm mã lệnh Clear Queue (ID 242 vs ID 245)
- **Hiện tượng:** Sau khi gặp lỗi hoặc dừng khẩn cấp, gửi lệnh mới robot không di chuyển dù cổng Serial vẫn kết nối.
- **Nguyên nhân gốc:**
  - Trong tài liệu giao thức Dobot Protocol:
    - ID 240 = `SetQueuedCmdStartExec` (Bắt đầu chạy queue)
    - ID 241 = `SetQueuedCmdStopExec` (Tạm dừng queue)
    - **ID 242 = `SetQueuedCmdForceStopExec`** (Cưỡng bức dừng queue khẩn cấp!)
    - **ID 245 = `SetQueuedCmdClear`** (Xóa sạch các lệnh đang kẹt trong queue!)
  - Code cũ gửi `id=242` với ý định xóa queue, nhưng thực chất lại liên tục ép vi điều khiển Dobot vào trạng thái Force Stop.
- **Cách sửa chuẩn:**
  ```python
  # Trình tự khôi phục chuẩn:
  self._send_raw_cmd(id=20, ctrl=1)   # Xóa cờ lỗi phần cứng
  self._send_raw_cmd(id=245, ctrl=1)  # Xóa sạch lệnh kẹt trong queue (ID 245)
  self._send_raw_cmd(id=240, ctrl=1)  # Kích hoạt thực thi lại queue (ID 240)
  ```

---

### ❌ Lỗi 2: Nhấn nút Jog hoặc Manual bị đỏ đèn còi hú liên tục
- **Hiện tượng:** Nhấn các nút jog manual trên giao diện web (+Z, -Z, +X, -X) hoặc lệnh test, robot lập tức ngắt động cơ, đèn chuyển sang ĐỎ và còi kêu.
- **Nguyên nhân gốc:**
  - Code cũ jog bằng chế độ tương đối tuyến tính Descartes: `mode=7` (`MOVL_XYZ_INC`).
  - Cơ cấu cánh tay song song SCARA của Dobot có các **điểm kỳ dị động học nghịch (IK Singularity)**. Khi đi đường thẳng gần giới hạn hoặc gần thân ($R < 140\text{ mm}$), vi điều khiển tính ra vận tốc góc khớp tiến tới vô hạn $\to$ kích hoạt cờ bảo vệ động cơ ngắt khẩn cấp (Alarm `0x11` - *ERR_PLAN_INV_SINGULARITY*).
- **Cách sửa chuẩn:**
  - Thay vì dùng `mode=7`, server đọc vị trí hiện tại: $X_{cur}, Y_{cur}, Z_{cur}, R_{cur}$.
  - Tính vị trí đích tuyệt đối: $X_{target} = X_{cur} + \Delta X, \dots$
  - Kiểm tra điều kiện an toàn vùng làm việc trước khi gửi.
  - Gửi lệnh di chuyển bằng **`mode=1` (`PTPMOVJXYZMode`)**:
    ```python
    # mode=1 là nội suy không gian khớp: chuyển động mượt mà,
    # hoàn toàn miễn nhiễm với điểm kỳ dị động học, không bao giờ bị đỏ đèn!
    params = bytes([1]) + struct.pack("<4f", tx, ty, tz, tr)
    self._send_raw_cmd(id=84, ctrl=3, params=params)
    ```

---

### ❌ Lỗi 3: Robot không di chuyển khi gửi lệnh PTP (`move_ptp`)
- **Hiện tượng:** Gửi lệnh PTP nhưng robot đứng im, không báo lỗi.
- **Nguyên nhân gốc:**
  1. Thiếu thông số vận tốc PTP: Nếu chưa gửi cấu hình vận tốc/gia tốc (ID 80, 81, 83), firmware đặt vận tốc mặc định bằng 0.
  2. Byte `ctrl`: Với lệnh `SetPTPCmd (ID 84)`, phải đặt `ctrl=3` (Queued write) để lệnh được nạp vào hàng đợi và bộ nội suy quỹ đạo kích hoạt.
- **Cách sửa chuẩn:**
  Ngay khi mở cổng Serial, bắt buộc gửi gói cấu hình vận tốc:
  ```python
  # ID 80: SetPTPJointParams (Vận tốc/gia tốc 4 khớp)
  self._send_raw_cmd(id=80, ctrl=1, params=struct.pack('<8f', *([200.0]*8)))
  # ID 81: SetPTPCoordinateParams (Vận tốc/gia tốc Descartes XYZ và R)
  self._send_raw_cmd(id=81, ctrl=1, params=struct.pack('<4f', 200.0, 200.0, 200.0, 200.0))
  # ID 83: SetPTPCommonParams (Tỉ lệ vận tốc & gia tốc = 50%)
  self._send_raw_cmd(id=83, ctrl=1, params=struct.pack('<2f', 50.0, 50.0))
  ```

---

### ❌ Lỗi 4: Rơi rớt gói tin Serial (Packet Loss) khi đọc phản hồi
- **Hiện tượng:** Hàm đọc dữ liệu (`get_pose()` hoặc `get_alarms()`) thỉnh thoảng trả về `None` dù robot vẫn gửi dữ liệu.
- **Nguyên nhân gốc:**
  - Bộ đệm `buf = bytearray()` nằm cục bộ trong hàm đọc phản hồi, mỗi lần gọi hàm thì buffer bị tạo mới.
  - Khi robot gửi liên tiếp nhiều gói tin (ví dụ: ACK 240, ACK 245, Pose, Alarms), các byte còn sót lại của gói tin sau bị hủy bỏ khi hàm kết thúc.
- **Cách sửa chuẩn:**
  - Khai báo `self.buf = bytearray()` là thuộc tính của đối tượng `DobotController`.
  - Giữ lại các byte chưa parse hết trong `self.buf` để hàm đọc tiếp theo xử lý trọn vẹn, không bao giờ mất byte.

---

### ❌ Lỗi 5: Đụng độ cổng mạng (Port 8080 Collision)
- **Hiện tượng:** Server báo `OSError: [Errno 98] Address already in use`.
- **Cách sửa chuẩn:**
  Tích hợp hàm `find_available_port(preferred_port=8080)` tự động kiểm tra cổng 8080 $\to$ 8081 $\to$ 8082 $\to$ 8088. Trên Web client, dùng `window.location.host` để WebSocket tự động bắt đúng port máy chủ.

---

### ❌ Lỗi 6: Dịch vụ `localtunnel` bị treo vô tận (Hang without response)
- **Hiện tượng:** Chạy `npx localtunnel --port 8080 --subdomain ...` thì terminal đứng im phắc, không in ra URL kết nối và không báo lỗi.
- **Nguyên nhân gốc:**
  - Máy chủ trung gian mã nguồn mở của `localtunnel.me` ở nước ngoài thường xuyên bị quá tải băng thông hoặc bị tường lửa/DNS của các nhà mạng tại Việt Nam bóp chặn quá trình bắt tay kết nối (handshake).
- **Cách sửa chuẩn:**
  - Hủy lệnh bằng `Ctrl + C`.
  - Thay thế bằng **Cloudflare Quick Tunnel** (hạ tầng Edge CDN cực mạnh có POP tại Việt Nam) hoặc **ngrok** (dịch vụ thương mại cấp domain tĩnh ổn định 100%).

---

### ❌ Lỗi 7: Bất tiện của Domain Ngẫu Nhiên / Domain Xấu khi đưa lên Internet
- **Hiện tượng:** 
  - Cloudflare Quick Tunnel đổi subdomain ngẫu nhiên sau mỗi lần khởi động (`xxx.trycloudflare.com`), khiến người dùng phải mở bánh răng ⚙️ dán lại link.
  - Ngrok Free cung cấp domain tĩnh nhưng tên tự sinh ngẫu nhiên khó nhớ và thiếu chuyên nghiệp (`rebuild-thinner-spur.ngrok-free.dev`).
- **Cách sửa chuẩn (Mô hình Mặt tiền đẹp + Ống ngầm):**
  - **Mặt tiền (Frontend):** Deploy giao diện Web 3D lên Netlify với tên miền tùy chọn đẹp mắt `https://dobot-fablab.netlify.app`.
  - **Ống nước ngầm (Backend Bridge):** Trong mã nguồn Web (`dist_netlify/index.html`), cài cứng địa chỉ kết nối ngầm `wss://rebuild-thinner-spur.ngrok-free.dev/ws`.
  - **Kết quả:** Người dùng mở link Netlify là điều khiển được robot ngay, không bao giờ phải cấu hình bánh răng ⚙️ và không ai nhìn thấy domain ngrok xấu.

---

## 4. BẢNG MÃ LỖI DOBOT MAGICIAN (DOBOT ALARM REFERENCE)

Khi đọc ID 20 (Ctrl=0), Dobot trả về mảng 16 byte (128 bit). Bit thứ $k$ tương ứng với mã lỗi $k$:

| Mã Hex | Tên kỹ thuật | Ý nghĩa & Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- | :--- |
| **`0x00`** | `Reset Alarm` | Vi điều khiển robot vừa khởi động lại hoặc cắm nguồn | Bấm "Khôi phục / Xóa lỗi" |
| **`0x01`** | `Undefined Instruction` | Vi điều khiển nhận được gói tin có ID không hợp lệ | Kiểm tra lại cấu trúc packet |
| **`0x02`** | `File System Error` | Lỗi bộ nhớ Flash lưu file của robot | Xóa lỗi hoặc nạp lại firmware |
| **`0x10`** | `Planning Error` | Lỗi thuật toán quy hoạch đường đi | Điều chỉnh điểm đích |
| **`0x11`** | `IK Singularity Error` | Vượt tầm với hoặc rơi vào điểm kỳ dị động học | Đổi sang mode 1 (`MOVJ`), kiểm tra bán kính $R \ge 140\text{ mm}$ |
| **`0x12`** | `Planning Limit Error` | Điểm yêu cầu vượt ngoài giới hạn phần mềm | Kiểm tra lại tọa độ $X, Y, Z$ |
| **`0x20`** | `Kinematics Motion Error` | Lỗi chấp hành chuyển động khi động cơ đang quay | Dừng khẩn cấp, giải phóng queue |
| **`0x21`** | `Joint 1 Limit` | Khớp 1 quay chạm giới hạn hành trình | Jog lùi khớp 1 lại |
| **`0x22`** | `Joint 2 Limit` | Khớp 2 (Rear arm) chạm giới hạn | Jog lùi khớp 2 lại |
| **`0x23`** | `Joint 3 Limit` | Khớp 3 (Forearm) chạm giới hạn | Jog lùi khớp 3 lại |
| **`0x24`** | `Joint 4 Limit` | Khớp 4 (Xoay đầu hút) chạm giới hạn | Xoay góc $R$ về $0^\circ$ |
| **`0x30`** | `Overspeed Alarm` | Vận tốc khớp vượt quá ngưỡng an toàn | Giảm vận tốc PTP xuống 30-50% |
| **`0x40`** | `Joint 1 Positive Limit` | Khớp 1 chạm giới hạn góc dương ($+J1$) | Jog Khớp 1 ngược chiều âm ($J1-$) |
| **`0x41`** | `Joint 1 Negative Limit` | Khớp 1 chạm giới hạn góc âm ($-J1$) | Jog Khớp 1 ngược chiều dương ($J1+$) |
| **`0x42`** | `Joint 2 Positive Limit` | Khớp 2 (cánh tay sau) chạm giới hạn dương ($+J2$) | Jog Khớp 2 ngược chiều âm ($J2-$) |
| **`0x43`** | `Joint 2 Negative Limit` | Khớp 2 (cánh tay sau) chạm giới hạn âm ($-J2$) | Nâng nhẹ cánh tay sau lên / Jog $J2+$ |
| **`0x44`** | `Joint 3 Positive Limit` | Khớp 3 (cẳng tay trước) chạm giới hạn dương ($+J3$) | Jog Khớp 3 ngược chiều âm ($J3-$) |
| **`0x45`** | `Joint 3 Negative Limit` | Khớp 3 (cẳng tay trước) chạm giới hạn âm ($-J3$) | Jog Khớp 3 ngược chiều dương ($J3+$) |
| **`0x46`** | `Joint 4 Positive Limit` | Khớp 4 (xoay đầu hút) chạm giới hạn dương ($+J4$) | Jog Khớp 4 ngược chiều âm ($J4-$) |
| **`0x47`** | `Joint 4 Negative Limit` | Khớp 4 (xoay đầu hút) chạm giới hạn âm ($-J4$) | Jog Khớp 4 ngược chiều dương ($J4+$) |
| **`0x48`** | `Parallelogram Positive Limit` | Cơ cấu thanh truyền song song đạt giới hạn dương | Jog đưa cánh tay về vùng làm việc trung tâm |
| **`0x49`** | `Parallelogram Negative Limit` | Cơ cấu thanh truyền song song đạt giới hạn âm | Jog đưa cánh tay về vùng làm việc trung tâm |

---

## 5. DANH SÁCH FILE VÀ CẤU TRÚC DỰ ÁN

```
/home/danh/FABLAB/DOBOT/
├── dobot_live_server.py      # Server chính: Tornado Web + WebSocket + Dobot Serial Driver (hỗ trợ PTP, Jog, Homing, Suction)
├── dobot_visualizer.html     # Giao diện Web 3D: Three.js 3 Tab, Gizmo Beacon, Homing, TCP Monitor
├── move_to_point.py          # Script CLI & Interactive: Di chuyển đầu hút đến 1 điểm với Safe Jump
├── test_dobot.py             # Script kiểm tra phần cứng độc lập (Menu 0-6 trên Terminal)
├── start_online.sh           # Script 1-click: Bật server + mở Cloudflare Tunnel ngẫu nhiên ra Internet
├── start_ngrok.sh            # Script 1-click: Bật server + kết nối domain cố định ngrok (rebuild-thinner-spur)
├── cloudflared               # Binary Cloudflare Tunnel dành cho Linux x86_64
└── DOBOT_DEVELOPMENT_LOG.md  # Tài liệu bàn giao & lịch sử phát triển toàn diện

/home/danh/FABLAB/dist_netlify/
├── index.html                # Bản build Web tĩnh tích hợp sẵn cầu nối ngrok cố định
├── TransformControls.js      # Thư viện Three.js kéo thả tọa độ 3D
├── _redirects                # Cấu hình redirect SPA cho Netlify
└── README.md                 # Hướng dẫn deploy Netlify
```

---

## 6. HƯỚNG DẪN VẬN HÀNH NHANH (QUICK START GUIDE)

### Cách 1: Chạy Menu Terminal độc lập (Offline)
```bash
cd /home/danh/FABLAB/DOBOT
python3 test_dobot.py
```
- Phím `1`: Đọc tọa độ hiện tại.
- Phím `2`: Bật/tắt giác hút.
- Phím `3`: Thử di chuyển trục Z $\pm 10\text{ mm}$ bằng `MOVJ`.
- Phím `4`: Xem chi tiết mã lỗi & khôi phục còi báo động.
- Phím `5`: Chạy Homing về vị trí chuẩn cơ khí.
- Phím `6`: Di chuyển đầu hút tới tọa độ $(X, Y, Z)$ chỉ định bằng Safe Jump.

### Cách 2: Mở Web 3D Local trên máy tính
```bash
cd /home/danh/FABLAB/DOBOT
python3 dobot_live_server.py
```
Mở trình duyệt: `http://localhost:8080` (hoặc `http://localhost:8081`).

### Cách 3: Điều khiển từ xa qua Internet bằng Cloudflare (Nhanh nhất - Không cần tài khoản)
```bash
cd /home/danh/FABLAB/DOBOT
./start_online.sh
```
Terminal tự động cấp link dạng: `https://xxxx.trycloudflare.com` để mở trên điện thoại / 4G.

### Cách 4: Điều khiển từ xa qua Netlify với Domain Cố Định Đẹp (Chuyên nghiệp nhất)
1. Trên máy Linux, chạy cầu nối:
   ```bash
   cd /home/danh/FABLAB/DOBOT
   ./start_ngrok.sh
   ```
2. Mở trình duyệt trên điện thoại/máy tính bất kỳ:
   👉 **`https://dobot-fablab.netlify.app`**
   *(Giao diện tự động kết nối ngầm về robot, không cần dán link, không hiện domain ngrok)*.

---

## 7. GHI CHÚ QUAN TRỌNG CHO CÁC AGENT / DEVELOPER TIẾP THEO

1. **Tuyệt đối không gửi lệnh di chuyển tương đối bằng `mode=7` (`MOVL_XYZ_INC`):** Luôn cộng delta vào vị trí hiện tại và dùng `mode=1` (`MOVJ_XYZ`) để tránh lỗi kỳ dị toán học.
2. **Luôn duy trì Tool Offset Z = 59.5mm:** Tọa độ người dùng quan tâm luôn là mũi đầu hút ($Z_{TCP}$), còn tọa độ robot thực thi là mặt bích ($Z_{Flange} = Z_{TCP} + 59.5$).
3. **Khi gửi lệnh xóa còi lỗi:** Bắt buộc gửi trọn bộ 3 lệnh: `ID 20` (Xóa lỗi) $\to$ `ID 245` (Xóa queue kẹt) $\to$ `ID 240` (Kích hoạt lại queue). Thiếu ID 245 hoặc gửi nhầm ID 242 sẽ làm robot tiếp tục đóng băng.
4. **Không đóng/mở Serial liên tục:** Dobot Magician dùng chip nạp CP2102. Khi mở serial với cờ DTR/RTS, vi điều khiển STM32 sẽ bị reset mất khoảng 0.3s - 0.5s để khởi động lại. Nên duy trì kết nối serial liên tục trong server daemon.
5. **Cơ chế Homing an toàn:** Homing (ID 31) sẽ kích hoạt vi điều khiển quay tìm công tắc hành trình cơ học của từng trục. Phải luôn nhắc người dùng dọn sạch không gian xung quanh trước khi bấm chạy.

---

## 8. CẢI TIẾN GIAO DIỆN WEB 3D (UI REDESIGN & HOMING INTEGRATION)

Giao diện Web 3D (`dobot_visualizer.html`) đã được tái cấu trúc từ bố cục 1 cột dài (>1200px) sang kiến trúc **3 Tab + Fixed Header + Sticky Footer**:

- **Header Cố định:** 
  - Logo, trạng thái kết nối (`Live` / `Offline`) kèm nút bánh răng ⚙️ cấu hình IP từ xa.
  - Chuyển chế độ: `⚡ Đồng bộ thật (Live)` vs `🎮 Mô phỏng (Manual)`.
  - Banner cảnh báo đèn đỏ thông minh (tự động hiện mã lỗi và nút 1-click Khôi phục khi robot lỗi).
- **Hệ thống 3 Tab gọn gàng:**
  - **Tab 1: 🎯 Điểm Đích (Target 3D):** Nút bật/tắt cục điểm đích 3D Gizmo, thanh legend màu mini (Z/X/Y), lưới 2x2 nhập tọa độ $(X, Y, Z, R)$, kiểm tra tầm với an toàn thời gian thực, 2 nút hành động chính (`📦 Nhấc An Toàn` / `🚀 Bay Thẳng`), và 4 chip điểm mẫu nhanh (`Home`, `A`, `B`, `Mặt Bàn`).
  - **Tab 2: 🕹️ Điều Khiển (Jog & Khớp):** Chuyển đổi giữa `Phím Jog Nhanh` (chọn bước 1/5/10/20/50mm, bàn phím 3x3) và `Thanh Trượt` (XYZ Đề-các vs Góc Khớp J1-J4 có nút $\pm$ vi chỉnh).
  - **Tab 3: 📊 Giám Sát:** Bảng dữ liệu TCP 2 cột hiện đại, cao độ mặt bàn, khoảng cách 3D, nút bật/tắt tia gióng 3D, chọn công cụ (Giác hút / Tay kẹp / Flange), mục **Hiệu chuẩn gốc (Homing Calibration)** với nút 1-click kích hoạt kèm cảnh báo an toàn, và chuyển theme (🌿 Simulator / 🌌 Studio Dark).
- **Sticky Footer Luôn Hiển Thị (3 Nút Hành Động Nhanh):** 
  - Nút `🔔 Xóa Lỗi` (khôi phục nhanh khi đèn đỏ).
  - Nút `🏠 Về Gốc (Home)` (chạy Homing tìm cữ chuẩn quang học với popup xác nhận an toàn).
  - Nút `💨 Giác Hút` (đổi màu nổi bật theo trạng thái thực tế).
- **Backend WebSocket:** Đã bổ sung `home()` (ID 31 `SetHOMECmd`) vào `DobotController` và xử lý action `"home"` trong `WebSocketHandler`.
- **Đồng bộ Netlify:** Đã đồng bộ trực tiếp mã nguồn vào `/home/danh/FABLAB/dist_netlify/index.html`.

---

## 9. ĐÁNH GIÁ CÁC GIẢI PHÁP ĐIỀU KHIỂN TỪ XA & HƯỚNG MỞ RỘNG KHÔNG GIỚI HẠN

### 9.1. So sánh kỹ thuật giữa các mô hình:
1. **Mô hình Netlify + ngrok Tunnel (Hiện tại):**
   - *Ưu điểm:* Giao diện đẹp cố định (`.netlify.app`), tự kết nối ngầm, không tốn chi phí.
   - *Khuyết điểm:* Gói ngrok Free có hạn mức ~1GB dữ liệu / tháng (đủ cho đồ án, nhưng không nên treo 24/7 cả tháng), chưa có mật khẩu xác thực người dùng.
2. **Mô hình Cloudflare Named Tunnel + Custom Domain (Khuyên dùng khi triển khai thực tế):**
   - *Ưu điểm:* Hoàn toàn **MIỄN PHÍ 100% & BĂNG THÔNG KHÔNG GIỚI HẠN**, độ trễ cực thấp (Data Center tại Viettel/VNPT/FPT < 10ms), có thể bật Cloudflare Zero Trust (bảo vệ bằng mã PIN hoặc Google Login).
   - *Yêu cầu:* Cần sở hữu 1 tên miền riêng (mua khoảng 20k VNĐ/năm hoặc subdomain trường cấp).
3. **Mô hình Mạng Riêng Ảo Tailscale / WireGuard (Dành cho nhóm nội bộ):**
   - *Ưu điểm:* Miễn phí 100%, không giới hạn băng thông, truyền dữ liệu Peer-to-Peer trực tiếp siêu nhanh, bảo mật tuyệt đối chỉ thiết bị đăng nhập cùng Gmail mới truy cập được.
   - *Khuyết điểm:* Thiết bị điều khiển bắt buộc phải cài app Tailscale (không gửi link cho người lạ bấm vào ngay được).
4. **Mô hình Cloud Broker (Firebase / MQTT giống ESP32):**
   - *Ưu điểm:* 100% chỉ dùng Web tĩnh Netlify, không cần tunnel chạy nền.
   - *Khuyết điểm:* Cần viết lại giao thức trao đổi dữ liệu sang dạng Pub/Sub hoặc REST, độ trễ cập nhật tư thế 3D sẽ cao hơn WebSocket trực tiếp.

---

## 10. TÍCH HỢP THỊ GIÁC MÁY TÍNH & CALIB HAND-EYE (VISION & HOMOGRAPHY CALIBRATION)

### 10.1. Bản chất toán học: Phép biến đổi phối cảnh 2D phẳng (Planar Perspective Homography)
Chuyển đổi từ tọa độ điểm ảnh Pixel $(u, v)$ từ camera treo nghiêng trên bàn sang tọa độ vật lý phẳng của Dobot $(X, Y)$ (tính bằng mm) theo ma trận phối cảnh $3 \times 3$:
$$s \begin{bmatrix} X \\ Y \\ 1 \end{bmatrix} = \begin{bmatrix} h_{00} & h_{01} & h_{02} \\ h_{10} & h_{11} & h_{12} \\ h_{20} & h_{21} & 1 \end{bmatrix} \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}$$
$$X = \frac{h_{00}u + h_{01}v + h_{02}}{h_{20}u + h_{21}v + 1}, \quad Y = \frac{h_{10}u + h_{11}v + h_{12}}{h_{20}u + h_{21}v + 1}$$

### 10.2. Công cụ Calib Hand-Eye: `calibrate_camera_to_dobot.py`
- Tự động nạp ma trận nội tại $K$ và hệ số méo thấu kính $D$ từ `camera_calibration_toolkit/calib_data_mono.json` để khử méo ảnh (`cv2.undistort`).
- Cho phép người dùng click 4 điểm mốc tương ứng giữa Pixel $(u, v)$ và tọa độ robot $(X, Y)$.
- Tự động tính ma trận $H$ và lưu vào `homography_dobot.json` và `homography_dobot.npy`.
- Tích hợp chế độ kiểm chứng thời gian thực (Verify Mode).

### 10.3. Bộ thông số Calib chuẩn mới nhất (Cập nhật 26/09/2026):
* **Điểm 1:** Pixel $(580, 354) \to (144.9, -147.9)$
* **Điểm 2:** Pixel $(754, 476) \to (194.4, -92.7)$
* **Điểm 3:** Pixel $(595, 605) \to (243.8, -143.9)$
* **Điểm 4:** Pixel $(419, 471) \to (195.9, -200.8)$
* **Sai số trung bình (Mean Error):** $0.00\text{ mm}$

### 10.4. Lưu ý về hiện tượng ngoại suy phối cảnh (Perspective Extrapolation Divergence):
- Khi một khối màu nằm **hoàn toàn bên trong** tứ giác 4 điểm mốc: Phép chiếu nội suy cực kỳ chính xác.
- Khi một khối màu bị đặt **ra ngoài phạm vi 4 điểm mốc**: Góc nghiêng camera bị khuếch đại phi tuyến tính, làm tọa độ $X$ bị tụt dốc (ví dụ: khối Vàng trước đó bị tụt xuống $X=35.2$).
- **Nguyên tắc cốt lõi:** Khi calib, luôn chọn 4 điểm rải rộng ra 4 góc xa nhất của vùng thao tác bàn làm việc để bao trọn mọi khối màu cần gắp.

---

## 11. ỨNG DỤNG TỰ ĐỘNG PHÂN LOẠI KHỐI MÀU (DOBOT_AUTO_SORT.PY)

File mã nguồn chính: `Object_Detection/dobot_auto_sort.py` (và bản đồng bộ `DOBOT/dobot_auto_sort.py`).

### 11.1. Các thông số làm việc vật lý tối ưu:
- **Tọa độ điểm thả phôi cố định:**
  - $X = 267.7\text{ mm}, Y = 28.7\text{ mm}, Z_{\text{Flange}} = -44.0\text{ mm}$
  - Bán kính ngang: $R \approx 269.2\text{ mm}$ (nằm ngay phía trước robot, góc hơi chếch trái, tầm với cực kỳ an toàn).
- **Độ cao hút phôi chuẩn:**
  - $Z_{\text{Flange}} = -51.7\text{ mm}$ (tương ứng $Z_{\text{TCP}} = -111.2\text{ mm}$, đã hạ $0.4\text{ cm}$ theo tinh chỉnh thực tế).
- **Độ cao di chuyển an toàn (Safe Arch Z):**
  - $Z_{\text{Safe}} = +35.0\text{ mm}$ (mặt bích nhấc cao vượt chướng ngại vật).
- **Độ bù vị trí hút (Offset):**
  - $\text{Offset } X = +5.0\text{ mm}$ ($+0.5\text{ cm}$ để căn thẳng tâm giác hút vào phôi).

### 11.2. Chu trình gắp thả an toàn (Safe Arch Pick-and-Place Worker):
1. Robot bay trên đỉnh phôi ở độ cao an toàn $Z_{\text{Safe}} = 35.0\text{ mm}$.
2. Bật bơm hút chân không (Suction on).
3. Hạ thẳng trục $Z$ xuống độ cao hút $Z_{\text{Flange}} = -51.7\text{ mm}$.
4. Nhấc thẳng lên độ cao an toàn $Z_{\text{Safe}}$.
5. Bay ngang sang khay thả ($X=267.7, Y=28.7$).
6. Hạ xuống khay ($Z_{\text{Flange}} = -44.0\text{ mm}$).
7. Tắt bơm & xả khí nhả phôi (Suction off).
8. Nhấc lên cao an toàn và hoàn tất chu trình.

### 11.3. Phương thức tương tác điều khiển:
- **Click chuột trái:** Click trực tiếp vào bất kỳ khối màu nào trên cửa sổ camera để robot gắp khối đó.
- **Phím cách [SPACE]:** Tự động gắp khối màu đầu tiên tìm thấy.
- **Phím [A]:** Bật/Tắt chế độ tự động hoàn toàn (Auto Sorting liên tục sau mỗi 2 giây).
- **Phím [Q] / [ESC]:** Thoát an toàn.

---

## 12. BẢN CHẤT CƠ CHẾ HOMING PHẦN CỨNG VS ĐIỂM MẪU TRÊN WEB

### 12.1. Nút "🏠 Về Gốc" ở thanh Footer:
- Kích hoạt lệnh Homing cơ học cấp thấp của vi điều khiển Dobot (Lệnh `ID 31 - SetHOMECmd`).
- Dobot sẽ tự động xoay các trục để chạm vào các công tắc cữ hành trình quang học, sau đó firmware tự động di chuyển về **vị trí Home xuất xưởng mặc định**:
  - Tọa độ mặt bích (Flange): $X = 250.0\text{ mm}, Y = 0.0\text{ mm}, Z_{\text{Flange}} = 50.0\text{ mm}$.
  - Do cánh tay gắn đầu hút dài $59.5\text{ mm}$, nên tọa độ mũi hút (TCP) hiển thị trên màn hình là:
    $$Z_{\text{TCP}} = Z_{\text{Flange}} - 59.5 = 50.0 - 59.5 = \mathbf{-9.5\text{ mm}}.$$
  - Hiển thị trên màn hình: **`TCP: (249.9, 0.0, -9.5)`** chính là vị trí gốc chuẩn xác của phần cứng Dobot!

### 12.2. Điểm mẫu nhanh "🏠 Home (240, 0, 50)" trên giao diện Web:
- Nút này thuộc mục *"⚡ ĐIỂM MẪU NHANH"*, có chức năng **nạp tọa độ đích vào cục mục tiêu 3D (Target Beacon)**, chứ không tự ý kích hoạt robot di chuyển.
- Để robot di chuyển tới tọa độ $(240, 0, 50)$, người dùng chỉ cần bấm nút **"🚀 Bay Thẳng (Direct)"** hoặc **"📦 Nhấc An Toàn (Safe Jump)"**.

---

## 13. QUẢN LÝ MÃ NGUỒN GIT REPOSITORY

- Thư mục `DOBOT` (`/home/danh/FABLAB/DOBOT`) đã được khởi tạo thành Git repository độc lập với nhánh `main`.
- Đã cấu hình `.gitignore` loại trừ file binary nặng (`cloudflared` 40MB) và log files.
- Đã đóng gói đầy đủ:
  - Hệ thống Digital Twin Web 3D (`dobot_visualizer.html`, `dist_netlify/`)
  - Server Tornado API (`dobot_live_server.py`)
  - Module AI phân loại (`dobot_auto_sort.py`)
  - File ma trận calib (`homography_dobot.json`, `.npy`)
- Sẵn sàng liên kết remote và push lên GitHub cá nhân (`DanhCon`):
```bash
cd /home/danh/FABLAB/DOBOT
git remote add origin git@github.com:DanhCon/<ten-repo>.git
git push -u origin main
```
---

## 14. CÁC TÍNH NĂNG CẦN SỬA & HƯỚNG HOÀN THIỆN (BUGS TO FIX & ROADMAP)

Dưới đây là phân tích chi tiết các vấn đề kỹ thuật phát sinh trong quá trình vận hành thực tế và giải pháp kỹ thuật cần áp dụng:

### 14.1. Lỗi 1: Thiếu bộ lọc vùng an toàn khi Click chuột và bấm phím [SPACE] (`dobot_auto_sort.py`)
- **Hiện trạng mã nguồn:**
  - Trong chế độ tự động `[A]`, vòng lặp đã có sẵn bộ lọc an toàn:
    ```python
    r_target = math.sqrt(best_cube['rx']**2 + best_cube['ry']**2)
    if not (140.0 <= r_target <= 330.0):
        print(f"[Auto] Khối màu nằm ngoài vùng an toàn (R={r_target:.1f}mm), bỏ qua...")
        continue
    ```
  - Tuy nhiên, trong sự kiện **Click chuột trái (`on_mouse`)** và **Bấm phím cách (`ord(' ')`)**:
    Tọa độ sau khi giải mã qua ma trận Homography được đưa thẳng vào luồng gắp `pick_and_place_async(rx, ry, drop_pos)` mà **hoàn toàn không kiểm tra giới hạn không gian làm việc**.

- **Hành vi thực tế của Dobot khi người dùng chọn vật thể ngoài tầm với:**
  1. **Phần cứng báo động (Alarm State):** Khi tọa độ gửi xuống có bán kính $R < 140\text{ mm}$ (quá gần chân đế) hoặc $R > 330\text{ mm}$ (vượt quá chiều dài vươn cơ học), thuật toán Động học nghịch (IK) trên firmware STM32 không thể giải được nghiệm. Firmware lập tức kích hoạt cờ lỗi:
     - `0x10`: `ERR_PLAN_INV_CALC` (Lỗi thuật toán quy hoạch đường đi).
     - `0x11`: `ERR_PLAN_INV_SINGULARITY` (Rơi vào điểm kỳ dị động học).
     - `0x12`: `ERR_PLAN_INV_LIMIT` (Vượt quá giới hạn tọa độ phần mềm).
  2. **Trạng thái robot:** Cánh tay Dobot lập tức phanh dừng khẩn cấp, **đèn LED chân đế chuyển sang MÀU ĐỎ**, và **còi buzzer phát tiếng kêu bíp liên tục**.
  3. **Hiện tượng "Chu trình ma" (Ghost Cycle):** Do luồng `pick_and_place_async` trong Python được viết dạng tuần tự bằng `time.sleep()`, Python không hề biết robot đã bị khóa cứng do Alarm. Luồng vẫn tiếp tục:
     - Bật bơm hút chân không (tiếng rơ-le nhảy rè rè).
     - Chờ 1.5s $\to$ gửi lệnh hạ trục $Z$ ảo $\to$ chờ 1.0s $\to$ gửi lệnh nhấc lên ảo $\to$ gửi lệnh bay sang khay thả ảo $\to$ tắt bơm hút.
     - Trong suốt thời gian đó, cánh tay robot vẫn đứng im tại chỗ do đang bị kẹt lỗi phần cứng.

- **Giải pháp kỹ thuật cần triển khai:**
  - Xây dựng hàm kiểm tra không gian làm việc chuẩn:
    ```python
    def is_safe_workspace(rx, ry):
        r = math.sqrt(rx**2 + ry**2)
        # Bán kính an toàn: 140mm <= R <= 330mm và X >= 70mm (phía trước robot)
        return (140.0 <= r <= 330.0) and (rx >= 70.0)
    ```
  - Trong `on_mouse` và `ord(' ')`: Nếu `not is_safe_workspace(rx, ry)`, **từ chối gửi lệnh gắp**, hiển thị cảnh báo đỏ OSD trên khung hình camera:
    `cv2.putText(frame, "CẢNH BÁO: VẬT THỂ NGOÀI TẦM VỚI (OUT OF WORKSPACE)!", ...)` và in ra terminal để người dùng biết.

---

### 14.2. Lỗi 2: Chu trình gắp chạy mù theo `time.sleep` (Open-loop Execution)
- **Nguyên nhân cốt lõi:**
  - Sử dụng `time.sleep(1.0)` đến `time.sleep(1.5)` giữa các bước di chuyển là cơ chế điều khiển vòng hở (Open-loop).
  - Nếu vi điều khiển gặp sự cố (vướng cản, quá tốc độ `0x30`, chạm cữ `0x40`, hoặc mất kết nối serial), chương trình Python hoàn toàn không nhận biết được.
- **Giải pháp kỹ thuật cần triển khai:**
  - Thay thế `time.sleep` bằng việc đọc chỉ số hàng đợi lệnh (`QueuedCmdIndex`):
    - Mỗi lệnh `set_ptpcmd` trả về một `cmd_index`.
    - Viết hàm `wait_cmd_finished(device, target_index, timeout=5.0)`: Đọc `get_queued_cmd_current_index()`, chỉ chuyển sang bước tiếp theo khi robot đã hoàn thành lệnh hoặc hết timeout.
  - Trước mỗi bước chuyển động, đọc cờ Alarm `ID 20`. Nếu phát hiện có lỗi $\\neq 0$, lập tức hủy chu trình (abort), ngắt bơm hút và báo lỗi lên giao diện.

---

### 14.3. Cải tiến 3: Trải nghiệm người dùng với nút "Về Gốc (Homing)"
- **Vấn đề đặt ra:**
  - Khi người dùng bấm nút "Về Gốc" trên Web, lệnh Homing phần cứng (`ID 31 - SetHOMECmd`) sẽ đưa robot về điểm gốc xuất xưởng của mặt bích ($X=250.0, Y=0.0, Z_{\\text{Flange}}=50.0 \\implies Z_{\\text{TCP}}=-9.5\\text{ mm}$).
  - Người dùng thường mong muốn robot sau khi Homing xong sẽ tự động nâng đầu hút lên vị trí làm việc an toàn chuẩn $(X=240.0, Y=0.0, Z=50.0)$.
- **Giải pháp kỹ thuật cần triển khai:**
  - Trong `dobot_live_server.py`, tại hàm xử lý action `"home"`, sau khi phát lệnh Homing thành công, lập tức gửi tiếp lệnh di chuyển PTP đưa robot tới điểm làm việc mong muốn $(240, 0, 50)$ để sẵn sàng gắp thả.

---

### 14.4. Cải tiến 4: Bộ lọc vùng lồi (Convex Hull Boundary Check) cho thị giác Homography

---

## 16. TÍCH HỢP RAY TRƯỢT (SLIDING RAIL KIT) - CHẨN ĐOÁN LỖI PHẦN CỨNG, HIỆU CHUẨN TỈ LỆ & ĐIỀU KHIỂN HOÀN CHỈNH

### 16.1. Tổng quan cấu hình phần cứng
* **Động cơ ray trượt:** Động cơ bước NEMA 17/42 cắm vào cổng **Stepper 1** (`RAIL_INDEX = 0` trên Dobot Magician).
* **Công tắc hành trình (Limit Switch):** Loại tiếp điểm cơ 2 dây, thường đóng (**NC - Normally Closed**):
  * Lúc bình thường (chưa chạm): 2 tiếp điểm chạm nhau $\to$ Thông mạch ($0\,\Omega$).
  * Lúc bị chạm (nhấn vào switch): Tiếp điểm mở ra $\to$ Ngắt mạch (Hở mạch).
* **Cổng kết nối cảm biến:** Cắm vào cổng **GP2** màu xanh lá ở hàng dưới trên cẳng tay robot (Forearm).

---

### 16.2. Nhật ký lỗi đã gặp & Cách khắc phục toàn diện (Troubleshooting Log)

#### ❌ Lỗi 1: Không đọc được tín hiệu ngõ vào số từ cảm biến (Đọc luôn trả về 0)
* **Hiện tượng:** Cắm cảm biến vào nhưng khi kiểm tra bằng code Python, tín hiệu không bao giờ thay đổi giữa 0 và 1.
* **Nguyên nhân cốt lõi:**
  * Mã lệnh cũ sử dụng **Command ID 132** (`SetIODO / GetIODO` - hàm đọc/ghi Digital Output). Trong firmware Dobot, hàm này chỉ đọc lại thanh ghi đệm ngõ ra chứ không đọc trạng thái vật lý ngõ vào.
  * Mã lệnh chuẩn của giao thức Dobot Communication Protocol để đọc mức logic ngõ vào Digital Input là **Command ID 133 (`GetIODI`)**.
* **Cách khắc phục:**
  * Sửa lại hàm gửi nhận gói tin sang Command ID 133 với payload `bytes([pin_address])`. Giá trị trả về tại `par[1]` phản ánh chính xác 100% mức logic $0$ (LOW) hoặc $1$ (HIGH) của chân vi điều khiển.

---

#### ❌ Lỗi 2: Đo đồng hồ VOM ở 2 đầu dây cảm biến chỉ ra 0V và 50mV (không nhảy mức logic)
* **Hiện tượng:** Người dùng đo thông mạch công tắc bên ngoài thì tốt, nhưng khi cắm vào chân 1 và chân 3 cổng GP2 và đo điện áp thì lúc không nhấn ra $0\text{ V}$, lúc nhấn ra $50\text{ mV}$ (gần như $0\text{ V}$), robot không thể nhận biết được trạng thái.
* **Nguyên nhân phần cứng:**
  * Công tắc hành trình 2 dây là linh kiện bị động (Passive switch), bản thân nó không có nguồn điện.
  * Cổng GP2 trên tay robot có sơ đồ 4 chân:
    * `Chân 1 (ngoài cùng bên trái)`: `GND` (Mass $0\text{V}$).
    * `Chân 2`: `REV` (`EIO13`).
    * `Chân 3`: `PWM` (`EIO14`).
    * `Chân 4 (ngoài cùng bên phải)`: `ADC` (`EIO15`).
  * Khi cắm công tắc vào Chân 1 (GND) và Chân 3 (EIO14), nếu người dùng đếm ngược từ phải sang trái thì chân cắm sẽ là Chân 4 (ADC) và Chân 2 (REV), không hề có chân Mass GND!
  * Đồng thời, khi công tắc hở mạch, nếu chân tín hiệu không có điện áp kéo lên thì nó sẽ lơ lửng ở $0\text{ V}$ (50 mV đo được chỉ là dòng rò nhiễu que đo).
* **Cách khắc phục:**
  * Chuẩn hóa chiều đếm chân theo sơ đồ mặt cắt giắc cắm: Nhìn trực diện cổng cắm với **rãnh gờ khuyết (notch) quay lên trên**, đếm từ **TRÁI sang PHẢI**:
    * **Dây 1:** Cắm vào **Chân 1 (ngoài cùng bên trái - `GND`)**.
    * **Dây 2:** Cắm vào **Chân 3 (thứ ba từ trái sang - `EIO14`)**.
  * Kiểm tra an toàn điện: Khi hở mạch, Chân 3 có điện áp kéo nội $\approx 3.3\text{ V}$. Dòng điện khi thông mạch xuống GND chỉ là $I = \frac{3.3\text{V}}{40.000\,\Omega} \approx 0.08\text{ mA}$, an toàn tuyệt đối cho vi điều khiển, không lo chập cháy.
  * Kết quả đo: Lúc không nhấn ra $0\text{ V}$ (`EIO14 = 0`), lúc nhấn ra $3.3\text{ V}$ (`EIO14 = 1`). Tín hiệu nhảy tức thì và cực kỳ ổn định.

---

#### ❌ Lỗi 3: Động cơ phát tiếng rên/rung ("è è") nhưng thanh ray đứng im (Stepper Stalling)
* **Hiện tượng:** Sau khi chạy Homing xong, ra lệnh di chuyển (`--mm 150` hoặc `--jog`) thì động cơ chỉ kêu gừ gừ/rung lắc tại chỗ mà không quay.
* **Nguyên nhân kỹ thuật:**
  * **Tần số xung khởi động quá cao:** Lệnh `SetEMotorS` (ID 136) phát xung trực tiếp đến động cơ bước mà không có đường cong gia tốc mềm (S-curve ramp). Code ban đầu đặt mặc định `50 mm/s` (tương đương $10.000\text{ xung/giây}$). Động cơ bước mang tải nặng của cánh tay robot khi đang đứng yên không thể bắt kịp từ trường ở tần số $10\text{ kHz} \to$ sinh ra hiện tượng **mất bước / kẹt tần số (stalling)**.
  * **Lệnh phanh dập tắt:** Hàm `close()` khi kết thúc script vô tình gọi `self.stop()`, dập tắt ngay động cơ khi vừa mới chớm quay.
* **Cách khắc phục:**
  * Cố định dải vận tốc vận hành tối ưu ở **$25 - 40\text{ mm/s}$ (tương đương $2.000 - 3.200\text{ xung/giây}$)**. Ở dải này, mô-men xoắn của động cơ đạt cực đại, kéo tải cánh tay robot êm ái, mạnh mẽ và không bao giờ kẹt bước.
  * Loại bỏ lệnh gọi `stop()` cưỡng bức trong hàm đóng kết nối thông thường.

---

#### ❌ Lỗi 4: Tọa độ di chuyển bị sai lệch gấp 2.5 lần (Lệnh chạy 10 cm nhưng ray đi 25 cm)
* **Hiện tượng:** Ra lệnh chạy $10\text{ cm}$ ($100\text{ mm}$), ray thực tế chạy vọt ra tận vạch $25 - 26\text{ cm}$.
* **Nguyên nhân & Căn cứ cơ khí:**
  * File cũ dùng thông số giả định `PULSES_PER_MM = 200`.
  * Khi yêu cầu $100\text{ mm}$, máy phát: $100 \times 200 = 20.000\text{ xung}$.
  * Cơ cấu thực tế của ray Dobot:
    * Động cơ bước $1.8^\circ$ / bước = $200\text{ bước/vòng}$.
    * Vi bước $1/16$ = $3.200\text{ xung/vòng}$.
    * Puly đai GT2 20 răng (bước $2\text{ mm}$) = $40\text{ mm/vòng}$.
    * Hệ số cơ khí chuẩn: $\frac{3.200\text{ xung}}{40\text{ mm}} = \mathbf{80\text{ xung / mm}}$.
  * Kiểm chứng thực nghiệm: $\text{Quãng đường thực tế} = \frac{20.000\text{ xung}}{80\text{ xung/mm}} = 250\text{ mm} = \mathbf{25\text{ cm}}$ (khớp 100% với phép đo thước).
* **Cách khắc phục:**
  * Cập nhật hệ số chuẩn xác: `PULSES_PER_MM = 80`. Sau khi chỉnh, lệnh `--mm 100` đi đúng chính xác vạch $10\text{ cm}$ từng milimet.

---

#### ❌ Lỗi 5: Mất trạng thái vị trí (Homing State Loss) giữa các lần chạy lệnh CLI
* **Hiện tượng:** Chạy `python3 dobot_rail_controller.py --home` thành công, nhưng khi gõ tiếp lệnh `python3 dobot_rail_controller.py --mm 150` thì bị báo lỗi "Cần chạy Homing trước".
* **Nguyên nhân:** Biến `current_pos` lưu trong RAM của tiến trình Python bị giải phóng khi lệnh trước kết thúc.
* **Cách khắc phục:**
  * Tích hợp cơ chế tự động đọc/ghi vị trí vào file trạng thái ẩn `.rail_state.json`.
  * Hỗ trợ lệnh chạy gộp: `python3 dobot_rail_controller.py --home --mm 150`.
  * Bổ sung chế độ dòng lệnh tương tác trực tiếp (`-i`): giữ kết nối Serial liên tục để gõ lệnh điều khiển tức thì.

---

### 16.3. Bảng tra cứu lệnh điều khiển ray trượt (`dobot_rail_controller.py`)

| Thao tác | Cú pháp lệnh | Mô tả chi tiết |
| :--- | :--- | :--- |
| **Về gốc Home** | `python3 dobot_rail_controller.py --home` | Tự động dò công tắc, phanh dừng và gán tọa độ $0.0\text{ mm}$ |
| **Home rồi chạy ngay** | `python3 dobot_rail_controller.py --home --mm 150` | Về gốc xong tự động chạy thẳng ra vị trí $150\text{ mm}$ ($15\text{ cm}$) |
| **Đi tới tọa độ mm** | `python3 dobot_rail_controller.py --mm 200` | Di chuyển đến tọa độ tuyệt đối $200\text{ mm}$ ($20\text{ cm}$) |
| **Nhích tiến tương đối** | `python3 dobot_rail_controller.py --jog 50` | Nhích tiến thêm $5\text{ cm}$ so với vị trí hiện tại |
| **Nhích lùi tương đối** | `python3 dobot_rail_controller.py --jog -50` | Nhích lùi lại $5\text{ cm}$ (tự ngắt nếu vô tình chạm switch) |
| **Lùi về vạch gốc** | `python3 dobot_rail_controller.py --mm 0` | Chạy lùi về lại điểm $0.0\text{ mm}$ |
| **Kiểm tra trạng thái** | `python3 dobot_rail_controller.py --status` | Xem vị trí hiện tại và mức logic của công tắc hành trình |
| **Dừng khẩn cấp** | `python3 dobot_rail_controller.py --stop` | Ngắt xung và phanh khựng động cơ ngay lập tức |
| **Giao diện tương tác** | `python3 dobot_rail_controller.py -i` | Giữ kết nối cổng COM, gõ số mm hoặc lệnh trực tiếp |

---

## 17. TÍCH HỢP MÔ HÌNH 3D & URDF RAY TRƯỢT VÀO HỆ THỐNG WEB LIVE SERVER (2026-10-03)

### 17.1. Bối cảnh & Mục tiêu
* **Yêu cầu:** 
  1. Tạo các file mô tả robot URDF / Xacro chuẩn cho Dobot Magician kèm ray trượt Dobot Sliding Rail Kit (khớp prismatic hành trình $0 - 1000\text{ mm}$).
  2. Dựng mô hình 3D chi tiết cao của ray trượt trong Three.js (thanh nhôm định hình 1120mm, 2 thanh ti dẫn hướng mạ crom $\varnothing 12\text{ mm}$, dây đai GT2, cụm động cơ NEMA 17, cữ chặn, công tắc hành trình có đèn LED và thước milimet).
  3. Thêm nút chuyển đổi chế độ trên giao diện Web 3D:
     * **`[ 🤖 Chỉ Dobot ]`**: Robot đứng độc lập trên bàn làm việc tại gốc $(0, 0, 0)$.
     * **`[ 🛤️ Dobot + Ray trượt ]`**: Robot được gắn trên bàn trượt cơ khí, di chuyển mượt mà dọc theo trục $L$ ($0.0 - 1000.0\text{ mm}$).
  4. Đồng bộ 2 chiều qua WebSocket với `dobot_live_server.py` với hệ số chuẩn xác $80\text{ xung/mm}$, tự động cập nhật vị trí $L$ và trạng thái công tắc hành trình trong telemetry.

### 17.2. Các tệp tin đã tạo và cập nhật
* **`dobot_sliding_rail.urdf`**: File URDF mô tả cấu trúc cơ khí độc lập của ray trượt (khớp `rail_joint` dạng prismatic, cự ly $0.0 - 1.0\text{ m}$, giới hạn lực và vận tốc, bàn trượt `rail_carriage_link` và mặt bích gá robot).
* **`dobot_with_rail.urdf.xacro`**: File XACRO kết hợp toàn bộ cánh tay robot 4-DOF Dobot Magician với ray trượt 1-DOF thành hệ thống 5-DOF hoàn chỉnh theo chuẩn ROS/MoveIt.
* **`dobot_live_server.py`**: Tích hợp các hàm điều khiển ray trượt (`rail_home`, `rail_move_to`, `rail_jog`, `rail_stop`, `get_rail_switch`), xử lý lệnh trong background thread để không chặn luồng mạng, nhúng trường `l`, `rail_switch`, `rail_homed` vào gói tin telemetry định kỳ 50ms.
* **`dobot_visualizer.html` & `dist_netlify/index.html`**:
  * Mô hình Three.js `createSlidingRailMesh()` chân thực với độ chi tiết cao, thước khắc laser milimet, đèn LED cữ hành trình đổi màu theo trạng thái cảm biến.
  * Nút chuyển đổi chế độ `[ 🤖 Chỉ Dobot ]` $\longleftrightarrow$ `[ 🛤️ Dobot + Ray trượt ]`.
  * Tab điều khiển riêng **🛤️ Ray Trượt**: phím Home ray, slider $0 - 1000\text{ mm}$, phím Jog $\pm 10/50\text{ mm}$, các mốc nhảy nhanh $0, 250, 500, 750, 1000\text{ mm}$, bộ chọn tốc độ $20 - 60\text{ mm/s}$.
  * Tự động bù trừ tọa độ không gian 3D (`baseOffset`) cho điểm đích, vòng tâm ngắm và đường gióng rơi bám theo đế robot khi trượt dọc thanh ray.

### 17.3. Khắc phục lỗi dừng ray & Mở rộng vùng an toàn di chuyển phối hợp (2026-10-03)
* **Lỗi 1: Nhấn dừng ray ngoài đời thì dừng nhưng trong 3D Simulation vẫn tiếp tục chạy:**
  * *Nguyên nhân:* Hàm `animateRailMove()` chạy qua vòng lặp `requestAnimationFrame(step)` không giữ ID hủy frame và không kiểm tra cờ dừng; đồng thời nút "Dừng ray" chỉ gửi `sendAction('rail_stop')` xuống server mà không ngắt hoạt hình client.
  * *Khắc phục:* Thêm biến `railAnimationFrameId` và hàm `stopRailMotion()` gọi `cancelAnimationFrame(railAnimationFrameId)`, đặt `isRailAnimating = false`, ghim vị trí `updateRailPosition()` tức thời. Trong `ws.onmessage`, khi nhận telemetry `rail_moving === false`, client tự động hủy hoạt hình và snap vị trí thật.
* **Lỗi 2: Đang chạy Homing ray mà nhấn Dừng thì chỉ khựng lại 1 chút rồi lại chạy tiếp:**
  * *Nguyên nhân:* Hàm `DobotController.rail_home()` trong server chạy luồng nền có 2 vòng lặp lớn (Coarse search 65 bước và Fine search 30 bước). Lệnh dừng `rail_stop()` chỉ ngắt xung của phân đoạn hiện tại mà không thoát khỏi vòng lặp `for`, khiến vòng lặp tiếp tục phát xung cho bước tiếp theo.
  * *Khắc phục:* Thêm cờ ngắt `self.stop_requested` vào `DobotController`. Khi gọi `rail_stop()`, bật `self.stop_requested = True`. Trong toàn bộ các vòng lặp coarse/fine search và thời gian chờ của `rail_home()` cũng như `rail_jog()`, kiểm tra liên tục `if self.stop_requested: self.rail_stop(); return False`. Đồng thời, nút Dừng khẩn cấp toàn hệ thống `emergency_stop()` cũng gọi kèm `self.rail_stop()`.
* **Tính năng: Vùng an toàn mở rộng (Expanded Workspace) & Di chuyển phối hợp Ray + Dobot:**
  * *Vùng an toàn mở rộng:* Nhờ có hành trình trượt $1000\text{ mm}$ của ray (Three.js $Z \in [-500, +500\text{ mm}]$), vùng làm việc an toàn của Dobot được mở rộng từ hình tròn bán kính $330\text{ mm}$ thành hình chữ nhật dạng sân vận động (stadium capsule envelope) dài $1660\text{ mm}$ dọc theo ray, với dải vươn an toàn trước mặt ray $X \in [140, 330\text{ mm}]$ và hai đầu bán nguyệt mở rộng.
  * *Mô hình trực quan:* Tạo nhóm `railWorkspaceZoneGroup` trong Three.js hiển thị dải an toàn màu xanh cyan phát sáng trên sàn kèm viền cảnh báo đỏ cam khi bật chế độ Ray trượt.
  * *Thuật toán định vị tối ưu & Di chuyển phối hợp 2 bước:*
    1. Khi người dùng kéo "cục đích" 3D hoặc click chọn điểm dọc bàn làm việc:
       $$L_{optimal} = \text{clamp}(Z_{world} + 500.0, 0.0, 1000.0)$$
       $$Z_{carriage} = L_{optimal} - 500.0$$
       $$X_{arm\_local} = X_{world},\quad Y_{arm\_local} = -(Z_{world} - Z_{carriage})$$
       $$r_{arm\_local} = \sqrt{X_{arm\_local}^2 + Y_{arm\_local}^2}$$
    2. Nếu $r_{arm\_local} < 140\text{ mm}$, $r_{arm\_local} > 330\text{ mm}$ hoặc $Z_{tcp} \notin [-120, 150\text{ mm}]$: Hệ thống hiển thị cảnh báo quá tầm và chặn không cho di chuyển.
    3. Khi bấm **[📦 Nhấc An Toàn (Safe Jump)]** hoặc **[🚀 Bay Thẳng (Direct)]**:
       * **Bước 1 (Di chuyển ray):** Ray trượt tự động chạy đến vị trí $L_{optimal}$ để đón cục đích.
       * **Bước 2 (Di chuyển Dobot):** Cánh tay Dobot vươn chính xác đến tọa độ đích $(X_{arm\_local}, Y_{arm\_local}, Z_{tcp})$.




