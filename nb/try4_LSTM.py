#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dash
from dash import Dash, dcc, html, Input, Output, State
from sqlalchemy import create_engine


# In[2]:


# ========= 連線 MySQL =========
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")

def load_metrics():
    return pd.read_sql("SELECT * FROM lstm_model_metrics", engine)

def load_predictions(model_version):
    query = f"""
        SELECT date, true_rate, pred_rate
        FROM predictions
        WHERE model_version = '{model_version}'
        ORDER BY date
    """
    return pd.read_sql(query, engine)

df_metrics = load_metrics()

# ========= Dash App =========
app = Dash(__name__)

app.layout = html.Div([

    # --- Source 選擇 ---
    html.Div([
        html.Label("選擇資料來源:"),
        dcc.Dropdown(
            id='source-dropdown',
            options=[{"label": s, "value": s} for s in sorted(df_metrics["source"].unique())],
            value=sorted(df_metrics["source"].unique())[0]
        )
    ], style={"margin-bottom": "10px"}),   

    # --- Currency 選擇 ---
    html.Div([
        html.Label("選擇幣別:"),
        dcc.Dropdown(id='currency-dropdown')
    ], style={"margin-bottom": "10px"}),   

    # --- Model 選擇 ---
    html.Div([
        html.Label("選擇模型版本:"),
        dcc.Dropdown(id='model-dropdown')
    ], style={"margin-bottom": "10px"}),   

    html.Div([
        html.Label(id='metrics-output')
    ]),     

    dcc.Graph(id='predictions-graph'),

], style={"padding": "20px", "backgroundColor": "white", "color": "black"})


# ========= Callback =========
# 更新 currency 選單
@app.callback(
    Output('currency-dropdown', 'options'),
    Output('currency-dropdown', 'value'),
    Input('source-dropdown', 'value')
)
def update_currency_options(selected_source):
    subset = df_metrics[df_metrics["source"] == selected_source]
    currencies = sorted(subset["currency"].unique())
    options = [{"label": c, "value": c} for c in currencies]
    return options, currencies[0] if currencies else None


# 更新 model 選單
@app.callback(
    Output('model-dropdown', 'options'),
    Output('model-dropdown', 'value'),
    Input('currency-dropdown', 'value'),
    State('source-dropdown', 'value')
)
def update_model_options(selected_currency, selected_source):
    subset = df_metrics[
        (df_metrics["source"] == selected_source) &
        (df_metrics["currency"] == selected_currency)
    ]

    # 顯示簡化的 label，例如 "layers=2, units=64, epochs=50, batch=32"
    options = [
        {"label": f"layers={r.layers}, units={r.units}, epochs={r.epochs}, batch={r.batch_size}",
         "value": r.model_version}
        for r in subset.itertuples()
    ]
    default_val = options[0]["value"] if options else None
    return options, default_val


# 更新 metrics 與圖表
@app.callback(
    [Output('metrics-output', 'children'),
     Output('predictions-graph', 'figure')],
    Input('model-dropdown', 'value')
)
def update_dashboard(model_version):
    if not model_version:
        return "尚無模型資料", go.Figure()

    # --- 抓 metrics ---
    row = df_metrics[df_metrics["model_version"] == model_version].iloc[0]

    metrics_text = (
        f"MAE: {row['mae']:.4f}, "
        f"RMSE: {row['rmse']:.4f}, "
        f"MAPE: {row['mape']:.2f}%, "
        f"R²: {row['r2']:.4f}, "
        f"Time: {row['time']}"
    )

    # --- 折線圖 (Pred vs True) ---
    df_pred = load_predictions(model_version)
    fig_pred = go.Figure()
    fig_pred.add_trace(go.Scatter(
        x=df_pred["date"], y=df_pred["true_rate"],
        mode="lines", name="實際匯率"
    ))
    fig_pred.add_trace(go.Scatter(
        x=df_pred["date"], y=df_pred["pred_rate"],
        mode="lines", name="預測匯率"
    ))
    fig_pred.update_layout(
        title=f"{model_version} 預測 vs 實際",
        xaxis_title="日期",
        yaxis_title="匯率",
        margin={"t": 80, "b": 40, "l": 20, "r": 20},
        xaxis=dict(rangeslider=dict(visible=True))
    )

    return metrics_text, fig_pred


if __name__ == '__main__':
    app.run(debug=True, port=5006)


# In[6]:


# 1️⃣ 建立 MySQL 連線
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")

def get_lstm_model_metrics():
    query = "SELECT * FROM lstm_model_metrics"
    df = pd.read_sql(query, engine)
    return df

df = get_lstm_model_metrics()
df["model_label"] = df.apply(
    lambda r: f"l{r.layers}_u{r.units}_e{r.epochs}_b{r.batch_size}", axis=1
)

