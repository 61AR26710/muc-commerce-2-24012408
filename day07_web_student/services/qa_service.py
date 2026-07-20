from pathlib import Path

import pandas as pd


def answer_question(base_dir: Path, question: str) -> str:
    data_dir = base_dir / "data"
    metrics_df = pd.read_csv(data_dir / "overall_metrics.csv", encoding="utf-8-sig")
    category_df = pd.read_csv(data_dir / "category_analysis.csv", encoding="utf-8-sig")
    segment_df = pd.read_csv(data_dir / "segment_analysis.csv", encoding="utf-8-sig")
    metrics = dict(zip(metrics_df["指标"], metrics_df["数值"]))
    normalized = question.replace(" ", "").lower()

    if any(word in normalized for word in ["多少用户", "用户数", "总用户"]):
        return f"数据集中共有{int(metrics['用户数']):,}名用户。"

    # 补充"流失率""偏好品类""生命周期风险"和"订单"四类问答

    # 流失率
    if any(word in normalized for word in ["流失率", "流失比例", "多少流失", "流失多少"]):
        return (
            f"数据集总体流失率为{metrics['流失率']:.1%}，"
            f"即{int(metrics['流失人数']):,}名用户中有{int(metrics['流失人数']):,}人流失。"
        )

    # 偏好品类
    if any(word in normalized for word in ["品类", "偏好品类", "哪个品类", "哪类", "类别"]):
        max_churn_cat = category_df.loc[category_df["流失率"].idxmax()]
        min_churn_cat = category_df.loc[category_df["流失率"].idxmin()]
        return (
            f"流失率最高的偏好品类是{max_churn_cat['PreferedOrderCat']}，"
            f"流失率达{max_churn_cat['流失率']:.1%}；"
            f"流失率最低的是{min_churn_cat['PreferedOrderCat']}，"
            f"流失率仅为{min_churn_cat['流失率']:.1%}。"
        )

    # 生命周期风险
    if any(word in normalized for word in ["生命周期", "阶段", "风险", "新用户", " tenure", "tenure"]):
        max_churn_seg = segment_df.loc[segment_df["流失率"].idxmax()]
        min_churn_seg = segment_df.loc[segment_df["流失率"].idxmin()]
        return (
            f"生命周期中流失风险最高的是「{max_churn_seg['TenureGroup']}」阶段，"
            f"流失率高达{max_churn_seg['流失率']:.1%}（{int(max_churn_seg['流失人数']):,}/{int(max_churn_seg['用户数']):,}人）；"
            f"风险最低的是「{min_churn_seg['TenureGroup']}」阶段，流失率为{min_churn_seg['流失率']:.1%}。"
        )

    # 订单
    if any(word in normalized for word in ["订单", "下单", "购买", "单数"]):
        max_orders_cat = category_df.loc[category_df["平均订单数"].idxmax()]
        return (
            f"用户平均订单数为{metrics['平均订单数']:.2f}单，订单数中位数为{int(metrics['订单数中位数'])}单；"
            f"平均订单数最高的品类是{max_orders_cat['PreferedOrderCat']}，"
            f"达{max_orders_cat['平均订单数']:.2f}单。"
        )

    return (
        "基础问答尚未完成。目前只能回答总用户数。"
        "请换一种更具体的问法。"
    )