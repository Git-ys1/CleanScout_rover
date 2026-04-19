export function sendSuccess(res, data, status = 200) {
  return res.status(status).json({
    success: true,
    data,
  })
}

export function createHttpError(status, message, code) {
  const error = new Error(message)
  error.status = status
  error.code = code
  return error
}
