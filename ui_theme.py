# -*- coding: utf-8 -*-
"""
文件名：ui_theme.py
作用：共享设计系统（阿尔卑斯·磨玻璃皮肤）。deploy 与 agent 两个前端共用同一套 CSS，
      保证视觉皮肤完全一致；任何皮肤改动只改这一处即可同步。
来源：从 app_ui_deploy.py 的 GLOBAL_CSS 原样抽取。
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root{
  /* 色彩 */
  --c-deep:#0a3a86; --c-primary:#2b7fff; --c-primary-2:#1466e6; --c-cyan:#46c4ff;
  --c-ink:#0f2742; --c-text:#3a566f; --c-muted:#7690a8;
  --c-line:rgba(20,80,160,.12); --c-line-soft:rgba(20,80,160,.07);
  --c-glass:rgba(255,255,255,.62); --c-glass-strong:rgba(255,255,255,.82);
  --grad:linear-gradient(120deg,var(--c-primary) 0%, var(--c-cyan) 100%);
  --grad-deep:linear-gradient(125deg,#0a3a86 0%, #2b7fff 55%, #46c4ff 100%);
  /* 圆角 */
  --r-sm:12px; --r-md:18px; --r-lg:26px; --r-xl:34px;
  /* 阴影 */
  --sh-sm:0 4px 14px rgba(20,80,160,.08);
  --sh-md:0 14px 40px rgba(20,80,160,.14);
  --sh-lg:0 30px 70px rgba(11,61,145,.20);
}

/* 隐藏 streamlit 默认装饰 */
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
[data-testid="stToolbar"]{display:none;}
[data-testid="stDecoration"]{display:none;}
[data-testid="stHeader"]{background:transparent; height:0;}

/* 背景：清爽雪原 + 冷光晕 */
.stApp{
  color:var(--c-text);
  font-family:'Inter','PingFang SC','Microsoft YaHei',sans-serif;
  background:
    radial-gradient(900px 480px at 85% -6%, rgba(70,196,255,.28) 0%, rgba(70,196,255,0) 60%),
    radial-gradient(820px 460px at 8% 2%, rgba(43,127,255,.18) 0%, rgba(43,127,255,0) 58%),
    linear-gradient(180deg,#eef6ff 0%, #f6fbff 40%, #ffffff 100%);
}
.stApp::before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:0; opacity:.45;
  background-image:
    radial-gradient(2px 2px at 18% 28%, #fff 50%, transparent 51%),
    radial-gradient(2px 2px at 72% 16%, #fff 50%, transparent 51%),
    radial-gradient(1.5px 1.5px at 42% 62%, #d6ecff 50%, transparent 51%),
    radial-gradient(1.5px 1.5px at 88% 72%, #fff 50%, transparent 51%);
  background-size:620px 620px,520px 520px,420px 420px,460px 460px;
}
.block-container{max-width:1140px; padding-top:1.2rem; padding-bottom:2rem; position:relative; z-index:1;}

/* ---------- 排版 ---------- */
.overline{font-size:.78rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:var(--c-primary-2);}
h1,h2,h3{color:var(--c-ink); letter-spacing:-.3px;}

/* ====================================================== */
/* Hero                                                    */
/* ====================================================== */
.hero{padding:46px 0 18px;}
.hero-grid{display:grid; grid-template-columns:1.08fr .92fr; gap:46px; align-items:center;}
.hero .overline{margin-bottom:14px;}
.hero h1{font-size:3.1rem; line-height:1.08; font-weight:900; margin:0 0 16px; letter-spacing:-1.2px;}
.hero h1 .grad{background:var(--grad); -webkit-background-clip:text; background-clip:text; color:transparent;}
.hero .lead{font-size:1.14rem; line-height:1.6; color:var(--c-text); margin:0 0 26px; max-width:520px;}
.hero-cta{display:flex; gap:12px; flex-wrap:wrap; margin-bottom:30px;}
.cta{display:inline-flex; align-items:center; gap:8px; text-decoration:none; font-weight:700; font-size:.98rem;
  padding:13px 26px; border-radius:999px; transition:all .2s ease;}
.cta.primary{background:var(--grad); color:#fff; box-shadow:0 12px 26px rgba(43,127,255,.34);}
.cta.primary:hover{transform:translateY(-2px); box-shadow:0 18px 34px rgba(43,127,255,.46);}
.cta.ghost{background:rgba(255,255,255,.7); color:var(--c-primary-2); border:1px solid var(--c-line); backdrop-filter:blur(6px);}
.cta.ghost:hover{transform:translateY(-2px); box-shadow:var(--sh-sm);}
.hero-stats{display:flex; gap:34px;}
.hero-stats .num{font-size:1.7rem; font-weight:900; color:var(--c-ink); line-height:1;}
.hero-stats .lab{font-size:.8rem; color:var(--c-muted); margin-top:6px;}

/* Hero 右侧浮层玻璃卡 */
.hero-card{position:relative; border-radius:var(--r-xl); padding:26px;
  background:var(--c-glass-strong); border:1px solid rgba(255,255,255,.7);
  box-shadow:var(--sh-lg); backdrop-filter:blur(16px);}
.hero-card::before{content:""; position:absolute; inset:0; border-radius:var(--r-xl);
  background:linear-gradient(140deg, rgba(255,255,255,.5), rgba(255,255,255,0) 40%); pointer-events:none;}
.hc-top{display:flex; align-items:center; gap:12px; margin-bottom:18px;}
.hc-emoji{width:52px; height:52px; border-radius:16px; display:flex; align-items:center; justify-content:center;
  font-size:26px; background:var(--grad-deep); box-shadow:0 8px 18px rgba(43,127,255,.34);}
.hc-brand{font-weight:800; color:var(--c-ink); font-size:1.05rem;}
.hc-sub{font-size:.8rem; color:var(--c-muted);}
.hc-badge{margin-left:auto; font-size:.72rem; font-weight:700; color:#0a8a4a; background:rgba(16,185,90,.12);
  padding:5px 11px; border-radius:999px;}
.hc-price{display:flex; align-items:baseline; gap:8px; margin:6px 0 4px;}
.hc-price .cur{color:var(--c-muted); font-weight:700;}
.hc-price .val{font-size:2.4rem; font-weight:900; color:var(--c-deep); letter-spacing:-1px;}
.hc-range{font-size:.82rem; color:var(--c-muted); margin-bottom:16px;}
.hc-bar{height:8px; border-radius:999px; background:rgba(43,127,255,.14); overflow:hidden;}
.hc-bar i{display:block; height:100%; width:64%; border-radius:999px; background:var(--grad);}
.hc-tags{display:flex; gap:8px; margin-top:16px; flex-wrap:wrap;}
.hc-tags span{font-size:.74rem; color:var(--c-primary-2); background:rgba(43,127,255,.1);
  border:1px solid var(--c-line-soft); padding:5px 11px; border-radius:999px;}

/* ====================================================== */
/* 通用 Section                                            */
/* ====================================================== */
.section{margin:60px 0 10px;}
.sec-head{text-align:center; max-width:660px; margin:0 auto 34px;}
.sec-head .overline{margin-bottom:10px; display:block;}
.sec-head h2{font-size:2.05rem; font-weight:900; margin:0 0 10px;}
.sec-head p{color:var(--c-muted); font-size:1rem; margin:0;}

/* 三步法 */
.steps{display:grid; grid-template-columns:repeat(3,1fr); gap:18px;}
.step{position:relative; padding:26px 22px; border-radius:var(--r-lg);
  background:var(--c-glass); border:1px solid var(--c-line-soft); box-shadow:var(--sh-sm); backdrop-filter:blur(10px);
  transition:transform .2s ease, box-shadow .2s ease;}
.step:hover{transform:translateY(-4px); box-shadow:var(--sh-md);}
.step .no{width:40px; height:40px; border-radius:12px; display:flex; align-items:center; justify-content:center;
  font-weight:900; color:#fff; background:var(--grad); box-shadow:0 8px 16px rgba(43,127,255,.3); margin-bottom:14px;}
.step h4{margin:0 0 6px; font-size:1.08rem; color:var(--c-ink);}
.step p{margin:0; font-size:.9rem; color:var(--c-muted); line-height:1.55;}

/* 特性栅格 */
.features{display:grid; grid-template-columns:repeat(2,1fr); gap:16px; margin-top:18px;}
.feat{display:flex; gap:14px; padding:20px; border-radius:var(--r-md);
  background:var(--c-glass); border:1px solid var(--c-line-soft); box-shadow:var(--sh-sm); backdrop-filter:blur(10px);}
.feat .ic{flex:0 0 auto; width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center;
  font-size:22px; background:rgba(43,127,255,.1);}
.feat h4{margin:0 0 4px; font-size:1.02rem; color:var(--c-ink);}
.feat p{margin:0; font-size:.88rem; color:var(--c-muted); line-height:1.55;}

/* ====================================================== */
/* 工具区：把 streamlit 容器变玻璃卡                         */
/* ====================================================== */
[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--c-glass-strong); border:1px solid var(--c-line)!important; border-radius:var(--r-lg)!important;
  box-shadow:var(--sh-md); backdrop-filter:blur(12px); padding:6px 6px;
}
.card-head{display:flex; align-items:center; gap:12px; margin:6px 4px 12px;}
.card-head .ic{width:44px; height:44px; border-radius:14px; display:flex; align-items:center; justify-content:center;
  font-size:22px; color:#fff; background:var(--grad); box-shadow:0 8px 16px rgba(43,127,255,.3);}
.card-head .tt{font-weight:800; color:var(--c-ink); font-size:1.1rem;}
.card-head .ds{font-size:.82rem; color:var(--c-muted);}

/* 按钮 */
.stButton>button{border-radius:999px; border:1px solid var(--c-line); font-weight:700;
  background:rgba(255,255,255,.85); color:var(--c-primary-2); transition:all .18s ease;}
.stButton>button:hover{transform:translateY(-2px); box-shadow:var(--sh-sm); border-color:var(--c-primary);}
.stButton>button[kind="primary"]{background:var(--grad); color:#fff; border:none; box-shadow:0 10px 22px rgba(43,127,255,.32);}
.stButton>button[kind="primary"]:hover{box-shadow:0 14px 28px rgba(43,127,255,.46);}

/* 上传区 */
[data-testid="stFileUploaderDropzone"]{
  background:rgba(240,247,255,.7); border:1.6px dashed var(--c-primary); border-radius:var(--r-md);}
[data-testid="stFileUploaderDropzone"]:hover{background:rgba(230,243,255,.9);}

/* 输入框 / 文本域 / 滑块 */
.stTextInput input, .stTextArea textarea{
  border-radius:12px!important; border:1px solid var(--c-line)!important; background:rgba(255,255,255,.85)!important;}
.stTextInput input:focus{border-color:var(--c-primary)!important; box-shadow:0 0 0 3px rgba(43,127,255,.15)!important;}

/* 提示框 */
[data-testid="stAlert"]{border-radius:14px; border:1px solid var(--c-line); backdrop-filter:blur(6px);}

/* Expander */
[data-testid="stExpander"]{border:1px solid var(--c-line)!important; border-radius:var(--r-md)!important;
  background:var(--c-glass)!important; box-shadow:var(--sh-sm); overflow:hidden;}
[data-testid="stExpander"] summary{font-weight:700; color:var(--c-ink);}

/* 聊天 */
[data-testid="stChatMessage"]{background:var(--c-glass); border:1px solid var(--c-line-soft);
  border-radius:16px; box-shadow:var(--sh-sm);}
[data-testid="stChatInput"]{border-radius:16px; border:1px solid var(--c-line);}

/* 图片 */
[data-testid="stImage"] img{border-radius:14px; box-shadow:var(--sh-sm);}

/* 档位单选 → 分段药丸 */
[data-testid="stRadio"] [role="radiogroup"]{gap:10px; flex-wrap:wrap;}
[data-testid="stRadio"] label{background:rgba(255,255,255,.7); border:1px solid var(--c-line);
  border-radius:999px; padding:8px 16px; transition:all .18s ease; cursor:pointer;}
[data-testid="stRadio"] label:hover{border-color:var(--c-primary); box-shadow:var(--sh-sm);}

hr{border-color:var(--c-line)!important;}

/* ====================================================== */
/* 结果页                                                  */
/* ====================================================== */
.result-hero{position:relative; overflow:hidden; border-radius:var(--r-lg); padding:24px 28px; margin-bottom:18px;
  background:var(--grad-deep); box-shadow:var(--sh-lg);}
.result-hero::after{content:""; position:absolute; right:-30px; bottom:-60px; width:240px; height:240px;
  background:radial-gradient(circle, rgba(255,255,255,.28), rgba(255,255,255,0) 70%);}
.result-hero .rh-row{display:flex; align-items:center; gap:16px; flex-wrap:wrap;}
.result-hero .rh-emoji{width:56px; height:56px; border-radius:16px; background:rgba(255,255,255,.18);
  border:1px solid rgba(255,255,255,.35); display:flex; align-items:center; justify-content:center; font-size:28px;}
.result-hero .rh-brand{color:#fff; font-weight:900; font-size:1.5rem; line-height:1.1;}
.result-hero .rh-model{color:#dbeaff; font-size:.9rem; margin-top:2px;}
.result-hero .rh-score{margin-left:auto; text-align:center; color:#fff;}
.result-hero .rh-score .v{font-size:2rem; font-weight:900; line-height:1;}
.result-hero .rh-score .l{font-size:.74rem; color:#cfe3ff; letter-spacing:1px;}

.price-panel{display:grid; grid-template-columns:1fr 1.25fr 1fr; gap:14px; margin:6px 0 14px;}
.price-card{border-radius:var(--r-md); padding:20px 18px; text-align:center;
  background:var(--c-glass-strong); border:1px solid var(--c-line); box-shadow:var(--sh-sm); backdrop-filter:blur(10px);}
.price-card .l{font-size:.82rem; color:var(--c-muted); margin-bottom:8px;}
.price-card .v{font-size:1.7rem; font-weight:800; color:var(--c-ink);}
.price-card.main{background:var(--grad-deep); border:none; box-shadow:0 18px 40px rgba(43,127,255,.36); transform:translateY(-4px);}
.price-card.main .l{color:#cfe3ff;}
.price-card.main .v{color:#fff; font-size:2.2rem;}
.price-card.main .cur{color:#cfe3ff;}

.review{position:relative; border-radius:var(--r-md); padding:22px 24px 22px 56px; margin:6px 0 4px;
  background:var(--c-glass-strong); border:1px solid var(--c-line); box-shadow:var(--sh-sm); backdrop-filter:blur(10px);}
.review::before{content:"“"; position:absolute; left:18px; top:6px; font-size:54px; line-height:1; font-weight:900;
  color:var(--c-primary); opacity:.5; font-family:Georgia,serif;}
.review .who{font-weight:800; color:var(--c-primary-2); font-size:.86rem; margin-bottom:6px;}
.review .txt{color:var(--c-text); line-height:1.65;}

.subhead{display:flex; align-items:center; gap:10px; margin:22px 0 12px; font-weight:800; color:var(--c-ink); font-size:1.12rem;}
.subhead .bar{width:4px; height:18px; border-radius:2px; background:var(--grad);}

/* ====================================================== */
/* Footer                                                  */
/* ====================================================== */
.foot{margin-top:60px; padding:26px 4px 10px; border-top:1px solid var(--c-line);
  display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;}
.foot .b{font-weight:900; color:var(--c-ink);}
.foot .s{font-size:.84rem; color:var(--c-muted);}
.foot a{color:var(--c-primary-2); text-decoration:none; font-weight:600;}

@media(max-width:900px){
  .hero-grid{grid-template-columns:1fr;}
  .steps{grid-template-columns:1fr;}
  .features{grid-template-columns:1fr;}
  .price-panel{grid-template-columns:1fr;}
  .hero h1{font-size:2.4rem;}
}
</style>
"""
