#!/bin/bash
set -e

# 1. Nạp môi trường ROS 2 Humble
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
else
    echo "[!] Không tìm thấy ROS 2 tại /opt/ros/humble/setup.bash"
    exit 1
fi

# 2. Định cấu hình AMENT_PREFIX_PATH cục bộ cho dobot_description
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AMENT_PREFIX_PATH="$SCRIPT_DIR/install_local:$AMENT_PREFIX_PATH"

echo "=========================================================="
echo "🚀 KHỞI CHẠY DOBOT MAGICIAN TRÊN RVIZ2 (ROS 2 HUMBLE)"
echo "   Hệ thống: Ray trượt 1.0m + Dobot 4-DOF + 3D CAD Meshes"
echo "=========================================================="

# 3. Khởi chạy ROS 2 launch file
ros2 launch dobot_description display.launch.py has_rail:=true tool:=suction_cup "$@"
