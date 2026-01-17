import { defineStore } from 'pinia'
import { login, logout, getProfile } from '@/api/admin'
import { getToken, setToken, removeToken } from '@/utils/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    userInfo: null,
    permissions: []
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.userInfo?.username || '',
    role: (state) => state.userInfo?.role || ''
  },

  actions: {
    async login(loginForm) {
      try {
        const { data } = await login(loginForm)
        this.token = data.token
        setToken(data.token)
        await this.getUserInfo()
        return Promise.resolve()
      } catch (error) {
        return Promise.reject(error)
      }
    },

    async getUserInfo() {
      try {
        const { data } = await getProfile()
        this.userInfo = data
        this.permissions = data.permissions || []
        return Promise.resolve(data)
      } catch (error) {
        return Promise.reject(error)
      }
    },

    async logout() {
      try {
        await logout()
      } catch (error) {
        console.error('退出登录失败:', error)
      } finally {
        this.token = ''
        this.userInfo = null
        this.permissions = []
        removeToken()
      }
    }
  }
})
