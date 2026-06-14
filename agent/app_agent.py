# -*- coding: utf-8 -*-
"""
文件名：agent/app_agent.py
作用：Agent 版的 Streamlit 对话界面（替代原来写死流水线的 app_ui_deploy.py）。
     用户可以：传图估价、问品牌保值、问保养知识——由 Agent 自主决定调哪个工具。

运行：streamlit run agent/app_agent.py
"""
import os
import tempfile
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from agent.snowboard_agent import build_agent, run_turn

st.set_page_config(page_title="雪板老炮 Agent", page_icon="🏂")
st.title("🏂 雪板老炮 · AI 估价 Agent")
st.caption("传图估价 / 问品牌保值 / 问保养选板 —— 我自己决定怎么帮你")

# 会话状态：Agent 实例 + 显示用消息 + 给 Agent 的记忆
if "executor" not in st.session_state:
    st.session_state.executor = build_agent(verbose=False)
if "messages" not in st.session_state:
    st.session_state.messages = []   # [{role, content}] 仅用于 UI 渲染
if "history" not in st.session_state:
    st.session_state.history = []    # LangChain message 列表，用于多轮记忆

# 图片上传（可选）
uploaded = st.file_uploader("上传雪板图片（要估价就传，纯聊天可不传）",
                            type=["jpg", "jpeg", "png"])
image_path = None
if uploaded is not None:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(uploaded.getvalue())
    tmp.close()
    image_path = tmp.name
    st.image(uploaded, width=240, caption="已上传，问我'这块值多少'试试")

# 渲染历史消息
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 输入框
placeholder = "例如：这块板值多少 / Burton 保值吗 / 板底锈了怎么办"
if prompt := st.chat_input(placeholder):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("老炮正在掂量..."):
            try:
                answer = run_turn(
                    st.session_state.executor,
                    prompt,
                    image_path=image_path,
                    chat_history=st.session_state.history,
                )
            except Exception as e:
                answer = f"（出错了：{e}）"
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    # 写入记忆
    st.session_state.history.append(HumanMessage(content=prompt))
    st.session_state.history.append(AIMessage(content=answer))
