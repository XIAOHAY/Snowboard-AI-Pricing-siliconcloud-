# -*- coding: utf-8 -*-
"""
文件名：utils/usage.py
作用：极简用量/成本观测——记录每次 LLM 调用的【模型 + token】，并估算花费。
     reset() 每轮清零；record() 埋点；summary() 汇总。
"""

# 价格表：¥/百万 token，(输入价, 输出价)。⚠️ 请按硅基流动模型广场实际价格填写；未列出的走 _default。
PRICES = {
    "Qwen/Qwen3-VL-8B-Instruct":  (0.0, 0.0),
    "Qwen/Qwen3-VL-32B-Instruct": (1.9, 1.9),
    "Qwen/Qwen3.5-397B-A17B":     (4.13, 4.13),
    "Qwen/Qwen3.5-9B":            (0.0, 0.0),
    "Qwen/Qwen3.5-27B":           (1.0, 1.0),
    "Qwen/Qwen3.6-27B":           (1.0, 1.0),
    "_default":                   (4.13, 4.13),
}

_records = []


def reset():
    _records.clear()


def record(model, in_tokens, out_tokens):
    _records.append({"model": model or "未知", "in": int(in_tokens or 0), "out": int(out_tokens or 0)})


def _cost(model, in_t, out_t):
    pin, pout = PRICES.get(model, PRICES["_default"])
    return (in_t * pin + out_t * pout) / 1_000_000.0


def summary():
    by_model = {}
    for r in _records:
        b = by_model.setdefault(r["model"], {"calls": 0, "in": 0, "out": 0, "cost": 0.0})
        b["calls"] += 1
        b["in"] += r["in"]
        b["out"] += r["out"]
        b["cost"] += _cost(r["model"], r["in"], r["out"])
    total_in = sum(r["in"] for r in _records)
    total_out = sum(r["out"] for r in _records)
    total_cost = sum(b["cost"] for b in by_model.values())
    return {
        "calls": len(_records),
        "total_in": total_in,
        "total_out": total_out,
        "total_tokens": total_in + total_out,
        "cost": total_cost,
        "by_model": by_model,
    }
