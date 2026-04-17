<template>
  <view class="auth-page">
    <view class="banner-card">
      <text class="banner-eyebrow">V-1.1.0 / Login</text>
      <text class="banner-title">登录 V 线控制端</text>
      <text class="banner-desc">
        本轮联调目标是打通登录、角色保护和 mock 数据链。默认管理员账号为 admin / 123456。
      </text>
    </view>

    <view class="form-card">
      <input v-model="form.username" class="field" placeholder="请输入用户名" />
      <input v-model="form.password" class="field" password placeholder="请输入密码" />

      <button class="submit-button" :loading="submitting" @tap="handleLogin">登录</button>

      <view class="link-row">
        <text class="link-text">还没有账号？</text>
        <text class="link-action" @tap="goRegister">去注册</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '../../stores/auth.js'
import { redirectIfLoggedIn } from '../../utils/auth-guard.js'

const authStore = useAuthStore()
const submitting = ref(false)
const form = reactive({
  username: '',
  password: '',
})

onShow(async () => {
  await redirectIfLoggedIn()
})

async function handleLogin() {
  if (!form.username.trim() || !form.password.trim()) {
    uni.showToast({
      title: '请输入用户名和密码',
      icon: 'none',
    })
    return
  }

  submitting.value = true

  try {
    await authStore.login(form)
    uni.showToast({
      title: '登录成功',
      icon: 'success',
    })
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/index/index' })
    }, 160)
  } catch (error) {
    uni.showToast({
      title: error.message || '登录失败',
      icon: 'none',
    })
  } finally {
    submitting.value = false
  }
}

function goRegister() {
  uni.navigateTo({ url: '/pages/auth/register' })
}
</script>

<style>
.auth-page {
  min-height: 100vh;
  padding: 36rpx 32rpx;
  box-sizing: border-box;
  background:
    radial-gradient(circle at left top, rgba(32, 83, 117, 0.18), transparent 38%),
    linear-gradient(180deg, #eef3f9 0%, #dde8f2 100%);
}

.banner-card,
.form-card {
  padding: 32rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18rpx 48rpx rgba(20, 32, 51, 0.08);
}

.banner-card {
  background: linear-gradient(135deg, #17324d, #205375 64%, #5ca4a9);
}

.banner-eyebrow {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.76);
  letter-spacing: 3rpx;
}

.banner-title {
  display: block;
  margin-top: 18rpx;
  font-size: 44rpx;
  font-weight: 700;
  color: #ffffff;
}

.banner-desc {
  display: block;
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.88);
}

.form-card {
  margin-top: 28rpx;
}

.field {
  height: 96rpx;
  margin-bottom: 20rpx;
  padding: 0 28rpx;
  border-radius: 20rpx;
  background: #f4f7fa;
  font-size: 28rpx;
  color: #17324d;
}

.submit-button {
  margin-top: 8rpx;
  border-radius: 999rpx;
  background: #205375;
  color: #ffffff;
}

.submit-button::after {
  border: none;
}

.link-row {
  display: flex;
  justify-content: center;
  margin-top: 28rpx;
}

.link-text,
.link-action {
  font-size: 26rpx;
}

.link-text {
  color: #57697b;
}

.link-action {
  margin-left: 8rpx;
  color: #205375;
  font-weight: 600;
}
</style>
