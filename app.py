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
    jp_url = 'https://natalie.mu/comic/news'
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
            # 根據實際的 HTML 結構更新這裡的選擇器
            date = date_div.get_text(strip=True)  # 更新為直接從 date_div 獲取日期
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
        if date_span:
            date = date_span.get_text(strip=True)  # 更新為直接從 date_span 獲取日期
        else:
            date = "未知日期"  # 如果找不到日期，設置為 "未知日期"
        
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
        # 檢查 URL 是否以 http:// 或 https:// 開頭
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url  # 預設為 https://
        
        # 確保 URL 中只有一個斜線
        url = url.replace(':////', '://')  # 移除多餘的斜線
        url = url.replace(':///', '://')  # 確保只有一個斜線
        
        # 獲取文章內容
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.33'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 檢查請求是否成功
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP 錯誤: {http_err}")  # 打印 HTTP 錯誤
            return f"發生錯誤: {http_err}，請稍後再試。", 500
        except Exception as err:
            print(f"其他錯誤: {err}")  # 打印其他錯誤
            return f"發生錯誤: {err}，請稍後再試。", 500
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 根據不同網站選擇不同的內容提取方式
        content = None
        if 'natalie.mu' in url:
            content = soup.find('div', class_='NA_article_body')
        elif 'gnn.gamer.com.tw' in url:
            content = soup.find('div', class_='GN-lbox3B')
        else:
            # 嘗試一些通用的內容選擇器
            content = soup.find('article') or soup.find('div', class_='article-content') or soup.find('div', class_='content')
        
        if content is None:
            raise ValueError("未能找到文章內容")
        
        content_text = content.get_text(strip=True)
        print(f"抓取的內容長度: {len(content_text)}")  # 打印抓取的內容長度
        
        # 使用 OpenRouter API 進行彙整
        api_key = "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"
        
        # 修正 API 請求頭
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",  # 修改為本地開發環境
            "X-Title": "Anime News Summarizer"
        }
        
        # 準備請求數據
        request_data = {
            "model": "google/gemini-2.0-flash-thinking-exp:free",  # 嘗試使用不同的模型
            "messages": [
                {"role": "system", "content": "你是一個專業的內容彙整助手，請將以下動漫新聞內容進行簡潔的摘要，提取關鍵信息並以條列式呈現。如果內容是日文，請先翻譯成繁體中文再進行彙整。"},
                {"role": "user", "content": content_text[:3000]}  # 減少內容長度
            ],
            "route": "fallback"  # 添加路由選項
        }
        
        # 發送請求到 OpenRouter API
        api_response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=request_data,
            timeout=60  # 增加超時時間
        )
        
        # 檢查 API 響應
        if api_response.status_code != 200:
            print(f"API 錯誤: {api_response.status_code}, {api_response.text}")
            raise ValueError(f"API 返回錯誤: {api_response.status_code}")
        
        # 解析 API 響應
        response_data = api_response.json()
        print("API 響應:", response_data)  # 調試輸出
        
        # 檢查響應格式並提取摘要
        if 'choices' in response_data and len(response_data['choices']) > 0:
            if 'message' in response_data['choices'][0] and 'content' in response_data['choices'][0]['message']:
                summarized_text = response_data['choices'][0]['message']['content']
            else:
                raise ValueError("API 響應格式不正確: 找不到 'message.content'")
        else:
            # 嘗試其他可能的響應格式
            if 'response' in response_data:
                summarized_text = response_data['response']
            elif 'output' in response_data:
                summarized_text = response_data['output']
            else:
                raise ValueError("API 響應格式不正確: 找不到 'choices'")
        
        return render_template('summary.html', summary=summarized_text, original_url=url)

    except Exception as e:
        print(f"發生錯誤: {e}")  # 打印錯誤信息
        import traceback
        traceback.print_exc()  # 打印完整的錯誤堆疊
        return f"發生錯誤: {str(e)}，請稍後再試。", 500  # 返回 500 錯誤

