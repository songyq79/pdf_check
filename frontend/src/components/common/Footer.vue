<template>
  <footer class="footer">
    <div class="footer-inner">

      <!-- 左：品牌 + 描述 -->
      <div class="footer-col footer-col--brand">
        <div class="footer-brand-name">VRonly</div>
        <p class="footer-brand-desc">专注于学术论文质量评估与提升的创新平台，助力科研梦想实现</p>
      </div>

      <!-- 中右：联系信息 -->
      <div class="footer-col footer-col--contact">
        <span class="footer-col-title">联系我们</span>
        <div class="contact-item">
          <svg class="contact-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/>
          </svg>
          <span>山东省青岛市崂山区科苑纬一路一号<br>创新园C座1001室</span>
        </div>
        <div class="contact-item">
          <svg class="contact-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6.62 10.79a15.05 15.05 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 1.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1C10.61 21 3 13.39 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1.02l-2.2 2.2z"/>
          </svg>
          <span>0532-83815891</span>
        </div>
        <div class="contact-item">
          <svg class="contact-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4-8 5-8-5V6l8 5 8-5v2z"/>
          </svg>
          <span>VRonly@163.com</span>
        </div>
      </div>

      <!-- 右：二维码 -->
      <div class="footer-col footer-col--qr">
        <span class="footer-col-title">关注我们</span>
        <div class="qr-wrap">
          <img src="/qrcode.jpg" alt="扫码关注" class="qr-img" />
          <p class="qr-label">扫码关注公众号</p>
        </div>
      </div>

    </div>

    <!-- 底部版权栏 -->
    <div class="footer-bottom">
      <span>© 2025 VRonly. 保留所有权利.</span>
      <span>鲁ICP备XXXXXXXX号</span>
    </div>
  </footer>
</template>

<script setup>
</script>

<style scoped>
.footer {
  width: 100%;
  background: rgb(244, 244, 245);
  padding: 56px 0 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.footer-inner {
  width: 1100px;
  max-width: calc(100% - 80px);
  display: flex;
  align-items: flex-start;
  gap: 60px;
  padding-bottom: 48px;
  border-bottom: 1px solid rgb(229, 231, 235);
}

/* 品牌列：占剩余空间 */
.footer-col--brand {
  flex: 1;
  min-width: 0;
}

/* 联系列：固定宽 */
.footer-col--contact {
  flex-shrink: 0;
  width: 240px;
}

/* 二维码列：固定宽 */
.footer-col--qr {
  flex-shrink: 0;
  width: 120px;
}

.footer-brand-name {
  font-family: 'Newsreader', serif;
  font-size: 20px;
  font-weight: 700;
  font-style: italic;
  color: rgb(24, 24, 27);
  margin-bottom: 12px;
}

.footer-brand-desc {
  font-size: 14px;
  color: rgb(113, 113, 122);
  line-height: 1.75;
  margin: 0;
  max-width: 320px;
}

.footer-col-title {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: rgb(24, 24, 27);
  margin-bottom: 16px;
  letter-spacing: 0.02em;
}

/* 联系信息 */
.contact-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: rgb(113, 113, 122);
  line-height: 1.6;
  margin-bottom: 12px;
}

.contact-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  margin-top: 2px;
  color: rgb(0, 108, 73);
}

/* 二维码 */
.qr-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.qr-img {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  border: 1px solid rgb(229, 231, 235);
  display: block;
}

.qr-label {
  font-size: 12px;
  color: rgb(113, 113, 122);
  margin: 0;
  white-space: nowrap;
}

/* 底部版权栏 */
.footer-bottom {
  width: 1100px;
  max-width: calc(100% - 80px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  font-size: 12px;
  color: rgb(161, 161, 170);
}

/* 响应式 */
@media (max-width: 1180px) {
  .footer-inner,
  .footer-bottom {
    width: calc(100% - 80px);
  }
}

@media (max-width: 760px) {
  .footer-inner {
    flex-wrap: wrap;
    gap: 32px;
  }
  .footer-col--brand {
    width: 100%;
    flex: none;
  }
  .footer-col--contact {
    width: auto;
    flex: 1;
  }
}

@media (max-width: 520px) {
  .footer {
    padding: 40px 0 0;
  }
  .footer-inner,
  .footer-bottom {
    width: calc(100% - 48px);
  }
  .footer-inner {
    flex-direction: column;
    gap: 28px;
    padding-bottom: 32px;
  }
  .footer-col--contact,
  .footer-col--qr {
    width: 100%;
  }
  .footer-bottom {
    flex-direction: column;
    gap: 6px;
    text-align: center;
    padding: 14px 0;
  }
}
</style>
