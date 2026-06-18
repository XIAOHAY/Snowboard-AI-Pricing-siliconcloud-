# -*- coding: utf-8 -*-
"""
文件名：app_ui_deploy.py
版本：v2 · 产品官网级落地页重做（阿尔卑斯·高级磨玻璃主题）
说明：仅重做视觉与信息架构（Hero→产品介绍→开始鉴定→结果→Footer），
      完整保留原有功能：多图视觉鉴定、定价引擎、专家点评、手动纠错、多轮对话。
设计：资深 APP 交互 UI 设计师 / 实现：终极开发者（融合版）
"""
import streamlit as st
import pandas as pd
import os
import sys
import tempfile
import json
import time
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. 核心逻辑导入（未改动）
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from llm.qwen_vl import analyze_snowboard_image
    from utils.analysis_merge import merge_analysis_results
    from pricing.pricing_engine import estimate_secondhand_price
    from pricing.review_generator import generate_expert_review
    from llm.chat_service import get_follow_up_answer
except ImportError as e:
    st.error(f"模块导入失败: {e}. 请确保文件结构正确。")
    st.stop()

import config  # 模型档位配置（经济/标准/旗舰）

# ==========================================
# 2. 页面配置
# ==========================================
st.set_page_config(
    page_title="SnowAppraise · AI 雪板智能鉴定",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# 3. 设计系统 · 全局 CSS（磨玻璃产品官网）
# ==========================================
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
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ==========================================
# 4. 加载动画（官网级磨玻璃）
# ==========================================
LOADING_HTML = """
<style>
    .loading-overlay{position:fixed; inset:0; z-index:99999; display:flex; justify-content:center; align-items:center;
        background:linear-gradient(180deg, rgba(10,58,134,.42), rgba(43,127,255,.32)); backdrop-filter:blur(6px);}
    .glass-card{position:relative; width:36vw; min-width:330px; max-width:480px; padding:38px 24px;
        background:rgba(255,255,255,.86); backdrop-filter:blur(18px); border:1px solid rgba(255,255,255,.7);
        border-radius:28px; box-shadow:0 30px 70px rgba(11,61,145,.4);
        display:flex; flex-direction:column; align-items:center; text-align:center; color:#0f2742; font-family:'Inter',sans-serif;}
    .stage-container{position:relative; width:240px; height:300px; display:flex; justify-content:center; align-items:center; margin-bottom:14px;}
    .center-obj{position:absolute; width:104px; z-index:10; content:url('https://raw.githubusercontent.com/XIAOHAY/Snowboard-AI-Pricing/main/img/snowboard.png');}
    .orbit-container{position:absolute; width:100%; height:100%; z-index:20; will-change:transform; transform:translateZ(0); animation:orbit-spin 5s linear infinite;}
    .dwarf-artisan{position:absolute; top:14px; left:50%; width:76px; margin-left:-38px; will-change:transform; transform:translateZ(0); backface-visibility:hidden; animation:counter-spin 5s linear infinite; content:url('https://raw.githubusercontent.com/XIAOHAY/Snowboard-AI-Pricing/main/img/dwarf.png');}
    .loading-text{font-size:1.35rem; font-weight:900; letter-spacing:.5px; margin-bottom:6px; color:#0a3a86;}
    .sub-text{font-size:.88rem; color:#7690a8; line-height:1.5;}
    .ski-progress{width:72%; height:6px; margin-top:16px; border-radius:999px; overflow:hidden; background:rgba(43,127,255,.15);}
    .ski-progress i{display:block; height:100%; width:42%; border-radius:999px; background:linear-gradient(90deg,#2b7fff,#46c4ff); animation:ski-slide 1.4s ease-in-out infinite;}
    @keyframes orbit-spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
    @keyframes counter-spin{0%{transform:rotate(0deg);}100%{transform:rotate(-360deg);}}
    @keyframes ski-slide{0%{margin-left:-42%;}100%{margin-left:100%;}}
</style>
<div class="loading-overlay">
    <div class="glass-card">
        <div class="stage-container"><img class="center-obj"><div class="orbit-container"><img class="dwarf-artisan"></div></div>
        <div class="loading-text">❄️ 雪场宗师鉴定中...</div>
        <div class="sub-text">AI 正在对多视图进行多模态融合分析<br>请稍候片刻</div>
        <div class="ski-progress"><i></i></div>
    </div>
</div>
"""

# ==========================================
# 5. 侧边栏（密钥配置，逻辑未改）
# ==========================================
with st.sidebar:
    st.markdown("### 🔧 配置")
    if "DASHSCOPE_API_KEY" in st.secrets:
        st.success("✅ 云端密钥已自动加载")
        api_key = st.secrets["DASHSCOPE_API_KEY"]
    elif os.getenv("DASHSCOPE_API_KEY"):
        st.success("✅ 本地环境变量已加载")
        api_key = os.getenv("DASHSCOPE_API_KEY")
    else:
        api_key = st.text_input("请输入阿里云 DashScope API Key", type="password")
        if not api_key:
            st.warning("⚠️ 请输入 Key 继续")
            st.stop()
    os.environ["DASHSCOPE_API_KEY"] = api_key
    os.environ["SNOWBOARD_API_KEYS"] = api_key

# 初始化状态
if "current_data" not in st.session_state:
    st.session_state.current_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 模型档位：初始化 + 每次运行即时生效（鉴定/点评/聊天都按此档位选模型）
if "tier" not in st.session_state:
    st.session_state.tier = config.DEFAULT_TIER
config.set_active_tier(st.session_state.tier)


# ==========================================
# 6. 落地页静态区块（HTML 渲染函数）
# ==========================================
def render_hero():
    st.markdown("""
<div class="hero">
  <div class="hero-grid">
    <div>
      <span class="overline">AI · 多模态视觉鉴定</span>
      <h1>一眼识板，<br><span class="grad">秒出二手雪板估价</span></h1>
      <p class="lead">上传几张照片，AI 像雪场老炮儿一样识别品牌型号、判断成色损伤，并给出可信价格区间与专家点评，还能多轮追问。</p>
      <div class="hero-cta">
        <a class="cta primary" href="#start">🚀 立即免费鉴定</a>
        <a class="cta ghost" href="#how">了解工作原理</a>
      </div>
      <div class="hero-stats">
        <div><div class="num">3 视图</div><div class="lab">多角度融合分析</div></div>
        <div><div class="num">Qwen-VL</div><div class="lab">多模态大模型</div></div>
        <div><div class="num">真实行情</div><div class="lab">闲鱼快照定价</div></div>
      </div>
    </div>
    <div>
      <div class="hero-card">
        <div class="hc-top">
          <div class="hc-emoji">🏂</div>
          <div><div class="hc-brand">BURTON · Custom</div><div class="hc-sub">成色评分 8.5 / 10</div></div>
          <div class="hc-badge">保值神板</div>
        </div>
        <div class="hc-price"><span class="cur">¥</span><span class="val">1,650</span></div>
        <div class="hc-range">建议区间 ¥1,280 — ¥2,020</div>
        <div class="hc-bar"><i></i></div>
        <div class="hc-tags"><span>板面无明显划痕</span><span>钢边完好</span><span>热门款</span></div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_intro():
    st.markdown("""
<div class="section" id="how">
  <div class="sec-head">
    <span class="overline">How it works</span>
    <h2>三步，拿到专业估价</h2>
    <p>无需任何雪板知识，跟着做就行。</p>
  </div>
  <div class="steps">
    <div class="step"><div class="no">1</div><h4>上传多视图照片</h4><p>板面、板底、钢边各来一张，多角度让 AI 看得更准。没有照片也能点演示案例。</p></div>
    <div class="step"><div class="no">2</div><h4>AI 多模态鉴定</h4><p>Qwen-VL 识别品牌型号、判断成色与损伤，多图投票融合，降低单图误判。</p></div>
    <div class="step"><div class="no">3</div><h4>估价 + 专家咨询</h4><p>定价引擎结合真实行情给出价格区间与点评，还能继续追问"能再高点吗"。</p></div>
  </div>
</div>

<div class="section">
  <div class="sec-head">
    <span class="overline">Why SnowAppraise</span>
    <h2>不止给个数字</h2>
    <p>像懂行的朋友帮你把关。</p>
  </div>
  <div class="features">
    <div class="feat"><div class="ic">🧠</div><div><h4>多模态视觉理解</h4><p>看图识别品牌、型号、成色与损伤位置，而非简单关键词匹配。</p></div></div>
    <div class="feat"><div class="ic">📊</div><div><h4>真实行情定价</h4><p>规则引擎叠加闲鱼真实成交快照，给出可解释的价格区间。</p></div></div>
    <div class="feat"><div class="ic">🛠️</div><div><h4>可人工纠错</h4><p>识别有偏差？手动修正品牌/型号/成色，一键重新估价。</p></div></div>
    <div class="feat"><div class="ic">💬</div><div><h4>老炮儿对话</h4><p>对结果有疑问，随时多轮追问，像和雪场老手聊天。</p></div></div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_footer():
    st.markdown("""
<div class="foot">
  <div><span class="b">🏂 SnowAppraise</span> &nbsp;<span class="s">AI 二手雪板智能定价系统</span></div>
  <div class="s">Qwen-VL · LangChain · SiliconFlow · Streamlit &nbsp;|&nbsp; <a href="https://github.com/XIAOHAY" target="_blank">GitHub @XIAOHAY</a></div>
</div>
<div class="foot" style="border:none; padding-top:0;">
  <div class="s">⚠️ 估价结果由 AI 生成，仅供参考，不构成交易建议。</div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# 7. 主流程
# ==========================================
loading_placeholder = st.empty()

# -------- A. 落地页 + 工具区（无结果时） --------
if not st.session_state.current_data:
    render_hero()
    render_intro()

    # 工具区锚点 + 标题
    st.markdown("""
<div class="section" id="start">
  <div class="sec-head">
    <span class="overline">Start now</span>
    <h2>开始鉴定</h2>
    <p>上传你的照片，或一键体验演示案例。</p>
  </div>
</div>
""", unsafe_allow_html=True)

    # ---------- 档位选择（鉴定前先选模型档位）----------
    with st.container(border=True):
        st.markdown(
            '<div class="card-head"><div class="ic">🎚️</div>'
            '<div><div class="tt">选择鉴定档位</div>'
            '<div class="ds">档位越高识别越准、成本越高；演示用标准档即可</div></div></div>',
            unsafe_allow_html=True)
        tier_names = list(config.TIERS.keys())
        st.radio(
            "选择模型档位", tier_names, key="tier", horizontal=True,
            label_visibility="collapsed",
            format_func=lambda t: f"{t} · {config.TIERS[t]['desc']}",
        )
        _t = config.TIERS[st.session_state.tier]
        st.caption(f"👁️ 视觉模型 `{_t['vl']}` ｜ 🧠 文本模型 `{_t['text']}`")

    col_upload, col_demo = st.columns([1, 1], gap="large")

    # ---------- 左：上传 ----------
    with col_upload:
        with st.container(border=True):
            st.markdown(
                '<div class="card-head"><div class="ic">📤</div>'
                '<div><div class="tt">上传照片</div><div class="ds">已有照片？直接上传体验 AI 鉴定</div></div></div>',
                unsafe_allow_html=True)
            user_hint = st.text_input("💡 (选填) 线索提示", placeholder="例如：Gray Desperado...")
            uploaded_files = st.file_uploader("点击或拖拽上传（板面 / 板底 / 钢边）", type=['jpg', 'png'],
                                              accept_multiple_files=True)

            if st.button("🚀 开始分析", type="primary", use_container_width=True):
                if uploaded_files:
                    loading_placeholder.markdown(LOADING_HTML, unsafe_allow_html=True)
                    try:
                        analysis_results = []
                        uploaded_images_bytes = []
                        for uploaded_file in uploaded_files:
                            file_bytes = uploaded_file.read()
                            uploaded_images_bytes.append(file_bytes)
                            suffix = os.path.splitext(uploaded_file.name)[1]
                            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                                tmp.write(file_bytes)
                                temp_path = tmp.name
                            try:
                                res = analyze_snowboard_image(temp_path, user_hint=user_hint)
                                analysis_results.append(res)
                            finally:
                                os.remove(temp_path)

                        if analysis_results:
                            final_analysis = merge_analysis_results(analysis_results)
                            price_result = estimate_secondhand_price(final_analysis)
                            p_low = price_result.get("price_low", 0)
                            p_high = price_result.get("price_high", 0)
                            expert_comment = generate_expert_review(
                                brand=final_analysis.get("brand"),
                                model=final_analysis.get("possible_model"),
                                condition_score=final_analysis.get("condition_score"),
                                price_low=p_low, price_high=p_high,
                                base_damage=final_analysis.get("base_damage"),
                                edge_damage=final_analysis.get("edge_damage")
                            )
                            st.session_state.current_data = {
                                "suggest_price": int((p_low + p_high) / 2),
                                "price_low": p_low,
                                "price_high": p_high,
                                "expert_review": expert_comment,
                                "brand": final_analysis.get("brand"),
                                "model": final_analysis.get("possible_model"),
                                "condition_score": final_analysis.get("condition_score"),
                                "base_damage": final_analysis.get("base_damage"),
                                "edge_damage": final_analysis.get("edge_damage"),
                                "calculation_process": price_result.get("calculation_process", []),
                                "uploaded_images": uploaded_images_bytes
                            }
                            loading_placeholder.empty()
                            st.rerun()
                        else:
                            loading_placeholder.empty()
                            st.error("未能识别图片内容")
                    except Exception as e:
                        loading_placeholder.empty()
                        st.error(f"运行出错: {e}")
                else:
                    st.warning("请先上传至少一张图片")

    # ---------- 右：一键演示 ----------
    with col_demo:
        with st.container(border=True):
            st.markdown(
                '<div class="card-head"><div class="ic">⚡️</div>'
                '<div><div class="tt">一键体验</div><div class="ds">没有照片？点击案例体验多视图融合分析</div></div></div>',
                unsafe_allow_html=True)

            DEMO_CASES = {
                "demo_good": {
                    "label": "✨ 挑战：热门保值神板",
                    "paths": ["./examples/good_top.jpg", "./examples/good_base.jpg", "./examples/good_edge.jpg"],
                    "desc": "热门准新款",
                    "force_brand": "BURTON", "force_model": "BURTON Good Company龙年限定", "hint": "Burton Good Company龙年限定"
                },
                "demo_bad": {
                    "label": "🥊 挑战：识别严重损伤",
                    "paths": ["./examples/bad_top.jpg", "./examples/bad_base.jpg", "./examples/bad_detail.jpg"],
                    "desc": "板底严重划痕 (多角度)",
                    "force_brand": "Burton", "force_model": "custom", "hint": "Burton Custom , heavy scratch"
                },
                "demo_old": {
                    "label": "🔍 鉴定日系经典",
                    "paths": ["./examples/old_top.jpg", "./examples/old_base.jpg", "./examples/old_logo.jpg"],
                    "desc": "老牌保值款",
                    "force_brand": "ogasaka", "force_model": "fcs", "hint": "ogasaka fcs 2526新款"
                }
            }

            def run_demo_analysis(case_key):
                cfg = DEMO_CASES[case_key]
                image_paths = cfg["paths"]
                with st.container():
                    st.markdown(f"##### 🖼️ 正在分析：{cfg['desc']}")
                    cols = st.columns(len(image_paths))
                    for idx, col in enumerate(cols):
                        with col:
                            if os.path.exists(image_paths[idx]):
                                st.image(image_paths[idx], caption=f"视图 {idx + 1}", use_container_width=True)
                    st.info("⚡️ 演示模式：正在对 3 张视图进行【多模态融合分析】...")

                loading_placeholder.markdown(LOADING_HTML, unsafe_allow_html=True)
                try:
                    analysis_results = []
                    for img_path in image_paths:
                        if os.path.exists(img_path):
                            res = analyze_snowboard_image(img_path, user_hint=cfg["hint"])
                            res["brand"] = cfg["force_brand"]
                            res["possible_model"] = cfg["force_model"]
                            analysis_results.append(res)

                    if analysis_results:
                        final_analysis = merge_analysis_results(analysis_results)
                        price_result = estimate_secondhand_price(final_analysis)
                        p_low = price_result.get("price_low", 0)
                        p_high = price_result.get("price_high", 0)
                        expert_comment = generate_expert_review(
                            brand=final_analysis.get("brand"),
                            model=final_analysis.get("possible_model"),
                            condition_score=final_analysis.get("condition_score"),
                            price_low=p_low, price_high=p_high,
                            base_damage=final_analysis.get("base_damage"),
                            edge_damage=final_analysis.get("edge_damage")
                        )
                        st.session_state.current_data = {
                            "suggest_price": int((p_low + p_high) / 2),
                            "price_low": p_low,
                            "price_high": p_high,
                            "expert_review": expert_comment,
                            "brand": final_analysis.get("brand"),
                            "model": final_analysis.get("possible_model"),
                            "condition_score": final_analysis.get("condition_score"),
                            "base_damage": final_analysis.get("base_damage"),
                            "edge_damage": final_analysis.get("edge_damage"),
                            "calculation_process": price_result.get("calculation_process", []),
                            "demo_image_paths": image_paths
                        }
                        loading_placeholder.empty()
                        st.rerun()
                    else:
                        loading_placeholder.empty()
                        st.error("未能加载演示图片，请检查文件路径")
                except Exception as e:
                    loading_placeholder.empty()
                    st.error(f"演示运行失败: {e}")

            for key, cfg in DEMO_CASES.items():
                cover_img = cfg["paths"][0]
                if os.path.exists(cover_img):
                    c_img, c_btn = st.columns([1, 2])
                    with c_img:
                        st.image(cover_img, use_container_width=True)
                    with c_btn:
                        st.markdown(f"**{cfg['desc']}**")
                        if st.button(cfg['label'], key=key, use_container_width=True):
                            run_demo_analysis(key)
                else:
                    st.warning(f"⚠️ 图片缺失: {cover_img}")

    render_footer()

# -------- B. 结果页（有结果时） --------
else:
    data = st.session_state.current_data

    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ 鉴定下一块", use_container_width=True):
            st.session_state.current_data = None
            st.session_state.chat_history = []
            st.rerun()

    # 结果 Hero
    brand = data.get('brand') or '未知品牌'
    model = data.get('model') or '型号待定'
    score = data.get('condition_score', '—')
    st.markdown(f"""
<div class="result-hero">
  <div class="rh-row">
    <div class="rh-emoji">🏂</div>
    <div><div class="rh-brand">{brand}</div><div class="rh-model">{model}</div></div>
    <div class="rh-score"><div class="v">{score}</div><div class="l">成色 / 10</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

    # 价格看板
    st.markdown(f"""
<div class="price-panel">
  <div class="price-card"><div class="l">📉 最低估价</div><div class="v"><span class="cur">¥</span>{data.get('price_low', 0)}</div></div>
  <div class="price-card main"><div class="l">🏷️ 建议成交价</div><div class="v"><span class="cur">¥</span>{data.get('suggest_price', 0)}</div></div>
  <div class="price-card"><div class="l">📈 最高估价</div><div class="v"><span class="cur">¥</span>{data.get('price_high', 0)}</div></div>
</div>
""", unsafe_allow_html=True)

    # 专家点评
    review = data.get('expert_review', '暂无')
    st.markdown(f"""
<div class="review">
  <div class="who">🗣️ 雪场老炮儿点评</div>
  <div class="txt">{review}</div>
</div>
""", unsafe_allow_html=True)

    # 图片回显
    st.markdown('<div class="subhead"><span class="bar"></span>分析底图</div>', unsafe_allow_html=True)
    if "demo_image_paths" in data:
        paths = data["demo_image_paths"]
        cols = st.columns(len(paths))
        for idx, col in enumerate(cols):
            with col:
                if os.path.exists(paths[idx]):
                    st.image(paths[idx], use_container_width=True, caption=f"视图 {idx + 1}")
    elif data.get("uploaded_images"):
        imgs = data["uploaded_images"]
        cols = st.columns(len(imgs))
        for idx, col in enumerate(cols):
            with col:
                st.image(imgs[idx], use_container_width=True, caption=f"上传图 {idx + 1}")
    st.caption(
        f"💡 AI 综合结论：品牌锁定 `{brand}` ｜ 成色评分 `{score}` ｜ 损伤检测 `{data.get('base_damage', '无')}`")

    # 手动纠错
    with st.expander("🛠️ 识别错了？点这里修正品牌 / 型号", expanded=False):
        with st.form("fix_form"):
            col_a, col_b, col_c = st.columns(3)
            new_brand = col_a.text_input("品牌", value=data.get('brand', ''))
            new_model = col_b.text_input("型号", value=data.get('model', ''))
            new_score = col_c.slider("成色", 1.0, 10.0, float(data.get('condition_score', 8.0)))
            if st.form_submit_button("🔄 修正并重新估价"):
                with st.spinner("正在重算..."):
                    try:
                        new_analysis = {
                            "brand": new_brand, "possible_model": new_model, "condition_score": new_score,
                            "can_use": True, "base_damage": data.get("base_damage", "用户修正"),
                            "edge_damage": data.get("edge_damage", "用户修正"), "is_old_model": False
                        }
                        new_price_res = estimate_secondhand_price(new_analysis)
                        p_low = new_price_res.get("price_low", 0)
                        p_high = new_price_res.get("price_high", 0)
                        new_review = generate_expert_review(
                            brand=new_brand, model=new_model, condition_score=new_score,
                            price_low=p_low, price_high=p_high,
                            base_damage=data.get("base_damage"), edge_damage=data.get("edge_damage")
                        )
                        updated_data = {
                            "brand": new_brand, "model": new_model, "condition_score": new_score,
                            "price_low": p_low, "price_high": p_high,
                            "suggest_price": int((p_low + p_high) / 2),
                            "expert_review": new_review,
                            "calculation_process": new_price_res.get("calculation_process", [])
                        }
                        st.session_state.current_data.update(updated_data)
                        st.session_state.chat_history = []
                        st.toast("数据已修正！", icon="✅")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"修正失败: {e}")

    # 聊天区
    st.markdown('<div class="subhead"><span class="bar"></span>咨询专家</div>', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("对估价有疑问？问问老炮儿..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                ans = get_follow_up_answer(prompt, data)
                st.write(ans)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})

    render_footer()
