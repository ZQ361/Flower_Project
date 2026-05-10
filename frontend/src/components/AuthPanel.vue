<script setup>
import { reactive, ref } from "vue";

defineProps({
  user: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["login", "register", "logout", "guest"]);
const mode = ref("login");

const loginForm = reactive({
  username: "",
  password: "",
});

const registerForm = reactive({
  username: "",
  email: "",
  password: "",
});

function submitLogin() {
  emit("login", {
    username: loginForm.username.trim(),
    password: loginForm.password,
  });
}

function submitRegister() {
  emit("register", {
    username: registerForm.username.trim(),
    email: registerForm.email.trim(),
    password: registerForm.password,
  });
}
</script>

<template>
  <section class="card auth-card auth-card-compact">
    <div class="auth-panel-top auth-panel-top-center">
      <div class="auth-panel-title">账号入口</div>
      <div v-if="user" class="chip">已登录</div>
    </div>

    <div v-if="user" class="auth-signed-in auth-signed-in-center">
      <div class="auth-summary">
        <div class="auth-avatar">{{ user.username?.slice(0, 1)?.toUpperCase() || "U" }}</div>
        <div>
          <div class="auth-username">{{ user.username }}</div>
          <div class="auth-meta">{{ user.email || "未绑定邮箱" }}</div>
        </div>
      </div>
      <div class="auth-actions auth-actions-center">
        <button class="primary-btn" type="button" :disabled="loading" @click="$emit('logout')">
          退出登录
        </button>
        <button class="ghost-btn" type="button" :disabled="loading" @click="$emit('guest')">
          游客模式
        </button>
      </div>
    </div>

    <template v-else>
      <div class="auth-tabs auth-tabs-center">
        <button type="button" class="auth-tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">
          登录
        </button>
        <button type="button" class="auth-tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">
          注册
        </button>
      </div>

      <p v-if="error" class="auth-error auth-error-center">{{ error }}</p>

      <form v-if="mode === 'login'" class="auth-form" autocomplete="off" @submit.prevent="submitLogin">
        <label class="field-group">
          <span>用户名</span>
          <input
            v-model="loginForm.username"
            type="text"
            autocomplete="off"
            autocapitalize="none"
            spellcheck="false"
            placeholder="请输入用户名"
          />
        </label>
        <label class="field-group">
          <span>密码</span>
          <input
            v-model="loginForm.password"
            type="password"
            autocomplete="new-password"
            placeholder="请输入密码"
          />
        </label>
        <div class="auth-buttons auth-buttons-center">
          <button class="primary-btn" type="submit" :disabled="loading">登录</button>
          <button class="ghost-btn" type="button" :disabled="loading" @click="$emit('guest')">游客模式</button>
        </div>
      </form>

      <form v-else class="auth-form" autocomplete="off" @submit.prevent="submitRegister">
        <label class="field-group">
          <span>用户名</span>
          <input
            v-model="registerForm.username"
            type="text"
            autocomplete="off"
            autocapitalize="none"
            spellcheck="false"
            placeholder="至少 3 个字符"
          />
        </label>
        <label class="field-group">
          <span>邮箱</span>
          <input v-model="registerForm.email" type="email" autocomplete="off" placeholder="可选" />
        </label>
        <label class="field-group">
          <span>密码</span>
          <input
            v-model="registerForm.password"
            type="password"
            autocomplete="new-password"
            placeholder="至少 6 个字符"
          />
        </label>
        <div class="auth-buttons auth-buttons-center">
          <button class="primary-btn" type="submit" :disabled="loading">注册并登录</button>
          <button class="ghost-btn" type="button" :disabled="loading" @click="$emit('guest')">游客模式</button>
        </div>
      </form>
    </template>
  </section>
</template>
