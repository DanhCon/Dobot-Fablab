#!/usr/bin/env python3
import os
import sys
import xml.etree.ElementTree as ET

ROOT_DIR = "/home/danh/FABLAB/DOBOT"
PKG_DIR = os.path.join(ROOT_DIR, "dobot_description")

def test_meshes():
    print("[1] Kiểm tra tệp 3D Mesh DAE...")
    required_meshes = [
        "meshes/dae/magicianBase.dae",
        "meshes/dae/magicianLink1.dae",
        "meshes/dae/magicianLink2.dae",
        "meshes/dae/magicianLink3.dae",
        "meshes/dae/magicianLink4_default.dae",
        "meshes/dae/magicianSuctionCup.dae",
        "meshes/dae/magicianGripper.dae",
        "meshes/dae/magician_pen.dae",
        "meshes/collision/additional_elements/sliding_rail.dae",
        "meshes/collision/core/magicianBase.dae",
        "meshes/collision/core/magicianLink1.dae",
    ]
    for rel_path in required_meshes:
        full_path = os.path.join(PKG_DIR, rel_path)
        assert os.path.exists(full_path), f"Thiếu file mesh: {rel_path}"
        size = os.path.getsize(full_path)
        assert size > 1000, f"File {rel_path} có dung lượng bất thường ({size} bytes)"
        print(f"  ✓ {rel_path} ({size:,} bytes)")
    print("  -> Tất cả tệp Mesh DAE đều hợp lệ!")

def test_xml_syntax():
    print("\n[2] Kiểm tra cú pháp XML các file URDF & Package...")
    xml_files = [
        os.path.join(PKG_DIR, "package.xml"),
        os.path.join(PKG_DIR, "urdf/dobot_magician_rail.urdf.xacro"),
        os.path.join(PKG_DIR, "urdf/dobot_magician_with_rail.urdf"),
        os.path.join(PKG_DIR, "urdf/dobot_magician_standalone.urdf"),
        os.path.join(ROOT_DIR, "dobot_magician_with_rail.urdf"),
        os.path.join(ROOT_DIR, "dobot_magician_standalone.urdf"),
    ]
    for f in xml_files:
        assert os.path.exists(f), f"File không tồn tại: {f}"
        tree = ET.parse(f)
        root = tree.getroot()
        assert root is not None
        print(f"  ✓ XML Syntax OK: {os.path.basename(f)} (root: <{root.tag}>)")

def test_kinematics_tree():
    print("\n[3] Kiểm tra cây động học Kinematic Tree...")
    # Test with_rail
    rail_urdf = os.path.join(PKG_DIR, "urdf/dobot_magician_with_rail.urdf")
    tree = ET.parse(rail_urdf)
    root = tree.getroot()

    joints = {j.attrib["name"]: j for j in root.findall("joint")}
    links = {l.attrib["name"]: l for l in root.findall("link")}

    assert "world" in links
    assert "rail_base_link" in links
    assert "rail_carriage_link" in links
    assert "dobot_base_link" in links
    assert "dobot_link_1" in links
    assert "dobot_link_2" in links
    assert "dobot_link_3" in links
    assert "dobot_link_4" in links
    assert "dobot_tool_link" in links
    assert "dobot_tcp" in links

    # Check rail joint
    assert "rail_joint" in joints
    rj = joints["rail_joint"]
    assert rj.attrib["type"] == "prismatic"
    limit = rj.find("limit")
    assert float(limit.attrib["lower"]) == 0.0
    assert float(limit.attrib["upper"]) == 1.000
    print("  ✓ Cấu hình Ray trượt L (Prismatic 0 -> 1.000m): OK")

    # Check arm joints
    for jname in ["dobot_joint_1", "dobot_joint_2", "dobot_joint_3", "dobot_joint_4", "dobot_joint_5_r"]:
        assert jname in joints, f"Thiếu joint: {jname}"
        assert joints[jname].attrib["type"] == "revolute"
    print("  ✓ 5 Khớp quay (Revolute J1, J2, J3, J4, J5): OK")

    # Check mimic on joint 4
    j4 = joints["dobot_joint_4"]
    mimic = j4.find("mimic")
    assert mimic is not None
    assert mimic.attrib["joint"] == "dobot_joint_2"
    assert float(mimic.attrib["multiplier"]) == -1.0
    print("  ✓ Cơ cấu bình hành (Joint 4 mimic Joint 2 multiplier=-1.0): OK")

def test_viewer_html():
    print("\n[4] Kiểm tra Web 3D Viewer...")
    html_path = os.path.join(PKG_DIR, "view_urdf.html")
    assert os.path.exists(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    assert "slider-rail" in html
    assert "slider-j1" in html
    assert "slider-j2" in html
    assert "slider-j3" in html
    assert "slider-j4" in html
    assert "setSystemMode" in html
    assert "setTool" in html
    assert "toggleTFAxes" in html
    print("  ✓ File view_urdf.html chứa đầy đủ bộ điều khiển tương tác!")

if __name__ == "__main__":
    try:
        test_meshes()
        test_xml_syntax()
        test_kinematics_tree()
        test_viewer_html()
        print("\n=======================================================")
        print("🎉 TẤT CẢ CÁC BƯỚC KIỂM TRA ĐỀU VƯỢT QUA 100% THÀNH CÔNG!")
        print("=======================================================")
    except Exception as e:
        print(f"\n[!] LỖI AUDIT: {e}")
        sys.exit(1)
