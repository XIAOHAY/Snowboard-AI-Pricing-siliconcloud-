# -*- coding: utf-8 -*-
"""
文件名：pricing/review_generator.py
状态：深度修复版 (防止 UnboundLocalError 阻断主流程)
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


def generate_expert_review(brand, model, condition_score, price_low, price_high, base_damage, edge_damage):
    # 1. 基础检查
    api_key = os.getenv("SILICONFLOW_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    base_url = "https://api.siliconflow.cn/v1"

    if not api_key:
        return "（系统提示：API Key 未配置，无法生成点评）"

    brand = str(brand).upper() if brand else "UNKNOWN"
    model = str(model).upper() if model else "未知型号"

    # ===========================================
    # 🔥 核心防御机制：显式初始化变量
    # ===========================================
    chat_model = None  # 先占位，防止后面报 "referenced before assignment"

    try:
        # 尝试初始化模型
        chat_model = ChatOpenAI(
            model="Qwen/Qwen2.5-72B-Instruct",
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7
        )
    except Exception as e:
        # 如果初始化失败（比如断网），直接在这里【return】
        # 这样代码就永远不会走到下面用到 chat_model 的地方
        print(f"❌ 模型初始化失败: {e}")
        return f"（专家连接失败，无法点评。错误: {e}）"

    # ===========================================
    # 2. 执行生成 (只有 chat_model 活着才会走到这)
    # ===========================================
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