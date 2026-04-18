import jwt from 'jsonwebtoken'

const JWT_SECRET = process.env.JWT_SECRET || 'v-line-local-dev-secret'
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '7d'

export function signToken(user) {
  return jwt.sign(
    {
      username: user.username,
      role: user.role,
    },
    JWT_SECRET,
    {
      subject: user.id,
      expiresIn: JWT_EXPIRES_IN,
    }
  )
}

export function verifyToken(token) {
  return jwt.verify(token, JWT_SECRET)
}
