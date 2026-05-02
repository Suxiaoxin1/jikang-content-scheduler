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
}
payload = {
    'inputs': {
        'topic': topic,
        'content_type': content_type,
        'keywords': keywords,
        'publish_date': publish_date,
    },
    'response_mode': 'blocking',
    'user': 'github-actions',
}
print(f"请求URL: {url}")
print(f"主题: {topic} | 类型: {content_type}")
req = urllib.request.Request(url, json.dumps(payload).encode('utf-8'), headers, method='POST')
try:
    with urllib.request.urlopen(req, timeout=120) as response:
        body = response.read().decode('utf-8')
        print(f"✅ Dify响应: {body[:300]}")
        result = json.loads(body)
        if result.get('result') == 'success' or 'workflow_run_id' in result:
            print('✅ Dify工作流触发成功！')
        else:
            print('⚠️ 响应状态异常')
            sys.exit(1)
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    print(f'❌ HTTP错误 {e.code}: {err_body}')
    sys.exit(1)
except Exception as e:
    print(f'❌ 错误: {e}')
    sys.exit(1)
