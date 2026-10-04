with open('dobot_visualizer.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add ColladaLoader script in <head>
target_head = '<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>'
loader_script = '<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>\n    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/ColladaLoader.js"></script>'
if loader_script not in html:
    html = html.replace(target_head, loader_script)
    print("1. Added ColladaLoader.js script tag")

# 2. Add CAD Toggle Button in Header
target_btn = '<button class="btn-config-gear" onclick="configureServerUrl()"'
new_btn = '<button id="btn-cad-toggle" class="btn-config-gear" onclick="toggleCadFidelity()" style="display: flex; align-items: center; gap: 4px; background: rgba(16, 185, 129, 0.25); border-color: #10b981; color: #6ee7b7; font-weight: 700;" title="Bật/Tắt mô hình 3D CAD Mesh chính hãng Dobot">🎨 CAD Mesh</button>\n                    <button class="btn-config-gear" onclick="configureServerUrl()"'
if 'id="btn-cad-toggle"' not in html:
    html = html.replace(target_btn, new_btn)
    print("2. Added CAD toggle button to header")

# 3. Add CAD Integration Logic right after gripper pad (around line 2398)
cad_code = """
        // ========================================================
        // OFFICIAL DOBOT CAD MESH INTEGRATION (.DAE)
        // ========================================================
        const baseCad = new THREE.Group();
        const j1Cad = new THREE.Group();
        const j2Cad = new THREE.Group();
        const j3Cad = new THREE.Group();
        const wristCad = new THREE.Group();
        const toolCad = new THREE.Group();

        baseGroup.add(baseCad);
        j1Group.add(j1Cad);
        j2Group.add(j2Cad);
        j3Group.add(j3Cad);
        wristGroup.add(wristCad);
        toolGroup.add(toolCad);

        // Collect procedural meshes
        const proceduralMeshes = [];
        [baseGroup, j1Group, j2Group, j3Group, wristGroup, toolGroup].forEach(parent => {
            parent.children.forEach(child => {
                if (child !== j1Group && child !== j2Group && child !== j3Group && child !== wristGroup && child !== toolGroup &&
                    child !== baseCad && child !== j1Cad && child !== j2Cad && child !== j3Cad && child !== wristCad && child !== toolCad) {
                    proceduralMeshes.push(child);
                }
            });
        });

        let cadPartsLoadedCount = 0;
        let isCadModeActive = false;

        function setCadMode(enable) {
            isCadModeActive = enable;
            proceduralMeshes.forEach(mesh => {
                mesh.visible = !enable;
            });
            baseCad.visible = enable;
            j1Cad.visible = enable;
            j2Cad.visible = enable;
            j3Cad.visible = enable;
            wristCad.visible = enable;
            toolCad.visible = enable;

            const btn = document.getElementById('btn-cad-toggle');
            if (btn) {
                btn.innerText = enable ? '🎨 CAD Mesh (BẬT)' : '📐 Khung (Thủ công)';
                btn.style.background = enable ? 'rgba(16, 185, 129, 0.3)' : 'transparent';
                btn.style.borderColor = enable ? '#10b981' : '#4a5568';
            }
        }

        function toggleCadFidelity() {
            setCadMode(!isCadModeActive);
        }

        function loadOfficialCadMeshes() {
            if (typeof THREE.ColladaLoader === 'undefined') return;
            const loader = new THREE.ColladaLoader();
            const basePath = window.location.protocol === 'file:' ? 'dobot_description/meshes/dae/' : '/dobot_description/meshes/dae/';

            function polishScene(sceneObj) {
                sceneObj.traverse(child => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                        if (child.material) {
                            if (Array.isArray(child.material)) {
                                child.material.forEach(m => { m.side = THREE.DoubleSide; });
                            } else {
                                child.material.side = THREE.DoubleSide;
                            }
                        }
                    }
                });
                return sceneObj;
            }

            // 1. Base Mesh
            loader.load(basePath + 'magicianBase.dae', function(c) {
                const obj = polishScene(c.scene);
                obj.position.set(0, 48.6, 0);
                baseCad.add(obj);
                onCadMeshLoaded();
            }, undefined, function(e) { console.warn('CAD Base error:', e); });

            // 2. Link 1 Tower
            loader.load(basePath + 'magicianLink1.dae', function(c) {
                const obj = polishScene(c.scene);
                obj.position.set(0, 90, 0);
                j1Cad.add(obj);
                onCadMeshLoaded();
            }, undefined, function(e) { console.warn('CAD Link1 error:', e); });

            // 3. Link 2 Rear Arm
            loader.load(basePath + 'magicianLink2.dae', function(c) {
                const obj = polishScene(c.scene);
                const w = new THREE.Group();
                w.rotation.z = 0.349066; // +20 deg compensation
                w.add(obj);
                j2Cad.add(w);
                onCadMeshLoaded();
            }, undefined, function(e) { console.warn('CAD Link2 error:', e); });

            // 4. Link 3 Forearm
            loader.load(basePath + 'magicianLink3.dae', function(c) {
                const obj = polishScene(c.scene);
                const w = new THREE.Group();
                w.position.set(16.452, -133.994, 0);
                w.rotation.z = 0.471239; // +27 deg compensation
                w.add(obj);
                j3Cad.add(w);
                onCadMeshLoaded();
            }, undefined, function(e) { console.warn('CAD Link3 error:', e); });

            // 5. Link 4 Wrist Bracket
            loader.load(basePath + 'magicianLink4_default.dae', function(c) {
                const obj = polishScene(c.scene);
                const w = new THREE.Group();
                w.position.set(-177.151, -58.595, 0);
                w.add(obj);
                wristCad.add(w);
                onCadMeshLoaded();
            }, undefined, function(e) { console.warn('CAD Link4 error:', e); });

            // 6. Suction Cup End-Effector
            loader.load(basePath + 'suction_cup.dae', function(c) {
                const obj = polishScene(c.scene);
                const w = new THREE.Group();
                w.position.set(-0.081, -11.843, 0);
                w.add(obj);
                toolCad.add(w);
                onCadMeshLoaded();
            }, undefined, function(e) { console.warn('CAD Suction error:', e); });
        }

        function onCadMeshLoaded() {
            cadPartsLoadedCount++;
            const btn = document.getElementById('btn-cad-toggle');
            if (btn && cadPartsLoadedCount < 6) {
                btn.innerText = '⏳ CAD (' + cadPartsLoadedCount + '/6)';
            }
            if (cadPartsLoadedCount >= 6) {
                setCadMode(true);
                console.log('✅ 100% Dobot CAD Meshes loaded and active!');
            }
        }

        loadOfficialCadMeshes();
"""

target_insert = '// HỆ TRỤC RGB VÀ ĐƯỜNG GIÓNG TẠI MŨI HÚT'
if 'loadOfficialCadMeshes()' not in html:
    html = html.replace(target_insert, cad_code + '\n\n        ' + target_insert)
    print("3. Injected CAD integration code")

with open('dobot_visualizer.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('dist_netlify/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved dobot_visualizer.html and dist_netlify/index.html")
