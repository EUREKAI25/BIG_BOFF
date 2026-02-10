"""
DOM MANIFEST - Extracteur de sites web
======================================
Une seule fonction: get_dom_details(url) -> dict

Installation:
    pip install playwright
    playwright install chromium
"""

import asyncio
import base64
import hashlib
import json
import mimetypes
import re
from collections import OrderedDict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

def _ensure_playwright():
    """Installe Playwright automatiquement si nécessaire"""
    try:
        from playwright.async_api import async_playwright
        return True
    except ImportError:
        print("📦 Installation de Playwright...")
        import subprocess
        subprocess.run(['pip3', 'install', 'playwright'], check=True)
        
        print("📦 Installation de Chromium...")
        subprocess.run(['playwright', 'install', 'chromium'], check=True)
        
        print("✅ Installation terminée\n")
        return True

PLAYWRIGHT_OK = _ensure_playwright()
from playwright.async_api import async_playwright


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def get_dom_details(url: str, viewport: tuple = (1920, 1080)) -> dict:
    """
    Extrait tous les détails d'une page web.
    
    Args:
        url: URL de la page à extraire
        viewport: (largeur, hauteur) du viewport
    
    Returns:
        {
            'manifest': { source, extractedAt, viewport },
            'fractaldom': { DOM fractal *List },
            'style': {
                'executed': str (CSS actif),
                'computed': dict (styles par sélecteur),
                'files': [{ url, size, data }]
            },
            'js': {
                'files': [{ url, size, data }]
            },
            'media': {
                'images': [{ url, type, size, data }],
                'videos': [{ url, type, size, data }],
                'audio': [{ url, type, size, data }],
                'fonts': [{ url, type, size, data }]
            },
            'errors': []
        }
    """
    raw = asyncio.run(_extract(url, viewport))
    
    # Réorganiser en structure claire
    result = {
        'manifest': raw['manifest'],
        'fractaldom': raw['template'],
        'style': {
            'executed': raw['css'].get('executed', ''),
            'computed': raw['css'].get('computed', {}),
            'files': []
        },
        'js': {
            'files': []
        },
        'media': {
            'images': [],
            'videos': [],
            'audio': [],
            'fonts': []
        },
        'errors': raw['errors']
    }
    
    # Trier les assets par catégorie
    for h, asset in raw.get('assets', {}).items():
        item = {
            'hash': h,
            'url': asset['url'],
            'type': asset['type'],
            'size': asset['size'],
            'data': asset['data']
        }
        
        cat = asset['category']
        if cat == 'styles':
            result['style']['files'].append(item)
        elif cat == 'scripts':
            result['js']['files'].append(item)
        elif cat == 'images':
            result['media']['images'].append(item)
        elif cat == 'media':
            # Distinguer video et audio
            if 'video' in asset['type']:
                result['media']['videos'].append(item)
            elif 'audio' in asset['type']:
                result['media']['audio'].append(item)
        elif cat == 'fonts':
            result['media']['fonts'].append(item)
    
    return result


async def _extract(url: str, viewport: tuple) -> dict:
    """Extraction async"""
    
    result = {
        'manifest': {
            'source': url,
            'extractedAt': datetime.now(timezone.utc).isoformat(),
            'viewport': f"{viewport[0]}x{viewport[1]}"
        },
        'template': {},
        'css': {},
        'assets': {},
        'errors': []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': viewport[0], 'height': viewport[1]},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Capturer les ressources
        resources = []
        page.on('response', lambda r: resources.append(r))
        
        # Charger
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)
        except Exception as e:
            result['errors'].append({'type': 'load', 'error': str(e)})
        
        # Extraire CSS
        result['css'] = await _extract_css(page)
        
        # Capturer assets
        result['assets'] = await _capture_assets(resources, result['errors'])
        
        # HTML rendu -> template
        html = await page.content()
        result['template'] = _parse_html(html)
        
        await browser.close()
    
    return result


