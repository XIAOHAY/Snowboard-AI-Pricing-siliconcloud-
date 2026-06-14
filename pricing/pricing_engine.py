# -*- coding: utf-8 -*-
"""
文件名：pricing/pricing_engine.py
功能：基于市场调研数据的分级定价引擎 (Market Research Based)
核心逻辑：
估价 = 参考原价 * (成色折旧率 * 品牌保值系数)
"""

import json
import os
from typing import Dict, Any, List

# ==========================================
# 1. 明星型号溢价 (依然需要，针对具体热门款)
# ==========================================
PREMIUM_MODELS = {
    "DOA": 500, "DEFENDERS": 500, "SUPER DOA": 800,
    "CUSTOM": 500, "CUSTOM X": 800,
    "ORCA": 1000, "T.RICE": 600,
    "HUCK KNIFE": 400, "PRO": 500,
    "DESPERADO": 800, "TYPE-R": 1500, "TI": 1000,
    "FC": 800, "CT": 500, "DR": 1200,
    "011": 500, "MANTARAY": 1000
}

# 品牌绰号映射
BRAND_NICKNAMES = {
    "小贺": "OGASAKA", "大灰": "GRAY", "德思板": "GRAY", "BC": "BC STREAM",
    "红树": "ARBOR", "黑树": "ARBOR", "树": "ARBOR", "家庭树": "BURTON",
    "菠萝": "BURTON", "B家": "BURTON", "C家": "CAPITA", "N家": "NITRO",
    "S家": "SALOMON", "黑珍珠": "BLACK PEARL", "杨树林": "YONEX",
    "虎鲸": "LIB TECH"
}

# ==========================================
# 2. 定义品牌保值梯队 (Liquidity Tiers)
# ==========================================
# 这一步决定了“掉价快慢”
TIER_FACTORS = {
    "TIER_1": 0.75, # 理财产品 (Gentemstick): 落地 75 折
    "TIER_2": 0.65, # 日系/高端 (Gray/Ogasaka): 落地 65 折
    "TIER_3": 0.50, # 国际大牌 (Burton/Salomon): 落地 5 折 (除非是当季新款)
    "TIER_4": 0.35, # 二线品牌 (K2/Ride): 很难卖上价
    "TIER_5": 0.20  # 国产/入门: 基本就是送人或几百块
}

# 手动维护品牌所属梯队 (也可以写在 JSON 里，这里写在代码里方便调整)
BRAND_TIERS = {
    "GENTEMSTICK": "TIER_1", "MOSS": "TIER_1", "KESSLER": "TIER_1",
    "OGASAKA": "TIER_2", "BC STREAM": "TIER_2", "GRAY": "TIER_2", "011 ARTISTIC": "TIER_2",
    "BURTON": "TIER_3", "CAPITA": "TIER_3", "SALOMON": "TIER_3", "NITRO": "TIER_3", "JONES": "TIER_3",
    "LIB TECH": "TIER_3",
    "ROME SDS": "TIER_3", "GNU": "TIER_3", "BATALEON": "TIER_3", "NIDECKER": "TIER_3", "YES": "TIER_3", "YONEX": "TIER_2", "RICE28": "TIER_2",
    "K2": "TIER_4", "RIDE": "TIER_4", "DC": "TIER_4", "ARBOR": "TIER_4",
    "ROSSIGNOL": "TIER_4", "HEAD": "TIER_4", "FLOW": "TIER_4", "SIGNAL": "TIER_4", "LOBSTER": "TIER_4", "REV": "TIER_4", "TERROR": "TIER_4",
    "NOBADAY": "TIER_5", "VECTOR": "TIER_5", "DECATHLON": "TIER_5", "UNKNOWN": "TIER_5"
}


