import { createStore } from 'vuex'
import connection from './modules/connection'
import stepper from './modules/stepper'
import servo from './modules/servo'
import radar from './modules/radar'
import pico from './modules/pico'
import system from './modules/system'
import notifications from './modules/notifications'

export default createStore({
  state: {
    isLoading: false,
    loadingMessage: ''
  },

  getters: {
    isLoading: state => state.isLoading,
    loadingMessage: state => state.loadingMessage
  },

  mutations: {
    SET_LOADING(state, { isLoading, message = '' }) {
      state.isLoading = isLoading
      state.loadingMessage = message
    }
  },

  actions: {
    setLoading({ commit }, payload) {
      commit('SET_LOADING', payload)
    }
  },

  modules: {
    connection,
    stepper,
    servo,
    radar,
    pico,
    system,
    notifications
  }
})
