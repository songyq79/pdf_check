"""
定价配置 — 默认值，可通过管理后台 SystemConfig 动态覆盖
"""

# 金额单位：分（1元 = 100分）
DEFAULT_PRICING = {
    "per_use": 990,      # 9.9元/次
    "monthly": 6990,     # 69.9元/月
    "monthly_limit": 20, # 包月每月限20次
}

# 免费试用次数（注册即送）
FREE_TRIAL_COUNT = 1

# 邀请奖励次数（每邀请1人送N次）
REFERRAL_REWARD_COUNT = 3
