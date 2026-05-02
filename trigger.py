import urllib.request
import json
import os
import datetime
import sys

api_key = os.environ['DIFY_API_KEY'].strip()
base_url = os.environ['DIFY_BASE_URL'].strip()
input_topic = os.environ.get('INPUT_TOPIC', '')

if input_topic:
    topic = input_topic.strip()
    content_type = os.environ.get('INPUT_CONTENT_TYPE', '技术').strip()
    keywords = os.environ.get('INPUT_KEYWORDS', '').strip()
    publish_date = os.environ.get('INPUT_PUBLISH_DATE', '').strip()
    print(f"手动触发模式: {topic}")
else:
    print("定时触发模式，读取schedule.json...")
    today = datetime.datetime.now().strftime('%A')
    topic = content_type = keywords = None
    with open('schedule.json') as f:
        data = json.load(f)
    for item in data['weekly_schedule']:
        if item['day'] == today:
            topic = item['topic']
            content_type = item['content_type']
            keywords = item['keywords']
            break
    if not topic:
        print(f"未找到今天的发布计划，跳过")
        sys.exit(0)
    publish_date = ''
    print(f"定时触发: {topic}")

if not publish_date:
    publish_date = (datetime.datetime.now() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')

url = base_url.rstrip('/') + '/v1/workflows/run'
headers = {
    'Authorization': 'Bearer ' + api_key,
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}
payload = {
    'inputs': {
        'topic': topic,
        'content_type': content_type,
        'keywords': keywords,
        'publish_date': publish_date,
    },
    'response_mode': 'streaming',  # 改成 streaming，不等待完成
    'user': 'github-actions',
}
print(f"请求URL: {url}")
print(f"主题: {topic} | 类型: {content_type}")
req = urllib.request.Request(url, json.dumps(payload).encode('utf-8'), headers, method='POST')
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        # streaming 模式读取前 500 字符即可
        body = response.read(500).decode('utf-8')
        print(f"✅ Dify响应: {body}")
        print('✅ Dify工作流已触发（streaming模式，后台执行中）')
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    print(f'❌ HTTP错误 {e.code}: {err_body}')
    sys.exit(1)
except Exception as e:
    print(f'❌ 错误: {e}')
    sys.exit(1)
