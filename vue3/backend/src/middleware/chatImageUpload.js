import multer from 'multer'

const MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: MAX_IMAGE_SIZE_BYTES,
    files: 1,
  },
  fileFilter(_req, file, callback) {
    const mimeType = String(file?.mimetype || '').toLowerCase()

    if (mimeType.startsWith('image/')) {
      callback(null, true)
      return
    }

    callback(new Error('只允许上传图片文件'))
  },
})

export const chatImageUploadSingle = upload.single('file')
