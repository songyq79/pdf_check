<template>
  <div class="b2b">
    <!-- Hero -->
    <section class="hero">
      <span class="badge">🏫 高校版</span>
      <h1>论文全生命周期 AI 助手<br><span class="accent">高校机构版</span></h1>
      <p class="sub">面向高校教务处、研究生院、学院——为全校学生提供选题、文献、写作、评价、校对、排版、查重一站式 AI 工具，并为管理者提供配额管理、使用统计与合规报表。</p>
      <div class="cta">
        <a class="btn-primary" href="mailto:bd@vronly-dh.com?subject=高校版演示申请">申请演示</a>
        <router-link class="btn-ghost" to="/">← 个人使用</router-link>
      </div>

      <!-- 已开通高校的入口（轻量文字链接） -->
      <p class="entry-line">
        已开通的高校：
        <router-link :to="{ path: '/login', query: { tab: 'account' } }">登录（管理员/学生）</router-link>
        <span class="dot">·</span>
        <router-link :to="{ path: '/login', query: { tab: 'inst-student' } }">新生用邀请码注册</router-link>
      </p>
    </section>

    <!-- 统计带 -->
    <section class="stats">
      <div><b>8</b><span>核心功能模块</span></div>
      <div><b>1套</b><span>后端·三入口</span></div>
      <div><b>年费制</b><span>不按次计费</span></div>
      <div><b>私有化</b><span>部署可选</span></div>
    </section>

    <!-- 价值 -->
    <section class="features">
      <h2>为什么选择高校版</h2>
      <div class="grid">
        <div class="card"><div class="ic">📊</div><h3>精细化配额管理</h3><p>机构配额池统一发放，按学院/年级/导师分配，配额预警与使用统计一目了然。</p></div>
        <div class="card"><div class="ic">📈</div><h3>使用数据与报表</h3><p>全校用量、按功能/学院聚合、近 30 天趋势，一键导出 CSV 月报。</p></div>
        <div class="card"><div class="ic">🎓</div><h3>学术诚信合规</h3><p>AI 辅助而非代写，生成初稿需学生二次修改；可选 AIGC 检测满足各校 AI 规范。</p></div>
        <div class="card"><div class="ic">🔒</div><h3>数据安全</h3><p>论文数据仅用于服务处理，不训练模型；支持私有化部署与 SSO 对接。</p></div>
        <div class="card"><div class="ic">🔍</div><h3>选题到投稿全覆盖</h3><p>选题评估、文献综述、写作辅助、实验评审、评价、校对、排版、查重。</p></div>
        <div class="card"><div class="ic">🎟️</div><h3>邀请码自助开通</h3><p>学生凭机构邀请码注册，管理员审批即用，无需逐个建号。</p></div>
      </div>
    </section>

    <!-- 年费定价 -->
    <section class="pricing">
      <h2>透明年费制</h2>
      <div class="grid">
        <div class="price-card">
          <div class="lvl">小规模</div><div class="scale">&lt; 100 学生</div>
          <div class="price">¥10<span>万 / 年</span></div>
          <ul><li>全功能模块</li><li>机构配额池</li><li>使用统计 + 报表</li><li>邮件支持</li></ul>
          <a class="btn-line" href="mailto:bd@vronly-dh.com">申请演示</a>
        </div>
        <div class="price-card featured">
          <div class="tag">推荐</div>
          <div class="lvl">中规模</div><div class="scale">100 - 500 学生</div>
          <div class="price">¥30<span>万 / 年</span></div>
          <ul><li>全功能 + 导师端</li><li>学院数据看板</li><li>品牌定制报告</li><li>专属客户经理</li></ul>
          <a class="btn-fill" href="mailto:bd@vronly-dh.com">申请演示</a>
        </div>
        <div class="price-card">
          <div class="lvl">大规模</div><div class="scale">&gt; 500 学生</div>
          <div class="price">¥50<span>万 / 年</span></div>
          <ul><li>不限量使用</li><li>私有化部署可选</li><li>SSO / Open API</li><li>SLA + 定制开发</li></ul>
          <a class="btn-line" href="mailto:bd@vronly-dh.com">定制方案</a>
        </div>
      </div>
      <p class="note">试点高校前 5 所享 50% 折扣。具体以商务洽谈为准。</p>
    </section>

    <section class="foot-cta">
      <h2>为全校师生引入 AI 论文助手</h2>
      <a class="btn-primary" href="mailto:bd@vronly-dh.com?subject=高校版合作咨询">联系我们</a>
    </section>
  </div>
