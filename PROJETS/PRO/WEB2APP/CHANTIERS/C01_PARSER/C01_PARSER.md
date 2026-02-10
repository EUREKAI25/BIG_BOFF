# CHANTIER 01 — PARSER (Extraction du site source)

⚠️ **CE PROJET N'UTILISE PAS EUREKAI**
Stack : Python + Playwright + BeautifulSoup. Pas de GEV/ERK.

---

## OBJECTIF
Extraire tout le contenu d'un site web (HTML, CSS, JS, assets) pour analyse ultérieure.

## INPUTS
- URL d'un site web
- OU code source (zip/repo)

## OUTPUTS
```python
@dataclass
class ParsedSite:
    url: str
    pages: list[ParsedPage]
    stylesheets: list[Stylesheet]
    scripts: list[Script]
    assets: list[Asset]
    metadata: SiteMetadata
```

---

## STRUCTURE DE FICHIERS

```
backend/app/parser/
├── __init__.py
├── models.py           # Dataclasses
├── scraper.py          # Playwright scraping
├── html_parser.py      # BeautifulSoup parsing
├── css_parser.py       # Extraction styles
├── js_parser.py        # Extraction JS/React
├── asset_extractor.py  # Images, fonts, etc.
└── utils.py
```

---

## MODÈLES DE DONNÉES

### models.py

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class ElementType(Enum):
    CONTAINER = "container"      # div, section, article
    TEXT = "text"                # p, span, h1-h6
    BUTTON = "button"            # button, a[role=button]
    LINK = "link"                # a
    IMAGE = "image"              # img
    INPUT = "input"              # input, textarea
    LIST = "list"                # ul, ol
    LIST_ITEM = "list_item"      # li
    FORM = "form"                # form
    VIDEO = "video"              # video
    ICON = "icon"                # svg, i.icon
    UNKNOWN = "unknown"

@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

@dataclass
class ComputedStyles:
    display: str = "block"
    position: str = "static"
    flex_direction: Optional[str] = None
    justify_content: Optional[str] = None
    align_items: Optional[str] = None
    padding: dict = field(default_factory=dict)  # top, right, bottom, left
    margin: dict = field(default_factory=dict)
    background_color: Optional[str] = None
    color: Optional[str] = None
    font_size: Optional[str] = None
    font_weight: Optional[str] = None
    font_family: Optional[str] = None
    border_radius: Optional[str] = None
    border: Optional[str] = None
    box_shadow: Optional[str] = None
    opacity: float = 1.0
    z_index: Optional[int] = None
    overflow: Optional[str] = None
    # Raw CSS pour cas non couverts
    raw: dict = field(default_factory=dict)

@dataclass
class ParsedElement:
    id: str                              # Unique ID généré
    tag: str                             # Tag HTML original
    element_type: ElementType            # Type normalisé
    classes: list[str] = field(default_factory=list)
    attributes: dict = field(default_factory=dict)
    text_content: Optional[str] = None
    children: list["ParsedElement"] = field(default_factory=list)
    styles: ComputedStyles = field(default_factory=ComputedStyles)
    bounding_box: Optional[BoundingBox] = None
    # Événements détectés
    has_click_handler: bool = False
    has_hover_effect: bool = False
    # Source
    source_html: str = ""

@dataclass
class ParsedPage:
    url: str
    path: str                            # /about, /contact
    title: str
    meta_description: Optional[str] = None
    root_element: Optional[ParsedElement] = None
    forms: list[ParsedElement] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)  # {text, href, is_internal}
    
@dataclass
class Stylesheet:
    url: Optional[str]
    content: str
    is_inline: bool = False
    media_queries: list[dict] = field(default_factory=list)

@dataclass
class Script:
    url: Optional[str]
    content: str
    is_inline: bool = False
    framework_detected: Optional[str] = None  # react, vue, angular, vanilla

@dataclass
class Asset:
    url: str
    local_path: Optional[str] = None
    asset_type: str = "unknown"  # image, font, video, audio
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None

