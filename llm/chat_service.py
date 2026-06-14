# -*- coding: utf-8 -*-
"""
文件名：llm/chat_service.py
状态：SiliconCloud 适配版 · config 集中配置版
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import get_api_key, BASE_URL, CHAT_MODEL

load_dotenv()


def get_follow_up_answer(user_question: str, appraisal_context: dict):
    api_key = get_api_key()
    base_url = BASE_URL

    if not api_key:
        return "API Key 缺失。"

    try:
        chat_model = ChatOpenAI(
            model=CHAT_MODEL,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7
        )

        context_str = f"""
        品牌：{appraisal_context.get('brand')}
        型号：{appraisal_context.get('model')}
        成色：{appraisal_context.get('condition_score')}
        估价：{appraisal_context.get('price_low')} - {appraisal_context.get('price_high')}
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是刚才给出估价报告的‘雪圈毒舌老炮’。请基于商品详情回答用户疑问。"),
            ("user", "【商品详情】：{context_str}\n\n【用户疑问】：{question}")
        ])

        chain = prompt | chat_model | StrOutputParser()

        return chain.invoke({
            "context_str": context_str,
            "question": user_question
        })

    except Exception as e:
        return f"（对话服务暂时不可用: {e}）"
