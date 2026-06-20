<template>
  <div class="home-wrap">
    <!-- Hero 区 -->
    <section class="home-hero">
      <div class="hero-inner">
        <div class="hero-badge">
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10.6358 4.72703L9.89722 3.10212L8.27231 2.36352L9.89722 1.62492L10.6358 0L11.3744 1.62492L12.9993 2.36352L11.3744 3.10212L10.6358 4.72703ZM10.6358 12.9993L9.89722 11.3744L8.27231 10.6358L9.89722 9.89722L10.6358 8.27231L11.3744 9.89722L12.9993 10.6358L11.3744 11.3744L10.6358 12.9993ZM4.72703 11.2267L3.24984 7.97687L0 6.49967L3.24984 5.02247L4.72703 1.77264L6.20423 5.02247L9.45407 6.49967L6.20423 7.97687L4.72703 11.2267Z" fill="#006C49"/>
          </svg>
          AI-Powered Thesis Evolution
        </div>
        <h1 class="hero-title">欢迎使用<br>论文评价<span class="accent">检验系统</span></h1>
        <p class="hero-desc">为您的学术论文提供专业的质量检测与智能评价。错别字、语法、段落逻辑，统统交给我们。无需烦恼，只需上传文档，等待专业反馈与自动修正。</p>
      </div>
    </section>

    <!-- 功能卡片 -->
    <section class="home-features">
      <div class="feature-card" @click="navigateTo('/topic-evaluation')">
        <span class="new-badge">新</span>
        <div class="feature-icon-wrap" style="background:rgba(39,226,159,0.10);">
          <span style="font-size: 32px;">🎯</span>
        </div>
        <h3 class="feature-title">选题评估</h3>
        <p class="feature-desc">填写研究选题，AI 检索真实相关文献，从创新性、可行性、重要性三个维度评估，给出改进建议与相关文献，帮你在开题阶段把方向选对。</p>
      </div>

      <div class="feature-card" @click="navigateTo('/literature-review')">
        <span class="new-badge">新</span>
        <div class="feature-icon-wrap" style="background:rgba(39,226,159,0.10);">
          <span style="font-size: 32px;">📚</span>
        </div>
        <h3 class="feature-title">文献综述</h3>
        <p class="feature-desc">上传论文列表或输入关键词，自动补检文献、按主题聚类，生成可二次编辑的文献综述初稿与 GB/T 7714 参考文献。</p>
      </div>

      <div class="feature-card" @click="navigateTo('/evaluation')">
        <div class="feature-icon-wrap" style="background:rgba(39,226,159,0.10);">
          <EvaluationIcon style="font-size: 36px; color: #006D4A" />
        </div>
        <h3 class="feature-title">智能评价</h3>
        <p class="feature-desc">从四个维度进行全面评价：从学术规范性、逻辑与创新性、语言质量、文献引用规范性等多个角度，提供详细的评价报告和改进建议。</p>
      </div>

      <div class="feature-card" @click="navigateTo('/spell-check')">
        <div class="feature-icon-wrap" style="background:rgba(167,139,250,0.10);">
          <SpellCheckIcon style="font-size: 36px; color: #A78BFA" />
        </div>
        <h3 class="feature-title">错别字检查</h3>
        <p class="feature-desc">利用先进的 AI 技术，对论文进行逐段校对，标记并修正文字错误、语法问题、标点符号使用不当等问题，确保文字表达准确无误。</p>
      </div>

      <div class="feature-card" @click="navigateTo('/formatting')">
        <div class="feature-icon-wrap" style="background:rgba(18,18,18,0.05);">
          <FormattingIcon style="font-size: 36px; color: #121212" />
        </div>
        <h3 class="feature-title">模板排版</h3>
        <p class="feature-desc">提供多种学术论文模板（如清华、北大、IEEE、APA 等格式），自动识别文档结构，一键应用专业排版样式，让您的论文符合投稿要求。</p>
      </div>

      <div class="feature-card" @click="navigateTo('/plagiarism')">
        <span class="coming-badge">敬请期待</span>
        <div class="feature-icon-wrap" style="background:rgb(232,250,244);">
          <PlagiarismIcon style="font-size: 36px; color: #006D4A" />
        </div>
        <h3 class="feature-title">论文查重</h3>
        <p class="feature-desc">基于 SimHash + AI 语义增强双引擎，检测文本相似度，标注疑似重复片段，生成详细查重报告，助您了解论文原创情况。</p>
      </div>
    </section>

    <!-- 数据统计（深色满幅） -->
    <section class="home-stats">
      <div class="stats-inner">
        <div class="stat-item">
          <span class="stat-number">98.5%</span>
          <span class="stat-label">评估准确率</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">500+</span>
          <span class="stat-label">活跃用户</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">2M+</span>
          <span class="stat-label">处理字数</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">24h/7d</span>
          <span class="stat-label">在线服务</span>
        </div>
      </div>
    </section>

    <!-- 定价区 -->
    <section class="home-pricing">
      <h2 class="pricing-heading">选择最适合您的学术进程方案</h2>
      <div class="pricing-cards">
        <!-- 按次购买 -->
        <div class="pricing-card light">
          <p class="pricing-label green">最优价格</p>
          <h3 class="pricing-name">按次使用</h3>
          <p class="pricing-sub">Perfect for final polish or single chapters.</p>
          <div class="pricing-price-row">
            <span class="pricing-price-num">¥{{ billingStore.pricing?.per_use_yuan || '9.90' }}</span>
            <span class="pricing-price-unit">/次</span>
          </div>
          <ul class="pricing-list">
            <li>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8.6 14.6L15.65 7.55L14.25 6.15L8.6 11.8L5.75 8.95L4.35 10.35L8.6 14.6ZM10 20C8.61667 20 7.31667 19.7375 6.1 19.2125C4.88333 18.6875 3.825 17.975 2.925 17.075C2.025 16.175 1.3125 15.1167 0.7875 13.9C0.2625 12.6833 0 11.3833 0 10C0 8.61667 0.2625 7.31667 0.7875 6.1C1.3125 4.88333 2.025 3.825 2.925 2.925C3.825 2.025 4.88333 1.3125 6.1 0.7875C7.31667 0.2625 8.61667 0 10 0C11.3833 0 12.6833 0.2625 13.9 0.7875C15.1167 1.3125 16.175 2.025 17.075 2.925C17.975 3.825 18.6875 4.88333 19.2125 6.1C19.7375 7.31667 20 8.61667 20 10C20 11.3833 19.7375 12.6833 19.2125 13.9C18.6875 15.1167 17.975 16.175 17.075 17.075C16.175 17.975 15.1167 18.6875 13.9 19.2125C12.6833 19.7375 11.3833 20 10 20Z" fill="#006C49"/>
              </svg>
              任意功能可用
            </li>
            <li>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8.6 14.6L15.65 7.55L14.25 6.15L8.6 11.8L5.75 8.95L4.35 10.35L8.6 14.6ZM10 20C8.61667 20 7.31667 19.7375 6.1 19.2125C4.88333 18.6875 3.825 17.975 2.925 17.075C2.025 16.175 1.3125 15.1167 0.7875 13.9C0.2625 12.6833 0 11.3833 0 10C0 8.61667 0.2625 7.31667 0.7875 6.1C1.3125 4.88333 2.025 3.825 2.925 2.925C3.825 2.025 4.88333 1.3125 6.1 0.7875C7.31667 0.2625 8.61667 0 10 0C11.3833 0 12.6833 0.2625 13.9 0.7875C15.1167 1.3125 16.175 2.025 17.075 2.925C17.975 3.825 18.6875 4.88333 19.2125 6.1C19.7375 7.31667 20 8.61667 20 10C20 11.3833 19.7375 12.6833 19.2125 13.9C18.6875 15.1167 17.975 16.175 17.075 17.075C16.175 17.975 15.1167 18.6875 13.9 19.2125C12.6833 19.7375 11.3833 20 10 20Z" fill="#006C49"/>
              </svg>
              使用即扣
            </li>
            <li>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8.6 14.6L15.65 7.55L14.25 6.15L8.6 11.8L5.75 8.95L4.35 10.35L8.6 14.6ZM10 20C8.61667 20 7.31667 19.7375 6.1 19.2125C4.88333 18.6875 3.825 17.975 2.925 17.075C2.025 16.175 1.3125 15.1167 0.7875 13.9C0.2625 12.6833 0 11.3833 0 10C0 8.61667 0.2625 7.31667 0.7875 6.1C1.3125 4.88333 2.025 3.825 2.925 2.925C3.825 2.025 4.88333 1.3125 6.1 0.7875C7.31667 0.2625 8.61667 0 10 0C11.3833 0 12.6833 0.2625 13.9 0.7875C15.1167 1.3125 16.175 2.025 17.075 2.925C17.975 3.825 18.6875 4.88333 19.2125 6.1C19.7375 7.31667 20 8.61667 20 10C20 11.3833 19.7375 12.6833 19.2125 13.9C18.6875 15.1167 17.975 16.175 17.075 17.075C16.175 17.975 15.1167 18.6875 13.9 19.2125C12.6833 19.7375 11.3833 20 10 20Z" fill="#006C49"/>
              </svg>
              无过期限制
            </li>
          </ul>
          <el-button class="pricing-btn light-btn" @click="goToPricing">立即购买</el-button>
        </div>

        <!-- 包月订阅 -->
        <div class="pricing-card dark">
          <div class="pricing-bg-circle"></div>
          <p class="pricing-label mint">最受欢迎</p>
          <h3 class="pricing-name">包月订阅</h3>
          <p class="pricing-sub">Unlimited access for deep research cycles.</p>
          <div class="pricing-price-row">
            <span class="pricing-price-num">¥{{ billingStore.pricing?.monthly_yuan || '69.90' }}</span>
            <span class="pricing-price-unit">/月</span>
          </div>
          <ul class="pricing-list">
            <li>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8.6 14.6L15.65 7.55L14.25 6.15L8.6 11.8L5.75 8.95L4.35 10.35L8.6 14.6ZM10 20C8.61667 20 7.31667 19.7375 6.1 19.2125C4.88333 18.6875 3.825 17.975 2.925 17.075C2.025 16.175 1.3125 15.1167 0.7875 13.9C0.2625 12.6833 0 11.3833 0 10C0 8.61667 0.2625 7.31667 0.7875 6.1C1.3125 4.88333 2.025 3.825 2.925 2.925C3.825 2.025 4.88333 1.3125 6.1 0.7875C7.31667 0.2625 8.61667 0 10 0C11.3833 0 12.6833 0.2625 13.9 0.7875C15.1167 1.3125 16.175 2.025 17.075 2.925C17.975 3.825 18.6875 4.88333 19.2125 6.1C19.7375 7.31667 20 8.61667 20 10C20 11.3833 19.7375 12.6833 19.2125 13.9C18.6875 15.1167 17.975 16.175 17.075 17.075C16.175 17.975 15.1167 18.6875 13.9 19.2125C12.6833 19.7375 11.3833 20 10 20Z" fill="#4FFBB6"/>
              </svg>
              每月 20 次使用额度
            </li>
            <li>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8.6 14.6L15.65 7.55L14.25 6.15L8.6 11.8L5.75 8.95L4.35 10.35L8.6 14.6ZM10 20C8.61667 20 7.31667 19.7375 6.1 19.2125C4.88333 18.6875 3.825 17.975 2.925 17.075C2.025 16.175 1.3125 15.1167 0.7875 13.9C0.2625 12.6833 0 11.3833 0 10C0 8.61667 0.2625 7.31667 0.7875 6.1C1.3125 4.88333 2.025 3.825 2.925 2.925C3.825 2.025 4.88333 1.3125 6.1 0.7875C7.31667 0.2625 8.61667 0 10 0C11.3833 0 12.6833 0.2625 13.9 0.7875C15.1167 1.3125 16.175 2.025 17.075 2.925C17.975 3.825 18.6875 4.88333 19.2125 6.1C19.7375 7.31667 20 8.61667 20 10C20 11.3833 19.7375 12.6833 19.2125 13.9C18.6875 15.1167 17.975 16.175 17.075 17.075C16.175 17.975 15.1167 18.6875 13.9 19.2125C12.6833 19.7375 11.3833 20 10 20Z" fill="#4FFBB6"/>
              </svg>
              优先客服支持
            </li>
            <li>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8.6 14.6L15.65 7.55L14.25 6.15L8.6 11.8L5.75 8.95L4.35 10.35L8.6 14.6ZM10 20C8.61667 20 7.31667 19.7375 6.1 19.2125C4.88333 18.6875 3.825 17.975 2.925 17.075C2.025 16.175 1.3125 15.1167 0.7875 13.9C0.2625 12.6833 0 11.3833 0 10C0 8.61667 0.2625 7.31667 0.7875 6.1C1.3125 4.88333 2.025 3.825 2.925 2.925C3.825 2.025 4.88333 1.3125 6.1 0.7875C7.31667 0.2625 8.61667 0 10 0C11.3833 0 12.6833 0.2625 13.9 0.7875C15.1167 1.3125 16.175 2.025 17.075 2.925C17.975 3.825 18.6875 4.88333 19.2125 6.1C19.7375 7.31667 20 8.61667 20 10C20 11.3833 19.7375 12.6833 19.2125 13.9C18.6875 15.1167 17.975 16.175 17.075 17.075C16.175 17.975 15.1167 18.6875 13.9 19.2125C12.6833 19.7375 11.3833 20 10 20Z" fill="#4FFBB6"/>
              </svg>
              30 天有效期
            </li>
            <li>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8.6 14.6L15.65 7.55L14.25 6.15L8.6 11.8L5.75 8.95L4.35 10.35L8.6 14.6ZM10 20C8.61667 20 7.31667 19.7375 6.1 19.2125C4.88333 18.6875 3.825 17.975 2.925 17.075C2.025 16.175 1.3125 15.1167 0.7875 13.9C0.2625 12.6833 0 11.3833 0 10C0 8.61667 0.2625 7.31667 0.7875 6.1C1.3125 4.88333 2.025 3.825 2.925 2.925C3.825 2.025 4.88333 1.3125 6.1 0.7875C7.31667 0.2625 8.61667 0 10 0C11.3833 0 12.6833 0.2625 13.9 0.7875C15.1167 1.3125 16.175 2.025 17.075 2.925C17.975 3.825 18.6875 4.88333 19.2125 6.1C19.7375 7.31667 20 8.61667 20 10C20 11.3833 19.7375 12.6833 19.2125 13.9C18.6875 15.1167 17.975 16.175 17.075 17.075C16.175 17.975 15.1167 18.6875 13.9 19.2125C12.6833 19.7375 11.3833 20 10 20Z" fill="#4FFBB6"/>
              </svg>
              支持续费累计
            </li>
          </ul>
          <el-button class="pricing-btn dark-btn" @click="goToPricing">立即订阅</el-button>
        </div>
      </div>
    </section>

    <!-- 安全承诺 -->
    <section class="home-security">
      <div class="security-left">
        <h2 class="security-title">安全承诺</h2>
        <p class="security-desc">您的学术成果是无价之宝，我们采用银行级加密技术保护您的隐私与知识产权。</p>
      </div>
      <div class="security-grid">
        <div class="security-item">
          <div class="security-icon-wrap" style="background:rgba(39,226,159,0.10);">
            <svg width="15" height="20" viewBox="0 0 15 20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M1.80768 19.4999C1.30896 19.4999 0.883006 19.3233 0.529803 18.9701C0.176601 18.6169 0 18.1909 0 17.6922V8.30764C0 7.80893 0.176601 7.38297 0.529803 7.02977C0.883006 6.67656 1.30896 6.49996 1.80768 6.49996H3V4.49996C3 3.25126 3.43782 2.18908 4.31345 1.31345C5.18908 0.437817 6.25126 0 7.49996 0C8.74867 0 9.81084 0.437817 10.6865 1.31345C11.5621 2.18908 11.9999 3.25126 11.9999 4.49996V6.49996H13.1922C13.691 6.49996 14.1169 6.67656 14.4701 7.02977C14.8233 7.38297 14.9999 7.80893 14.9999 8.30764V17.6922C14.9999 18.1909 14.8233 18.6169 14.4701 18.9701C14.1169 19.3233 13.691 19.4999 13.1922 19.4999H1.80768ZM7.49996 14.7499C7.98586 14.7499 8.39899 14.5797 8.73937 14.2393C9.07975 13.899 9.24994 13.4858 9.24994 12.9999C9.24994 12.514 9.07975 12.1009 8.73937 11.7605C8.39899 11.4201 7.98586 11.2499 7.49996 11.2499C7.01407 11.2499 6.60093 11.4201 6.26055 11.7605C5.92017 12.1009 5.74998 12.514 5.74998 12.9999C5.74998 13.4858 5.92017 13.899 6.26055 14.2393C6.60093 14.5797 7.01407 14.7499 7.49996 14.7499ZM4.49996 6.49996H10.5V4.49996C10.5 3.66663 10.2083 2.9583 9.62496 2.37496C9.04163 1.79163 8.3333 1.49996 7.49996 1.49996C6.66663 1.49996 5.9583 1.79163 5.37496 2.37496C4.79163 2.9583 4.49996 3.66663 4.49996 4.49996V6.49996Z" fill="#006D4A"/>
            </svg>
          </div>
          <div class="security-item-text">
            <h4>Security Audit</h4>
            <p>定期进行第三方安全审计，确保系统无漏洞。</p>
          </div>
        </div>
        <div class="security-item">
          <div class="security-icon-wrap" style="background:rgba(167,139,250,0.10);">
            <svg width="18" height="19" viewBox="0 0 18 19" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M0 18.6103V17.0758H11.7642V18.6103H0ZM5.93721 13.334L0.511526 7.90834L2.30564 6.06307L7.78248 11.4888L5.93721 13.334ZM12.0003 7.27095L6.5746 1.79412L8.41987 0L13.8456 5.42569L12.0003 7.27095ZM16.9224 17.4889L3.92668 4.49319L5.00471 3.41515L18.0004 16.4109L16.9224 17.4889Z" fill="#A78BFA"/>
            </svg>
          </div>
          <div class="security-item-text">
            <h4>Legal Compliance</h4>
            <p>严格遵守数据保护法，不存储用户核心内容。</p>
          </div>
        </div>
        <div class="security-item">
          <div class="security-icon-wrap" style="background:rgb(244,244,245);">
            <svg width="19" height="15" viewBox="0 0 19 15" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M1.80768 14.9999C1.30255 14.9999 0.874992 14.8249 0.524995 14.4749C0.174998 14.1249 0 13.6974 0 13.1922V1.80768C0 1.30255 0.174998 0.874992 0.524995 0.524995C0.874992 0.174998 1.30255 0 1.80768 0H17.1922C17.6974 0 18.1249 0.174998 18.4749 0.524995C18.8249 0.874992 18.9999 1.30255 18.9999 1.80768V13.1922C18.9999 13.6974 18.8249 14.1249 18.4749 14.4749C18.1249 14.8249 17.6974 14.9999 17.1922 14.9999H1.80768ZM1.80768 13.5H17.1922C17.2692 13.5 17.3397 13.4679 17.4038 13.4038C17.4679 13.3397 17.5 13.2692 17.5 13.1922V3.49996H1.49996V13.1922C1.49996 13.2692 1.53202 13.3397 1.59612 13.4038C1.66023 13.4679 1.73075 13.5 1.80768 13.5ZM4.99996 12.1442L3.95576 11.1L6.53076 8.49996L3.93076 5.89996L4.99996 4.85576L8.64417 8.49996L4.99996 12.1442ZM9.74998 12.2499V10.75H15.2499V12.2499H9.74998Z" fill="#121212"/>
            </svg>
          </div>
          <div class="security-item-text">
            <h4>Technical Encryption</h4>
            <p>AES-256 位加密传输，全程密文处理。</p>
          </div>
        </div>
        <div class="security-item">
          <div class="security-icon-wrap" style="background:rgba(39,226,159,0.05);">
            <svg width="21" height="14" viewBox="0 0 21 14" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10.4638 11.0769C11.5969 11.0769 12.5592 10.6803 13.3509 9.8871C14.1426 9.09393 14.5384 8.1308 14.5384 6.9977C14.5384 5.8646 14.1418 4.90222 13.3486 4.11056C12.5555 3.3189 11.5923 2.92307 10.4592 2.92307C9.32614 2.92307 8.36376 3.31966 7.5721 4.11282C6.78044 4.90599 6.38461 5.86913 6.38461 7.00223C6.38461 8.13532 6.78119 9.0977 7.57436 9.88936C8.36753 10.681 9.33066 11.0769 10.4638 11.0769ZM10.4615 9.69996C9.7115 9.69996 9.074 9.43746 8.549 8.91246C8.024 8.38746 7.7615 7.74996 7.7615 6.99996C7.7615 6.24996 8.024 5.61246 8.549 5.08746C9.074 4.56246 9.7115 4.29996 10.4615 4.29996C11.2115 4.29996 11.849 4.56246 12.374 5.08746C12.899 5.61246 13.1615 6.24996 13.1615 6.99996C13.1615 7.74996 12.899 8.38746 12.374 8.91246C11.849 9.43746 11.2115 9.69996 10.4615 9.69996ZM10.4629 13.9999C8.16325 13.9999 6.06793 13.3656 4.17691 12.0971C2.28589 10.8285 0.893589 9.12944 0 6.99996C0.893589 4.87049 2.28543 3.17146 4.17554 1.90287C6.06564 0.634292 8.1605 0 10.4601 0C12.7597 0 14.8551 0.634292 16.7461 1.90287C18.6371 3.17146 20.0294 4.87049 20.923 6.99996C20.0294 9.12944 18.6376 10.8285 16.7475 12.0971C14.8574 13.3656 12.7625 13.9999 10.4629 13.9999Z" fill="#006D4A"/>
            </svg>
          </div>
          <div class="security-item-text">
            <h4>Transparency</h4>
            <p>透明的处理流程，用户可随时撤回授权。</p>
          </div>
        </div>
      </div>
    </section>


  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { onMounted, onUnmounted } from 'vue'
