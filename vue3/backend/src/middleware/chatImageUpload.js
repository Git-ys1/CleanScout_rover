import multer from 'multer'
import { createHttpError } from '../utils/response.js'

const MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
const ALLOWED_IMAGE_MIME_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
])

const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: MAX_IMAGE_SIZE_BYTES,
    files: 1,
  },
  fileFilter(_req, file, callback) {
    const mimeType = String(file?.mimetype || '').toLowerCase()

    if (ALLOWED_IMAGE_MIME_TYPES.has(mimeType)) {
      callback(null, true)
      return
    }

    callback(createHttpError(415, '只允许上传 JPEG、PNG、GIF 或 WebP 图片', 'CHAT_IMAGE_TYPE_UNSUPPORTED'))
  },
})

const uploadSingle = upload.single('file')

export function chatImageUploadSingle(req, res, next) {
  uploadSingle(req, res, (error) => {
    if (!error) {
      next()
      return
    }

    if (error instanceof multer.MulterError) {
      next(createHttpError(400, error.message, `CHAT_IMAGE_UPLOAD_${error.code}`))
      return
    }

    next(error.status ? error : createHttpError(400, error.message, 'CHAT_IMAGE_UPLOAD_FAILED'))
  })
}
