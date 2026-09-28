from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objs as go
from sqlalchemy import create_engine
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from dotenv import load_dotenv
import os


app = Flask(__name__)

# 爬蟲函數
def get_exchange_rates():
    url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
    res = requests.get(url)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    rows = soup.find("table", {"title": "牌告匯率"}).find("tbody").find_all("tr")

    # 要保留的主要貨幣
    keep_currencies = [
        "美金 (USD)", "港幣 (HKD)", "英鎊 (GBP)", "澳幣 (AUD)",
        "加拿大幣 (CAD)", "新加坡幣 (SGD)", "瑞士法郎 (CHF)",
        "日圓 (JPY)", "紐元 (NZD)", "韓元 (KRW)", "人民幣 (CNY)"
    ]

    data = []
    for row in rows:
        currency = row.find("div", {"class": "hidden-phone"}).get_text(strip=True)
        if currency not in keep_currencies:
            continue  # 跳過非主要貨幣
        tds = row.find_all("td")
        data.append({
            "currency": currency,
            "cash_buy": tds[1].get_text(strip=True),
            "cash_sell": tds[2].get_text(strip=True),
            "spot_buy": tds[3].get_text(strip=True),
            "spot_sell": tds[4].get_text(strip=True)
        })
    return data

def get_select_options():
    url = "https://rate.bot.com.tw/xrt/history/USD"  # 任意貨幣，主要為了抓<select>
    resp = requests.get(url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "lxml")

    # 年份選項
    year_select = soup.find("select", {"name": "year"})
    years = [opt["value"] for opt in year_select.find_all("option")]

    # 月份選項
    month_select = soup.find("select", {"name": "month"})
    months = [opt["value"] for opt in month_select.find_all("option")]

    # 幣別選項
    currency_select = soup.find("select", {"name": "currency"})
    currencies = [(opt["value"], opt.text.strip()) for opt in currency_select.find_all("option")]

    return {"years": years, "months": months, "currencies": currencies}


# 爬取歷史匯率資料
def get_history_data(currency="USD", year="2025", month="08"):
    url = f"https://rate.bot.com.tw/xrt/quote/{year}-{month}/{currency}"
    resp = requests.get(url)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.find('table', attrs={'title': '歷史本行營業時間牌告匯率'})
    if not table:
        return pd.DataFrame()  # 沒表格 → 空DataFrame

    tbody = table.find('tbody')
    rows = tbody.find_all('tr')
    if not rows:
        return pd.DataFrame()  # 沒有tr → 空DataFrame

    # 如果第一個<td>包含"找不到任何一筆資料"
    first_td = rows[0].find("td")
    if first_td and "找不到任何一筆資料" in first_td.get_text(strip=True):
        return pd.DataFrame()  # 網站明確提示無資料 → 空DataFrame

    # 解析資料
    data = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 5:
            continue
        data.append({
            "date": tds[0].get_text(strip=True),
            "cash_buy": tds[2].get_text(strip=True),
            "cash_sell": tds[3].get_text(strip=True),
            "spot_buy": tds[4].get_text(strip=True),
            "spot_sell": tds[5].get_text(strip=True)
        })
    return pd.DataFrame(data)

# 畫折線圖
def plot_history_chart(df, year="2025", month="08", currency="USD"):
    if df.empty:
        return "<p style='color:red; text-align:center;'>查無資料</p>"
    df['date'] = pd.to_datetime(df['date'])
    fig = px.line(df, x="date", y=["cash_buy", "cash_sell", "spot_buy", "spot_sell"], title=f"{year}年{month}月{currency} 匯率走勢圖")
    fig.update_layout(
        margin={"t": 80, "b": 20, "l": 20, "r": 20},
        legend=dict(
            orientation="h",   # 水平
            yanchor="bottom",
            y=1.02,            # 在圖表上方
            xanchor="center",
            x=0.5              # 置中
        ),
        legend_title_text=""
    )
    return fig.to_html(full_html=False)

@app.route("/update_chart", methods=["POST"])
def update_chart():
    year = request.form.get("year", "2025")
    month = request.form.get("month", "08")
    currency = request.form.get("currency", "USD")
    df = get_history_data(currency, year, month)
    chart_html = plot_history_chart(df, year, month, currency)
    return jsonify({"chart_html": chart_html})

# 專案首頁
@app.route("/")
def index():
    return render_template("index.html")

# 匯率資料爬蟲
@app.route("/crawler")
def crawler():
    rates = get_exchange_rates()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    options = get_select_options()  # 動態抓選單
    # 預設圖：當年當月 USD
    default_chart = plot_history_chart(get_history_data())

    return render_template("crawler.html",
                           rates=rates,
                           update_time=update_time,
                           options=options,
                           default_chart=default_chart)

# 資料庫儲存
@app.route("/database")
def database():
    return render_template("database.html")

