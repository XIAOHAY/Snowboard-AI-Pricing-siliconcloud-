# -*- coding: utf-8 -*-
"""
文件名：eval/run_eval.py
作用：跨【模型档位】评测雪板鉴定——对每个 case 跑感知+定价，对比每档的
     品牌识别准确率 / 估价相对误差 / token / 成本 / 耗时。

用法（仓库根目录下）：
    python eval/run_eval.py
产物：
    eval/report.md   （对比表，可直接贴简历/README）
    eval/results.csv （逐 case 明细）

说明：默认【不喂 hint】，测模型"裸识别"能力；想测带提示的效果把 USE_HINT 改 True。
"""
import os
import sys
import csv
import json
import time

# 让脚本在仓库根目录可被正确导入
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import config
from llm.qwen_vl import analyze_snowboard_image
from utils.analysis_merge import merge_analysis_results
from pricing.pricing_engine import estimate_secondhand_price
from utils import usage

USE_HINT = False  # True = 把 case 里的 hint 喂给视觉模型（测带提示效果）


def load_cases():
    with open(os.path.join(ROOT, "eval", "cases.json"), "r", encoding="utf-8") as f:
        return json.load(f)["cases"]


def brand_ok(pred, truth):
    p = str(pred or "").upper().strip()
    t = str(truth or "").upper().strip()
    if not t:
        return None  # 没标注真值，不计入准确率
    return p == t or (t in p) or (p in t)


def appraise_case(case):
    """对一个 case 跑：每图感知 -> 融合 -> 定价。返回预测与用量。"""
    usage.reset()
    t0 = time.time()
    analyses = []
    for rel in case["images"]:
        path = os.path.join(ROOT, rel)
        hint = case.get("hint") if USE_HINT else None
        analyses.append(analyze_snowboard_image(path, hint))
    final = merge_analysis_results(analyses)
    price = estimate_secondhand_price(final)
    dt = time.time() - t0
    u = usage.summary()
    mid = (price.get("price_low", 0) + price.get("price_high", 0)) / 2
    return {
        "pred_brand": final.get("brand"),
        "pred_low": price.get("price_low", 0),
        "pred_high": price.get("price_high", 0),
        "pred_mid": mid,
        "tokens": u["total_tokens"],
        "cost": u["cost"],
        "latency": dt,
    }


def evaluate():
    cases = load_cases()
    rows = []
    for tier in config.TIERS:
        config.set_active_tier(tier)
        vl = config.get_vl_model()
        print(f"\n===== 档位：{tier}（视觉 {vl}）=====")
        for case in cases:
            try:
                r = appraise_case(case)
            except Exception as e:
                print(f"  [{case['id']}] 出错: {e}")
                continue
            fair = case.get("fair_price") or 0
            err_pct = abs(r["pred_mid"] - fair) / fair if fair else None
            ok = brand_ok(r["pred_brand"], case.get("true_brand"))
            rows.append({
                "tier": tier, "vl_model": vl, "case": case["id"],
                "true_brand": case.get("true_brand"), "pred_brand": r["pred_brand"],
                "brand_ok": ok, "fair_price": fair,
                "pred_mid": round(r["pred_mid"]), "err_pct": err_pct,
                "tokens": r["tokens"], "cost": r["cost"], "latency": round(r["latency"], 1),
            })
            ok_str = "✓" if ok else ("—" if ok is None else "✗")
            ep = f"{err_pct*100:.0f}%" if err_pct is not None else "—"
            print(f"  [{case['id']}] 品牌 {r['pred_brand']}({ok_str}) | 估价¥{round(r['pred_mid'])} 误差{ep} | {r['tokens']}tok ≈¥{r['cost']:.4f}")
    return rows


def compute_metrics(rows):
    """按档位汇总（纯函数，便于单测）。"""
    by_tier = {}
    for r in rows:
        b = by_tier.setdefault(r["tier"], {"n": 0, "brand_ok": 0, "brand_n": 0,
                                           "err_sum": 0.0, "err_n": 0, "tok": 0, "cost": 0.0, "lat": 0.0})
        b["n"] += 1
        if r["brand_ok"] is not None:
            b["brand_n"] += 1
            b["brand_ok"] += 1 if r["brand_ok"] else 0
        if r["err_pct"] is not None:
            b["err_sum"] += r["err_pct"]
            b["err_n"] += 1
        b["tok"] += r["tokens"]
        b["cost"] += r["cost"]
        b["lat"] += r["latency"]
    out = {}
    for tier, b in by_tier.items():
        out[tier] = {
            "brand_acc": (b["brand_ok"] / b["brand_n"]) if b["brand_n"] else None,
            "avg_err": (b["err_sum"] / b["err_n"]) if b["err_n"] else None,
            "avg_tokens": round(b["tok"] / b["n"]) if b["n"] else 0,
            "total_cost": b["cost"],
            "avg_latency": (b["lat"] / b["n"]) if b["n"] else 0,
            "n": b["n"],
        }
    return out


def render_report(metrics):
    lines = ["# 模型档位评测对比\n",
             "| 档位 | 品牌识别准确率 | 估价平均相对误差 | 平均token | 总成本(估) | 平均耗时 |",
             "| --- | --- | --- | --- | --- | --- |"]
    for tier, m in metrics.items():
        acc = f"{m['brand_acc']*100:.0f}%" if m["brand_acc"] is not None else "—"
        err = f"{m['avg_err']*100:.0f}%" if m["avg_err"] is not None else "—"
        lines.append(f"| {tier} | {acc} | {err} | {m['avg_tokens']} | ¥{m['total_cost']:.4f} | {m['avg_latency']:.1f}s |")
    lines.append("\n> 误差 = |估价中值 − 合理价| / 合理价，越低越准。成本为估算（价格表见 utils/usage.py）。")
    return "\n".join(lines)


def main():
    rows = evaluate()
    if not rows:
        print("没有结果，请检查 eval/cases.json 和图片路径。")
        return
    # 写 CSV 明细
    csv_path = os.path.join(ROOT, "eval", "results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # 写报告
    metrics = compute_metrics(rows)
    report = render_report(metrics)
    with open(os.path.join(ROOT, "eval", "report.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print("\n" + report)
    print(f"\n✅ 明细已存 {csv_path}，报告已存 eval/report.md")


if __name__ == "__main__":
    main()
