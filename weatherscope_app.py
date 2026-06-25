"""
WeatherScope — Premium Edition v3
- OWM: current weather + AQI
- Open-Meteo: 7-day ECMWF forecast + 30-day historical
- Math engine: Fourier decomposition + Holt-Winters + ECMWF blend
Run:  pip install streamlit
      streamlit run weatherscope_v3.py
"""
import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="WeatherScope", page_icon="🌤️", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
#MainMenu, header, footer {visibility:hidden;}
.block-container {padding:0 !important; max-width:100% !important;}
section.main > div {padding:0 !important;}
iframe {border:none !important;}
html, body {margin:0; padding:0; background:#020818;}
</style>
""", unsafe_allow_html=True)

# OpenWeatherMap API key — loaded from Streamlit secrets (on the cloud) or an
# environment variable. NEVER hardcoded here, so it stays out of GitHub.
# For local runs, put it in .streamlit/secrets.toml (which is gitignored).
try:
    OWM_KEY = st.secrets["OWM_KEY"]
except Exception:
    OWM_KEY = os.environ.get("OWM_KEY", "")

HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>WeatherScope</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<script src="https://unpkg.com/three@0.152.2/build/three.min.js"></script>
<style>
*{box-sizing:border-box;scrollbar-width:none}
*::-webkit-scrollbar{display:none}
html,body{margin:0;padding:0;font-family:'Outfit',system-ui,sans-serif;color:#fff;overflow-x:hidden}
body{min-height:100vh;background:#020818;transition:background 1.2s ease}
input::placeholder{color:rgba(255,255,255,.35)}
button{font-family:inherit}

/* INTRO */
#intro-overlay{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:#020818;pointer-events:all}
#intro-canvas{position:absolute;inset:0;width:100%;height:100%}
#intro-text{position:relative;z-index:2;text-align:center;pointer-events:none}
#intro-text h1{font-size:clamp(32px,6vw,72px);font-weight:800;letter-spacing:-.04em;background:linear-gradient(135deg,#60a5fa,#a78bfa,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;opacity:0;transform:translateY(20px);transition:all .6s ease .2s}
#intro-text p{font-size:16px;font-weight:400;color:rgba(255,255,255,.5);margin-top:8px;opacity:0;transition:all .6s ease .4s}
#intro-text.show h1,#intro-text.show p{opacity:1;transform:translateY(0)}
#intro-overlay.burst-out{animation:introOut .7s ease-in .2s both}
@keyframes introOut{0%{opacity:1;transform:scale(1)}60%{opacity:1;transform:scale(1.04)}100%{opacity:0;transform:scale(0.96);pointer-events:none}}

/* KEYFRAMES */
@keyframes wrain{0%{transform:translateY(-30px) rotate(14deg);opacity:0}8%{opacity:1}90%{opacity:.8}100%{transform:translateY(115vh) rotate(14deg);opacity:0}}
@keyframes floatA{0%{transform:translateX(-400px)}100%{transform:translateX(calc(100vw + 400px))}}
@keyframes floatB{0%{transform:translateX(-300px)}100%{transform:translateX(calc(100vw + 300px))}}
@keyframes floatC{0%{transform:translateX(-220px)}100%{transform:translateX(calc(100vw + 220px))}}
@keyframes ambientPulse{0%,100%{opacity:.65}50%{opacity:1}}
@keyframes snowfall{0%{transform:translateY(-20px) rotate(0deg);opacity:0}10%{opacity:.9}90%{opacity:.6}100%{transform:translateY(110vh) rotate(360deg);opacity:0}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes alertPulse{0%,100%{opacity:1}50%{opacity:.6}}
@keyframes slideInRight{from{transform:translateX(60px);opacity:0}to{transform:translateX(0);opacity:1}}
@keyframes lightning{0%,94%,100%{opacity:0}95%,97%{opacity:1}96%,98%{opacity:.3}}
@keyframes predGrow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes confPulse{0%,100%{opacity:.7}50%{opacity:1}}
@keyframes chartDraw{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}

.fade{animation:fadeIn .5s ease both}
.glass{backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);border-radius:24px;transition:all .35s}
.glass.dark{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.10);box-shadow:0 8px 40px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.06)}
.glass.light{background:rgba(255,255,255,.42);border:1px solid rgba(255,255,255,.6);box-shadow:0 8px 40px rgba(0,0,0,.10),inset 0 1px 0 rgba(255,255,255,.6)}
.stat{display:flex;flex-direction:column;align-items:center;gap:4px;padding:14px 8px;border-radius:18px}
.tab{flex:1;padding:9px 0;font-size:12px;font-weight:600;border-radius:16px;text-transform:capitalize;border:none;cursor:pointer;transition:all .28s;letter-spacing:.02em;background:transparent;color:rgba(255,255,255,.5)}
.tab.active{background:rgba(255,255,255,.18);color:#fff;box-shadow:0 2px 16px rgba(0,0,0,.25)}
body.light .tab.active{background:rgba(255,255,255,.78);color:#0d1f40}
.row{display:flex;align-items:center;gap:14px;padding:14px 16px;border-radius:18px;transition:background .25s}
.row:hover{background:rgba(255,255,255,.05)}
body.light .row:hover{background:rgba(255,255,255,.4)}
.spinner{width:20px;height:20px;border:2px solid rgba(255,255,255,.2);border-top-color:#fff;border-radius:50%;animation:spin .9s linear infinite}
.ambient{position:fixed;inset:-20% -10% auto -10%;height:70vh;pointer-events:none;filter:blur(80px);animation:ambientPulse 8s ease-in-out infinite;z-index:0}
.clouds,.rain,.snow{position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:1}
.content{position:relative;z-index:10;max-width:520px;margin:0 auto;padding:24px 18px 60px}
.temp{font-family:'DM Mono',monospace;font-weight:300;font-size:108px;line-height:.95;letter-spacing:-.05em}
.city{font-size:22px;font-weight:600;letter-spacing:-.01em}
.desc{font-size:17px;font-weight:500;text-transform:capitalize;opacity:.9}
.meta{font-size:13px;color:rgba(255,255,255,.55);font-weight:500}
.hi-lo{display:flex;gap:14px;align-items:center;font-size:14px;color:rgba(255,255,255,.7);font-weight:500;margin-top:10px;flex-wrap:wrap}
.hi-lo .chip{display:inline-flex;align-items:center;gap:4px}
.search-wrap{position:relative;flex:1}
.search{display:flex;align-items:center;gap:10px;padding:11px 14px;border-radius:14px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);backdrop-filter:blur(12px)}
body.light .search{background:rgba(255,255,255,.45);border:1px solid rgba(255,255,255,.6)}
.search input{background:transparent;border:none;outline:none;flex:1;font-size:14px;font-weight:500;color:#fff;min-width:0;font-family:inherit}
body.light .search input{color:#0d1f40}
body.light .search input::placeholder{color:rgba(13,31,64,.45)}
.dd{position:absolute;top:calc(100% + 8px);left:0;right:0;border-radius:16px;overflow:hidden;z-index:50;background:rgba(20,28,48,.92);border:1px solid rgba(255,255,255,.12);backdrop-filter:blur(20px);box-shadow:0 20px 60px rgba(0,0,0,.5)}
body.light .dd{background:rgba(255,255,255,.92);border:1px solid rgba(0,0,0,.08);color:#0d1f40}
.dd button{width:100%;text-align:left;padding:12px 16px;font-size:14px;border:none;background:transparent;color:inherit;cursor:pointer;display:flex;align-items:center;gap:10px;border-bottom:1px solid rgba(255,255,255,.06)}
body.light .dd button{border-bottom:1px solid rgba(0,0,0,.06)}
.dd button:last-child{border-bottom:none}
.dd button:hover{background:rgba(255,255,255,.08)}
body.light .dd button:hover{background:rgba(0,0,0,.04)}
.theme-btn{width:44px;height:44px;border-radius:14px;flex-shrink:0;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);backdrop-filter:blur(12px);cursor:pointer;transition:all .35s}
body.light .theme-btn{background:rgba(255,255,255,.45);border:1px solid rgba(255,255,255,.6)}
.err{display:flex;align-items:center;gap:10px;padding:14px 16px;border-radius:16px;background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.35);color:#fca5a5;font-size:14px;margin-top:14px}
.hour-card{min-width:82px;display:flex;flex-direction:column;align-items:center;gap:8px;padding:14px 8px;border-radius:18px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08)}
body.light .hour-card{background:rgba(255,255,255,.5);border:1px solid rgba(255,255,255,.7)}
.hour-row{display:flex;gap:10px;overflow-x:auto;padding:4px}
.bar{height:5px;border-radius:99px;background:rgba(255,255,255,.14);overflow:hidden;position:relative;flex:1}
body.light .bar{background:rgba(13,31,64,.15)}
.bar>span{position:absolute;left:0;top:0;height:100%;border-radius:99px}
.grid-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:18px}
.grid-now{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
#bg3d{position:fixed;inset:0;width:100vw;height:100vh;z-index:0;pointer-events:none;mask-image:radial-gradient(ellipse at center,#000 55%,transparent 95%)}
.tilt{transform-style:preserve-3d;transition:transform .25s ease-out;will-change:transform}
.tilt:hover{box-shadow:0 30px 80px rgba(80,150,255,.25),inset 0 1px 0 rgba(255,255,255,.12)}
.alert-banner{display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:16px;background:rgba(251,146,60,.12);border:1px solid rgba(251,146,60,.4);color:#fed7aa;font-size:13px;font-weight:500;margin-top:14px;animation:slideInRight .5s ease both,alertPulse 3s ease-in-out infinite 1s}
.alert-dot{width:8px;height:8px;border-radius:50%;background:#fb923c;flex-shrink:0;animation:alertPulse 1.5s ease-in-out infinite}
.aqi-bar{height:8px;border-radius:99px;background:linear-gradient(90deg,#22c55e,#eab308,#f97316,#ef4444,#7e22ce);position:relative;overflow:visible;margin:10px 0 4px}
.aqi-needle{position:absolute;top:-3px;width:3px;height:14px;border-radius:99px;background:#fff;box-shadow:0 0 6px rgba(255,255,255,.6);transform:translateX(-50%);transition:left .8s cubic-bezier(.34,1.56,.64,1)}
.precip-chart{display:flex;align-items:flex-end;gap:6px;height:60px;padding:0 4px}
.precip-bar-wrap{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;height:100%}
.precip-bar-inner{width:100%;border-radius:4px 4px 0 0;background:linear-gradient(to top,#3b82f6,#93c5fd);min-height:2px}

/* PREDICTION PANEL */
.pred-card{border-radius:18px;padding:14px 16px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);margin-bottom:8px;animation:fadeIn .4s ease both}
.pred-day-label{font-size:13px;font-weight:700;min-width:72px}
.pred-temp-range{display:flex;align-items:center;gap:8px;flex:1}
.pred-bar-track{flex:1;height:6px;border-radius:99px;background:rgba(255,255,255,.08);position:relative;overflow:visible}
.pred-bar-fill{position:absolute;height:100%;border-radius:99px;transform-origin:left;animation:predGrow .8s cubic-bezier(.34,1.56,.64,1) both}
.pred-ci{position:absolute;top:-2px;height:10px;border-radius:99px;opacity:.3}
.conf-badge{font-size:10px;font-weight:700;padding:2px 7px;border-radius:99px;letter-spacing:.04em}
.pred-method-tag{font-size:9px;color:rgba(255,255,255,.35);font-weight:600;letter-spacing:.06em;text-transform:uppercase}
.chart-container{width:100%;overflow:hidden;border-radius:16px;margin-top:12px}
.chart-svg{width:100%;overflow:visible}
.chart-path{fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}
.chart-area{opacity:.12}
.loading-pred{display:flex;align-items:center;gap:10px;padding:20px;color:rgba(255,255,255,.5);font-size:13px}
#lightning-flash{position:fixed;inset:0;background:rgba(220,200,255,.08);pointer-events:none;z-index:5;animation:lightning 6s ease-in-out infinite}

/* UNIT TOGGLE + ICON BUTTONS */
.icon-btn{width:44px;height:44px;border-radius:14px;flex-shrink:0;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);backdrop-filter:blur(12px);cursor:pointer;transition:all .35s}
body.light .icon-btn{background:rgba(255,255,255,.45);border:1px solid rgba(255,255,255,.6)}
.icon-btn:hover{background:rgba(255,255,255,.18);transform:translateY(-1px)}
.unit-toggle{display:flex;height:44px;border-radius:14px;overflow:hidden;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.10);backdrop-filter:blur(12px);flex-shrink:0}
body.light .unit-toggle{background:rgba(255,255,255,.45);border:1px solid rgba(255,255,255,.6)}
.unit-toggle button{border:none;background:transparent;color:rgba(255,255,255,.5);font-weight:700;font-size:13px;padding:0 13px;cursor:pointer;transition:all .25s;font-family:inherit}
.unit-toggle button.on{background:rgba(255,255,255,.20);color:#fff}
body.light .unit-toggle button{color:rgba(13,31,64,.5)}
body.light .unit-toggle button.on{background:rgba(255,255,255,.8);color:#0d1f40}

/* CITY CHIPS (favorites + recent) */
.chip-row{display:flex;gap:8px;overflow-x:auto;margin-bottom:16px;padding:2px}
.city-chip{display:inline-flex;align-items:center;gap:6px;padding:7px 12px;border-radius:99px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);font-size:12.5px;font-weight:600;color:#fff;cursor:pointer;white-space:nowrap;transition:all .25s;backdrop-filter:blur(10px)}
body.light .city-chip{background:rgba(255,255,255,.5);border:1px solid rgba(255,255,255,.7);color:#0d1f40}
.city-chip:hover{background:rgba(255,255,255,.16);transform:translateY(-1px)}
.city-chip .star{color:#fbbf24}
.fav-star{cursor:pointer;transition:transform .2s}
.fav-star:hover{transform:scale(1.25)}

/* ADVISOR */
.advisor-card{display:flex;gap:12px;align-items:flex-start;padding:14px 16px;border-radius:18px;margin-bottom:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);animation:fadeIn .4s ease both}
body.light .advisor-card{background:rgba(255,255,255,.5);border:1px solid rgba(255,255,255,.7)}
.advisor-emoji{font-size:26px;line-height:1;flex-shrink:0}
.advisor-title{font-size:13px;font-weight:700;margin-bottom:3px}
.advisor-text{font-size:12.5px;color:rgba(255,255,255,.6);line-height:1.5}
body.light .advisor-text{color:rgba(13,31,64,.6)}
.advisor-tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.advisor-tag{font-size:10.5px;font-weight:600;padding:3px 9px;border-radius:99px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12)}

/* COUNTDOWN */
.countdown-wrap{display:flex;align-items:center;gap:10px;margin-top:14px;padding:11px 14px;border-radius:14px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07)}
.countdown-num{font-family:'DM Mono',monospace;font-weight:600;font-size:14px}
.day-progress{flex:1;height:5px;border-radius:99px;background:rgba(255,255,255,.10);overflow:hidden;position:relative}
.day-progress>span{position:absolute;left:0;top:0;height:100%;border-radius:99px;background:linear-gradient(90deg,#fbbf24,#fb923c)}

/* ACCURACY BADGE */
.accuracy-ring{position:relative;width:54px;height:54px;flex-shrink:0}
.accuracy-pill{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;border-radius:99px;font-size:11px;font-weight:700}
.pred-tip{position:fixed;z-index:9000;pointer-events:none;opacity:0;transition:opacity .15s;min-width:150px;padding:11px 13px;border-radius:14px;background:rgba(15,23,42,.94);border:1px solid rgba(255,255,255,.14);box-shadow:0 16px 50px rgba(0,0,0,.55);backdrop-filter:blur(14px);font-size:12px}
body.light .pred-tip{background:rgba(255,255,255,.96);border:1px solid rgba(0,0,0,.08);color:#0d1f40;box-shadow:0 16px 50px rgba(0,0,0,.18)}
.fc-hit:hover{fill:rgba(255,255,255,.05)}

/* HOURLY TEMP LINE CHART */
@keyframes lineDraw{to{stroke-dashoffset:0}}
@keyframes areaFade{to{opacity:1}}
@keyframes dotPop{from{opacity:0;transform:scale(0)}to{opacity:1;transform:scale(1)}}
.hr-line{stroke-dasharray:1;stroke-dashoffset:1;animation:lineDraw 1.3s ease forwards;filter:drop-shadow(0 3px 10px rgba(96,165,250,.45))}
.hr-area{opacity:0;animation:areaFade .8s ease .7s forwards}
.hr-dot{fill:#fff;opacity:0;transform-box:fill-box;transform-origin:center;animation:dotPop .45s cubic-bezier(.34,1.56,.64,1) forwards}
.hr-lbl{font-family:'DM Mono',monospace;font-size:11px;font-weight:600;fill:#fff;opacity:0;animation:areaFade .4s ease forwards}
.hr-x{fill:rgba(255,255,255,.45);font-size:9px}
body.light .hr-lbl,body.light .hr-dot{fill:#0d1f40}
body.light .hr-x{fill:rgba(13,31,64,.5)}
</style>
</head>
<body class="dark">

<!-- INTRO -->
<div id="intro-overlay">
  <canvas id="intro-canvas"></canvas>
  <div id="intro-text">
    <h1>WeatherScope</h1>
    <p>Real-time weather · Mathematical AI forecasting</p>
  </div>
</div>

<canvas id="bg3d"></canvas>
<div class="ambient" id="ambient"></div>
<div class="clouds" id="clouds"></div>
<div class="rain" id="rain"></div>
<div class="snow" id="snow"></div>
<div id="lightning-flash" style="display:none"></div>

<div class="content">
  <div style="display:flex;gap:12px;align-items:center;margin-bottom:20px">
    <div class="search-wrap" id="searchWrap">
      <div class="search">
        <span><i data-lucide="search" style="width:18px;height:18px;opacity:.65"></i></span>
        <input id="q" placeholder="Search any city…" autocomplete="off"/>
        <button id="clearBtn" style="background:none;border:none;cursor:pointer;padding:0;display:none">
          <i data-lucide="x" style="width:16px;height:16px;opacity:.6;color:#fff"></i>
        </button>
      </div>
      <div id="dd" class="dd" style="display:none"></div>
    </div>
    <div class="unit-toggle" id="unitToggle">
      <button data-u="c" class="on">°C</button>
      <button data-u="f">°F</button>
    </div>
    <button class="icon-btn" id="geoBtn" title="Use my location"><i data-lucide="locate-fixed" style="width:18px;height:18px"></i></button>
    <button class="theme-btn" id="themeBtn"><i data-lucide="moon" style="width:18px;height:18px"></i></button>
  </div>
  <div id="chipRow" class="chip-row" style="display:none"></div>
  <div id="errorBox"></div>
  <div id="alertBox"></div>
  <div id="hero"></div>
  <div id="tabsWrap" style="display:none;margin-top:18px">
    <div class="glass dark" style="padding:5px;display:flex;gap:3px;border-radius:20px" id="tabs">
      <button class="tab active" data-v="now">now</button>
      <button class="tab" data-v="hourly">hourly</button>
      <button class="tab" data-v="weekly">weekly</button>
      <button class="tab" data-v="predict">AI predict</button>
      <button class="tab" data-v="details">details</button>
    </div>
  </div>
  <div id="panel" style="margin-top:14px"></div>
  <div id="predTip" class="pred-tip"></div>
</div>

<script>
/* ============================================================
   CLOUD BURST INTRO
============================================================ */
(function(){
  const overlay=document.getElementById('intro-overlay');
  const canvas=document.getElementById('intro-canvas');
  const introText=document.getElementById('intro-text');
  const W=()=>window.innerWidth, H=()=>window.innerHeight;
  const ctx=canvas.getContext('2d');
  canvas.width=W(); canvas.height=H();
  window.addEventListener('resize',()=>{canvas.width=W();canvas.height=H()});
  const CX=()=>W()/2, CY=()=>H()/2;
  const CLOUD_COLOR=[[110,180,255],[130,200,255],[160,220,255],[200,235,255],[255,255,255]];
  const TOTAL=320, parts=[];
  for(let i=0;i<TOTAL;i++){
    const angle=Math.random()*Math.PI*2, r=20+Math.random()*120;
    const cx2=Math.cos(angle)*r*1.6+(Math.random()-.5)*60;
    const cy2=Math.sin(angle)*r*0.7+(Math.random()-.5)*40;
    const col=CLOUD_COLOR[Math.floor(Math.random()*CLOUD_COLOR.length)];
    parts.push({ox:cx2,oy:cy2,x:(Math.random()-.5)*W()*2,y:(Math.random()-.5)*H()*2,tx:cx2,ty:cy2,size:14+Math.random()*28,opacity:0,r:col[0],g:col[1],b:col[2],phase:Math.random()*Math.PI*2});
  }
  let t=0, phase='gather', frameId;
  const GATHER_DUR=90, HOLD_DUR=40, EXPLODE_DUR=50;
  const ease=t=>t<.5?2*t*t:-1+(4-2*t)*t;
  const easeOut=t=>1-Math.pow(1-t,3);
  function tick(){
    frameId=requestAnimationFrame(tick);
    ctx.clearRect(0,0,W(),H());
    t++;
    if(phase==='gather'){
      const ep=ease(Math.min(t/GATHER_DUR,1));
      parts.forEach(p=>{
        const px=p.x+(p.tx-p.x)*ep+CX(), py=p.y+(p.ty-p.y)*ep+CY();
        const sz=p.size*(1+0.08*Math.sin(t*0.12+p.phase));
        p.opacity=ep*0.7;
        const grd=ctx.createRadialGradient(px,py,0,px,py,sz);
        grd.addColorStop(0,`rgba(${p.r},${p.g},${p.b},${p.opacity})`);
        grd.addColorStop(1,`rgba(${p.r},${p.g},${p.b},0)`);
        ctx.beginPath(); ctx.arc(px,py,sz,0,Math.PI*2); ctx.fillStyle=grd; ctx.fill();
      });
      const g2=ctx.createRadialGradient(CX(),CY(),0,CX(),CY(),180*ep);
      g2.addColorStop(0,`rgba(140,200,255,${0.18*ep})`); g2.addColorStop(1,`rgba(80,140,255,0)`);
      ctx.beginPath(); ctx.arc(CX(),CY(),180*ep,0,Math.PI*2); ctx.fillStyle=g2; ctx.fill();
      if(t>=GATHER_DUR){phase='hold';t=0;introText.classList.add('show');}
    } else if(phase==='hold'){
      const pulse=1+0.04*Math.sin(t*0.18);
      parts.forEach(p=>{
        const px=p.tx*pulse+CX(), py=p.ty*pulse+CY();
        const sz=p.size*(1+0.06*Math.sin(t*0.2+p.phase));
        const grd=ctx.createRadialGradient(px,py,0,px,py,sz);
        grd.addColorStop(0,`rgba(${p.r},${p.g},${p.b},0.72)`); grd.addColorStop(1,`rgba(${p.r},${p.g},${p.b},0)`);
        ctx.beginPath(); ctx.arc(px,py,sz,0,Math.PI*2); ctx.fillStyle=grd; ctx.fill();
      });
      if(t>=HOLD_DUR){phase='explode';t=0;}
    } else if(phase==='explode'){
      const ep=easeOut(Math.min(t/EXPLODE_DUR,1));
      ctx.fillStyle=`rgba(200,220,255,${0.55*(1-ep)*Math.max(0,1-ep*3)})`;
      ctx.fillRect(0,0,W(),H());
      parts.forEach(p=>{
        const ba=Math.atan2(p.oy,p.ox), bd=(140+Math.random()*200)*ep;
        const px=p.tx*(1-ep)+Math.cos(ba)*bd+CX(), py=p.ty*(1-ep)+Math.sin(ba)*bd+CY();
        const sz=p.size*(1-ep*0.6), op=(1-ep)*0.8;
        if(op<=0||sz<=0) return;
        const grd=ctx.createRadialGradient(px,py,0,px,py,sz);
        grd.addColorStop(0,`rgba(${p.r},${p.g},${p.b},${op})`); grd.addColorStop(1,`rgba(${p.r},${p.g},${p.b},0)`);
        ctx.beginPath(); ctx.arc(px,py,sz,0,Math.PI*2); ctx.fillStyle=grd; ctx.fill();
      });
      if(ep>=1){cancelAnimationFrame(frameId); overlay.classList.add('burst-out'); setTimeout(()=>{overlay.style.display='none';},900);}
    }
  }
  tick();
})();
</script>

<script>
/* ============================================================
   CONSTANTS & HELPERS
============================================================ */
const OWM_KEY="__OWM_KEY__";
const OWM="https://api.openweathermap.org";
const OM="https://api.open-meteo.com/v1";

const SKY={
  dark:{sunny:"linear-gradient(155deg,#020818 0%,#0a1628 25%,#0d2149 55%,#1a3a6e 80%,#0d1f40 100%)","partly-cloudy":"linear-gradient(155deg,#060c18 0%,#0d1825 30%,#162030 60%,#1e2e40 85%,#111e2e 100%)",cloudy:"linear-gradient(155deg,#080810 0%,#101020 30%,#181828 60%,#202035 85%,#101018 100%)",rainy:"linear-gradient(155deg,#020208 0%,#06041a 25%,#0e0828 55%,#1e0f42 75%,#100828 100%)",stormy:"linear-gradient(155deg,#010103 0%,#040310 25%,#080518 55%,#120a22 80%,#060310 100%)",snowy:"linear-gradient(155deg,#0c1422 0%,#162030 30%,#1e2e40 60%,#263850 85%,#162030 100%)"},
  light:{sunny:"linear-gradient(155deg,#48c6ef 0%,#6f86d6 40%,#89f7fe 75%,#66a6ff 100%)","partly-cloudy":"linear-gradient(155deg,#89c2d9 0%,#a8c8e0 40%,#c0d8ec 75%,#d6e8f4 100%)",cloudy:"linear-gradient(155deg,#7f8c8d 0%,#95a5a6 40%,#aab4b5 75%,#bfc8c9 100%)",rainy:"linear-gradient(155deg,#3d4f5e 0%,#4e6070 40%,#607080 75%,#728090 100%)",stormy:"linear-gradient(155deg,#1a2535 0%,#263040 40%,#323d4e 75%,#3e4a5a 100%)",snowy:"linear-gradient(155deg,#c8d8e8 0%,#d8e4f0 40%,#e4eef8 75%,#f0f6fc 100%)"}
};
const GLOW={sunny:"rgba(251,191,36,.20)","partly-cloudy":"rgba(148,163,184,.16)",cloudy:"rgba(100,116,139,.13)",rainy:"rgba(96,165,250,.22)",stormy:"rgba(167,139,250,.24)",snowy:"rgba(226,232,240,.20)"};
const ICON_CLR={sunny:"#fbbf24","partly-cloudy":"#94a3b8",cloudy:"#64748b",rainy:"#60a5fa",stormy:"#a78bfa",snowy:"#e2e8f0"};
const COND_ICON={sunny:"sun","partly-cloudy":"cloud",cloudy:"cloud",rainy:"cloud-rain",stormy:"cloud-lightning",snowy:"cloud-snow"};

function owmToCond(id){
  if(id>=200&&id<300)return"stormy"; if(id>=300&&id<600)return"rainy";
  if(id>=600&&id<700)return"snowy";  if(id>=700&&id<800)return"cloudy";
  if(id===800)return"sunny";         if(id<=802)return"partly-cloudy";
  return"cloudy";
}
// Open-Meteo WMO codes → condition
function wmoToCond(c){
  if(c===0)return"sunny"; if(c<=2)return"partly-cloudy"; if(c<=3)return"cloudy";
  if(c<=67||c===80||c===81||c===82)return"rainy"; if(c<=77||c>=85)return"snowy";
  if(c>=95)return"stormy"; return"cloudy";
}
const degToDir=d=>["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"][Math.round(d/22.5)%16];
const fmtTime=u=>new Date(u*1000).toLocaleTimeString("en-US",{hour:"numeric",minute:"2-digit",hour12:true});
const fmtHour=u=>new Date(u*1000).toLocaleTimeString("en-US",{hour:"numeric",hour12:true});
const calcDew=(t,rh)=>{const a=17.27,b=237.7,al=(a*t/(b+t))+Math.log(rh/100);return Math.round(b*al/(a-al));};
const uvLabel=n=>n<=2?"Low":n<=5?"Moderate":n<=7?"High":n<=10?"Very High":"Extreme";
const cap=s=>s.charAt(0).toUpperCase()+s.slice(1);
function getMoonPhase(){
  const known=new Date(2000,0,6,18,14,0), cycle=29.530588853;
  const diff=(Date.now()-known.getTime())/(1000*60*60*24);
  const phase=((diff%cycle)+cycle)%cycle;
  const idx=Math.round(phase/(cycle/8))%8;
  return{name:["New Moon","Waxing Crescent","First Quarter","Waxing Gibbous","Full Moon","Waning Gibbous","Last Quarter","Waning Crescent"][idx],emoji:["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][idx],pct:phase/cycle};
}
function calcComfort(temp,humidity,windSpeed,condition){
  let s=100;
  s-=Math.min(Math.abs(temp-21)*2.5,40);
  s-=Math.min(Math.max(0,humidity-65)*0.5,20);
  s-=Math.min(Math.max(0,windSpeed-20)*0.8,20);
  if(condition==="stormy")s-=25; else if(condition==="rainy")s-=15; else if(condition==="snowy")s-=10;
  return Math.max(0,Math.min(100,Math.round(s)));
}
function getAlert(c){
  if(!c)return null;
  if(c.condition==="stormy")return"⚡ Thunderstorm warning — seek shelter indoors";
  if(c.windSpeed>60)return"💨 High wind alert — gusts up to "+c.windSpeed+" km/h";
  if(c.uv>=8)return"☀️ Extreme UV — apply SPF 50+ and limit sun exposure";
  if(c.humidity>90&&c.temp>30)return"🌡️ Heat + humidity alert — risk of heat exhaustion";
  if(c.condition==="snowy"&&c.temp<-5)return"❄️ Extreme cold warning — dress in layers";
  return null;
}

/* Clothing / activity advisor — rule-based on temp/wind/condition/uv */
function getAdvice(c){
  const t=c.temp, out=[];
  // Clothing
  let clothEmoji,clothTitle,clothText;
  if(t>=30){clothEmoji="🩳";clothTitle="Light & breathable";clothText="Shorts, t-shirt, sunglasses. Stay hydrated and seek shade midday.";}
  else if(t>=22){clothEmoji="👕";clothTitle="Summer comfort";clothText="T-shirt and light trousers are perfect. A cap helps in direct sun.";}
  else if(t>=15){clothEmoji="🧥";clothTitle="Light layers";clothText="A long sleeve or light jacket. Easy to adjust as it warms up.";}
  else if(t>=7){clothEmoji="🧥";clothTitle="Bundle up a bit";clothText="Jacket or sweater recommended. Mornings will feel chilly.";}
  else if(t>=0){clothEmoji="🧣";clothTitle="Stay warm";clothText="Coat, scarf and warm layers. Gloves wouldn't hurt.";}
  else{clothEmoji="🧤";clothTitle="Heavy winter gear";clothText="Insulated coat, hat, gloves and scarf. Limit time outdoors.";}

  // Activity verdict
  let actEmoji,actTitle,actText;
  if(c.condition==="stormy"){actEmoji="🏠";actTitle="Stay indoors";actText="Thunderstorms around — not a good time for outdoor plans.";}
  else if(c.condition==="rainy"){actEmoji="☔";actTitle="Grab an umbrella";actText="Rain likely. Indoor activities or waterproof gear advised.";}
  else if(c.condition==="snowy"){actEmoji="⛄";actTitle="Snowy out there";actText="Great for snow fun — wear waterproof boots and drive carefully.";}
  else if(c.windSpeed>35){actEmoji="🌬️";actTitle="Quite windy";actText="Strong winds — secure loose items, cycling may be tough.";}
  else if(c.condition==="sunny"&&t>=18&&t<=30){actEmoji="🌳";actTitle="Perfect for outdoors";actText="Ideal conditions for a walk, run or picnic. Enjoy it!";}
  else{actEmoji="🚶";actTitle="Decent day out";actText="Conditions are fine for most outdoor activities.";}

  // Tags
  const tags=[];
  if(c.uv>=6)tags.push("🧴 SPF "+(c.uv>=8?"50+":"30+"));
  if(c.condition==="rainy"||c.condition==="stormy")tags.push("☂️ Umbrella");
  if(t<=7)tags.push("🧤 Gloves");
  if(c.windSpeed>=25)tags.push("🧥 Windbreaker");
  if(c.humidity>=80)tags.push("💧 Hydrate");
  if(c.condition==="sunny"&&t>=24)tags.push("🕶️ Sunglasses");
  if(c.visibility<3)tags.push("🚗 Drive slow");
  return{clothEmoji,clothTitle,clothText,actEmoji,actTitle,actText,tags};
}

/* Live countdown to next sun event */
function sunCountdown(c){
  const now=Date.now()/1000;
  let label,target;
  if(now<c.sunrise){label="until sunrise";target=c.sunrise;}
  else if(now<c.sunset){label="until sunset";target=c.sunset;}
  else{label="until sunrise";target=c.sunrise+86400;}
  let s=Math.max(0,Math.round(target-now));
  const h=Math.floor(s/3600);s%=3600;const m=Math.floor(s/60);
  const dayLen=c.sunset-c.sunrise, prog=Math.max(0,Math.min(1,(now-c.sunrise)/dayLen));
  return{label,text:`${h}h ${m}m`,prog:now<c.sunrise||now>c.sunset?0:prog,isDay:now>=c.sunrise&&now<c.sunset};
}

function geolocate(){
  if(!navigator.geolocation){state.error="Geolocation not supported by this browser";render();return;}
  state.locating=true; render();
  navigator.geolocation.getCurrentPosition(
    p=>{state.locating=false;loadCity(p.coords.latitude,p.coords.longitude);},
    ()=>{state.locating=false;state.error="Couldn't get your location — please search instead";render();},
    {enableHighAccuracy:false,timeout:9000,maximumAge:600000}
  );
}

/* ============================================================
   STATE
============================================================ */
let state={
  theme:"dark",view:"now",units:"c",
  current:null,hourly:[],daily:[],
  loading:true,error:null,suggs:[],showDD:false,
  aqi:null,locating:false,
  favorites:[],recents:[],
  prediction:null,predLoading:false,predError:null
};

/* ---- persistence (localStorage) ---- */
function loadPrefs(){
  try{
    state.theme=localStorage.getItem("ws_theme")||"dark";
    state.units=localStorage.getItem("ws_units")||"c";
    state.favorites=JSON.parse(localStorage.getItem("ws_favs")||"[]");
    state.recents=JSON.parse(localStorage.getItem("ws_recents")||"[]");
  }catch{}
}
function savePrefs(){
  try{
    localStorage.setItem("ws_theme",state.theme);
    localStorage.setItem("ws_units",state.units);
    localStorage.setItem("ws_favs",JSON.stringify(state.favorites));
    localStorage.setItem("ws_recents",JSON.stringify(state.recents.slice(0,6)));
  }catch{}
}
function cityKey(o){return `${(o.cityName||o.name)},${o.country}`;}
function isFav(o){return o&&state.favorites.some(f=>cityKey(f)===cityKey(o));}
function toggleFav(o){
  if(!o)return;
  const k=cityKey(o), entry={cityName:o.cityName||o.name,country:o.country,lat:o.lat,lon:o.lon};
  if(state.favorites.some(f=>cityKey(f)===k)) state.favorites=state.favorites.filter(f=>cityKey(f)!==k);
  else state.favorites.unshift(entry);
  state.favorites=state.favorites.slice(0,8);
  savePrefs(); render();
}
function pushRecent(o){
  const entry={cityName:o.cityName,country:o.country,lat:o.lat,lon:o.lon},k=cityKey(entry);
  state.recents=state.recents.filter(r=>cityKey(r)!==k);
  state.recents.unshift(entry);
  state.recents=state.recents.slice(0,6);
  savePrefs();
}

/* ---- unit conversion ---- */
function cvT(v){return state.units==="f"?Math.round(v*9/5+32):Math.round(v);}
function cvD(v){return state.units==="f"?Math.round(v*9/5*10)/10:v;} // delta (no +32 offset)
function uSym(){return state.units==="f"?"°F":"°C";}
function uLet(){return state.units==="f"?"F":"C";}

/* ============================================================
   API CALLS
============================================================ */
async function apiGeocode(q){
  const r=await fetch(`${OWM}/geo/1.0/direct?q=${encodeURIComponent(q)}&limit=6&appid=${OWM_KEY}`);
  if(!r.ok)throw new Error("Geocoding failed");
  return r.json();
}
async function apiCurrent(lat,lon){
  const r=await fetch(`${OWM}/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${OWM_KEY}&units=metric`);
  if(!r.ok)throw new Error("Weather unavailable");
  const d=await r.json();
  let uv=0;
  try{const ur=await fetch(`${OWM}/data/2.5/uvi?lat=${lat}&lon=${lon}&appid=${OWM_KEY}`);if(ur.ok){const ud=await ur.json();uv=Math.round(ud.value);}}catch{}
  return{
    cityName:d.name,country:d.sys.country,
    temp:Math.round(d.main.temp),feels:Math.round(d.main.feels_like),
    hi:Math.round(d.main.temp_max),lo:Math.round(d.main.temp_min),
    humidity:d.main.humidity,pressure:d.main.pressure,
    visibility:Math.round((d.visibility||0)/1000),
    windSpeed:Math.round((d.wind?.speed||0)*3.6),windDeg:d.wind?.deg||0,
    dew:calcDew(d.main.temp,d.main.humidity),uv,
    sunrise:d.sys.sunrise,sunset:d.sys.sunset,
    condition:owmToCond(d.weather[0].id),desc:cap(d.weather[0].description),
    lat,lon,comfort:0
  };
}
async function apiAQI(lat,lon){
  try{
    const r=await fetch(`${OWM}/data/2.5/air_pollution?lat=${lat}&lon=${lon}&appid=${OWM_KEY}`);
    if(!r.ok)return null;
    const d=await r.json();
    const aqi=d.list[0]?.main?.aqi;
    const labels=[null,"Good","Fair","Moderate","Poor","Very Poor"];
    const colors=[null,"#22c55e","#84cc16","#eab308","#f97316","#ef4444"];
    return{value:aqi,label:labels[aqi]||"Unknown",color:colors[aqi]||"#888",pct:((aqi-1)/4)*100};
  }catch{return null;}
}

/* Open-Meteo: ECMWF 7-day hourly forecast */
async function apiOMForecast(lat,lon){
  const url=`${OM}/forecast?latitude=${lat}&longitude=${lon}`+
    `&hourly=temperature_2m,precipitation_probability,weathercode,windspeed_10m,relativehumidity_2m`+
    `&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode,windspeed_10m_max`+
    `&forecast_days=7&timezone=auto`;
  const r=await fetch(url);
  if(!r.ok)throw new Error("Open-Meteo forecast failed");
  return r.json();
}

/* Open-Meteo: 30-day historical hourly (for math engine) */
async function apiOMHistory(lat,lon){
  const now=new Date();
  const end=new Date(now); end.setDate(end.getDate()-1);
  const start=new Date(now); start.setDate(start.getDate()-31);
  const fmt=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const url=`https://archive-api.open-meteo.com/v1/archive?latitude=${lat}&longitude=${lon}`+
    `&start_date=${fmt(start)}&end_date=${fmt(end)}`+
    `&hourly=temperature_2m,precipitation,windspeed_10m&timezone=auto`;
  const r=await fetch(url);
  if(!r.ok)throw new Error("History unavailable");
  return r.json();
}

/* ============================================================
   MATHEMATICAL PREDICTION ENGINE
   Steps:
   1. Parse 30d hourly history → daily means
   2. Fourier decomposition: extract dominant freq components
   3. Holt-Winters double exponential smoothing on residuals
   4. ECMWF forecast from Open-Meteo (days 1-7)
   5. Weighted blend: ECMWF + statistical model
   6. Confidence interval = ±(residual std * coverage factor)
============================================================ */
/* Standalone statistical core: Fourier reconstruction + Holt-Winters on residuals.
   Given a daily-mean series Y, forecast the next `horizon` days. Used by both the
   main blend and the self-validation backtest below. */
function statForecastCore(Y, horizon){
  const useN=Math.min(Y.length,60);
  const Yuse=Y.slice(Y.length-useN);
  // DFT
  const spectrum=[];
  for(let k=0;k<useN;k++){
    let re=0,im=0;
    for(let t=0;t<useN;t++){const a=2*Math.PI*k*t/useN;re+=Yuse[t]*Math.cos(a);im-=Yuse[t]*Math.sin(a);}
    spectrum.push({k,re:re/useN,im:im/useN,amp:Math.sqrt(re*re+im*im)/useN});
  }
  const dc=spectrum[0].re;
  const top=[...spectrum.slice(1)].sort((a,b)=>b.amp-a.amp).slice(0,5);
  const recon=t=>{let v=dc;for(const c of top)v+=2*(c.re*Math.cos(2*Math.PI*c.k*t/useN)-c.im*Math.sin(2*Math.PI*c.k*t/useN));return v;};
  const residuals=Yuse.map((y,t)=>y-recon(t));
  // Holt-Winters double exponential on residuals
  const alpha=0.3,beta=0.1;
  let L=residuals[0],B=residuals.length>1?residuals[1]-residuals[0]:0;
  for(let i=1;i<residuals.length;i++){const Ln=alpha*residuals[i]+(1-alpha)*(L+B);B=beta*(Ln-L)+(1-beta)*B;L=Ln;}
  const out=[];
  for(let h=1;h<=horizon;h++)out.push(recon(useN+h-1)+(L+h*B));
  return out;
}

/* Self-validation backtest: hide the last H days, predict them from the rest,
   compare to the real recorded values → genuine MAE-based accuracy (not random). */
function backtestModel(dailyMeans){
  const H=5, Y=dailyMeans.map(d=>d.mean);
  if(Y.length<14)return null;
  const train=Y.slice(0,Y.length-H), actual=Y.slice(Y.length-H);
  const pred=statForecastCore(train,H);
  let absErr=0;
  for(let i=0;i<H;i++)absErr+=Math.abs(pred[i]-actual[i]);
  const mae=absErr/H;
  // Map MAE → accuracy %: 0°→100%, ~6°→~40%. Bounded.
  const accuracy=Math.round(Math.max(35,Math.min(99,100-mae*9)));
  return{mae:Math.round(mae*10)/10,accuracy,samples:H,
    detail:actual.map((a,i)=>({actual:Math.round(a),predicted:Math.round(pred[i])}))};
}

function runMathEngine(histData, ecmwfData){
  // --- Parse historical daily means from hourly ---
  const hTemps=histData.hourly.temperature_2m;
  const hTimes=histData.hourly.time;
  const dayMap=new Map();
  hTemps.forEach((t,i)=>{
    if(t==null)return;
    const day=hTimes[i].slice(0,10);
    if(!dayMap.has(day))dayMap.set(day,[]);
    dayMap.get(day).push(t);
  });
  const dailyMeans=[];
  for(const[d,temps]of dayMap){
    dailyMeans.push({date:d, mean:temps.reduce((a,b)=>a+b,0)/temps.length});
  }
  dailyMeans.sort((a,b)=>a.date.localeCompare(b.date));
  const Y=dailyMeans.map(d=>d.mean); // N-length array of daily mean temps
  const N=Y.length;

  // --- 1. FOURIER DECOMPOSITION ---
  // Compute DFT to find dominant period components (annual + weekly)
  // We'll reconstruct a smooth trend using the top K frequency components
  function dft(signal){
    const n=signal.length, out=[];
    for(let k=0;k<n;k++){
      let re=0,im=0;
      for(let t=0;t<n;t++){
        const angle=2*Math.PI*k*t/n;
        re+=signal[t]*Math.cos(angle);
        im-=signal[t]*Math.sin(angle);
      }
      out.push({k,re:re/n,im:im/n,amp:Math.sqrt(re*re+im*im)/n});
    }
    return out;
  }
  // Only do DFT on first 60 points max (perf), keep top 5 freqs
  const useN=Math.min(N,60);
  const Yuse=Y.slice(N-useN);
  const spectrum=dft(Yuse);
  // Sort by amplitude, keep top 5 (exclude DC component k=0 separately)
  const dc=spectrum[0].re; // mean
  const sorted=[...spectrum.slice(1)].sort((a,b)=>b.amp-a.amp).slice(0,5);

  // Reconstruct signal from top components
  function fourierReconstruct(t, components, mean, totalN){
    let val=mean;
    for(const c of components){
      const angle=2*Math.PI*c.k*t/totalN;
      val+=2*(c.re*Math.cos(angle)-c.im*Math.sin(angle));
    }
    return val;
  }

  // --- 2. COMPUTE RESIDUALS ---
  const reconstructed=Yuse.map((_,t)=>fourierReconstruct(t,sorted,dc,useN));
  const residuals=Yuse.map((y,t)=>y-reconstructed[t]);

  // --- 3. HOLT-WINTERS DOUBLE EXPONENTIAL SMOOTHING ---
  // On the residuals to capture trend
  const alpha=0.3, beta=0.1; // smoothing params
  let L=residuals[0], B=residuals[1]-residuals[0];
  const smoothed=[L];
  for(let i=1;i<residuals.length;i++){
    const Lnew=alpha*residuals[i]+(1-alpha)*(L+B);
    const Bnew=beta*(Lnew-L)+(1-beta)*B;
    L=Lnew; B=Bnew;
    smoothed.push(L);
  }
  // Forecast residuals for next 7 days using Holt-Winters extrapolation
  const hwForecast=[];
  for(let h=1;h<=7;h++) hwForecast.push(L+h*B);

  // --- 4. STATISTICAL FORECAST FOR DAYS 1-7 ---
  const statForecast=hwForecast.map((res,i)=>{
    const t=useN+i;
    return fourierReconstruct(t,sorted,dc,useN)+res;
  });

  // --- 5. ECMWF DATA ---
  const ecmwfHi=ecmwfData.daily.temperature_2m_max;  // [7 days]
  const ecmwfLo=ecmwfData.daily.temperature_2m_min;
  const ecmwfMean=ecmwfHi.map((h,i)=>(h+ecmwfLo[i])/2);
  const ecmwfPrec=ecmwfData.daily.precipitation_probability_max;
  const ecmwfWMO=ecmwfData.daily.weathercode;
  const ecmwfWind=ecmwfData.daily.windspeed_10m_max;
  const ecmwfDates=ecmwfData.daily.time;

  // --- 6. WEIGHTED BLEND ---
  // ECMWF gets higher weight on days 1-3 (more reliable near-term)
  // Statistical model corrects days 4-7
  const ecmwfWeights=[0.92,0.88,0.82,0.72,0.62,0.50,0.40];

  // Residual std for confidence intervals
  const resMean=residuals.reduce((a,b)=>a+b,0)/residuals.length;
  const resStd=Math.sqrt(residuals.map(r=>(r-resMean)**2).reduce((a,b)=>a+b,0)/residuals.length);

  // Trend direction from HW
  const trend=B; // degrees/day

  const predictions=ecmwfDates.map((dateStr,i)=>{
    const w=ecmwfWeights[i];
    const blendedMean=w*ecmwfMean[i]+(1-w)*statForecast[i];
    // Scale hi/lo around blended mean preserving ECMWF range
    const ecmwfRange=ecmwfHi[i]-ecmwfLo[i];
    const blendedHi=blendedMean+ecmwfRange/2;
    const blendedLo=blendedMean-ecmwfRange/2;
    // Confidence: higher ECMWF weight + lower std = higher confidence
    // Coverage factor 1.28 = 80% CI, 1.645 = 90% CI
    const ciHalfWidth=(1+i*0.15)*resStd*1.28*(1-w*0.5);
    const confidence=Math.round(Math.max(55,Math.min(95,95-i*5-(resStd*1.5))));
    const label=i===0?"Today":i===1?"Tomorrow":new Date(dateStr).toLocaleDateString("en-US",{weekday:"short"});
    return{
      date:dateStr, label,
      hi:Math.round(blendedHi), lo:Math.round(blendedLo),
      mean:Math.round(blendedMean),
      ecmwfHi:Math.round(ecmwfHi[i]), ecmwfLo:Math.round(ecmwfLo[i]),
      ciLo:Math.round(blendedMean-ciHalfWidth),
      ciHi:Math.round(blendedMean+ciHalfWidth),
      precip:ecmwfPrec[i],
      cond:wmoToCond(ecmwfWMO[i]),
      wind:Math.round(ecmwfWind[i]),
      confidence,
      ecmwfWeight:Math.round(w*100),
      statWeight:Math.round((1-w)*100),
      trend:trend>0.2?"↑ rising":trend<-0.2?"↓ falling":"→ stable"
    };
  });

  // Chart data: historical means + predictions
  const chartHistory=dailyMeans.slice(-14).map(d=>({date:d.date,temp:Math.round(d.mean)}));
  const backtest=backtestModel(dailyMeans);
  return{predictions, chartHistory, trend:Math.round(trend*10)/10, resStd:Math.round(resStd*10)/10, backtest};
}

/* ============================================================
   LOAD CITY
============================================================ */
async function loadCity(lat,lon){
  state.loading=true; state.error=null; state.aqi=null; state.prediction=null; render();
  try{
    const[cur,omData,aq]=await Promise.all([apiCurrent(lat,lon),apiOMForecast(lat,lon),apiAQI(lat,lon)]);
    cur.comfort=calcComfort(cur.temp,cur.humidity,cur.windSpeed,cur.condition);
    state.current=cur;
    state.animateHero=true;
    pushRecent(cur);
    // Parse Open-Meteo hourly (next 24h)
    state.hourly=omData.hourly.time.slice(0,24).filter((_,i)=>i%3===0).map((_,idx)=>{
      const i=idx*3;
      return{dt:new Date(omData.hourly.time[i]).getTime()/1000,temp:Math.round(omData.hourly.temperature_2m[i]||0),cond:wmoToCond(omData.hourly.weathercode[i]||0),rain:Math.round(omData.hourly.precipitation_probability[i]||0)};
    });
    // 7-day from Open-Meteo
    state.daily=omData.daily.time.map((dateStr,i)=>{
      const today=new Date().toLocaleDateString("en-US");
      const tom=new Date(Date.now()+86400000).toLocaleDateString("en-US");
      const ds=new Date(dateStr).toLocaleDateString("en-US");
      const label=ds===today?"Today":ds===tom?"Tomorrow":new Date(dateStr).toLocaleDateString("en-US",{weekday:"short"});
      return{label,hi:Math.round(omData.daily.temperature_2m_max[i]),lo:Math.round(omData.daily.temperature_2m_min[i]),rain:Math.round(omData.daily.precipitation_probability_max[i]||0),cond:wmoToCond(omData.daily.weathercode[i])};
    });
    state.aqi=aq;
    state._om=omData;              // keep the ECMWF forecast for the prediction engine / retries
    state.loading=false; render();
    loadPrediction(lat,lon);       // run the math model (self-healing: retried from the tab on failure)
  }catch(e){ state.error=e.message||"Failed to load weather"; state.loading=false; render(); }
}

/* Runs the mathematical forecast. Separated from loadCity so the AI-predict tab can
   lazily trigger it and a Retry button can re-run it without reloading the whole city. */
async function loadPrediction(lat,lon){
  if(!state._om){state.predError="Forecast data not ready — reload the city";render();return;}
  state.predLoading=true; state.predError=null; state.prediction=null; render();
  try{
    const histData=await apiOMHistory(lat,lon);
    state.prediction=runMathEngine(histData,state._om);
    if(!state.prediction||!state.prediction.predictions?.length)throw new Error("model produced no output");
  }catch(e){ state.predError="Prediction model error: "+(e.message||e); }
  state.predLoading=false; render();
}

/* ============================================================
   VFX
============================================================ */
function buildClouds(showRain,dark){
  const base=[{a:"floatA",dur:55,del:-8,top:"5%",w:360,op:dark?.07:.27},{a:"floatA",dur:70,del:-32,top:"19%",w:280,op:dark?.05:.21},{a:"floatB",dur:40,del:-14,top:"2%",w:230,op:dark?.09:.33},{a:"floatB",dur:48,del:-24,top:"27%",w:190,op:dark?.07:.26},{a:"floatC",dur:30,del:-7,top:"11%",w:165,op:dark?.11:.37},{a:"floatC",dur:36,del:-20,top:"34%",w:210,op:dark?.08:.30}];
  if(showRain){base.push({a:"floatA",dur:33,del:-3,top:"0%",w:440,op:dark?.15:.44});base.push({a:"floatB",dur:27,del:-15,top:"13%",w:390,op:dark?.12:.40});}
  document.getElementById("clouds").innerHTML=base.map(c=>`<div style="position:absolute;top:${c.top};left:0;animation:${c.a} ${c.dur}s linear ${c.del}s infinite;will-change:transform"><svg width="${c.w}" height="${c.w*0.45}" viewBox="0 0 260 117" xmlns="http://www.w3.org/2000/svg" style="opacity:${c.op}"><ellipse cx="70" cy="75" rx="55" ry="32" fill="white"/><ellipse cx="120" cy="60" rx="60" ry="38" fill="white"/><ellipse cx="170" cy="70" rx="50" ry="30" fill="white"/><ellipse cx="200" cy="80" rx="40" ry="25" fill="white"/></svg></div>`).join("");
}
function buildRain(heavy,dark){
  const n=heavy?130:80,rgb=dark?"147,197,253":"96,140,210";
  let h="";
  for(let i=0;i<n;i++){const l=((i*1.43+9)%100).toFixed(1),dl=((i*0.053)%3.2).toFixed(3),dr=(0.45+(i*0.013)%0.6).toFixed(3),ht=9+(i*7)%20,op=(0.2+(i*0.009)%0.6).toFixed(2);h+=`<span style="position:absolute;left:${l}%;top:-30px;width:1px;height:${ht}px;background:linear-gradient(to bottom,rgba(${rgb},0),rgba(${rgb},${op}));animation:wrain ${dr}s linear ${dl}s infinite"></span>`;}
  document.getElementById("rain").innerHTML=h;
}
function buildSnow(){
  let h="";
  for(let i=0;i<55;i++){const l=((i*1.81+5)%100).toFixed(1),dl=((i*0.087)%4).toFixed(2),dr=(5+(i*0.07)%5).toFixed(2),sz=2+(i%4);h+=`<span style="position:absolute;left:${l}%;top:-20px;width:${sz}px;height:${sz}px;background:rgba(255,255,255,.85);border-radius:50%;animation:snowfall ${dr}s linear ${dl}s infinite"></span>`;}
  document.getElementById("snow").innerHTML=h;
}

/* ============================================================
   RENDER COMPONENTS
============================================================ */
/* Catmull-Rom → cubic-bezier smooth path through points [[x,y],...] */
function smoothPath(pts){
  if(pts.length<2)return pts.length?`M ${pts[0][0]},${pts[0][1]}`:"";
  let d=`M ${pts[0][0]},${pts[0][1]}`;
  for(let i=0;i<pts.length-1;i++){
    const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;
    const c1x=p1[0]+(p2[0]-p0[0])/6,c1y=p1[1]+(p2[1]-p0[1])/6;
    const c2x=p2[0]-(p3[0]-p1[0])/6,c2y=p2[1]-(p3[1]-p1[1])/6;
    d+=` C ${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }
  return d;
}

function statCard(icon,label,val,unit,clr){
  return`<div class="glass ${state.theme}" style="padding:14px 8px"><div class="stat">
    <div style="display:flex;align-items:center;gap:6px"><i data-lucide="${icon}" style="width:14px;height:14px;color:${clr}"></i>
    <span style="font-size:11px;color:rgba(255,255,255,.55);font-weight:600;letter-spacing:.08em;text-transform:uppercase">${label}</span></div>
    <div style="font-size:22px;font-weight:600;font-family:'DM Mono',monospace;margin-top:4px">${val}</div>
    ${unit?`<div style="font-size:11px;color:rgba(255,255,255,.4)">${unit}</div>`:""}
  </div></div>`;
}

function renderHero(){
  const c=state.current;
  if(!c){
    if(state.loading)return`<div class="glass ${state.theme}" style="padding:60px 24px;text-align:center"><div style="display:inline-flex;align-items:center;gap:12px;color:rgba(255,255,255,.7)"><div class="spinner"></div><span>Loading weather…</span></div></div>`;
    return"";
  }
  const ic=COND_ICON[c.condition],clr=ICON_CLR[c.condition];
  const date=new Date().toLocaleDateString("en-GB",{weekday:"long",day:"numeric",month:"long"});
  const moon=getMoonPhase();
  const comfortColor=c.comfort>=70?"#22c55e":c.comfort>=40?"#eab308":"#ef4444";
  return`<div class="glass ${state.theme} fade" style="padding:26px 24px">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:6px;color:rgba(255,255,255,.7)">
          <i data-lucide="map-pin" style="width:14px;height:14px"></i>
          <span class="city">${c.cityName}, ${c.country}</span>
          <i data-lucide="star" id="favStar" class="fav-star" style="width:17px;height:17px;margin-left:2px;color:${isFav(c)?'#fbbf24':'rgba(255,255,255,.35)'};fill:${isFav(c)?'#fbbf24':'none'}" title="${isFav(c)?'Remove favorite':'Add to favorites'}"></i>
        </div>
        <div class="meta" style="margin-top:6px">${date}</div>
        <div class="temp" style="margin-top:18px"><span id="heroTemp">${cvT(c.temp)}</span><span style="font-size:42px;color:rgba(255,255,255,.55);font-weight:300">${uSym()}</span></div>
        <div class="desc" style="margin-top:6px">${c.desc}</div>
        <div class="hi-lo">
          <span class="chip"><i data-lucide="arrow-up" style="width:13px;height:13px;color:#f87171"></i>${cvT(c.hi)}°</span>
          <span class="chip"><i data-lucide="arrow-down" style="width:13px;height:13px;color:#60a5fa"></i>${cvT(c.lo)}°</span>
          <span style="opacity:.7">Feels ${cvT(c.feels)}°</span>
          <span title="${moon.name}">${moon.emoji} ${moon.name}</span>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;gap:8px">
        <div style="width:88px;height:88px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle,${GLOW[c.condition]} 0%,transparent 70%)">
          <i data-lucide="${ic}" style="width:64px;height:64px;color:${clr};filter:drop-shadow(0 4px 14px ${GLOW[c.condition]})"></i>
        </div>
        <div style="text-align:center">
          <div style="font-size:10px;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.06em">Comfort</div>
          <div style="font-size:18px;font-weight:700;color:${comfortColor};font-family:'DM Mono',monospace">${c.comfort}<span style="font-size:11px">%</span></div>
        </div>
      </div>
    </div>
    <div class="grid-stats">
      ${statCard("wind","Wind",c.windSpeed+" km/h",degToDir(c.windDeg),"#60a5fa")}
      ${statCard("droplets","Humidity",c.humidity+"%","Relative","#38bdf8")}
      ${statCard("eye","Visibility",c.visibility+" km","Clear","#a78bfa")}
    </div>
    ${(()=>{const cd=sunCountdown(c);return`<div class="countdown-wrap">
      <i data-lucide="${cd.isDay?'sunset':'sunrise'}" style="width:18px;height:18px;color:${cd.isDay?'#fb923c':'#fbbf24'}"></i>
      <span class="countdown-num" id="cdNum">${cd.text}</span>
      <span style="font-size:11px;color:rgba(255,255,255,.5)" id="cdLabel">${cd.label}</span>
      <div class="day-progress"><span id="cdBar" style="width:${(cd.prog*100).toFixed(1)}%"></span></div>
    </div>`;})()}
  </div>`;
}

function renderPrediction(){
  if(state.predLoading){
    return`<div class="glass ${state.theme}" style="padding:20px">
      <div class="loading-pred"><div class="spinner"></div>
        <div><div style="font-weight:600;font-size:14px">Running prediction model…</div>
        <div style="font-size:12px;color:rgba(255,255,255,.4);margin-top:2px">Fourier decomposition · Holt-Winters · ECMWF blend</div></div>
      </div>
    </div>`;
  }
  if(state.predError)return`<div class="glass ${state.theme}" style="padding:18px;text-align:center">
    <div class="err" style="margin:0 0 14px"><i data-lucide="alert-circle" style="width:16px;height:16px"></i>${state.predError}</div>
    <button id="predRetry" class="city-chip" style="margin:0 auto"><i data-lucide="refresh-cw" style="width:13px;height:13px"></i>Retry prediction</button>
  </div>`;
  if(!state.prediction)return`<div class="glass ${state.theme}" style="padding:20px;text-align:center;color:rgba(255,255,255,.4)">Search a city to run predictions</div>`;

  const{predictions,chartHistory,trend,resStd}=state.prediction;

  // Global temp range for bar scaling
  const allHi=predictions.map(p=>p.ciHi), allLo=predictions.map(p=>p.ciLo);
  const globalMin=Math.min(...allLo)-2, globalMax=Math.max(...allHi)+2;
  const range=globalMax-globalMin||1;

  const confColor=c=>c>=85?"#22c55e":c>=70?"#60a5fa":c>=60?"#eab308":"#f97316";
  const condIc=(cd)=>({sunny:"☀️","partly-cloudy":"⛅",cloudy:"☁️",rainy:"🌧️",stormy:"⛈️",snowy:"❄️"})[cd]||"🌤️";

  // Build forecast cards
  const cards=predictions.map((p,i)=>{
    const loFrac=(p.lo-globalMin)/range;
    const hiFrac=(p.hi-globalMin)/range;
    const ciLoFrac=(p.ciLo-globalMin)/range;
    const ciHiFrac=(p.ciHi-globalMin)/range;
    const barLeft=`${loFrac*100}%`;
    const barWidth=`${(hiFrac-loFrac)*100}%`;
    const ciLeft=`${ciLoFrac*100}%`;
    const ciWidth=`${(ciHiFrac-ciLoFrac)*100}%`;
    const cc=confColor(p.confidence);
    return`<div class="pred-card" style="animation-delay:${i*0.06}s">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
        <div class="pred-day-label">${p.label}</div>
        <span style="font-size:18px">${condIc(p.cond)}</span>
        <div style="flex:1"></div>
        <span class="conf-badge" style="background:${cc}22;color:${cc};border:1px solid ${cc}44">${p.confidence}% conf</span>
        <span class="pred-method-tag">${p.ecmwfWeight}% ECMWF · ${p.statWeight}% stat</span>
      </div>
      <div class="pred-temp-range">
        <span style="font-size:13px;color:rgba(255,255,255,.5);font-family:'DM Mono',monospace;min-width:28px">${cvT(p.lo)}°</span>
        <div class="pred-bar-track">
          <div class="pred-ci" style="left:${ciLeft};width:${ciWidth};background:linear-gradient(90deg,#60a5fa,#a78bfa)"></div>
          <div class="pred-bar-fill" style="left:${barLeft};width:${barWidth};background:linear-gradient(90deg,#60a5fa,#a78bfa);animation-delay:${i*0.1}s"></div>
        </div>
        <span style="font-size:13px;font-weight:700;font-family:'DM Mono',monospace;min-width:28px;text-align:right">${cvT(p.hi)}°</span>
      </div>
      <div style="display:flex;gap:14px;margin-top:8px;font-size:11px;color:rgba(255,255,255,.4)">
        <span>CI: ${cvT(p.ciLo)}°–${cvT(p.ciHi)}°</span>
        <span>💧 ${p.precip}%</span>
        <span>💨 ${p.wind} km/h</span>
        <span style="color:${p.trend.includes('↑')?'#f87171':p.trend.includes('↓')?'#60a5fa':'#94a3b8'}">${p.trend}</span>
      </div>
    </div>`;
  }).join("");

  // ===== PROMINENT "NEXT 7 DAYS" FORECAST CHART (highs + lows + confidence band) =====
  const fcHi=predictions.map(p=>cvT(p.hi)),   fcLo=predictions.map(p=>cvT(p.lo));
  const fcCiHi=predictions.map(p=>cvT(p.ciHi)),fcCiLo=predictions.map(p=>cvT(p.ciLo));
  const FW=480,FH=216,fL=16,fR=16,fTop=52,fBot=44;
  const fMin=Math.min(...fcCiLo)-2,fMax=Math.max(...fcCiHi)+2,fRange=(fMax-fMin)||1;
  const fx=i=>fL+(predictions.length>1?i*(FW-fL-fR)/(predictions.length-1):0);
  const fy=v=>fTop+(1-(v-fMin)/fRange)*(FH-fTop-fBot);
  const hiPts=fcHi.map((v,i)=>[fx(i),fy(v)]), loPts=fcLo.map((v,i)=>[fx(i),fy(v)]);
  const ciHiPts=fcCiHi.map((v,i)=>[fx(i),fy(v)]), ciLoPts=fcCiLo.map((v,i)=>[fx(i),fy(v)]);
  const hiPath=smoothPath(hiPts), loPath=smoothPath(loPts);
  const bandPath=smoothPath(ciHiPts)+" L "+ciLoPts.slice().reverse().map(p=>`${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" L ")+" Z";
  const fcGrid=predictions.map((p,i)=>`<line x1="${fx(i).toFixed(1)}" y1="${fTop-8}" x2="${fx(i).toFixed(1)}" y2="${FH-fBot}" stroke="rgba(255,255,255,.06)" stroke-width="1"/>`).join("");
  const fcEmoji=predictions.map((p,i)=>`<text x="${fx(i).toFixed(1)}" y="${fTop-30}" text-anchor="middle" font-size="17">${condIc(p.cond)}</text>`).join("");
  const fcHiDots=hiPts.map((pt,i)=>`<circle class="hr-dot" cx="${pt[0].toFixed(1)}" cy="${pt[1].toFixed(1)}" r="3.4" style="animation-delay:${(0.7+i*0.09).toFixed(2)}s"/><text class="hr-lbl" x="${pt[0].toFixed(1)}" y="${(pt[1]-9).toFixed(1)}" text-anchor="middle" style="animation-delay:${(0.85+i*0.09).toFixed(2)}s;fill:#fca5a5">${fcHi[i]}°</text>`).join("");
  const fcLoDots=loPts.map((pt,i)=>`<circle class="hr-dot" cx="${pt[0].toFixed(1)}" cy="${pt[1].toFixed(1)}" r="3.4" style="animation-delay:${(0.7+i*0.09).toFixed(2)}s"/><text class="hr-lbl" x="${pt[0].toFixed(1)}" y="${(pt[1]+17).toFixed(1)}" text-anchor="middle" style="animation-delay:${(0.85+i*0.09).toFixed(2)}s;fill:#93c5fd">${fcLo[i]}°</text>`).join("");
  const fcXLbl=predictions.map((p,i)=>`<text class="hr-x" x="${fx(i).toFixed(1)}" y="${FH-16}" text-anchor="middle" style="font-weight:700">${p.label.length>4?p.label.slice(0,3):p.label}</text>${p.precip>=10?`<text class="hr-x" x="${fx(i).toFixed(1)}" y="${FH-4}" text-anchor="middle" style="font-size:8px;fill:#60a5fa">${p.precip}%💧</text>`:""}`).join("");
  const bigChart=`<svg viewBox="0 0 ${FW} ${FH}" style="width:100%;height:220px;overflow:visible">
    <defs>
      <linearGradient id="fcHiG" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#fb923c"/><stop offset="100%" stop-color="#f87171"/></linearGradient>
      <linearGradient id="fcLoG" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#818cf8"/></linearGradient>
      <linearGradient id="fcBandG" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#a78bfa" stop-opacity="0.30"/><stop offset="100%" stop-color="#60a5fa" stop-opacity="0.04"/></linearGradient>
    </defs>
    ${fcGrid}
    <path class="hr-area" d="${bandPath}" fill="url(#fcBandG)"/>
    <path class="hr-line" d="${hiPath}" fill="none" stroke="url(#fcHiG)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/>
    <path class="hr-line" d="${loPath}" fill="none" stroke="url(#fcLoG)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/>
    ${fcEmoji}${fcHiDots}${fcLoDots}${fcXLbl}
    ${predictions.map((p,i)=>{const w=((FW-fL-fR)/(predictions.length-1))||40;return `<rect class="fc-hit" x="${(fx(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${FH}" fill="transparent" style="cursor:pointer" data-d="${encodeURIComponent(JSON.stringify({l:p.label,em:condIc(p.cond),hi:fcHi[i],lo:fcLo[i],cl:fcCiLo[i],ch:fcCiHi[i],pr:p.precip,wd:p.wind,cf:p.confidence,tr:p.trend}))}"/>`;}).join("")}
  </svg>`;

  // SVG line chart: history (14d) + prediction (7d)
  const allPoints=[...chartHistory.map(h=>({temp:h.temp,type:'history'})),...predictions.map(p=>({temp:p.mean,ciLo:p.ciLo,ciHi:p.ciHi,type:'pred'}))];
  const allTemps=allPoints.map(p=>p.temp);
  const chartMin=Math.min(...allTemps,...predictions.map(p=>p.ciLo))-3;
  const chartMax=Math.max(...allTemps,...predictions.map(p=>p.ciHi))+3;
  const chartRange=chartMax-chartMin||1;
  const W=460,H=100,pad=10;
  const xScale=(i)=>pad+i*(W-pad*2)/(allPoints.length-1);
  const yScale=(t)=>H-pad-(t-chartMin)/(chartRange)*(H-pad*2);

  const histPts=chartHistory.map((h,i)=>`${xScale(i)},${yScale(h.temp)}`).join(" ");
  const predPts=predictions.map((p,i)=>`${xScale(chartHistory.length+i)},${yScale(p.mean)}`).join(" ");
  const joinPt=`${xScale(chartHistory.length-1)},${yScale(chartHistory[chartHistory.length-1].temp)}`;

  // CI area path
  const ciTop=predictions.map((p,i)=>`${xScale(chartHistory.length+i)},${yScale(p.ciHi)}`);
  const ciBot=[...predictions].reverse().map((p,i)=>`${xScale(chartHistory.length+predictions.length-1-i)},${yScale(p.ciLo)}`);
  const ciPath=`M ${ciTop.join(" L ")} L ${ciBot.join(" L ")} Z`;

  // Divider x position
  const divX=xScale(chartHistory.length-1);

  const svgChart=`<svg viewBox="0 0 ${W} ${H}" class="chart-svg" style="height:100px">
    <!-- CI band -->
    <path d="${ciPath}" fill="url(#ciGrad)" opacity="0.25"/>
    <!-- History line -->
    <polyline points="${histPts}" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <!-- Prediction line -->
    <polyline points="${joinPt} ${predPts}" fill="none" stroke="url(#predGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4 2"/>
    <!-- Divider -->
    <line x1="${divX}" y1="${pad}" x2="${divX}" y2="${H-pad}" stroke="rgba(255,255,255,.2)" stroke-width="1" stroke-dasharray="3 3"/>
    <!-- Labels -->
    <text x="${divX-4}" y="${H-2}" font-size="8" fill="rgba(255,255,255,.3)" text-anchor="end">14d history</text>
    <text x="${divX+4}" y="${H-2}" font-size="8" fill="rgba(148,163,184,.6)">7d forecast</text>
    <defs>
      <linearGradient id="predGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#60a5fa"/>
        <stop offset="100%" stop-color="#a78bfa"/>
      </linearGradient>
      <linearGradient id="ciGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#a78bfa" stop-opacity="0.6"/>
        <stop offset="100%" stop-color="#60a5fa" stop-opacity="0.1"/>
      </linearGradient>
    </defs>
  </svg>`;

  const bt=state.prediction.backtest;
  const btColor=bt?(bt.accuracy>=80?"#22c55e":bt.accuracy>=65?"#60a5fa":"#eab308"):"#94a3b8";
  const accuracyHTML=bt?`<div class="accuracy-ring" title="Validated by hiding the last ${bt.samples} days and predicting them — mean error ${cvD(bt.mae)}${uLet()}°">
      <svg width="54" height="54" style="transform:rotate(-90deg)">
        <circle cx="27" cy="27" r="22" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="5"/>
        <circle cx="27" cy="27" r="22" fill="none" stroke="${btColor}" stroke-width="5" stroke-linecap="round" stroke-dasharray="${2*Math.PI*22}" stroke-dashoffset="${2*Math.PI*22*(1-bt.accuracy/100)}"/>
      </svg>
      <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1">
        <span style="font-size:14px;font-weight:800;font-family:'DM Mono',monospace;color:${btColor}">${bt.accuracy}</span>
        <span style="font-size:7px;color:rgba(255,255,255,.4);letter-spacing:.05em">ACCURACY</span>
      </div>
    </div>`:"";

  return`<div class="glass ${state.theme} fade" style="padding:18px 16px">
    <!-- Header -->
    <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px">
      <div style="flex:1;min-width:0">
        <div style="font-size:16px;font-weight:700">Mathematical AI Forecast</div>
        <div style="font-size:11px;color:rgba(255,255,255,.4);margin-top:2px">Fourier + Holt-Winters + ECMWF · ±${cvD(resStd)}${uLet()}° σ</div>
        <div style="font-size:11px;font-weight:700;color:${trend>0?"#f87171":trend<0?"#60a5fa":"#94a3b8"};margin-top:6px">${trend>0?"↑":trend<0?"↓":"→"} ${Math.abs(cvD(trend))}${uLet()}°/day trend</div>
      </div>
      ${accuracyHTML}
    </div>
    ${bt?`<div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;padding:9px 12px;border-radius:12px;background:${btColor}14;border:1px solid ${btColor}33">
      <i data-lucide="check-circle-2" style="width:15px;height:15px;color:${btColor}"></i>
      <span style="font-size:11.5px;color:rgba(255,255,255,.7)">Back-tested on the last ${bt.samples} recorded days · mean error <b style="color:${btColor}">±${cvD(bt.mae)}${uLet()}°</b> — this model is validated, not random.</span>
    </div>`:""}
    <!-- BIG "Next 7 days" outlook chart (the centerpiece) -->
    <div style="font-size:14px;font-weight:700;margin:2px 2px 2px;display:flex;align-items:center;gap:6px">📅 Next 7 days — what to expect</div>
    <div style="display:flex;gap:14px;margin:6px 2px 4px;font-size:10px;color:rgba(255,255,255,.5)">
      <span style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:14px;height:3px;background:linear-gradient(90deg,#fb923c,#f87171);border-radius:2px"></span>Daily high</span>
      <span style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:14px;height:3px;background:linear-gradient(90deg,#38bdf8,#818cf8);border-radius:2px"></span>Daily low</span>
      <span style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:14px;height:8px;background:rgba(167,139,250,.25);border-radius:2px"></span>Confidence band</span>
    </div>
    <div class="chart-container">${bigChart}</div>
    <!-- Secondary: trend vs recent history -->
    <div style="font-size:11px;color:rgba(255,255,255,.4);font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin:14px 2px 2px">Trend vs. recent history</div>
    <div class="chart-container" style="margin-top:6px">${svgChart}</div>
    <!-- Model legend -->
    <div style="display:flex;gap:14px;margin:10px 0 14px;font-size:10px;color:rgba(255,255,255,.4)">
      <span style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:16px;height:2px;background:rgba(255,255,255,.35)"></span>Historical</span>
      <span style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:16px;height:2px;background:linear-gradient(90deg,#60a5fa,#a78bfa);border-radius:2px"></span>Prediction</span>
      <span style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:16px;height:8px;background:rgba(167,139,250,.25);border-radius:2px"></span>80% CI band</span>
    </div>
    <!-- Day cards -->
    ${cards}
    <!-- Method note -->
    <div style="margin-top:10px;padding:10px 12px;border-radius:12px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06)">
      <div style="font-size:10px;color:rgba(255,255,255,.3);line-height:1.7">
        <strong style="color:rgba(255,255,255,.5)">How this works:</strong> 30 days of hourly history → DFT extracts dominant frequency components → Holt-Winters smoothing captures short-term trend → blended with ECMWF NWP model (ECMWF weight decreases day 1→7 as uncertainty grows) → 80% confidence intervals from residual standard deviation.
      </div>
    </div>
  </div>`;
}

function renderPanel(){
  const c=state.current; if(!c)return"";
  if(state.view==="now"){
    const adv=getAdvice(c);
    const advisorHTML=`<div class="glass ${state.theme}" style="padding:14px;margin-bottom:12px">
      <div style="font-size:11px;color:rgba(255,255,255,.45);font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:2px 4px 10px">What to wear & do</div>
      <div class="advisor-card">
        <div class="advisor-emoji">${adv.clothEmoji}</div>
        <div><div class="advisor-title">${adv.clothTitle}</div><div class="advisor-text">${adv.clothText}</div></div>
      </div>
      <div class="advisor-card">
        <div class="advisor-emoji">${adv.actEmoji}</div>
        <div><div class="advisor-title">${adv.actTitle}</div><div class="advisor-text">${adv.actText}</div>
          ${adv.tags.length?`<div class="advisor-tags">${adv.tags.map(t=>`<span class="advisor-tag">${t}</span>`).join("")}</div>`:""}
        </div>
      </div>
    </div>`;
    return advisorHTML+`<div class="grid-now">
      ${statCard("thermometer","Feels Like",cvT(c.feels)+"°","Apparent","#fb923c")}
      ${statCard("gauge","Pressure",c.pressure,"hPa","#34d399")}
      ${statCard("droplets","Dew Point",cvT(c.dew)+"°","Comfort","#38bdf8")}
      ${statCard("sun","UV Index",String(c.uv),uvLabel(c.uv),"#fbbf24")}
      ${statCard("sunrise","Sunrise",fmtTime(c.sunrise),"Morning","#fbbf24")}
      ${statCard("sunset","Sunset",fmtTime(c.sunset),"Evening","#fb923c")}
    </div>`;
  }
  if(state.view==="hourly"){
    if(!state.hourly.length)return`<div class="glass ${state.theme}" style="padding:28px;text-align:center;color:rgba(255,255,255,.55)">No hourly data</div>`;
    const maxRain=Math.max(...state.hourly.map(h=>h.rain),1);
    const cards=state.hourly.map((h,i)=>{
      const ic=COND_ICON[h.cond],cl=ICON_CLR[h.cond];
      return`<div class="hour-card">
        <div style="font-size:11px;color:rgba(255,255,255,.6);font-weight:600">${i===0?"Now":fmtHour(h.dt)}</div>
        <i data-lucide="${ic}" style="width:26px;height:26px;color:${cl}"></i>
        <div style="font-size:18px;font-weight:600;font-family:'DM Mono',monospace">${cvT(h.temp)}°</div>
        ${h.rain>5?`<div style="font-size:10px;color:#60a5fa;font-weight:600">${h.rain}%💧</div>`:""}
      </div>`;
    }).join("");
    const precipBars=state.hourly.map((h,i)=>`<div class="precip-bar-wrap">
      <div style="flex:1;display:flex;align-items:flex-end;width:100%"><div class="precip-bar-inner" style="height:${Math.max((h.rain/maxRain)*100,2)}%"></div></div>
      <div style="font-size:9px;color:rgba(255,255,255,.4);font-weight:600">${i===0?"Now":fmtHour(h.dt).replace(" ","")}</div>
    </div>`).join("");
    // --- animated temperature line chart ---
    const HT=state.hourly.map(h=>cvT(h.temp));
    const cW=460,cH=140,padX=24,padTop=26,padBot=34;
    const tMin=Math.min(...HT),tMax=Math.max(...HT),tRange=(tMax-tMin)||1;
    const xAt=i=>padX+(HT.length>1?i*(cW-padX*2)/(HT.length-1):0);
    const yAt=v=>padTop+(1-(v-tMin)/tRange)*(cH-padTop-padBot);
    const pts=HT.map((v,i)=>[xAt(i),yAt(v)]);
    const linePath=smoothPath(pts);
    const areaPath=`${linePath} L ${xAt(HT.length-1).toFixed(1)},${cH-padBot} L ${xAt(0).toFixed(1)},${cH-padBot} Z`;
    const dots=pts.map((p,i)=>`<circle class="hr-dot" cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="3.5" style="animation-delay:${(0.6+i*0.08).toFixed(2)}s"/>
      <text class="hr-lbl" x="${p[0].toFixed(1)}" y="${(p[1]-11).toFixed(1)}" text-anchor="middle" style="animation-delay:${(0.7+i*0.08).toFixed(2)}s">${HT[i]}°</text>`).join("");
    const xLabels=state.hourly.map((h,i)=>`<text class="hr-x" x="${xAt(i).toFixed(1)}" y="${cH-12}" text-anchor="middle">${i===0?"Now":fmtHour(h.dt).replace(" ","")}</text>`).join("");
    const tempChart=`<svg viewBox="0 0 ${cW} ${cH}" style="width:100%;height:148px;overflow:visible">
      <defs>
        <linearGradient id="hrLine" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#38bdf8"/><stop offset="50%" stop-color="#60a5fa"/><stop offset="100%" stop-color="#a78bfa"/></linearGradient>
        <linearGradient id="hrArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#60a5fa" stop-opacity="0.32"/><stop offset="100%" stop-color="#60a5fa" stop-opacity="0"/></linearGradient>
      </defs>
      <path class="hr-area" d="${areaPath}" fill="url(#hrArea)"/>
      <path class="hr-line" d="${linePath}" fill="none" stroke="url(#hrLine)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/>
      ${dots}${xLabels}
    </svg>`;
    return`<div class="glass ${state.theme}" style="padding:14px">
      <div class="hour-row">${cards}</div>
      <div style="margin-top:16px;padding:0 4px">
        <div style="font-size:11px;color:rgba(255,255,255,.4);font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px">Temperature trend · 24h</div>
        ${tempChart}
      </div>
      <div style="margin-top:14px;padding:0 4px">
        <div style="font-size:11px;color:rgba(255,255,255,.4);font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px">Precipitation probability</div>
        <div class="precip-chart">${precipBars}</div>
      </div>
    </div>`;
  }
  if(state.view==="weekly"){
    if(!state.daily.length)return`<div class="glass ${state.theme}" style="padding:28px;text-align:center;color:rgba(255,255,255,.55)">No forecast data</div>`;
    const rows=state.daily.map(d=>{
      const ic=COND_ICON[d.cond],cl=ICON_CLR[d.cond];
      const grad=d.rain>65?"linear-gradient(90deg,#818cf8,#60a5fa)":d.rain>30?"linear-gradient(90deg,#60a5fa,#93c5fd)":"rgba(255,255,255,.45)";
      return`<div class="row">
        <div style="width:72px;font-size:14px;font-weight:600">${d.label}</div>
        <i data-lucide="${ic}" style="width:24px;height:24px;color:${cl};flex-shrink:0"></i>
        <div style="flex:1;display:flex;align-items:center;gap:8px">
          <div class="bar"><span style="width:${Math.max(d.rain,4)}%;background:${grad}"></span></div>
          ${d.rain>=5?`<span style="font-size:11px;color:#60a5fa;font-weight:600;min-width:32px;text-align:right">${d.rain}%</span>`:""}
        </div>
        <div style="display:flex;gap:10px;font-family:'DM Mono',monospace;font-size:14px">
          <span style="color:rgba(255,255,255,.55)">${cvT(d.lo)}°</span>
          <span style="font-weight:600">${cvT(d.hi)}°</span>
        </div>
      </div>`;
    }).join("");
    return`<div class="glass ${state.theme}" style="padding:8px;border-radius:20px">
      <div style="padding:8px 8px 4px;font-size:11px;color:rgba(255,255,255,.35);font-weight:600;letter-spacing:.06em;text-transform:uppercase">Open-Meteo ECMWF · 7-day</div>
      ${rows}
    </div>`;
  }
  if(state.view==="predict"){
    // lazy-load (or self-heal) the prediction if it isn't ready and isn't already running
    if(state.current&&state._om&&!state.prediction&&!state.predLoading&&!state.predError){
      setTimeout(()=>loadPrediction(state.current.lat,state.current.lon),0);
    }
    return renderPrediction();
  }
  if(state.view==="details"){
    const moon=getMoonPhase();
    const aqi=state.aqi;
    const comfortColor=c.comfort>=70?"#22c55e":c.comfort>=40?"#eab308":"#ef4444";
    const now=Date.now()/1000, dayLen=c.sunset-c.sunrise;
    const sunPct=Math.max(0,Math.min(1,(now-c.sunrise)/dayLen));
    const aqiHTML=aqi?`<div style="padding:0 0 8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
        <span style="font-size:11px;color:rgba(255,255,255,.5);font-weight:600;letter-spacing:.08em;text-transform:uppercase">Air Quality Index</span>
        <span style="font-size:13px;font-weight:700;color:${aqi.color}">${aqi.label}</span>
      </div>
      <div class="aqi-bar"><div class="aqi-needle" style="left:${aqi.pct}%"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:10px;color:rgba(255,255,255,.3);margin-top:6px"><span>Good</span><span>Fair</span><span>Moderate</span><span>Poor</span><span>Very Poor</span></div>
    </div>`:`<div style="font-size:13px;color:rgba(255,255,255,.35);padding:8px 0">AQI data unavailable</div>`;
    return`<div class="glass ${state.theme}" style="padding:16px 20px">
      <div style="font-size:13px;color:rgba(255,255,255,.5);font-weight:600;margin-bottom:4px">🌙 Moon Phase</div>
      <div style="font-size:28px">${moon.emoji} <span style="font-size:14px;font-weight:600">${moon.name}</span></div>
      <div style="height:1px;background:rgba(255,255,255,.07);margin:14px 0"></div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px"><i data-lucide="wind" style="width:14px;height:14px;color:#38bdf8"></i><span style="font-size:11px;color:rgba(255,255,255,.5);font-weight:600;letter-spacing:.08em;text-transform:uppercase">Air Quality (OWM)</span></div>
      ${aqiHTML}
      <div style="height:1px;background:rgba(255,255,255,.07);margin:14px 0"></div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px"><i data-lucide="navigation" style="width:14px;height:14px;color:#60a5fa"></i><span style="font-size:11px;color:rgba(255,255,255,.5);font-weight:600;letter-spacing:.08em;text-transform:uppercase">Wind</span></div>
      <div style="display:flex;align-items:center;gap:18px;padding:8px 0">
        <div style="width:80px;height:80px;border-radius:50%;border:2px solid rgba(255,255,255,.15);position:relative;display:flex;align-items:center;justify-content:center;flex-shrink:0">
          <span style="font-size:9px;position:absolute;top:4px;left:50%;transform:translateX(-50%);color:rgba(255,255,255,.5)">N</span>
          <span style="font-size:9px;position:absolute;bottom:4px;left:50%;transform:translateX(-50%);color:rgba(255,255,255,.5)">S</span>
          <span style="font-size:9px;position:absolute;left:4px;top:50%;transform:translateY(-50%);color:rgba(255,255,255,.5)">W</span>
          <span style="font-size:9px;position:absolute;right:4px;top:50%;transform:translateY(-50%);color:rgba(255,255,255,.5)">E</span>
          <div style="position:absolute;width:4px;height:36px;background:linear-gradient(to bottom,#ef4444,rgba(255,255,255,.3));border-radius:99px;top:50%;left:50%;transform:translate(-50%,-100%) rotate(${c.windDeg}deg);transform-origin:bottom center"></div>
          <div style="width:6px;height:6px;border-radius:50%;background:#fff"></div>
        </div>
        <div><div style="font-size:24px;font-weight:700;font-family:'DM Mono',monospace">${c.windSpeed} <span style="font-size:13px;font-weight:400;opacity:.6">km/h</span></div><div style="font-size:13px;color:rgba(255,255,255,.5)">${degToDir(c.windDeg)} wind</div></div>
      </div>
      <div style="height:1px;background:rgba(255,255,255,.07);margin:14px 0"></div>
      <div style="font-size:11px;color:rgba(255,255,255,.5);font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px">Sun position</div>
      <div style="position:relative;height:50px">
        <svg width="100%" height="50" viewBox="0 0 300 50" style="overflow:visible">
          <path d="M 10 45 Q 150 -20 290 45" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="2"/>
          <path d="M 10 45 Q 150 -20 290 45" fill="none" stroke="rgba(251,191,36,.5)" stroke-width="2" stroke-dasharray="320" stroke-dashoffset="${320*(1-sunPct)}"/>
          <circle cx="${10+(280*sunPct)}" cy="${45-Math.sin(sunPct*Math.PI)*65}" r="8" fill="#fbbf24"/>
        </svg>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:rgba(255,255,255,.4);margin-top:2px"><span>↑ ${fmtTime(c.sunrise)}</span><span>↓ ${fmtTime(c.sunset)}</span></div>
      </div>
      <div style="height:1px;background:rgba(255,255,255,.07);margin:14px 0"></div>
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div style="font-size:11px;color:rgba(255,255,255,.5);font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px">Comfort Score</div>
          <div style="font-size:32px;font-weight:800;font-family:'DM Mono',monospace;color:${comfortColor}">${c.comfort}<span style="font-size:14px">%</span></div>
          <div style="font-size:12px;color:rgba(255,255,255,.4)">temp · humidity · wind</div>
        </div>
        <div style="width:72px;height:72px;position:relative">
          <svg width="72" height="72" style="transform:rotate(-90deg)">
            <circle cx="36" cy="36" r="30" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="6"/>
            <circle cx="36" cy="36" r="30" fill="none" stroke="${comfortColor}" stroke-width="6" stroke-dasharray="${2*Math.PI*30}" stroke-dashoffset="${2*Math.PI*30*(1-c.comfort/100)}" stroke-linecap="round"/>
          </svg>
          <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:${comfortColor}">${c.comfort}</div>
        </div>
      </div>
    </div>`;
  }
}

function render(){
  const dark=state.theme==="dark";
  document.body.className=dark?"dark":"light";
  const cond=state.current?.condition??"sunny";
  document.body.style.background=SKY[state.theme][cond];
  document.getElementById("ambient").style.background=`radial-gradient(ellipse at 50% 0%,${GLOW[cond]} 0%,transparent 60%)`;
  buildClouds(cond==="rainy"||cond==="stormy",dark);
  document.getElementById("rain").innerHTML="";
  document.getElementById("snow").innerHTML="";
  if(cond==="rainy"||cond==="stormy")buildRain(cond==="stormy",dark);
  if(cond==="snowy")buildSnow();
  document.getElementById("lightning-flash").style.display=cond==="stormy"?"block":"none";
  (function(){
    const c=state.current; let kind="none",intensity=0;
    if(cond==="stormy"){kind="rain";intensity=1.0;}
    else if(cond==="rainy"){kind="rain";intensity=0.6;}
    else if(cond==="snowy"){kind="snow";intensity=0.8;}
    else if(c&&(c.visibility<4||c.humidity>=92)){kind="fog";intensity=Math.min(1,0.4+(c.humidity-85)/30);}
    else if(cond==="cloudy"){kind="fog";intensity=0.25;}
    window.__wx={kind,intensity,dark,cond};
  })();
  // Only rebuild the theme icon when the theme actually changes — replacing it on every
  // render would cancel the click (Chrome drops a click if the pressed node is removed).
  if(state._renderedTheme!==state.theme){
    document.getElementById("themeBtn").innerHTML=`<i data-lucide="${dark?"moon":"sun"}" style="width:18px;height:18px;color:${dark?"#e2e8f0":"#fbbf24"}"></i>`;
    state._renderedTheme=state.theme;
  }
  // unit toggle active state
  document.querySelectorAll("#unitToggle button").forEach(b=>b.classList.toggle("on",b.dataset.u===state.units));
  // geo button (spinner while locating) — only rebuilt when the locating state flips
  const geoBtn=document.getElementById("geoBtn");
  if(state._renderedLocating!==state.locating){
    geoBtn.innerHTML=state.locating?`<div class="spinner"></div>`:`<i data-lucide="locate-fixed" style="width:18px;height:18px"></i>`;
    state._renderedLocating=state.locating;
  }
  geoBtn.style.pointerEvents=state.locating?"none":"auto";
  // city chips (favorites first, then recents not already favorited)
  const chipRow=document.getElementById("chipRow");
  const favChips=state.favorites.map(f=>({...f,fav:true}));
  const recChips=state.recents.filter(r=>!isFav(r)).map(r=>({...r,fav:false}));
  const chips=[...favChips,...recChips].slice(0,10);
  if(chips.length){
    chipRow.style.display="flex";
    chipRow.innerHTML=chips.map((ch,i)=>`<div class="city-chip" data-lat="${ch.lat}" data-lon="${ch.lon}">${ch.fav?'<i data-lucide="star" class="star" style="width:12px;height:12px;fill:#fbbf24"></i>':'<i data-lucide="clock" style="width:12px;height:12px;opacity:.5"></i>'}${ch.cityName}</div>`).join("");
    chipRow.querySelectorAll(".city-chip").forEach(el=>el.onclick=()=>loadCity(+el.dataset.lat,+el.dataset.lon));
  }else{chipRow.style.display="none";}
  document.getElementById("errorBox").innerHTML=state.error?`<div class="err"><i data-lucide="alert-circle" style="width:16px;height:16px"></i>${state.error}</div>`:"";
  const alertMsg=state.current?getAlert(state.current):null;
  document.getElementById("alertBox").innerHTML=alertMsg?`<div class="alert-banner"><div class="alert-dot"></div><span>${alertMsg}</span></div>`:"";
  document.getElementById("hero").innerHTML=renderHero();
  const favStar=document.getElementById("favStar");
  if(favStar)favStar.onclick=()=>toggleFav(state.current);
  document.getElementById("tabsWrap").style.display=state.current?"block":"none";
  document.querySelectorAll(".tab").forEach(b=>b.classList.toggle("active",b.dataset.v===state.view));
  document.getElementById("panel").innerHTML=state.current?renderPanel():"";
  const pr=document.getElementById("predRetry");
  if(pr)pr.onclick=()=>{if(state.current)loadPrediction(state.current.lat,state.current.lon);};
  // forecast-chart hover tooltip
  const tip=document.getElementById("predTip");
  if(tip){
    document.querySelectorAll(".fc-hit").forEach(r=>{
      r.addEventListener("mousemove",e=>{
        const d=JSON.parse(decodeURIComponent(r.dataset.d)),u=uSym();
        const cc=d.cf>=85?"#22c55e":d.cf>=70?"#60a5fa":d.cf>=60?"#eab308":"#f97316";
        tip.innerHTML=`<div style="display:flex;align-items:center;gap:7px;margin-bottom:7px"><span style="font-size:17px">${d.em}</span><span style="font-weight:700;font-size:13px">${d.l}</span></div>
          <div style="display:flex;gap:12px;font-family:'DM Mono',monospace;margin-bottom:6px"><span style="color:#fca5a5">▲ ${d.hi}°</span><span style="color:#93c5fd">▼ ${d.lo}°</span></div>
          <div style="display:flex;flex-direction:column;gap:3px;font-size:11px;color:rgba(255,255,255,.6)">
            <span>💧 Rain ${d.pr}% · 💨 ${d.wd} km/h</span>
            <span>Range ${d.cl}°–${d.ch}° ${u}</span>
            <span style="color:${cc};font-weight:600">${d.cf}% confidence · ${d.tr}</span>
          </div>`;
        tip.style.opacity="1";
        const pad=14,tw=tip.offsetWidth,th=tip.offsetHeight;
        let x=e.clientX+pad,y=e.clientY+pad;
        if(x+tw>window.innerWidth-8)x=e.clientX-tw-pad;
        if(y+th>window.innerHeight-8)y=e.clientY-th-pad;
        tip.style.left=x+"px"; tip.style.top=y+"px";
      });
      r.addEventListener("mouseleave",()=>{tip.style.opacity="0";});
    });
  }
  const dd=document.getElementById("dd");
  if(state.showDD&&state.suggs.length){
    dd.style.display="block";
    dd.innerHTML=state.suggs.map((g,i)=>`<button data-i="${i}"><i data-lucide="map-pin" style="width:14px;height:14px;opacity:.6"></i><div><div style="font-weight:600">${g.name}${g.state?", "+g.state:""}</div><div style="font-size:11px;opacity:.55">${g.country}</div></div></button>`).join("");
    dd.querySelectorAll("button").forEach(b=>{b.onclick=()=>{const g=state.suggs[+b.dataset.i];document.getElementById("q").value="";document.getElementById("clearBtn").style.display="none";state.suggs=[];state.showDD=false;loadCity(g.lat,g.lon);};});
  }else{dd.style.display="none";}
  if(window.lucide)window.lucide.createIcons();
  // animated count-up of hero temperature (only right after a city loads)
  if(state.animateHero&&state.current){
    state.animateHero=false;
    animateCount(document.getElementById("heroTemp"),cvT(state.current.temp));
  }
}

/* Count up a number element from 0 → target with easing */
function animateCount(el,target){
  if(!el)return;
  const dur=900,start=performance.now(),from=0;
  function step(now){
    const p=Math.min(1,(now-start)/dur),e=1-Math.pow(1-p,3);
    el.textContent=Math.round(from+(target-from)*e);
    if(p<1)requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* Live sun-event countdown — updates the small widget every second without a full re-render */
setInterval(()=>{
  if(!state.current)return;
  const num=document.getElementById("cdNum"); if(!num)return;
  const cd=sunCountdown(state.current);
  num.textContent=cd.text;
  const lbl=document.getElementById("cdLabel"); if(lbl)lbl.textContent=cd.label;
  const bar=document.getElementById("cdBar"); if(bar)bar.style.width=(cd.prog*100).toFixed(1)+"%";
},1000);

/* Wiring */
document.getElementById("themeBtn").onclick=()=>{state.theme=state.theme==="dark"?"light":"dark";savePrefs();render();};
document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>{state.view=b.dataset.v;render();});
document.querySelectorAll("#unitToggle button").forEach(b=>b.onclick=()=>{state.units=b.dataset.u;savePrefs();render();});
document.getElementById("geoBtn").onclick=geolocate;
let debTimer;
const qEl=document.getElementById("q"),clearBtn=document.getElementById("clearBtn");
qEl.addEventListener("input",e=>{
  clearBtn.style.display=e.target.value?"block":"none";
  clearTimeout(debTimer); const v=e.target.value.trim();
  if(v.length<2){state.suggs=[];state.showDD=false;render();return;}
  debTimer=setTimeout(async()=>{try{const res=await apiGeocode(v);state.suggs=res;state.showDD=res.length>0;render();}catch{}},380);
});
clearBtn.onclick=()=>{qEl.value="";clearBtn.style.display="none";state.suggs=[];state.showDD=false;render();};
document.addEventListener("mousedown",e=>{if(state.showDD&&!document.getElementById("searchWrap").contains(e.target)){state.showDD=false;render();}});

loadPrefs();
document.querySelector('#unitToggle button[data-u="'+state.units+'"]')?.classList.add("on");
render();
// open last city if remembered, else Karachi default
if(state.recents.length){const r=state.recents[0];loadCity(r.lat,r.lon);}
else loadCity(24.8607,67.0011);
</script>

<script>
/* ============================================================
   THREE.JS 3D BACKGROUND
============================================================ */
(function(){
  if(!window.THREE)return;
  const canvas=document.getElementById('bg3d');
  const renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(55,1,0.1,1000);
  camera.position.z=7;
  function resize(){const w=window.innerWidth,h=window.innerHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
  resize(); window.addEventListener('resize',resize);
  scene.add(new THREE.AmbientLight(0x6fa8ff,0.55));
  const key=new THREE.PointLight(0x88c0ff,2.2,50); key.position.set(6,5,6); scene.add(key);
  const rim=new THREE.PointLight(0xff7ad9,1.4,40); rim.position.set(-7,-3,4); scene.add(rim);
  // Stars
  const starGeo=new THREE.BufferGeometry();
  const N=1400,pos=new Float32Array(N*3),col=new Float32Array(N*3);
  const c1=new THREE.Color('#9ec5ff'),c2=new THREE.Color('#ffd2f2');
  for(let i=0;i<N;i++){const r=30+Math.random()*60,t2=Math.random()*Math.PI*2,p=Math.acos(2*Math.random()-1);pos[i*3]=r*Math.sin(p)*Math.cos(t2);pos[i*3+1]=r*Math.sin(p)*Math.sin(t2);pos[i*3+2]=r*Math.cos(p);const m=c1.clone().lerp(c2,Math.random());col[i*3]=m.r;col[i*3+1]=m.g;col[i*3+2]=m.b;}
  starGeo.setAttribute('position',new THREE.BufferAttribute(pos,3));
  starGeo.setAttribute('color',new THREE.BufferAttribute(col,3));
  const stars=new THREE.Points(starGeo,new THREE.PointsMaterial({size:.12,vertexColors:true,transparent:true,opacity:.9,depthWrite:false,blending:THREE.AdditiveBlending}));
  scene.add(stars);
  // Globe
  const globe=new THREE.Group();
  const sphere=new THREE.Mesh(new THREE.IcosahedronGeometry(2.1,3),new THREE.MeshStandardMaterial({color:0x0b1a3a,metalness:.6,roughness:.25,emissive:0x0a2a66,emissiveIntensity:.4,transparent:true,opacity:.55}));
  const wire=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(2.12,3)),new THREE.LineBasicMaterial({color:0x6ad0ff,transparent:true,opacity:.55}));
  const halo=new THREE.Mesh(new THREE.SphereGeometry(2.55,48,48),new THREE.MeshBasicMaterial({color:0x4aa6ff,transparent:true,opacity:.07,side:THREE.BackSide,blending:THREE.AdditiveBlending}));
  globe.add(sphere);globe.add(wire);globe.add(halo);
  globe.position.set(-4.2,1.2,0); scene.add(globe);
  // Orbs
  const orbs=[];
  const palette=[0x6ad0ff,0xff7ad9,0xffd66a,0x7affc1,0xa18bff];
  for(let i=0;i<7;i++){const g=new THREE.IcosahedronGeometry(.35+Math.random()*.5,0);const m=new THREE.MeshStandardMaterial({color:palette[i%palette.length],metalness:.7,roughness:.15,emissive:palette[i%palette.length],emissiveIntensity:.6,flatShading:true,transparent:true,opacity:.85});const o=new THREE.Mesh(g,m);o.position.set((Math.random()-.5)*10,(Math.random()-.5)*6,(Math.random()-.5)*4-1);o.userData={sx:(Math.random()-.5)*.01,sy:(Math.random()-.5)*.01,fx:Math.random()*Math.PI*2,fy:Math.random()*Math.PI*2,base:o.position.clone()};scene.add(o);orbs.push(o);}
  // Condition models
  const lightningGroup=new THREE.Group();
  function makeLightning(){lightningGroup.clear();const mat=new THREE.MeshBasicMaterial({color:0xc4b5fd,transparent:true,opacity:.9,blending:THREE.AdditiveBlending});const pts=[];let y=3.5;for(let i=0;i<=8;i++){pts.push(new THREE.Vector3((i%2===0?-.15:.15)+(Math.random()-.5)*.3,y,0));y-=.8+Math.random()*.3;}const curve=new THREE.CatmullRomCurve3(pts);lightningGroup.add(new THREE.Mesh(new THREE.TubeGeometry(curve,20,.04,5,false),mat));lightningGroup.add(new THREE.Mesh(new THREE.TubeGeometry(curve,20,.15,5,false),new THREE.MeshBasicMaterial({color:0xa78bfa,transparent:true,opacity:.25,blending:THREE.AdditiveBlending})));}
  makeLightning(); lightningGroup.position.set(3.5,1.5,-2); lightningGroup.visible=false; scene.add(lightningGroup);
  const snowCrystalGroup=new THREE.Group();
  const scMat=new THREE.MeshStandardMaterial({color:0xe2e8f0,metalness:.3,roughness:.1,emissive:0xb8d4f0,emissiveIntensity:.5,transparent:true,opacity:.8});
  for(let i=0;i<6;i++){const arm=new THREE.Mesh(new THREE.CylinderGeometry(.04,.04,1.8,6),scMat);arm.rotation.z=i*(Math.PI/3);snowCrystalGroup.add(arm);}
  snowCrystalGroup.add(new THREE.Mesh(new THREE.IcosahedronGeometry(.18,0),scMat));
  snowCrystalGroup.position.set(3.8,.5,-1.5); snowCrystalGroup.visible=false; scene.add(snowCrystalGroup);
  const sunGroup=new THREE.Group();
  const sunMat=new THREE.MeshStandardMaterial({color:0xfbbf24,emissive:0xfbbf24,emissiveIntensity:1.5,transparent:true,opacity:.9});
  sunGroup.add(new THREE.Mesh(new THREE.SphereGeometry(.55,32,32),sunMat));
  for(let i=0;i<3;i++)sunGroup.add(new THREE.Mesh(new THREE.SphereGeometry(.7+i*.28,32,32),new THREE.MeshBasicMaterial({color:0xfde68a,transparent:true,opacity:.12,blending:THREE.AdditiveBlending})));
  for(let i=0;i<8;i++){const ray=new THREE.Mesh(new THREE.CylinderGeometry(.018,.005,1.1,4),new THREE.MeshBasicMaterial({color:0xfbbf24,transparent:true,opacity:.6,blending:THREE.AdditiveBlending}));ray.rotation.z=i*(Math.PI/4);ray.position.set(Math.cos(i*Math.PI/4)*.85,Math.sin(i*Math.PI/4)*.85,0);sunGroup.add(ray);}
  sunGroup.position.set(3.5,1.8,-1.8); sunGroup.visible=false; scene.add(sunGroup);
  const cloud3DGroup=new THREE.Group();
  function makeCloud3D(color,opacity){cloud3DGroup.clear();const mat=new THREE.MeshStandardMaterial({color,roughness:.9,transparent:true,opacity});[{x:0,y:0,z:0,r:.55},{x:.55,y:.18,z:0,r:.45},{x:-.5,y:.1,z:0,r:.4},{x:.25,y:-.1,z:.15,r:.38},{x:-.2,y:-.1,z:.15,r:.35}].forEach(p=>{const m=new THREE.Mesh(new THREE.SphereGeometry(p.r,12,10),mat);m.position.set(p.x,p.y,p.z);cloud3DGroup.add(m);});}
  makeCloud3D(0xffffff,.42); cloud3DGroup.position.set(3.2,.8,-2); cloud3DGroup.visible=false; scene.add(cloud3DGroup);
  // Weather particles
  const WX={x:24,y:18,z:14};
  const RAIN_MAX=1800,rainPos=new Float32Array(RAIN_MAX*6),rainSpeed=new Float32Array(RAIN_MAX);
  for(let i=0;i<RAIN_MAX;i++){const x=(Math.random()-.5)*WX.x,y=(Math.random()-.5)*WX.y,z=(Math.random()-.5)*WX.z,len=.5+Math.random()*.7;rainPos[i*6]=x;rainPos[i*6+1]=y+len;rainPos[i*6+2]=z;rainPos[i*6+3]=x;rainPos[i*6+4]=y;rainPos[i*6+5]=z;rainSpeed[i]=.35+Math.random()*.5;}
  const rainGeo=new THREE.BufferGeometry(); rainGeo.setAttribute('position',new THREE.BufferAttribute(rainPos,3));
  const rainMat=new THREE.LineBasicMaterial({color:0x9ec8ff,transparent:true,opacity:.55,blending:THREE.AdditiveBlending,depthWrite:false});
  const rain3d=new THREE.LineSegments(rainGeo,rainMat); rain3d.visible=false; scene.add(rain3d);
  const SNOW_MAX=1200,snowPos=new Float32Array(SNOW_MAX*3),snowDrift=new Float32Array(SNOW_MAX*3);
  for(let i=0;i<SNOW_MAX;i++){snowPos[i*3]=(Math.random()-.5)*WX.x;snowPos[i*3+1]=(Math.random()-.5)*WX.y;snowPos[i*3+2]=(Math.random()-.5)*WX.z;snowDrift[i*3]=(Math.random()-.5)*.4;snowDrift[i*3+1]=.06+Math.random()*.10;snowDrift[i*3+2]=Math.random()*Math.PI*2;}
  function makeFlake(){const s=64,c=document.createElement('canvas');c.width=c.height=s;const g=c.getContext('2d'),grd=g.createRadialGradient(s/2,s/2,0,s/2,s/2,s/2);grd.addColorStop(0,'rgba(255,255,255,1)');grd.addColorStop(.35,'rgba(220,235,255,.7)');grd.addColorStop(1,'rgba(255,255,255,0)');g.fillStyle=grd;g.fillRect(0,0,s,s);return new THREE.CanvasTexture(c);}
  const snowGeo=new THREE.BufferGeometry(); snowGeo.setAttribute('position',new THREE.BufferAttribute(snowPos,3));
  const snow3d=new THREE.Points(snowGeo,new THREE.PointsMaterial({size:.28,map:makeFlake(),transparent:true,opacity:.95,depthWrite:false,blending:THREE.AdditiveBlending}));
  snow3d.visible=false; scene.add(snow3d);
  function makeFogTex(){const s=128,c=document.createElement('canvas');c.width=c.height=s;const g=c.getContext('2d'),grd=g.createRadialGradient(s/2,s/2,0,s/2,s/2,s/2);grd.addColorStop(0,'rgba(200,215,235,.55)');grd.addColorStop(.5,'rgba(180,200,225,.18)');grd.addColorStop(1,'rgba(180,200,225,0)');g.fillStyle=grd;g.fillRect(0,0,s,s);return new THREE.CanvasTexture(c);}
  const fogGroup=new THREE.Group(); const fogPuffs=[];
  for(let i=0;i<28;i++){const m=new THREE.SpriteMaterial({map:makeFogTex(),transparent:true,opacity:.18,depthWrite:false,blending:THREE.NormalBlending,color:0xb8c8dc});const s=new THREE.Sprite(m);const sc=5+Math.random()*7;s.scale.set(sc,sc,1);s.position.set((Math.random()-.5)*WX.x*1.2,(Math.random()-.5)*WX.y*.7,(Math.random()-.5)*WX.z-1);s.userData={sx:.003+Math.random()*.006,base:s.position.clone(),ph:Math.random()*Math.PI*2};fogGroup.add(s);fogPuffs.push(s);}
  fogGroup.visible=false; scene.add(fogGroup);
  function applyWX(){
    const wx=window.__wx||{kind:'none',intensity:0,cond:'sunny'};
    const cond=wx.cond||'sunny';
    rain3d.visible=wx.kind==='rain'; snow3d.visible=wx.kind==='snow'; fogGroup.visible=wx.kind==='fog';
    lightningGroup.visible=cond==='stormy'; snowCrystalGroup.visible=cond==='snowy';
    sunGroup.visible=cond==='sunny'; cloud3DGroup.visible=cond==='cloudy'||cond==='partly-cloudy'||cond==='rainy';
    if(cond==='rainy')makeCloud3D(0x8090a8,.5); else if(cond==='partly-cloudy')makeCloud3D(0xe8f0ff,.38); else makeCloud3D(0xffffff,.42);
    if(rain3d.visible){rainGeo.setDrawRange(0,Math.floor(RAIN_MAX*wx.intensity)*2);rainMat.opacity=.35+wx.intensity*.45;}
    if(snow3d.visible){snowGeo.setDrawRange(0,Math.floor(SNOW_MAX*wx.intensity));}
    if(fogGroup.visible){fogPuffs.forEach(p=>p.material.opacity=.10+wx.intensity*.28);}
  }
  applyWX(); setInterval(applyWX,600);
  const clock=new THREE.Clock();
  const mouse={x:0,y:0,tx:0,ty:0};
  window.addEventListener('mousemove',e=>{mouse.tx=(e.clientX/window.innerWidth-.5);mouse.ty=(e.clientY/window.innerHeight-.5);});
  function tick(){
    requestAnimationFrame(tick);
    const t=clock.getElapsedTime();
    const wx=window.__wx||{kind:'none',intensity:0};
    if(rain3d.visible){const p=rainGeo.attributes.position.array;const wX=.05+wx.intensity*.18;for(let i=0;i<RAIN_MAX;i++){const v=rainSpeed[i]*(.6+wx.intensity*.8),idx=i*6;p[idx+1]-=v;p[idx+4]-=v;p[idx]+=wX*.3;p[idx+3]+=wX*.3;if(p[idx+4]<-WX.y/2){const x=(Math.random()-.5)*WX.x,z=(Math.random()-.5)*WX.z,y=WX.y/2+Math.random()*2,len=.5+Math.random()*.7;p[idx]=x;p[idx+1]=y+len;p[idx+2]=z;p[idx+3]=x;p[idx+4]=y;p[idx+5]=z;}}rainGeo.attributes.position.needsUpdate=true;}
    if(snow3d.visible){const p=snowGeo.attributes.position.array;for(let i=0;i<SNOW_MAX;i++){const idx=i*3;p[idx]+=Math.sin(t*.6+snowDrift[i*3+2])*.01*(1+snowDrift[i*3]);p[idx+1]-=snowDrift[i*3+1];if(p[idx+1]<-WX.y/2){p[idx]=(Math.random()-.5)*WX.x;p[idx+1]=WX.y/2+Math.random()*2;p[idx+2]=(Math.random()-.5)*WX.z;}}snowGeo.attributes.position.needsUpdate=true;}
    if(fogGroup.visible){fogPuffs.forEach(s=>{s.position.x=s.userData.base.x+Math.sin(t*s.userData.sx+s.userData.ph)*2.2;s.position.y=s.userData.base.y+Math.cos(t*s.userData.sx*.7+s.userData.ph)*.8;s.material.rotation=Math.sin(t*.05+s.userData.ph)*.3;});}
    stars.rotation.y+=.0006; stars.rotation.x+=.0002;
    globe.rotation.y+=.0035; globe.rotation.x=Math.sin(t*.3)*.15;
    halo.material.opacity=.06+Math.sin(t*1.2)*.025;
    orbs.forEach(o=>{o.rotation.x+=o.userData.sx;o.rotation.y+=o.userData.sy;o.position.y=o.userData.base.y+Math.sin(t*.8+o.userData.fy)*.4;o.position.x=o.userData.base.x+Math.cos(t*.5+o.userData.fx)*.3;});
    if(lightningGroup.visible){lightningGroup.rotation.y=Math.sin(t*2.5)*.15;if(Math.random()<.015)makeLightning();}
    if(snowCrystalGroup.visible){snowCrystalGroup.rotation.z+=.004;snowCrystalGroup.rotation.y+=.003;snowCrystalGroup.position.y=.5+Math.sin(t*.7)*.2;}
    if(sunGroup.visible)sunGroup.rotation.z+=.008;
    if(cloud3DGroup.visible){cloud3DGroup.position.y=.8+Math.sin(t*.5)*.15;cloud3DGroup.rotation.y+=.002;}
    mouse.x+=(mouse.tx-mouse.x)*.05; mouse.y+=(mouse.ty-mouse.y)*.05;
    camera.position.x=mouse.x*1.2; camera.position.y=-mouse.y*.8; camera.lookAt(0,0,0);
    renderer.render(scene,camera);
  }
  tick();
  function bindTilt(){document.querySelectorAll('.glass').forEach(el=>{if(el.__tilt)return;el.__tilt=true;el.classList.add('tilt');el.addEventListener('mousemove',e=>{const r=el.getBoundingClientRect(),px=(e.clientX-r.left)/r.width-.5,py=(e.clientY-r.top)/r.height-.5;el.style.transform=`perspective(900px) rotateX(${-py*6}deg) rotateY(${px*8}deg) translateZ(0)`;});el.addEventListener('mouseleave',()=>{el.style.transform='';});});}
  bindTilt(); new MutationObserver(bindTilt).observe(document.body,{childList:true,subtree:true});
})();
</script>
</body>
</html>
"""

components.html(HTML.replace("__OWM_KEY__", OWM_KEY), height=1400, scrolling=True)