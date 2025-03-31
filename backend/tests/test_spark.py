import json
import hmac
import base64
import datetime
import hashlib
import websocket
import threading
import time
import ssl

class SparkAPI:
    def __init__(self, app_id, api_key, api_secret):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.url = 'wss://spark-api.xf-yun.com/v4.0/chat'
        self.response = None
        self.ws = None
        self.connected = False
        self.data_to_send = None

    def _create_signature(self):
        """生成鉴权签名"""
        date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        signature_origin = f"host: spark-api.xf-yun.com\ndate: {date}\nGET /v4.0/chat HTTP/1.1"
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(signature_sha).decode()
        authorization = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        return {
            "authorization": authorization,
            "date": date,
            "host": "spark-api.xf-yun.com",
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Version": "13",
            "Origin": "https://spark-api.xf-yun.com"
        }

    def _on_message(self, ws, message):
        """处理WebSocket消息"""
        print(f"收到消息: {message}")
        try:
            data = json.loads(message)
            if data.get('header', {}).get('code') == 0:
                self.response = data
            else:
                self.response = {'error': data.get('header', {}).get('message', '未知错误')}
        except Exception as e:
            print(f"处理消息时出错: {str(e)}")
            self.response = {'error': str(e)}

    def _on_error(self, ws, error):
        """处理WebSocket错误"""
        print(f"发生错误: {error}")
        self.response = {'error': str(error)}
        self.connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        """处理WebSocket关闭"""
        print(f"连接关闭: {close_status_code} - {close_msg}")
        self.connected = False

    def _on_open(self, ws):
        """处理WebSocket连接打开"""
        print("连接已打开，准备发送数据")
        self.connected = True
        if self.data_to_send:
            try:
                print(f"发送数据: {json.dumps(self.data_to_send, ensure_ascii=False)}")
                self.ws.send(json.dumps(self.data_to_send))
            except Exception as e:
                print(f"发送数据时出错: {str(e)}")
                self.response = {'error': f'发送数据失败: {str(e)}'}

    def chat(self, prompt):
        """发送聊天请求"""
        headers = self._create_signature()
        self.data_to_send = {
            "header": {
                "app_id": self.app_id
            },
            "parameter": {
                "chat": {
                    "domain": "general",
                    "temperature": 0.5,
                    "max_tokens": 2048
                }
            },
            "payload": {
                "message": {
                    "text": [{"role": "user", "content": prompt}]
                }
            }
        }

        print(f"准备发送请求: {json.dumps(self.data_to_send, ensure_ascii=False)}")
        print(f"请求头: {headers}")

        # 创建WebSocket连接
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            self.url,
            header=headers,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )

        # 在新线程中运行WebSocket
        wst = threading.Thread(target=self.ws.run_forever, kwargs={'sslopt': {"cert_reqs": ssl.CERT_NONE}})
        wst.daemon = True
        wst.start()

        # 等待响应
        timeout = 10
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.response is not None:
                break
            time.sleep(0.1)

        self.ws.close()
        return self.response or {'error': '超时未收到响应'}

def test_spark_api():
    # 使用实际的API信息
    app_id = 'dc9344e0'
    api_key = 'bef7f194967740d4921f71ce326b303a'
    api_secret = 'NDQ2NThkZGRhZTI1YTc2ZGNjYTk4ZDdi'

    spark = SparkAPI(app_id, api_key, api_secret)
    
    # 测试简单的对话
    prompt = "你好，请做个自我介绍"
    print(f"\n发送测试消息: {prompt}")
    
    response = spark.chat(prompt)
    print(f"\n收到响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    test_spark_api() 