import EvaluationIcon from '@/components/icons/EvaluationIcon.vue'
import SpellCheckIcon from '@/components/icons/SpellCheckIcon.vue'
import FormattingIcon from '@/components/icons/FormattingIcon.vue'
import PlagiarismIcon from '@/components/icons/PlagiarismIcon.vue'
import { useBillingStore } from '@/store/modules/billing'

const router = useRouter()
const billingStore = useBillingStore()

onMounted(() => {
  document.body.classList.add('home-page')
  billingStore.loadPricing()
})

onUnmounted(() => {
  document.body.classList.remove('home-page')
})

function navigateTo(path) {
  router.push(path)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goToPricing() {
  router.push('/pricing')
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

</script>

<style>
/* 全局背景覆盖 */
body.home-page {
  background: #f9f9f9 !important;
}
</style>

<style scoped>
.home-wrap {
  width: 100%;
  margin: 0;
  padding: 0;
}

/* ─── Hero 区 ─── */
.home-hero {
  width: 100%;
  padding: 128px 20px 100px;
  text-align: center;
}

.hero-inner {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(79, 251, 182, 0.20);
  border-radius: 9999px;
  padding: 8px 16px;
  font-size: 14px;
  color: #006C49;
  line-height: 20px;
}

.hero-title {
  width: 688px;
  font-size: 88px;
  font-weight: 500;
  color: #1a1c1c;
  line-height: 120px;
  letter-spacing: -2.4px;
  margin: 0;
  -webkit-font-smoothing: antialiased;
}

.hero-title .accent {
  color: #006C49;
}

.hero-desc {
  font-size: 20px;
  font-weight: 400;
  color: #3b4a41;
  line-height: 32.5px;
  margin: 0;
  max-width: 1000px;
}

/* ─── 功能卡片 ─── */
.home-features {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px 80px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
}

.feature-card {
  position: relative;
  background: rgb(253, 253, 253);
  border: 1px solid rgba(229, 231, 235, 0.5);
  border-radius: 32px;
  padding: 40px;
  height: 400px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 24px;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
  cursor: pointer;
}

.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.1);
}

