"""Python 标准库本地后端：消息持久化、图片输入、Agnes 调用。"""
import base64
import json
import re
import sqlite3
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from agent import ROOT, generate_reply, load_config

DB = ROOT / 'data' / 'messages.sqlite3'
LOCK = threading.Lock()
MAX_BODY = 8 * 1024 * 1024


@contextmanager
def connect():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    try:
        with con:
            con.execute('CREATE TABLE IF NOT EXISTS turns (id INTEGER PRIMARY KEY, session TEXT, user TEXT, reply TEXT)')
            yield con
    finally:
        con.close()


def session_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', value):
        raise ValueError('无效会话 ID。')
    return value


def read_messages(session, limit=20):
    with connect() as con:
        rows = con.execute('SELECT user, reply FROM (SELECT id, user, reply FROM turns WHERE session=? ORDER BY id DESC LIMIT ?) ORDER BY id', (session, limit)).fetchall()
    return [message for user, reply in rows for message in (
        json.loads(user), {'role': 'assistant', 'content': reply})]


def user_message(text, image):
    if not isinstance(text, str) or not isinstance(image, str):
        raise ValueError('消息和图片必须是字符串。')
    text, image = text.strip(), image.strip()
    if len(text) > 12000:
        raise ValueError('文字最多 12000 字。')
    if not text and not image:
        raise ValueError('请输入文字或选择图片。')
    if image:
        if image.startswith('data:'):
            match = re.fullmatch(r'data:image/(png|jpeg|webp|gif);base64,([A-Za-z0-9+/=]+)', image)
            if not match:
                raise ValueError('仅支持 PNG、JPEG、WEBP、GIF 图片。')
            try:
                raw = base64.b64decode(match[2], validate=True)
            except ValueError:
                raise ValueError('图片编码无效。') from None
            if not raw or len(raw) > 5 * 1024 * 1024:
                raise ValueError('图片不能为空且不能超过 5 MB。')
        else:
            parsed = urlparse(image)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('图片地址必须是可公开访问的 HTTPS URL。')
        return {'role': 'user', 'content': [
            {'type': 'text', 'text': text or '请描述这张图片的内容。'},
            {'type': 'image_url', 'image_url': {'url': image}}]}
    return {'role': 'user', 'content': text}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            data = (ROOT / 'index.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif parsed.path == '/api/status':
            self.send_json(200, {'configured': bool(load_config()['AGNES_API_KEY'])})
        elif parsed.path == '/api/messages':
            try:
                session = session_id(parse_qs(parsed.query).get('session_id', [''])[0])
                self.send_json(200, {'messages': read_messages(session, 100)})
            except ValueError as exc:
                self.send_json(400, {'error': str(exc)})
        else:
            self.send_json(404, {'error': '接口不存在。'})

    def do_POST(self):
        if self.path != '/api/chat':
            return self.send_json(404, {'error': '接口不存在。'})
        if self.headers.get('Origin') not in (None, f'http://{self.headers.get("Host")}'):
            return self.send_json(403, {'error': '不允许跨站请求。'})
        try:
            if 'application/json' not in self.headers.get('Content-Type', ''):
                raise ValueError('请求必须使用 application/json。')
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_BODY:
                raise ValueError('请求为空或超过 8 MB。')
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError('请求必须是 JSON 对象。')
            session = session_id(body.get('session_id'))
            message = user_message(body.get('message', ''), body.get('image', ''))
            # 本地单人应用串行生成，保证同一会话的历史顺序。
            with LOCK:
                reply = generate_reply(read_messages(session), message)
                with connect() as con:
                    con.execute('INSERT INTO turns(session,user,reply) VALUES(?,?,?)',
                                (session, json.dumps(message, ensure_ascii=False), reply))
            self.send_json(200, {'reply': reply})
        except (ValueError, UnicodeError) as exc:
            self.send_json(400, {'error': str(exc)})
        except RuntimeError as exc:
            self.send_json(502, {'error': str(exc)})
        except Exception:
            self.send_json(500, {'error': '本地服务出错，请检查数据库是否可写。'})


if __name__ == '__main__':
    print('BS Agent: http://127.0.0.1:8000 （Ctrl+C 停止）')
    server = ThreadingHTTPServer(('127.0.0.1', 8000), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