@dataclass
class SiteMetadata:
    title: str
    description: Optional[str] = None
    favicon: Optional[str] = None
    theme_color: Optional[str] = None
    language: str = "en"
    framework: Optional[str] = None
    is_spa: bool = False
    has_dark_mode: bool = False
    color_palette: list[str] = field(default_factory=list)
    fonts_used: list[str] = field(default_factory=list)

@dataclass
class ParsedSite:
    url: str
    pages: list[ParsedPage] = field(default_factory=list)
    stylesheets: list[Stylesheet] = field(default_factory=list)
    scripts: list[Script] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    metadata: SiteMetadata = field(default_factory=SiteMetadata)
    parse_timestamp: str = ""
    parse_duration_ms: int = 0
```

---

## SCRAPER (Playwright)

### scraper.py

```python
import asyncio
from playwright.async_api import async_playwright, Page, Browser
from .models import ParsedSite, ParsedPage, Asset, SiteMetadata
from .html_parser import parse_html_tree
from .css_parser import extract_computed_styles
from typing import Optional
import hashlib
from datetime import datetime

class WebScraper:
    def __init__(self, max_pages: int = 20, timeout_ms: int = 30000):
        self.max_pages = max_pages
        self.timeout_ms = timeout_ms
        self.visited_urls: set[str] = set()
        
    async def scrape(self, url: str) -> ParsedSite:
        """Scrape un site web complet."""
        start_time = datetime.now()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Web2App Bot/1.0"
            )
            
            site = ParsedSite(url=url)
            
            # Scraper la page principale
            main_page = await self._scrape_page(context, url)
            site.pages.append(main_page)
            self.visited_urls.add(url)
            
            # Extraire et suivre les liens internes
            internal_links = [
                link["href"] for link in main_page.links 
                if link["is_internal"] and link["href"] not in self.visited_urls
            ]
            
            # Scraper les pages liées (jusqu'à max_pages)
            for link in internal_links[:self.max_pages - 1]:
                if link not in self.visited_urls:
                    try:
                        page = await self._scrape_page(context, link)
                        site.pages.append(page)
                        self.visited_urls.add(link)
                    except Exception as e:
                        print(f"Erreur scraping {link}: {e}")
            
            # Extraire les métadonnées globales
            site.metadata = await self._extract_metadata(context, url)
            
            await browser.close()
        
        site.parse_duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        site.parse_timestamp = datetime.now().isoformat()
        
        return site
    
    async def _scrape_page(self, context, url: str) -> ParsedPage:
        """Scrape une page individuelle."""
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=self.timeout_ms, wait_until="networkidle")
            
            # Attendre que le JS s'exécute
            await page.wait_for_timeout(1000)
            
            # Extraire le HTML
            html = await page.content()
            
            # Extraire le titre
            title = await page.title()
            
            # Parser le HTML en arbre d'éléments
            root_element = await self._parse_page_elements(page)
            
            # Extraire les liens
            links = await self._extract_links(page, url)
            
            # Extraire les formulaires
            forms = await self._extract_forms(page)
            
            parsed_page = ParsedPage(
                url=url,
                path=self._url_to_path(url),
                title=title,
                root_element=root_element,
                links=links,
                forms=forms
            )
            
            return parsed_page
            
        finally:
            await page.close()
    
    async def _parse_page_elements(self, page: Page) -> ParsedElement:
        """Parse tous les éléments de la page avec leurs styles."""
        
        # Script pour extraire l'arbre DOM avec styles
        script = """
        () => {
            function parseElement(el, depth = 0) {
                if (depth > 50) return null;  // Limite de profondeur
                if (!el || el.nodeType !== 1) return null;
                
                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                
                // Ignorer les éléments invisibles
                if (rect.width === 0 && rect.height === 0) return null;
                if (styles.display === 'none') return null;
                if (styles.visibility === 'hidden') return null;
                
                const element = {
                    tag: el.tagName.toLowerCase(),
                    classes: Array.from(el.classList),
                    attributes: {},
                    textContent: el.childNodes.length === 1 && el.childNodes[0].nodeType === 3 
                        ? el.textContent.trim().substring(0, 500) 
                        : null,
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    styles: {
                        display: styles.display,
                        position: styles.position,
                        flexDirection: styles.flexDirection,
                        justifyContent: styles.justifyContent,
                        alignItems: styles.alignItems,
                        padding: {
                            top: styles.paddingTop,
                            right: styles.paddingRight,
                            bottom: styles.paddingBottom,
                            left: styles.paddingLeft
                        },
                        margin: {
                            top: styles.marginTop,
                            right: styles.marginRight,
                            bottom: styles.marginBottom,
                            left: styles.marginLeft
                        },
                        backgroundColor: styles.backgroundColor,
                        color: styles.color,
                        fontSize: styles.fontSize,
                        fontWeight: styles.fontWeight,
                        fontFamily: styles.fontFamily,
                        borderRadius: styles.borderRadius,
                        border: styles.border,
                        boxShadow: styles.boxShadow,
                        opacity: styles.opacity,
                        overflow: styles.overflow
                    },
                    hasClickHandler: el.onclick !== null || el.hasAttribute('onclick'),
                    children: []
                };
                
                // Attributs importants
                ['id', 'href', 'src', 'alt', 'placeholder', 'type', 'name', 'role', 'aria-label'].forEach(attr => {
                    if (el.hasAttribute(attr)) {
                        element.attributes[attr] = el.getAttribute(attr);
                    }
                });
                
                // Parser les enfants
                for (const child of el.children) {
                    const parsed = parseElement(child, depth + 1);
                    if (parsed) {
                        element.children.push(parsed);
                    }
                }
                
                return element;
            }
            
            return parseElement(document.body);
        }
        """
        
        result = await page.evaluate(script)
        return self._dict_to_parsed_element(result) if result else None
    
    def _dict_to_parsed_element(self, d: dict) -> ParsedElement:
        """Convertit un dict JS en ParsedElement."""
        if not d:
            return None
            
        element = ParsedElement(
            id=hashlib.md5(str(d).encode()).hexdigest()[:8],
            tag=d.get("tag", "div"),
            element_type=self._infer_element_type(d),
            classes=d.get("classes", []),
            attributes=d.get("attributes", {}),
            text_content=d.get("textContent"),
            has_click_handler=d.get("hasClickHandler", False),
        )
        
        if d.get("boundingBox"):
            bb = d["boundingBox"]
            element.bounding_box = BoundingBox(
                x=bb["x"], y=bb["y"], 
                width=bb["width"], height=bb["height"]
            )
        
        if d.get("styles"):
            s = d["styles"]
            element.styles = ComputedStyles(
                display=s.get("display", "block"),
                position=s.get("position", "static"),
                flex_direction=s.get("flexDirection"),
                justify_content=s.get("justifyContent"),
                align_items=s.get("alignItems"),
                padding=s.get("padding", {}),
                margin=s.get("margin", {}),
                background_color=s.get("backgroundColor"),
                color=s.get("color"),
                font_size=s.get("fontSize"),
                font_weight=s.get("fontWeight"),
                font_family=s.get("fontFamily"),
                border_radius=s.get("borderRadius"),
                border=s.get("border"),
                box_shadow=s.get("boxShadow"),
                opacity=float(s.get("opacity", 1)),
                overflow=s.get("overflow"),
            )
        
        # Parser les enfants récursivement
        for child in d.get("children", []):
            parsed_child = self._dict_to_parsed_element(child)
            if parsed_child:
                element.children.append(parsed_child)
        
        return element
    
    def _infer_element_type(self, d: dict) -> ElementType:
        """Détermine le type d'élément."""
        tag = d.get("tag", "").lower()
        attrs = d.get("attributes", {})
        classes = d.get("classes", [])
        
        # Mapping direct
        if tag in ["button"]:
            return ElementType.BUTTON
        if tag == "a":
            if attrs.get("role") == "button" or "btn" in " ".join(classes).lower():
                return ElementType.BUTTON
            return ElementType.LINK
        if tag == "img":
            return ElementType.IMAGE
        if tag in ["input", "textarea", "select"]:
            return ElementType.INPUT
        if tag in ["p", "span", "h1", "h2", "h3", "h4", "h5", "h6", "label"]:
            return ElementType.TEXT
        if tag in ["ul", "ol"]:
            return ElementType.LIST
        if tag == "li":
            return ElementType.LIST_ITEM
        if tag == "form":
            return ElementType.FORM
        if tag == "video":
            return ElementType.VIDEO
        if tag == "svg" or "icon" in " ".join(classes).lower():
            return ElementType.ICON
        if tag in ["div", "section", "article", "header", "footer", "nav", "main", "aside"]:
            return ElementType.CONTAINER
        
        return ElementType.UNKNOWN
    
    async def _extract_links(self, page: Page, base_url: str) -> list[dict]:
        """Extrait tous les liens de la page."""
        from urllib.parse import urlparse, urljoin
        
        base_domain = urlparse(base_url).netloc
        
        links = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                text: a.textContent.trim().substring(0, 100),
                href: a.href
            }))
        """)
        
        result = []
        for link in links:
            href = link["href"]
            parsed = urlparse(href)
            is_internal = parsed.netloc == base_domain or parsed.netloc == ""
            
            result.append({
                "text": link["text"],
                "href": href,
                "is_internal": is_internal
            })
        
        return result
    
    async def _extract_forms(self, page: Page) -> list:
        """Extrait les formulaires."""
        # Implémentation simplifiée
        return []
    
    async def _extract_metadata(self, context, url: str) -> SiteMetadata:
        """Extrait les métadonnées du site."""
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=self.timeout_ms)
            
            metadata = await page.evaluate("""
                () => ({
                    title: document.title,
                    description: document.querySelector('meta[name="description"]')?.content,
                    favicon: document.querySelector('link[rel="icon"]')?.href,
                    themeColor: document.querySelector('meta[name="theme-color"]')?.content,
                    language: document.documentElement.lang || 'en'
                })
            """)
            
            # Détecter le framework
            framework = await self._detect_framework(page)
            
            # Extraire la palette de couleurs
            colors = await self._extract_color_palette(page)
            
            # Extraire les fonts
            fonts = await self._extract_fonts(page)
            
            return SiteMetadata(
                title=metadata.get("title", ""),
                description=metadata.get("description"),
                favicon=metadata.get("favicon"),
                theme_color=metadata.get("themeColor"),
                language=metadata.get("language", "en"),
                framework=framework,
                color_palette=colors,
                fonts_used=fonts
            )
            
        finally:
            await page.close()
    
    async def _detect_framework(self, page: Page) -> Optional[str]:
        """Détecte le framework JS utilisé."""
        return await page.evaluate("""
            () => {
                if (window.__NEXT_DATA__) return 'nextjs';
                if (window.__NUXT__) return 'nuxt';
                if (document.querySelector('[data-reactroot]')) return 'react';
                if (document.querySelector('[data-v-]')) return 'vue';
                if (window.angular) return 'angular';
                return null;
            }
        """)
    
    async def _extract_color_palette(self, page: Page) -> list[str]:
        """Extrait les couleurs dominantes."""
        colors = await page.evaluate("""
            () => {
                const colors = new Set();
                const elements = document.querySelectorAll('*');
                
                elements.forEach(el => {
                    const styles = window.getComputedStyle(el);
                    const bg = styles.backgroundColor;
                    const color = styles.color;
                    
                    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                        colors.add(bg);
                    }
                    if (color) {
                        colors.add(color);
                    }
                });
                
                return Array.from(colors).slice(0, 20);
            }
        """)
        return colors
    
    async def _extract_fonts(self, page: Page) -> list[str]:
        """Extrait les fonts utilisées."""
        fonts = await page.evaluate("""
            () => {
                const fonts = new Set();
                const elements = document.querySelectorAll('*');
                
                elements.forEach(el => {
                    const fontFamily = window.getComputedStyle(el).fontFamily;
                    if (fontFamily) {
                        fontFamily.split(',').forEach(f => {
                            fonts.add(f.trim().replace(/['"]/g, ''));
                        });
                    }
                });
                
                return Array.from(fonts);
            }
        """)
        return fonts
    
    def _url_to_path(self, url: str) -> str:
        """Convertit une URL en path."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path or "/"
        return path if path != "" else "/"
```

---

## SERVICE

### service.py

```python
from .scraper import WebScraper
from .models import ParsedSite
import json
from pathlib import Path

class ParserService:
    def __init__(self, output_dir: str = "./parsed"):
        self.scraper = WebScraper()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def parse_url(self, url: str) -> ParsedSite:
        """Parse un site depuis son URL."""
        site = await self.scraper.scrape(url)
        return site
    
    async def parse_and_save(self, url: str) -> tuple[ParsedSite, Path]:
        """Parse et sauvegarde le résultat."""
        site = await self.parse_url(url)
        
        # Générer un nom de fichier
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace(".", "_")
        filename = f"{domain}_{site.parse_timestamp[:10]}.json"
        filepath = self.output_dir / filename
        
        # Sauvegarder
        self.save_to_json(site, filepath)
        
        return site, filepath
    
    def save_to_json(self, site: ParsedSite, filepath: Path):
        """Sauvegarde un ParsedSite en JSON."""
        from dataclasses import asdict
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(site), f, indent=2, ensure_ascii=False)
    
    def load_from_json(self, filepath: Path) -> dict:
        """Charge un ParsedSite depuis JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
```

---

## TESTS

### tests/test_parser.py

```python
import pytest
from backend.app.parser import ParserService, WebScraper
from backend.app.parser.models import ElementType

@pytest.mark.asyncio
async def test_scrape_simple_page():
    """Test scraping d'une page simple."""
    scraper = WebScraper(max_pages=1)
    site = await scraper.scrape("https://example.com")
    
    assert site.url == "https://example.com"
    assert len(site.pages) >= 1
    assert site.pages[0].title is not None

@pytest.mark.asyncio
async def test_element_type_detection():
    """Test détection des types d'éléments."""
    scraper = WebScraper()
    
    # Test button
    assert scraper._infer_element_type({"tag": "button"}) == ElementType.BUTTON
    
    # Test link
    assert scraper._infer_element_type({"tag": "a", "attributes": {}}) == ElementType.LINK
    
    # Test button-like link
    assert scraper._infer_element_type({
        "tag": "a", 
        "attributes": {"role": "button"}
    }) == ElementType.BUTTON

@pytest.mark.asyncio
async def test_service_parse_and_save():
    """Test parsing et sauvegarde."""
    service = ParserService(output_dir="./test_output")
    site, filepath = await service.parse_and_save("https://example.com")
    
    assert filepath.exists()
    assert site.metadata.title is not None
```

---

## LIVRABLES

```
backend/app/parser/
├── __init__.py
├── models.py
├── scraper.py
├── html_parser.py
├── css_parser.py
├── js_parser.py
├── asset_extractor.py
├── service.py
└── utils.py

tests/
└── test_parser.py
```

## CRITÈRES DE VALIDATION

- [ ] Scrape une URL et retourne ParsedSite
- [ ] Extrait l'arbre DOM avec tous les éléments
- [ ] Extrait les styles computed de chaque élément
- [ ] Détecte le framework (React, Vue, etc.)
- [ ] Extrait les liens internes
- [ ] Extrait la palette de couleurs
- [ ] Extrait les fonts utilisées
- [ ] Sauvegarde en JSON
- [ ] Tests passent

## TEMPS ESTIMÉ
3 heures
