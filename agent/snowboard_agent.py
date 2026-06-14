# -*- coding: utf-8 -*-
"""
文件名：agent/snowboard_agent.py
作用：构建一个 tool-calling（函数调用）Agent。
     核心变化：从"传图→估价→点评"的写死流水线，升级为"模型自主决定调用哪个工具"。

模型：SiliconFlow 的 Qwen2.5-72B-Instruct（OpenAI 协议兼容，支持 function calling）。
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

from agent.tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = """你是「雪圈毒舌老炮」——一名有 15 年雪龄的二手雪板鉴定师。风格：专业、犀利、带点调侃。

你有以下工具，必须根据用户意图【自主判断】调用哪个、是否调用：

- appraise_snowboard：用户上传了雪板图片且想估价/想卖/想买这块板时用。
  图片路径会在用户消息里以 [图片路径: xxx] 的形式给你，把它作为 image_path 传入。
- search_market_price：已经给出估价后，用户质疑价格、或想看市场实际挂价时用，用来交叉验证。
- get_brand_liquidity：用户只是泛泛问某品牌保不保值、掉不掉价，不针对某块具体的板时用。
- query_gear_knowledge：用户问保养、选板、术语等知识性问题时用。

工作规则：
1. 不要无脑调用工具。纯闲聊、或你能直接答的常识，就直接回答，别硬凑工具。
2. 消息里【没有图片路径】时，绝不调用 appraise_snowboard，而是提示用户先上传雪板照片。
3. 调用工具拿到结果后，用"老炮"口吻把结论讲明白，并解释价格/判断是怎么来的。
4. 诚实第一：search_market_price 返回的是示例数据时，要说明这是参考行情、不是实时真实成交价。
"""


def build_agent(verbose: bool = True) -> AgentExecutor:
    """构建并返回一个可执行的 Agent。"""
    api_key = os.getenv("SILICONFLOW_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 SILICONFLOW_API_KEY，请在 .env 中配置。")

    llm = ChatOpenAI(
        model="Qwen/Qwen2.5-72B-Instruct",
        openai_api_key=api_key,
        openai_api_base="https://api.siliconflow.cn/v1",
        temperature=0.3,  # Agent 决策要稳一点，别太发散
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),  # 工具调用的中间步骤
    ])

    agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=verbose,
        handle_parsing_errors=True,  # 工具/解析出错时兜底，不直接崩
        max_iterations=6,            # 防止 Agent 死循环
    )


def run_turn(executor: AgentExecutor, user_text: str,
             image_path: str = None, chat_history: list = None) -> str:
    """跑一轮对话。

    image_path：本轮如果用户上传了图片，把保存后的本地路径传进来；
                函数会把它拼进输入，Agent 据此决定是否调用 appraise_snowboard。
    chat_history：LangChain message 列表，用于多轮记忆。
    """
    chat_history = chat_history or []
    user_input = user_text
    if image_path:
        user_input = f"[图片路径: {image_path}]\n{user_text}"
    result = executor.invoke({"input": user_input, "chat_history": chat_history})
    return result["output"]


# 命令行快速自测（无图：测品牌问答 / 知识问答）
if __name__ == "__main__":
    ex = build_agent(verbose=True)
    print(run_turn(ex, "Burton 这个牌子的板保值吗？"))
    print("-" * 40)
    print(run_turn(ex, "板底有点浮锈，要紧吗，怎么处理？"))
