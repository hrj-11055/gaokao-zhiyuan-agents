function defaultSleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function waitForPregeneratedReport({
  checkStatus,
  intervalMs = 2000,
  timeoutMs = 330000,
  sleep = defaultSleep,
}) {
  const startedAt = Date.now()

  while (Date.now() - startedAt < timeoutMs) {
    const result = await checkStatus()

    if (result?.status === 'ready' && result.url) {
      return result
    }
    if (result?.status === 'failed') {
      const err = new Error(result.error || '报告生成失败，请稍后重试')
      err.code = 'PREGEN_FAILED'
      throw err
    }
    if (result?.status === 'not_found') {
      return null
    }

    await sleep(intervalMs)
  }

  const err = new Error('报告生成时间较长，请稍后重试')
  err.code = 'PREGEN_TIMEOUT'
  throw err
}
