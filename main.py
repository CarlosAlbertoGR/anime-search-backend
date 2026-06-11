from fastapi import FastAPI, Query
import httpx
from bs4 import BeautifulSoup
import asyncio
import urllib.parse

app = FastAPI(title="Anime Figure Search API")

@app.get("/")
def home():
    return {"status": "API is running. Ready for real queries."}

# 1. API Oficial de Mercado Libre (México)
async def buscar_mercado_libre(keyword: str):
    # Codificamos el texto (ej. "mazinger z" -> "mazinger%20z")
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://api.mercadolibre.com/sites/MLM/search?q={safe_keyword}&category=MLM1126"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            data = response.json()
            results = []
            
            for item in data.get("results", [])[:10]: # Traemos los primeros 10
                results.append({
                    "tienda": "Mercado Libre",
                    "titulo": item.get("title", "Sin título"),
                    "precio": f"${item.get('price')} MXN",
                    "imagen": item.get("thumbnail", "").replace("http://", "https://"), # Forzamos HTTPS
                    "url": item.get("permalink", url)
                })
            return results
        except Exception as e:
            print(f"Error ML: {e}")
            return []

# 2. Scraper Ligero para eBay
async def buscar_ebay(keyword: str):
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://www.ebay.com/sch/i.html?_nkw={safe_keyword}&_sacat=0"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=12.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # eBay usa la clase 's-item' para sus productos
            items = soup.select('.s-item')
            for item in items[1:11]: # Saltamos el 0 porque suele ser un anuncio fantasma
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
            return results
        except Exception as e:
            print(f"Error eBay: {e}")
            return []

# 3. Scraper para Mandarake
async def buscar_mandarake(keyword: str):
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://order.mandarake.co.jp/order/listPage/list?keyword={safe_keyword}&lang=en"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=15.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            items = soup.find_all('div', class_='block')
            for item in items[:10]:
                title_el = item.find('div', class_='title')
                price_el = item.find('p', class_='price')
                img_el = item.find('img')
                
                # Buscamos el enlace en el padre
                link_tag = item.find('a')
                
                if title_el:
                    titulo = title_el.text.strip()
                    # Limpiamos el texto de Mandarake que a veces viene sucio
                    titulo = " ".join(titulo.split())
                    
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
            return results
        except Exception as e:
            print(f"Error Mandarake: {e}")
            return []

# 4. El Orquestador (Ejecuta todo al mismo tiempo)
@app.get("/buscar")
async def buscar(query: str = Query(..., min_length=2)):
    # Lanzamos las 3 tareas de forma concurrente
    tareas = [
        buscar_mercado_libre(query),
        buscar_ebay(query),
        buscar_mandarake(query)
    ]
    
    resultados_totales = await asyncio.gather(*tareas)
    
    # Unimos las listas de resultados en una sola gran lista
    resultado_final = []
    for sublista in resultados_totales:
        resultado_final.extend(sublista)
    
    return {"resultados": resultado_final}
