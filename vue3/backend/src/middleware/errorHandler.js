export function errorHandler(error, _req, res, _next) {
  const status = error.status || 500

  return res.status(status).json({
    success: false,
    message: error.message || '服务器内部错误',
    ...(error.code ? { code: error.code } : {}),
  })
}
