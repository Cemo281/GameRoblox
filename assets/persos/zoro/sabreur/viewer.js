window.SabreViewer = function (canvas) {
  const T = THREE, D = Math.PI / 180;
  const renderer = new T.WebGLRenderer({canvas, antialias: true});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFSoftShadowMap;
  const scene = new T.Scene();
  scene.background = new T.Color('#141615');
  scene.fog = new T.Fog('#141615', 22, 55);
  const camera = new T.PerspectiveCamera(34, 1, 0.1, 200);
  camera.position.set(-11.5, 6.4, -14.5);
  const controls = new T.OrbitControls(camera, canvas);
  controls.target.set(0, 2.6, 0);
  controls.enableDamping = true;
  controls.maxPolarAngle = Math.PI * 0.49;
  controls.minDistance = 5; controls.maxDistance = 30;

  scene.add(new T.HemisphereLight('#dfe7e2', '#202420', 0.75));
  const sun = new T.DirectionalLight('#fff6ea', 0.9);
  sun.position.set(-6, 12, -5); sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, {left: -8, right: 8, top: 10, bottom: -4});
  scene.add(sun);
  const rim = new T.DirectionalLight('#7dffb0', 0.55); rim.position.set(6, 5, 8); scene.add(rim);
  const aura = new T.PointLight('#5dff9a', 0, 12); aura.position.set(0, 3, 0); scene.add(aura);

  const ground = new T.Mesh(new T.PlaneGeometry(120, 120), new T.MeshStandardMaterial({color: '#1c1f1d', roughness: 1}));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const grid = new T.GridHelper(40, 20, '#2c312e', '#232725'); grid.position.y = 0.01; scene.add(grid);

  const mat = c => new T.MeshStandardMaterial({color: c, roughness: 0.75});
  const SKIN = mat('#c9b79c'), CLOTH = mat('#2a2d2b'), SASH = mat('#3f8f62'), DARK = mat('#111');
  const box = (s, m, o) => { const b = new T.Mesh(new T.BoxGeometry(s[0], s[1], s[2]), m); if (o) b.position.set(o[0], o[1], o[2]); b.castShadow = true; return b; };

  const hrp = new T.Group(); hrp.position.y = 2.8; scene.add(hrp);
  const J = {};
  const joint = (name, parent, c0, mesh) => { const g = new T.Group(); g.position.set(c0[0], c0[1], c0[2]); g.userData.c0 = new T.Vector3(c0[0], c0[1], c0[2]); if (mesh) g.add(mesh); parent.add(g); J[name] = g; return g; };
  joint('root', hrp, [0, 0, 0], box([2, 0.4, 1], CLOTH));
  J.root.add(box([2.04, 0.18, 1.04], SASH, [0, 0.05, 0]));
  joint('waist', J.root, [0, 0.2, 0], box([2, 1.6, 1], SKIN, [0, 0.8, 0]));
  joint('neck', J.waist, [0, 1.6, 0], box([1.15, 1.15, 1.15], SKIN, [0, 0.6, 0]));
  J.neck.add(box([0.16, 0.12, 0.04], DARK, [-0.22, 0.7, -0.59]), box([0.16, 0.12, 0.04], DARK, [0.22, 0.7, -0.59]), box([1.2, 0.18, 1.2], SASH, [0, 1.02, 0]));
  [['r', 1], ['l', -1]].forEach(([s, x]) => {
    joint(s + 's', J.waist, [1.5 * x, 1.35, 0], box([1, 1.2, 1], SKIN, [0, -0.35, 0]));
    joint(s + 'e', J[s + 's'], [0, -0.85, 0], box([0.96, 0.95, 0.96], SKIN, [0, -0.45, 0]));
    joint(s + 'w', J[s + 'e'], [0, -0.9, 0], box([0.96, 0.3, 0.96], SKIN, [0, -0.15, 0]));
    joint(s + 'hip', J.root, [0.5 * x, -0.2, 0], box([1, 1.2, 1], CLOTH, [0, -0.6, 0]));
    joint(s + 'k', J[s + 'hip'], [0, -1.2, 0], box([0.96, 1.1, 0.96], CLOTH, [0, -0.55, 0]));
    joint(s + 'a', J[s + 'k'], [0, -1.1, 0], box([1, 0.3, 1.1], DARK, [0, -0.15, -0.05]));
  });

  const BLADE = new T.MeshStandardMaterial({color: '#f1f4f2', metalness: 0.6, roughness: 0.3, emissive: '#3a3f3c'});
  function sword(handle) {
    const g = new T.Group();
    g.add(box([0.2, 0.2, 0.95], mat(handle), [0, 0, 0.45]));
    g.add(box([0.5, 0.5, 0.07], mat('#b89b4a'), [0, 0, -0.05]));
    g.add(box([0.07, 0.2, 4.1], BLADE, [0, 0, -2.15]));
    g.userData.tip = new T.Vector3(0, 0, -4.2); g.userData.base = new T.Vector3(0, 0, -0.8);
    return g;
  }
  const SW = {};
  SW.SabreDroit = sword('#e9e6dc'); SW.SabreDroit.position.set(0, -0.3, 0); J.rw.add(SW.SabreDroit);
  SW.SabreGauche = sword('#1c1c1c'); SW.SabreGauche.position.set(0, -0.3, 0); J.lw.add(SW.SabreGauche);
  SW.SabreBouche = sword('#6b2233'); SW.SabreBouche.rotation.y = -Math.PI / 2; SW.SabreBouche.position.set(-0.2, 0.32, -0.66); J.neck.add(SW.SabreBouche);
  SW.SabresHanche = new T.Group();
  ['#e9e6dc', '#1c1c1c', '#6b2233'].forEach((c, i) => {
    const s = new T.Group();
    s.add(box([0.2, 0.2, 0.95], mat(c), [0, 0, -0.5]));
    s.add(box([0.24, 0.3, 4.1], mat('#1b1b1b'), [0, 0, 2.05]));
    s.position.set(-1.12, 0.05 - i * 0.12, -0.25 + i * 0.22);
    s.rotation.set(0.42 + i * 0.07, 0.12 - i * 0.05, 0);
    SW.SabresHanche.add(s);
  });
  J.root.add(SW.SabresHanche);

  const TRAIL_N = 16, trails = [];
  ['SabreDroit', 'SabreGauche', 'SabreBouche'].forEach(name => {
    const geo = new T.BufferGeometry();
    const pos = new Float32Array(TRAIL_N * 2 * 3), col = new Float32Array(TRAIL_N * 2 * 3), idx = [];
    for (let i = 0; i < TRAIL_N - 1; i++) { const a = i * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    geo.setAttribute('position', new T.BufferAttribute(pos, 3));
    geo.setAttribute('color', new T.BufferAttribute(col, 3));
    geo.setIndex(idx);
    const mesh = new T.Mesh(geo, new T.MeshBasicMaterial({vertexColors: true, transparent: true, blending: T.AdditiveBlending, depthWrite: false, side: T.DoubleSide}));
    mesh.frustumCulled = false; scene.add(mesh);
    trails.push({name, mesh, hist: []});
  });

  const rings = [];
  function ring(strength) {
    const m = new T.Mesh(new T.RingGeometry(0.6, 1, 48), new T.MeshBasicMaterial({color: '#6dffa6', transparent: true, opacity: 0.9, blending: T.AdditiveBlending, side: T.DoubleSide, depthWrite: false}));
    m.rotation.x = -Math.PI / 2;
    const p = new T.Vector3(); J.root.getWorldPosition(p);
    m.position.set(p.x, 0.03, p.z); m.userData = {age: 0, s: strength || 1};
    scene.add(m); rings.push(m);
  }

  const qa = new T.Quaternion(), qb = new T.Quaternion(), ea = new T.Euler(0, 0, 0, 'XYZ');
  function setPose(s) {
    for (const k in J) {
      const a = s.a[k], b = s.b[k], g = J[k];
      qa.setFromEuler(ea.set(a[3] * D, a[4] * D, a[5] * D, 'XYZ'));
      qb.setFromEuler(ea.set(b[3] * D, b[4] * D, b[5] * D, 'XYZ'));
      g.quaternion.copy(qa).slerp(qb, s.w);
      g.position.copy(g.userData.c0).add(new T.Vector3(a[0] + (b[0] - a[0]) * s.w, a[1] + (b[1] - a[1]) * s.w, a[2] + (b[2] - a[2]) * s.w));
    }
  }
  function setVisible(v) { for (const k in SW) SW[k].visible = !!v[k]; }

  let trailOn = true, auraTarget = 0, last = performance.now();
  const tmp = new T.Vector3(), tmp2 = new T.Vector3(), rp = new T.Vector3();
  function render(playing) {
    const now = performance.now(), dt = Math.min(0.05, (now - last) / 1000); last = now;
    scene.updateMatrixWorld(true);
    trails.forEach(tr => {
      const sw = SW[tr.name];
      if (playing || !tr.hist.length) {
        tmp.copy(sw.userData.tip); sw.localToWorld(tmp);
        tmp2.copy(sw.userData.base); sw.localToWorld(tmp2);
        tr.hist.unshift([tmp.clone(), tmp2.clone(), sw.visible && trailOn]);
        if (tr.hist.length > TRAIL_N) tr.hist.pop();
      }
      const pos = tr.mesh.geometry.attributes.position, col = tr.mesh.geometry.attributes.color;
      for (let i = 0; i < TRAIL_N; i++) {
        const h = tr.hist[Math.min(i, tr.hist.length - 1)];
        const f = h[2] && playing ? Math.pow(1 - i / TRAIL_N, 1.6) * 0.85 : 0;
        pos.setXYZ(i * 2, h[0].x, h[0].y, h[0].z); pos.setXYZ(i * 2 + 1, h[1].x, h[1].y, h[1].z);
        col.setXYZ(i * 2, 0.35 * f, 1 * f, 0.6 * f); col.setXYZ(i * 2 + 1, 0.05 * f, 0.25 * f, 0.12 * f);
      }
      pos.needsUpdate = true; col.needsUpdate = true;
    });
    for (let i = rings.length - 1; i >= 0; i--) {
      const r = rings[i]; r.userData.age += dt;
      const k = r.userData.age / 0.6;
      r.scale.setScalar(1 + k * 6 * r.userData.s); r.material.opacity = Math.max(0, 0.9 * (1 - k));
      if (k >= 1) { scene.remove(r); r.geometry.dispose(); r.material.dispose(); rings.splice(i, 1); }
    }
    aura.intensity += (auraTarget - aura.intensity) * Math.min(1, dt * 6);
    const ai = aura.intensity / 3;
    BLADE.emissive.setRGB(0.23 + ai * 0.05, 0.25 + ai * 0.75, 0.24 + ai * 0.25);
    J.root.getWorldPosition(rp); aura.position.set(rp.x, rp.y + 0.6, rp.z);
    controls.target.lerp(tmp.set(0, 2.4 + Math.max(0, rp.y - 2.8) * 0.85, 0), 0.15);
    controls.update();
    renderer.render(scene, camera);
  }
  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight; if (!w || !h) return;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  const ro = new ResizeObserver(resize); ro.observe(canvas); resize();
  return {
    setPose, setVisible, render, ring,
    setTrail: on => { trailOn = on; },
    setAura: v => { auraTarget = v; },
    clearTrails: () => trails.forEach(t => t.hist.length = 0),
    dispose: () => { ro.disconnect(); renderer.dispose(); }
  };
};
