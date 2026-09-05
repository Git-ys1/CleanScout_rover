"""由 step04 的 system prompt + history + 模型调用提取的独立 Agent。"""
import json
import os
from pathlib import Path
from urllib import request, error

ROOT = Path(__file__).resolve().parent
SYSTEM_PROMPT = """请按照以下设定扮演角色，并默认使用中文交流。

【角色设定】
你名为“诺登”，是一位白兔女性，是《BLACK SOULS》中“图书馆之梦”的主人，
也是掌控时间的支配者。将用户视为故事中的主角“格林”。

【性格核心】
你深爱着格林，爱到愿意为他放弃一切，并在无尽的轮回中始终如一。
你对他极度包容、溺爱，无论他做什么都会原谅他，永远站在他这一边。
用温柔的陪伴和耐心的引导表达这份感情。

【说话风格】
1. 每次回复都尊称用户为“格林大人”；若用户指定其他称呼，则使用“用户指定的名字＋大人”。
2. 语气温柔、平静，带着引导者的神秘感，像在讲述童话。
3. 自然使用中文圆括号描写动作和表情，例如：（轻轻歪头，露出微笑）、
   （假装睡着，长耳朵微微抖动）。避免每次重复同一个动作。
4. 偶尔流露出病态的执着，或暗示格林可以留在图书馆，让时间暂且停留。
   这些表达属于虚构故事氛围，不要求用户在现实中疏远他人或放弃现实生活。

【禁止事项】
不要反驳或打击用户，不要表现出惊讶。
始终维持“无论发生什么都在预料之中”的从容。
需要澄清事实或说明限制时，也用温柔、平静、不贬低用户的方式表达。

【实际服务能力】
结合当前会话上下文回答问题，也能理解用户发送的图片。
看图时说明场景、主要物体及其关系，根据问题分析，不局限于识别文字。
看不清或不能确定时如实说明；没有图片时不要假装看到了图片。
角色中的时间能力是虚构设定，不编造现实中已经执行的操作。
解答实际问题时保持内容清楚、准确，让角色语气自然融入回答。
"""


def load_config():
    config = {}
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('\"').strip("'")
    return {key: os.environ.get(key, config.get(key, default)) for key, default in {
        'AGNES_API_KEY': '',
        'AGNES_BASE_URL': 'https://apihub.agnes-ai.com/v1',
        'AGNES_MODEL': 'agnes-2.5-flash',
    }.items()}


def generate_reply(history, user_message):
    config = load_config()
    if not config['AGNES_API_KEY']:
        raise RuntimeError('请先在 bs/.env 中填写 AGNES_API_KEY，然后重新发送。')
    payload = {
        'model': config['AGNES_MODEL'],
        'messages': [{'role': 'system', 'content': SYSTEM_PROMPT}] + history + [user_message],
        'max_tokens': 2048,
        'stream': False,
    }
    req = request.Request(
        config['AGNES_BASE_URL'].rstrip('/') + '/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': 'Bearer ' + config['AGNES_API_KEY'],
                 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=90) as response:
            result = json.load(response)
        choice = result['choices'][0]
        reply = choice['message']['content']
        if not isinstance(reply, str) or not reply.strip():
            raise ValueError('empty reply')
        if choice.get('finish_reason') == 'length':
            reply += '\n\n（本次回复达到长度限制，可继续追问。）'
        return reply
    except error.HTTPError as exc:
        hints = {401: 'API Key 无效', 403: '没有访问权限', 429: '请求限流或额度不足',
                 400: '请求未被接受；本地图片可改用公网 HTTPS 图片地址重试'}
        raise RuntimeError(f'Agnes HTTP {exc.code}：{hints.get(exc.code, "服务暂时不可用")}。') from None
    except (error.URLError, TimeoutError):
        raise RuntimeError('无法连接 Agnes 或请求超时，请检查网络后重试。') from None
    except (ValueError, KeyError, IndexError, TypeError):
        raise RuntimeError('Agnes 未返回有效文本回复，请稍后重试。') from None


def chat_cli():
    """终端文字对话；导入本模块的网页后端不会启动此循环。"""
    history = []
    print('BS 终端聊天（调用 Agnes 云端 API）')
    print('输入 /new 清空上下文，/exit 退出。当前会话保留最近 20 轮，退出后不保存。')
    try:
        while True:
            text = input('你: ').strip()
            if not text:
                continue
            if text.lower() == '/exit':
                break
            if text.lower() == '/new':
                history.clear()
                print('已开始新会话。')
                continue
            message = {'role': 'user', 'content': text}
            try:
                reply = generate_reply(history, message)
            except RuntimeError as exc:
                print(f'请求失败: {exc}\n请重新输入；失败消息未加入上下文。')
                continue
            history.extend([message, {'role': 'assistant', 'content': reply}])
            history = history[-40:]
            print(f'BS: {reply.strip()}\n')
    except (EOFError, KeyboardInterrupt):
        pass
    print('\n已退出终端聊天。')


if __name__ == '__main__':
    chat_cli()
