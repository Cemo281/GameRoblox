(function () {
  const J = ['root','waist','neck','rs','re','rw','ls','le','lw','rhip','rk','ra','lhip','lk','la'];
  const PART = {root:'LowerTorso',waist:'UpperTorso',neck:'Head',rs:'RightUpperArm',re:'RightLowerArm',rw:'RightHand',ls:'LeftUpperArm',le:'LeftLowerArm',lw:'LeftHand',rhip:'RightUpperLeg',rk:'RightLowerLeg',ra:'RightFoot',lhip:'LeftUpperLeg',lk:'LeftLowerLeg',la:'LeftFoot'};
  const ACCESSORIES = [
    {name:'ChapeauTete', att:'HatAttachment (Head)', desc:'chapeau de paille sur la tête'},
    {name:'ChapeauDos', att:'BodyBackAttachment (UpperTorso)', desc:'chapeau pendu dans le dos'}
  ];
  const norm = v => !v ? [0,0,0,0,0,0] : (v.length === 3 ? [0,0,0].concat(v) : v.slice());
  const P = (base, o) => { const r = {}; J.forEach(j => r[j] = norm((o && o[j]) || base[j])); return r; };
  const K = (t, pose, e, d) => ({t, pose, e: e || 'Cubic', d: d || 'Out'});
  const S = (rot, len) => [0, -len, 0].concat(rot);   // segment étiré le long du membre parent

  const GUARD = P({}, {root:[0,-0.35,0, 0,-15,0], waist:[-8,12,0], neck:[-4,4,0], rs:[70,0,22], re:[105,0,0], ls:[80,0,-18], le:[115,0,0], rhip:[28,0,10], rk:[-45,0,0], ra:[17,0,0], lhip:[-8,0,-10], lk:[-28,0,0], la:[12,0,0]});
  const HOPUP = P(GUARD, {root:[0,0.2,0, 0,-15,0], rhip:[18,0,10], rk:[-22,0,0], ra:[8,0,0], lk:[-15,0,0], rs:[76,0,22], ls:[86,0,-18]});

  const WIND = P(GUARD, {root:[0,-0.5,0.3, 0,35,0], waist:[-5,-30,0], neck:[-6,-25,0], rs:[-55,0,25], re:S([0,0,0],1.8), rw:S([0,0,0],1.6), ls:[90,0,-20], le:[25,0,0], rhip:[15,0,12], rk:[-55,0,0], lhip:[35,0,-10], lk:[-55,0,0], la:[20,0,0]});
  const PUNCH = P(GUARD, {root:[0,-0.55,-0.5, 0,-25,0], waist:[-12,35,0], neck:[-6,-10,0], rs:[90,0,-8], re:S([0,0,0],3.6), rw:S([-10,0,0],3.6), ls:[35,0,-35], le:[95,0,0], rhip:[48,0,10], rk:[-62,0,0], ra:[14,0,0], lhip:[-28,0,-10], lk:[-12,0,0], la:[25,0,0]});
  const PUNCH_OVER = P(PUNCH, {root:[0,-0.6,-0.6, 0,-27,0], re:S([0,0,0],4.1), rw:S([-10,0,0],4.1)});
  const RUN = (z, y, front) => P(GUARD, Object.assign({root:[0,y,z, -8,-20,0], waist:[-18,18,0], neck:[14,-12,0], rs:[155,0,45], re:[115,0,0], rw:[-10,0,0], ls:[45,0,-15], le:[105,0,0], lw:[0,0,0]},
    front === 'r' ? {rhip:[95,0,10], rk:[-100,0,0], ra:[20,0,0], lhip:[-30,0,-8], lk:[-55,0,0], la:[30,0,0]}
                  : {lhip:[85,0,-10], lk:[-95,0,0], la:[20,0,0], rhip:[-30,0,8], rk:[-55,0,0], ra:[30,0,0]}));
  const LEAP = P(RUN(-2.8, 0.35, 'r'), {root:[0,0.35,-2.8, -6,10,0], waist:[-12,-35,0], neck:[8,15,0], rs:[75,0,35], re:[145,0,0], rw:[0,0,0], ls:[85,0,-10], le:[30,0,0], rhip:[100,0,10], rk:[-110,0,0], lhip:[-20,0,-8], lk:[-70,0,0]});
  const COCK = P(RUN(-2.2,-0.15,'r'), {waist:[-15,-10,0], rs:[90,0,30], re:[135,0,0], rw:[0,0,0]});
  const DASH_HIT = P(PUNCH, {root:[0,-0.55,-3.4, 0,-25,0]});
  const DASH_OVER = P(PUNCH_OVER, {root:[0,-0.6,-3.5, 0,-27,0]});

  const GSET = P(GUARD, {root:[0,-0.65,0, 0,0,0], waist:[-14,0,0], neck:[-4,0,0], rs:[75,0,25], re:[110,0,0], ls:[75,0,-25], le:[110,0,0], rhip:[40,0,22], rk:[-60,0,0], ra:[20,0,0], lhip:[40,0,-22], lk:[-60,0,0], la:[20,0,0]});
  const gat = i => {
    const x = [88,96,82,92,85][i % 5], z = [-6,4,-12,10,0][(i * 3) % 5];
    return i % 2 === 0
      ? P(GSET, {waist:[-14,14,0], rs:[x,0,z-4], re:S([0,0,0],3.2), rw:S([0,0,0],3.2), ls:[86,0,-12], le:[0,0,0], lw:[0,0,0]})
      : P(GSET, {waist:[-14,-14,0], ls:[x,0,4-z], le:S([0,0,0],3.2), lw:S([0,0,0],3.2), rs:[86,0,12], re:[0,0,0], rw:[0,0,0]});
  };

  const LEGWIND = P(GUARD, {root:[0,-0.8,0.1, 0,-30,8], waist:[-10,-20,-8], rs:[40,0,60], re:[60,0,0], ls:[40,0,-60], le:[60,0,0], rhip:[60,0,50], rk:[-100,0,0], ra:[20,0,0], lhip:[50,0,-8], lk:[-80,0,0], la:[25,0,0]});
  const legSpin = ry => P(GUARD, {root:[0,-0.7,0, 0,ry,10], waist:[-5,0,-12], neck:[0,0,10], rs:[20,0,70], re:[30,0,0], ls:[20,0,-70], le:[30,0,0], rhip:[0,0,82], rk:S([0,0,0],3.2), ra:S([0,0,0],3.0), lhip:[40,0,-6], lk:[-70,0,0], la:[25,0,0]});

  const BZ_BACK = P(GUARD, {root:[0,-0.75,0.5, 0,0,0], waist:[-28,0,0], neck:[18,0,0], rs:[-75,0,18], re:S([0,0,0],2.4), rw:S([0,0,0],2.2), ls:[-75,0,-18], le:S([0,0,0],2.4), lw:S([0,0,0],2.2), rhip:[55,0,16], rk:[-85,0,0], ra:[25,0,0], lhip:[-10,0,-16], lk:[-35,0,0], la:[15,0,0]});
  const BZ_BACK2 = P(BZ_BACK, {root:[0,-0.8,0.6, 0,0,0], re:S([0,0,0],2.9), rw:S([0,0,0],2.7), le:S([0,0,0],2.9), lw:S([0,0,0],2.7)});
  const BZ_HIT = P(GUARD, {root:[0,-0.75,-0.9, 0,0,0], waist:[-18,0,0], neck:[-8,0,0], rs:[88,0,-10], re:S([0,0,0],2.6), rw:S([-60,0,0],2.6), ls:[88,0,10], le:S([0,0,0],2.6), lw:S([-60,0,0],2.6), rhip:[60,0,14], rk:[-70,0,0], ra:[10,0,0], lhip:[-30,0,-14], lk:[-15,0,0], la:[25,0,0]});
  const BZ_OVER = P(BZ_HIT, {root:[0,-0.8,-1.0, 0,0,0], re:S([0,0,0],3.1), rw:S([-60,0,0],3.1), le:S([0,0,0],3.1), lw:S([-60,0,0],3.1)});

  const RK_REACH = P(GUARD, {root:[0,-0.9,0, 0,0,0], waist:[8,0,0], neck:[25,0,0], rs:[178,0,12], re:S([0,0,0],3.5), rw:S([0,0,0],3.5), ls:[178,0,-12], le:S([0,0,0],3.5), lw:S([0,0,0],3.5), rhip:[60,0,14], rk:[-95,0,0], ra:[30,0,0], lhip:[60,0,-14], lk:[-95,0,0], la:[30,0,0]});
  const RK_PULL = P(RK_REACH, {root:[0,-1.35,0.1, 0,0,0], waist:[-5,0,0], re:S([0,0,0],3.75), rw:S([0,0,0],3.75), le:S([0,0,0],3.75), lw:S([0,0,0],3.75), rhip:[85,0,14], rk:[-120,0,0], lhip:[85,0,-14], lk:[-120,0,0]});
  const RK_LAUNCH = P(GUARD, {root:[0,6,0, 0,0,0], waist:[12,0,0], neck:[10,0,0], rs:[175,0,10], re:[0,0,0], rw:[0,0,0], ls:[175,0,-10], le:[0,0,0], lw:[0,0,0], rhip:[0,0,6], rk:[0,0,0], ra:[-15,0,0], lhip:[0,0,-6], lk:[0,0,0], la:[-15,0,0]});
  const flip = (rx, y, z) => P(GUARD, {root:[0,y,z, rx,0,0], waist:[30,0,0], neck:[20,0,0], rs:[60,0,30], re:[100,0,0], ls:[60,0,-30], le:[100,0,0], rhip:[110,0,10], rk:[-130,0,0], ra:[0,0,0], lhip:[110,0,-10], lk:[-130,0,0], la:[0,0,0]});
  const RK_SLAM = P(GUARD, {root:[0,-1.15,-1.5, 0,0,0], waist:[-45,0,0], neck:[20,0,0], rs:[30,0,20], re:[0,0,0], rw:[0,0,0], ls:[30,0,-20], le:[0,0,0], lw:[0,0,0], rhip:[85,0,16], rk:[-110,0,0], ra:[25,0,0], lhip:[85,0,-16], lk:[-110,0,0], la:[25,0,0]});
  const RK_RISE = P(RK_SLAM, {root:[0,-0.9,-1.5, 0,0,0], waist:[-30,0,0], neck:[10,0,0]});

  const HAT_TOUCH = P(GUARD, {root:[0,-0.3,0, 0,-10,0], waist:[-4,5,0], neck:[-12,0,0], rs:[165,0,-35], re:[100,0,0], rw:[0,0,0], ls:[30,0,-25], le:[60,0,0], rhip:[15,0,10], rk:[-25,0,0], lhip:[0,0,-10], lk:[-15,0,0]});
  const HAT_BACK = P(HAT_TOUCH, {neck:[10,0,0], rs:[160,0,20], re:[130,0,0]});
  const PUMP_A = P(GUARD, {root:[0,-1.35,0.15, 0,0,0], waist:[-38,0,0], neck:[30,0,0], rs:[30,0,20], re:[10,0,0], rw:[-20,0,0], ls:[30,0,-20], le:[10,0,0], lw:[-20,0,0], rhip:[85,0,18], rk:[-115,0,0], ra:[30,0,0], lhip:[85,0,-18], lk:[-115,0,0], la:[30,0,0]});
  const PUMP_B = P(PUMP_A, {root:[0,-1.1,0.1, 0,0,0], waist:[-32,0,0], rhip:[75,0,18], rk:[-100,0,0], lhip:[75,0,-18], lk:[-100,0,0]});
  const MYTH = P(GUARD, {root:[0,-1.25,0, 0,0,0], waist:[-32,0,0], neck:[38,0,0], rs:[28,0,22], re:S([10,0,0],0.5), rw:[-35,0,0], ls:[15,0,-35], le:[75,0,0], lw:[-10,0,0], rhip:[80,0,35], rk:[-105,0,0], ra:[25,0,-15], lhip:[80,0,-35], lk:[-105,0,0], la:[25,0,15]});
  const MYTH_B = P(MYTH, {root:[0,-1.05,0, 0,0,0], waist:[-28,0,0], neck:[34,0,0], rhip:[70,0,35], rk:[-95,0,0], lhip:[70,0,-35], lk:[-95,0,0]});
  const MYTH_H = P(MYTH, {root:[0,-1.3,0.05, 0,0,0], waist:[-34,0,0], neck:[40,0,0]});
  const G2_BURST = P(GUARD, {root:[0,-0.3,0, 0,0,0], waist:[6,0,0], neck:[25,0,0], rs:[30,0,78], re:[60,0,0], rw:[0,0,0], ls:[30,0,-78], le:[60,0,0], lw:[0,0,0], rhip:[15,0,22], rk:[-25,0,0], ra:[8,0,0], lhip:[15,0,-22], lk:[-25,0,0], la:[8,0,0]});
  const G2_STANCE = P(GUARD, {root:[0,-0.55,0, 0,0,0], waist:[-15,0,0], neck:[15,0,0], rs:[35,0,55], re:[95,0,0], rw:[0,0,0], ls:[35,0,-55], le:[95,0,0], lw:[0,0,0], rhip:[30,0,18], rk:[-45,0,0], ra:[15,0,0], lhip:[30,0,-18], lk:[-45,0,0], la:[15,0,0]});
  const G2_STANCE2 = P(G2_STANCE, {root:[0,-0.62,0, 0,0,0], waist:[-18,0,0], neck:[17,0,0], rs:[38,0,57], ls:[38,0,-57]});
  const FLEX = P(GUARD, {root:[0,-0.2,0, 0,0,0], waist:[10,0,0], neck:[12,0,0], rs:[25,0,40], re:[90,0,0], rw:[0,0,0], ls:[25,0,-40], le:[90,0,0], lw:[0,0,0], rhip:[10,0,16], rk:[-15,0,0], ra:[5,0,0], lhip:[10,0,-16], lk:[-15,0,0], la:[5,0,0]});
  const FLEX2 = P(FLEX, {root:[0,-0.26,0, 0,0,0], waist:[13,0,0], neck:[16,0,0]});

  const U_GATHER = P(GUARD, {root:[0,-0.9,0.4, 0,45,0], waist:[-10,-40,0], neck:[-6,-30,0], rs:[-45,0,35], re:S([0,0,0],2.6), rw:S([0,0,0],2.6), ls:[90,0,-30], le:[15,0,0], lw:[0,0,0], rhip:[40,0,24], rk:[-75,0,0], ra:[25,0,0], lhip:[45,0,-24], lk:[-80,0,0], la:[25,0,0]});
  const tw = (ry, len, o) => P(U_GATHER, Object.assign({re:S([0,ry,0],len), rw:S([0,ry,0],len)}, o));
  const U_SHOT = P(GUARD, {root:[0,-0.95,-1.1, 0,-30,0], waist:[-15,42,0], neck:[-6,-12,0], rs:[90,0,-8], re:S([0,0,0],6), rw:S([-10,0,0],6), ls:[15,0,-45], le:[60,0,0], rhip:[55,0,16], rk:[-70,0,0], ra:[15,0,0], lhip:[-30,0,-16], lk:[-10,0,0], la:[28,0,0]});
  const U_OVER = P(U_SHOT, {re:S([0,0,0],6.6), rw:S([-10,0,0],6.6)});

  const HAT_HEAD = [[0,'Montrer','ChapeauTete'],[0,'Cacher','ChapeauDos']];
  const legAngles = [-90,-180,90,0,-90,-180,90,0];
  const r2 = x => Math.round(x * 100) / 100;

  const SETTLE = P(GUARD, {root:[0,-0.55,0, 0,-15,0], waist:[-13,14,0], neck:[-8,4,0], rs:[66,0,24], ls:[76,0,-20], rhip:[38,0,10], rk:[-62,0,0], ra:[22,0,0], lhip:[2,0,-10], lk:[-42,0,0], la:[18,0,0]});
  const hopBack = z => P(GUARD, {root:[0,0.45,z, 10,-15,0], waist:[-4,10,0], neck:[-10,4,0], rs:[55,0,30], re:[100,0,0], rw:[0,0,0], ls:[60,0,-28], le:[105,0,0], lw:[0,0,0], rhip:[55,0,10], rk:[-95,0,0], ra:[10,0,0], lhip:[40,0,-10], lk:[-85,0,0], la:[10,0,0]});
  const recover = (t, z) => [K(t, hopBack(z / 2), 'Cubic', 'In'), K(r2(t + 0.13), SETTLE, 'Cubic', 'Out'), K(r2(t + 0.3), GUARD)];

  const HOP_R = P(HOPUP, {waist:[-8,20,0], neck:[-4,-4,3], rs:[88,0,14], re:[90,0,0], ls:[74,0,-22], le:[120,0,0]});
  const HOP_L = P(HOPUP, {waist:[-8,2,0], neck:[-4,8,-3], ls:[94,0,-10], le:[95,0,0], rs:[64,0,26], re:[115,0,0]});

  const ANT_P = P(SETTLE, {root:[0,-0.62,0.25, 6,-22,0], waist:[-2,8,0], neck:[-10,6,0], rs:[125,0,40], re:[120,0,0]});
  const RETR_P = P(DASH_HIT, {rs:[80,0,20], re:[110,0,0], rw:[0,0,0]});

  const G_ANT = P(GSET, {root:[0,-0.75,0.3, 0,0,0], waist:[-2,0,0], neck:[-10,0,0], rs:[20,0,40], re:[120,0,0], ls:[20,0,-40], le:[120,0,0]});
  const FIN_HIT = P(PUNCH, {root:[0,-0.62,-0.7, 0,-25,0], re:S([0,0,0],4.3), rw:S([-10,0,0],4.3)});
  const nHits = 12, hitT = i => r2(0.26 + i * 0.07);

  const LAND = P(SETTLE, {root:[0,-0.85,0, 0,-15,0], waist:[-20,10,0], rs:[40,0,55], re:[70,0,0], ls:[40,0,-55], le:[70,0,0], rhip:[50,0,20], rk:[-90,0,0], lhip:[30,0,-10], lk:[-70,0,0]});
  const BZ_RETR = P(BZ_HIT, {rs:[70,0,15], re:[100,0,0], rw:[0,0,0], ls:[70,0,-15], le:[100,0,0], lw:[0,0,0]});
  const RK_SQUASH = P(RK_SLAM, {root:[0,-1.3,-1.5, 0,0,0], waist:[-50,0,0], neck:[25,0,0]});
  const U_RETR = P(U_SHOT, {rs:[75,0,20], re:[110,0,0], rw:[0,0,0], ls:[60,0,-25], le:[100,0,0]});

  const KNEEL = P(GUARD, {root:[0,-1.25,0, 0,0,0], waist:[-32,0,0], neck:[-28,0,0], rs:[32,0,10], re:S([0,0,0],0.38), rw:S([-20,0,0],0.38), ls:[40,0,-30], le:[75,0,0], lw:[-10,0,0], rhip:[80,0,32], rk:[-105,0,0], ra:[25,0,-12], lhip:[80,0,-32], lk:[-105,0,0], la:[25,0,12]});
  const KNEEL_B = P(KNEEL, {root:[0,-1.08,0, 0,0,0], waist:[-29,0,0], re:S([0,0,0],0.47), rw:S([-20,0,0],0.47), rhip:[72,0,32], rk:[-96,0,0], lhip:[72,0,-32], lk:[-96,0,0]});
  const KNEEL_H = P(KNEEL, {root:[0,-1.3,0, 0,0,0], waist:[-35,0,0], neck:[-34,0,0], re:S([0,0,0],0.3), rw:S([-20,0,0],0.3), ls:[44,0,-32], le:[80,0,0]});
  const KNEEL_H2 = P(KNEEL_H, {root:[0,-1.32,0, 0,0,0], waist:[-36,1,0], neck:[-36,0,0]});
  const KNEEL_UP  = P(KNEEL,    {root:[0,-1.22,0, 0,0,0], waist:[-28,0,0], neck:[32,0,0]});
  const KNEEL_UP2 = P(KNEEL_UP, {root:[0,-1.25,0, 0,0,0], waist:[-30,0,0], neck:[28,0,0]});
  const G2_RISE = P(G2_BURST, {neck:[30,0,0], waist:[8,0,0]});

  const KICK_WIND = P(GSET, {root:[0,-0.45,0.1, 10,-20,0], waist:[8,10,0], neck:[-14,0,0], rs:[60,0,35], re:[110,0,0], ls:[70,0,-30], le:[115,0,0], rhip:[110,0,8], rk:[-130,0,0], ra:[20,0,0], lhip:[-5,0,-10], lk:[-25,0,0], la:[15,0,0]});
  const KICK = P(KICK_WIND, {root:[0,-0.4,0, 18,-20,0], waist:[14,10,0], neck:[-20,0,0], rhip:[95,0,4], rk:S([0,0,0],2.5), ra:S([-30,0,0],2.2), lhip:[-15,0,-10], lk:[-15,0,0]});
  const KICK_OVER = P(KICK, {rk:S([0,0,0],2.9), ra:S([-30,0,0],2.6)});
  const JCROUCH = P(GUARD, {root:[0,-1.2,0, 0,10,0], waist:[-30,-15,0], neck:[25,0,0], rs:[-50,0,25], re:[40,0,0], ls:[-40,0,-25], le:[40,0,0], rhip:[85,0,14], rk:[-115,0,0], ra:[30,0,0], lhip:[85,0,-14], lk:[-115,0,0], la:[30,0,0]});
  const AIR_RISE = P(GUARD, {root:[0,4.6,-0.4, 0,30,0], waist:[-5,-30,0], neck:[-6,-20,0], rs:[-50,0,25], re:S([0,0,0],1.4), rw:S([0,0,0],1.3), ls:[100,0,-20], le:[25,0,0], rhip:[80,0,10], rk:[-110,0,0], ra:[10,0,0], lhip:[40,0,-10], lk:[-90,0,0], la:[10,0,0]});
  const AIR_CHARGE = P(AIR_RISE, {root:[0,5.8,-0.7, 10,38,0], waist:[-2,-38,0], rs:[150,0,35], re:[100,0,0], rw:[0,0,0], ls:[75,0,-15], le:[15,0,0]}); // poing près de la tête, sans étirement
  const AIR_CHARGE2 = P(AIR_CHARGE, {root:[0,5.9,-0.75, 12,40,0], re:[105,0,0], rw:[0,0,0]});
  const AIR_CHARGE3 = P(AIR_CHARGE2, {root:[0,6.0,-0.8, 14,42,0], waist:[0,-40,0], re:[110,0,0], rw:[0,0,0]});
  const AIR_PUNCH = P(GUARD, {root:[0,5.3,-1.3, -20,-25,0], waist:[-12,35,0], neck:[-12,-10,0], rs:[78,0,-8], re:S([0,0,0],5), rw:S([-10,0,0],5), ls:[20,0,-45], le:[60,0,0], lw:[0,0,0], rhip:[20,0,10], rk:[-40,0,0], ra:[20,0,0], lhip:[-30,0,-10], lk:[-60,0,0], la:[25,0,0]});
  const AIR_OVER = P(AIR_PUNCH, {root:[0,5.2,-1.4, -22,-27,0], re:S([0,0,0],5.6), rw:S([-10,0,0],5.6)});
  const AIR_RETR = P(AIR_PUNCH, {root:[0,3,-1.5, -5,-15,0], waist:[-8,10,0], rs:[70,0,25], re:[105,0,0], rw:[0,0,0], ls:[60,0,-30], le:[100,0,0], rhip:[60,0,12], rk:[-90,0,0], lhip:[50,0,-12], lk:[-80,0,0]});
  const LANDING = P(SETTLE, {root:[0,-0.95,-1.5, 0,-15,0], waist:[-24,10,0], neck:[10,0,0], rs:[40,0,50], re:[80,0,0], ls:[40,0,-50], le:[80,0,0], rhip:[70,0,16], rk:[-105,0,0], ra:[28,0,0], lhip:[60,0,-16], lk:[-100,0,0], la:[28,0,0]});

  const ANIMS = [
    {id:'Elastique_Idle_Rebond', label:'Idle — Rebond', loop:true, priority:'Idle', dur:1.4,
      keys:[K(0,GUARD,'Cubic','Out'), K(0.35,HOP_R,'Cubic','In'), K(0.7,GUARD,'Cubic','Out'), K(1.05,HOP_L,'Cubic','In'), K(1.4,GUARD)], markers:HAT_HEAD.slice()},
    {id:'Elastique_Gear2', label:'Transformation — Gear 2', priority:'Action', dur:3.6,
      keys:[K(0,GUARD,'Cubic','InOut'), K(0.3,KNEEL,'Cubic','Out'), K(0.45,KNEEL_B,'Cubic','InOut'), K(0.6,KNEEL,'Cubic','InOut'), K(0.75,KNEEL_B,'Cubic','InOut'),
        K(0.9,KNEEL_H,'Cubic','InOut'), K(1.4,KNEEL_H2,'Cubic','InOut'), K(1.9,KNEEL_H,'Cubic','InOut'), K(2.2,KNEEL_H2,'Cubic','In'),
        K(2.32,KNEEL_UP,'Cubic','Out'), K(2.7,KNEEL_UP2,'Cubic','InOut'), K(3.15,KNEEL_UP,'Cubic','InOut'), K(3.6,GUARD)],
      markers:HAT_HEAD.concat([[0.3,'Cacher','ChapeauTete'],[0.3,'Montrer','ChapeauDos'],[0.3,'Gonfler','Debut'],[0.45,'Pompe','1'],[0.75,'Pompe','2'],[0.9,'Aura','Vapeur'],[1.4,'Pompe','3'],[1.9,'Pompe','4'],[2.32,'Explosion','Vapeur']])},
    {id:'Elastique_Combo', label:'Combo — Rafale, pied, poing aérien', priority:'Action', dur:3.8,
      keys:[K(0,GUARD,'Cubic','Out'), K(0.12,G_ANT,'Cubic','In'), K(0.2,GSET,'Cubic','Out')]
        .concat(Array.from({length:nHits}, (_, i) => K(hitT(i), gat(i), i === nHits - 1 ? 'Cubic' : 'Linear')),
          [K(1.12,KICK_WIND,'Cubic','Out'), K(1.2,KICK,'Cubic','Out'), K(1.3,KICK_OVER,'Cubic','InOut'), K(1.38,KICK,'Cubic','InOut'),
           K(1.52,JCROUCH,'Cubic','Out'), K(1.72,AIR_RISE,'Cubic','Out'), K(1.95,AIR_CHARGE,'Cubic','InOut'), K(2.35,AIR_CHARGE2,'Cubic','InOut'), K(2.65,AIR_CHARGE3,'Cubic','Out'),
           K(2.75,AIR_PUNCH,'Cubic','Out'), K(2.9,AIR_OVER,'Cubic','InOut'), K(3.02,AIR_RETR,'Cubic','In'), K(3.28,LANDING,'Cubic','Out')], recover(3.5,-1.5)),
      markers:[[0.2,'VFX','Rafale_Trainees']].concat(Array.from({length:nHits}, (_, i) => [hitT(i), 'Impact', 'Rafale'])).concat([[1.2,'Impact','Pied'],[1.6,'Feu','Debut'],[2.75,'Impact','AirPoing'],[2.75,'Explosion','AirPoing'],[3.0,'Feu','Fin'],[3.28,'Esquive','Atterrissage']])},
    {id:'Elastique_Poing', label:'Poing élastique — Charge', priority:'Action', dur:1.5,
      keys:[K(0,GUARD,'Cubic','Out'), K(0.1,ANT_P,'Cubic','In'), K(0.2,RUN(-0.4,-0.15,'r'),'Linear'), K(0.36,RUN(-1.3,0.1,'l'),'Linear'), K(0.52,COCK,'Cubic','InOut'),
        K(0.64,LEAP,'Cubic','In'), K(0.71,DASH_HIT,'Cubic','Out'), K(0.82,DASH_OVER,'Cubic','InOut'), K(0.9,DASH_HIT,'Cubic','InOut'), K(1.06,RETR_P,'Cubic','Out')].concat(recover(1.2,-3.4)),
      markers:[[0.15,'Feu','Debut'],[0.71,'Impact','Poing'],[0.9,'Feu','Fin']]},
    {id:'Elastique_Rafale', label:'Rafale de poings', priority:'Action', dur:1.85,
      keys:[K(0,GUARD,'Cubic','Out'), K(0.12,G_ANT,'Cubic','In'), K(0.2,GSET,'Cubic','Out')]
        .concat(Array.from({length:nHits}, (_, i) => K(hitT(i), gat(i), i === nHits - 1 ? 'Cubic' : 'Linear')),
          [K(1.12,WIND,'Cubic','Out'), K(1.2,FIN_HIT,'Cubic','InOut'), K(1.32,FIN_HIT,'Elastic','Out'), K(1.7,SETTLE,'Cubic','InOut'), K(1.85,GUARD)]),
      markers:Array.from({length:nHits}, (_, i) => [hitT(i), 'Impact', 'Rafale']).concat([[1.2,'Impact','RafaleFinal'],[1.2,'Explosion','Rafale']])},
    {id:'Elastique_Fouet', label:'Fouet de jambe', priority:'Action', dur:1.2,
      keys:[K(0,GUARD,'Cubic','Out'), K(0.2,LEGWIND,'Cubic','Out')].concat(legAngles.map((ang, i) => K(r2(0.27 + i * 0.07), legSpin(ang), i === 7 ? 'Cubic' : 'Linear')), [K(0.86,LAND,'Cubic','Out'), K(1.02,SETTLE,'Cubic','InOut'), K(1.2,GUARD)]),
      markers:[[0.34,'Impact','Fouet'],[0.48,'Impact','Fouet'],[0.62,'Impact','Fouet'],[0.76,'Impact','Fouet']]},
    {id:'Elastique_Double_Paume', label:'Double paume', priority:'Action', dur:1.4,
      keys:[K(0,GUARD,'Cubic','InOut'), K(0.35,BZ_BACK,'Cubic','InOut'), K(0.52,BZ_BACK2,'Cubic','Out'), K(0.6,BZ_HIT,'Cubic','Out'), K(0.72,BZ_OVER,'Cubic','InOut'), K(0.8,BZ_HIT,'Cubic','InOut'), K(0.98,BZ_RETR,'Cubic','Out')].concat(recover(1.1,-0.9)),
      markers:[[0.6,'Impact','DoublePaume'],[0.6,'Explosion','DoublePaume']]},
    {id:'Elastique_Fusee', label:'Fusée + impact au sol', priority:'Action', dur:1.72,
      keys:[K(0,GUARD,'Cubic','InOut'), K(0.22,RK_REACH,'Cubic','In'), K(0.5,RK_PULL,'Cubic','Out'), K(0.64,RK_LAUNCH,'Cubic','Out'),
        K(0.74,flip(-90,7.6,-0.4),'Linear'), K(0.84,flip(-180,8.2,-0.8),'Linear'), K(0.94,flip(90,7.6,-1.1),'Linear'), K(1.04,flip(0,5.5,-1.3),'Cubic','In'),
        K(1.18,RK_SLAM,'Cubic','Out'), K(1.3,RK_SQUASH,'Cubic','Out')].concat(recover(1.42,-1.5)),
      markers:[[0.5,'Esquive','Fusee'],[1.18,'Impact','Sol'],[1.18,'Explosion','Sol']]},
    {id:'Elastique_Ultime_Spirale', label:'Ultime — Canon spirale', priority:'Action4', dur:3.2,
      keys:[K(0,GUARD,'Cubic','InOut'), K(0.4,tw(0,2.6),'Linear'), K(0.7,tw(120,3.0),'Linear'), K(1.0,tw(240,3.3),'Linear'), K(1.3,tw(0,3.6),'Linear'),
        K(1.6,tw(120,3.9),'Cubic','In'), K(1.78,tw(170,4.2,{root:[0,-1.0,0.6, 0,50,0]}),'Cubic','Out'), K(1.88,U_SHOT,'Cubic','Out'),
        K(2.15,U_OVER,'Cubic','InOut'), K(2.35,U_SHOT,'Elastic','Out'), K(2.8,U_RETR,'Cubic','Out')].concat(recover(2.9,-1.1)),
      markers:[[0.4,'Aura','Ultime'],[1.88,'Impact','Ultime'],[1.88,'Explosion','Ultime'],[2.6,'Fin','Aura'],[2.6,'Gonfler','Fin']]}
  ];

  function chain(id, label, ids) {
    let off = 0; const keys = [], markers = [];
    ids.forEach((src, i) => {
      const a = ANIMS.find(x => x.id === src);
      if (i > 0) keys.pop();
      a.keys.forEach(k => keys.push(Object.assign({}, k, {t: Math.round((k.t + off) * 1000) / 1000})));
      a.markers.forEach(m => { if (!(i > 0 && m[0] === 0)) markers.push([Math.round((m[0] + off) * 1000) / 1000, m[1], m[2]]); });
      off += a.dur;
    });
    return {id, label, priority:'Action', dur: Math.round(off * 1000) / 1000, keys, markers};
  }
  ANIMS.unshift(chain('Elastique_Sequence_Complete', 'Séquence complète',
    ['Elastique_Gear2','Elastique_Combo']));
  const KEEP = ['Elastique_Sequence_Complete','Elastique_Idle_Rebond','Elastique_Gear2','Elastique_Combo'];
  const kept = KEEP.map(id => ANIMS.find(x => x.id === id));
  ANIMS.length = 0; ANIMS.push(...kept);

  const EASE = {
    Linear: x => x, Constant: () => 0,
    Cubic: {In: x => x*x*x, Out: x => 1-Math.pow(1-x,3), InOut: x => x < .5 ? 4*x*x*x : 1-Math.pow(-2*x+2,3)/2},
    Elastic: {Out: x => x === 0 ? 0 : x === 1 ? 1 : Math.pow(2,-10*x)*Math.sin((x*10-.75)*2*Math.PI/3)+1},
    Bounce: {Out: x => { const n=7.5625,d=2.75; if(x<1/d) return n*x*x; if(x<2/d) return n*(x-=1.5/d)*x+.75; if(x<2.5/d) return n*(x-=2.25/d)*x+.9375; return n*(x-=2.625/d)*x+.984375; }}
  };
  function ease(e, d, x) { const f = EASE[e]; if (typeof f === 'function') return f(x); return (f[d] || f.Out || (y => y))(x); }
  function sample(anim, t) {
    const ks = anim.keys;
    if (t <= ks[0].t) return {a: ks[0].pose, b: ks[0].pose, w: 0};
    for (let i = 0; i < ks.length - 1; i++) {
      const A = ks[i], B = ks[i+1];
      if (t < B.t) return {a: A.pose, b: B.pose, w: ease(A.e, A.d, (t - A.t) / (B.t - A.t))};
    }
    const L = ks[ks.length-1].pose; return {a: L, b: L, w: 0};
  }
  function visibility(anim, t) {
    const v = {ChapeauTete:true, ChapeauDos:false};
    anim.markers.forEach(m => { if (m[0] <= t + 1e-6 && (m[1] === 'Montrer' || m[1] === 'Cacher')) v[m[2]] = m[1] === 'Montrer'; });
    return v;
  }
  function fireOn(anim, t) {
    let on = false;
    anim.markers.forEach(m => { if (m[0] <= t && m[1] === 'Feu') on = m[2] === 'Debut'; });
    return on;
  }
  function inflateAmt(anim, t) {
    let st = -1;
    anim.markers.forEach(m => { if (m[0] <= t && m[1] === 'Gonfler') st = m[2] === 'Debut' ? m[0] : -1; });
    if (st < 0 || t > anim.dur - 0.15) return 0;
    return Math.min(1, (t - st) / 0.3);
  }
  function auraOn(anim, t) {
    let on = false;
    anim.markers.forEach(m => { if (m[0] <= t && (m[1] === 'Aura' || m[1] === 'Fin')) on = m[1] === 'Aura'; });
    return on && t < anim.dur - 0.15;
  }

  const n = x => String(Math.round(x * 1000) / 1000);
  function toLuau() {
    const L = [];
    L.push('--[[ COMBATTANT ÉLASTIQUE — animations R15');
    L.push('  1. Dans l\'Explorer, sélectionne le Model de ton personnage R15 (avec Humanoid).');
    L.push('  2. Affichage > Barre de commande : colle tout ce script puis Entrée.');
    L.push('  3. Avatar > Éditeur d\'animation > choisis le rig > ⋯ > Charger > Elastique_…');
    L.push('  4. ⋯ > Publier sur Roblox, puis copie l\'ID d\'animation (rbxassetid://…).');
    L.push('  Les membres s\'étirent via la position des Pose (Motor6D) : le script marqueurs remplit les trous avec des tubes.');
    L.push('  Marqueurs : Montrer / Cacher (valeur = nom de l\'Accessory), Impact, Aura, Explosion, Fin, Esquive, Feu (Debut/Fin), Gonfler (Debut/Fin), Pompe.');
    L.push(']]');
    L.push('local rig = game:GetService("Selection"):Get()[1]');
    L.push('assert(rig and rig:FindFirstChildOfClass("Humanoid"), "Sélectionne d\'abord ton rig R15 dans l\'Explorer.")');
    L.push('local ServerStorage = game:GetService("ServerStorage")');
    L.push('local saves = ServerStorage:FindFirstChild("RBX_ANIMSAVES")');
    L.push('if not saves then saves = Instance.new("Folder") saves.Name = "RBX_ANIMSAVES" saves.Parent = ServerStorage end');
    L.push('local holder = saves:FindFirstChild(rig.Name)');
    L.push('if not holder then holder = Instance.new("ObjectValue") holder.Name = rig.Name holder.Value = rig holder.Parent = saves end');
    L.push('local rad = math.rad');
    L.push('local STYLE = {Cubic = Enum.PoseEasingStyle.CubicV2, Linear = Enum.PoseEasingStyle.Linear, Constant = Enum.PoseEasingStyle.Constant, Elastic = Enum.PoseEasingStyle.Elastic, Bounce = Enum.PoseEasingStyle.Bounce}');
    L.push('local TREE = {"LowerTorso", {{"UpperTorso", {{"Head", {}}, {"RightUpperArm", {{"RightLowerArm", {{"RightHand", {}}}}}}, {"LeftUpperArm", {{"LeftLowerArm", {{"LeftHand", {}}}}}}}}, {"RightUpperLeg", {{"RightLowerLeg", {{"RightFoot", {}}}}}}, {"LeftUpperLeg", {{"LeftLowerLeg", {{"LeftFoot", {}}}}}}}}');
    L.push('local ANIMS = {');
    ANIMS.forEach(a => {
      L.push(`  {name = "${a.id}", loop = ${!!a.loop}, priority = "${a.priority}", keys = {`);
      a.keys.forEach(k => {
        const parts = J.map(j => `${PART[j]} = {${k.pose[j].map(n).join(', ')}}`).join(', ');
        L.push(`    {t = ${n(k.t)}, e = "${k.e}", d = "${k.d}", p = {${parts}}},`);
      });
      L.push('  }, markers = {' + a.markers.map(m => `{${n(m[0])}, "${m[1]}", "${m[2]}"}`).join(', ') + '}},');
    });
    L.push('}');
    L.push(`
local function addPose(kf, parentPose, node, k)
	local name, children = node[1], node[2]
	local v = k.p[name]
	local pose = Instance.new("Pose")
	pose.Name = name
	pose.CFrame = CFrame.new(v[1], v[2], v[3]) * CFrame.Angles(rad(v[4]), rad(v[5]), rad(v[6]))
	pose.Weight = 1
	pose.EasingStyle = STYLE[k.e]
	pose.EasingDirection = Enum.PoseEasingDirection[k.d]
	parentPose:AddSubPose(pose)
	for _, child in ipairs(children) do addPose(kf, pose, child, k) end
end

for _, a in ipairs(ANIMS) do
	local old = holder:FindFirstChild(a.name)
	if old then old:Destroy() end
	local seq = Instance.new("KeyframeSequence")
	seq.Name = a.name
	seq.Loop = a.loop
	seq.Priority = Enum.AnimationPriority[a.priority]
	for _, k in ipairs(a.keys) do
		local kf = Instance.new("Keyframe")
		kf.Time = k.t
		local hrp = Instance.new("Pose")
		hrp.Name = "HumanoidRootPart"
		hrp.Weight = 0
		kf:AddPose(hrp)
		addPose(kf, hrp, TREE, k)
		kf.Parent = seq
	end
	for _, m in ipairs(a.markers) do
		local kf
		for _, existing in ipairs(seq:GetKeyframes()) do
			if math.abs(existing.Time - m[1]) < 1e-4 then kf = existing break end
		end
		if not kf then kf = Instance.new("Keyframe") kf.Time = m[1] kf.Parent = seq end
		local mk = Instance.new("KeyframeMarker")
		mk.Name = m[2]
		mk.Value = m[3]
		kf:AddMarker(mk)
	end
	seq.Parent = holder
end
print("✔ " .. #ANIMS .. " animations créées dans ServerStorage.RBX_ANIMSAVES." .. rig.Name .. " — ouvre l'Éditeur d'animation > Charger.")`);
    return L.join('\n');
  }

  const RUNTIME = `-- LocalScript à placer dans StarterPlayer > StarterPlayerScripts
-- 1) Remplit les trous des membres étirés avec des tubes élastiques (couleur du membre).
-- 2) Affiche / cache les Accessory selon les marqueurs Montrer / Cacher.
-- 3) Expose Impact / Aura / Explosion / Fin / Esquive via onMarker() pour tes hitbox et VFX.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local LIMBS = {"RightElbow", "RightWrist", "LeftElbow", "LeftWrist", "RightKnee", "RightAnkle", "LeftKnee", "LeftAnkle"}
local folder = Instance.new("Folder")
folder.Name = "MembresElastiques"
folder.Parent = workspace
local rigs = {}

local function setVisible(character, accessoryName, visible)
	local acc = character:FindFirstChild(accessoryName)
	if not acc then return end
	for _, d in ipairs(acc:GetDescendants()) do
		if d:IsA("BasePart") or d:IsA("Decal") then d.Transparency = visible and 0 or 1 end
	end
end

local TweenService = game:GetService("TweenService")
local INFLATE = {"RightUpperArm", "RightLowerArm", "LeftUpperArm", "LeftLowerArm", "RightUpperLeg", "RightLowerLeg", "LeftUpperLeg", "LeftLowerLeg"}
local baseSize = {}
local function inflate(character, k, t)
	for _, n in ipairs(INFLATE) do
		local p = character:FindFirstChild(n)
		if p then
			baseSize[p] = baseSize[p] or p.Size
			local s = baseSize[p]
			TweenService:Create(p, TweenInfo.new(t or 0.3, Enum.EasingStyle.Quad), {Size = Vector3.new(s.X * k, s.Y, s.Z * k)}):Play()
		end
	end
end

local function onMarker(character, name, value)
	if name == "Pompe" then
		inflate(character, 1.24, 0.08)
		task.delay(0.1, function() inflate(character, 1.12, 0.25) end)
	end
	-- ex : if name == "Impact" then ... end
end

local function makeTube(motor)
	local p = Instance.new("Part")
	p.Name = "Elastique_" .. motor.Name
	p.Shape = Enum.PartType.Cylinder
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = motor.Part1 and motor.Part1.Color or Color3.fromRGB(230, 180, 140)
	p.Transparency = 1
	p.Parent = folder
	return p
end

local function hook(character)
	local humanoid = character:WaitForChild("Humanoid")
	local animator = humanoid:WaitForChild("Animator")
	local list = {}
	for _, n in ipairs(LIMBS) do
		local m = character:WaitForChild(n == "RightElbow" and "RightLowerArm" or n == "RightWrist" and "RightHand" or n == "LeftElbow" and "LeftLowerArm" or n == "LeftWrist" and "LeftHand" or n == "RightKnee" and "RightLowerLeg" or n == "RightAnkle" and "RightFoot" or n == "LeftKnee" and "LeftLowerLeg" or "LeftFoot", 5)
		local motor = m and m:FindFirstChild(n)
		if motor and motor:IsA("Motor6D") then table.insert(list, {m = motor, p = makeTube(motor)}) end
	end
	rigs[character] = list
	character.AncestryChanged:Connect(function(_, parent)
		if parent then return end
		for _, e in ipairs(list) do e.p:Destroy() end
		rigs[character] = nil
	end)
	animator.AnimationPlayed:Connect(function(track)
		track:GetMarkerReachedSignal("Montrer"):Connect(function(v) setVisible(character, v, true) end)
		track:GetMarkerReachedSignal("Cacher"):Connect(function(v) setVisible(character, v, false) end)
		track:GetMarkerReachedSignal("Gonfler"):Connect(function(v) inflate(character, v == "Debut" and 1.12 or 1) end)
		for _, n in ipairs({"Impact", "Aura", "Explosion", "Fin", "Esquive", "Feu", "Pompe"}) do
			track:GetMarkerReachedSignal(n):Connect(function(v) onMarker(character, n, v) end)
		end
	end)
end

RunService.RenderStepped:Connect(function()
	for _, list in pairs(rigs) do
		for _, e in ipairs(list) do
			local m = e.m
			if m.Part0 and m.Part1 then
				local a = (m.Part0.CFrame * m.C0).Position
				local b = (m.Part1.CFrame * m.C1).Position
				local d = (b - a).Magnitude
				if d > 0.15 then
					local w = math.min(m.Part1.Size.X, m.Part1.Size.Z) * 0.75
					e.p.Size = Vector3.new(d, w, w)
					e.p.CFrame = CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.rad(90), 0)
					e.p.Transparency = 0
				else
					e.p.Transparency = 1
				end
			end
		end
	end
end)

local function watch(player)
	if player.Character then task.spawn(hook, player.Character) end
	player.CharacterAdded:Connect(hook)
end
for _, p in ipairs(Players:GetPlayers()) do watch(p) end
Players.PlayerAdded:Connect(watch)
`;

  window.ELASTIC = {ANIMS, ACCESSORIES, J, PART, sample, visibility, auraOn, fireOn, inflateAmt, toLuau, RUNTIME};
})();
