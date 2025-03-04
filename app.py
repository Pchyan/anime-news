# app.py
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import openrouter  # 引入 OpenRouter 庫
import lxml  # 確保 lxml 庫被導入

app = Flask(__name__)

# 儲存抓取的消息
news_list = []

# 設定 OpenRouter API 金鑰
openrouter.api_key = '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'

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
            date = date_div.find('div', class_='NA_card_date').get_text(strip=True) if date_div else "未知日期"
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

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        url = request.form['url']
        # 獲取文章內容
        response = requests.get(url)
        response.raise_for_status()  # 檢查請求是否成功
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 假設文章內容在某個標籤中，這裡需要根據實際情況調整
        content = soup.find('div', class_='article-content')  # 根據實際情況調整
        if content is None:
            raise ValueError("未能找到文章內容")  # 如果找不到內容，拋出錯誤
        
        content_text = content.get_text(strip=True)  # 根據實際情況調整
        print(f"抓取的內容: {content_text}")  # 打印抓取的內容

        # 使用 OpenRouter API 進行彙整
        summary = openrouter.summarize(
            content=content_text,
            model="deepseek/deepseek-r1-distill-llama-70b:free",  # 根據需要選擇模型
            options={"language": "zh-TW"}  # 設置語言選項
        )

        summarized_text = summary['summary']
        print(f"API 響應: {summary}")  # 打印 API 響應
        return render_template('summary.html', summary=summarized_text)

    except Exception as e:
        print(f"發生錯誤: {e}")  # 打印錯誤信息
        return "發生錯誤，請稍後再試。", 500  # 返回 500 錯誤

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_news, 'interval', minutes=30)  # 每30分鐘抓取一次
    scheduler.start()
    fetch_news()  # 啟動時立即抓取一次
    app.run(debug=True)