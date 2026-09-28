#!/usr/bin/env python
# coding: utf-8

# In[2]:


import requests
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import errorcode
from sqlalchemy import create_engine, text
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output


# In[75]:


url_daily = "https://cpx.cbc.gov.tw/API/DataAPI/Get?FileName=BP01D01"
resp = requests.get(url_daily)
data_daily = resp.json()

# 2. 取得每日資料
daily_data = data_daily['data']['dataSets']

# 3. 幣別欄位名稱
columns_daily = ['Date', 'NTD_USD','JPY_USD','USD_GBP','HKD_USD','KRW_USD','CAD_USD',
           'SGD_USD','CNY_USD','USD_AUD','IDR_USD','THB_USD','MYR_USD','PHP_USD',
           'USD_EUR','DEM_USD','FRF_USD','NLG_USD','VND_USD']

# 4. 轉成 DataFrame
df_daily = pd.DataFrame(daily_data, columns=columns_daily)

df_daily = df_daily.replace("-", None)
df_daily["Date"] = pd.to_datetime(df_daily["Date"], format="%Y%m%d")

print(df_daily.head())


# In[76]:


url_monthly = "https://cpx.cbc.gov.tw/API/DataAPI/Get?FileName=BP01M01"
resp = requests.get(url_monthly)
data_monthly = resp.json()

# 2. 取得每日資料
monthly_data = data_monthly['data']['dataSets']

# 3. 幣別欄位名稱
columns_monthly = ['Date', 'NTD_USD','JPY_USD','USD_GBP','HKD_USD','KRW_USD','CAD_USD',
           'SGD_USD','CNY_USD','USD_AUD','IDR_USD','THB_USD','MYR_USD','PHP_USD',
           'USD_EUR','DEM_USD','FRF_USD','NLG_USD','VND_USD']

# 4. 轉成 DataFrame
df_monthly = pd.DataFrame(monthly_data, columns=columns_monthly)

df_monthly = df_monthly.replace("-", None)
df_monthly["Date"] = pd.to_datetime(df_monthly["Date"], format="%YM%m")

print(df_monthly.head())


# In[93]:


url_yearly = "https://cpx.cbc.gov.tw/API/DataAPI/Get?FileName=BP01Y01"
resp = requests.get(url_yearly)
data_yearly = resp.json()

# 2. 取得每日資料
yearly_data = data_yearly['data']['dataSets']

# 3. 幣別欄位名稱
columns_yearly = ['Date', 'NTD_USD','JPY_USD','USD_GBP','HKD_USD','KRW_USD','CAD_USD',
           'SGD_USD','CNY_USD','USD_AUD','IDR_USD','THB_USD','MYR_USD','PHP_USD',
           'USD_EUR','DEM_USD','FRF_USD','NLG_USD','VND_USD']

# 4. 轉成 DataFrame
df_yearly = pd.DataFrame(yearly_data, columns=columns_yearly)
df_yearly["Date"] = pd.to_datetime(df_yearly["Date"], format="%Y")

df_yearly = df_yearly.replace("-", None)

print(df_yearly.head())


# In[89]:


cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_MYSQL_PASSWORD",
    database="exchange_db"
)
cursor = cnx.cursor()

create_table = """
CREATE TABLE IF NOT EXISTS bp01d01_rates (
    Date DATE PRIMARY KEY,
    NTD_USD FLOAT,
    JPY_USD FLOAT,
    USD_GBP FLOAT,
    HKD_USD FLOAT,
    KRW_USD FLOAT,
    CAD_USD FLOAT,
    SGD_USD FLOAT,
    CNY_USD FLOAT,
    USD_AUD FLOAT,
    IDR_USD FLOAT,
    THB_USD FLOAT,
    MYR_USD FLOAT,
    PHP_USD FLOAT,
    USD_EUR FLOAT,
    DEM_USD FLOAT,
    FRF_USD FLOAT,
    NLG_USD FLOAT,
    VND_USD FLOAT
)
"""
cursor.execute(create_table)

