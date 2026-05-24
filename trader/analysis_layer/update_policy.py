from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UpdatePolicy:
    source: str
    cadence: str
    cadence_label: str
    rationale: str
    user_action: str


UPDATE_POLICIES = [
    UpdatePolicy(
        source="行情价格 / 新闻",
        cadence="daily",
        cadence_label="每日更新",
        rationale="长期投资不需要分钟级噪音，但每日收盘后的价格和新闻足够支持复盘。",
        user_action="必要时点击“刷新行情与新闻”。",
    ),
    UpdatePolicy(
        source="推荐关注雷达",
        cadence="daily",
        cadence_label="每日更新",
        rationale="它依赖大师共识和 5 日异动，日更可以捕捉显著变化，又不会鼓励高频交易。",
        user_action="重大事件后可点击“重新生成今日关注雷达”。",
    ),
    UpdatePolicy(
        source="归因 / 大师批判",
        cadence="daily",
        cadence_label="每日更新",
        rationale="LLM 分析适合沉淀成投资日志；一天一次能控制成本和情绪噪音。",
        user_action="重大新闻后可点击“重新生成今日归因/批判”。",
    ),
    UpdatePolicy(
        source="投资框架分析",
        cadence="daily",
        cadence_label="每日更新",
        rationale="框架本身稳定，但应用到具体标的时需要读取当天价格、趋势、风险和投资天气。",
        user_action="随行情/新闻日更自动重算；换标的或周期也会即时重算。",
    ),
    UpdatePolicy(
        source="大师持仓 / 共识塔",
        cadence="weekly",
        cadence_label="每周复核",
        rationale="公开披露通常有季度滞后，日更意义不大；周度复核更适合学习和整理研究队列。",
        user_action="每周检查来源链接和持仓摘要是否需要维护。",
    ),
    UpdatePolicy(
        source="ETF 快捷目录",
        cadence="monthly",
        cadence_label="每月复核",
        rationale="ETF 产品变化慢，月度维护可以兼顾完整性、费率变化和列表可读性。",
        user_action="新增市场或风格时再手动更新目录。",
    ),
    UpdatePolicy(
        source="本地组合状态",
        cadence="on_demand",
        cadence_label="按需更新",
        rationale="这是个人敏感数据，只应在你主动解析文件或修改输入时更新。",
        user_action="未来接入 PDF 解析后，由本地解析动作触发。",
    ),
]


def get_update_policies() -> list[UpdatePolicy]:
    return UPDATE_POLICIES


def get_policy(source: str) -> UpdatePolicy:
    for policy in UPDATE_POLICIES:
        if policy.source == source:
            return policy
    raise ValueError(f"Unknown update policy source: {source}")
