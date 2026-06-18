# -*- coding: utf-8 -*-
"""
文件名：agent/app_agent.py
版本：v2 · 产品官网级磨玻璃皮肤（阿尔卑斯·清爽蓝白）
作用：Agent 版 Streamlit 界面 + 模型档位 + 多图上传 + 本次调用用量/成本展示。
说明：仅重做视觉，完整保留原有功能（档位选择 / 多图融合 / Agent 自主工具调用 / 用量观测）。
运行：streamlit run agent/app_agent.py
设计：资深 APP 交互 UI 设计师 / 实现：终极开发者（融合版）
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

import config
from utils import usage
from agent.snowboard_agent import build_agent, run_turn

st.set_page_config(
    page_title="雪板老炮 · AI 估价 Agent",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 设计系统 · 全局 CSS（磨玻璃产品官网）
# ==========================================
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{
  --c-deep:#0a3a86; --c-primary:#2b7fff; --c-primary-2:#1466e6; --c-cyan:#46c4ff;
  --c-ink:#0f2742; --c-text:#3a566f; --c-muted:#7690a8;
  --c-line:rgba(20,80,160,.12); --c-line-soft:rgba(20,80,160,.07);
  --c-glass:rgba(255,255,255,.62); --c-glass-strong:rgba(255,255,255,.82);
  --grad:linear-gradient(120deg,var(--c-primary) 0%, var(--c-cyan) 100%);
  --grad-deep:linear-gradient(125deg,#0a3a86 0%, #2b7fff 55%, #46c4ff 100%);
  --r-sm:12px; --r-md:18px; --r-lg:26px; --r-xl:34px;
  --sh-sm:0 4px 14px rgba(20,80,160,.08); --sh-md:0 14px 40px rgba(20,80,160,.14); --sh-lg:0 30px 70px rgba(11,61,145,.20);
}
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
[data-testid="stToolbar"]{display:none;}
[data-testid="stDecoration"]{display:none;}
[data-testid="stHeader"]{background:transparent; height:0;}

.stApp{color:var(--c-text); font-family:'Inter','PingFang SC','Microsoft YaHei',sans-serif;
  background:
    radial-gradient(900px 480px at 85% -6%, rgba(70,196,255,.28) 0%, rgba(70,196,255,0) 60%),
    radial-gradient(820px 460px at 8% 2%, rgba(43,127,255,.18) 0%, rgba(43,127,255,0) 58%),
    linear-gradient(180deg,#eef6ff 0%, #f6fbff 40%, #ffffff 100%);}
.stApp::before{content:""; position:fixed; inset:0; pointer-events:none; z-index:0; opacity:.45;
  background-image:
    radial-gradient(2px 2px at 18% 28%, #fff 50%, transparent 51%),
    radial-gradient(2px 2px at 72% 16%, #fff 50%, transparent 51%),
    radial-gradient(1.5px 1.5px at 42% 62%, #d6ecff 50%, transparent 51%),
    radial-gradient(1.5px 1.5px at 88% 72%, #fff 50%, transparent 51%);
  background-size:620px 620px,520px 520px,420px 420px,460px 460px;}
.block-container{max-width:980px; padding-top:1.2rem; padding-bottom:6rem; position:relative; z-index:1;}

.overline{font-size:.78rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:var(--c-primary-2);}
h1,h2,h3,h4{color:var(--c-ink); letter-spacing:-.3px;}

/* Hero */
.hero{position:relative; overflow:hidden; border-radius:var(--r-xl); padding:32px 34px; margin-bottom:18px;
  background:var(--c-glass-strong); border:1px solid rgba(255,255,255,.7); box-shadow:var(--sh-md); backdrop-filter:blur(14px);}
.hero::after{content:""; position:absolute; right:-50px; top:-60px; width:240px; height:240px;
  background:radial-gradient(circle, rgba(70,196,255,.25), rgba(70,196,255,0) 70%);}
.hero .overline{display:block; margin-bottom:12px;}
.hero h1{font-size:2.3rem; line-height:1.1; font-weight:900; margin:0 0 12px; letter-spacing:-.8px;}
.hero h1 .grad{background:var(--grad); -webkit-background-clip:text; background-clip:text; color:transparent;}
.hero p{font-size:1.02rem; color:var(--c-text); margin:0 0 16px; max-width:600px;}
.hero .chips{display:flex; gap:8px; flex-wrap:wrap;}
.hero .chips span{font-size:.76rem; font-weight:600; color:var(--c-primary-2); background:rgba(43,127,255,.1);
  border:1px solid var(--c-line-soft); padding:6px 12px; border-radius:999px;}

/* 如何用 三步 */
.steps{display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:8px 0 18px;}
.step{padding:18px 18px; border-radius:var(--r-md); background:var(--c-glass); border:1px solid var(--c-line-soft);
  box-shadow:var(--sh-sm); backdrop-filter:blur(10px);}
.step .no{width:34px; height:34px; border-radius:10px; display:flex; align-items:center; justify-content:center;
  font-weight:900; color:#fff; background:var(--grad); box-shadow:0 8px 16px rgba(43,127,255,.3); margin-bottom:10px;}
.step h4{margin:0 0 4px; font-size:1rem;}
.step p{margin:0; font-size:.85rem; color:var(--c-muted); line-height:1.5;}

/* 卡片头 */
.card-head{display:flex; align-items:center; gap:12px; margin:6px 4px 12px;}
.card-head .ic{width:42px; height:42px; border-radius:13px; display:flex; align-items:center; justify-content:center;
  font-size:21px; color:#fff; background:var(--grad); box-shadow:0 8px 16px rgba(43,127,255,.3);}
.card-head .tt{font-weight:800; color:var(--c-ink); font-size:1.05rem;}
.card-head .ds{font-size:.82rem; color:var(--c-muted);}

/* 示例问题 chips */
.asks{display:flex; gap:10px; flex-wrap:wrap; margin:4px 0 6px;}
.asks span{font-size:.86rem; color:var(--c-text); background:var(--c-glass-strong); border:1px solid var(--c-line);
  padding:9px 15px; border-radius:999px; box-shadow:var(--sh-sm);}

/* 容器玻璃卡 */
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--c-glass-strong); border:1px solid var(--c-line)!important;
  border-radius:var(--r-lg)!important; box-shadow:var(--sh-md); backdrop-filter:blur(12px); padding:6px 6px;}

/* 侧边栏 */
[data-testid="stSidebar"]{background:linear-gradient(180deg, rgba(255,255,255,.9), rgba(231,243,255,.9));
  backdrop-filter:blur(10px); border-right:1px solid var(--c-line);}
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] .stSubheader{color:var(--c-deep);}

/* 档位单选 → 药丸 */
[data-testid="stRadio"] [role="radiogroup"]{gap:8px;}
[data-testid="stRadio"] label{background:rgba(255,255,255,.7); border:1px solid var(--c-line);
  border-radius:14px; padding:8px 12px; transition:all .18s ease;}
[data-testid="stRadio"] label:hover{border-color:var(--c-primary); box-shadow:var(--sh-sm);}

/* 上传区 */
[data-testid="stFileUploaderDropzone"]{background:rgba(240,247,255,.7); border:1.6px dashed var(--c-primary); border-radius:var(--r-md);}
[data-testid="stFileUploaderDropzone"]:hover{background:rgba(230,243,255,.9);}

/* 聊天气泡 */
[data-testid="stChatMessage"]{background:var(--c-glass); border:1px solid var(--c-line-soft);
  border-radius:18px; box-shadow:var(--sh-sm); backdrop-filter:blur(8px);}
[data-testid="stChatInput"]{border-radius:18px; border:1px solid var(--c-line); box-shadow:var(--sh-md);}
[data-testid="stBottomBlockContainer"]{background:transparent;}

/* 用量 expander */
[data-testid="stExpander"]{border:1px solid var(--c-line)!important; border-radius:var(--r-md)!important;
  background:var(--c-glass)!important; box-shadow:var(--sh-sm); overflow:hidden;}
[data-testid="stExpander"] summary{font-weight:700; color:var(--c-ink);}

[data-testid="stImage"] img{border-radius:14px; box-shadow:var(--sh-sm);}
hr{border-color:var(--c-line)!important;}

@media(max-width:900px){.steps{grid-template-columns:1fr;} .hero h1{font-size:1.9rem;}}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ==========================================
# 侧边栏：模型档位（逻辑未改）
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ 模型档位")
    tier_names = list(config.TIERS.keys())
    tier = st.radio("选择档位", tier_names,
                    index=tier_names.index(config.DEFAULT_TIER),
                    format_func=lambda t: f"{t} · {config.TIERS[t]['desc']}")
    config.set_active_tier(tier)
    st.caption(f"👁️ 视觉：`{config.TIERS[tier]['vl']}`")
    st.caption(f"🧠 文本：`{config.TIERS[tier]['text']}`")

# ==========================================
# Hero 头图
# ==========================================
st.markdown("""
<div class="hero">
  <span class="overline">AI Agent · 自主决策估价</span>
  <h1>雪板老炮 · <span class="grad">AI 估价 Agent</span></h1>
  <p>传图问"这块值多少"，或问品牌保值、保养选板 —— 我自己决定调用哪个工具来帮你，并实时展示用量与成本。</p>
  <div class="chips"><span>🖼️ 多图融合鉴定</span><span>🧰 自主工具调用</span><span>📊 用量/成本可观测</span></div>