async def _extract_css(page) -> dict:
    """Extrait le CSS exécuté"""
    
    css = {'executed': '', 'all': '', 'computed': {}}
    
    # Tout le CSS (toutes les règles actives)
    css['all'] = await page.evaluate('''() => {
        const rules = [];
        for (const sheet of document.styleSheets) {
            try { for (const rule of sheet.cssRules) rules.push(rule.cssText); } catch(e) {}
        }
        return rules.join('\\n');
    }''')
    
    css['executed'] = css['all']  # Même chose, c'est le CSS chargé et actif
    
    # Styles computés
    css['computed'] = await page.evaluate('''() => {
        const result = {};
        const props = ['display','position','width','height','margin','padding',
            'background','background-color','color','font-family','font-size',
            'border','border-radius','flex','grid','transform','opacity'];
        document.querySelectorAll('[id],[class]').forEach(el => {
            let sel = el.id ? '#'+el.id : 
                (el.className && typeof el.className==='string' && el.className.trim()) ? 
                '.'+el.className.trim().split(/\\s+/).join('.') : null;
            if (!sel || result[sel]) return;
            const cs = getComputedStyle(el), styles = {};
            props.forEach(p => { const v = cs.getPropertyValue(p); if (v && v!=='none' && v!=='auto') styles[p] = v; });
            if (Object.keys(styles).length) result[sel] = styles;
        });
        return result;
    }''')
    
    return css


async def _capture_assets(responses: list, errors: list) -> dict:
    """Capture tous les assets"""
    
    assets = {}
    
    for resp in responses:
        try:
            url = resp.url
            if url.startswith('data:'):
                continue
            
            ct = resp.headers.get('content-type', '').split(';')[0].lower()
            
            # Filtrer les types utiles
            if not any(t in ct for t in ['css', 'javascript', 'image', 'font', 'video', 'audio']):
                continue
            
            try:
                body = await resp.body()
            except:
                continue
            
            h = hashlib.sha256(body).hexdigest()
            
            if h not in assets:
                cat = 'other'
                if 'css' in ct: cat = 'styles'
                elif 'javascript' in ct: cat = 'scripts'
                elif ct.startswith('image/'): cat = 'images'
                elif 'font' in ct: cat = 'fonts'
                elif ct.startswith(('video/', 'audio/')): cat = 'media'
                
                assets[h] = {
                    'url': url,
                    'type': ct,
                    'category': cat,
                    'size': len(body),
                    'data': base64.b64encode(body).decode()
                }
        except Exception as e:
            errors.append({'type': 'asset', 'url': getattr(resp, 'url', '?'), 'error': str(e)})
    
    return assets


# =============================================================================
# PARSER HTML -> TEMPLATE FRACTAL
# =============================================================================

VOID_ELEMENTS = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

def _parse_html(html: str) -> dict:
    parser = _HTMLParser(html)
    parser.feed(html)
    return parser.root


class _HTMLParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.root = OrderedDict()
        self.stack = [self.root]
        self.order_stack = [[]]
    
    def handle_decl(self, decl):
        self.root['doctypeList'] = [decl]
    
    def handle_starttag(self, tag, attrs):
        elem = OrderedDict()
        elem['tagList'] = [tag]
        
        ad = OrderedDict()
        for n, v in attrs:
            k = f"{n}List"
            if n == 'class' and v:
                ad[k] = v.split()
            else:
                ad[k] = [v] if v is not None else [True]
        elem['attrsList'] = [ad]
        elem['rawAttrStrList'] = [self._raw_attrs(tag)]
        
        parent = self.stack[-1]
        key = f"{tag}List"
        if key not in parent:
            parent[key] = []
        idx = len(parent[key])
        parent[key].append(elem)
        self.order_stack[-1].append((tag, idx))
        
        if tag.lower() not in VOID_ELEMENTS:
            children = OrderedDict()
            elem['childrenList'] = [children]
            self.stack.append(children)
            self.order_stack.append([])
    
    def _raw_attrs(self, tag):
        pos = self.getpos()
        lines = self.source.split('\n')
        text = '\n'.join(lines[pos[0]-1:pos[0]+3])[pos[1]:]
        m = re.match(r'<[a-zA-Z0-9]+\s*([^>]*)/?>', text, re.DOTALL)
        return m.group(1).strip() if m else ''
    
    def handle_endtag(self, tag):
        if tag.lower() not in VOID_ELEMENTS and len(self.stack) > 1:
            self.stack[-1]['orderList'] = self.order_stack[-1]
            self.stack.pop()
            self.order_stack.pop()
    
    def handle_data(self, data):
        p = self.stack[-1]
        if 'textList' not in p: p['textList'] = []
        idx = len(p['textList'])
        p['textList'].append(data)
        self.order_stack[-1].append(('#text', idx))
    
    def handle_comment(self, data):
        p = self.stack[-1]
        if 'commentList' not in p: p['commentList'] = []
        idx = len(p['commentList'])
        p['commentList'].append(data)
        self.order_stack[-1].append(('#comment', idx))
    
    def handle_entityref(self, name):
        self.handle_data(f"&{name};")
    
    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