# ==========================================
# 3. 数据加载
# ==========================================
def load_original_price_table() -> Dict[str, int]:
    current_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    price_file_path = os.path.join(project_root, "data", "brand_price.json")

    if not os.path.exists(price_file_path):
        return {"BURTON": 4800, "UNKNOWN": 2000}

    clean_data = {}
    try:
        with open(price_file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            for k, v in raw_data.items():
                if not k.startswith("_"):
                    clean_data[k.upper()] = v
        return clean_data
    except Exception:
        return {"UNKNOWN": 2000}


ORIGINAL_PRICE_REF = load_original_price_table()


# ==========================================
# 4. 成色物理折旧 (Physical Depreciation)
# ==========================================
def get_physical_condition_rate(score: float) -> float:
    """
    仅代表物理损耗，不包含品牌因素
    """
    try:
        s = float(score)
    except:
        s = 5.0

    if s >= 9.8:
        return 0.90  # 全新
    elif s >= 9.0:
        return 0.80  # 充新
    elif s >= 8.0:
        return 0.65  # 正常使用 (之前是 0.6 或 0.75，这里取中)
    elif s >= 7.0:
        return 0.50
    elif s >= 6.0:
        return 0.40
    elif s >= 4.0:
        return 0.20
    else:
        return 0.10


# ==========================================
# 5. 主计算函数
# ==========================================
def estimate_secondhand_price(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    # 1. 基础信息
    raw_brand = str(analysis_result.get("brand", "UNKNOWN")).strip().upper()
    raw_model = str(analysis_result.get("possible_model", "")).strip().upper()
    condition_score = analysis_result.get("condition_score", 5)
    can_use = analysis_result.get("can_use", True)

    if not can_use:
        return {"currency": "CNY", "price_low": 0, "price_high": 50, "suggestion": "不建议交易",
                "calculation_process": ["报废板"]}

    # 2. 品牌映射
    brand = raw_brand
    if raw_brand in BRAND_NICKNAMES:
        brand = BRAND_NICKNAMES[raw_brand]

    # 3. 获取参考原价 (Original Price)
    original_price = ORIGINAL_PRICE_REF.get(brand, ORIGINAL_PRICE_REF.get("UNKNOWN", 2000))

    # 4. 确定品牌保值梯队 (Brand Tier)
    tier_name = BRAND_TIERS.get(brand, "TIER_5")  # 默认当入门板处理
    brand_factor = TIER_FACTORS.get(tier_name, 0.35)

    # 5. 计算物理折旧率
    phys_rate = get_physical_condition_rate(condition_score)

    # 6. 计算型号溢价 (Premium)
    model_premium = 0
    hit_model = None
    for keyword, extra in PREMIUM_MODELS.items():
        if keyword in raw_model:
            model_premium = extra
            hit_model = keyword
            break

    # ==========================================
    # 🔥 核心公式：原价 × (物理折旧 × 品牌系数) + 热门款溢价
    # ==========================================
    # 比如: Burton (T3, 0.6) 8成新 (0.7) -> 综合保值率 = 0.6 * 0.7 = 0.42 (4.2折)
    # 这符合调研：国际热门板二手一般在 4-5 折左右

    # 针对成色极好(>9分)的情况，品牌系数的影响应该变小（准新板都很贵）
    # 针对成色差的情况，品牌系数影响变大

    # 修正逻辑：
    final_rate = phys_rate * brand_factor

    # 动态调整：如果是 T3 以上的品牌，且成色好，保值率不能太低
    if tier_name in ["TIER_1", "TIER_2", "TIER_3"] and condition_score >= 8.5:
        final_rate = final_rate * 1.3  # 提权

    # 计算基础估价
    base_estimation = original_price * final_rate
    is_old = analysis_result.get("is_old_model", False)
    if is_old:
        print("Detected Old Model: Applying 40% discount")
        base_estimation = base_estimation * 0.6  # 老款直接打6折
    # 加上溢价
    final_price = base_estimation + model_premium
    final_price = int(final_price)

    # 7. 价格区间
    price_low = int(final_price * 0.9)
    price_high = int(final_price * 1.1)
    price_low = round(price_low, -2)
    price_high = round(price_high, -2)
    if price_low < 100: price_low = 100

    # 8. 记录过程
    steps = []
    steps.append(f"① 参考原价 ({brand}): ¥{original_price}")
    steps.append(f"② 品牌梯队: {tier_name} (保值系数 {brand_factor})")
    steps.append(f"③ 物理成色 ({condition_score}分): 残值率 {phys_rate}")
    steps.append(f"   ➜ 综合折算率: {final_rate:.2f}")
    if hit_model:
        steps.append(f"④ 热门款溢价 ({hit_model}): +¥{model_premium}")
    steps.append(f"⑤ 最终估价: ¥{original_price} × {final_rate:.2f} + {model_premium} = ¥{final_price}")

    return {
        "currency": "CNY",
        "price_low": price_low,
        "price_high": price_high,
        "confidence": 0.85,
        "suggestion": "价格合理" if condition_score >= 6 else "建议议价",
        "calculation_process": steps,
        "pricing_reason": f"基于{brand}原价¥{original_price}及{tier_name}级市场保值率计算。"
    }