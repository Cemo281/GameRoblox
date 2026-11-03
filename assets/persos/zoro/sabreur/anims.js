(function () {
  const J = ['root','waist','neck','rs','re','rw','ls','le','lw','rhip','rk','ra','lhip','lk','la'];
  const PART = {root:'LowerTorso',waist:'UpperTorso',neck:'Head',rs:'RightUpperArm',re:'RightLowerArm',rw:'RightHand',ls:'LeftUpperArm',le:'LeftLowerArm',lw:'LeftHand',rhip:'RightUpperLeg',rk:'RightLowerLeg',ra:'RightFoot',lhip:'LeftUpperLeg',lk:'LeftLowerLeg',la:'LeftFoot'};
  const ACCESSORIES = [
    {name:'SabresHanche', att:'LeftHipAttachment (LowerTorso)', desc:'3 sabres au fourreau'},
    {name:'SabreDroit', att:'RightGripAttachment (RightHand)', desc:'sabre main droite'},
    {name:'SabreGauche', att:'LeftGripAttachment (LeftHand)', desc:'sabre main gauche'},
    {name:'SabreBouche', att:'FaceFrontAttachment (Head)', desc:'sabre tenu en bouche'}
  ];
  // [px,py,pz, rx,ry,rz] — rotation seule : [rx,ry,rz] (degrés)
  const norm = v => !v ? [0,0,0,0,0,0] : (v.length === 3 ? [0,0,0].concat(v) : v.slice());
  const P = (base, o) => { const r = {}; J.forEach(j => r[j] = norm((o && o[j]) || base[j])); return r; };
  const K = (t, pose, e, d) => ({t, pose, e: e || 'Cubic', d: d || 'Out'});

  const RELAX = P({}, {rs:[5,0,6], ls:[5,0,-6], re:[10,0,0], le:[10,0,0]});
  const GUARD = P({}, {
    root:[0,-0.4,0, 0,-20,0], waist:[-10,15,0], neck:[-6,8,0],
    rs:[60,15,25], re:[50,0,0], rw:[-55,0,0],
    ls:[35,-15,-40], le:[45,0,0], lw:[-45,0,0],
    rhip:[30,0,12], rk:[-50,0,0], ra:[18,0,0],
    lhip:[-15,0,-14], lk:[-30,0,0], la:[12,0,0]
  });
  const BREATH = P(GUARD, {root:[0,-0.47,0, 0,-20,0], waist:[-13,15,0], rs:[63,15,25], ls:[38,-15,-40], neck:[-8,8,0]});

  const WIND1 = P(GUARD, {root:[0,-0.45,0, 0,10,0], waist:[-5,-40,0], rs:[85,0,80], re:[25,0,0], rw:[-80,0,0], ls:[20,0,-30]});
  const STRIKE1 = P(GUARD, {root:[0,-0.55,-0.3, 0,-35,0], waist:[-12,45,0], neck:[-6,-10,0], rs:[85,0,-35], re:[10,0,0], rw:[-80,0,0], ls:[10,0,-55], le:[20,0,0]});
  const WIND2 = P(GUARD, {root:[0,-0.5,0, 0,-30,0], waist:[-15,-30,0], ls:[40,0,45], le:[60,0,0], lw:[-60,0,0], rs:[40,0,50]});
  const STRIKE2 = P(GUARD, {root:[0,-0.35,-0.3, 0,25,0], waist:[5,40,0], neck:[5,15,0], ls:[150,0,-60], le:[10,0,0], lw:[-30,0,0], rs:[30,0,60]});
  const WIND3 = P(GUARD, {root:[0,-0.25,0.1, 0,0,0], waist:[18,0,0], neck:[12,0,0], rs:[170,0,15], re:[40,0,0], rw:[0,0,0], ls:[170,0,-15], le:[40,0,0], lw:[0,0,0]});
  const STRIKE3 = P(GUARD, {root:[0,-0.8,-0.4, 0,0,0], waist:[-35,0,0], neck:[-10,0,0], rs:[45,0,10], re:[0,0,0], rw:[-70,0,0], ls:[45,0,-10], le:[0,0,0], lw:[-70,0,0], rhip:[60,0,10], rk:[-80,0,0], lhip:[-25,0,-10], lk:[-40,0,0]});
  const tuck = ry => P(GUARD, {root:[0,-0.6,0, 0,ry,0], waist:[-10,0,0], rs:[60,0,-40], ls:[60,0,40], re:[80,0,0], le:[80,0,0]});
  const THRUST = P(GUARD, {root:[0,-0.7,-1.2, 0,0,0], waist:[-20,0,0], neck:[5,0,0], rs:[90,0,5], re:[0,0,0], rw:[-90,0,0], ls:[90,0,-5], le:[0,0,0], lw:[-90,0,0], rhip:[75,0,8], rk:[-75,0,0], ra:[0,0,0], lhip:[-45,0,-8], lk:[-20,0,0]});

  const CROSS = P(GUARD, {root:[0,-0.55,0.2, 0,0,0], waist:[10,0,0], neck:[8,0,0], rs:[135,0,-45], re:[20,0,0], rw:[-20,0,0], ls:[135,0,45], le:[20,0,0], lw:[-20,0,0], rhip:[45,0,15], rk:[-70,0,0], ra:[25,0,0], lhip:[45,0,-15], lk:[-70,0,0], la:[25,0,0]});
  const CROSS2 = P(CROSS, {root:[0,-0.62,0.25, 0,0,0], rs:[142,0,-52], ls:[142,0,52]});
  const XSLASH = P(GUARD, {root:[0,-0.85,-1.2, 0,0,0], waist:[-25,0,0], neck:[0,0,0], rs:[35,0,85], re:[0,0,0], rw:[-60,0,0], ls:[35,0,-85], le:[0,0,0], lw:[-60,0,0], rhip:[70,0,12], rk:[-80,0,0], ra:[10,0,0], lhip:[-40,0,-12], lk:[-25,0,0], la:[20,0,0]});
  const XHOLD = P(XSLASH, {root:[0,-0.8,-1.15, 0,0,0], waist:[-22,0,0]});

  const SPREAD = P(GUARD, {root:[0,-0.35,0, 0,40,0], waist:[-5,0,0], neck:[0,0,0], rs:[0,0,95], re:[0,0,0], rw:[-90,0,0], ls:[0,0,-95], le:[0,0,0], lw:[-90,0,0], rhip:[10,0,15], rk:[-20,0,0], ra:[10,0,0], lhip:[10,0,-15], lk:[-20,0,0], la:[10,0,0]});
  const spin = (ry, y) => P(SPREAD, {root:[0,y,0, 0,ry,0]});
  const SPINEND = P(GUARD, {root:[0,-0.9,-0.4, 0,40,0], waist:[-25,-20,0], rs:[60,0,80], ls:[60,0,-80], re:[10,0,0], le:[10,0,0], rhip:[60,0,20], rk:[-90,0,0], lhip:[-20,0,-20], lk:[-50,0,0]});

  const CROUCH = P(GUARD, {root:[0,-1.2,0.2, 0,0,0], waist:[-30,0,0], neck:[15,0,0], rs:[-45,0,20], re:[20,0,0], rw:[-20,0,0], ls:[-45,0,-20], le:[20,0,0], lw:[-20,0,0], rhip:[80,0,12], rk:[-110,0,0], ra:[30,0,0], lhip:[80,0,-12], lk:[-110,0,0], la:[30,0,0]});
  const AIR = P(GUARD, {root:[0,5,-0.4, 0,0,0], waist:[18,0,0], neck:[10,0,0], rs:[175,0,10], re:[45,0,0], rw:[0,0,0], ls:[175,0,-10], le:[45,0,0], lw:[0,0,0], rhip:[60,0,10], rk:[-100,0,0], ra:[0,0,0], lhip:[30,0,-10], lk:[-80,0,0], la:[0,0,0]});
  const APEX = P(AIR, {root:[0,5.6,-0.7, 15,0,0], waist:[24,0,0], rs:[178,0,10], ls:[178,0,-10]});
  const SLAM = P(GUARD, {root:[0,-1.1,-1, 0,0,0], waist:[-45,0,0], neck:[-15,0,0], rs:[25,0,10], re:[0,0,0], rw:[-60,0,0], ls:[25,0,-10], le:[0,0,0], lw:[-60,0,0], rhip:[85,0,10], rk:[-100,0,0], ra:[15,0,0], lhip:[-20,0,-10], lk:[-100,0,0], la:[40,0,0]});
  const RISE = P(SLAM, {root:[0,-1,-1, 0,0,0], waist:[-40,0,0], neck:[-5,0,0]});

  const REACH1 = P(RELAX, {root:[0,-0.15,0, 0,0,0], waist:[-5,25,0], neck:[-15,-10,0], rs:[35,0,-30], re:[75,0,0], ls:[10,0,-15], le:[40,0,0]});
  const DRAW1 = P(RELAX, {root:[0,-0.25,0, 0,-15,0], waist:[-5,-15,0], neck:[-5,10,0], rs:[100,0,55], re:[15,0,0], rw:[-40,0,0], ls:[15,0,-15], le:[50,0,0]});
  const REACH2 = P(DRAW1, {waist:[-8,10,0], neck:[-15,0,0], ls:[20,0,-5], le:[60,0,0]});
  const DRAW2 = P(DRAW1, {root:[0,-0.3,0, 0,15,0], waist:[-5,10,0], neck:[-5,-5,0], ls:[100,0,-55], le:[15,0,0], lw:[-40,0,0]});
  const MOUTH = P(DRAW2, {neck:[-10,0,0], rs:[110,0,-25], re:[120,0,0], rw:[-20,0,0]});

  const GATHER = P(GUARD, {root:[0,-0.9,0, 0,0,0], waist:[-35,0,0], neck:[-25,0,0], rs:[25,0,-45], re:[70,0,0], rw:[-30,0,0], ls:[25,0,45], le:[70,0,0], lw:[-30,0,0], rhip:[60,0,18], rk:[-90,0,0], ra:[30,0,0], lhip:[60,0,-18], lk:[-90,0,0], la:[30,0,0]});
  const GATHER_B = P(GATHER, {root:[0,-0.96,0, 0,0,0], waist:[-38,3,0], rs:[27,0,-47]});
  const BURST = P(GUARD, {root:[0,0.3,0, 0,0,0], waist:[25,0,0], neck:[30,0,0], rs:[0,0,145], re:[10,0,0], rw:[-60,0,0], ls:[0,0,-145], le:[10,0,0], lw:[-60,0,0], rhip:[0,0,18], rk:[0,0,0], ra:[0,0,0], lhip:[0,0,-18], lk:[0,0,0], la:[0,0,0]});
  const BURST2 = P(BURST, {root:[0,0.45,0, 0,0,0], waist:[28,0,0], neck:[34,0,0]});
  const UCROSS = P(CROSS2, {root:[0,-0.75,0.3, 0,0,0]});
  const USLASH = P(XSLASH, {root:[0,-1,-1.4, 0,0,0], waist:[-30,0,0], rs:[25,0,95], ls:[25,0,-95]});

  const at = (pose, x, y, z, rx, ry, rz) => { const p = P(pose); const r = p.root; p.root = [x, y ?? r[1], z, rx ?? r[3], ry ?? r[4], rz ?? r[5]]; return p; };
  const DODGE_L = P(GUARD, {root:[-2,-0.75,0, 0,-20,15], waist:[-15,25,0], neck:[-10,8,0], rs:[45,0,30], re:[70,0,0], ls:[20,0,-50], le:[55,0,0], rhip:[10,0,35], rk:[-10,0,0], ra:[0,0,0], lhip:[45,0,-5], lk:[-85,0,0], la:[30,0,0]});
  const DODGE_R = P(GUARD, {root:[2,-0.75,0, 0,-20,-15], waist:[-15,5,0], neck:[-10,8,0], rs:[50,0,45], re:[70,0,0], ls:[30,0,-30], le:[55,0,0], lhip:[10,0,-35], lk:[-10,0,0], la:[0,0,0], rhip:[45,0,5], rk:[-85,0,0], ra:[30,0,0]});
  const HOP = P(GUARD, {root:[0,-0.1,0, 0,-20,-6], waist:[-8,10,0], rhip:[50,0,10], rk:[-90,0,0], lhip:[40,0,-10], lk:[-90,0,0], ra:[10,0,0], la:[10,0,0]});
  const BACKSTEP = P(GUARD, {root:[0,-0.8,2, 12,-20,0], waist:[-5,15,0], neck:[-12,8,0], rs:[70,0,20], re:[60,0,0], rw:[-60,0,0], ls:[60,0,-25], le:[60,0,0], rhip:[-25,0,10], rk:[-20,0,0], ra:[25,0,0], lhip:[60,0,-10], lk:[-95,0,0], la:[25,0,0]});
  const DBL_WIND_R = P(GUARD, {root:[0,-0.5,0, 0,15,0], waist:[-8,-45,0], neck:[-6,-5,0], rs:[80,0,85], re:[20,0,0], rw:[-80,0,0], ls:[85,0,40], le:[35,0,0], lw:[-80,0,0]});
  const DBL_STRIKE_L = P(GUARD, {root:[0,-0.6,-0.3, 0,-30,0], waist:[-12,50,0], neck:[-6,-12,0], rs:[85,0,-30], re:[10,0,0], rw:[-80,0,0], ls:[80,0,-85], le:[10,0,0], lw:[-80,0,0]});
  const DBL_WIND_L = P(GUARD, {root:[0,-0.5,0, 0,-40,0], waist:[-8,45,0], neck:[-6,10,0], rs:[85,0,-40], re:[35,0,0], rw:[-80,0,0], ls:[80,0,-85], le:[20,0,0], lw:[-80,0,0]});
  const DBL_STRIKE_R = P(GUARD, {root:[0,-0.6,-0.3, 0,10,0], waist:[-12,-45,0], neck:[-6,10,0], rs:[80,0,85], re:[10,0,0], rw:[-80,0,0], ls:[85,0,30], le:[10,0,0], lw:[-80,0,0]});
  const DBL_LOW = P(GUARD, {root:[0,-0.9,0.2, 0,0,0], waist:[-25,0,0], neck:[10,0,0], rs:[-30,0,35], re:[15,0,0], rw:[-30,0,0], ls:[-30,0,-35], le:[15,0,0], lw:[-30,0,0], rhip:[60,0,14], rk:[-90,0,0], ra:[25,0,0], lhip:[50,0,-14], lk:[-85,0,0], la:[25,0,0]});
  const DBL_RISE = P(GUARD, {root:[0,-0.2,-0.5, 0,0,0], waist:[15,0,0], neck:[12,0,0], rs:[165,0,20], re:[10,0,0], rw:[-20,0,0], ls:[165,0,-20], le:[10,0,0], lw:[-20,0,0], rhip:[35,0,10], rk:[-30,0,0], lhip:[-25,0,-10], lk:[-15,0,0]});
  const SPREAD_AURA = P({}, {root:[0,-0.25,0, 0,0,0], waist:[-4,0,0], neck:[-12,0,0], rs:[8,0,60], re:[0,0,0], rw:[0,-90,0], ls:[8,0,-60], le:[0,0,0], lw:[0,90,0], rhip:[8,0,14], rk:[-14,0,0], ra:[6,0,0], lhip:[8,0,-14], lk:[-14,0,0], la:[6,0,0]});
  const SPREAD_AURA2 = P(SPREAD_AURA, {root:[0,-0.35,0, 0,0,0], waist:[-2,0,0], neck:[-8,0,0], rs:[8,0,65], ls:[8,0,-65], rk:[-20,0,0], lk:[-20,0,0], rhip:[11,0,14], lhip:[11,0,-14]});
  // Charge d'aura v2 (03/11, réf. utilisateur) : bras tendus à l'horizontale, lames dans le prolongement des bras,
  // lévitation, tête baissée. rw/lw -80 : la lame (-Z de la main) passe dans l'axe du bras.
  const WINGS = P(GUARD, {root:[0,0.4,0, 0,0,0], waist:[12,0,0], neck:[-12,0,0],
    rs:[0,0,100], re:[5,0,0], rw:[-80,0,0], ls:[0,0,-100], le:[5,0,0], lw:[-80,0,0],
    rhip:[20,0,8], rk:[-35,0,0], ra:[20,0,0], lhip:[5,0,-8], lk:[-15,0,0], la:[25,0,0]});
  const FLOAT_A = P(WINGS, {root:[0,1.3,0, 0,0,0], waist:[8,0,0], neck:[-14,0,0],
    rs:[6,0,88], re:[10,0,0], rw:[-75,0,0], ls:[6,0,-88], le:[10,0,0], lw:[-75,0,0],
    rhip:[28,0,8], rk:[-45,0,0], ra:[25,0,0], lhip:[10,0,-8], lk:[-20,0,0], la:[30,0,0]});
  const FLOAT_B = P(FLOAT_A, {root:[0,1.5,0, 0,0,0], waist:[10,0,0], neck:[-10,0,0], rs:[4,0,92], ls:[4,0,-92], rk:[-50,0,0], lk:[-25,0,0]});
  const LAND = P(GUARD, {root:[0,-0.85,0, 0,-20,0], waist:[-18,15,0], neck:[-12,8,0], rk:[-75,0,0], lk:[-55,0,0], rhip:[45,0,12]});
  const DRAWN = [['Montrer','SabreDroit'],['Montrer','SabreGauche'],['Montrer','SabreBouche'],['Cacher','SabresHanche']];

  const ANIMS = [
    {id:'Sabreur_Idle_Garde', label:'Idle — Garde', loop:true, priority:'Idle', dur:2,
      keys:[K(0,GUARD,'Cubic','InOut'), K(1,BREATH,'Cubic','InOut'), K(2,GUARD)],
      markers:DRAWN.map(m => [0, m[0], m[1]])},
    {id:'Sabreur_M1_1', label:'M1 · 1 — Coupe droite', priority:'Action', dur:0.45,
      keys:[K(0,GUARD), K(0.1,WIND1), K(0.22,STRIKE1,'Cubic','InOut'), K(0.45,GUARD)],
      markers:[[0.2,'Impact','M1_1']]},
    {id:'Sabreur_M1_2', label:'M1 · 2 — Revers gauche', priority:'Action', dur:0.45,
      keys:[K(0,GUARD), K(0.1,WIND2), K(0.22,STRIKE2,'Cubic','InOut'), K(0.45,GUARD)],
      markers:[[0.2,'Impact','M1_2']]},
    {id:'Sabreur_M1_3', label:'M1 · 3 — Double taille', priority:'Action', dur:0.5,
      keys:[K(0,GUARD), K(0.12,WIND3,'Cubic','In'), K(0.25,STRIKE3,'Cubic','InOut'), K(0.5,GUARD)],
      markers:[[0.24,'Impact','M1_3']]},
    {id:'Sabreur_M1_4', label:'M1 · 4 — Vrille + estoc', priority:'Action', dur:0.7,
      keys:[K(0,GUARD,'Linear'), K(0.12,tuck(90),'Linear'), K(0.22,tuck(180),'Linear'), K(0.32,tuck(270),'Cubic'), K(0.42,THRUST,'Linear'), K(0.55,THRUST,'Cubic','InOut'), K(0.7,GUARD)],
      markers:[[0.42,'Impact','M1_4']]},
    {id:'Sabreur_Coupe_X', label:'Coupe croisée en X', priority:'Action', dur:0.9,
      keys:[K(0,GUARD), K(0.18,CROSS,'Cubic','InOut'), K(0.35,CROSS2,'Cubic','In'), K(0.45,XSLASH,'Cubic','InOut'), K(0.65,XHOLD,'Cubic','InOut'), K(0.9,GUARD)],
      markers:[[0.45,'Impact','CoupeX']]},
    {id:'Sabreur_Tornade', label:'Tornade', priority:'Action', dur:1.2,
      keys:[K(0,GUARD), K(0.12,SPREAD,'Linear'),
        K(0.21,spin(-50,-0.1),'Linear'), K(0.3,spin(-140,0.1),'Linear'), K(0.39,spin(130,0.25),'Linear'), K(0.48,spin(40,0.35),'Linear'),
        K(0.57,spin(-50,0.35),'Linear'), K(0.66,spin(-140,0.25),'Linear'), K(0.75,spin(130,0.1),'Linear'), K(0.84,spin(40,-0.2)),
        K(1.0,SPINEND,'Cubic','InOut'), K(1.2,GUARD)],
      markers:[[0.3,'Impact','Tornade'],[0.48,'Impact','Tornade'],[0.66,'Impact','Tornade'],[0.84,'Impact','Tornade']]},
    {id:'Sabreur_Saut_Impact', label:'Saut + impact au sol', priority:'Action', dur:1.4,
      keys:[K(0,GUARD), K(0.15,CROUCH), K(0.4,AIR,'Cubic','Out'), K(0.55,APEX,'Cubic','In'), K(0.72,SLAM,'Cubic','InOut'), K(1.05,RISE,'Cubic','InOut'), K(1.4,GUARD)],
      markers:[[0.72,'Impact','Sol']]},
    {id:'Sabreur_Combat_Esquives', label:'Combat — Esquives + saut', priority:'Action', dur:3.4,
      keys:[K(0,GUARD),
        K(0.16,DODGE_L), K(0.3,at(DBL_WIND_R,-2,-0.5,0)), K(0.4,at(DBL_STRIKE_L,-2,-0.6,-0.3),'Cubic','InOut'),
        K(0.56,at(HOP,0,-0.1,0),'Cubic','InOut'), K(0.72,DODGE_R), K(0.86,at(DBL_WIND_L,2,-0.5,0)), K(0.96,at(DBL_STRIKE_R,2,-0.6,-0.3),'Cubic','InOut'),
        K(1.1,at(DBL_LOW,1,-0.9,0.2)), K(1.2,at(DBL_RISE,1,-0.2,-0.5),'Cubic','InOut'),
        K(1.38,BACKSTEP,'Cubic','InOut'), K(1.48,at(BACKSTEP,0,-0.85,2,12,-20,0)),
        K(1.55,at(CROUCH,0,-1.2,2)), K(1.8,at(AIR,0,5,0.8),'Cubic','Out'), K(1.95,at(APEX,0,5.6,0),'Cubic','In'), K(2.12,SLAM,'Cubic','InOut'),
        K(2.35,at(CROSS2,0,-0.85,-0.8),'Cubic','In'), K(2.48,at(XSLASH,0,-0.9,-1.6),'Cubic','InOut'),
        K(2.8,at(XHOLD,0,-0.85,-1.5),'Cubic','InOut'), K(3.15,GUARD,'Cubic','InOut'), K(3.4,BREATH)],
      markers:[[0.16,'Esquive','Gauche'],[0.4,'Impact','Contre1'],[0.72,'Esquive','Droite'],[0.96,'Impact','Contre2'],[1.2,'Impact','Contre3'],[1.38,'Esquive','Arriere'],[2.12,'Impact','Sol'],[2.48,'Impact','CoupeX']]},
    {id:'Sabreur_Charge_Aura', label:'Charge d\'aura', priority:'Action', dur:3.0,
      keys:[K(0,GUARD,'Cubic','InOut'),
        K(0.28,GATHER,'Cubic','In'), K(0.4,WINGS,'Cubic','Out'), K(0.75,FLOAT_A,'Cubic','InOut'), K(1.3,FLOAT_B,'Cubic','InOut'),
        K(1.85,FLOAT_A,'Cubic','InOut'), K(2.4,FLOAT_B,'Cubic','In'), K(2.75,LAND,'Cubic','Out'), K(3.0,GUARD)],
      markers:[[0.05,'Aura','Debut'],[0.4,'Explosion','Aura'],[2.8,'Fin','Aura']]},
    {id:'Sabreur_Degainage', label:'Dégainage (sabre en bouche)', priority:'Action', dur:1.4,
      keys:[K(0,RELAX,'Cubic','InOut'), K(0.2,REACH1), K(0.35,DRAW1,'Cubic','InOut'), K(0.55,REACH2), K(0.7,DRAW2,'Cubic','InOut'), K(0.92,MOUTH,'Cubic','InOut'), K(1.12,GUARD,'Cubic','InOut'), K(1.4,BREATH)],
      markers:[[0,'Montrer','SabresHanche'],[0,'Cacher','SabreDroit'],[0,'Cacher','SabreGauche'],[0,'Cacher','SabreBouche'],
        [0.22,'Montrer','SabreDroit'],[0.55,'Montrer','SabreGauche'],[0.95,'Montrer','SabreBouche'],[0.95,'Cacher','SabresHanche']]},
    {id:'Sabreur_Ultime_Eveil', label:'Ultime — Éveil', priority:'Action4', dur:3.3,
      keys:[K(0,GUARD), K(0.3,GATHER,'Linear'), K(0.6,GATHER_B,'Linear'), K(0.9,GATHER,'Linear'), K(1.2,GATHER_B,'Cubic','In'),
        K(1.4,BURST,'Cubic','InOut'), K(2.0,BURST2,'Cubic','InOut'), K(2.3,UCROSS,'Cubic','In'), K(2.55,USLASH,'Cubic','InOut'), K(2.9,USLASH,'Cubic','InOut'), K(3.3,GUARD)],
      markers:[[0.3,'Aura','Debut'],[1.4,'Explosion','Eveil'],[2.55,'Impact','Ultime']]}
  ];
  ANIMS.splice(ANIMS.findIndex(a => a.id === 'Sabreur_Degainage') + 1, 0,
    {id:'Sabreur_Rengainage', label:'Rengainage', priority:'Action', dur:1.4,
      keys:[K(0,GUARD,'Cubic','InOut'), K(0.25,MOUTH,'Cubic','InOut'), K(0.45,DRAW2), K(0.65,REACH2,'Cubic','InOut'), K(0.85,DRAW1), K(1.05,REACH1,'Cubic','InOut'), K(1.4,RELAX)],
      markers:[[0.25,'Cacher','SabreBouche'],[0.65,'Cacher','SabreGauche'],[0.65,'Montrer','SabresHanche'],[1.05,'Cacher','SabreDroit']]});
  function chain(id, label, ids) {
    let off = 0; const keys = [], markers = [];
    ids.forEach((src, i) => {
      const a = ANIMS.find(x => x.id === src);
      if (i > 0) keys.pop();
      a.keys.forEach(k => keys.push(Object.assign({}, k, {t: Math.round((k.t + off) * 1000) / 1000})));
      a.markers.forEach(m => markers.push([Math.round((m[0] + off) * 1000) / 1000, m[1], m[2]]));
      off += a.dur;
    });
    return {id, label, priority:'Action', dur: Math.round(off * 1000) / 1000, keys, markers};
  }
  ANIMS.unshift(chain('Sabreur_Sequence_Complete', 'Séquence complète', ['Sabreur_Degainage','Sabreur_Charge_Aura','Sabreur_Combat_Esquives','Sabreur_Rengainage']));
  const KEEP = ['Sabreur_Sequence_Complete','Sabreur_Degainage','Sabreur_Charge_Aura','Sabreur_Combat_Esquives','Sabreur_Rengainage'];
  const kept = KEEP.map(id => ANIMS.find(a => a.id === id));
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
    const v = {SabresHanche:false, SabreDroit:true, SabreGauche:true, SabreBouche:true};
    anim.markers.forEach(m => { if (m[0] <= t + 1e-6 && (m[1] === 'Montrer' || m[1] === 'Cacher')) v[m[2]] = m[1] === 'Montrer'; });
    return v;
  }

  const n = x => String(Math.round(x * 1000) / 1000);
  function toLuau() {
    const L = [];
    L.push('--[[ SABREUR À TROIS SABRES — animations de la séquence complète (R15)');
    L.push('  1. Dans l\'Explorer, sélectionne le Model de ton personnage R15 (avec Humanoid).');
    L.push('  2. Affichage > Barre de commande : colle tout ce script puis Entrée.');
    L.push('  3. Avatar > Éditeur d\'animation > choisis le rig > ⋯ > Charger > Sabreur_…');
    L.push('  4. ⋯ > Publier sur Roblox, puis copie l\'ID d\'animation (rbxassetid://…).');
    L.push('  Marqueurs : Montrer / Cacher (valeur = nom de l\'Accessory), Impact, Aura, Explosion.');
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
-- Affiche / cache les Accessory des sabres selon les marqueurs Montrer / Cacher des animations.
-- Les marqueurs Impact / Aura / Explosion sont exposés via onMarker() pour brancher tes hitbox et VFX.
local Players = game:GetService("Players")

local function setVisible(character, accessoryName, visible)
	local acc = character:FindFirstChild(accessoryName)
	if not acc then return end
	for _, d in ipairs(acc:GetDescendants()) do
		if d:IsA("BasePart") or d:IsA("Decal") then d.Transparency = visible and 0 or 1 end
	end
end

local function onMarker(character, name, value)
	-- ex : if name == "Impact" then ... end
end

local function hook(character)
	local humanoid = character:WaitForChild("Humanoid")
	local animator = humanoid:WaitForChild("Animator")
	animator.AnimationPlayed:Connect(function(track)
		track:GetMarkerReachedSignal("Montrer"):Connect(function(v) setVisible(character, v, true) end)
		track:GetMarkerReachedSignal("Cacher"):Connect(function(v) setVisible(character, v, false) end)
		for _, n in ipairs({"Impact", "Aura", "Explosion"}) do
			track:GetMarkerReachedSignal(n):Connect(function(v) onMarker(character, n, v) end)
		end
	end)
end

local function watch(player)
	if player.Character then task.spawn(hook, player.Character) end
	player.CharacterAdded:Connect(hook)
end
for _, p in ipairs(Players:GetPlayers()) do watch(p) end
Players.PlayerAdded:Connect(watch)
`;

  window.SABRE = {ANIMS, ACCESSORIES, J, PART, sample, visibility, toLuau, RUNTIME};
})();