for index, row in df_daily.iterrows():
    sql = """
    REPLACE INTO bp01d01_rates
    (Date, NTD_USD, JPY_USD, USD_GBP, HKD_USD, KRW_USD, CAD_USD,
     SGD_USD, CNY_USD, USD_AUD, IDR_USD, THB_USD, MYR_USD, PHP_USD,
     USD_EUR, DEM_USD, FRF_USD, NLG_USD, VND_USD)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, tuple(row))

cnx.commit()
cursor.close()
cnx.close()

print("資料已成功存入 MySQL")


# In[88]:


cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_MYSQL_PASSWORD",
    database="exchange_db"
)
cursor = cnx.cursor()

create_table = """
CREATE TABLE IF NOT EXISTS bp01m01_rates (
    Date DATE PRIMARY KEY,
    NTD_USD FLOAT,
    JPY_USD FLOAT,
    USD_GBP FLOAT,
    HKD_USD FLOAT,
    KRW_USD FLOAT,
    CAD_USD FLOAT,
    SGD_USD FLOAT,
    CNY_USD FLOAT,
    USD_AUD FLOAT,
    IDR_USD FLOAT,
    THB_USD FLOAT,
    MYR_USD FLOAT,
    PHP_USD FLOAT,
    USD_EUR FLOAT,
    DEM_USD FLOAT,
    FRF_USD FLOAT,
    NLG_USD FLOAT,
    VND_USD FLOAT
)
"""
cursor.execute(create_table)

for index, row in df_monthly.iterrows():
    sql = """
    REPLACE INTO bp01m01_rates
    (Date, NTD_USD, JPY_USD, USD_GBP, HKD_USD, KRW_USD, CAD_USD,
     SGD_USD, CNY_USD, USD_AUD, IDR_USD, THB_USD, MYR_USD, PHP_USD,
     USD_EUR, DEM_USD, FRF_USD, NLG_USD, VND_USD)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, tuple(row))

cnx.commit()
cursor.close()
cnx.close()

print("資料已成功存入 MySQL")


# In[98]:


cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_MYSQL_PASSWORD",
    database="exchange_db"
)
cursor = cnx.cursor()

create_table = """
CREATE TABLE IF NOT EXISTS bp01y01_rates (
    Date DATE PRIMARY KEY,
    NTD_USD FLOAT,
    JPY_USD FLOAT,
    USD_GBP FLOAT,
    HKD_USD FLOAT,
    KRW_USD FLOAT,
    CAD_USD FLOAT,
    SGD_USD FLOAT,
    CNY_USD FLOAT,
    USD_AUD FLOAT,
    IDR_USD FLOAT,
    THB_USD FLOAT,
    MYR_USD FLOAT,
    PHP_USD FLOAT,
    USD_EUR FLOAT,
    DEM_USD FLOAT,
    FRF_USD FLOAT,
    NLG_USD FLOAT,
    VND_USD FLOAT
)
"""
cursor.execute(create_table)

