from fastapi import FastAPI, Query

app = FastAPI(title="Anime Figure Search API")

@app.get("/")
def home():
    return {"status": "API is running. Ready for Android integration."}

@app.get("/buscar")
async def buscar(query: str = Query(..., min_length=2), sitios: str = ""):
    # Convertimos a minúsculas para validar
    query_lower = query.lower()
    
    # Si busca algo relacionado con Goku, le mandamos figuras de prueba reales
    if "goku" in query_lower:
        return {
            "resultados": [
                {
                    "tienda": "Mercado Libre",
                    "titulo": "S.H. Figuarts Goku Super Saiyan Awakening Bound",
                    "precio": "$1,450 MXN",
                    "imagen": "https://http2.mlstatic.com/D_NQ_NP_2X_735681-MLM51336494957_082022-F.webp",
                    "url": "https://www.mercadolibre.com.mx"
                },
                {
                    "tienda": "Mandarake",
                    "titulo": "Dragon Ball Z - Son Goku - Solid Edge Works Vol.1",
                    "precio": "3,500 JPY",
                    "imagen": "https://img.mandarake.co.jp/mevent/00/02/14/36/0002143615.jpg",
                    "url": "https://order.mandarake.co.jp"
                },
                {
                    "tienda": "Mercado Libre",
                    "titulo": "Figura Banpresto Dragon Ball Z Blood of Saiyans Goku",
                    "precio": "$699 MXN",
                    "imagen": "https://http2.mlstatic.com/D_NQ_NP_2X_892241-MLM74288339192_022024-F.webp",
                    "url": "https://www.mercadolibre.com.mx"
                }
            ]
        }
    else:
        # Si busca cualquier otra cosa, le damos una figura genérica de prueba
        return {
            "resultados": [
                {
                    "tienda": "Mercado Libre",
                    "titulo": f"Figura Coleccionable Anime - {query}",
                    "precio": "$450 MXN",
                    "imagen": "https://http2.mlstatic.com/D_NQ_NP_2X_892241-MLM74288339192_022024-F.webp",
                    "url": "https://www.mercadolibre.com.mx"
                }
            ]
        }
