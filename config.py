# -*- coding: utf-8 -*-
"""
文件名：config.py
作用：集中管理 API 凭证、Base URL、以及【模型档位（梯度收费）】。
     ✅ 改模型/换 API：改 Secrets 或 .env；
     ✅ 切换档位：界面里选，或调 set_active_tier()，运行时即时生效，无需改代码。

读取优先级（取模型时）：显式 Secrets/.env 强制覆盖 > 当前档位 > 默认档位。
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)  # 本地 .env 优先，覆盖可能残留的旧系统环境变量

try:
    import streamlit as st
    _HAS_ST = True
except Exception:
    _HAS_ST = False


def _get(key: str, default: str = None) -> str:
    if _HAS_ST:
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
    val = os.getenv(key)
    if val:
        return val
    return default


def get_api_key() -> str:
    return _get("DASHSCOPE_API_KEY") or _get("SILICONFLOW_API_KEY")


BASE_URL = _get("LLM_BASE_URL", "https://api.siliconflow.cn/v1")

# ============================================================
# 模型档位（梯度收费）—— 模型 ID 请以硅基流动模型广场实际为准，可随时改这里
# ============================================================
TIERS = {
    "经济档": {
        "vl":   "Qwen/Qwen3-VL-8B-Instruct",   # 视觉：小杯，省钱
        "text": "Qwen/Qwen3.5-9B",             # 文本/决策：轻量
        "desc": "省钱 · 量大 · 演示够用",
    },
    "标准档": {
        "vl":   "Qwen/Qwen3-VL-32B-Instruct",  # 视觉：SOTA 级，识别准
        "text": "Qwen/Qwen3.5-27B",
        "desc": "均衡 · 识别准（默认）",
    },
    "旗舰档": {
        "vl":   "Qwen/Qwen3.5-397B-A17B",      # 视觉：顶配多模态，最强识别
        "text": "Qwen/Qwen3.6-27B",            # 文本/决策：最新，推理更强
        "desc": "最强识别 · 关键鉴定",
    },
}
DEFAULT_TIER = "标准档"
_active_tier = None  # None = 用 DEFAULT_TIER


def set_active_tier(name: str):
    """运行时切换档位（界面选择时调用）。"""
    global _active_tier
    _active_tier = name if name in TIERS else None


def get_active_tier() -> str:
    return _active_tier or DEFAULT_TIER


def _tier() -> dict:
    return TIERS[get_active_tier()]


# 取模型（调用时实时读取，所以切档位立即生效）
def get_vl_model() -> str:     return _get("VL_MODEL")     or _tier()["vl"]
def get_review_model() -> str: return _get("REVIEW_MODEL") or _tier()["text"]
def get_chat_model() -> str:   return _get("CHAT_MODEL")   or _tier()["text"]
def get_agent_model() -> str:  return _get("AGENT_MODEL")  or _tier()["text"]


# 向后兼容：旧代码若直接引用常量，仍取默认档（不影响新代码用 getter）
VL_MODEL     = TIERS[DEFAULT_TIER]["vl"]
REVIEW_MODEL = TIERS[DEFAULT_TIER]["text"]
CHAT_MODEL   = TIERS[DEFAULT_TIER]["text"]
AGENT_MODEL  = TIERS[DEFAULT_TIER]["text"]