# =============================================================================
# UTILITAIRES
# =============================================================================

def export_all(data: dict, output_dir: str):
    """
    Exporte tout vers un dossier structuré:
        output_dir/
            index.html          (HTML reconstruit)
            fractaldom.json     (DOM fractal)
            style/
                executed.css
                fichiers CSS...
            js/
                fichiers JS...
            media/
                images/
                videos/
                audio/
                fonts/
    """
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)
    
    # 1. fractaldom.json
    with open(base / 'fractaldom.json', 'w', encoding='utf-8') as f:
        json.dump(data['fractaldom'], f, indent=2, ensure_ascii=False)
    
    # 2. HTML reconstruit
    html = rebuild_html(data)
    (base / 'index.html').write_text(html, encoding='utf-8')
    
    # 3. Style
    style_dir = base / 'style'
    style_dir.mkdir(exist_ok=True)
    
    # CSS exécuté
    if data['style']['executed']:
        (style_dir / 'executed.css').write_text(data['style']['executed'], encoding='utf-8')
    
    # Fichiers CSS
    for f in data['style']['files']:
        filename = _safe_filename(f['url'], f['hash'], '.css')
        (style_dir / filename).write_bytes(base64.b64decode(f['data']))
    
    # 4. JS
    js_dir = base / 'js'
    js_dir.mkdir(exist_ok=True)
    
    for f in data['js']['files']:
        filename = _safe_filename(f['url'], f['hash'], '.js')
        (js_dir / filename).write_bytes(base64.b64decode(f['data']))
    
    # 5. Media
    media_dir = base / 'media'
    
    for subcat in ['images', 'videos', 'audio', 'fonts']:
        sub_dir = media_dir / subcat
        sub_dir.mkdir(parents=True, exist_ok=True)
        
        for f in data['media'].get(subcat, []):
            ext = _get_ext(f['url'], f['type'])
            filename = _safe_filename(f['url'], f['hash'], ext)
            (sub_dir / filename).write_bytes(base64.b64decode(f['data']))
    
    print(f"✅ Exporté vers {output_dir}/")
    print(f"   - fractaldom.json")
    print(f"   - index.html")
    print(f"   - style/ ({len(data['style']['files'])} fichiers + executed.css)")
    print(f"   - js/ ({len(data['js']['files'])} fichiers)")
    print(f"   - media/images/ ({len(data['media']['images'])} fichiers)")
    print(f"   - media/videos/ ({len(data['media']['videos'])} fichiers)")
    print(f"   - media/audio/ ({len(data['media']['audio'])} fichiers)")
    print(f"   - media/fonts/ ({len(data['media']['fonts'])} fichiers)")


def _safe_filename(url: str, hash: str, default_ext: str) -> str:
    """Génère un nom de fichier safe depuis l'URL"""
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if name and '.' in name:
        return f"{hash[:8]}_{name}"
    return f"{hash[:16]}{default_ext}"


def _get_ext(url: str, content_type: str) -> str:
    """Détermine l'extension"""
    ext = Path(urlparse(url).path).suffix
    if ext:
        return ext
    
    type_map = {
        'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif',
        'image/webp': '.webp', 'image/svg+xml': '.svg', 'image/avif': '.avif',
        'video/mp4': '.mp4', 'video/webm': '.webm',
        'audio/mpeg': '.mp3', 'audio/wav': '.wav',
        'font/woff': '.woff', 'font/woff2': '.woff2', 'font/otf': '.otf', 'font/ttf': '.ttf'
    }
    return type_map.get(content_type, '')


