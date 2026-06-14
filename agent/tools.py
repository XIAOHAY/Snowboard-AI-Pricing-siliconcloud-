# -*- coding: utf-8 -*-
"""
文件名：agent/tools.py
作用：把现有能力封装成 LangChain 工具。
     search_market_price 已接入真实闲鱼行情快照（data/market_snapshot.json）。
     多图：本轮待鉴定图片由前端 set_pending_images() 放进上下文，appraise_snowboard 自取。
"""
import os
import json
import statistics
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
    global _PENDING_IMAGES
    _PENDING_IMAGES = [p for p in (paths or []) if p]


def get_pending_images():
    return list(_PENDING_IMAGES)


# ===== 真实行情快照（懒加载 + 缓存）=====
_SNAPSHOT = None


def _load_snapshot():
    global _SNAPSHOT
    if _SNAPSHOT is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "market_snapshot.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                _SNAPSHOT = json.load(f)
        except Exception:
            _SNAPSHOT = {"listings": []}
    return _SNAPSHOT


@tool
def appraise_snowboard(user_hint: str = "") -> str:
    """给【用户当前上传的雪板图片】做成色鉴定 + 确定性估价（支持多视图融合）。

    使用场景：用户上传了雪板图片，并且想估价 / 想卖 / 想买这块板时调用。
    参数: user_hint: 用户对品牌或型号的额外提示，没有就传空字符串。
    """
    images = get_pending_images()
    if not images:
        return json.dumps({"error": "NO_IMAGE", "message": "用户还没上传图片。请提示用户先上传雪板照片再估价。"},
                          ensure_ascii=False)
    analyses = []
    for p in images:
        try:
            analyses.append(analyze_snowboard_image(p, user_hint or None))
        except Exception as e:
            analyses.append({"brand": "UNKNOWN", "error": str(e), "can_use": True, "condition_score": 5})
    final = merge_analysis_results(analyses)
    models = [str(a.get("possible_model", "")).strip() for a in analyses]
    models = [m for m in models if m and m.upper() not in {"UNKNOWN", "NONE", "NULL", "未知型号"}]
    final["possible_model"] = Counter(models).most_common(1)[0][0] if models else ""
    price = estimate_secondhand_price(final)
    return json.dumps({"analysis": final, "price": price, "image_count": len(images)}, ensure_ascii=False)


@tool
def get_brand_liquidity(brand: str) -> str:
    """查询某个雪板品牌的【保值梯队】与保值系数。

    使用场景：用户泛泛问某品牌保不保值、掉不掉价，不涉及具体某块板、也没有图片时调用。
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
    """查询某品牌/型号在二手平台（闲鱼）的真实【挂牌价】行情，用于交叉验证估价。

    数据来自预抓取的闲鱼行情快照（挂牌价，非真实成交价，普遍偏高）。
    参数: brand 品牌（英文或中文均可）；model 型号（可空）。
    """
    snap = _load_snapshot()
    listings = snap.get("listings", [])
    b = (brand or "").strip().upper()
    m = (model or "").strip().upper()

    def hit(it):
        text = (str(it.get("brand", "")) + " " + str(it.get("title", ""))).upper()
        if b and b not in text:
            return False
        if m and m not in text:
            return False
        return True

    matches = [it for it in listings if hit(it)] if b else []

    if not matches:
        prices = [it["price"] for it in listings if it.get("price")]
        out = {"source": "闲鱼行情快照", "matched": 0,
               "note": f"快照里暂无『{brand} {model}』的样本。"}
        if prices:
            out["overall_range"] = {"low": min(prices), "median": statistics.median(prices), "high": max(prices)}
            out["overall_sample"] = len(prices)
            out["note"] += "下面是整体二手单板挂牌价范围(仅供参考)。"
        out["snapshot_date"] = snap.get("scraped_at")
        return json.dumps(out, ensure_ascii=False)

    prices = sorted(it["price"] for it in matches if it.get("price"))
    examples = [{"title": it["title"][:42], "price": it["price"], "city": it.get("city")} for it in matches[:3]]
    return json.dumps({
        "source": "闲鱼行情快照（挂牌价，非成交价，普遍偏高，作上界参考）",
        "brand": brand, "matched": len(prices),
        "price_low": prices[0],
        "price_median": statistics.median(prices),
        "price_high": prices[-1],
        "examples": examples,
        "snapshot_date": snap.get("scraped_at"),
    }, ensure_ascii=False)


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