</div>
""", unsafe_allow_html=True)

# 会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []

# 档位变化 → 重建 Agent
if st.session_state.get("_tier") != tier:
    st.session_state._tier = tier
    st.session_state.executor = build_agent(verbose=False)
if "executor" not in st.session_state:
    st.session_state.executor = build_agent(verbose=False)

# ==========================================
# 空状态：如何用 + 示例问题（仅无消息时）
# ==========================================
if not st.session_state.messages:
    st.markdown("""
<div class="steps">
  <div class="step"><div class="no">1</div><h4>传图（可选）</h4><p>板面 / 板底 / 细节多张一起传，Agent 自动多视图融合。</p></div>
  <div class="step"><div class="no">2</div><h4>直接提问</h4><p>"这块值多少""Burton 保值吗""板底锈了怎么办"。</p></div>
  <div class="step"><div class="no">3</div><h4>Agent 自主作答</h4><p>它自己决定看图/查行情/给保养建议，并展示用量。</p></div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 多图上传（逻辑未改，外观玻璃卡）
# ==========================================
with st.container(border=True):
    st.markdown(
        '<div class="card-head"><div class="ic">📤</div>'
        '<div><div class="tt">上传雪板图片</div><div class="ds">可多张：板面 / 板底 / 细节，自动融合分析</div></div></div>',
        unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "上传雪板图片（可多张）",
        type=["jpg", "jpeg", "png"], accept_multiple_files=True,
        label_visibility="collapsed",
    )
    image_paths = []
    if uploaded_files:
        cols = st.columns(min(len(uploaded_files), 4))
        for i, uf in enumerate(uploaded_files):
            suffix = os.path.splitext(uf.name)[1] or ".jpg"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(uf.getvalue())
            tmp.close()
            image_paths.append(tmp.name)
            with cols[i % len(cols)]:
                st.image(uf, use_container_width=True, caption=f"视图 {i + 1}")
        st.caption(f"已上传 {len(image_paths)} 张，问我“这块值多少”试试")

