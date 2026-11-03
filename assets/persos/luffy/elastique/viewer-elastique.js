window.ElastiqueViewer = function (canvas) {
  const T = THREE, D = Math.PI / 180;
  const renderer = new T.WebGLRenderer({canvas, antialias: true});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFSoftShadowMap;
  const scene = new T.Scene();
  scene.background = new T.Color('#151312');
  scene.fog = new T.Fog('#151312', 26, 60);
  const camera = new T.PerspectiveCamera(34, 1, 0.1, 200);
  camera.position.set(-19, 7.5, -10);
  const controls = new T.OrbitControls(camera, canvas);
  controls.target.set(0, 2.8, -3.5);
  controls.enableDamping = true;
  controls.maxPolarAngle = Math.PI * 0.49;
  controls.minDistance = 6; controls.maxDistance = 40;

  scene.add(new T.HemisphereLight('#efe6dc', '#231f1c', 0.75));
  const sun = new T.DirectionalLight('#fff3e2', 0.9);
  sun.position.set(-6, 14, -6); sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, {left: -14, right: 14, top: 14, bottom: -6});
  scene.add(sun);
  const rim = new T.DirectionalLight('#ffb08a', 0.5); rim.position.set(6, 5, 8); scene.add(rim);
  const aura = new T.PointLight('#ff5a45', 0, 14); scene.add(aura);

  const ground = new T.Mesh(new T.PlaneGeometry(140, 140), new T.MeshStandardMaterial({color: '#1f1c1a', roughness: 1}));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const grid = new T.GridHelper(48, 24, '#332e2a', '#272320'); grid.position.y = 0.01; scene.add(grid);

  const mat = c => new T.MeshStandardMaterial({color: c, roughness: 0.75});
  const SKIN = mat('#d9a47a'), VEST = mat('#c8372d'), SHORTS = mat('#3b5a9a'), SASH = mat('#e2bd55'), DARK = mat('#141414'), SANDAL = mat('#5a3a24'), STRAW = mat('#e6c46a'), BAND = mat('#b32a22');
  const skinBase = new T.Color('#d9a47a'), skinG2 = new T.Color('#f2858a');
  const box = (s, m, o) => { const b = new T.Mesh(new T.BoxGeometry(s[0], s[1], s[2]), m); if (o) b.position.set(o[0], o[1], o[2]); b.castShadow = true; return b; };

  const hrp = new T.Group(); hrp.position.y = 2.8; scene.add(hrp);
  const J = {};
  const joint = (name, parent, c0, mesh) => { const g = new T.Group(); g.position.set(c0[0], c0[1], c0[2]); g.userData.c0 = new T.Vector3(c0[0], c0[1], c0[2]); if (mesh) g.add(mesh); parent.add(g); J[name] = g; return g; };
  joint('root', hrp, [0, 0, 0], box([2, 0.4, 1], SHORTS));
  J.root.add(box([2.04, 0.2, 1.04], SASH, [0, 0.08, 0]));
  joint('waist', J.root, [0, 0.2, 0], box([2, 1.6, 1], SKIN, [0, 0.8, 0]));
  J.waist.add(box([0.62, 1.62, 1.04], VEST, [-0.7, 0.8, 0]), box([0.62, 1.62, 1.04], VEST, [0.7, 0.8, 0]), box([2.04, 1.62, 0.5], VEST, [0, 0.8, 0.28]));
  joint('neck', J.waist, [0, 1.6, 0], box([1.15, 1.15, 1.15], SKIN, [0, 0.6, 0]));
  J.neck.add(box([0.16, 0.14, 0.04], DARK, [-0.22, 0.68, -0.59]), box([0.16, 0.14, 0.04], DARK, [0.22, 0.68, -0.59]), box([1.22, 0.32, 1.22], DARK, [0, 1.08, 0.02]), box([1.22, 0.5, 0.3], DARK, [0, 0.82, 0.48]));
  [['r', 1], ['l', -1]].forEach(([s, x]) => {
    joint(s + 's', J.waist, [1.5 * x, 1.35, 0], box([1, 1.2, 1], SKIN, [0, -0.35, 0]));
    J[s + 's'].add(box([1.04, 0.5, 1.04], VEST, [0, 0.0, 0]));
    joint(s + 'e', J[s + 's'], [0, -0.85, 0], box([0.96, 0.95, 0.96], SKIN, [0, -0.45, 0]));
    joint(s + 'w', J[s + 'e'], [0, -0.9, 0], box([0.98, 0.42, 0.98], SKIN, [0, -0.2, 0]));
    joint(s + 'hip', J.root, [0.5 * x, -0.2, 0], box([1, 1.2, 1], SHORTS, [0, -0.6, 0]));
    joint(s + 'k', J[s + 'hip'], [0, -1.2, 0], box([0.92, 1.1, 0.92], SKIN, [0, -0.55, 0]));
    joint(s + 'a', J[s + 'k'], [0, -1.1, 0], box([1, 0.22, 1.15], SANDAL, [0, -0.19, -0.05]));
  });

  function hat() {
    const g = new T.Group();
    const cyl = (rt, rb, h, m, y) => { const c = new T.Mesh(new T.CylinderGeometry(rt, rb, h, 28), m); c.position.y = y; c.castShadow = true; g.add(c); };
    cyl(1.25, 1.25, 0.08, STRAW, 0); cyl(0.6, 0.66, 0.55, STRAW, 0.3); cyl(0.67, 0.67, 0.16, BAND, 0.12);
    return g;
  }
  const ACC = {};
  ACC.ChapeauTete = hat(); ACC.ChapeauTete.position.set(0, 1.22, 0.04); ACC.ChapeauTete.rotation.x = 0.06; J.neck.add(ACC.ChapeauTete);
  ACC.ChapeauDos = hat(); ACC.ChapeauDos.position.set(0, 1.0, 0.58); ACC.ChapeauDos.rotation.x = Math.PI / 2 - 0.15; J.waist.add(ACC.ChapeauDos);

  const LIMB = ['rs','re','rw','ls','le','lw','rhip','rk','lhip','lk'].map(k => J[k].children[0]);
  let inflate = 0, pulse = 0;
  const TUBES = {re: SKIN, rw: SKIN, le: SKIN, lw: SKIN, rk: SKIN, ra: SKIN, lk: SKIN, la: SKIN};
  const tubes = Object.keys(TUBES).map(k => {
    const m = new T.Mesh(new T.CylinderGeometry(0.38, 0.38, 1, 14), TUBES[k]);
    m.castShadow = true; m.visible = false; scene.add(m);
    return {k, m};
  });
  let tubesOn = true;
  const ta = new T.Vector3(), tb = new T.Vector3(), up = new T.Vector3(0, 1, 0), dir = new T.Vector3();
  function updateTubes() {
    tubes.forEach(({k, m}) => {
      const g = J[k];
      ta.copy(g.userData.c0); g.parent.localToWorld(ta);
      g.getWorldPosition(tb);
      const d = ta.distanceTo(tb);
      m.visible = tubesOn && d > 0.12;
      if (!m.visible) return;
      m.position.copy(ta).add(tb).multiplyScalar(0.5);
      m.scale.set(m.userData.inf || 1, d, m.userData.inf || 1);
      m.quaternion.setFromUnitVectors(up, dir.copy(tb).sub(ta).normalize());
    });
  }

  const TRAIL_N = 16, trails = [];
  [['rw', [0.5, -0.2, 0], [-0.5, -0.2, 0]], ['lw', [0.5, -0.2, 0], [-0.5, -0.2, 0]], ['ra', [0, -0.15, 0.55], [0, 0.6, 0]]].forEach(([name, a, b]) => {
    const geo = new T.BufferGeometry();
    const pos = new Float32Array(TRAIL_N * 2 * 3), col = new Float32Array(TRAIL_N * 2 * 3), idx = [];
    for (let i = 0; i < TRAIL_N - 1; i++) { const q = i * 2; idx.push(q, q + 1, q + 2, q + 1, q + 3, q + 2); }
    geo.setAttribute('position', new T.BufferAttribute(pos, 3));
    geo.setAttribute('color', new T.BufferAttribute(col, 3));
    geo.setIndex(idx);
    const mesh = new T.Mesh(geo, new T.MeshBasicMaterial({vertexColors: true, transparent: true, blending: T.AdditiveBlending, depthWrite: false, side: T.DoubleSide}));
    mesh.frustumCulled = false; scene.add(mesh);
    trails.push({name, mesh, hist: [], a: new T.Vector3(...a), b: new T.Vector3(...b)});
  });

  const rings = [];
  function ring(strength) {
    const m = new T.Mesh(new T.RingGeometry(0.6, 1, 48), new T.MeshBasicMaterial({color: '#ff8a5c', transparent: true, opacity: 0.9, blending: T.AdditiveBlending, side: T.DoubleSide, depthWrite: false}));
    m.rotation.x = -Math.PI / 2;
    const p = new T.Vector3(); J.root.getWorldPosition(p);
    m.position.set(p.x, 0.03, p.z); m.userData = {age: 0, s: strength || 1};
    scene.add(m); rings.push(m);
  }

  const STEAM_N = 46, steam = [];
  const steamGeo = new T.BoxGeometry(0.45, 0.45, 0.45);
  for (let i = 0; i < STEAM_N; i++) {
    const m = new T.Mesh(steamGeo, new T.MeshBasicMaterial({color: '#ffffff', transparent: true, opacity: 0, depthWrite: false}));
    m.visible = false; scene.add(m); steam.push({m, age: 1, life: 1, v: new T.Vector3()});
  }
  let steamAcc = 0, steamOn = true, shakeAmt = 0;
  const SPARK_N = 60, sparks = [], sparkGeo = new T.BoxGeometry(0.18, 0.18, 0.9);
  for (let i = 0; i < SPARK_N; i++) {
    const m = new T.Mesh(sparkGeo, new T.MeshBasicMaterial({color: '#fff1b8', transparent: true, opacity: 0, blending: T.AdditiveBlending, depthWrite: false}));
    m.visible = false; scene.add(m); sparks.push({m, age: 1, life: 1, v: new T.Vector3()});
  }
  const flash = new T.Mesh(new T.SphereGeometry(1, 16, 12), new T.MeshBasicMaterial({color: '#fff6d8', transparent: true, opacity: 0, blending: T.AdditiveBlending, depthWrite: false}));
  flash.userData.age = 1; scene.add(flash);
  const sp = new T.Vector3(), rootW = new T.Vector3();
  function spark(strength) {
    J.root.getWorldPosition(rootW);
    let best = null, bd = -1;
    ['rw', 'lw', 'ra', 'la'].forEach(k => { J[k].getWorldPosition(tb); const d = tb.distanceTo(rootW); if (d > bd) { bd = d; best = tb.clone(); } });
    sp.copy(best);
    flash.position.copy(sp); flash.userData.age = 0; flash.userData.s = strength;
    let n = Math.round(10 * strength);
    for (const p of sparks) {
      if (n <= 0) break; if (p.age < p.life) continue; n--;
      p.age = 0; p.life = 0.14 + Math.random() * 0.12;
      p.m.position.copy(sp);
      p.v.set(Math.random() - 0.5, Math.random() - 0.3, Math.random() - 0.5).normalize().multiplyScalar(14 + Math.random() * 10);
      p.m.lookAt(tb.copy(sp).add(p.v));
    }
  }
  const BURST_N = 90, bursts = [], burstGeo = new T.BoxGeometry(0.8, 0.8, 0.8);
  for (let i = 0; i < BURST_N; i++) {
    const m = new T.Mesh(burstGeo, new T.MeshBasicMaterial({color: '#ffffff', transparent: true, opacity: 0, depthWrite: false}));
    m.visible = false; scene.add(m); bursts.push({m, age: 1, life: 1, v: new T.Vector3()});
  }
  function burst() {
    J.root.getWorldPosition(rp);
    bursts.forEach((p, i) => {
      const ang = i / BURST_N * Math.PI * 2 + Math.random() * 0.2, el = Math.random() * 1.1 - 0.15, sp = 9 + Math.random() * 9;
      p.age = 0; p.life = 0.55 + Math.random() * 0.5;
      p.m.position.set(rp.x, rp.y + 0.6, rp.z);
      p.v.set(Math.cos(ang) * Math.cos(el) * sp, Math.sin(el) * sp * 0.8 + 1.5, Math.sin(ang) * Math.cos(el) * sp);
      p.m.rotation.set(Math.random() * 3, Math.random() * 3, 0);
    });
  }
  const FIRE_N = 70, fire = [], fireGeo = new T.BoxGeometry(0.32, 0.32, 0.32);
  for (let i = 0; i < FIRE_N; i++) {
    const m = new T.Mesh(fireGeo, new T.MeshBasicMaterial({color: '#ffb340', transparent: true, opacity: 0, blending: T.AdditiveBlending, depthWrite: false}));
    m.visible = false; scene.add(m); fire.push({m, age: 1, life: 1, v: new T.Vector3()});
  }
  const fireLight = new T.PointLight('#ff8a2a', 0, 7); scene.add(fireLight);
  let fireOn = false, fireAcc = 0; const fp = new T.Vector3(), fcA = new T.Color('#ffe066'), fcB = new T.Color('#ff3a12');

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
  function setVisible(v) { for (const k in ACC) ACC[k].visible = !!v[k]; }

  let trailOn = true, auraTarget = 0, last = performance.now();
  const tmp = new T.Vector3(), tmp2 = new T.Vector3(), rp = new T.Vector3();
  function render(playing) {
    const now = performance.now(), dt = Math.min(0.05, (now - last) / 1000); last = now;
    scene.updateMatrixWorld(true);
    pulse = Math.max(0, pulse - dt * 5);
    const inf = 1 + inflate * 0.14 + pulse * 0.1;
    LIMB.forEach(m => m.scale.set(inf, 1, inf));
    tubes.forEach(({m}) => { m.userData.inf = inf; });
    updateTubes();
    trails.forEach(tr => {
      const g = J[tr.name];
      if (playing || !tr.hist.length) {
        tmp.copy(tr.a); g.localToWorld(tmp);
        tmp2.copy(tr.b); g.localToWorld(tmp2);
        tr.hist.unshift([tmp.clone(), tmp2.clone(), trailOn]);
        if (tr.hist.length > TRAIL_N) tr.hist.pop();
      }
      const pos = tr.mesh.geometry.attributes.position, col = tr.mesh.geometry.attributes.color;
      for (let i = 0; i < TRAIL_N; i++) {
        const h = tr.hist[Math.min(i, tr.hist.length - 1)];
        const f = h[2] && playing ? Math.pow(1 - i / TRAIL_N, 1.6) * 0.8 : 0;
        pos.setXYZ(i * 2, h[0].x, h[0].y, h[0].z); pos.setXYZ(i * 2 + 1, h[1].x, h[1].y, h[1].z);
        col.setXYZ(i * 2, 1 * f, 0.55 * f, 0.3 * f); col.setXYZ(i * 2 + 1, 0.5 * f, 0.15 * f, 0.08 * f);
      }
      pos.needsUpdate = true; col.needsUpdate = true;
    });
    for (let i = rings.length - 1; i >= 0; i--) {
      const r = rings[i]; r.userData.age += dt;
      const k = r.userData.age / 0.6;
      r.scale.setScalar(1 + k * 6 * r.userData.s); r.material.opacity = Math.max(0, 0.9 * (1 - k));
      if (k >= 1) { scene.remove(r); r.geometry.dispose(); r.material.dispose(); rings.splice(i, 1); }
    }
    J.root.getWorldPosition(rp);
    aura.intensity += (auraTarget - aura.intensity) * Math.min(1, dt * 6);
    aura.position.set(rp.x, rp.y + 0.8, rp.z);
    const ai = aura.intensity / 3;
    SKIN.color.copy(skinBase).lerp(skinG2, Math.min(1, ai * 1.2 + inflate * 0.2));
    SKIN.emissive.setRGB(ai * 0.14, ai * 0.02, ai * 0.03);
    if (playing && auraTarget > 0 && steamOn) {
      steamAcc += dt * 40;
      while (steamAcc > 1) {
        steamAcc--;
        const p = steam.find(s => s.age >= s.life); if (!p) break;
        p.age = 0; p.life = 0.7 + Math.random() * 0.6;
        p.m.position.set(rp.x + (Math.random() - 0.5) * 2.2, rp.y + Math.random() * 2.2 - 0.3, rp.z + (Math.random() - 0.5) * 1.4);
        p.v.set((Math.random() - 0.5) * 0.6, 2 + Math.random() * 1.5, (Math.random() - 0.5) * 0.6);
        p.m.rotation.set(Math.random() * 3, Math.random() * 3, 0);
      }
    }
    J.rw.localToWorld(fp.set(0, -0.2, 0));
    fireLight.position.copy(fp);
    fireLight.intensity += ((fireOn ? 2.2 : 0) - fireLight.intensity) * Math.min(1, dt * 12);
    if (playing && fireOn) {
      fireAcc += dt * 140;
      while (fireAcc > 1) {
        fireAcc--;
        const p = fire.find(s => s.age >= s.life); if (!p) break;
        p.age = 0; p.life = 0.22 + Math.random() * 0.2;
        p.m.position.set(fp.x + (Math.random() - 0.5) * 0.8, fp.y + (Math.random() - 0.5) * 0.8, fp.z + (Math.random() - 0.5) * 0.8);
        p.v.set((Math.random() - 0.5) * 1.2, 2.5 + Math.random() * 2, (Math.random() - 0.5) * 1.2);
        p.m.rotation.set(Math.random() * 3, Math.random() * 3, 0);
      }
    }
    fire.forEach(s => {
      if (s.age >= s.life) { s.m.visible = false; return; }
      if (playing) { s.age += dt; s.m.position.addScaledVector(s.v, dt); s.m.rotation.x += dt * 4; }
      const k = s.age / s.life;
      s.m.visible = true; s.m.scale.setScalar(1.3 - k * 0.9); s.m.material.opacity = 0.9 * (1 - k);
      s.m.material.color.copy(fcA).lerp(fcB, k);
    });
    sparks.forEach(s => {
      if (s.age >= s.life) { s.m.visible = false; return; }
      s.age += dt; s.m.position.addScaledVector(s.v, dt);
      const k = s.age / s.life; s.m.visible = true; s.m.material.opacity = 1 - k; s.m.scale.set(1, 1, 1.4 - k);
    });
    if (flash.userData.age < 0.14) {
      flash.userData.age += dt; const k = flash.userData.age / 0.14;
      flash.visible = true; flash.scale.setScalar((0.5 + k * 1.4) * (flash.userData.s || 1)); flash.material.opacity = 0.9 * (1 - k);
    } else flash.visible = false;
    bursts.forEach(s => {
      if (s.age >= s.life) { s.m.visible = false; return; }
      s.age += dt; s.v.multiplyScalar(Math.max(0, 1 - dt * 4)); s.m.position.addScaledVector(s.v, dt);
      const k = s.age / s.life;
      s.m.visible = true; s.m.scale.setScalar(0.8 + k * 3.2); s.m.material.opacity = 0.85 * (1 - k);
    });
    steam.forEach(s => {
      if (s.age >= s.life) { s.m.visible = false; return; }
      if (playing) { s.age += dt; s.m.position.addScaledVector(s.v, dt); s.m.rotation.y += dt; }
      const k = s.age / s.life;
      s.m.visible = true; s.m.scale.setScalar(0.6 + k * 1.6); s.m.material.opacity = 0.5 * (1 - k);
    });
    controls.target.lerp(tmp.set(0, 2.6 + Math.max(0, rp.y - 2.8) * 0.8, -3.5), 0.12);
    controls.update();
    shakeAmt = Math.max(0, shakeAmt - dt * 3.2);
    const sx = (Math.random() - 0.5) * shakeAmt, sy = (Math.random() - 0.5) * shakeAmt, sz = (Math.random() - 0.5) * shakeAmt;
    camera.position.x += sx; camera.position.y += sy; camera.position.z += sz;
    renderer.render(scene, camera);
    camera.position.x -= sx; camera.position.y -= sy; camera.position.z -= sz;
  }
  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight; if (!w || !h) return;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  const ro = new ResizeObserver(resize); ro.observe(canvas); resize();
  return {
    setPose, setVisible, render, ring,
    setTrail: on => { trailOn = on; },
    setTubes: on => { tubesOn = on; },
    setAura: v => { auraTarget = v; },
    setFire: on => { fireOn = on; },
    setSteam: on => { steamOn = on; },
    setInflate: x => { inflate = x; },
    pulse: () => { pulse = 1; },
    burst, spark,
    shake: x => { shakeAmt = Math.max(shakeAmt, x); },
    clearTrails: () => trails.forEach(t => t.hist.length = 0),
    dispose: () => { ro.disconnect(); renderer.dispose(); }
  };
};
