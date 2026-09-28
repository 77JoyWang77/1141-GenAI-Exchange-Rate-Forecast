#!/usr/bin/env python
# coding: utf-8

# In[2]:


import itertools
import time
from datetime import datetime
import requests
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import errorcode
from sqlalchemy import create_engine, text

import plotly.graph_objects as go
import plotly.express as px
import dash
from dash import dcc, html, Input, Output

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout, Input


# In[3]:


# 1️⃣ 連接 MySQL
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")
query = "SELECT Date, NTD_USD FROM bp01d01_rates ORDER BY Date"
df = pd.read_sql(query, engine, parse_dates=["Date"])
df = df.set_index('Date')

# 2️⃣ 資料正規化 (LSTM 通常要 0~1)
scaler = MinMaxScaler(feature_range = (0, 1))
scaled_data = scaler.fit_transform(df.values)


# In[4]:


# 3️⃣ 建立時間序列資料 (例如用前 30 天預測下一天)
SEQ_LEN = 30
X, y = [], []
for i in range(SEQ_LEN, len(scaled_data)):
    X.append(scaled_data[i-SEQ_LEN:i, 0])
    y.append(scaled_data[i, 0])
X, y = np.array(X), np.array(y)
X = np.reshape(X, (X.shape[0], X.shape[1], 1))  # (samples, timesteps, features)

# 拆訓練集 / 測試集
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]


# In[ ]:


# 4️⃣ 建立 LSTM 模型
model = Sequential()
model.add(Input(shape=(X_train.shape[1], 1)))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')

# 訓練
model.fit(X_train, y_train, epochs=20, batch_size=16, verbose=1)


# In[ ]:


# 5️⃣ 預測
y_pred = model.predict(X_test)
y_pred_inv = scaler.inverse_transform(y_pred.reshape(-1, 1))
y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))


#  📊 LSTM 預測模型評估指標說明
# 
# 在時間序列模型（如 LSTM）中，我們通常會使用以下指標來衡量預測表現：
# 
# ---
# 
#  1. MAE (Mean Absolute Error) 平均絕對誤差
# **公式：**
# $$
# MAE = \frac{1}{n}\sum_{i=1}^{n} \left| y_i - \hat{y}_i \right|
# $$
# 
# **解釋：**
# - 代表預測值與真實值「平均相差多少」。
# - 單位與原始數據一致（例如匯率 = 新台幣元）。
# - **越接近 0 越好**。
# 
# ---
# 
#  2. RMSE (Root Mean Squared Error) 均方根誤差
# **公式：**
# $$
# RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n} (y_i - \hat{y}_i)^2}
# $$
# 
# **解釋：**
# - 與 MAE 類似，但對「大誤差」懲罰更嚴格。
# - 如果模型偶爾出現偏差很大的預測，RMSE 會比 MAE 高很多。
# - **越接近 0 越好**。
# 
# ---
# 
#  3. MAPE (Mean Absolute Percentage Error) 平均絕對百分比誤差
# **公式：**
# $$
# MAPE = \frac{100\%}{n}\sum_{i=1}^{n}\left|\frac{y_i - \hat{y}_i}{y_i}\right|
# $$
# 
# **解釋：**
# - 用「百分比」表示誤差，更直觀。
# - 例如 MAPE = 2% → 代表平均預測值與真實值差距 2%。
# - **越接近 0% 越好**。
# - ⚠️ 注意：若真實值接近 0，MAPE 可能會失真。
# 
# ---
# 
#  4. R² (決定係數, Coefficient of Determination)
# **公式：**
# $$
# R^2 = 1 - \frac{\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{n}(y_i - \bar{y})^2}
# $$
# 
# **解釋：**
# - 衡量模型比「用平均值亂猜」好多少。
# - 範圍通常在 0 ~ 1 之間：
#   - **R² = 1** → 完美預測  
#   - **R² = 0** → 跟亂猜一樣爛  
#   - **R² < 0** → 還比亂猜更差  
# 
# ---
# 
#  ✅ 評估指標總結
# - **MAE, RMSE, MAPE → 越小越好（理想 = 0）**
# - **R² → 越大越好（理想 = 1）**
# 
# 👉 白話理解：
# - MAE / RMSE = 預測「誤差距離」
# - MAPE = 預測「誤差百分比」
# - R² = 模型「理解資料的程度」
# 

# In[36]:


# 6️⃣ 計算評分
mae = mean_absolute_error(y_test_inv, y_pred_inv)
rmse = np.sqrt(mean_squared_error(y_test_inv, y_pred_inv))
mape = np.mean(np.abs((y_test_inv - y_pred_inv) / y_test_inv)) * 100
r2 = r2_score(y_test_inv, y_pred_inv)

print(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}, MAPE: {mape:.2f}%, R²: {r2:.4f}")


# In[43]:


# 7️⃣ 建立 Dash 顯示
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='rate-graph'),
    html.Div([
        html.P(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}, MAPE: {mape:.2f}%, R²: {r2:.4f}")
    ], style={'textAlign':'center', 'fontSize':18})
], style={"padding": "20px", "backgroundColor": "white", "color": "black"})

