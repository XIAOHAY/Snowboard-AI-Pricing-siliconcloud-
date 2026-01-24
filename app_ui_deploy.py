# -*- coding: utf-8 -*-
"""
文件名：app_ui_deploy.py
状态：最终完整版 (两列布局 + 多图演示 + 结果回显 + 自动定价修正)
"""
import streamlit as st
import pandas as pd
import os
import sys
import tempfile
import json
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==========================================
# 1. 核心逻辑导入
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from llm.qwen_vl import analyze_snowboard_image
    from utils.analysis_merge import merge_analysis_results
    from pricing.pricing_engine import estimate_secondhand_price
    from pricing.review_generator import generate_expert_review
    from llm.chat_service import get_follow_up_answer
except ImportError as e:
    st.error(f"模块导入失败: {e}. 请确保文件结构正确。")
    st.stop()

# ==========================================
# 2. 页面配置 & 密钥自动加载
# ==========================================
st.set_page_config(page_title="AI 雪板鉴定 Pro", page_icon="🏂", layout="wide")

st.title("🏂 AI 二手雪板智能定价系统 (Online Demo)")
st.caption("💡 这是一个在线演示版本，支持 AI 视觉鉴定、价格计算及多轮对话。")

with st.sidebar:
    st.title("🔧 配置")
    # 自动加载 Secrets
    if "DASHSCOPE_API_KEY" in st.secrets:
        st.success("✅ 云端密钥已自动加载")
        api_key = st.secrets["DASHSCOPE_API_KEY"]
    elif os.getenv("DASHSCOPE_API_KEY"):
        st.success("✅ 本地环境变量已加载")
        api_key = os.getenv("DASHSCOPE_API_KEY")
    else:
        api_key = st.text_input("请输入阿里云 DashScope API Key", type="password")
        if not api_key:
            st.warning("⚠️ 请输入 Key 继续")
            st.stop()

    os.environ["DASHSCOPE_API_KEY"] = api_key
    os.environ["SNOWBOARD_API_KEYS"] = api_key

# 初始化状态
if "current_data" not in st.session_state:
    st.session_state.current_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==========================================
# 3. 定义加载动画 HTML
# ==========================================
LOADING_HTML = """
<style>
    .loading-overlay {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.4); display: flex; justify-content: center; align-items: center; z-index: 99999;
    }
    .glass-card {
        position: relative; width: 35vw; min-width: 320px; max-width: 500px; padding: 40px 20px;
        background: rgba(30, 30, 30, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 20px; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
        display: flex; flex-direction: column; align-items: center; color: #ffffff; font-family: sans-serif; text-align: center;
    }
    .stage-container { position: relative; width: 270px; height: 370px; display: flex; justify-content: center; align-items: center; margin-bottom: 20px; }
    .center-obj { position: absolute; width: 110px; z-index: 10; content: url('https://raw.githubusercontent.com/XIAOHAY/Snowboard-AI-Pricing/main/img/snowboard.png'); }
    .orbit-container { position: absolute; width: 100%; height: 100%; z-index: 20; will-change: transform; transform: translateZ(0); animation: orbit-spin 5s linear infinite; }
    .dwarf-artisan { position: absolute; top: 15px; left: 50%; width: 80px; margin-left: -40px; will-change: transform; transform: translateZ(0); backface-visibility: hidden; animation: counter-spin 5s linear infinite; content: url('https://raw.githubusercontent.com/XIAOHAY/Snowboard-AI-Pricing/main/img/dwarf.png'); }
    .loading-text { font-size: 1.4rem; font-weight: bold; letter-spacing: 1px; margin-bottom: 8px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
    .sub-text { font-size: 0.9rem; color: #dddddd; line-height: 1.4; }
    @keyframes orbit-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    @keyframes counter-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(-360deg); } }
</style>
<div class="loading-overlay">
    <div class="glass-card">
        <div class="stage-container"><img class="center-obj"><div class="orbit-container"><img class="dwarf-artisan"></div></div>
        <div class="loading-text">⚒️ 宗师鉴定中...</div>
        <div class="sub-text">AI 正在进行多模态融合分析<br>请稍候片刻</div>
    </div>
</div>
"""

