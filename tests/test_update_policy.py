from trader.analysis_layer.update_policy import get_policy, get_update_policies


def test_update_policies_cover_core_sources() -> None:
    sources = {policy.source for policy in get_update_policies()}

    assert {
        "行情价格 / 新闻",
        "推荐关注雷达",
        "归因 / 大师批判",
        "大师持仓 / 共识塔",
        "ETF 快捷目录",
        "本地组合状态",
    } <= sources


def test_update_policy_cadences_match_long_term_workflow() -> None:
    assert get_policy("行情价格 / 新闻").cadence == "daily"
    assert get_policy("推荐关注雷达").cadence == "daily"
    assert get_policy("归因 / 大师批判").cadence == "daily"
    assert get_policy("大师持仓 / 共识塔").cadence == "weekly"
    assert get_policy("ETF 快捷目录").cadence == "monthly"
    assert get_policy("本地组合状态").cadence == "on_demand"
