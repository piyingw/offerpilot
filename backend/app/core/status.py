"""投递状态机与枚举的唯一定义处（前端有对应镜像：frontend/src/constants/application.ts）。"""

STATUS_LABELS: dict[str, str] = {
    "applied": "已投递",
    "viewed": "已查看",
    "written_test": "笔试",
    "interview_1": "一面",
    "interview_2": "二面",
    "interview_3": "三面",
    "hr_interview": "HR面",
    "offer": "Offer",
    "rejected": "已挂",
    "closed": "流程终止",
}

# 漏斗的推进阶段（按顺序）；rejected / closed 是旁路终态，不参与漏斗
STAGE_ORDER: list[str] = [
    "applied",
    "viewed",
    "written_test",
    "interview_1",
    "interview_2",
    "interview_3",
    "hr_interview",
    "offer",
]

TERMINAL_NEGATIVE: list[str] = ["rejected", "closed"]
TERMINAL_POSITIVE: list[str] = ["offer"]

CHANNEL_LABELS: dict[str, str] = {
    "boss": "Boss直聘",
    "zhilian": "智联招聘",
    "51job": "前程无忧",
    "liepin": "猎聘",
    "niuke": "牛客",
    "official": "官网网申",
    "referral": "内推",
    "other": "其他",
}
