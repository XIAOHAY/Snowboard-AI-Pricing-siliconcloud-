# -*- coding: utf-8 -*-
"""
文件名：agent/app_agent.py
版本：v3 · 视觉皮肤对齐 deploy（共用 ui_theme.GLOBAL_CSS）
作用：Agent 版 Streamlit 界面 + 模型档位 + 多图上传 + 本次调用用量/成本展示。
说明：仅统一视觉皮肤，完整保留原有功能（档位选择 / 多图融合 /
      Agent 自主工具调用 / 多轮对话 / 用量观测）。交互仍为对话式。
运行：streamlit run agent/app_agent.py
设计：资深 APP 交互 UI 设计师 / 实现：终极开发者（融合版）
"""
import os
import sys
import tempfile

# 把项目根目录加入 sys.path，使 `import ui_theme` 与 `import config` 可用
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

import config
from utils import usage
from agent.snowboard_agent import build_agent, run_turn
from ui_theme import GLOBAL_CSS  # 与 deploy 共用的设计系统（磨玻璃皮肤）

st.set_page_config(
    page_title="雪板老炮 · AI 估价 Agent",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 设计系统：deploy 同款 GLOBAL_CSS + Agent 专属补充
# ==========================================
AGENT_CSS = """
<style>
/* 底部固定聊天输入框需要留白，避免遮挡 footer/正文 */
.block-container{padding-bottom:6rem!important;}
[data-testid="stBottomBlockContainer"]{background:transparent;}

/* 侧边栏：档位面板（deploy 默认收起侧边栏，Agent 需要常驻档位选择） */
[data-testid="stSidebar"]{background:linear-gradient(180deg, rgba(255,255,255,.9), rgba(231,243,255,.9));
  backdrop-filter:blur(10px); border-right:1px solid var(--c-line);}
[data-testid="stSidebar"] h3{color:var(--c-deep);}

/* 示例问题 chips（Agent 空状态引导） */
.asks{display:flex; gap:10px; flex-wrap:wrap; margin:4px 0 6px;}
.asks span{font-size:.86rem; color:var(--c-text); background:var(--c-glass-strong); border:1px solid var(--c-line);
  padding:9px 15px; border-radius:999px; box-shadow:var(--sh-sm);}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(AGENT_CSS, unsafe_allow_html=True)

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
# Hero 头图（deploy 同款结构）
# ==========================================
st.markdown("""
<div class="hero">
  <div class="hero-grid">
    <div>
      <span class="overline">AI Agent · 多模态视觉鉴定</span>
      <h1>一眼识板，<br><span class="grad">秒出二手雪板估价</span></h1>
      <p class="lead">传图问“这块值多少”，AI 像雪场老炮儿一样识别品牌型号、判断成色损伤，给出可信价格区间，还能自主调用工具、多轮追问。</p>
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
# 空状态：如何用（三步）+ 为什么（特性栅格）+ 开始鉴定锚点
# ==========================================
if not st.session_state.messages:
    st.markdown("""
<div class="section" id="how">
  <div class="sec-head">
    <span class="overline">How it works</span>
    <h2>三步，拿到专业估价</h2>
    <p>无需任何雪板知识，跟着做就行。</p>
  </div>
  <div class="steps">
    <div class="step"><div class="no">1</div><h4>传图（可选）</h4><p>板面 / 板底 / 细节多张一起传，Agent 自动多视图融合。</p></div>
    <div class="step"><div class="no">2</div><h4>直接提问</h4><p>“这块值多少”“Burton 保值吗”“板底锈了怎么办”。</p></div>
    <div class="step"><div class="no">3</div><h4>Agent 自主作答</h4><p>它自己决定看图 / 查行情 / 给保养建议，并展示用量。</p></div>
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
    <div class="feat"><div class="ic">🤖</div><div><h4>Agent 自主调用工具</h4><p>自己决定看图 / 查行情 / 判保值 / 查保养，无需固定流程。</p></div></div>
    <div class="feat"><div class="ic">💬</div><div><h4>老炮儿对话</h4><p>对结果有疑问，随时多轮追问，像和雪场老手聊天。</p></div></div>
  </div>
</div>

<div class="section" id="start">
  <div class="sec-head">
    <span class="overline">Start now</span>
    <h2>开始鉴定</h2>
    <p>上传你的照片，然后直接提问。</p>
  </div>
</div>
""", unsafe_allow_html=True)
else:
    st.markdown('<div id="start"></div>', unsafe_allow_html=True)

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


def render_footer():
    """deploy 同款 Footer，保证两端页脚视觉一致。"""
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

# 页脚（与 deploy 一致，始终展示）
render_footer()
