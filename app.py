# app.py
from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 儲存抓取的消息
news_list = []

def fetch_news():
    global news_list
    news_list = []  # 清空舊的消息

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.33'}

    # 日本動漫消息來源
    jp_url = 'https://natalie.mu/comic'
    jp_response = requests.get(jp_url, headers=headers)
    print("日本動漫消息響應狀態:", jp_response.status_code)  # 調試輸出
    jp_soup = BeautifulSoup(jp_response.text, 'html.parser')
    print(jp_soup.prettify())  # 打印抓取的 HTML 內容

    # 更新選擇器
    jp_articles = jp_soup.find_all('div', class_='NA_card')  # 根據實際 HTML 結構更新選擇器

    print(f"找到的日本動漫文章數量: {len(jp_articles)}")  # 調試輸出

    for article in jp_articles:
        title = article.find('p', class_='NA_card_title').get_text(strip=True)
        link = article.find('a')['href']
        
        # 嘗試獲取日期，並添加條件檢查
        date_div = article.find('div', class_='NA_card_data')
        if date_div:
            date = date_div.find('div', class_='NA_card_date')
            date = date.get_text(strip=True) if date else "未知日期"  # 如果找不到日期，設置為 "未知日期"
        else:
            date = "未知日期"  # 如果找不到 NA_card_data，設置為 "未知日期"
        
        news_list.append({'title': title, 'link': link, 'date': date})

    # 台灣動漫消息來源
    tw_url = 'https://gnn.gamer.com.tw/index.php?k=5'
    tw_response = requests.get(tw_url, headers=headers)
    print("台灣動漫消息響應狀態:", tw_response.status_code)  # 調試輸出
    tw_soup = BeautifulSoup(tw_response.text, 'html.parser')
    print(tw_soup.prettify())  # 打印抓取的 HTML 內容

    # 更新選擇器
    tw_articles = tw_soup.find_all('h1', class_='GN-lbox2D')  # 根據實際 HTML 結構更新選擇器

    for article in tw_articles:
        title = article.get_text(strip=True)
        link = article.find('a')['href']
        
        # 嘗試獲取日期，並添加條件檢查
        date_span = article.find('span', class_='NA_card_date')
        date = date_span.get_text(strip=True) if date_span else "未知日期"  # 如果找不到日期，設置為 "未知日期"
        
        news_list.append({'title': title, 'link': link, 'date': date})

    # 按時間排序，假設日期格式為 'YYYY-MM-DD'，需要根據實際格式進行調整
    news_list.sort(key=lambda x: x['date'], reverse=True)

    print("抓取的消息數量:", len(news_list))  # 調試輸出

@app.route('/')
def index():
    return render_template('index.html', news=news_list)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_news, 'interval', minutes=30)  # 每30分鐘抓取一次
    scheduler.start()
    fetch_news()  # 啟動時立即抓取一次
    app.run(debug=True)