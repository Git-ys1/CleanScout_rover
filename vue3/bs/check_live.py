"""手动运行的真实 API 验收：仅发送测试文字及内存生成的几何图。"""
import base64
import json
import struct
import zlib

from agent import generate_reply
from server import user_message


def test_image():
    width, height = 300, 160
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            color = (255, 255, 255)
            if 25 <= x < 115 and 35 <= y < 125:
                color = (235, 30, 30)
            if (x - 220) ** 2 + (y - 80) ** 2 < 45 ** 2:
                color = (20, 70, 235)
            rows.extend(color)
    def chunk(name, data):
        return struct.pack('!I', len(data)) + name + data + struct.pack('!I', zlib.crc32(name + data))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')
    return 'data:image/png;base64,' + base64.b64encode(png).decode()


if __name__ == '__main__':
    first = user_message('你好，请用一句中文介绍你自己。', '')
    print(json.dumps({'text': generate_reply([], first)}, ensure_ascii=True), flush=True)
    visual = user_message('描述图片中两个图形的颜色、形状和左右位置。', test_image())
    reply = generate_reply([], visual)
    print(json.dumps({'vision': reply}, ensure_ascii=True), flush=True)
    followup = generate_reply([visual, {'role': 'assistant', 'content': reply}],
                              user_message('右边的图形是什么颜色？', ''))
    print(json.dumps({'followup': followup}, ensure_ascii=True), flush=True)