@app.callback(
    Output('rate-graph', 'figure'),
    Input('rate-graph', 'id')  # dummy input 觸發一次更新
)
def update_graph(_):
    fig = go.Figure()
    # 只畫測試集的實際值
    test_dates = df.index[-len(y_test):]
    fig.add_trace(go.Scatter(
        x=test_dates,
        y=y_test_inv.flatten(),
        mode='lines',
        name='實際匯率'
    ))

    # 預測值
    fig.add_trace(go.Scatter(
        x=test_dates,
        y=y_pred_inv.flatten(),
        mode='lines',
        name='預測匯率'
    ))
    fig.update_layout(
        title=f"NTD_USD LSTM",
        xaxis_title="日期",
        yaxis_title="匯率",
        margin={"t": 80, "b": 40, "l": 20, "r": 20},
        xaxis=dict(
            rangeslider=dict(visible=True),  # 顯示橫向滑桿
            fixedrange=False
        ),
        yaxis=dict(fixedrange=False),
        legend=dict(
            orientation="h",   # 水平
            yanchor="bottom",
            y=1.02,            # 在圖表上方
            xanchor="center",
            x=0.1              # 置中
        )
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=5004)


# In[7]:


# MySQL 連線
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")

# 建立資料表
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS predictions (
            model_version VARCHAR(50) PRIMARY KEY,
            date DATE PRIMARY KEY,
            true_rate FLOAT,
            pred_rate FLOAT
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lstm_model_metrics (
            model_version VARCHAR(50) PRIMARY KEY,
            source VARCHAR(20),
            currency VARCHAR(10),
            layers INT,
            units INT,
            epochs INT,
            batch_size INT,
            mae FLOAT,
            rmse FLOAT,
            mape FLOAT,
            r2 FLOAT,
            time FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))


# In[3]:


# 1️⃣ 連接 MySQL
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")
currency = "JPY_USD"  # 你要預測的幣別
source = "bp01m01_rates"
query = f"SELECT Date, {currency} FROM {source} ORDER BY Date"
df = pd.read_sql(query, engine, parse_dates=["Date"])
df = df.set_index('Date')

# 2️⃣ 資料正規化 (LSTM 通常要 0~1)
scaler = MinMaxScaler(feature_range = (0, 1))
scaled_data = scaler.fit_transform(df.values)


# In[4]:


# 3️⃣ 建立時間序列資料 (例如用前 30 天預測下一天)
SEQ_LEN = 30
X, y = [], []
for i in range(SEQ_LEN, len(scaled_data)):
    X.append(scaled_data[i-SEQ_LEN:i, 0])
    y.append(scaled_data[i, 0])
X, y = np.array(X), np.array(y)
X = np.reshape(X, (X.shape[0], X.shape[1], 1))  # (samples, timesteps, features)

# 拆訓練集 / 測試集
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]
test_dates = df.index[-len(y_test):]


# In[11]:


param_grid = { 
    "layers": [1, 2], 
    "units": [50, 100], 
    "epochs": [20, 50], 
    "batch_size": [16, 32] 
}

# 建立連線
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_MYSQL_PASSWORD",
    database="exchange_db"
)
cursor = conn.cursor()

for layers, units, epochs, batch_size in itertools.product(
    param_grid["layers"], param_grid["units"], param_grid["epochs"], param_grid["batch_size"]
):
    model_version = f"{source}_{currency}_l{layers}_u{units}_e{epochs}_b{batch_size}"
    print(f"▶ 測試組合：{model_version}")

    # 模型建立、訓練、預測流程（同之前）
    model = Sequential()
    model.add(Input(shape=(X_train.shape[1], 1)))
    for i in range(layers):
        return_seq = (i < layers - 1)
        model.add(LSTM(units=units, return_sequences=return_seq))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mse")

    start = time.time()
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
    duration = time.time() - start

    y_pred = model.predict(X_test)
    y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))
    y_pred_inv = scaler.inverse_transform(y_pred)

    mae = mean_absolute_error(y_test_inv, y_pred_inv)
    rmse = np.sqrt(mean_squared_error(y_test_inv, y_pred_inv))
    mape = np.mean(np.abs((y_test_inv - y_pred_inv) / y_test_inv)) * 100
    r2 = r2_score(y_test_inv, y_pred_inv)

    # 寫入 predictions 表
    for date_val, true_val, pred_val in zip(test_dates, y_test_inv.flatten(), y_pred_inv.flatten()):
        # 轉型別
        true_val = float(true_val)
        pred_val = float(pred_val)
        if isinstance(date_val, np.datetime64):
            date_val = pd.to_datetime(date_val).to_pydatetime()

        sql_pred = """
        INSERT INTO predictions (model_version, date, true_rate, pred_rate)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            true_rate=VALUES(true_rate),
            pred_rate=VALUES(pred_rate)
        """
        cursor.execute(sql_pred, (model_version, date_val, true_val, pred_val))

    conn.commit()

    # 寫入 lstm_model_metrics
    sql = """
    INSERT INTO lstm_model_metrics
    (model_version, source, currency, layers, units, epochs, batch_size, mae, rmse, mape, r2, time, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        mae=VALUES(mae),
        rmse=VALUES(rmse),
        mape=VALUES(mape),
        r2=VALUES(r2),
        time=VALUES(time),
        created_at=VALUES(created_at)
    """
    values = (
        model_version, source, currency,
        int(layers), int(units), int(epochs), int(batch_size),
        float(mae), float(rmse), float(mape), float(r2), float(duration), datetime.now()
    )
    cursor.execute(sql, values)
    conn.commit()

    print(f"✅ 完成 {model_version}, MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")

cursor.close()
conn.close()

