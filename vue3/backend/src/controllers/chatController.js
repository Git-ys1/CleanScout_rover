import { createHttpError, sendSuccess } from '../utils/response.js'
import { getChatHistory, sendChatImage, sendChatMessage } from '../services/chatService.js'

export async function history(req, res, next) {
  try {
    const messages = await getChatHistory(req.user.id)
    return sendSuccess(res, messages)
  } catch (error) {
    next(error)
  }
}

export async function send(req, res, next) {
  try {
    const content = req.body?.content

    if (!String(content || '').trim()) {
      throw createHttpError(400, '消息内容不能为空', 'CHAT_CONTENT_REQUIRED')
    }

    const result = await sendChatMessage(req.user.id, content)
    return sendSuccess(res, result, 201)
  } catch (error) {
    next(error.status ? error : createHttpError(400, error.message, 'CHAT_SEND_FAILED'))
  }
}

export async function sendImage(req, res, next) {
  try {
    if (!req.file) {
      throw createHttpError(400, '请选择要发送的图片', 'CHAT_IMAGE_REQUIRED')
    }

    const result = await sendChatImage(req.user.id, req.file)
    return sendSuccess(res, result, 201)
  } catch (error) {
    next(error.status ? error : createHttpError(400, error.message, 'CHAT_IMAGE_SEND_FAILED'))
  }
}
