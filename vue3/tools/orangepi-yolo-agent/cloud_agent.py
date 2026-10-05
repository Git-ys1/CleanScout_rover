"""Authenticated cloud worker for the Orange Pi YOLO chat agent."""
import base64
import json
import queue
import ssl
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import websocket

from agent import generate_reply, load_config


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / '.cloud-agent.json'
TOKEN_PATH = ROOT / '.cloud-agent-token'


def read_config():
    raw = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    return {
        'cloud_ws_url': str(raw.get('cloud_ws_url', 'wss://api.hzhhds.top/ws/agents')).strip(),
        'device_id': str(raw.get('device_id', 'cleanscout-001')).strip(),
        'agent_id': str(raw.get('agent_id', 'orangepi-rk3588-main')).strip(),
        'agent_type': 'orangepi-yolo-agent',
        'heartbeat_seconds': max(3.0, float(raw.get('heartbeat_seconds', 10))),
        'reconnect_seconds': max(1.0, float(raw.get('reconnect_seconds', 3))),
        'max_frame_age_seconds': max(1.0, float(raw.get('max_frame_age_seconds', 10))),
        'fresh_frame_wait_seconds': max(0.0, float(raw.get('fresh_frame_wait_seconds', 5))),
        'debug_roots': [Path(value).expanduser() for value in raw.get(
            'debug_roots', ['/home/orangepi/rk3588_ai/debug_logs'])],
    }


def model_status():
    config = load_config()
    return bool(config['AGNES_API_KEY']), config['AGNES_MODEL']


def newest_yolo_frame(roots):
    newest = None
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob('latest_debug.jpg'):
            try:
                stat = path.stat()
            except OSError:
                continue
            if newest is None or stat.st_mtime > newest[0]:
                newest = (stat.st_mtime, path)
    return newest


def frame_status(config):
    newest = newest_yolo_frame(config['debug_roots'])
    if newest is None:
        return {'yoloReachable': False, 'latestFrameAt': '', 'imageAgeMs': 0}
    modified, _path = newest
    age = max(0.0, time.time() - modified)
    return {
        'yoloReachable': age <= config['max_frame_age_seconds'],
        'latestFrameAt': datetime.fromtimestamp(modified, timezone.utc).isoformat(),
        'imageAgeMs': round(age * 1000),
    }


def read_fresh_frame(config):
    deadline = time.monotonic() + config['fresh_frame_wait_seconds']
    while True:
        newest = newest_yolo_frame(config['debug_roots'])
        if newest is not None:
            modified, path = newest
            age = max(0.0, time.time() - modified)
            if age <= config['max_frame_age_seconds']:
                raw = path.read_bytes()
                if not raw.startswith(b'\xff\xd8\xff') or not raw.endswith(b'\xff\xd9'):
                    time.sleep(0.15)
                    raw = path.read_bytes()
                if not raw or len(raw) > 5 * 1024 * 1024:
                    raise RuntimeError('YOLO 截图为空或超过 5 MB')
                if not raw.startswith(b'\xff\xd8\xff') or not raw.endswith(b'\xff\xd9'):
                    raise RuntimeError('YOLO 截图写入未完成')
                return path, raw, modified, round(age * 1000)
        if time.monotonic() >= deadline:
            raise RuntimeError('没有找到 10 秒内更新的 YOLO 画面，请确认 YOLO 正在运行')
        time.sleep(0.25)


