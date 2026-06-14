# -*- coding: utf-8 -*-
"""
文件名：config.py
作用：集中管理 API 凭证、Base URL、各模型 ID。
     ✅ 改模型 / 换 API：优先改 Streamlit Secrets 或 .env，无需改动任何业务代码。

读取优先级：Streamlit Secrets（线上）> 环境变量 / .env（本地）> 代码默认值。
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Streamlit 在云端会把 Secrets 暴露给 st.secrets；本地无 secrets 文件时安全降级。
try:
    import streamlit as st
    _HAS_ST = True
except Exception:
    _HAS_ST = False


def _get(key: str, default: str = None) -> str:
    # 1) Streamlit Secrets（线上优先）
    if _HAS_ST:
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
    # 2) 环境变量 / .env（本地）
    val = os.getenv(key)
    if val:
        return val
    # 3) 代码默认值
    return default


# ===================== API 凭证 & 接入点 =====================
def get_api_key() -> str:
    """运行时获取 API Key（兼容两种变量名）。"""
    return _get("DASHSCOPE_API_KEY") or _get("SILICONFLOW_API_KEY")


BASE_URL = _get("LLM_BASE_URL", "https://api.siliconflow.cn/v1")

# ===================== 模型 ID =====================
# 改模型只改这里的默认值，或在 Secrets / .env 里覆盖同名变量即可。
VL_MODEL     = _get("VL_MODEL", "Qwen/Qwen2-VL-72B-Instruct")      # 视觉鉴定
REVIEW_MODEL = _get("REVIEW_MODEL", "Qwen/Qwen2.5-72B-Instruct")   # 专家点评
CHAT_MODEL   = _get("CHAT_MODEL", "Qwen/Qwen2.5-72B-Instruct")     # 追问对话
AGENT_MODEL  = _get("AGENT_MODEL", "Qwen/Qwen2.5-72B-Instruct")    # Agent 决策