</template>

<script setup>
// 纯展示页，公开访问
</script>

<style scoped>
.b2b { max-width: 1080px; margin: 0 auto; padding: 0 20px 60px; color: #1a1c1c; }
.hero { text-align: center; padding: 64px 0 40px; }
.badge { display: inline-block; background: rgba(0,108,73,0.1); color: #006C49; border-radius: 100px; padding: 5px 14px; font-size: 13px; font-weight: 600; }
.hero h1 { font-size: 44px; font-weight: 600; line-height: 1.25; margin: 20px 0 16px; }
.hero .accent { color: #006C49; }
.hero .sub { max-width: 680px; margin: 0 auto; font-size: 16px; color: rgb(75,85,99); line-height: 1.8; }
.cta { margin-top: 28px; display: flex; gap: 14px; justify-content: center; align-items: center; }
.btn-primary { background: #006C49; color: #fff; border-radius: 100px; padding: 12px 28px; text-decoration: none; font-weight: 600; }
.btn-ghost { color: rgb(75,85,99); text-decoration: none; font-size: 14px; }

.entry-line { margin-top: 22px; font-size: 14px; color: rgb(107,114,128); }
.entry-line a { color: #006C49; text-decoration: none; font-weight: 500; }
.entry-line a:hover { text-decoration: underline; }
.entry-line .dot { margin: 0 8px; color: rgb(203,213,225); }

.stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; background: #f8faf9; border-radius: 24px; padding: 28px; margin: 20px 0 48px; text-align: center; }
.stats b { display: block; font-size: 28px; color: #006C49; font-weight: 700; }
.stats span { font-size: 13px; color: rgb(107,114,128); }

.features, .pricing { margin-bottom: 56px; }
.features h2, .pricing h2, .foot-cta h2 { text-align: center; font-size: 30px; font-weight: 600; margin-bottom: 32px; }
.grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; }
@media (max-width: 820px){ .grid, .stats { grid-template-columns: repeat(2,1fr);} .hero h1{font-size:32px;} }
.card { background: #fff; border: 1px solid rgba(0,108,73,0.1); border-radius: 20px; padding: 24px; }
.card .ic { font-size: 30px; }
.card h3 { font-size: 17px; margin: 12px 0 8px; }
.card p { font-size: 14px; color: rgb(75,85,99); line-height: 1.7; }

.price-card { background: #fff; border: 1px solid rgba(0,108,73,0.12); border-radius: 24px; padding: 28px; position: relative; }
.price-card.featured { border-color: #006C49; box-shadow: 0 8px 40px rgba(0,108,73,0.12); }
.tag { position: absolute; top: 16px; right: 16px; background: #006C49; color: #fff; font-size: 12px; padding: 3px 10px; border-radius: 100px; }
.lvl { font-size: 18px; font-weight: 700; }
.scale { font-size: 13px; color: rgb(107,114,128); margin-bottom: 12px; }
.price { font-size: 36px; font-weight: 700; color: #006C49; margin-bottom: 16px; }
.price span { font-size: 15px; color: rgb(107,114,128); font-weight: 400; }
.price-card ul { list-style: none; padding: 0; margin: 0 0 20px; }
.price-card li { font-size: 14px; color: rgb(55,65,81); padding: 6px 0; border-bottom: 1px solid rgba(0,0,0,.04); }
.btn-line { display: block; text-align: center; border: 1px solid #006C49; color: #006C49; border-radius: 100px; padding: 10px; text-decoration: none; font-weight: 600; }
.btn-fill { display: block; text-align: center; background: #006C49; color: #fff; border-radius: 100px; padding: 10px; text-decoration: none; font-weight: 600; }
.note { text-align: center; font-size: 13px; color: rgb(156,163,175); margin-top: 20px; }

.foot-cta { text-align: center; background: #f8faf9; border-radius: 24px; padding: 48px; }
</style>
