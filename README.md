# 🦾 Dobot Magician 3D Digital Twin & AI Vision Auto-Sorting

Hệ thống điều khiển, bản sao số 3D thời gian thực (**Digital Twin**) và phân loại vật thể tự động (**AI Computer Vision**) dành cho cánh tay robot công nghiệp **Dobot Magician** trên hệ điều hành Linux (Ubuntu).

---

## 🌟 Tính Năng Nổi Bật (Key Features)

### 1. 🌐 Bản Sao Số 3D Thời Gian Thực (Digital Twin Web)
* **Giao diện Three.js mượt mà:** Đồng bộ tư thế thực của cánh tay robot với tần số 20Hz qua WebSocket.
* **Cục Điểm Đích 3D Tương Tác (3D Interactive Target Gizmo):** Điều khiển điểm đến trực quan trong không gian 3 chiều bằng các trục kéo mũi tên (TransformControls) hoặc click trực tiếp lên mặt bàn 3D.
* **Động học Nghịch Thông Minh (Kinematics & Reachability Check):** Tự động tính toán góc khớp (Inverse Kinematics), cảnh báo màu đỏ/xanh thời gian thực nếu điểm đến vượt quá tầm với hoặc quá gần chân đế.
* **Hệ thống điều khiển đa dạng:** Hỗ trợ phím Jog nhanh (chọn bước 1/5/10/20/50mm), thanh trượt Descartes XYZ và góc khớp $J_1 - J_4$.
* **Giám sát & Khôi phục lỗi 1 chạm:** Tự động giải mã cờ Alarm phần cứng của Dobot và nút Reset lỗi nhanh không cần khởi động lại.

### 2. 👁️ Thị Giác Máy Tính & Hiệu Chuẩn Hand-Eye (AI Vision & Calibration)
* **Khử méo thấu kính:** Tự động nạp ma trận nội tại $K$ và hệ số méo $D$ (`calib_data_mono.json`) để nắn phẳng ảnh (`cv2.undistort`).
* **Hiệu chuẩn tọa độ Camera - Robot (Planar Homography):** Công cụ `calibrate_camera_to_dobot.py` cho phép click 4 điểm mốc để sinh ma trận biến đổi phối cảnh 2D phẳng chuẩn xác với sai số $0.00\text{ mm}$.
* **Nhận diện đa vật thể:** Hỗ trợ mô hình YOLO (`best_v8_more_augmentation.pt` / `best_v11.pt`) hoặc bộ lọc màu đa dải OpenCV HSV đạt tốc độ 40 - 60 FPS.

### 3. 🎯 Chu Trình Tự Động Phân Loại Khối Màu (Auto-Sorting)
* **Quỹ đạo an toàn (Safe Arch Pick-and-Place):** Bay trên đỉnh phôi an toàn $\to$ Bật hút chân không $\to$ Hạ thẳng trục $Z$ gắp phôi $\to$ Nhấc lên cao $\to$ Bay sang khay thả $\to$ Hạ xuống khay $\to$ Xả khí nhả phôi $\to$ Rút về cao độ an toàn.
* **Chế độ kích hoạt linh hoạt:** Click chuột vào khối màu trên camera, phím cách `[SPACE]` hoặc tự động phân loại liên tục `[A]`.

### 4. 🌍 Xuất Bản Điều Khiển Online (Remote Cloud Publishing)
* Tích hợp sẵn thư mục `dist_netlify/` sẵn sàng kéo thả hoặc kết nối Git lên Netlify.
* Script `./start_online.sh` tự động thiết lập Cloudflare Tunnel (`cloudflared`) để điều khiển từ xa qua Internet / 4G mà không cần mở port modem.

---

## 📐 Thông Số Vật Lý & Không Gian Hoạt Động (Specifications)

