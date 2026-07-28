const JOB_MESSAGE_CODES = new Set([
  'parsing',
  'empty_workbook',
  'no_sheets',
  'preparing',
  'processing_sheet',
  'processing_sheet_page',
  'empty_sheets',
  'zipping',
  'completed',
  'failed',
  'queued',
  'uploaded',
])

const ERROR_CODES = new Set([
  'file.unsupported_type',
  'file.not_found',
  'file.parse_failed',
  'job.not_found',
  'job.not_completed',
  'job.invalid_sheet_indices',
  'output.not_found',
])

function translate(t, key, params = {}, plural) {
  return plural === undefined ? t(key, params) : t(key, params, plural)
}

export function localizeJobMessage(payload = {}, t) {
  const normalizedPayload = payload && typeof payload === 'object' ? payload : {}
  const messageCode = typeof normalizedPayload.message_code === 'string'
    ? normalizedPayload.message_code
    : ''
  const code = messageCode.replace(/^job\./, '')

  if (JOB_MESSAGE_CODES.has(code)) {
    const params = normalizedPayload.message_params
      && typeof normalizedPayload.message_params === 'object'
      ? normalizedPayload.message_params
      : {}
    const key = code === 'completed' && Number(params.pages) === 1
      ? 'job.completed_one_page'
      : `job.${code}`
    return translate(t, key, params, code === 'completed' ? params.sheets : undefined)
  }

  if (!messageCode && typeof normalizedPayload.message === 'string' && normalizedPayload.message) {
    return normalizedPayload.message
  }
  return t('errors.generic')
}

export function localizeApiError(payload = {}, t) {
  const detail = payload?.detail ?? payload

  if (typeof detail === 'string' && detail) return detail
  if (detail && typeof detail === 'object' && ERROR_CODES.has(detail.code)) {
    const params = detail.params && typeof detail.params === 'object' ? detail.params : {}
    return t(`errors['${detail.code}']`, params)
  }

  return t('errors.generic')
}
