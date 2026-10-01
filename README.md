# 匯率預測分析平台（Exchange Rate Forecast）

從資料蒐集、儲存、建模到網頁展示的完整匯率分析系統，以 **LSTM** 預測下一交易日匯率，並系統化比較不同超參數的模型表現。

> 國立中央大學「生成式人工智慧與 Python 程式設計跨域應用」期末個人專案

## 功能

- 爬取台灣銀行牌告匯率與中央銀行統計資料庫（18 種幣別），可指定月份抓取歷史資料
- pandas 清理後以 SQLAlchemy 寫入 MySQL（寬表：每列一個交易日、每欄一個幣別）
- LSTM 以前 30 筆匯率預測下一筆（日資料即下一交易日），訓練與測試集依時間順序 8:2 切分；以月資料比較 16 組層數、神經元數、訓練輪數與批次大小的組合
- 每組設定的 MAE、RMSE、MAPE、R² 存入資料庫，以 Dash 儀表板互動比較
- Flask + Jinja2 + Plotly 網站，AJAX 依選單即時更新圖表

## 系統架構

```
requests + BeautifulSoup 爬蟲 → pandas 清理 → MySQL（SQLAlchemy）
        → Keras LSTM（超參數實驗結果寫回資料庫）
        → Flask + Jinja2 + Plotly / Dash 儀表板
```

| 路徑 | 內容 |
|---|---|
| `app.py` | Flask 網站（首頁、爬蟲、資料庫、預測頁） |
| `nb/` | 開發過程的 notebook：爬蟲 → 資料庫 → LSTM |
| `templates/`、`static/` | 網頁模板與靜態資源（版型來自 HTML5 UP Editorial） |
| `Dockerfile`、`flask-deployment.yaml` | 容器化與 Kubernetes 部署設定（規劃中） |

## 執行方式

需求：Python 3.11、MySQL 8。

```bash
pip install -r requirements.txt
cp .env.example .env     # 填入 MySQL 連線字串
python app.py            # http://localhost:5000
```

`nb/` 中的 notebook 使用 `YOUR_MYSQL_PASSWORD` 作為密碼佔位字，執行前請改成自己的設定。

## 限制與後續

- Kubernetes（AKS）部署僅完成設計，尚未實際部署。
- 匯率時序自相關高，後續應加入「以前一日值預測」的 baseline 比較，以確認模型的實際效益。