| Thông số | Giá trị | Ghi chú |
| :--- | :--- | :--- |
| **Cổng giao tiếp Serial** | `/dev/ttyUSB0` hoặc `/dev/ttyUSB1` | Tự động quét và nhận diện |
| **Baudrate** | `115200` bps (8N1) | Giao thức nhị phân Dobot Protocol v1.1.4 |
| **Bù trừ đầu hút (Tool Offset Z)** | **`59.5 mm`** | $Z_{\text{TCP}} = Z_{\text{Flange}} - 59.5\text{ mm}$ |
| **Bán kính làm việc an toàn ($R$)** | $140.0\text{ mm} \le R \le 330.0\text{ mm}$ | Dưới 140mm đâm chân đế, trên 330mm quá tầm với |
| **Cao độ mũi hút an toàn ($Z_{\text{TCP}}$)** | $-120.0\text{ mm} \le Z_{\text{TCP}} \le +150.0\text{ mm}$ | Tránh đâm mũi hút xuống mặt bàn |
| **Độ cao hút phôi tối ưu** | $Z_{\text{Flange}} = -51.7\text{ mm}$ ($Z_{\text{TCP}} = -111.2\text{ mm}$) | Đã hạ áp sát mặt khối màu |
| **Tọa độ điểm thả phôi cố định** | $X = 267.7\text{ mm}, Y = 28.7\text{ mm}, Z_{\text{Flange}} = -44.0\text{ mm}$ | Nằm ngay phía trước robot ($R \approx 269.2\text{ mm}$) |
| **Độ bù vị trí hút (Offset)** | $\text{Offset } X = +5.0\text{ mm}$ | Căn thẳng tâm đầu hút |

---

## 📁 Cấu Trúc Thư Mục Dự Án (Project Structure)

```plaintext
DOBOT/
├── dobot_auto_sort.py                 # Chương trình chính: Nhận diện & tự động gắp thả
├── dobot_live_server.py               # Backend Tornado Server (WebSocket + HTTP API)
├── dobot_visualizer.html              # Frontend giao diện Web 3D Digital Twin (Three.js)
├── calibrate_camera_to_dobot.py       # Tool hiệu chuẩn Hand-Eye Homography (Pixel -> Robot mm)
├── homography_dobot.json              # Ma trận Homography calib lưu dạng JSON
├── homography_dobot.npy               # Ma trận Homography calib lưu dạng NumPy
├── move_to_point.py                   # Script điều khiển robot tới tọa độ chỉ định qua CLI
├── test_dobot.py                      # Menu Terminal kiểm tra phần cứng & test chức năng
├── start_online.sh                    # Script 1-click mở Cloudflare Tunnel điều khiển từ xa
├── start_ngrok.sh                     # Script mở tunnel ngrok kết nối Web Netlify
├── dist_netlify/                      # Thư mục web build tĩnh sẵn sàng deploy lên Netlify
│   ├── index.html
│   └── TransformControls.js
├── DOBOT_DEVELOPMENT_LOG.md           # Nhật ký kỹ thuật toàn diện, mã lỗi và giải pháp
├── ROBOT_MOTION_PLANNING_AND_KINEMATICS_GUIDE.md  # Giáo trình động học & quỹ đạo di chuyển
├── DOBOT_SPECIFICATIONS_AND_STATES.md # Tài liệu tra cứu trạng thái & thông số Dobot
└── README.md                          # Hướng dẫn sử dụng dự án này
```

---

## 🚀 Hướng Dẫn Cài Đặt (Installation)

### 1. Yêu cầu hệ thống
* Hệ điều hành: Linux (Ubuntu 20.04 / 22.04 LTS khuyến nghị) hoặc Windows 10/11.
* Python: `>= 3.8` (khuyên dùng Python 3.10).

### 2. Cấp quyền cổng Serial trên Linux
```bash
sudo usermod -aG dialout $USER
# Sau đó đăng xuất và đăng nhập lại hoặc restart máy để áp dụng
```

### 3. Cài đặt các thư viện cần thiết
```bash
pip install tornado pyserial opencv-python numpy websocket-client
# Nếu sử dụng mô hình nhận diện YOLO (tùy chọn):
pip install ultralytics
```

---

## 🕹️ Hướng Dẫn Vận Hành (Quick Start Guide)

