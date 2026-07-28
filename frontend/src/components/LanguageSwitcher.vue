<template>
  <nav class="language-switcher" :aria-label="t('app.language')">
    <button
      v-for="option in options"
      :key="option.locale"
      type="button"
      :data-locale="option.locale"
      :class="{ active: locale === option.locale }"
      :aria-current="locale === option.locale ? 'true' : undefined"
      @click="selectLocale(option.locale)"
    >
      {{ t(option.label) }}
    </button>
  </nav>
</template>

<script>
import { useI18n } from 'vue-i18n'
import { switchLocale } from '../i18n/locale'

export default {
  name: 'LanguageSwitcher',
  setup() {
    const { t, locale } = useI18n()
    const options = [
      { locale: 'zh-CN', label: 'app.chinese' },
      { locale: 'en-US', label: 'app.english' },
    ]

    const selectLocale = (nextLocale) => {
      if (nextLocale === locale.value) return

      const previousLocale = locale.value
      switchLocale(nextLocale)
      locale.value = nextLocale
      document.documentElement.lang = nextLocale
      window.gtag?.('event', 'language_change', {
        from_language: previousLocale,
        to_language: nextLocale,
      })
    }

    return {
      locale,
      options,
      selectLocale,
      t,
    }
  },
}
</script>

<style scoped>
.language-switcher {
  position: absolute;
  top: 20px;
  right: 20px;
  display: inline-flex;
  padding: 3px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
}

.language-switcher button {
  padding: 6px 12px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: white;
  cursor: pointer;
}

.language-switcher button.active {
  background: white;
  color: #5f6fdd;
}
</style>