.coming-badge {
  position: absolute;
  top: 17px;
  right: 17px;
  display: inline-flex;
  align-items: center;
  background: rgb(232, 250, 244);
  border-radius: 9999px;
  padding: 4.5px 12px;
  font-size: 10px;
  color: #006D4A;
  letter-spacing: 1px;
  text-transform: uppercase;
  z-index: 1;
}

.new-badge {
  position: absolute;
  top: 17px;
  right: 17px;
  display: inline-flex;
  align-items: center;
  background: #006C49;
  color: #fff;
  border-radius: 9999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 600;
  z-index: 1;
}

.feature-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.feature-title {
  font-size: 24px;
  font-weight: 400;
  color: #121212;
  line-height: 32px;
  margin: 0;
}

.feature-desc {
  font-size: 16px;
  color: #6b7280;
  line-height: 26px;
  margin: 0;
}

/* ─── 统计栏（深色满幅） ─── */
.home-stats {
  width: 100%;
  background: rgb(26, 28, 28);
  padding: 96px 0;
  display: flex;
  justify-content: center;
  margin: 64px 0;
}

.stats-inner {
  max-width: 1000px;
  width: 100%;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  gap: 32px;
}

.stat-item {
  width: 214px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.stat-number {
  font-family: 'Newsreader', serif;
  font-style: italic;
  font-size: 48px;
  font-weight: 400;
  color: rgb(83, 254, 185);
  line-height: 48px;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: rgb(238, 238, 238);
  letter-spacing: 1.2px;
  text-align: center;
  text-transform: uppercase;
}

/* ─── 定价区 ─── */
.home-pricing {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px 80px;
  display: flex;
  flex-direction: column;
  gap: 64px;
}

.pricing-heading {
  font-size: 36px;
  font-weight: 400;
  color: #1a1c1c;
  text-align: center;
  line-height: 36px;
  margin: 0;
}

.pricing-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.pricing-card {
  height: auto;
  border-radius: 48px;
  padding: 48px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  overflow: hidden;
}

.pricing-card.light {
  background: rgb(243, 243, 244);
  border: 1px solid rgba(186, 202, 191, 0.1);
}

.pricing-card.dark {
  background: #006C49;
  box-shadow: 0 16px 48px rgba(0, 108, 73, 0.35);
  color: white;
}

.pricing-bg-circle {
  position: absolute;
  width: 192px;
  height: 192px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  top: -96px;
  right: -96px;
  pointer-events: none;
}

.pricing-label {
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 1.2px;
  line-height: 16px;
}

.pricing-label.green {
  color: #006C49;
}

.pricing-label.mint {
  color: rgb(79, 251, 182);
}

.pricing-name {
  font-size: 36px;
  font-weight: 400;
  line-height: 40px;
  margin: 0;
}

.pricing-card.light .pricing-name {
  color: #1a1c1c;
}

.pricing-card.dark .pricing-name {
  color: white;
}

.pricing-sub {
  font-family: 'Manrope', sans-serif;
  font-size: 16px;
  line-height: 24px;
  margin: 0;
}

.pricing-card.light .pricing-sub {
  color: #3b4a41;
}

.pricing-card.dark .pricing-sub {
  color: rgba(255, 255, 255, 0.8);
}

.pricing-price-row {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: auto;
  margin: 24px 0;
}

.pricing-price-num {
  font-family: 'Newsreader', serif;
  font-size: 48px;
  font-weight: 400;
  line-height: 48px;
}

.pricing-card.light .pricing-price-num {
  color: #1a1c1c;
}

.pricing-card.dark .pricing-price-num {
  color: white;
}

.pricing-price-unit {
  font-size: 20px;
  line-height: 28px;
}

.pricing-card.light .pricing-price-unit {
  color: #3b4a41;
}

.pricing-card.dark .pricing-price-unit {
  color: rgba(255, 255, 255, 0.8);
}

.pricing-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0;
  margin: 20px 0;
}

