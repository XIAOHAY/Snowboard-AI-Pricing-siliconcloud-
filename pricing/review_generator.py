# -*- coding: utf-8 -*-
"""
文件名：pricing/review_generator.py
状态：config 集中配置 + 档位动态选模型版（点评用当前档位的文本模型）。
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import get_api_key, BASE_URL, get_review_model

load_dotenv()


def generate_expert_review(brand, model, condition_score, price_low, price_high, base_damage, edge_damage):
    api_key = get_api_key()
    base_url = BASE_URL

    if not api_key:
        return "（系统提示：API Key 未配置，无法生成点评）"

    brand = str(brand).upper() if brand else "UNKNOWN"
    model = str(model).upper() if model else "未知型号"

    chat_model = None  # 先占位，防止后面报 "referenced before assignment"

    try:
        chat_model = ChatOpenAI(
            model=get_review_model(),
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7
        )
    except Exception as e:
        print(f"❌ 模型初始化失败: {e}")
        return f"（专家连接失败，无法点评。错误: {e}）"

    try:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "你是一名有15年雪龄的‘雪圈毒舌老炮’鉴定师。风格：专业、犀利、稍微带点调侃。"),
            ("user", """
            请根据以下数据，写一段 100 字左右的二手交易点评。

            【数据】
            - 品牌：{brand}
            - 型号：{model}
            - 成色：{condition_score}/10
            - 损伤：{base_damage} / {edge_damage}
            - 估价：¥{price_low} - ¥{price_high}

            【要求】
            1. 解释为什么值这个价。
            2. 给出购买建议。
            """)
        ])

        chain = prompt_template | chat_model | StrOutputParser()

        return chain.invoke({
            "brand": brand,
            "model": model,
            "condition_score": condition_score,
            "base_damage": base_damage,
            "edge_damage": edge_damage,
            "price_low": price_low,
            "price_high": price_high
        })

    except Exception as e:
        print(f"❌ 生成过程报错: {e}")
        return f"（点评生成中断: {e}）"
