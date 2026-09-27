import { useAuthStore } from '@/stores/authStore'

type SSEHandler = (data: Record<string, unknown>) => void

/**
 * 用 fetch 读取 POST + SSE 的流式响应（axios 不支持浏览器端流式读取）。
 * 服务端每条事件形如 `data: {"delta": "..."}\n\n`。
 */
export async function streamSSE(
  url: string,
  body: unknown,
  onEvent: SSEHandler,
  signal?: AbortSignal,
): Promise<void> {
  const token = useAuthStore.getState().token
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!resp.ok || !resp.body) {
    let detail = `请求失败（HTTP ${resp.status}）`
    try {
      const err = await resp.json()
      if (err?.detail) detail = String(err.detail)
    } catch {
      // 非 JSON 响应体，保留默认错误信息
    }
    throw new Error(detail)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''
    for (const part of parts) {
      for (const line of part.split('\n')) {
        if (!line.startsWith('data:')) continue
        const payload = line.slice(5).trim()
        if (!payload) continue
        try {
          onEvent(JSON.parse(payload) as Record<string, unknown>)
        } catch {
          // 忽略无法解析的行（如心跳）
        }
      }
    }
  }
}
