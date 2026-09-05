import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

import agent
import server


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=agent.ROOT)
        self.db = patch.object(server, 'DB', Path(self.temp.name) / 'messages.sqlite3')
        self.db.start()
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.http.server_port)

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        self.db.stop()
        self.temp.cleanup()

    def post(self, data):
        req = Request(self.base + '/api/chat', json.dumps(data).encode(),
                      {'Content-Type': 'application/json'})
        with urlopen(req) as response:
            return json.load(response)

    def test_text_image_followup_and_isolation(self):
        image = 'https://example.com/scene.jpg'
        with patch.object(server, 'generate_reply', return_value='场景描述') as model:
            self.assertEqual(self.post({'session_id': 'a', 'image': image})['reply'], '场景描述')
            self.post({'session_id': 'a', 'message': '有什么物体？'})
            self.assertEqual(model.call_args.args[0][0]['content'][1]['image_url']['url'], image)
            self.post({'session_id': 'b', 'message': '你好'})
            self.assertEqual(model.call_args.args[0], [])
        with urlopen(self.base + '/api/messages?session_id=a') as response:
            self.assertEqual(len(json.load(response)['messages']), 4)

    def test_failure_does_not_save(self):
        with patch.object(server, 'generate_reply', side_effect=RuntimeError('服务失败')):
            with self.assertRaises(HTTPError) as ctx:
                self.post({'session_id': 'a', 'message': '你好'})
            self.assertEqual(ctx.exception.code, 502)
        self.assertEqual(server.read_messages('a'), [])

    def test_validation_and_private_files(self):
        for data in ({'session_id': 'a'}, {'session_id': '../a', 'message': 'hi'},
                     {'session_id': 'a', 'image': 'file:///secret'}):
            with self.assertRaises(HTTPError) as ctx:
                self.post(data)
            self.assertEqual(ctx.exception.code, 400)
        with self.assertRaises(HTTPError) as ctx:
            urlopen(self.base + '/.env')
        self.assertEqual(ctx.exception.code, 404)

    def test_local_image_payload(self):
        value = 'data:image/png;base64,aGVsbG8='
        message = server.user_message('', value)
        self.assertEqual(message['content'][1]['image_url']['url'], value)

    def test_missing_key(self):
        with patch.object(agent, 'load_config', return_value={'AGNES_API_KEY': ''}):
            with self.assertRaisesRegex(RuntimeError, 'AGNES_API_KEY'):
                agent.generate_reply([], {'role': 'user', 'content': 'hi'})


if __name__ == '__main__':
    unittest.main()
