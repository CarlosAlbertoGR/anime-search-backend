from fastapi import FastAPI, Query
import httpx
from bs4 import BeautifulSoup
import asyncio
import urllib.parse

app = FastAPI(title="Anime Figure Search API")

@app.get("/")
def home():
    return {"status": "API is running. Ready for Android."}

# Disfrazamos el servidor de Render como si fuera una PC normal con Google Chrome
HEADERS_NINJA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive"
}

HEADERS_HTML = HEADERS_NINJA.copy()
HEADERS_HTML["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"

async def buscar_mercado_libre(keyword: str):
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://api.mercadolibre.com/sites/MLM/search?q={safe_keyword}&category=MLM1126"
    
    async with httpx.AsyncClient() as client:
        try:
            # Usamos headers ninja y le pedimos que nos avise si hay error HTTP
            response = await client.get(url, headers=HEADERS_NINJA, timeout=10.0)
            response.raise_for_status() 
            
            data = response.json()
            results = []
            
            for item in data.get("results", [])[:10]:
                results.append({
                    "tienda": "Mercado Libre",
                    "titulo": item.get("title", "Sin título"),
                    "precio": f"${item.get('price')} MXN",
                    "imagen": item.get("thumbnail", "").replace("http://", "https://"),
                    "url": item.get("permalink", url)
                })
            return results, None
        except Exception as e:
            return [], f"ML Falló: {str(e)}"

async def buscar_ebay(keyword: str):
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://www.ebay.com/sch/i.html?_nkw={safe_keyword}&_sacat=0"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=HEADERS_HTML, timeout=12.0)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            items = soup.select('.s-item')
            for item in items[1:11]: 
                title_el = item.select_one('.s-item__title')
                price_el = item.select_one('.s-item__price')
                img_el = item.select_one('.s-item__image-img')
                link_el = item.select_one('.s-item__link')
                
                if title_el and price_el and link_el:
                    results.append({
                        "tienda": "eBay",
                        "titulo": title_el.text.strip(),
                        "precio": price_el.text.strip(),
                        "imagen": img_el['src'] if img_el and 'src' in img_el.attrs else "",
                        "url": link_el['href']
                    })
            return results, None
        except Exception as e:
            return [], f"eBay Falló: {str(e)}"

async def buscar_mandarake(keyword: str):
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://order.mandarake.co.jp/order/listPage/list?keyword={safe_keyword}&lang=en"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=HEADERS_HTML, timeout=15.0)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            items = soup.find_all('div', class_='block')
            for item in items[:10]:
                title_el = item.find('div', class_='title')
                price_el = item.find('p', class_='price')
                img_el = item.find('img')
                link_tag = item.find('a')
                
                if title_el:
                    titulo = " ".join(title_el.text.strip().split())
                    imagen = img_el['src'] if img_el and 'src' in img_el.attrs else ""
                    if imagen.startswith("//"):
                        imagen = "https:" + imagen
                    url_producto = "https://order.mandarake.co.jp" + link_tag['href'] if link_tag else url
                    
                    results.append({
                        "tienda": "Mandarake",
                        "titulo": titulo,
                        "precio": price_el.text.strip() if price_el else "Consultar",
                        "imagen": imagen,
                        "url": url_producto
                    })
            return results, None
        except Exception as e:
            return [], f"Mandarake Falló: {str(e)}"

@app.get("/buscar")
async def buscar(query: str = Query(..., min_length=2)):
    tareas = [
        buscar_mercado_libre(query),
        buscar_ebay(query),
        buscar_mandarake(query)
    ]
    
    resultados_totales = await asyncio.gather(*tareas)
    
    resultado_final = []
    errores = []
    
    for sublista, error in resultados_totales:
        if sublista:
            resultado_final.extend(sublista)
        if error:
            errores.append(error)
    
    # Si alguna tienda nos bloquea, ahora lo sabremos
    return {
        "resultados": resultado_final,
        "alertas_debug": errores
    }