.pricing-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  line-height: 24px;
}

.pricing-card.light .pricing-list li {
  color: #1a1c1c;
}

.pricing-card.dark .pricing-list li {
  color: white;
}

.pricing-list li svg {
  flex-shrink: 0;
}

.pricing-btn {
  width: 100%;
  height: 56px;
  border: none;
  border-radius: 9999px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
  transition: filter 0.18s ease, transform 0.1s ease;
}

.pricing-btn:hover {
  filter: brightness(0.92);
}

.pricing-btn:active {
  transform: scale(0.97);
}

.pricing-btn.light-btn {
  background: rgb(226, 226, 226);
  color: #1a1c1c;
}

.pricing-btn.dark-btn {
  background: white;
  color: #006C49;
}

/* ─── 安全承诺 ─── */
.home-security {
  max-width: 1000px;
  margin: 0 auto 80px;
  background: rgb(255, 255, 255);
  border: 1px solid rgba(229, 231, 235, 0.50);
  border-radius: 32px;
  padding: 48px;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 64px;
}

.security-left {
  width: 269px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.security-title {
  font-size: 30px;
  font-weight: 400;
  color: rgb(18, 18, 18);
  line-height: 36px;
  margin: 0;
}

.security-desc {
  font-size: 16px;
  color: rgb(107, 114, 128);
  line-height: 26px;
  margin: 0;
}

.security-grid {
  width: 537px;
  display: grid;
  grid-template-columns: 245px 245px;
  column-gap: 47px;
  row-gap: 48px;
}

.security-item {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.security-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.security-item-text h4 {
  font-size: 16px;
  font-weight: 400;
  color: rgb(18, 18, 18);
  line-height: 24px;
  margin: 0 0 4px;
}

.security-item-text p {
  font-size: 14px;
  color: rgb(107, 114, 128);
  line-height: 22.75px;
  margin: 0;
}


.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.empty-icon {
  color: #dcdfe6;
  margin-bottom: 20px;
  font-size: 80px;
}

.empty-text {
  font-size: 18px;
  color: rgb(107, 114, 128);
  margin-bottom: 10px;
}

.empty-hint {
  font-size: 14px;
  color: #c0c4cc;
}

/* ─── 响应式 ─── */
@media (max-width: 1100px) {
  .home-features {
    grid-template-columns: repeat(2, 1fr);
  }

  .pricing-cards {
    grid-template-columns: 1fr;
  }

  .stats-inner {
    flex-wrap: wrap;
  }

  .stat-item {
    flex: 1;
    min-width: 150px;
  }

  .home-security {
    flex-direction: column;
    gap: 40px;
  }

  .security-left {
    width: 100%;
  }

  .security-grid {
    width: 100%;
    grid-template-columns: 1fr 1fr;
    column-gap: 32px;
    row-gap: 32px;
  }
}

@media (max-width: 680px) {
  .home-hero {
    padding: 80px 20px 60px;
  }

  .hero-title {
    font-size: 44px;
    line-height: 58px;
    letter-spacing: -1px;
  }

  .hero-desc {
    font-size: 16px;
    line-height: 26px;
  }

  .home-features {
    grid-template-columns: 1fr;
    gap: 20px;
    padding-bottom: 60px;
  }

  .feature-card {
    padding: 24px;
  }

  .stats-inner {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .stat-item {
    flex: 0 1 calc(50% - 16px);
    min-width: 140px;
  }

  .pricing-cards {
    gap: 16px;
  }

  .pricing-card {
    padding: 36px;
  }

  .home-security {
    padding: 32px;
    border-radius: 24px;
  }

  .security-title {
    font-size: 24px;
  }

  .security-grid {
    grid-template-columns: 1fr;
    row-gap: 24px;
  }


  .pricing-heading {
    font-size: 26px;
  }
}
</style>
