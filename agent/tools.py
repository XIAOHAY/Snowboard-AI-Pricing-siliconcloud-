# -*- coding: utf-8 -*-
"""
文件名：agent/tools.py
作用：把现有能力封装成 LangChain 工具。
     多图说明：本轮"待鉴定的图片"由前端通过 set_pending_images() 放进上下文，
     appraise_snowboard 工具自己取——模型只负责决定"要不要估价"，不碰文件路径，更稳。
"""
import os
import json
from collections import Counter
from langchain_core.tools import tool

from llm.qwen_vl import analyze_snowboard_image
from utils.analysis_merge import merge_analysis_results
from pricing.pricing_engine import (
    estimate_secondhand_price,
    BRAND_TIERS,
    TIER_FACTORS,
    BRAND_NICKNAMES,
)

# ===== 本轮待鉴定的图片（前端每轮设置）=====
_PENDING_IMAGES = []


def set_pending_images(paths):
    """前端在每轮调用前设置本轮上传的图片路径列表。"""
    global _PENDING_IMAGES
    _PENDING_IMAGES = [p for p in (paths or []) if p]


def get_pending_images():
    return list(_PENDING_IMAGES)


@tool
def appraise_snowboard(user_hint: str = "") -> str:
    """给【用户当前上传的雪板图片】做成色鉴定 + 确定性估价（支持多视图融合）。

    使用场景：用户上传了雪板图片，并且想估价 / 想卖 / 想买这块板时调用。
    多张图（板面/板底/细节）会自动融合：品牌投票、成色取均值、损伤合并。
    参数:
        user_hint: 用户对品牌或型号的额外提示（如“这是小贺的板”），没有就传空字符串。
    返回: JSON 字符串，含融合后的鉴定结果(analysis) 与价格区间(price)。
    """
    images = get_pending_images()
    if not images:
        return json.dumps(
            {"error": "NO_IMAGE", "message": "用户还没上传图片。请提示用户先上传雪板照片再估价。"},
            ensure_ascii=False,
        )

    # 1. 逐张视觉鉴定
    analyses = []
    for p in images:
        try:
            analyses.append(analyze_snowboard_image(p, user_hint or None))
        except Exception as e:
            analyses.append({"brand": "UNKNOWN", "error": str(e), "can_use": True, "condition_score": 5})

    # 2. 多图融合（单图也走，保持一致）
    final = merge_analysis_results(analyses)

    # merge 不保留型号，这里从各图里补一个最常见的有效型号（影响热门款溢价）
    models = [str(a.get("possible_model", "")).strip() for a in analyses]
    models = [m for m in models if m and m.upper() not in {"UNKNOWN", "NONE", "NULL", "未知型号"}]
    final["possible_model"] = Counter(models).most_common(1)[0][0] if models else ""

    # 3. 确定性定价
    price = estimate_secondhand_price(final)
    return json.dumps({"analysis": final, "price": price, "image_count": len(images)},
                      ensure_ascii=False)


@tool
def get_brand_liquidity(brand: str) -> str:
    """查询某个雪板品牌的【保值梯队】与保值系数。

    使用场景：用户只是泛泛地问某品牌保不保值、掉不掉价，不涉及具体某块板、也没有图片时调用。
    参数: brand: 品牌名，中文绰号或英文均可（如 'Burton'、'菠萝'、'小贺'）。
    """
    raw = brand.strip()
    b = BRAND_NICKNAMES.get(raw, raw).upper()
    tier = BRAND_TIERS.get(b, "TIER_5")
    factor = TIER_FACTORS.get(tier, 0.35)
    desc = {
        "TIER_1": "理财级（Gentemstick等），落地约 75 折，极保值",
        "TIER_2": "日系/高端（Gray/Ogasaka等），落地约 65 折，保值",
        "TIER_3": "国际大牌（Burton/Salomon等），落地约 5 折",
        "TIER_4": "二线品牌（K2/Ride等），较难卖上价",
        "TIER_5": "入门/国产，残值很低",
    }.get(tier, "未知梯队")
    return json.dumps({"brand": b, "tier": tier, "factor": factor, "desc": desc}, ensure_ascii=False)


@tool
def search_market_price(brand: str, model: str = "") -> str:
    """联网查询某型号雪板当前的【二手市场在售行情】，用于交叉验证估价是否合理。

    使用场景：已经给出估价后，用户质疑“凭什么这个价” / 想看看市场实际挂多少时调用。
    参数: brand 品牌；model 型号（可空）。
    """
    # TODO(接真实数据源)：当前为示例数据，先保证 Agent 闭环可演示。
    mock_listings = [
        {"platform": "闲鱼", "title": f"{brand} {model} 二手", "price": 2600, "condition": "9成新"},
        {"platform": "闲鱼", "title": f"{brand} {model}", "price": 1980, "condition": "8成新"},
        {"platform": "小红书", "title": f"出 {brand} {model}", "price": 2200, "condition": "95新"},
    ]
    return json.dumps(
        {"source": "MOCK_DATA", "listings": mock_listings,
         "note": "当前为示例数据，尚未接入实时行情；回答时请说明这是参考而非真实成交价"},
        ensure_ascii=False,
    )


@tool
def query_gear_knowledge(question: str) -> str:
    """回答滑雪装备相关的【知识性问题】（保养、选板、参数、术语等），与具体估价无关时调用。

    参数: question: 用户的知识性问题。
    """
    kb_path = os.path.join(os.path.dirname(__file__), "..", "data", "gear_knowledge.md")
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = f.read()
        return f"【装备知识库】可参考以下内容回答用户问题：\n{kb}"
    return "（暂无本地知识库，可用通用常识回答，并提示用户这是常识性建议。）"


ALL_TOOLS = [
    appraise_snowboard,
    get_brand_liquidity,
    search_market_price,
    query_gear_knowledge,
]
