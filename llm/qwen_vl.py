# -*- coding: utf-8 -*-
"""
文件名：llm/qwen_vl.py
状态：SiliconCloud 迁移版 (OpenAI 协议兼容)
"""
import os
import base64
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 1. 配置 SiliconCloud
# 建议在 secrets 或 .env 中将变量名改为 SILICONFLOW_API_KEY
api_key = os.getenv("SILICONFLOW_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
base_url = "https://api.siliconflow.cn/v1"

client = OpenAI(api_key=api_key, base_url=base_url)


# 辅助函数：图片转 Base64 (解决云端路径问题)
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def clean_json_text(text: str) -> str:
    if not text: return ""
    return text.strip().replace("```json", "").replace("```", "").strip()


# 复用你原来的 Prompt，不需要改动
DEFAULT_PROMPT = """
你是一名极其严苛的二手滑雪板鉴定专家。你的任务是根据图片客观描述损伤，并依据严格标准进行评分。
【重要提示】
1. 图片中可能包含竖排、旋转或艺术字体的 LOGO，请仔细辨认。
2. **注意区分通用词与品牌**：例如 "GRAY", "RIDE", "SIGNAL", "YES", "FLOW" 在这里是【品牌名】，而不是普通单词。
3. 请忽略水印文字（如“闲鱼”、“小红书”等）。

【已知品牌列表参考】
BURTON, SALOMON, CAPITA, NITRO, K2, RIDE, ROME SDS, JONES, LIB TECH, GNU, 
GRAY, OGASAKA, BC STREAM, MOSS, GENTEMSTICK, YONEX, 011 ARTISTIC, RICE28,
BATALEON, LOBSTER, ARBOR, DC, HEAD, FLOW, FLUX, UNION, NIDECKER, YES,
NOBADAY, VECTOR, REV, TERROR.
【第一步：强制视觉推理】
在输出 JSON 之前，你必须先在心中（或作为"thinking"字段）确认以下细节：
1. **板面 (Top sheet)**：是否有边缘崩裂(Chipping)？固定器安装区是否有压痕？
2. **板底 (Base)**：是否有露芯深划痕(Core Shot)？还是仅仅是发丝痕(Hairline)？
3. **板刃 (Edge)**：是否有断裂？是否有锈迹（浮锈还是腐蚀）？

【第二步：严格评分标准 (Rubric)】
请完全按照以下标准打分，禁止自由发挥：
- **9-10分**：充新。仅有极其轻微的使用痕迹，无肉眼可见划痕。
- **7-8分**：良好。板面有少量轻微划痕，板刃无锈或仅有浮锈，板底无深伤。
- **5-6分**：伊拉克成色。板面边缘有崩裂，板底有明显划痕但未漏芯，板刃有锈。
- **1-4分**：报废。板刃断裂、板底漏芯、板层开裂。

【第三步：输出格式】
请输出且仅输出以下 JSON 格式：
{
  "reasoning": "一句话描述你看到的损伤证据（例如：板头左侧有明显的边缘崩裂，板底有两条浅划痕）",
  "brand": "品牌英文大写 (例如 BURTON)",
  "possible_model": "型号猜测",
  "condition_score": "1-10的整数",
  "base_damage": "板底具体损伤 (无/轻微/严重)",
  "edge_damage": "板刃具体损伤 (无/浮锈/腐蚀/断裂)",
  "can_use": true
  "is_old_model": true 或 false (判断依据：板面设计风格是否陈旧，或者明显的旧款LOGO。如果无法判断，返回 false),
}
"""



def analyze_snowboard_image(image_path: str, user_hint: str = None) -> dict:
    # 动态构建 Prompt 逻辑保留不变
    final_prompt = DEFAULT_PROMPT
    if user_hint and user_hint.strip():
        final_prompt += f"\n【用户额外提示】\n用户指出：{user_hint}..."

    # 图片转 Base64
    base64_image = encode_image(image_path)

    max_retries = 3

    for attempt in range(max_retries):
        try:
            print(f"🚀 [SiliconCloud] 调用 Qwen2-VL-72B (第 {attempt + 1} 次)...")

            response = client.chat.completions.create(
                model="Qwen/Qwen2-VL-72B-Instruct",  # 🔥 核心修改：使用硅基流动的模型ID
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": final_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ],
                    }
                ],
                temperature=0.01,  # 保持理性
                top_p=0.1,
                max_tokens=1024
            )

            raw_text = response.choices[0].message.content
            print("✅ 模型返回成功")

            # 解析 JSON
            clean_text = clean_json_text(raw_text)
            return json.loads(clean_text)

        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            time.sleep(2)

    return {"brand": "UNKNOWN", "error": "NETWORK_ERROR", "can_use": True, "condition_score": 5}