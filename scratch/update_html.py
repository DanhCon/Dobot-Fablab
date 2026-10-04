with open('view_urdf.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the broken line
old_broken = "txt.innerText = ;"
new_fixed = "txt.innerText = 'Đang tải CAD Meshes (' + cadLoadedCount + '/' + totalCadRequired + ')...';"

if old_broken in text:
    text = text.replace(old_broken, new_fixed)
    print("Fixed broken line!")

# Also remove duplicate function if any
duplicate = """        function updateCadLoadingStatus() {
            const dot = document.getElementById('dot-cad-status');
            const txt = document.getElementById('text-cad-status');

            if (cadLoadedCount >= totalCadRequired) {
                dot.className = 'status-dot';
                txt.innerText = '✅ 100% CAD Mesh Dobot Chính Hãng (Độ chính xác cao)';
                if (visualMode === 'cad') {
                    toggleVisualModeMesh(true);
                }"""

if text.count("function updateCadLoadingStatus()") > 1:
    idx = text.find("function updateCadLoadingStatus()")
    second_idx = text.find("function updateCadLoadingStatus()", idx + 1)
    # let's see how much to slice
    pass

with open('view_urdf.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('dobot_description/view_urdf.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('dist_netlify/view_urdf.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Synchronized all files.")
