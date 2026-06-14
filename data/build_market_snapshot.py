# -*- coding: utf-8 -*-
"""
文件名：data/build_market_snapshot.py
作用：从闲鱼(Goofish)抓取二手单板在售挂牌价，生成/刷新 data/market_snapshot.json。
     这是 search_market_price 真实行情数据的来源（数据管线）。

依赖：pip install apify-client
鉴权：环境变量 APIFY_TOKEN（在 https://console.apify.com/account/integrations 获取）
用法：python data/build_market_snapshot.py
成本：按 Apify 的 zen-studio/goofish-xianyu-search-scraper 计费，summary 模式很便宜（几分钱）。
"""
import os
import json
import datetime

ACTOR = "zen-studio/goofish-xianyu-search-scraper"
KEYWORD = "单板滑雪板"
MAX_ITEMS = 60  # 想要更多样本就调大

# 从标题里识别品牌（命中即归类）
BRAND_KEYWORDS = {
    "BURTON": ["burton", "伯顿"],
    "SALOMON": ["salomon", "萨洛蒙"],
    "CAPITA": ["capita"],
    "NITRO": ["nitro"],
    "NOBADAY": ["nobaday", "小黑板"],
    "JONES": ["jones"],
    "LIB TECH": ["lib tech", "libtech", "虎鲸"],
    "GNU": ["gnu"],
    "K2": ["k2"],
    "RIDE": ["ride"],
    "ROME SDS": ["rome"],
    "BATALEON": ["bataleon"],
    "YONEX": ["yonex", "杨树林"],
    "OGASAKA": ["ogasaka", "小贺"],
    "GRAY": ["gray", "大灰"],
    "BC STREAM": ["bc stream", "bcstream"],
    "COSONE": ["cosone"],
    "PRIME": ["prime"],
    "LOZEN": ["lozen"],
    "NEVERBEENDONE": ["neverbeendone", "nbd"],
}


def detect_brand(title: str) -> str:
    t = (title or "").lower()
    for brand, kws in BRAND_KEYWORDS.items():
        if any(k in t for k in kws):
            return brand
    return "UNKNOWN"


def main():
    from apify_client import ApifyClient
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise SystemExit("缺少 APIFY_TOKEN 环境变量")

    client = ApifyClient(token)
    run = client.actor(ACTOR).call(run_input={
        "keyword": KEYWORD,
        "maxItems": MAX_ITEMS,
        "detailLevel": "summary",
        "sortBy": "relevance",
        "priceMin": 300,
        "quickFilters": ["filterPersonal"],
    })

    listings = []
    for it in client.dataset(run["defaultDatasetId"]).iterate_items():
        price = it.get("price")
        title = it.get("title", "")
        if not price:
            continue
        listings.append({
            "brand": detect_brand(title),
            "title": title[:80],
            "price": price,
            "city": it.get("city"),
            "posted": (it.get("postedAt") or "")[:10],
            "wants": it.get("stats.wants") or it.get("stats", {}).get("wants"),
        })

    snapshot = {
        "source": f"闲鱼 (Goofish) via Apify {ACTOR}",
        "keyword": KEYWORD,
        "filters": "个人闲置, 价格≥300, summary 模式",
        "scraped_at": datetime.date.today().isoformat(),
        "price_type": "挂牌价 (asking price)，非真实成交价，普遍偏高",
        "listings": listings,
    }

    out = os.path.join(os.path.dirname(__file__), "market_snapshot.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"✅ 已写入 {out}，共 {len(listings)} 条")


if __name__ == "__main__":
    main()