# 2️⃣ 啟動 Dash
app = dash.Dash(__name__)
app.title = "LSTM 模型比較 Dashboard"

# 3️⃣ Layout
app.layout = html.Div([
    html.H1("📊 LSTM 模型比較分析", style={"textAlign":"center"}),

    # 來源選單（單選）
    html.Div([
        html.Label("選擇資料來源:"),
        dcc.Dropdown(
            id="source-selector",
            options=[{"label": s, "value": s} for s in sorted(df["source"].unique())],
            value=sorted(df["source"].unique())[0],
            clearable=False
        )
    ], style={"margin":"auto"}),

    html.Br(),

    # 幣別選單（單選）
    html.Div([
        html.Label("選擇幣別:"),
        dcc.Dropdown(
            id="currency-selector",
            multi=False
        )
    ], style={"margin":"auto"}),

    html.Br(),

    # 模型版本選單（多選）
    html.Div([
        html.Label("選擇模型版本:"),
        dcc.Dropdown(
            id="model-selector",
            multi=True
        )
    ], style={"margin":"auto"}),

    html.Hr(),

    # 各種圖表
    dcc.Graph(id="bar-errors"),
    dcc.Graph(id="bar-r2"),
    dcc.Graph(id="bar-time"),
    dcc.Graph(id="scatter-efficiency"),
    dcc.Graph(id="boxplot-errors")
], style={"padding": "20px", "backgroundColor": "white", "color": "black"})

# 4️⃣ Callback - 動態更新幣別選單 (單選)
@app.callback(
    Output("currency-selector", "options"),
    Output("currency-selector", "value"),
    Input("source-selector", "value")
)
def update_currency_options(selected_source):
    subset = df[df["source"] == selected_source]
    currencies = sorted(subset["currency"].unique())
    options = [{"label": c, "value": c} for c in currencies]
    return options, currencies[0] if currencies else None  # 預設選第一個

# 5️⃣ Callback - 動態更新模型版本選單
@app.callback(
    Output("model-selector", "options"),
    Output("model-selector", "value"),
    Input("source-selector", "value"),
    Input("currency-selector", "value")
)
def update_model_options(selected_source, selected_currency):
    if not selected_currency:
        return [], []

    subset = df[
        (df["source"] == selected_source) &
        (df["currency"] == selected_currency)
    ]

    # 顯示簡化標籤，例如 "l2_u64_e50_b32"
    options = [
        {"label": f"layers={r.layers}, units={r.units}, epochs={r.epochs}, batch={r.batch_size}",
         "value": r.model_version}
        for r in subset.itertuples()
    ]
    default_vals = [r["value"] for r in options]  # 預設全選
    return options, default_vals

# 6️⃣ Callback - 更新圖表
@app.callback(
    Output("bar-errors", "figure"),
    Output("bar-r2", "figure"),
    Output("bar-time", "figure"),
    Output("scatter-efficiency", "figure"),
    Output("boxplot-errors", "figure"),
    Input("source-selector", "value"),
    Input("currency-selector", "value"),
    Input("model-selector", "value")
)
def update_graphs(selected_source, selected_currency, selected_models):
    if not selected_currency or not selected_models:
        return go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()

    dff = df[
        (df["source"] == selected_source) &
        (df["currency"] == selected_currency) &
        (df["model_version"].isin(selected_models))
    ]

    # --- 誤差比較 (Bar) ---
    fig_errors = px.bar(
        dff, x="model_label", y=["mae", "rmse", "mape"],
        barmode="group",
        title=f"{selected_source} | {selected_currency} 誤差指標比較 (MAE / RMSE / MAPE)"
    )
    fig_errors.update_layout(
        margin={"t": 80, "b": 20, "l": 20, "r": 20},
        legend=dict(
            orientation="h",   # 水平
            yanchor="bottom",
            y=1.02,            # 在圖表上方
            xanchor="center",
            x=0.1              # 置中
        ),
        legend_title_text=""
    )

    # --- R² ---
    r2_min = dff["r2"].min()
    r2_max = dff["r2"].max()
    margin = 0.01
    fig_r2 = px.bar(dff, x="model_label", y="r2",
                    title=f"{selected_source} | {selected_currency} 決定係數 R² (放大差異)")
    fig_r2.update_yaxes(range=[max(0, r2_min - margin), min(1, r2_max + margin)])
    fig_r2.update_layout(margin={"t": 60, "b": 20, "l": 20, "r": 20})

    # --- 訓練時間 ---
    fig_time = px.bar(dff, x="model_label", y="time",
                      title=f"{selected_source} | {selected_currency} 訓練耗時 (秒)")
    fig_time.update_layout(margin={"t": 60, "b": 20, "l": 20, "r": 20})

    # --- 效率 vs 準確度 (scatter) ---
    fig_scatter = px.scatter(dff, x="time", y="r2", color="model_label",
                             hover_data=["units", "layers", "epochs", "batch_size"],
                             title=f"{selected_source} | {selected_currency} 效率 vs 準確度 (訓練時間 vs R²)")
    fig_scatter.update_layout(showlegend=False, margin={"t": 60, "b": 20, "l": 20, "r": 20})

    # --- 誤差分布 (boxplot) ---
    df_melted = dff.melt(id_vars=["model_label"], value_vars=["mae", "rmse", "mape"],
                         var_name="metric", value_name="value")

    fig_box = go.Figure()
    for m in df_melted["metric"].unique():
        fig_box.add_trace(go.Box(
            y=df_melted[df_melted["metric"] == m]["value"],
            x=df_melted[df_melted["metric"] == m]["model_label"],
            name=m
        ))
    fig_box.update_layout(
        title=f"{selected_source} | {selected_currency} 模型誤差分布 (MAE / RMSE / MAPE)",
        xaxis_title="模型版本",
        yaxis_title="誤差值",
        margin={"t": 80, "b": 20, "l": 20, "r": 20},
        legend=dict(
            orientation="h",   # 水平
            yanchor="bottom",
            y=1.02,            # 在圖表上方
            xanchor="center",
            x=0.1              # 置中
        )
    )

    return fig_errors, fig_r2, fig_time, fig_scatter, fig_box

