with open('view_urdf.html', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace loadAllCadMeshes and buildProceduralFallback with progressive enhancement
old_load = """        function loadAllCadMeshes() {
            const loader = new THREE.ColladaLoader();
            const meshesToLoad = [
                { id: 'base', file: 'magicianBase.dae', group: baseGroup, pos: [0, 0, 48.6], rot: [0, 0, 0] },
                { id: 'link1', file: 'magicianLink1.dae', group: j1Group, pos: [0, 0, 0], rot: [0, 0, 0] },
                { id: 'link2', file: 'magicianLink2.dae', group: j2Group, pos: [0, 0, 0], rot: [0, -0.349066, 0] },
                { id: 'link3', file: 'magicianLink3.dae', group: j3Group, pos: [16.452, 0, -133.994], rot: [0, -0.471239, 0] },
                { id: 'link4', file: 'magicianLink4_default.dae', group: j4WristGroup, pos: [-177.151, 0, -58.595], rot: [0, 0, 0] },
                { id: 'suction', file: 'suction_cup.dae', group: toolGroup, pos: [-0.081, 0, -11.843], rot: [0, 0, 0] },
                { id: 'gripper', file: 'magicianGripper.dae', group: null, pos: [0, 0, 0], rot: [0, 0, 0] }
            ];

            meshesToLoad.forEach(item => {
                loader.load(
                    getMeshUrl(item.file),
                    function(collada) {
                        const cadObj = polishCadScene(collada.scene);
                        cadObj.position.set(item.pos[0], item.pos[1], item.pos[2]);
                        cadObj.rotation.set(item.rot[0], item.rot[1], item.rot[2]);
                        cadNodes[item.id] = cadObj;

                        if (item.group) {
                            item.group.add(cadObj);
                        }

                        cadLoadedCount++;
                        updateCadLoadingStatus();
                    },
                    undefined,
                    function(error) {
                        console.warn('CAD Mesh fallback for:', item.file, error);
                    }
                );
            });
        }"""

new_load = """        function loadAllCadMeshes() {
            const loader = new THREE.ColladaLoader();
            const meshesToLoad = [
                { id: 'base', file: 'magicianBase.dae', group: baseGroup, pos: [0, 0, 48.6], rot: [0, 0, 0] },
                { id: 'link1', file: 'magicianLink1.dae', group: j1Group, pos: [0, 0, 0], rot: [0, 0, 0] },
                { id: 'link2', file: 'magicianLink2.dae', group: j2Group, pos: [0, 0, 0], rot: [0, -0.349066, 0] },
                { id: 'link3', file: 'magicianLink3.dae', group: j3Group, pos: [16.452, 0, -133.994], rot: [0, -0.471239, 0] },
                { id: 'link4', file: 'magicianLink4_default.dae', group: j4WristGroup, pos: [-177.151, 0, -58.595], rot: [0, 0, 0] },
                { id: 'suction', file: 'suction_cup.dae', group: toolGroup, pos: [-0.081, 0, -11.843], rot: [0, 0, 0] },
                { id: 'gripper', file: 'magicianGripper.dae', group: null, pos: [0, 0, 0], rot: [0, 0, 0] }
            ];

            meshesToLoad.forEach(item => {
                loader.load(
                    getMeshUrl(item.file),
                    function(collada) {
                        const cadObj = polishCadScene(collada.scene);
                        cadObj.position.set(item.pos[0], item.pos[1], item.pos[2]);
                        cadObj.rotation.set(item.rot[0], item.rot[1], item.rot[2]);
                        cadNodes[item.id] = cadObj;

                        if (item.group) {
                            item.group.add(cadObj);
                        }

                        // Immediately hide corresponding procedural parts as each CAD part arrives
                        if (geomRobotGroup && geomRobotGroup.proceduralMap && geomRobotGroup.proceduralMap[item.id]) {
                            geomRobotGroup.proceduralMap[item.id].forEach(m => { m.visible = false; });
                        }

                        cadLoadedCount++;
                        updateCadLoadingStatus();
                    },
                    undefined,
                    function(error) {
                        console.warn('CAD Mesh fallback for:', item.file, error);
                    }
                );
            });
        }"""

# Update procedural map in buildProceduralFallback
old_fallback_end = """            geomRobotGroup.proceduralElements = [baseMesh, ringMesh, tower, rearArm, rod, foreArm, foreCover, wrist, servo, stem, cup];
        }"""

new_fallback_end = """            geomRobotGroup.proceduralElements = [baseMesh, ringMesh, tower, rearArm, rod, foreArm, foreCover, wrist, servo, stem, cup];
            geomRobotGroup.proceduralMap = {
                base: [baseMesh, ringMesh],
                link1: [tower],
                link2: [rearArm, rod],
                link3: [foreArm, foreCover],
                link4: [wrist],
                suction: [servo, stem, cup]
            };
        }"""

if old_load in code:
    code = code.replace(old_load, new_load)
    print("Replaced loadAllCadMeshes")

if old_fallback_end in code:
    code = code.replace(old_fallback_end, new_fallback_end)
    print("Replaced procedural map")

with open('view_urdf.html', 'w', encoding='utf-8') as f:
    f.write(code)

with open('dobot_description/view_urdf.html', 'w', encoding='utf-8') as f:
    f.write(code)

with open('dist_netlify/view_urdf.html', 'w', encoding='utf-8') as f:
    f.write(code)

print("Synchronized view_urdf.html across all 3 directories!")
