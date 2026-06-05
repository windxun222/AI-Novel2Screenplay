<template>
  <div class="app">
    <header class="app-header">
      <div class="header-content">
        <router-link to="/" class="logo">
          <span class="logo-icon">&#9998;</span>
          <span class="logo-text">AI 小说转剧本</span>
        </router-link>
        <nav class="nav">
          <router-link to="/" class="nav-link">首页</router-link>
          <router-link to="/convert" class="nav-link">开始转换</router-link>
        </nav>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.app-header {
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 0 24px;
  border-bottom: 1px solid #2a2a4a;
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: #e0e0e0;
  font-weight: 600;
  font-size: 18px;
}
.logo-icon {
  font-size: 24px;
}
.nav {
  display: flex;
  gap: 16px;
}
.nav-link {
  color: #a0a0b0;
  text-decoration: none;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background 0.2s, color 0.2s;
}
.nav-link:hover,
.nav-link.router-link-active {
  background: #2a2a4a;
  color: #fff;
}
.app-main {
  min-height: calc(100vh - 56px);
}
</style>