for index, row in df_yearly.iterrows():
    sql = """
    REPLACE INTO bp01y01_rates
    (Date, NTD_USD, JPY_USD, USD_GBP, HKD_USD, KRW_USD, CAD_USD,
     SGD_USD, CNY_USD, USD_AUD, IDR_USD, THB_USD, MYR_USD, PHP_USD,
     USD_EUR, DEM_USD, FRF_USD, NLG_USD, VND_USD)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, tuple(row))

cnx.commit()
cursor.close()
cnx.close()

print("資料已成功存入 MySQL")


# In[104]:


# 連接 MySQL
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")
query = "SELECT Date, NTD_USD FROM bp01d01_rates ORDER BY Date"
df = pd.read_sql(query, engine, parse_dates=["Date"])

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["NTD_USD"],
    mode='lines',
    name='新台幣對美元'
))

fig.update_layout(
    title="匯率走勢圖NTD/USD",
    xaxis_title="日期",
    yaxis_title="匯率",
    margin={"t": 60, "b": 40, "l": 60, "r": 20},
    xaxis=dict(
        rangeslider=dict(visible=True),  # 顯示橫向滑桿
        fixedrange=False
    ),
    yaxis=dict(fixedrange=False)
)

fig.show()


# In[1]:


# 連接 MySQL
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")
query = "SELECT * FROM bp01d01_rates ORDER BY Date"
df = pd.read_sql(query, engine, parse_dates=["Date"])

# 幣別欄位列表（去掉 Date）
currency_cols = df.columns[1:].tolist()

# 建立 Dash app
app = dash.Dash(__name__)

# Dash 佈局
app.layout = html.Div([

    # 下拉選單：多選
    html.Label("選擇幣別:"),
    dcc.Dropdown(
        id='currency-dropdown',
        options=[{'label': col, 'value': col} for col in currency_cols],
        value=[currency_cols[0]],  # 預設選第一個幣別
        multi=True
    ),

    # 繪圖區
    dcc.Graph(id='rate-graph')
], style={"padding": "20px", "backgroundColor": "white", "color": "black"})

# Callback：更新圖表
@app.callback(
    Output('rate-graph', 'figure'),
    Input('currency-dropdown', 'value')
)
def update_graph(selected_currencies):
    fig = go.Figure()
    for col in selected_currencies:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df[col],
            mode='lines',
            name=col
        ))

    fig.update_layout(
        title="匯率走勢圖",
        xaxis_title="日期",
        yaxis_title="匯率",
        margin={"t": 60, "b": 40, "l": 60, "r": 20},
        xaxis=dict(
            rangeslider=dict(visible=True),  # 顯示橫向滑桿
            fixedrange=False
        ),
        yaxis=dict(fixedrange=False)
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=5004)


# In[4]:


# 連接 MySQL
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")
query = "SELECT * FROM bp01m01_rates ORDER BY Date"
df = pd.read_sql(query, engine, parse_dates=["Date"])

# 幣別欄位列表（去掉 Date）
currency_cols = df.columns[1:].tolist()

# 建立 Dash app
app = dash.Dash(__name__)

# Dash 佈局
app.layout = html.Div([

    # 下拉選單：多選
    html.Label("選擇幣別:"),
    dcc.Dropdown(
        id='currency-dropdown',
        options=[{'label': col, 'value': col} for col in currency_cols],
        value=[currency_cols[0]],  # 預設選第一個幣別
        multi=True
    ),

    # 繪圖區
    dcc.Graph(id='rate-graph')
], style={"padding": "20px", "backgroundColor": "white", "color": "black"})

# Callback：更新圖表
@app.callback(
    Output('rate-graph', 'figure'),
    Input('currency-dropdown', 'value')
)
def update_graph(selected_currencies):
    fig = go.Figure()
    for col in selected_currencies:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df[col],
            mode='lines',
            name=col
        ))

    fig.update_layout(
        title="匯率走勢圖",
        xaxis_title="日期",
        yaxis_title="匯率",
        margin={"t": 60, "b": 40, "l": 60, "r": 20},
        xaxis=dict(
            rangeslider=dict(visible=True),  # 顯示橫向滑桿
            fixedrange=False
        ),
        yaxis=dict(fixedrange=False)
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=5001)


# In[5]:


# 連接 MySQL
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")
query = "SELECT * FROM bp01y01_rates ORDER BY Date"
df = pd.read_sql(query, engine, parse_dates=["Date"])

# 幣別欄位列表（去掉 Date）
currency_cols = df.columns[1:].tolist()

# 建立 Dash app
app = dash.Dash(__name__)

# Dash 佈局
app.layout = html.Div([

    # 下拉選單：多選
    html.Label("選擇幣別:"),
    dcc.Dropdown(
        id='currency-dropdown',
        options=[{'label': col, 'value': col} for col in currency_cols],
        value=[currency_cols[0]],  # 預設選第一個幣別
        multi=True
    ),

    # 繪圖區
    dcc.Graph(id='rate-graph')
], style={"padding": "20px", "backgroundColor": "white", "color": "black"})

# Callback：更新圖表
@app.callback(
    Output('rate-graph', 'figure'),
    Input('currency-dropdown', 'value')
)
def update_graph(selected_currencies):
    fig = go.Figure()
    for col in selected_currencies:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df[col],
            mode='lines',
            name=col
        ))

    fig.update_layout(
        title="匯率走勢圖",
        xaxis_title="日期",
        yaxis_title="匯率",
        margin={"t": 60, "b": 40, "l": 60, "r": 20},
        xaxis=dict(
            rangeslider=dict(visible=True),  # 顯示橫向滑桿
            fixedrange=False
        ),
        yaxis=dict(fixedrange=False)
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=5002)


# In[6]:


# MySQL 連線
engine = create_engine("mysql+mysqlconnector://root:YOUR_MYSQL_PASSWORD@localhost/exchange_db")

# 先抓所有幣別欄位名
query_cols = "SHOW COLUMNS FROM bp01d01_rates"
cols_df = pd.read_sql(query_cols, engine)
currencies = [c for c in cols_df['Field'] if c != 'Date']  # 去掉 Date

# 建立 Dash app
app = dash.Dash(__name__)

app.layout = html.Div([    
    # 下拉選單（改成 multi=True 可多選）
    html.Label("選擇幣別："),
    dcc.Dropdown(
        id='currency-dropdown',
        options=[{'label': cur, 'value': cur} for cur in currencies],
        value=[currencies[0]],  # 預設選第一個幣別
        multi=True,             # 多選
    ),

    # 繪圖區
    dcc.Graph(id='exchange-graph')
], style={"padding": "20px", "backgroundColor": "white", "color": "black"})

# callback 依選定幣別更新圖
@app.callback(
    Output('exchange-graph', 'figure'),
    Input('currency-dropdown', 'value')
)
def update_graph(selected_currencies):
    if not selected_currencies:
        return go.Figure()  # 沒選就回空圖

    # SQL 取多個幣別資料
    cols_sql = ", ".join([f"`{cur}`" for cur in selected_currencies])
    query = f"SELECT Date, {cols_sql} FROM bp01d01_rates ORDER BY Date"
    df = pd.read_sql(query, engine, parse_dates=['Date'])

    fig = go.Figure()
    for cur in selected_currencies:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df[cur],
            mode='lines',
            name=cur
        ))

    fig.update_layout(
        title="匯率走勢",
        xaxis_title="日期",
        yaxis_title="匯率",
        margin={"t": 60, "b": 40, "l": 60, "r": 20},
        xaxis=dict(
            rangeslider=dict(visible=True),  # 顯示橫向滑桿
            fixedrange=False
        ),
        yaxis=dict(fixedrange=False)
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=5003)