### Bước 1: Khởi động Server điều khiển & Giao diện Web 3D
Mở Terminal và chạy:
```bash
cd DOBOT
python3 dobot_live_server.py
```
* Mở trình duyệt truy cập: **`http://localhost:8080`** (hoặc `http://localhost:8081`).
* Bạn sẽ thấy mô hình 3D của Dobot Magician di chuyển đồng bộ với robot thật bên ngoài.

---

### Bước 2: Hiệu chuẩn Camera Hand-Eye (Nếu thay đổi góc Camera)
Nếu bạn thay đổi vị trí đặt camera hoặc bàn làm việc, hãy chạy script calib:
```bash
python3 calibrate_camera_to_dobot.py --cam 0
```
1. Click chọn lần lượt 4 điểm mốc trên cửa sổ ảnh camera (nên chọn 4 góc rộng nhất của vùng làm việc).
2. Nhập tọa độ thực tế tương ứng của Dobot $(X, Y)$ tại từng điểm mốc.
3. Chương trình sẽ tự động tính ma trận và lưu đè vào `homography_dobot.json`.

---

### Bước 3: Chạy chương trình Nhận diện & Tự động Phân loại Khối màu
Mở một Terminal khác và chạy:
```bash
python3 dobot_auto_sort.py --cam 0
```
* **Thao tác điều khiển trên cửa sổ Camera:**
  * **Click chuột trái:** Nhấp vào bất kỳ khối màu nào để robot gắp khối đó.
  * **Bấm phím `[SPACE]`:** Tự động gắp khối màu đầu tiên tìm thấy.
  * **Bấm phím `[A]`:** Bật / Tắt chế độ **Tự Động Phân Loại Hoàn Toàn** (robot tự phát hiện và gắp liên tục).
  * **Bấm phím `[Q]`:** Thoát chương trình an toàn.

---

### Bước 4: Điều khiển từ xa qua Internet (Online Remote Control)
Để người khác ở ngoài mạng LAN (dùng 4G/Wifi khác) có thể truy cập điều khiển:
```bash
cd DOBOT
./start_online.sh
```
Terminal sẽ cung cấp một đường link Cloudflare dạng `https://xxxx.trycloudflare.com` để mở trên điện thoại hoặc máy tính từ xa.

---

## ⚠️ Lưu Ý An Toàn & Vận Hành (Safety Notes)

1. **Cơ chế Homing phần cứng (`ID 31`):**
   * Khi nhấn nút **"🏠 Về Gốc"** trên thanh footer, robot sẽ kích hoạt cữ hành trình quang học phần cứng và tự động đưa mặt bích về vị trí Home xuất xưởng ($X=250.0, Y=0.0, Z_{\text{Flange}}=50.0$).
   * Tọa độ đầu hút lúc này sẽ hiển thị là **`TCP: (249.9, 0.0, -9.5)`** do trừ đi chiều dài đầu hút $59.5\text{ mm}$.
   * Để robot di chuyển tới điểm đích `(240, 0, 50)`, hãy chọn điểm mẫu nhanh và bấm nút **"🚀 Bay Thẳng"** hoặc **"📦 Nhấc An Toàn"**.
2. **Khôi phục còi báo động (Alarm Reset):**
   * Nếu robot bị kẹt hoặc va chạm phát còi kêu và đèn đỏ, chỉ cần bấm nút **"🔔 Xóa Lỗi"** trên web hoặc chạy `test_dobot.py` (chọn menu 4). Hệ thống sẽ gửi bộ 3 lệnh `ID 20 -> ID 245 -> ID 240` để khôi phục đèn xanh ngay lập tức.
3. **Tránh điểm kỳ dị (Singularity):**
   * Luôn di chuyển bằng chế độ khớp (`mode=1 - MOVJ`) khi nội suy không gian để chuyển động mượt mà, không bao giờ dùng lệnh tương đối `mode=7` gần các trục giới hạn.

---

## 👨‍💻 Tác giả & Đơn vị
* **Phát triển bởi:** DanhCon (FABLAB)
* **Kho lưu trữ:** [https://github.com/DanhCon/Dobot-Fablab](https://github.com/DanhCon/Dobot-Fablab)
