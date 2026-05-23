<template>
  <div class="app-shell">
    <header class="app-header">
      <router-link class="brand" to="/">CoinMarketCap Web3</router-link>
      <nav class="nav-links">
        <router-link to="/">行情</router-link>
        <router-link to="/ai">AI 助手</router-link>
      </nav>
    </header>
    <router-view />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(11,14,20,0.86);
  backdrop-filter: blur(18px);
}

.brand {
  color: #f1f5f9;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
}

.nav-links {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.nav-links a {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 6px;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #e2e8f0;
  background: rgba(255,255,255,0.06);
}

@media (max-width: 640px) {
  .app-header {
    padding: 10px 12px;
  }

  .brand {
    font-size: 13px;
  }

  .nav-links a {
    min-height: 32px;
    padding: 0 9px;
  }
}
</style>
