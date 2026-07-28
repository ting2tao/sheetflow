<template>
  <section class="seo-content" v-if="showSeoContent">
    <div class="content-section">
      <h2>{{ t('seo.whatTitle') }}</h2>
      <p>{{ t('seo.whatBody') }}</p>

      <h2>{{ t('seo.featuresTitle') }}</h2>
      <ul>
        <li v-for="(item, index) in features" :key="index">
          <strong>{{ item[0] }}</strong> - {{ item[1] }}
        </li>
      </ul>

      <h2>{{ t('seo.scenariosTitle') }}</h2>
      <div class="scenarios">
        <div v-for="(scenario, index) in scenarios" :key="index" class="scenario">
          <h3>{{ scenario[0] }}</h3>
          <p>{{ scenario[1] }}</p>
        </div>
      </div>

      <h2>{{ t('seo.usageTitle') }}</h2>
      <ol>
        <li v-for="(step, index) in usage" :key="index">{{ step }}</li>
      </ol>

      <h2>{{ t('seo.faqTitle') }}</h2>
      <div class="faq">
        <div v-for="(item, index) in faq" :key="index" class="faq-item">
          <h3>{{ item[0] }}</h3>
          <p>{{ item[1] }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()
const showSeoContent = ref(false)
let showTimer = null
const features = computed(() => tm('seo.features'))
const scenarios = computed(() => tm('seo.scenarios'))
const usage = computed(() => tm('seo.usage'))
const faq = computed(() => tm('seo.faq'))

onMounted(() => {
  // Show SEO content after initial render for better LCP
  showTimer = setTimeout(() => {
    showTimer = null
    showSeoContent.value = true
  }, 100)
})

onBeforeUnmount(() => {
  if (showTimer !== null) {
    clearTimeout(showTimer)
    showTimer = null
  }
})
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
