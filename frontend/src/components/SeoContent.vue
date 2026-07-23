<template>
  <section class="seo-content" v-if="showSeoContent">
    <div class="content-section">
      <h2>🎯 SheetFlow 是什么？</h2>
      <p>
        SheetFlow 是一款免费的在线 Excel 转图片工具。只需上传 Excel 文件，
        设置分页规则，即可自动生成多张高质量图片并打包下载。
      </p>

      <h2>✨ 核心功能</h2>
      <ul>
        <li><strong>Excel 转图片</strong> - 支持 .xlsx 格式，保留表格样式</li>
        <li><strong>智能分页</strong> - 自定义表头行数和每页数据行数</li>
        <li><strong>固定表头</strong> - 每张图片都包含固定表头信息</li>
        <li><strong>多格式输出</strong> - 支持 PNG 和 JPG 格式</li>
        <li><strong>批量处理</strong> - 支持多 Sheet 一并处理</li>
        <li><strong>一键下载</strong> - 自动打包 ZIP 文件</li>
      </ul>

      <h2>📋 适用场景</h2>
      <div class="scenarios">
        <div class="scenario">
          <h3>💰 退款单生成</h3>
          <p>批量生成退款单图片，方便客服发送给客户</p>
        </div>
        <div class="scenario">
          <h3>📦 订单截图</h3>
          <p>将订单数据转换为图片，用于存档或分享</p>
        </div>
        <div class="scenario">
          <h3>📊 数据报表</h3>
          <p>将 Excel 报表转换为图片，便于展示和汇报</p>
        </div>
        <div class="scenario">
          <h3>🎨 运营素材</h3>
          <p>快速生成运营活动所需的表格图片素材</p>
        </div>
      </div>

      <h2>🚀 使用方法</h2>
      <ol>
        <li>上传 Excel 文件（.xlsx 格式）</li>
        <li>选择要处理的 Sheet</li>
        <li>设置表头行数和每页数据行数</li>
        <li>选择输出格式（PNG 或 JPG）</li>
        <li>点击"开始生成"</li>
        <li>下载 ZIP 文件</li>
      </ol>

      <h2>❓ 常见问题</h2>
      <div class="faq">
        <div class="faq-item">
          <h3>支持哪些 Excel 格式？</h3>
          <p>目前支持 .xlsx 格式。后续版本将支持 .xls 和 .csv 格式。</p>
        </div>
        <div class="faq-item">
          <h3>支持复杂的 Excel 公式吗？</h3>
          <p>SheetFlow 会读取公式的计算结果值，但不会重新计算公式。</p>
        </div>
        <div class="faq-item">
          <h3>图片质量如何？</h3>
          <p>默认使用 2x 分辨率生成，确保图片清晰。PNG 格式无损压缩，JPG 格式可调节质量。</p>
        </div>
        <div class="faq-item">
          <h3>文件大小有限制吗？</h3>
          <p>建议文件大小不超过 10MB，行数不超过 10000 行，以获得最佳体验。</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'SeoContent',
  setup() {
    const showSeoContent = ref(false)

    onMounted(() => {
      // Show SEO content after initial render for better LCP
      setTimeout(() => {
        showSeoContent.value = true
      }, 100)
    })

    return {
      showSeoContent
    }
  }
}
</script>

<style scoped>
.seo-content {
  background: white;
  border-radius: 12px;
  padding: 40px 30px;
  margin-top: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.content-section h2 {
  color: #333;
  font-size: 1.5rem;
  margin: 30px 0 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #667eea;
}

.content-section h2:first-child {
  margin-top: 0;
}

.content-section p {
  color: #666;
  line-height: 1.8;
  margin-bottom: 15px;
}

.content-section ul,
.content-section ol {
  color: #666;
  line-height: 2;
  padding-left: 25px;
  margin-bottom: 20px;
}

.content-section li {
  margin-bottom: 8px;
}

.scenarios {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.scenario {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 20px;
  border-left: 4px solid #667eea;
}

.scenario h3 {
  color: #333;
  font-size: 1.1rem;
  margin-bottom: 10px;
}

.scenario p {
  color: #666;
  font-size: 0.95rem;
  margin: 0;
}

.faq {
  margin: 20px 0;
}

.faq-item {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 15px;
}

.faq-item h3 {
  color: #333;
  font-size: 1.1rem;
  margin-bottom: 10px;
}

.faq-item p {
  color: #666;
  margin: 0;
}

@media (max-width: 600px) {
  .seo-content {
    padding: 20px 15px;
  }

  .scenarios {
    grid-template-columns: 1fr;
  }
}
</style>