# 7️⃣ 啟動
if __name__ == "__main__":
    app.run(debug=True, port=5007)


# In[7]:


# ======= 1️⃣ MySQL 連線 & 讀取資料 =======
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")
df = pd.read_sql("SELECT * FROM lstm_model_metrics", engine)

# ======= 2️⃣ 建立 Dash App =======
app = Dash(__name__)
app.title = "LSTM 單參數敏感度分析"

param_options = ["layers","units","epochs","batch_size"]
metric_options = ["mae","rmse","mape","r2","time"]

# ======= 3️⃣ Layout =======
app.layout = html.Div([
    html.H1("📊 LSTM 單參數敏感度分析", style={"textAlign":"center"}),

    # 來源選單
    html.Div([
        html.Label("選擇來源:"),
        dcc.Dropdown(
            id="source-selector",
            options=[{"label": s, "value": s} for s in df["source"].unique()],
            value=df["source"].unique()[0],
            clearable=False
        )
    ], style={"margin":"10px"}),

    # 幣別選單
    html.Div([
        html.Label("選擇幣別:"),
        dcc.Dropdown(
            id="currency-selector",
            clearable=False
        )
    ], style={"margin":"10px"}),

    # 模型版本選單（可讀 label）
    html.Div([
        html.Label("選擇模型版本:"),
        dcc.Dropdown(
            id="model-selector",
            multi=True
        )
    ], style={"margin":"10px"}),

    # 單參數 X 軸
    html.Div([
        html.Label("選擇分析參數 (X軸):"),
        dcc.Dropdown(
            id="param-selector",
            options=[{"label": p, "value": p} for p in param_options],
            value="layers",
            clearable=False
        )
    ], style={"margin":"10px"}),

    # 指標 Y 軸
    html.Div([
        html.Label("選擇指標 (Y軸):"),
        dcc.Dropdown(
            id="metric-selector",
            options=[{"label": m.upper(), "value": m} for m in metric_options],
            value="mae",
            clearable=False
        )
    ], style={"margin":"10px"}),

    # 圖表
    dcc.Graph(id="param-bar-chart")

], style={"padding":"20px", "backgroundColor":"white","color":"black"})

# ======= 4️⃣ Callback: 更新幣別選單 =======
@app.callback(
    Output("currency-selector","options"),
    Output("currency-selector","value"),
    Input("source-selector","value")
)
def update_currency_options(selected_source):
    currencies = df[df["source"]==selected_source]["currency"].unique()
    options = [{"label": c, "value": c} for c in currencies]
    return options, currencies[0]

# ======= 5️⃣ Callback: 更新模型選單（可讀 label） =======
@app.callback(
    Output("model-selector","options"),
    Output("model-selector","value"),
    Input("source-selector","value"),
    Input("currency-selector","value")
)
def update_model_options(selected_source, selected_currency):
    subset = df[(df.source==selected_source) & (df.currency==selected_currency)]
    options = [
        {
            "label": f"layers={r.layers}, units={r.units}, epochs={r.epochs}, batch={r.batch_size}",
            "value": r.model_version
        }
        for r in subset.itertuples()
    ]
    values = [r.model_version for r in subset.itertuples()]  # 預設全選
    return options, values

