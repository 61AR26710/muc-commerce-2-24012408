from pathlib import Path

import pandas as pd
import csv
import io


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def load_dashboard_data(base_dir: Path, selected_category: str = "全部") -> dict:
    data_dir = base_dir / "data"
    metrics_df = _read_csv(data_dir / "overall_metrics.csv")
    category_df = _read_csv(data_dir / "category_analysis.csv")
    segment_df = _read_csv(data_dir / "segment_analysis.csv")

    metric_map = dict(zip(metrics_df["指标"], metrics_df["数值"]))
    
    # 在已有两张指标卡基础上，增加"总体流失率"和"平均订单数"
    metrics = [
        {"label": "总用户数", "value": f"{int(metric_map['用户数']):,}", "note": "人"},
        {"label": "流失用户", "value": f"{int(metric_map['流失人数']):,}", "note": "人"},
        {"label": "总体流失率", "value": f"{metric_map['流失率']:.1%}", "note": ""},
        {"label": "平均订单数", "value": f"{metric_map['平均订单数']:.2f}", "note": "单"},
    ]

    categories = ["全部", *category_df["PreferedOrderCat"].tolist()]
    table_df = category_df.copy()
    
    # 选择具体品类后筛选table_df
    # 使用布尔条件筛选：当 selected_category 不是"全部"时，只保留匹配品类的行
    if selected_category != "全部":
        table_df = table_df[table_df["PreferedOrderCat"] == selected_category]

    table_df = table_df.rename(
        columns={
            "PreferedOrderCat": "偏好品类",
            "用户数": "用户数",
            "流失率": "流失率",
            "平均订单数": "平均订单数",
        }
    )[["偏好品类", "用户数", "流失率", "平均订单数"]]
    table_df["流失率"] = table_df["流失率"].map(lambda value: f"{value:.1%}")
    table_df["平均订单数"] = table_df["平均订单数"].map(lambda value: f"{value:.2f}")

    # 找出流失率最高的生命周期阶段，并生成一句数据观察
    max_churn_idx = segment_df["流失率"].idxmax()
    max_churn_row = segment_df.loc[max_churn_idx]
    stage_name = max_churn_row["TenureGroup"]
    churn_rate = max_churn_row["流失率"]
    user_count = int(max_churn_row["用户数"])
    churn_count = int(max_churn_row["流失人数"])
    
    insight = (
        f"⚠️ 风险聚焦：{stage_name}群体的流失率高达{churn_rate:.1%}，"
        f"该阶段共有{user_count:,}名用户，其中{churn_count:,}人已流失，"
        f"是生命周期中流失风险最高的阶段，建议优先投入挽留资源。"
    )

    return {
        "metrics": metrics,
        "categories": categories,
        "category_rows": table_df.to_dict("records"),
        "insight": insight,
    }

# 下载已筛选内容
def export_category_csv(base_dir: Path, selected_category: str = "全部") -> io.BytesIO:
    """
    根据当前筛选的品类，导出对应的 category_analysis 数据为 CSV。
    返回一个已 seek(0) 的 BytesIO 对象，可直接用于 Flask send_file。
    """
    data_dir = base_dir / "data"
    category_df = _read_csv(data_dir / "category_analysis.csv")

    # 筛选逻辑与 load_dashboard_data 保持一致
    if selected_category != "全部":
        category_df = category_df[category_df["PreferedOrderCat"] == selected_category]

    # 重命名并选择展示列
    table_df = category_df.rename(
        columns={
            "PreferedOrderCat": "偏好品类",
            "用户数": "用户数",
            "流失率": "流失率",
            "平均订单数": "平均订单数",
        }
    )[["偏好品类", "用户数", "流失率", "平均订单数"]]

    # 格式化数值（与前端展示一致）
    table_df["流失率"] = table_df["流失率"].map(lambda v: f"{v:.1%}")
    table_df["平均订单数"] = table_df["平均订单数"].map(lambda v: f"{v:.2f}")

    # 写入内存 CSV（Python 3 中 csv 模块需要 StringIO，send_file 需要 BytesIO）
    string_buffer = io.StringIO()
    writer = csv.writer(string_buffer)
    writer.writerow(["偏好品类", "用户数", "流失率", "平均订单数"])
    for _, row in table_df.iterrows():
        writer.writerow([row["偏好品类"], row["用户数"], row["流失率"], row["平均订单数"]])

    # 转换为 BytesIO 以供 Flask send_file 使用
    byte_buffer = io.BytesIO()
    byte_buffer.write(string_buffer.getvalue().encode("utf-8-sig"))  # 带 BOM，Excel 兼容
    byte_buffer.seek(0)
    return byte_buffer