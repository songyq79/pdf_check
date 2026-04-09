<template>
  <footer class="modern-footer">
    <div class="footer-container">
      <div class="footer-content">
        <!-- 关于我们 -->
        <div class="footer-section">
          <h3>关于我们</h3>
          <div class="footer-about">
            唯唯人工智能科技（山东）有限公司致力于人工智能技术、算法大型语言模型（LLM）、RAG、AI Agent等技术，专注打造高效全面的AI智能平台，以提升用户体验和技术创新为核心，为客户提供优质的AI解决方案，推动智能化未来的发展。是国家高新技术企业，是国家级专精特新企业。
          </div>
        </div>

        <!-- 服务 -->
        <div class="footer-section">
          <h3>服务</h3>
          <div class="footer-links">
            <a href="#" class="footer-link">用户协议</a>
            <a href="#" class="footer-link">隐私政策</a>
            <a href="#" class="footer-link">购买协议</a>
          </div>
        </div>

        <!-- 联系我们 -->
        <div class="footer-section">
          <h3>联系我们</h3>
          <div class="footer-contact">
            地址：山东省青岛市城阳区科技街一路一号创新汇1001室<br>
            邮箱：VRonly@163.com<br>
            电话：0532-83815991
          </div>
        </div>

        <!-- 二维码 -->
        <div class="footer-section">
          <h3>唯维视界公众号 &nbsp;&nbsp; 唯维人工智能</h3>
          <div class="footer-qr">
            <div class="qr-item">
              <div class="qr-code">公众号二维码</div>
              <div class="qr-label">唯维视界公众号</div>
            </div>
            <div class="qr-item">
              <div class="qr-code">小程序二维码</div>
              <div class="qr-label">唯维人工智能</div>
            </div>
          </div>
        </div>
      </div>

      <div class="footer-bottom">
        © 2026 唯唯人工智能科技（山东）有限公司. All rights reserved.
      </div>
    </div>
  </footer>
</template>

<script setup>
// 页脚组件
</script>

<style scoped>
.modern-footer {
  background: rgba(26, 26, 26, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px 16px 0 0;
  margin-top: 60px;
  color: white;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.footer-content {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 40px;
  margin-bottom: 30px;
}

.footer-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: white;
}

.footer-about {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  line-height: 1.8;
}

.footer-links {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.footer-link {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s;
}

.footer-link:hover {
  color: white;
}

.footer-contact {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  line-height: 1.8;
}

.footer-qr {
  display: flex;
  gap: 20px;
}

.qr-item {
  text-align: center;
}

.qr-code {
  width: 100px;
  height: 100px;
  background: white;
  border-radius: 8px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #666;
}

.qr-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.footer-bottom {
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .footer-content {
    grid-template-columns: 1fr 1fr;
    gap: 30px;
  }
}

@media (max-width: 768px) {
  .footer-container {
    padding: 30px 15px;
  }

  .footer-content {
    grid-template-columns: 1fr;
    gap: 25px;
  }

  .footer-qr {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .modern-footer {
    margin-top: 40px;
  }

  .footer-container {
    padding: 24px 15px;
  }

  .footer-section h3 {
    font-size: 15px;
  }

  .footer-about,
  .footer-contact {
    font-size: 12px;
  }

  .qr-code {
    width: 80px;
    height: 80px;
    font-size: 11px;
  }
}
</style>
