from fastapi import FastAPI, Query
import httpx
from bs4 import BeautifulSoup
import asyncio

app = FastAPI(title="Anime Figure Search API")

# Scraper para Mandarake (Ejemplo base)
async def buscar_mandarake(keyword: str):
    url = f"https://order.mandarake.co.jp/order/listPage/list?keyword={keyword}&lang=en"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Buscamos los contenedores de las figuras en el HTML de Mandarake
            items = soup.find_all('div', class_='thumblist')
            for item in items[:10]: # Limitamos a los primeros 10 para ir rápido
                title = item.find('div', class_='title').text.strip() if item.find('div', class_='title') else "Figura"
                price = item.find('p', class_='price').text.strip() if item.find('p', class_='price') else "Consultar"
                link = "https://order.mandarake.co.jp" + item.find('a')['href'] if item.find('a') else url
                image = item.find('img')['src'] if item.find('img') else ""
                
                results.append({
                    "tienda": "Mandarake",
                    "titulo": title,
                    "precio": price,
                    "imagen": image,
                    "url": link
                })
            return results
        except Exception as e:
            return [{"tienda": "Mandarake", "error": str(e)}]

@app.get("/buscar")
async def buscar(query: str = Query(..., min_length=2), sitios: str = ""):
    lista_sitios = sitios.split(",") if sitios else ["mandarake"]
    tareas = []
    
    if "mandarake" in lista_sitios:
        tareas.append(buscar_mandarake(query))
    
    # Aquí irían las funciones para eBay, Mercado Libre, etc.
    # if "ebay" in lista_sitios: tareas.append(buscar_ebay(query))

    # Ejecutamos todas las búsquedas al mismo tiempo (en paralelo)
    resultados_totales = await asyncio.gather(*tareas)
    
    # Aplanamos la lista de listas en una sola
    resultado_final = [item for sublist in resultados_totales for item in sublist]
    
    return {"resultados": resultado_final}