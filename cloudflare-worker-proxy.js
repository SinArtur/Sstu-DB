// Cloudflare Worker для проксирования запросов к rasp.sstu.ru
// Разверните этот код в Cloudflare Workers (бесплатно)

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // Получаем URL из параметра запроса
  const url = new URL(request.url)
  const targetUrl = url.searchParams.get('url') || 'https://rasp.sstu.ru/'
  
  // Создаем новый запрос к целевому сайту
  const modifiedRequest = new Request(targetUrl, {
    method: request.method,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
      'Accept-Encoding': 'gzip, deflate, br',
      'Connection': 'keep-alive',
      'Upgrade-Insecure-Requests': '1',
    },
    body: request.body,
  })
  
  try {
    const response = await fetch(modifiedRequest)
    
    // Создаем новый ответ с правильными заголовками
    const modifiedResponse = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'text/html; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    })
    
    return modifiedResponse
  } catch (error) {
    return new Response(`Error: ${error.message}`, { status: 500 })
  }
}