@app.route('/yahoo-news')
def yahoo_news():
    # 定義要抓取的頁面 URL
    yahoo_urls = [
        'https://news.yahoo.co.jp/topics/top-picks',  # 第一頁
        'https://news.yahoo.co.jp/topics/top-picks?page=2'  # 第二頁
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.33'
    }
    
    news_items = []  # 儲存所有新聞項目的列表

    for yahoo_url in yahoo_urls:
        response = requests.get(yahoo_url, headers=headers)
        print(f"Yahoo 響應狀態: {response.status_code}")  # 調試輸出
        response.raise_for_status()  # 檢查請求是否成功
        soup = BeautifulSoup(response.text, 'html.parser')

        # 抓取新聞標題和連結
        articles = soup.find_all('li', class_='sc-1u4589e-0 kKmBYF')  # 根據實際 HTML 結構更新選擇器
        
        print(f"找到的新聞數量: {len(articles)}")  # 調試輸出

        for article in articles:
            link_tag = article.find('a')
            if link_tag:  # 確保找到 <a> 標籤
                title = link_tag.get_text(strip=True)
                link = link_tag['href']
                news_items.append({'title': title, 'link': link})
            else:
                print("未找到 <a> 標籤，跳過此文章")  # 調試輸出

    return render_template('yahoo_news.html', news=news_items)

@app.route('/taiwan-yahoo-news')
def taiwan_yahoo_news():
    taiwan_yahoo_url = 'https://tw.news.yahoo.com/archive/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.33'
    }
    
    response = requests.get(taiwan_yahoo_url, headers=headers)
    print(f"台灣 Yahoo 響應狀態: {response.status_code}")  # 調試輸出
    response.raise_for_status()  # 檢查請求是否成功
    soup = BeautifulSoup(response.text, 'html.parser')

    # 抓取即時新聞標題和連結
    news_items = []
    articles = soup.find_all('h3', class_='Mb(5px)')  # 根據實際 HTML 結構更新選擇器
    
    print(f"找到的即時新聞數量: {len(articles)}")  # 調試輸出

    for article in articles:
        link_tag = article.find('a')
        if link_tag:  # 確保找到 <a> 標籤
            title = link_tag.get_text(strip=True)
            link = link_tag['href']
            # 檢查連結是否為相對 URL，並轉換為完整的 URL
            if not link.startswith('http'):
                link = 'https://tw.news.yahoo.com' + link  # 添加主域名
            news_items.append({'title': title, 'link': link})
        else:
            print("未找到 <a> 標籤，跳過此文章")  # 調試輸出

    return render_template('taiwan_yahoo_news.html', news=news_items)

@app.route('/google-news')
def google_news():
    google_news_url = 'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.33'
    }
    
    # 抓取 Google 新聞主頁
    response = requests.get(google_news_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    news_items = []
    articles = soup.find_all('div', class_='XlKvRb')  # 每個主題區塊

    for article in articles:
        # 尋找「完整報導」連結
        coverage_link_tag = article.find('a', string='完整報導')  # 假設連結文字為「完整報導」
        if not coverage_link_tag:
            continue  # 如果找不到，跳過此區塊
        
        coverage_url = coverage_link_tag['href']
        if not coverage_url.startswith('http'):
            coverage_url = 'https://news.google.com' + coverage_url

        # 訪問「完整報導」頁面
        coverage_response = requests.get(coverage_url, headers=headers)
        coverage_response.raise_for_status()
        coverage_soup = BeautifulSoup(coverage_response.text, 'html.parser')

        # 提取第一則新聞
        first_article = coverage_soup.find('h3')  # 假設第一則新聞的標題在 h3 中
        if first_article:
            link_tag = first_article.find('a')
            if link_tag:
                title = link_tag.get_text(strip=True)
                link = link_tag['href']
                if not link.startswith('http'):
                    link = 'https://news.google.com' + link
                news_items.append({'title': title, 'link': link})

    return render_template('google_news.html', news=news_items)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_news, 'interval', minutes=30)  # 每30分鐘抓取一次
    scheduler.start()
    fetch_news()  # 啟動時立即抓取一次
    app.run(debug=True)