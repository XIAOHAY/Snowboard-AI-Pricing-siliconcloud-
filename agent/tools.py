# -*- coding: utf-8 -*-
"""
文件名：agent/tools.py
作用：把你现有的"感知/决策/知识"能力封装成 LangChain 工具(tool)，
     让 Agent 可以根据用户意图自主决定调用哪个，而不是写死流水线。

依赖现有模块（无需改动它们）：
    llm/qwen_vl.py          -> analyze_snowboard_image()
    pricing/pricing_engine  -> estimate_secondhand_price() 及品牌梯队表
"""
import os
import json
from langchain_core.tools import tool

from llm.qwen_vl import analyze_snowboard_image
from pricing.pricing_engine import (
    estimate_secondhand_price,
    BRAND_TIERS,
    TIER_FACTORS,
    BRAND_NICKNAMES,
)


@tool
def appraise_snowboard(image_path: str, user_hint: str = "") -> str:
    """给一块二手雪板做【成色鉴定 + 确定性估价】。

    使用场景：用户上传了雪板图片，并且想知道这块板值多少钱 / 想卖 / 想买时调用。
    参数:
        image_path: 已保存在本地的雪板图片路径（前端上传后会以 [图片路径: xxx] 形式给你）。
        user_hint:  用户对品牌或型号的额外提示（如"这是小贺的板"），没有就传空字符串。
    返回:
        JSON 字符串，包含视觉鉴定结果(analysis)与价格区间(price)。
    """
    # 感知层：多模态模型看图 -> 结构化特征
    analysis = analyze_snowboard_image(image_path, user_hint or None)
    # 决策层：规则引擎把概率输出转成确定性价格（治理大模型幻觉报价）
    price = estimate_secondhand_price(analysis)
    return json.dumps({"analysis": analysis, "price": price}, ensure_ascii=False)


@tool
def get_brand_liquidity(brand: str) -> str:
    """查询某个雪板品牌的【保值梯队】与保值系数。

    使用场景：用户只是泛泛地问某品牌保不保值、掉不掉价，不涉及具体某块板、也没有图片时调用。
    参数:
        brand: 品牌名，中文绰号或英文均可（如 'Burton'、'菠萝'、'小贺'）。
    """
    raw = brand.strip()
    b = BRAND_NICKNAMES.get(raw, raw).upper()  # 绰号 -> 英文
    tier = BRAND_TIERS.get(b, "TIER_5")
    factor = TIER_FACTORS.get(tier, 0.35)
    desc = {
        "TIER_1": "理财级（Gentemstick等），落地约 75 折，极保值",
        "TIER_2": "日系/高端（Gray/Ogasaka等），落地约 65 折，保值",
        "TIER_3": "国际大牌（Burton/Salomon等），落地约 5 折",
        "TIER_4": "二线品牌（K2/Ride等），较难卖上价",
        "TIER_5": "入门/国产，残值很低",
    }.get(tier, "未知梯队")
    return json.dumps({"brand": b, "tier": tier, "factor": factor, "desc": desc},
                      ensure_ascii=False)


@tool
def search_market_price(brand: str, model: str = "") -> str:
    """联网查询某型号雪板当前的【二手市场在售行情】，用于交叉验证估价是否合理。

    使用场景：已经给出估价后，用户质疑"凭什么这个价" / 想看看市场实际挂多少时调用。
    参数:
        brand: 品牌；model: 型号（可空）。
    返回:
        在售参考价列表（JSON）。
    """
    # =========================================================
    # TODO（接真实数据源）：当前返回示例数据，保证 Agent 闭环可演示。
    # 升级路线（任选其一）：
    #   1) 闲鱼/小红书 搜索结果爬取并结构化
    #   2) SERP / Bright Data / Nimble 等搜索 API
    #   3) 自建一张近期成交价表，先用静态数据兜底
    # =========================================================
    mock_listings = [
        {"platform": "闲鱼", "title": f"{brand} {model} 二手", "price": 2600, "condition": "9成新"},
        {"platform": "闲鱼", "title": f"{brand} {model}", "price": 1980, "condition": "8成新"},
        {"platform": "小红书", "title": f"出 {brand} {model}", "price": 2200, "condition": "95新"},
    ]
    return json.dumps(
        {"source": "MOCK_DATA", "listings": mock_listings,
         "note": "当前为示例数据，尚未接入实时行情；回答时请向用户说明这是参考而非真实成交价"},
        ensure_ascii=False,
    )


@tool
def query_gear_knowledge(question: str) -> str:
    """回答滑雪装备相关的【知识性问题】（保养、选板、参数、术语等），与具体估价无关时调用。

    参数:
        question: 用户的知识性问题。
    """
    # TODO（升级为 RAG）：现在是"把小知识库整段塞进上下文"的最简实现，
    # 后续可替换为 Chroma 向量检索：文档切分 -> embedding -> 相似度召回 Top-K。
    kb_path = os.path.join(os.path.dirname(__file__), "..", "data", "gear_knowledge.md")
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = f.read()
        return f"【装备知识库】可参考以下内容回答用户问题：\n{kb}"
    return "（暂无本地知识库，可用通用常识回答，并提示用户这是常识性建议。）"


# 给 Agent 注册用的工具清单
ALL_TOOLS = [
    appraise_snowboard,
    get_brand_liquidity,
    search_market_price,
    query_gear_knowledge,
]
