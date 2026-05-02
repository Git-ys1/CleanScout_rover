import multer from 'multer'

const MAX_AUDIO_SIZE_BYTES = 20 * 1024 * 1024

const storage = multer.memoryStorage()

function fileFilter(_req, file, callback) {
  const mimeType = String(file?.mimetype || '').toLowerCase()

  if (!mimeType || mimeType.startsWith('audio/') || mimeType === 'application/octet-stream' || mimeType === 'video/webm') {
    callback(null, true)
    return
  }

  callback(new Error(`Unsupported audio mime type: ${mimeType}`))
}

const upload = multer({
  storage,
  limits: {
    fileSize: MAX_AUDIO_SIZE_BYTES,
    files: 1,
  },
  fileFilter,
})

export const asrUploadSingle = upload.single('file')