# 空状态示例问题
if not st.session_state.messages:
    st.markdown("""
<div class="asks">
  <span>💰 这块板值多少？</span>
  <span>📈 Burton 保值吗？</span>
  <span>🛠️ 板底锈了怎么办？</span>
  <span>🎯 新手选什么板型？</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 渲染历史
# ==========================================
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


def render_usage():
    s = usage.summary()
    if not s["calls"]:
        return
    head = f"📊 本次调用：{s['calls']} 次 · {s['total_tokens']} tokens · ≈¥{s['cost']:.4f}（估算）"
    with st.expander(head):
        for m, b in s["by_model"].items():
            st.caption(f"`{m}` ×{b['calls']}　入 {b['in']} / 出 {b['out']} tok　≈¥{b['cost']:.4f}")
        st.caption("价格为估算，可在 utils/usage.py 的 PRICES 里按模型广场实际填写。")


# ==========================================
# 输入（逻辑未改）
# ==========================================
placeholder = "例如：这块板值多少 / Burton 保值吗 / 板底锈了怎么办"
if prompt := st.chat_input(placeholder):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"老炮正在掂量...（{tier}）"):
            try:
                answer = run_turn(
                    st.session_state.executor,
                    prompt,
                    image_paths=image_paths,
                    chat_history=st.session_state.history,
                )
            except Exception as e:
                answer = f"（出错了：{e}）"
            st.markdown(answer)
            render_usage()

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.history.append(HumanMessage(content=prompt))
    st.session_state.history.append(AIMessage(content=answer))
