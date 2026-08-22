import requests

url = 'http://127.0.0.1:11434/api/generate'
payload = {'model':'llama3.2','prompt':'Ping','stream':False}
try:
    r = requests.post(url, json=payload, timeout=5)
    print('status', r.status_code)
    print(r.text[:2000])
except Exception as e:
    print('error', repr(e))
