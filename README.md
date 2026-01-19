# 🏂 雪板智能鉴定与定价系统 (Snowboard AI Pricing)

### 🔗 [在线 Demo 体验链接](https://snowboard-ai-pricing-7z2pajzoiem3eencx2blbm.streamlit.app/)

---

## 🌟 项目背景

在二手雪板交易市场中，非标品的“成色鉴定”与“价格评估”长期存在主观性强、价格混乱的问题。本项目通过 **多模态大模型 (LVM)** 结合 **规则定价引擎**，为用户提供一套标准化、透明化的雪板评估方案。

## 🚀 核心功能

* **多维视觉特征提取**：识别雪板品牌、型号，并精准捕捉板底划痕、边缘损伤及板刃锈迹等细微特征。
* **多图决策融合算法**：支持“板面、板底、细节”三视图并行分析，通过投票机制过滤识别噪点，模拟专家全方位检视。
* **确定性定价引擎**：自研折旧算法模型，将 AI 的概率输出转化为确定性价格区间，彻底解决大模型的“幻觉”报价问题。
* **专家级点评与追问**：利用 **LangChain** 构建“雪圈老炮”人格，生成犀利专业的鉴定报告，并支持基于当前鉴定上下文的实时问答。
* **场景化演示模式**：内置“热门保值”、“战损识别”、“日系老款”三大演示案例，确保在任何网络环境下都能 100% 呈现核心业务逻辑。

---

## 🛠️ 技术架构：感知与决策分离

本项目采用了 **感知层 (AI) 与 决策层 (Logic) 解耦** 的混合智能架构：

1. **感知层 (Perception)**：使用 `Qwen-VL-Max` 提取非结构化特征（成色评分、损伤描述）。
2. **决策层 (Decision)**：由 Python 逻辑引擎根据品牌梯队系数（Tier Factors）和物理折旧曲线计算最终估价。
3. **交互层 (Interaction)**：使用 `Streamlit` 构建响应式 Web UI，并注入 GPU 加速的 CSS 动画优化加载体验。

---

## 📈 痛点攻克 (Problem Solving)

* **非确定性 (Non-determinism) 治理**：
* 针对同一图片重复上传结果差异大的问题，通过将 `temperature` 调优至极低值 (0.01) 并引入 **评分锚点 (Rubric)** 提示词策略，显著提升了结果一致性。


* **长尾型号识别优化**：
* 针对 AI 难以识别冷门或艺术字 Logo 的问题，设计了 **动态线索注入 (User Hint Injection)** 机制，允许用户干预模型关注点。



---

## 📦 技术栈

| 类别 | 技术 |
| --- | --- |
| **大模型** | Qwen-VL-Max, Qwen-Plus (Aliyun DashScope) |
| **框架** | LangChain (LCEL), FastAPI |
| **前端** | Streamlit + Custom CSS Animation |
| **工具** | Pydantic (数据校验), SQLite (记录持久化) |

---

## 🔧 快速开始

1. **克隆仓库**
```bash
git clone https://github.com/XIAOHAY/Snowboard-AI-Pricing.git
cd 仓库名

```


2. **配置环境**
在根目录创建 `.env` 文件并添加你的 API Key：
```env
DASHSCOPE_API_KEY=你的Key

```


3. **安装依赖**
```bash
pip install -r requirements.txt

```


4. **启动应用**
```bash
streamlit run app_ui_deploy.py

```



---

## 👨‍💻 作者

**GitHub ID（XIAOHAY）** **学校**：北方工业大学