load_dotenv()  # 讀取 .env 檔
DB_URI = os.getenv("DB_URI")
engine = create_engine(DB_URI)
query = "SELECT * FROM bp01d01_rates ORDER BY Date"
df = pd.read_sql(query, engine, parse_dates=["Date"])
currency_cols = df.columns[1:].tolist()
# === Dash 子應用 ===
dash_app = dash.Dash(__name__, server=app, url_base_pathname="/dash/")
dash_app.layout = html.Div([
    html.Label("選擇幣別:"),
    dcc.Dropdown(
        id='currency-dropdown',
        options=[{'label': col, 'value': col} for col in currency_cols],
        value=[currency_cols[0]],
        multi=True
    ),
    dcc.Graph(id='rate-graph')
], style={"padding": "20px", "backgroundColor": "white", "color": "black"})

@dash_app.callback(
    Output('rate-graph', 'figure'),
    Input('currency-dropdown', 'value')
)
def update_graph(selected_currencies):
    fig = go.Figure()
    for col in selected_currencies:
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df[col],
            mode='lines', name=col
        ))
    fig.update_layout(
        title="匯率走勢圖",
        xaxis_title="日期", yaxis_title="匯率",
        margin={"t":60,"b":40,"l":60,"r":20},
        xaxis=dict(rangeslider=dict(visible=True)),
        yaxis=dict(fixedrange=False)
    )
    return fig
# ======== 資料庫連線 =========
DB_URI = os.getenv("DB_URI", "mysql+mysqlconnector://root:password@localhost/exchange_db")
engine = create_engine(DB_URI)

# ======== 讀取 LSTM 模型指標表 =========
def get_lstm_model_metrics():
    query = "SELECT * FROM lstm_model_metrics"
    return pd.read_sql(query, engine)

df_metrics = get_lstm_model_metrics()
df_metrics["model_label"] = df_metrics.apply(
    lambda r: f"l{r.layers}_u{r.units}_e{r.epochs}_b{r.batch_size}", axis=1
)

# ======== Flask /prediction 路由 =========
@app.route("/prediction")
def prediction():
    # 單模型資料
    query = """
        SELECT date, true_rate, pred_rate
        FROM predictions
        WHERE model_version='bp01d01_rates_NTD_USD_l1_u50_e20_b16'
        ORDER BY date
    """
    df = pd.read_sql(query, engine, parse_dates=["date"])

    metric_query = """
        SELECT mae, rmse, mape, r2
        FROM lstm_model_metrics
        WHERE model_version='bp01d01_rates_NTD_USD_l1_u50_e20_b16'
    """
    metrics = pd.read_sql(metric_query, engine).iloc[0]

    # 單模型圖
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["true_rate"], mode="lines", name="實際匯率"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["pred_rate"], mode="lines", name="預測匯率"))
    fig.update_layout(
        title="USD/NTD 匯率 LSTM 預測",
        xaxis_title="日期", yaxis_title="匯率",
        margin={"t":60,"b":40,"l":60,"r":20},
        xaxis=dict(rangeslider=dict(visible=True)),
    )
    chart_html = fig.to_html(full_html=False)

    # ======== 多模型圖表生成 ========
    extra_charts = generate_analysis_charts(df_metrics, "bp01d01_rates", "NTD_USD")

    return render_template(
        "prediction.html",
        chart=chart_html,
        mae=metrics["mae"],
        rmse=metrics["rmse"],
        mape=metrics["mape"],
        r2=metrics["r2"],
        extra_charts=extra_charts
    )


# ======== 深度分析圖表生成函數 ========
def generate_analysis_charts(df, source, currency):
    subset = df[(df["source"] == source) & (df["currency"] == currency)]
    if subset.empty:
        return "<p style='color:red;'>查無模型資料</p>"

    # 誤差比較
    fig_errors = px.bar(
        subset, x="model_label", y=["mae","rmse","mape"],
        barmode="group",
        title=f"{source} | {currency} 誤差指標比較"
    )
    fig_errors.update_layout(
        margin={"t":80,"b":20,"l":20,"r":20},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        legend_title_text=""
    )

    # R²
    fig_r2 = px.bar(subset, x="model_label", y="r2", title=f"{source} | {currency} 決定係數 R²")
    fig_r2.update_layout(margin={"t":60,"b":20,"l":20,"r":20})

    # 訓練時間
    fig_time = px.bar(subset, x="model_label", y="time", title="訓練耗時 (秒)")
    fig_time.update_layout(margin={"t":60,"b":20,"l":20,"r":20})

    # 散點
    fig_scatter = px.scatter(subset, x="time", y="r2", color="model_label", title="效率 vs 準確度")
    fig_scatter.update_layout(showlegend=False, margin={"t":60,"b":20,"l":20,"r":20})

    # 誤差分布
    melted = subset.melt(id_vars=["model_label"], value_vars=["mae","rmse","mape"], var_name="metric")
    fig_box = go.Figure()
    for m in melted["metric"].unique():
        fig_box.add_trace(go.Box(
            y=melted[melted["metric"]==m]["value"],
            x=melted[melted["metric"]==m]["model_label"],
            name=m
        ))
    fig_box.update_layout(
        title="誤差分布 (MAE / RMSE / MAPE)",
        margin={"t":80,"b":20,"l":20,"r":20},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )

    return "".join([
        fig_errors.to_html(full_html=False),
        fig_r2.to_html(full_html=False),
        fig_time.to_html(full_html=False),
        fig_scatter.to_html(full_html=False),
        fig_box.to_html(full_html=False)
    ])

if __name__ == "__main__":
    app.run(debug=True, port=5000)
