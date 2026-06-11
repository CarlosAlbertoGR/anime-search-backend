from fastapi import FastAPI, Query
import httpx
from bs4 import BeautifulSoup
import asyncio

app = FastAPI(title="Anime Figure Search API")

@app.get("/")
def home():
    return {"status": "API is running. Use /buscar?query=tu_busqueda"}

async def buscar_mandarake(keyword: str):
    # Usamos la URL de búsqueda global que es más amigable para scraping
    url = f"https://order.mandarake.co.jp/order/listPage/list?keyword={keyword}&lang=en"
    
    # CRUCIAL: Añadimos cabeceras para que Mandarake no nos bloquee o nos mande una página vacía
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=15.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Mandarake organiza sus productos en divs con la clase 'item' o dentro de un contenedor 'thumblist'
            # Vamos a usar un selector más amplio para asegurar capturar las tarjetas de producto
            items = soup.select('.item .detail') or soup.find_all('div', class_='thumblist')
            
            if not items:
                # Intento alternativo por estructura de bloques común en Mandarake
                items = soup.find_all('div', class_='block')

            for item in items[:15]:
                # Buscamos el título (suele estar en un h1 o un div .title)
                title_el = item.find(['div', 'h1', 'p'], class_='title')
                title = title_el.text.strip() if title_el else None
                
                # Buscamos el precio
                price_el = item.find('p', class_='price')
                price = price_el.text.strip() if price_el else "Consultar"
                
                # Buscamos el link y la imagen
                parent = item.find_parent('div') or item
                link_el = parent.find('a')
                link = "https://order.mandarake.co.jp" + link_el['href'] if link_el and link_el.has_attr('href') else url
                
                img_el = parent.find('img')
                image = img_el['src'] if img_el and img_el.has_attr('src') else ""
                
                if title:  # Solo agregamos si logramos extraer al menos el título
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
        
    resultados_totales = await asyncio.gather(*tareas)
    resultado_final = [item for sublist in resultados_totales for item in sublist]
    
    return {"resultados": resultado_final}
