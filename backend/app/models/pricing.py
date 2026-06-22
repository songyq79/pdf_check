"""
定价配置 — 默认值，可通过管理后台 SystemConfig 动态覆盖
"""

# 金额单位：分（1元 = 100分）
# 说明：计费基本单位是 "credit"（次）。per_use 是每个 credit 的单价；
# 不同功能消耗的 credit 数见下方 FEATURE_COSTS。
DEFAULT_PRICING = {
    "per_use": 990,      # 9.9元/credit（每次基础单价）
    "monthly": 6990,     # 69.9元/月
    "monthly_limit": 20, # 包月每月 20 credits
}

# ── 功能消耗价目表（唯一真相源）──────────────────────────────
# 所有 API 扣费统一从这里读取，不要在各端点里硬编码 cost。
# action 名称必须与 consume_quota(action=...) 传入的字符串一致。
# 查重按语言区分，单独用 plagiarism_cn / plagiarism_en。
FEATURE_COSTS = {
    "evaluation": 1,             # 智能评价
    "proofread": 1,             # 论文校对
    "formatter": 1,             # 模板排版
    "plagiarism_cn": 1,         # 论文查重（中文）
    "plagiarism_en": 2,         # 论文查重（英文）
    "topic_evaluation": 3,      # 选题评估（定题评测）
    "topic_recommend": 2,       # 选题推荐（生成候选选题）
    "experiment_evaluation": 3, # 实验设计评审
    "writing_assist": 2,        # 写作辅助（单段检查）
    "writing_whole": 10,        # 写作辅助（整篇，一次性分析全文）
    "literature_review": 5,     # 文献综述生成
}

# 各功能中文展示名（前端价目表/提示用）
FEATURE_LABELS = {
    "evaluation": "智能评价",
    "proofread": "论文校对",
    "formatter": "模板排版",
    "plagiarism_cn": "论文查重（中文）",
    "plagiarism_en": "论文查重（英文）",
    "topic_evaluation": "选题评估",
    "topic_recommend": "选题推荐",
    "experiment_evaluation": "实验设计评审",
    "writing_assist": "写作辅助（单段）",
    "writing_whole": "写作辅助（整篇）",
    "literature_review": "文献综述生成",
}


def get_feature_cost(action: str) -> int:
    """返回某功能消耗的 credit 数，未登记的功能默认 1。"""
    return FEATURE_COSTS.get(action, 1)


# 免费试用次数（注册即送，够体验一次任意功能）
FREE_TRIAL_COUNT = 5

# 邀请奖励次数（每邀请1人送N次）
REFERRAL_REWARD_COUNT = 3
