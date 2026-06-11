from fastapi import FastAPI, Query
import httpx
from bs4 import BeautifulSoup
import asyncio

app = FastAPI(title="Anime Figure Search API")

@app.get("/")
def home():
    return {"status": "API is running. Use /buscar?query=tu_busqueda"}

# NUEVA FUNCIÓN: API Oficial de Mercado Libre
async def buscar_mercado_libre(keyword: str):
    # Usamos el site 'MLM' que corresponde a Mercado Libre México
    url = f"https://api.mercadolibre.com/sites/MLM/search?q={keyword}&category=MLM1126" # Categoría: Figuras de Acción
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            data = response.json()
            results = []
            
            # Recorremos los productos que nos da la API
            for item in data.get("results", [])[:15]:
                results.append({
                    "tienda": "Mercado Libre",
                    "titulo": item.get("title"),
                    "precio": f"${item.get('price')} MXN",
                    "imagen": item.get("thumbnail"),
                    "url": item.get("permalink")
                })
            return results
        except Exception as e:
            return [{"tienda": "Mercado Libre", "error": str(e)}]

async def buscar_mandarake(keyword: str):
    url = f"https://order.mandarake.co.jp/order/listPage/list?keyword={keyword}&lang=en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=10.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            items = soup.select('.item .detail') or soup.find_all('div', class_='thumblist')
            for item in items[:10]:
                title_el = item.find(['div', 'h1', 'p'], class_='title')
                if title_el:
                    results.append({
                        "tienda": "Mandarake",
                        "titulo": title_el.text.strip(),
                        "precio": "Ver en web",
                        "imagen": "",
                        "url": url
                    })
            return results
        except:
            return []

@app.get("/buscar")
async def buscar(query: str = Query(..., min_length=2), sitios: str = ""):
    lista_sitios = sitios.split(",") if sitios else ["mercadolibre", "mandarake"]
    tareas = []
    
    if "mercadolibre" in lista_sitios:
        tareas.append(buscar_mercado_libre(query))
    if "mandarake" in lista_sitios:
        tareas.append(buscar_mandarake(query))
        
    resultados_totales = await asyncio.gather(*tareas)
    resultado_final = [item for sublist in resultados_totales for item in sublist]
    
    return {"resultados": resultado_final}