# ==========================================
# 4. 核心页面逻辑
# ==========================================
tab1, tab2 = st.tabs(["📷 鉴定与咨询", "ℹ️ 关于项目"])

with tab1:
    loading_placeholder = st.empty()

    # --- A. 输入区 (无数据时显示) ---
    if not st.session_state.current_data:

        # 🔥 采用两列布局：左侧上传，右侧演示
        col_upload, col_demo = st.columns([1, 1], gap="large")

        # -------------------------------------------------------
        # 左侧：用户上传
        # -------------------------------------------------------
        with col_upload:
            st.subheader("📤 上传照片")
            st.caption("已有照片？直接上传体验 AI 鉴定。")
            user_hint = st.text_input("💡 (选填) 线索提示", placeholder="例如：Gray Desperado...")
            uploaded_files = st.file_uploader("点击或拖拽上传", type=['jpg', 'png'], accept_multiple_files=True)

            if st.button("🚀 开始分析", type="primary", use_container_width=True):
                if uploaded_files:
                    loading_placeholder.markdown(LOADING_HTML, unsafe_allow_html=True)
                    try:
                        # 1. 视觉分析
                        analysis_results = []
                        for uploaded_file in uploaded_files:
                            suffix = os.path.splitext(uploaded_file.name)[1]
                            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                                tmp.write(uploaded_file.read())
                                temp_path = tmp.name
                            try:
                                res = analyze_snowboard_image(temp_path, user_hint=user_hint)
                                analysis_results.append(res)
                            finally:
                                os.remove(temp_path)

                        # 2. 逻辑计算
                        if analysis_results:
                            final_analysis = merge_analysis_results(analysis_results)
                            price_result = estimate_secondhand_price(final_analysis)
                            p_low = price_result.get("price_low", 0)
                            p_high = price_result.get("price_high", 0)
                            expert_comment = generate_expert_review(
                                brand=final_analysis.get("brand"),
                                model=final_analysis.get("possible_model"),
                                condition_score=final_analysis.get("condition_score"),
                                price_low=p_low, price_high=p_high,
                                base_damage=final_analysis.get("base_damage"),
                                edge_damage=final_analysis.get("edge_damage")
                            )

                            st.session_state.current_data = {
                                "suggest_price": int((p_low + p_high) / 2),
                                "price_low": p_low,
                                "price_high": p_high,
                                "expert_review": expert_comment,
                                "brand": final_analysis.get("brand"),
                                "model": final_analysis.get("possible_model"),
                                "condition_score": final_analysis.get("condition_score"),
                                "base_damage": final_analysis.get("base_damage"),
                                "edge_damage": final_analysis.get("edge_damage"),
                                "calculation_process": price_result.get("calculation_process", [])
                            }
                            loading_placeholder.empty()
                            st.rerun()
                        else:
                            loading_placeholder.empty()
                            st.error("未能识别图片内容")
                    except Exception as e:
                        loading_placeholder.empty()
                        st.error(f"运行出错: {e}")

        # -------------------------------------------------------
        # 右侧：一键演示 (多图版)
        # -------------------------------------------------------
        with col_demo:
            st.subheader("⚡️ 一键体验")
            st.caption("没有照片？点击下方案例，体验多视图融合分析。")

            # 1. 定义演示配置 (3张图/案例)
            DEMO_CASES = {
                "demo_good": {
                    "label": "✨ 挑战：热门保值神板",
                    "paths": ["./examples/good_top.jpg", "./examples/good_base.jpg", "./examples/good_edge.jpg"],
                    "desc": "热门准新款",
                    "force_brand": "BURTON", "force_model": "BURTON Good Company龙年限定", "hint": "Burton Good Company龙年限定"
                },
                "demo_bad": {
                    "label": "🥊 挑战：识别严重损伤",
                    "paths": ["./examples/bad_top.jpg", "./examples/bad_base.jpg", "./examples/bad_detail.jpg"],
                    "desc": "板底严重划痕 (多角度)",
                    "force_brand": "Burton", "force_model": "custom", "hint": "Burton Custom , heavy scratch"
                },
                "demo_old": {
                    "label": "🔍 鉴定日系经典",
                    "paths": ["./examples/old_top.jpg", "./examples/old_base.jpg", "./examples/old_logo.jpg"],
                    "desc": "老牌保值款",
                    "force_brand": "ogasaka", "force_model": "fcs", "hint": "ogasaka fcs 2526新款"
                }
            }


            # 2. 演示运行函数
            def run_demo_analysis(case_key):
                cfg = DEMO_CASES[case_key]
                image_paths = cfg["paths"]

                # 展示底图
                with st.container():
                    st.markdown(f"### 🖼️ 正在分析：{cfg['desc']}")
                    cols = st.columns(len(image_paths))
                    for idx, col in enumerate(cols):
                        with col:
                            if os.path.exists(image_paths[idx]):
                                st.image(image_paths[idx], caption=f"视图 {idx + 1}", use_container_width=True)
                    st.info("⚡️ 演示模式：正在对 3 张视图进行【多模态融合分析】...")

                loading_placeholder.markdown(LOADING_HTML, unsafe_allow_html=True)

                try:
                    analysis_results = []
                    # 循环分析每一张图
                    for img_path in image_paths:
                        if os.path.exists(img_path):
                            res = analyze_snowboard_image(img_path, user_hint=cfg["hint"])
                            # 🔥 强制修正品牌/型号 (保留 AI 的成色判断)
                            res["brand"] = cfg["force_brand"]
                            res["possible_model"] = cfg["force_model"]
                            analysis_results.append(res)

                    if analysis_results:
                        final_analysis = merge_analysis_results(analysis_results)
                        price_result = estimate_secondhand_price(final_analysis)
                        p_low = price_result.get("price_low", 0)
                        p_high = price_result.get("price_high", 0)
                        expert_comment = generate_expert_review(
                            brand=final_analysis.get("brand"),
                            model=final_analysis.get("possible_model"),
                            condition_score=final_analysis.get("condition_score"),
                            price_low=p_low, price_high=p_high,
                            base_damage=final_analysis.get("base_damage"),
                            edge_damage=final_analysis.get("edge_damage")
                        )
                        st.session_state.current_data = {
                            "suggest_price": int((p_low + p_high) / 2),
                            "price_low": p_low,
                            "price_high": p_high,
                            "expert_review": expert_comment,
                            "brand": final_analysis.get("brand"),
                            "model": final_analysis.get("possible_model"),
                            "condition_score": final_analysis.get("condition_score"),
                            "base_damage": final_analysis.get("base_damage"),
                            "edge_damage": final_analysis.get("edge_damage"),
                            "calculation_process": price_result.get("calculation_process", []),
                            "demo_image_paths": image_paths  # 👈 记录图片路径用于回显
                        }
                        loading_placeholder.empty()
                        st.rerun()
                    else:
                        loading_placeholder.empty()
                        st.error("未能加载演示图片，请检查文件路径")
                except Exception as e:
                    loading_placeholder.empty()
                    st.error(f"演示运行失败: {e}")


            # 3. 渲染按钮 (卡片式布局)
            for key, cfg in DEMO_CASES.items():
                # 检查第一张图是否存在，作为封面
                cover_img = cfg["paths"][0]
                if os.path.exists(cover_img):
                    with st.container():
                        c_img, c_btn = st.columns([1, 2])
                        with c_img:
                            st.image(cover_img, use_container_width=True)
                        with c_btn:
                            st.markdown(f"**{cfg['desc']}**")
                            if st.button(cfg['label'], key=key, use_container_width=True):
                                run_demo_analysis(key)
                        st.divider()
                else:
                    st.warning(f"⚠️ 图片缺失: {cover_img} (请检查 examples 文件夹)")

    # --- B. 结果展示区 (有数据时显示) ---
    else:
        data = st.session_state.current_data

        # 顶部导航
        col_back, col_space = st.columns([1, 5])
        with col_back:
            if st.button("⬅️ 测下一块"):
                st.session_state.current_data = None
                st.session_state.chat_history = []
                st.rerun()

        st.divider()
        st.success("✅ 鉴定完成")

        # 🔥 多图回显逻辑
        if "demo_image_paths" in data:
            with st.expander("📷 查看分析底图 (3视图)", expanded=True):
                paths = data["demo_image_paths"]
                cols = st.columns(len(paths))
                for idx, col in enumerate(cols):
                    with col:
                        if os.path.exists(paths[idx]):
                            st.image(paths[idx], use_container_width=True, caption=f"视图 {idx + 1}")
                st.info(
                    f"💡 **AI 综合分析结论：** 品牌锁定 `{data.get('brand')}` | 成色评分 `{data.get('condition_score')}` | 损伤检测 `{data.get('base_damage')}`")

        # 1. 价格看板
        c1, c2, c3 = st.columns(3)
        c1.metric("📉 最低", f"¥{data.get('price_low', 0)}")
        c2.metric("🏷️ 均价", f"¥{data.get('suggest_price', 0)}")
        c3.metric("📈 最高", f"¥{data.get('price_high', 0)}")

        st.info(f"🗣️ **专家点评**：{data.get('expert_review', '暂无')}")

        # 2. 手动纠错
        st.markdown("---")
        with st.expander("🛠️ 识别错了？点这里修正品牌/型号", expanded=False):
            with st.form("fix_form"):
                col_a, col_b, col_c = st.columns(3)
                new_brand = col_a.text_input("品牌", value=data.get('brand', ''))
                new_model = col_b.text_input("型号", value=data.get('model', ''))
                new_score = col_c.slider("成色", 1.0, 10.0, float(data.get('condition_score', 8.0)))

                if st.form_submit_button("🔄 修正并重新估价"):
                    with st.spinner("正在重算..."):
                        try:
                            new_analysis = {
                                "brand": new_brand, "possible_model": new_model, "condition_score": new_score,
                                "can_use": True, "base_damage": data.get("base_damage", "用户修正"),
                                "edge_damage": data.get("edge_damage", "用户修正"), "is_old_model": False
                            }
                            new_price_res = estimate_secondhand_price(new_analysis)
                            p_low = new_price_res.get("price_low", 0)
                            p_high = new_price_res.get("price_high", 0)
                            new_review = generate_expert_review(
                                brand=new_brand, model=new_model, condition_score=new_score,
                                price_low=p_low, price_high=p_high,
                                base_damage=data.get("base_damage"), edge_damage=data.get("edge_damage")
                            )
                            # 保持 demo_image_paths 不丢失
                            updated_data = {
                                "brand": new_brand, "model": new_model, "condition_score": new_score,
                                "price_low": p_low, "price_high": p_high,
                                "suggest_price": int((p_low + p_high) / 2),
                                "expert_review": new_review,
                                "calculation_process": new_price_res.get("calculation_process", [])
                            }
                            st.session_state.current_data.update(updated_data)
                            st.session_state.chat_history = []
                            st.toast("数据已修正！", icon="✅")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"修正失败: {e}")

        # 3. 聊天区
        st.divider()
        st.subheader("💬 咨询专家")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("有疑问？问问老炮儿..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    ans = get_follow_up_answer(prompt, data)
                    st.write(ans)
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})

with tab2:
    st.markdown("### 👨‍💻 关于项目\n基于 LangChain + Qwen-VL 的多模态二手雪板定价系统。")