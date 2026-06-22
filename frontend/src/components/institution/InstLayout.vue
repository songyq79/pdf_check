<template>
  <div class="inst-shell" :class="`variant-${variant}`">
    <!-- 侧边栏 -->
    <aside class="inst-sidebar">
      <div class="sb-logo">
        <span class="sb-wordmark">VRonly</span>
        <span class="sb-brandsub">{{ brandSub }}</span>
      </div>

      <div class="sb-scroll">
        <div v-for="(group, gi) in navGroups" :key="gi" class="sb-group">
          <div class="sb-group-label">{{ group.label }}</div>
          <a
            v-for="(item, ii) in group.items"
            :key="ii"
            class="sb-nav-item"
            :class="{ active: item.active }"
            href="javascript:void(0)"
            @click="onNav(item)"
          >
            <span class="sb-nav-icon">{{ item.icon }}</span>
            <span class="sb-nav-text">{{ item.text }}</span>
            <span v-if="item.badge" class="sb-nav-badge" :class="item.badgeType">{{ item.badge }}</span>
          </a>
        </div>
        <slot name="sidebar-extra" />
      </div>

      <div class="sb-bottom">
        <div class="sb-user">
          <div class="sb-avatar">{{ (userName || '?').slice(0, 1) }}</div>
          <div class="sb-user-meta">
            <div class="sb-user-name">{{ userName }}</div>
            <div class="sb-user-role">{{ userRole }}</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主区 -->
    <div class="inst-main">
      <header class="inst-topbar">
        <div class="tb-titlewrap">
          <div class="tb-title">{{ pageTitle }}</div>
          <div v-if="breadcrumb" class="tb-path">{{ breadcrumb }}</div>
        </div>
        <div class="tb-actions">
          <slot name="actions" />
          <el-dropdown @command="onUserCommand" trigger="click">
            <span class="tb-user">
              <span class="tb-user-dot"></span>{{ userName }} <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="home">返回首页</el-dropdown-item>
                <el-dropdown-item command="account">用户中心</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="inst-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'

const props = defineProps({
  variant: { type: String, default: 'admin' },   // admin | student
  brandSub: { type: String, default: '' },
  navGroups: { type: Array, default: () => [] },  // [{label, items:[{icon,text,active,badge,badgeType,key,to}]}]
  pageTitle: { type: String, default: '' },
  breadcrumb: { type: String, default: '' },
  userName: { type: String, default: '' },
  userRole: { type: String, default: '' },
})

const emit = defineEmits(['nav'])
const router = useRouter()
const authStore = useAuthStore()

function onNav(item) {
  emit('nav', item)
}

function onUserCommand(cmd) {
  if (cmd === 'home') router.push(props.variant === 'student' ? '/workspace' : '/')
  else if (cmd === 'account') router.push('/user-center')
  else if (cmd === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  }
}
</script>

<style scoped>
.inst-shell {
  --green: #006C49;
  --green-mid: #00875C;
  --green-pale: #E8F5EE;
  --green-pale2: #F0FAF5;
  --orange: #E8840A;
  --red: #DC3545;
  --blue: #2563EB;
  --body-bg: #F5F7F6;
  --card-bg: #FFFFFF;
  --text: #1A2E20;
  --muted: #7A8C82;
  --border: #E2EBE6;
  --sidebar-w: 224px;
  --font-d: 'Newsreader', serif;

  display: flex;
  min-height: 100vh;
  background: var(--body-bg);
  font-size: 14px;
  color: var(--text);
}

/* ── 侧边栏 ── */
.inst-sidebar {
  width: var(--sidebar-w);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100vh;
}
.variant-admin .inst-sidebar { background: #003D28; }
.variant-student .inst-sidebar { background: #fff; border-right: 1px solid var(--border); }

.sb-logo {
  padding: 22px 20px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.variant-student .sb-logo { border-bottom-color: var(--border); }
.sb-wordmark {
  font-family: var(--font-d);
  font-style: italic;
  font-size: 20px;
  display: block;
  margin-bottom: 4px;
}
.variant-admin .sb-wordmark { color: #fff; }
.variant-student .sb-wordmark { color: var(--text); }
.sb-brandsub {
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}
.variant-admin .sb-brandsub { color: rgba(255, 255, 255, 0.45); }
.variant-student .sb-brandsub { color: var(--muted); }

.sb-scroll { flex: 1; overflow-y: auto; padding-bottom: 8px; }
.sb-group { padding: 14px 12px 4px; }
.sb-group-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  padding: 0 8px;
  margin-bottom: 6px;
}
.variant-admin .sb-group-label { color: rgba(255, 255, 255, 0.28); }
.variant-student .sb-group-label { color: var(--muted); }

.sb-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 13.5px;
  font-weight: 500;
  text-decoration: none;
  margin-bottom: 2px;
}
.variant-admin .sb-nav-item { color: rgba(255, 255, 255, 0.55); }
.variant-admin .sb-nav-item:hover { background: rgba(255, 255, 255, 0.07); color: rgba(255, 255, 255, 0.85); }
.variant-admin .sb-nav-item.active { background: var(--green); color: #fff; }
.variant-student .sb-nav-item { color: var(--muted); }
.variant-student .sb-nav-item:hover { background: var(--green-pale); color: var(--green); }
.variant-student .sb-nav-item.active { background: var(--green-pale); color: var(--green); font-weight: 700; }

.sb-nav-icon { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
.sb-nav-text { flex: 1; }
.sb-nav-badge {
  margin-left: auto;
  background: var(--red);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 100px;
  min-width: 18px;
  text-align: center;
}
.sb-nav-badge.orange { background: var(--orange); }

.sb-bottom {
  padding: 14px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.variant-student .sb-bottom { border-top-color: var(--border); }
.sb-user { display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 10px; }
.sb-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: var(--green-mid);
  color: #fff; font-size: 14px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.variant-student .sb-avatar { background: linear-gradient(135deg, var(--green) 0%, #00A870 100%); }
.sb-user-name { font-size: 13px; font-weight: 700; }
.variant-admin .sb-user-name { color: rgba(255, 255, 255, 0.85); }
.variant-student .sb-user-name { color: var(--text); }
.sb-user-role { font-size: 11px; }
.variant-admin .sb-user-role { color: rgba(255, 255, 255, 0.38); }
.variant-student .sb-user-role { color: var(--muted); }

/* ── 主区 ── */
.inst-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.inst-topbar {
  height: 60px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 28px;
  gap: 16px;
  position: sticky;
  top: 0;
  z-index: 10;
}
.tb-titlewrap { flex: 1; }
.tb-title { font-size: 16px; font-weight: 700; color: var(--text); }
.tb-path { font-size: 13px; color: var(--muted); margin-top: 1px; }
.tb-actions { display: flex; gap: 10px; align-items: center; }
.tb-user {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: var(--text); cursor: pointer; font-weight: 500;
  padding: 5px 10px; border-radius: 100px; outline: none;
}
.tb-user:hover { background: var(--green-pale); color: var(--green); }
.tb-user-dot { width: 22px; height: 22px; border-radius: 50%; background: var(--green); flex-shrink: 0; }

.inst-content { padding: 24px 28px; flex: 1; }

@media (max-width: 820px) {
  .inst-shell { flex-direction: column; }
  .inst-sidebar { width: 100%; height: auto; position: static; flex-direction: row; flex-wrap: wrap; }
  .sb-scroll { display: flex; flex-wrap: wrap; }
}
</style>
