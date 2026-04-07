"""
API FastAPI pour le scraper.
Usage: uvicorn api:app --port 8001
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from .scraper import SiteScraper, RawStyles

app = FastAPI(
    title="EURKAI Scraper API",
    description="API pour scraper les design tokens d'un site web",
    version="0.1.0"
)

scraper = SiteScraper()


class ScrapeRequest(BaseModel):
    """Requête de scraping."""
    url: HttpUrl
    screenshot: bool = True


@app.post("/scrape", response_model=RawStyles)
async def scrape_site(request: ScrapeRequest):
    """
    Scrape un site et retourne les design tokens.

    Args:
        url: URL du site à scraper
        screenshot: Inclure un screenshot (base64)

    Returns:
        RawStyles avec tous les tokens extraits
    """
    try:
        styles = scraper.scrape(str(request.url), screenshot=request.screenshot)
        return styles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur scraping: {str(e)}")


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "eurkai-scraper"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 EURKAI Scraper API")
    print("   → http://127.0.0.1:8001")
    print("   → http://127.0.0.1:8001/docs")
    uvicorn.run(app, host="127.0.0.1", port=8001)