def save_manifest(data: dict, filepath: str):
    """Sauvegarde le manifest en JSON"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_manifest(filepath: str) -> dict:
    """Charge un manifest JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def rebuild_html(data: dict) -> str:
    """Reconstruit le HTML depuis le fractaldom"""
    return _rebuild_node(data.get('fractaldom', {}))


def _rebuild_node(node: dict) -> str:
    parts = []
    
    if 'doctypeList' in node:
        parts.append(f"<!{node['doctypeList'][0]}>")
    
    order = node.get('orderList', [])
    
    if order:
        for item_type, idx in order:
            if item_type == '#text':
                texts = node.get('textList', [])
                if idx < len(texts): parts.append(texts[idx])
            elif item_type == '#comment':
                comments = node.get('commentList', [])
                if idx < len(comments): parts.append(f"<!--{comments[idx]}-->")
            else:
                key = f"{item_type}List"
                elems = node.get(key, [])
                if idx < len(elems): parts.append(_rebuild_elem(elems[idx]))
    else:
        for key, val in node.items():
            if key in ('orderList', 'doctypeList'): continue
            if key == 'textList': parts.extend(val)
            elif key == 'commentList': parts.extend(f"<!--{c}-->" for c in val)
            elif key.endswith('List') and isinstance(val, list):
                for e in val:
                    if isinstance(e, dict): parts.append(_rebuild_elem(e))
    
    return ''.join(parts)


def _rebuild_elem(elem: dict) -> str:
    tag = elem.get('tagList', ['div'])[0]
    attrs = elem.get('rawAttrStrList', [''])[0]
    
    if tag.lower() in VOID_ELEMENTS:
        return f"<{tag} {attrs}>" if attrs else f"<{tag}>"
    
    children = elem.get('childrenList', [{}])[0]
    inner = _rebuild_node(children)
    
    return f"<{tag} {attrs}>{inner}</{tag}>" if attrs else f"<{tag}>{inner}</{tag}>"


# =============================================================================
# MAIN DE TEST
# =============================================================================

if __name__ == '__main__':
    import sys
    import os
    
    # ============================================
    # CONFIGURATION - Modifier ce chemin si besoin
    # ============================================
    pathdirectory = "/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/_INPUTS/EURKAI/FINAL1211/converters/dom_extractor/outputs"
    # ============================================
    
    # URL par défaut ou passée en argument
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(pathdirectory, exist_ok=True)
    
    print(f"🌐 Extraction de {url}...")
    
    try:
        data = get_dom_details(url)
        
        print(f"\n✅ Extraction terminée")
        print(f"\n📁 Structure:")
        print(f"   fractaldom: {len(json.dumps(data['fractaldom'])):,} caractères")
        print(f"   style:")
        print(f"      - executed: {len(data['style']['executed']):,} caractères")
        print(f"      - computed: {len(data['style']['computed'])} sélecteurs")
        print(f"      - files: {len(data['style']['files'])} fichiers CSS")
        print(f"   js:")
        print(f"      - files: {len(data['js']['files'])} fichiers JS")
        print(f"   media:")
        print(f"      - images: {len(data['media']['images'])} fichiers")
        print(f"      - videos: {len(data['media']['videos'])} fichiers")
        print(f"      - audio: {len(data['media']['audio'])} fichiers")
        print(f"      - fonts: {len(data['media']['fonts'])} fichiers")
        
        if data['errors']:
            print(f"   ⚠️  Erreurs: {len(data['errors'])}")
        
        # Sauvegarder le manifest
        manifest_name = url.split('//')[-1].split('/')[0].replace('.', '_') + '_manifest.json'
        manifest_path = os.path.join(pathdirectory, manifest_name)
        save_manifest(data, manifest_path)
        print(f"\n💾 Manifest sauvegardé:")
        print(f"   file://{manifest_path}")
        
        # Exporter si dossier spécifié ou par défaut
        if output_dir:
            export_path = os.path.join(pathdirectory, output_dir)
        else:
            export_name = url.split('//')[-1].split('/')[0].replace('.', '_') + '_export'
            export_path = os.path.join(pathdirectory, export_name)
        
        export_all(data, export_path)
        print(f"\n📂 Export complet:")
        print(f"   file://{export_path}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
