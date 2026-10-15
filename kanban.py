import glob
import os
import pandas as pd
import streamlit as st

# 页面配置
st.set_page_config(page_title="板块强度异动监控", layout="wide")

# 自定义暗黑发光样式
st.markdown(
    """
<style>
    .stApp {
        background-color: #121621;
        color: #ffffff;
    }
    .card {
        background: rgba(255, 255, 255, 0.92);
        color: #1f2329;
        padding: 6px 14px;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 500;
        margin: 5px;
        white-space: nowrap;
    }
    .card-pink { border: 2px solid #ff4d4f; box-shadow: 0 0 8px rgba(255, 77, 79, 0.4); }
    .card-yellow { border: 2px solid #fadb14; box-shadow: 0 0 8px rgba(250, 219, 20, 0.4); }
    .card-blue { border: 2px solid #1890ff; box-shadow: 0 0 8px rgba(24, 144, 255, 0.4); }
    .card-green { border: 2px solid #52c41a; box-shadow: 0 0 8px rgba(82, 196, 26, 0.4); }
    
    .c-title { font-weight: 700; color: #000; font-size: 15px; }
    .c-info { color: #667085; font-size: 12px; }
    .c-val { color: #d92d20; font-weight: 700; font-size: 15px; }
    .section-header { font-size: 18px; font-weight: 600; margin-top: 20px; margin-bottom: 10px; color: #ffffff; }
    .sub-text { font-size: 14px; color: #94a3b8; font-weight: normal; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("📈 板块强度排名与异动监控中心")

# 自动寻找文件夹中的所有 excel 文件
files = sorted(
    glob.glob("板块强度排名*.xls*") + glob.glob("板块强度排名*.xlsx")
)

if not files:
    st.warning("未检测到 Excel 文件，请将表格上传到项目根目录下。")
else:
    # 加载所有日期数据
    data_dict = {}
    for f in files:
        # 从文件名提取日期
        date_str = "".join(filter(str.isdigit, f))
        if len(date_str) >= 8:
            formatted_date = f"{date_str[4:6]}-{date_str[6:8]}"
        else:
            formatted_date = f

        try:
            if f.endswith(".xlsx"):
                df = pd.read_excel(f, skiprows=1)
            else:
                df = pd.read_csv(f, sep="\t", encoding="gbk", skiprows=1)

            df.columns = [c.strip() for c in df.columns]
            df["强度"] = pd.to_numeric(df["强度"], errors="coerce")
            df = df.dropna(subset=["名称"]).copy()
            df["rank"] = df["强度"].rank(ascending=False, method="min").astype(
                int
            )
            data_dict[formatted_date] = df
        except Exception as e:
            st.error(f"读取文件 {f} 失败: {e}")

    if data_dict:
        dates = sorted(list(data_dict.keys()))
        latest_date = dates[-1]
        prev_date = dates[-2] if len(dates) > 1 else dates[0]

        st.markdown(
            f'<div class="section-header">当日异动 <span class="sub-text">（前50名中跳升最大 —— {latest_date} vs {prev_date}）</span></div>',
            unsafe_allow_html=True,
        )

        # 计算当日跳升排名
        df_latest = data_dict[latest_date]
        df_prev = data_dict[prev_date]
        merged = pd.merge(
            df_latest[["名称", "rank", "股数"]],
            df_prev[["名称", "rank"]],
            on="名称",
            suffixes=("_latest", "_prev"),
            how="inner",
        )
        merged["jump"] = merged["rank_prev"] - merged["rank_latest"]
        top_jumps = (
            merged[merged["rank_latest"] <= 50]
            .sort_values("jump", ascending=False)
            .head(5)
        )

        cols = st.columns(len(top_jumps) if len(top_jumps) > 0 else 1)
        colors = ["card-pink", "card-green", "card-blue", "card-yellow"]

        for i, (_, row) in enumerate(top_jumps.iterrows()):
            c_style = colors[i % len(colors)]
            card_html = f"""
            <div class="card {c_style}">
                <span class="c-title">{row['名称']}</span>
                <span class="c-info">第{row['rank_prev']}名 → 第{row['rank_latest']}名</span>
                <span class="c-val">↑{row['jump']}</span>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

        st.markdown(
            '<div class="section-header">近一周异动</div>',
            unsafe_allow_html=True,
        )

        # 近一周各日期展示
        for dt in dates:
            df_d = data_dict[dt].sort_values("rank").head(3)
            row_html = f"""<div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 60px; color: #94a3b8; font-family: monospace;">{dt}</div>
                <div>"""
            for _, r in df_d.iterrows():
                row_html += f"""
                <span class="card card-pink" style="margin-right: 10px;">
                    <span class="c-title">{r['名称']}</span>
                    <span class="c-info">强度第{r['rank']}名</span>
                    <span class="c-info">{int(r['股数']) if pd.notnull(r['股数']) else 0}股</span>
                </span>
                """
            row_html += "</div></div>"
            st.markdown(row_html, unsafe_allow_html=True)