with open('dobot_visualizer.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update polishScene to include scale.set(1000, 1000, 1000)
old_polish = """            function polishScene(sceneObj) {
                sceneObj.traverse(child => {"""

new_polish = """            function polishScene(sceneObj) {
                sceneObj.scale.set(1000, 1000, 1000); // Essential: Scale Collada meters to Three.js millimeters
                sceneObj.traverse(child => {"""

text = text.replace(old_polish, new_polish)

# 2. Update magicianBase position from 48.6 to 154.6
old_base_pos = "obj.position.set(0, 48.6, 0);"
new_base_pos = "obj.position.set(0, 154.6, 0);"
text = text.replace(old_base_pos, new_base_pos)

# 3. Ensure CAD groups start hidden until all 6 parts are loaded
old_setup = """        baseGroup.add(baseCad);
        j1Group.add(j1Cad);
        j2Group.add(j2Cad);
        j3Group.add(j3Cad);
        wristGroup.add(wristCad);
        toolGroup.add(toolCad);"""

new_setup = """        baseGroup.add(baseCad);
        j1Group.add(j1Cad);
        j2Group.add(j2Cad);
        j3Group.add(j3Cad);
        wristGroup.add(wristCad);
        toolGroup.add(toolCad);

        // Keep CAD groups hidden while loading so procedural model remains visible
        baseCad.visible = false;
        j1Cad.visible = false;
        j2Cad.visible = false;
        j3Cad.visible = false;
        wristCad.visible = false;
        toolCad.visible = false;"""

text = text.replace(old_setup, new_setup)

with open('dobot_visualizer.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('dist_netlify/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied CAD scale and position fixes to dobot_visualizer.html!")
