# -*- coding: utf-8 -*-
"""
文件名：agent/app_agent.py
作用：Agent 版 Streamlit 界面 + 模型档位 + 多图上传 + 本次调用用量/成本展示。
运行：streamlit run agent/app_agent.py
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

st.set_page_config(page_title="雪板老炮 Agent", page_icon="🏂")
st.title("🏂 雪板老炮 · AI 估价 Agent")
st.caption("传图估价 / 问品牌保值 / 问保养选板 —— 我自己决定怎么帮你")

# ===== 侧边栏：模型档位 =====
with st.sidebar:
    st.subheader("⚙️ 模型档位")
    tier_names = list(config.TIERS.keys())
    tier = st.radio("选择档位", tier_names,
                    index=tier_names.index(config.DEFAULT_TIER),
                    format_func=lambda t: f"{t} · {config.TIERS[t]['desc']}")
    config.set_active_tier(tier)
    st.caption(f"视觉：`{config.TIERS[tier]['vl']}`")
    st.caption(f"文本：`{config.TIERS[tier]['text']}`")

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

# ===== 多图上传 =====
uploaded_files = st.file_uploader(
    "上传雪板图片（可多张：板面 / 板底 / 细节，会自动融合）",
    type=["jpg", "jpeg", "png"], accept_multiple_files=True,
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

# 渲染历史
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


# 输入
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
            render_usage()  # 本次调用的模型/token/花费

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.history.append(HumanMessage(content=prompt))
    st.session_state.history.append(AIMessage(content=answer))
