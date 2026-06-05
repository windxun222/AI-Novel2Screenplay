<template>
  <div class="home">
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">AI 小说转剧本工具</h1>
        <p class="hero-subtitle">
          将你的小说作品自动转换为结构化中文剧本 YAML，<br />
          降低改编门槛，让创作更流畅。
        </p>
        <router-link to="/convert" class="btn btn-primary hero-btn">
          开始转换
        </router-link>
      </div>
    </section>

    <section class="features container">
      <div class="feature-card">
        <div class="feature-icon">&#9881;</div>
        <h3>逐章处理</h3>
        <p>智能分章，逐章提交 AI 转换，上下文自动衔接，确保连续性。</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#128196;</div>
        <h3>中文剧本规范</h3>
        <p>遵循中文影视通用格式：场景标题、动作描述、角色对白、旁白与转场。</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#128220;</div>
        <h3>YAML 结构化输出</h3>
        <p>输出标准 YAML 格式，可编辑、可版本化管理、可进一步打磨。</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#9888;</div>
        <h3>连续性校验</h3>
        <p>自动检测角色命名冲突、场景逻辑矛盾，输出警告供作者审阅。</p>
      </div>
    </section>

    <section class="usage container">
      <h2 class="section-title">使用方法</h2>
      <div class="steps">
        <div class="step">
          <span class="step-num">1</span>
          <div>
            <strong>粘贴或上传</strong>
            <p>将你的小说文本（3 章以上）粘贴到输入框，或上传 .txt 文件。</p>
          </div>
        </div>
        <div class="step">
          <span class="step-num">2</span>
          <div>
            <strong>AI 自动转换</strong>
            <p>系统逐章调用 DeepSeek API，提取角色、分析场景、生成剧本。</p>
          </div>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <div>
            <strong>校验与编辑</strong>
            <p>查看连续性校验结果，直接在编辑器中调整剧本内容。</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
</script>

<style scoped>
.hero {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 80px 24px;
  text-align: center;
}
.hero-content {
  max-width: 640px;
  margin: 0 auto;
}
.hero-title {
  font-size: 40px;
  font-weight: 700;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #7c8cf0, #a0b4ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-subtitle {
  font-size: 16px;
  color: #a0a0b0;
  margin-bottom: 32px;
  line-height: 1.8;
}
.hero-btn {
  font-size: 16px;
  padding: 12px 32px;
}
.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  padding-top: 48px;
  padding-bottom: 48px;
}
.feature-card {
  background: #1a1a2e;
  border: 1px solid #2a2a4a;
  border-radius: 8px;
  padding: 24px;
}
.feature-icon {
  font-size: 28px;
  margin-bottom: 12px;
}
.feature-card h3 {
  font-size: 16px;
  margin-bottom: 8px;
}
.feature-card p {
  font-size: 13px;
  color: #a0a0b0;
  line-height: 1.6;
}
.usage {
  padding-bottom: 64px;
}
.steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.step {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  padding: 16px;
  background: #1a1a2e;
  border: 1px solid #2a2a4a;
  border-radius: 8px;
}
.step-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #4a5ae0;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}
.step strong {
  display: block;
  margin-bottom: 4px;
}
.step p {
  font-size: 13px;
  color: #a0a0b0;
}
</style>