def text_content(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return '\n'.join(str(item.get('text', '')).strip() for item in value
                         if isinstance(item, dict) and item.get('text')).strip()
    return ''


class CloudAgent:
    def __init__(self, config, token):
        self.config = config
        self.token = token
        self.socket = None
        self.send_lock = threading.Lock()
        self.stop_heartbeat = threading.Event()
        self.tasks = queue.Queue()
        threading.Thread(target=self.task_loop, daemon=True).start()

    def send(self, payload):
        raw = json.dumps(payload, ensure_ascii=False)
        with self.send_lock:
            if not self.socket or not self.socket.sock or not self.socket.sock.connected:
                raise ConnectionError('cloud websocket is not connected')
            self.socket.send(raw)

    def health_payload(self):
        ready, model = model_status()
        return dict(frame_status(self.config), modelReady=ready, model=model)

    def register(self):
        health = self.health_payload()
        self.send({
            'type': 'AGENT_REGISTER',
            'token': self.token,
            'agentType': self.config['agent_type'],
            'deviceId': self.config['device_id'],
            'agentId': self.config['agent_id'],
            'capabilities': ['chat', 'yolo.snapshot', 'vision.analysis'],
            'version': '1.0.0',
            **health,
            'ts': int(time.time() * 1000),
        })

    def heartbeat_loop(self):
        while not self.stop_heartbeat.wait(self.config['heartbeat_seconds']):
            try:
                self.send({
                    'type': 'AGENT_HEARTBEAT',
                    'deviceId': self.config['device_id'],
                    'agentId': self.config['agent_id'],
                    **self.health_payload(),
                    'ts': int(time.time() * 1000),
                })
            except Exception as exc:
                print('[cloud-agent] heartbeat failed: {}'.format(exc), flush=True)
                return

    def on_open(self, ws):
        self.socket = ws
        self.stop_heartbeat.clear()
        self.register()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        print('[cloud-agent] connected {}'.format(self.config['cloud_ws_url']), flush=True)

    def on_message(self, _ws, raw):
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError):
            return
        message_type = payload.get('type')
        if message_type == 'AGENT_REGISTER_ACK':
            print('[cloud-agent] registered device={} agent={}'.format(
                payload.get('deviceId', ''), payload.get('agentId', '')), flush=True)
        elif message_type == 'AGENT_ERROR':
            print('[cloud-agent] server error {}: {}'.format(
                payload.get('code', ''), payload.get('message', '')), flush=True)
        elif message_type == 'ORANGEPI_CHAT_REQUEST':
            self.tasks.put(payload)
            print('[cloud-agent] queued request={}'.format(payload.get('requestId', '')), flush=True)

    def on_close(self, _ws, code, reason):
        self.stop_heartbeat.set()
        print('[cloud-agent] disconnected code={} reason={}'.format(code, reason), flush=True)

    def on_error(self, _ws, error):
        print('[cloud-agent] websocket error: {}'.format(error), flush=True)

    def task_loop(self):
        while True:
            payload = self.tasks.get()
            try:
                self.process_task(payload)
            except Exception as exc:
                print('[cloud-agent] task fatal: {}'.format(exc), flush=True)
            finally:
                self.tasks.task_done()

    def process_task(self, payload):
        request_id = str(payload.get('requestId', '')).strip()
        try:
            path, raw, modified, age_ms = read_fresh_frame(self.config)
            messages = payload.get('messages') if isinstance(payload.get('messages'), list) else []
            history = []
            for item in messages[:-1][-20:]:
                content = text_content(item.get('content')) if isinstance(item, dict) else ''
                if content:
                    history.append({'role': 'assistant' if item.get('role') == 'assistant' else 'user',
                                    'content': content})
            prompt = text_content(messages[-1].get('content')) if messages else ''
            if not prompt:
                raise RuntimeError('云端消息为空')
            image_data_url = 'data:image/jpeg;base64,' + base64.b64encode(raw).decode('ascii')
            user_message = {'role': 'user', 'content': [
                {'type': 'text', 'text': (
                    '云端用户消息：' + prompt + '\n'
                    '以下是香橙派当前 YOLO 调试画面。请结合画面回答，并说明可见目标、检测框和关键信息。')},
                {'type': 'image_url', 'image_url': {'url': image_data_url}},
            ]}
            reply = generate_reply(history, user_message)
            ready, model = model_status()
            self.send({
                'type': 'ORANGEPI_CHAT_RESULT',
                'requestId': request_id,
                'conversationId': payload.get('conversationId', ''),
                'ok': True,
                'reply': reply,
                'imageBase64': base64.b64encode(raw).decode('ascii'),
                'imageName': path.name,
                'capturedAt': datetime.fromtimestamp(modified, timezone.utc).isoformat(),
                'imageAgeMs': age_ms,
                'yoloReachable': True,
                'modelReady': ready,
                'model': model,
            })
            print('[cloud-agent] completed request={} imageAgeMs={}'.format(request_id, age_ms), flush=True)
        except Exception as exc:
            ready, model = model_status()
            health = frame_status(self.config)
            try:
                self.send({
                    'type': 'ORANGEPI_CHAT_RESULT',
                    'requestId': request_id,
                    'conversationId': payload.get('conversationId', ''),
                    'ok': False,
                    'error': {'code': 'ORANGEPI_PROCESS_FAILED', 'message': str(exc)[:1000]},
                    'modelReady': ready,
                    'model': model,
                    **health,
                })
            except Exception as send_error:
                print('[cloud-agent] failed to report request error: {}'.format(send_error), flush=True)

    def run(self):
        while True:
            self.stop_heartbeat.clear()
            self.socket = websocket.WebSocketApp(
                self.config['cloud_ws_url'],
                header=['Authorization: Bearer ' + self.token],
                on_open=self.on_open,
                on_message=self.on_message,
                on_close=self.on_close,
                on_error=self.on_error,
            )
            self.socket.run_forever(
                sslopt={'cert_reqs': ssl.CERT_REQUIRED},
                ping_interval=20,
                ping_timeout=10,
            )
            time.sleep(self.config['reconnect_seconds'])


def main():
    config = read_config()
    token = TOKEN_PATH.read_text(encoding='ascii').strip()
    if len(token) < 32:
        raise SystemExit('.cloud-agent-token 必须至少 32 位')
    ready, model = model_status()
    print('[cloud-agent] starting device={} agent={} model={} modelReady={}'.format(
        config['device_id'], config['agent_id'], model, ready), flush=True)
    CloudAgent(config, token).run()


if __name__ == '__main__':
    main()
