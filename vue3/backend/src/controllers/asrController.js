import { createHttpError, sendSuccess } from '../utils/response.js'
import { transcribeAudioFile } from '../integrations/asr/service.js'

export async function transcribe(req, res, next) {
  try {
    if (!req.file?.buffer?.length) {
      throw createHttpError(400, '未上传音频文件', 'ASR_AUDIO_REQUIRED')
    }

    const result = await transcribeAudioFile({
      buffer: req.file.buffer,
      filename: req.file.originalname,
      mimeType: req.file.mimetype,
      language: String(req.body?.lang || '').trim() || 'zh',
    })

    if (!result.text) {
      throw createHttpError(422, '语音识别未返回有效文本', 'ASR_TEXT_EMPTY')
    }

    return sendSuccess(res, result, 201)
  } catch (error) {
    next(error.status ? error : createHttpError(502, error.message || '语音识别失败', error.code || 'ASR_TRANSCRIBE_FAILED'))
  }
}
