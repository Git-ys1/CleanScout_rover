import { getCurrentUser, loginUser, registerUser } from '../services/authService.js'
import { sendSuccess } from '../utils/response.js'

export async function register(req, res, next) {
  try {
    const user = await registerUser(req.body)
    return sendSuccess(res, user, 201)
  } catch (error) {
    next(error)
  }
}

export async function login(req, res, next) {
  try {
    const result = await loginUser(req.body)
    return sendSuccess(res, result)
  } catch (error) {
    next(error)
  }
}

export async function me(req, res, next) {
  try {
    const user = await getCurrentUser(req.user.id)
    return sendSuccess(res, user)
  } catch (error) {
    next(error)
  }
}

export async function logout(_req, res) {
  return sendSuccess(res, { loggedOut: true })
}
