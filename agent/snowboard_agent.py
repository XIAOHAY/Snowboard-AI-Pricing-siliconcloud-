# -*- coding: utf-8 -*-
"""
文件名：agent/snowboard_agent.py
作用：tool-calling Agent —— bind_tools + 手写工具调用循环 + 用量埋点。
     多图：本轮上传图片通过 set_pending_images 放进工具上下文，模型只决定"要不要估价"。
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from agent.tools import ALL_TOOLS, set_pending_images
from config import get_api_key, BASE_URL, get_agent_model
from utils import usage

load_dotenv()

SYSTEM_PROMPT = """你是「雪圈毒舌老炮」——一名有 15 年雪龄的二手雪板鉴定师。风格：专业、犀利、带点调侃。

你有以下工具，必须根据用户意图【自主判断】调用哪个、是否调用：

- appraise_snowboard：用户上传了雪板图片且想估价/想卖/想买这块板时用。
  直接调用即可——工具会自动读取用户已上传的图片（可能多张，会自动融合），你不需要传任何路径。
- search_market_price：已经给出估价后，用户质疑价格、或想看市场实际挂价时用，用来交叉验证。
- get_brand_liquidity：用户只是泛泛问某品牌保不保值、掉不掉价，不针对某块具体的板时用。
- query_gear_knowledge：用户问保养、选板、术语等知识性问题时用。

工作规则：
1. 不要无脑调用工具。纯闲聊、或你能直接答的常识，就直接回答，别硬凑工具。
2. 消息里【没有“已上传N张图片”标记】时，绝不调用 appraise_snowboard，而是提示用户先上传雪板照片。
3. 调用工具拿到结果后，用"老炮"口吻把结论讲明白，并解释价格/判断是怎么来的。
4. 诚实第一：search_market_price 返回的是示例数据时，要说明这是参考行情、不是实时真实成交价。
"""

_TOOL_MAP = {t.name: t for t in ALL_TOOLS}
MAX_TOOL_ROUNDS = 6


class SnowboardAgent:
    """极简 tool-calling agent：bind_tools + 手写循环。"""

    def __init__(self, verbose: bool = True):
        api_key = get_api_key()
        if not api_key:
            raise RuntimeError("缺少 API Key，请在 Streamlit Secrets 或 .env 中配置 DASHSCOPE_API_KEY。")
        self.verbose = verbose
        llm = ChatOpenAI(
            model=get_agent_model(),
            openai_api_key=api_key,
            openai_api_base=BASE_URL,
            temperature=0.3,
        )
        self.llm = llm.bind_tools(ALL_TOOLS)

    def run(self, user_text: str, image_paths=None, chat_history: list = None, image_path: str = None) -> str:
        usage.reset()  # 每轮清零用量
        chat_history = chat_history or []
        if image_path and not image_paths:
            image_paths = [image_path]
        image_paths = image_paths or []

        set_pending_images(image_paths)

        user_content = user_text
        if image_paths:
            user_content = f"[用户已上传 {len(image_paths)} 张雪板图片]\n{user_text}"

        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(chat_history) + [HumanMessage(content=user_content)]

        for _ in range(MAX_TOOL_ROUNDS):
            ai_msg: AIMessage = self.llm.invoke(messages)
            messages.append(ai_msg)

            # 用量埋点（Agent 决策/总结这次的 token）
            try:
                um = getattr(ai_msg, "usage_metadata", None) or {}
                usage.record(get_agent_model(), um.get("input_tokens"), um.get("output_tokens"))
            except Exception:
                pass

            tool_calls = getattr(ai_msg, "tool_calls", None) or []
            if not tool_calls:
                return ai_msg.content or "（无内容）"

            for call in tool_calls:
                name = call.get("name")
                args = call.get("args", {})
                if self.verbose:
                    print(f"> Invoking: `{name}` with `{args}`")
                tool = _TOOL_MAP.get(name)
                if tool is None:
                    result = f"（未知工具：{name}）"
                else:
                    try:
                        result = tool.invoke(args)
                    except Exception as e:
                        result = f"（工具 {name} 执行出错：{e}）"
                messages.append(ToolMessage(content=str(result), tool_call_id=call.get("id")))

        return "（已达到最大工具调用轮数，请简化问题再试）"


def build_agent(verbose: bool = True) -> "SnowboardAgent":
    return SnowboardAgent(verbose=verbose)


def run_turn(executor: "SnowboardAgent", user_text: str,
             image_paths=None, chat_history: list = None, image_path: str = None) -> str:
    return executor.run(user_text, image_paths=image_paths, chat_history=chat_history, image_path=image_path)


if __name__ == "__main__":
    ex = build_agent(verbose=True)
    print(run_turn(ex, "Burton 这个牌子的板保值吗？"))
    print("-" * 40)
    print(run_turn(ex, "板底有点浮锈，要紧吗，怎么处理？"))
    print("用量:", usage.summary())
