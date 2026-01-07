// Cloudflare Worker для проксирования запросов к rasp.sstu.ru
// Разверните этот код в Cloudflare Workers (бесплатно)

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // Получаем URL из параметра запроса
  const url = new URL(request.url)
  let targetUrl = url.searchParams.get('url')
  
  // Если URL не передан, используем путь из запроса
  if (!targetUrl) {
    const path = url.pathname
    if (path === '/' || path === '') {
      targetUrl = 'https://rasp.sstu.ru/'
    } else {
      targetUrl = `https://rasp.sstu.ru${path}${url.search}`
    }
  }
  
  // Создаем новый запрос к целевому сайту с увеличенным таймаутом
  const modifiedRequest = new Request(targetUrl, {
    method: request.method,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
      'Accept-Encoding': 'gzip, deflate, br',
      'Connection': 'keep-alive',
      'Upgrade-Insecure-Requests': '1',
      'Cache-Control': 'no-cache',
    },
    body: request.body,
    // Cloudflare Workers автоматически используют таймаут до 30 секунд для fetch
  })
  
  try {
    // Используем fetch с таймаутом через AbortController
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 25000) // 25 секунд таймаут
    
    const response = await fetch(modifiedRequest, {
      signal: controller.signal,
      // Cloudflare Workers автоматически проксируют через их сеть
    })
    
    clearTimeout(timeoutId)
    
    // Создаем новый ответ с правильными заголовками
    const modifiedResponse = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'text/html; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Cache-Control': 'no-cache',
      },
    })
    
    return modifiedResponse
  } catch (error) {
    if (error.name === 'AbortError') {
      return new Response('Request timeout', { status: 504 })
    }
    return new Response(`Error: ${error.message}`, { status: 500 })
  }
}