# ======= 6️⃣ Callback: 畫 Bar Chart =======
@app.callback(
    Output("param-bar-chart","figure"),
    Input("source-selector","value"),
    Input("currency-selector","value"),
    Input("model-selector","value"),
    Input("param-selector","value"),   # 選 X 軸參數
    Input("metric-selector","value")   # 選 Y 軸指標
)
def update_bar_chart(selected_source, selected_currency, selected_models, x_param, y_metric):
    dff = df[
        (df.source == selected_source) &
        (df.currency == selected_currency) &
        (df.model_version.isin(selected_models))
    ]

    fig = go.Figure()

    # 假設你想去掉 "batch_size"
    param_options_filtered = [p for p in param_options if p != x_param]
    # 依 units, epochs, batch_size 分組，顏色一致
    for i, (combo, group) in enumerate(dff.groupby(param_options_filtered)):
        # 將 X 軸轉成字串，確保是離散分類
        x_vals = [str(getattr(r, x_param)) for r in group.itertuples()]
        y_vals = [getattr(r, y_metric) for r in group.itertuples()]
        hover_texts = [
            f"layers={r.layers}, units={r.units}, epochs={r.epochs}, batch={r.batch_size}" 
            for r in group.itertuples()
        ]
        name_label = "_".join([f"{p[0]}={getattr(group.iloc[0], p)}" for p in param_options_filtered if p != x_param])

        fig.add_trace(go.Bar(
            x=x_vals,
            y=y_vals,
            name=name_label,
            hovertext=hover_texts
        ))

    fig.update_layout(
        title=f"{selected_source} | {selected_currency}: {x_param} vs {y_metric.upper()}",
        xaxis_title=x_param,
        yaxis_title=y_metric.upper(),
        barmode="group",
        showlegend=True,
        margin={"t":80,"b":40,"l":60,"r":20}
    )

    return fig



# ======= 7️⃣ 啟動 App =======
if __name__=="__main__":
    app.run(debug=True, port=5008)


# In[8]:


# ========= 連線 MySQL =========
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")

def get_lstm_model_metrics():
    query = "SELECT * FROM lstm_model_metrics"
    df = pd.read_sql(query, engine)
    return df

df = get_lstm_model_metrics()

# ========= Dash App =========
app = Dash(__name__)
app.title = "LSTM 模型比較 Dashboard"

# ========= Layout =========
app.layout = html.Div([
    html.H1("📊 LSTM 模型比較分析", style={"textAlign":"center"}),

    # 選單區
    html.Div([
        html.Label("選擇來源:"),
        dcc.Dropdown(
            id="source-selector",
            options=[{"label": s, "value": s} for s in df["source"].unique()],
            value=df["source"].unique()[0],
            clearable=False
        )
    ]),
    html.Div([
        html.Label("選擇幣別:"),
        dcc.Dropdown(
            id="currency-selector",
            options=[{"label": c, "value": c} for c in df["currency"].unique()],
            value=df["currency"].unique()[0],
            clearable=False
        )
    ]),
    html.Div([
        html.Label("選擇模型:"),
        dcc.Dropdown(
            id="model-selector",
            multi=True
        )
    ]),

    html.Hr(),

    # Correlation Matrix 區
    html.Div([
        html.H3("🔹 模型參數與指標相關矩陣"),
        dcc.Graph(id="corr-matrix")
    ])

], style={"padding": "20px", "backgroundColor": "white", "color": "black"})


# ========= Callback 1: 更新模型選單 =========
@app.callback(
    Output("model-selector", "options"),
    Output("model-selector", "value"),
    Input("source-selector", "value"),
    Input("currency-selector", "value")
)
def update_model_options(selected_source, selected_currency):
    dff = df[(df["source"] == selected_source) & (df["currency"] == selected_currency)]
    options = [
        {"label": f"l{r.layers}_u{r.units}_e{r.epochs}_b{r.batch_size}", "value": r.model_version}
        for r in dff.itertuples()
    ]
    return options, [o["value"] for o in options]  # 預設全選


# ========= Callback 2: Correlation Matrix =========
@app.callback(
    Output("corr-matrix", "figure"),
    Input("source-selector", "value"),
    Input("currency-selector", "value"),
    Input("model-selector", "value")
)
def update_corr_matrix(selected_source, selected_currency, selected_models):
    dff = df[
        (df["source"] == selected_source) &
        (df["currency"] == selected_currency) &
        (df["model_version"].isin(selected_models))
    ]

    corr_cols = ["layers", "units", "epochs", "batch_size", "mae", "rmse", "mape", "r2", "time"]
    corr_df = dff[corr_cols].corr()

    fig = px.imshow(
        corr_df,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        title=f"{selected_source} | {selected_currency} 模型參數與指標相關矩陣",
        aspect="auto"
    )
    fig.update_layout(
        margin={"t": 80, "b": 40, "l": 40, "r": 20},
        xaxis_title="",
        yaxis_title=""
    )
    return fig


# ========= 啟動 =========
if __name__ == "__main__":
    app.run(debug=True, port=5009)

