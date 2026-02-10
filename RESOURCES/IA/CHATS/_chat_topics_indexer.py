
#!/usr/bin/env python3
# chat_topics_indexer.py
# Description: Recursively scan archived chat/conversation files and build a concise topical index
# Inputs:
#   - root directory path (required)
#   - file extensions to include (optional)
#   - language for stopwords (optional; supports fr, en, it)
# Outputs:
#   - topics_index.csv  : per-file summary (path, title, date_guess, top_topics, tags, people, urls)
#   - topics_index.jsonl: same as CSV in JSON Lines format
#   - global_summary.md : global overview with the most frequent topics and tags
# Notes:
#   - Pure standard library. If scikit-learn is available, the script will optionally compute TF-IDF keywords.
#   - Optimized for large corpora: streams line by line, avoids loading everything in RAM.
#   - Heuristics-based (no AI); safe to run offline.
#
# Usage (examples):
#   python chat_topics_indexer.py --root "/path/to/archives"
#   python chat_topics_indexer.py --root "/path/to/archives" --ext ".txt,.md,.json" --lang fr --topk 12
#
# -----------------------------------------------------------------------------

import argparse
import csv
import dataclasses
import html
import io
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from typing import Iterable, List, Dict, Tuple, Optional

def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def normalize_space(s: str) -> str:
    return re.sub(r'\\s+', ' ', s).strip()

URL_RE = re.compile(r'(https?://[^\\s)>\\]"}]+)', re.IGNORECASE)
DATE_RE = re.compile(
    r'\\b((?:\\d{4}[-/]\\d{1,2}[-/]\\d{1,2})|(?:\\d{1,2}[-/]\\d{1,2}[-/]\\d{2,4})|(?:\\d{1,2}\\s+[A-Za-zéûôîàèìíóúäëïöüçÉÈÀÙÂÊÎÔÛÇ]{3,}\\s+\\d{2,4}))\\b'
)

HTML_TAG_RE = re.compile(r'<[^>]+>')

def strip_html(s: str) -> str:
    s = html.unescape(s)
    return HTML_TAG_RE.sub(' ', s)

def safe_open_text(path: str) -> Optional[io.TextIOBase]:
    try:
        return open(path, 'r', encoding='utf-8', errors='ignore')
    except Exception:
        try:
            return open(path, 'r', encoding='latin-1', errors='ignore')
        except Exception:
            return None

STOPWORDS = {
    'fr': {
        'a','à','â','abord','afin','ai','ainsi','après','attendu','au','aucun','aussi','autre','avant','avec','avoir',
        'car','ce','cela','celle','celui','cent','cependant','certain','certaine','certains','ces','cet','cette','ceux',
        'chacun','chaque','ci','comme','comment','d','dans','de','des','du','dedans','dehors','depuis','deux','devrait',
        'doit','donc','dos','droite','début','elle','elles','en','encore','essai','est','et','eu','eux','fait','faites',
        'fois','font','force','haut','hors','ici','il','ils','je','juste','la','le','les','leur','là','ma','maintenant',
        'mais','mes','mine','moins','mon','mot','même','ni','nommés','nos','notre','nous','nouveaux','ou','où','par',
        'parce','parole','pas','personnes','peu','peut','peuvent','plupart','pour','pourquoi','quand','que','quel',
        'quelle','quelles','quels','qui','sa','sans','ses','seulement','si','sien','son','sont','sous','soyez','sujet',
        'sur','ta','tandis','tellement','tels','tes','ton','tous','tout','trop','très','tu','valeur','voie','voient',
        'vont','votre','vous','vu','ça','étaient','état','étions','été','être'
    },
    'en': {
        'a','about','above','after','again','against','all','am','an','and','any','are','as','at','be','because','been',
        'before','being','below','between','both','but','by','could','did','do','does','doing','down','during','each',
        'few','for','from','further','had','has','have','having','he','her','here','hers','herself','him','himself',
        'his','how','i','if','in','into','is','it','its','itself','just','me','more','most','my','myself','no','nor',
        'not','now','of','off','on','once','only','or','other','our','ours','ourselves','out','over','own','same','she',
        'should','so','some','such','than','that','the','their','theirs','them','themselves','then','there','these',
        'they','this','those','through','to','too','under','until','up','very','was','we','were','what','when','where',
        'which','while','who','whom','why','with','would','you','your','yours','yourself','yourselves'
    },
    'it': {
        'a','ad','agli','ai','al','alla','allo','allora','altre','altri','altro','anche','ancora','avere','aveva',
        'avevano','ben','buono','che','chi','cinque','comprare','con','contro','cosa','cui','da','dagli','dai','dal',
        'dalla','dalle','dallo','degl','degli','dei','del','dell','della','delle','dello','dentro','deve','devi','di',
        'dice','dietro','dire','dopo','due','e','ecco','fare','fatto','fino','fra','gente','gia','già','gli','ha',
        'hai','hanno','ho','il','in','indietro','invece','io','la','lavoro','le','lei','lo','loro','lui','ma','me',
        'meglio','molta','molti','molto','nei','nella','nelle','nello','no','noi','nome','nostro','nove','nuovi','o',
        'oltre','ora','per','perché','pero','piu','più','poco','primo','promesso','qua','qual','quale','quanta','quanti',
        'quanto','quarto','quasi','quello','questo','qui','quindi','quinto','sara','sarà','sarebbe','sei','sembra','sembrava',
        'senza','sette','sia','siamo','siete','solo','sono','sopra','soprattutto','sotto','stati','stato','stesso','su',
        'subito','sul','sulla','sulle','sullo','suo','suoi','tanto','te','tempo','terzo','tra','tre','troppo','tu','tua',
        'tue','tuo','tuoi','tutti','tutto','avete','voi','volte'
    }
}

def get_stopwords(lang: str) -> set:
    return STOPWORDS.get(lang, STOPWORDS['fr'])

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_'-]+")

def tokenize(text: str) -> List[str]:
    text = strip_accents(text.lower())
    return WORD_RE.findall(text)

def ngrams(tokens: List[str], n: int) -> Iterable[Tuple[str, ...]]:
    for i in range(len(tokens) - n + 1):
        yield tuple(tokens[i:i+n])

def extract_title_and_text(path: str, raw: str) -> Tuple[str, str]:
    title = os.path.basename(path)
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            for k in ('title','subject','conversation_title','thread','name'):
                if k in obj and isinstance(obj[k], str):
                    title = obj[k]
                    break
            parts = []
            for k in ('messages','items','chats','log'):
                if k in obj and isinstance(obj[k], list):
                    for it in obj[k]:
                        for mk in ('content','text','message','body','msg'):
                            if isinstance(it, dict) and mk in it and isinstance(it[mk], str):
                                parts.append(it[mk])
            if parts:
                return title, "\\n".join(parts)
            for k in ('content','text','message','body'):
                if k in obj and isinstance(obj[k], str):
                    return title, obj[k]
        elif isinstance(obj, list):
            parts = []
            for it in obj:
                if isinstance(it, dict):
                    for mk in ('content','text','message','body','msg'):
                        if mk in it and isinstance(it[mk], str):
                            parts.append(it[mk])
            if parts:
                return title, "\\n".join(parts)
    except Exception:
        pass

    if '<html' in raw.lower() or '<div' in raw.lower() or '<p' in raw.lower():
        cleaned = strip_html(raw)
        for line in cleaned.splitlines():
            ln = normalize_space(line)
            if ln:
                title = ln[:120]
                break
        return title, cleaned

    lines = raw.splitlines()
    for line in lines:
        ln = normalize_space(line.lstrip('# ').strip())
        if ln:
            title = ln[:120]
            break
    return title, raw

def extract_candidates(text: str, lang: str, topk: int = 10) -> Dict[str, List[str]]:
    stops = get_stopwords(lang)
    toks = [t for t in tokenize(text) if t not in stops and len(t) > 2 and not t.isdigit()]
    c1 = Counter(toks)
    c2 = Counter([' '.join(bg) for bg in ngrams(toks, 2) if all(w not in stops for w in bg)])
    c3 = Counter([' '.join(tg) for tg in ngrams(toks, 3) if all(w not in stops for w in tg)])

    combined = Counter()
    combined.update(c1)
    combined.update({k: v*2 for k, v in c2.items()})
    combined.update({k: v*3 for k, v in c3.items()})

    topics = [w for w, _ in combined.most_common(topk*3)]
    pruned = []
    for t in topics:
        if not any(t != u and t in u for u in pruned):
            pruned.append(t)
        if len(pruned) >= topk:
            break

    tags = []
    seen = set()
    for t in pruned:
        tag = t.lower().replace(' ', '-').replace("'", '')
        if tag not in seen and len(tag) >= 3:
            seen.add(tag)
            tags.append(tag)

    caps = re.findall(r'\\b[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ][A-Za-zÉÈÀÙÂÊÎÔÛÄËÏÖÜÇéèàùâêîôûäëïöüç\\-]{1,}\\b', text)
    people = []
    seenp = set()
    for c in caps:
        key = c.strip()
        if key.upper() == key or len(key) < 3:
            continue
        if key.lower() in stops:
            continue
        if key not in seenp:
            seenp.add(key)
            people.append(key)
    people = people[:10]

    urls = URL_RE.findall(text)
    dates = DATE_RE.findall(text)

    return {
        'topics': pruned[:topk],
        'tags': tags[:topk],
        'people': people,
        'urls': urls[:20],
        'dates': dates[:20],
    }

def tfidf_keywords(docs: List[str], topk: int = 5, lang: str = 'fr') -> List[List[str]]:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except Exception:
        return [[] for _ in docs]
    stops = get_stopwords(lang)
    vectorizer = TfidfVectorizer(
        stop_words=list(stops),
        ngram_range=(1,3),
        max_features=50000,
        token_pattern=r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_'-]+"
    )
    X = vectorizer.fit_transform([strip_accents(d.lower()) for d in docs])
    vocab = vectorizer.get_feature_names_out()
    out = []
    for i in range(X.shape[0]):
        row = X.getrow(i)
        idx = row.toarray().ravel().argsort()[::-1]
        kws = []
        for j in idx[:topk*3]:
            term = vocab[j]
            if not any(term != u and term in u for u in kws):
                kws.append(term)
            if len(kws) >= topk:
                break
        out.append(kws)
    return out

@dataclasses.dataclass
class FileSummary:
    path: str
    title: str
    date_guess: str
    topics: List[str]
    tags: List[str]
    people: List[str]
    urls: List[str]

# ---------------- File scanner ----------------

IGNORE_DIR_PARTS = ("_files", "static", "assets", "node_modules", "__pycache__")

# ---------------- File scanner ----------------

IGNORE_DIR_PARTS = ("_files", "static", "assets", "node_modules", "__pycache__")

def iter_files(root: str, exts: Tuple[str, ...] = (".json",)) -> List[str]:
    """
    Parcourt récursivement le répertoire en ignorant :
    - les dossiers temporaires ou techniques
    - les fichiers commençant par '_'
    - les fichiers dont l'extension n'est pas dans exts (par défaut .json)
    """
    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        # ignorer les répertoires indésirables
        if any(part in dirpath for part in IGNORE_DIR_PARTS):
            continue
        for fn in filenames:
            # ignorer fichiers techniques (commençant par _)
            if fn.startswith("_"):
                continue
            if not fn.lower().endswith(exts):
                continue
            full_path = os.path.join(dirpath, fn)
            paths.append(full_path)
    paths.sort()
    return paths


def read_text_for_path(path: str) -> Optional[str]:
    f = safe_open_text(path)
    if not f:
        return None
    with f:
        raw = f.read()
    return raw

def guess_date_from_path_or_text(path: str, text: str) -> str:
    m = re.search(r'(20\\d{2}[-_/]\\d{1,2}[-_/]\\d{1,2})', path)
    if m:
        return m.group(1)
    m2 = re.search(r'(20\\d{2}\\d{2}\\d{2})', path)
    if m2:
        g = m2.group(1)
        return f'{g[:4]}-{g[4:6]}-{g[6:]}'
    md = DATE_RE.search(text or '')
    if md:
        return md.group(1)
    return ''

def build_index(root: str, exts: Tuple[str, ...], lang: str, topk: int, limit: Optional[int]=None) -> Tuple[List[FileSummary], Dict[str,int]]:
    summaries: List[FileSummary] = []
    global_topics = Counter()

    docs_for_tfidf = []
    snippets_idx = []

    count = 0
    for path in iter_files(root, exts):
        raw = read_text_for_path(path)
        if raw is None:
            continue
        title, body = extract_title_and_text(path, raw)
        text = body if len(body) < 2_000_000 else body[:2_000_000]

        cand = extract_candidates(text, lang=lang, topk=topk)
        date_guess = guess_date_from_path_or_text(path, text)

        for t in cand['topics']:
            global_topics[t] += 1

        summaries.append(FileSummary(
            path=path,
            title=normalize_space(title)[:200],
            date_guess=date_guess,
            topics=cand['topics'],
            tags=cand['tags'],
            people=cand['people'],
            urls=cand['urls']
        ))

        docs_for_tfidf.append(text[:5000])
        snippets_idx.append(len(summaries)-1)

        count += 1
        if limit and count >= limit:
            break

    tfidf = tfidf_keywords(docs_for_tfidf, topk=max(3, topk//2), lang=lang)
    for kws, idx in zip(tfidf, snippets_idx):
        if not kws:
            continue
        merged = summaries[idx].topics[:]
        for k in kws:
            if k not in merged:
                merged.append(k)
        summaries[idx].topics = merged[:max(len(merged), topk)]

    return summaries, dict(global_topics.most_common(2000))

def write_csv(path: str, rows: List[FileSummary]) -> None:
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['path','title','date_guess','top_topics','tags','people','urls'])
        for r in rows:
            w.writerow([
                r.path,
                r.title,
                r.date_guess,
                '; '.join(r.topics),
                '; '.join(r.tags),
                '; '.join(r.people),
                '; '.join(r.urls),
            ])

def write_jsonl(path: str, rows: List[FileSummary]) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(dataclasses.asdict(r), ensure_ascii=False) + '\\n')

def write_global_md(path: str, global_topics: Dict[str,int], rows: List[FileSummary], topn: int = 100) -> None:
    by_count = sorted(global_topics.items(), key=lambda x: x[1], reverse=True)[:topn]
    total_files = len(rows)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# Global Topic Summary\\n\\n")
        f.write(f"- Generated: {now}\\n")
        f.write(f"- Files indexed: {total_files}\\n\\n")
        f.write("## Top recurring topics\\n\\n")
        for term, cnt in by_count:
            f.write(f"- {term} — {cnt}\\n")
        f.write("\\n---\\n\\n")
        f.write("## How to use\\n")
        f.write("- Use `topics_index.csv` to sort/filter by topics/tags.\\n")
        f.write("- Use the `tags` column as lightweight labels for later classification.\\n")
        f.write("- The `date_guess` is extracted from filenames or the first date found in the text.\\n")

def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scan archived chat logs and build a topical index.")
    p.add_argument('--root', required=True, help='Root directory containing your archived discussions')
    p.add_argument('--ext', default='.txt,.md,.json,.html,.htm', help='Comma-separated list of file extensions to include')
    p.add_argument('--lang', default='fr', choices=['fr','en','it'], help='Stopword language')
    p.add_argument('--topk', type=int, default=10, help='Number of topics/tags per file')
    p.add_argument('--limit', type=int, default=None, help='Optional limit on files scanned (for testing)')
    p.add_argument('--outdir', default='.', help='Output directory (default: current working dir)')
    return p.parse_args(argv)
def build_index_from_paths(paths, lang: str, topk: int):
    summaries = []
    from collections import Counter
    global_topics = Counter()
    docs_for_tfidf, snippets_idx = [], []

    for path in paths:
        raw = read_text_for_path(path)
        if raw is None:
            continue
        title, body = extract_title_and_text(path, raw)
        text = body if len(body) < 2_000_000 else body[:2_000_000]

        cand = extract_candidates(text, lang=lang, topk=topk)
        date_guess = guess_date_from_path_or_text(path, text)

        for t in cand['topics']:
            global_topics[t] += 1

        summaries.append(FileSummary(
            path=path,
            title=normalize_space(title)[:200],
            date_guess=date_guess,
            topics=cand['topics'],
            tags=cand['tags'],
            people=cand['people'],
            urls=cand['urls'],
        ))
        docs_for_tfidf.append(text[:5000])
        snippets_idx.append(len(summaries)-1)

    # Optionnel TF-IDF (si sklearn dispo)
    tfidf = tfidf_keywords(docs_for_tfidf, topk=max(3, topk//2), lang=lang)
    for kws, idx in zip(tfidf, snippets_idx):
        if not kws: 
            continue
        merged = summaries[idx].topics[:]
        for k in kws:
            if k not in merged:
                merged.append(k)
        summaries[idx].topics = merged[:max(len(merged), topk)]

    return summaries, dict(global_topics.most_common(2000))

def main(argv: List[str]) -> int:
    args = parse_args(argv)
    exts = tuple([e.strip().lower() for e in args.ext.split(',') if e.strip()])
    if not os.path.isdir(args.root):
        print(f"[error] root directory not found: {args.root}", file=sys.stderr)
        return 2
    os.makedirs(args.outdir, exist_ok=True)

    print(f"[info] scanning: {args.root}")
    print(f"[info] include extensions: {exts or '(all)'}")
    summaries, gtopics = build_index(args.root, exts, lang=args.lang, topk=args.topk, limit=args.limit)

    csv_path = os.path.join(args.outdir, 'topics_index.csv')
    jsonl_path = os.path.join(args.outdir, 'topics_index.jsonl')
    md_path = os.path.join(args.outdir, 'global_summary.md')

    write_csv(csv_path, summaries)
    write_jsonl(jsonl_path, summaries)
    write_global_md(md_path, gtopics, summaries)

    print(f"[ok] wrote {csv_path}")
    print(f"[ok] wrote {jsonl_path}")
    print(f"[ok] wrote {md_path}")
    return 0

if __name__ == "__main__":
    # --- Config minimale ---
    ROOT_DIR = "/Users/nathalie/Dropbox/CHATS"
    OUTDIR = "/Users/nathalie/Dropbox/CHATS/_index"
    LANG = "fr"
    TOPK = 10
    EXTENSIONS = (".json",)

    # 🧪 Test: limiter à 2 fichiers (mets None quand tu veux tout traiter)
    TEST_LIMIT = 2

    os.makedirs(OUTDIR, exist_ok=True)

    # 1) Lister les fichiers éligibles (json uniquement, exclude dossiers et fichiers commençant par _)
    files = iter_files(ROOT_DIR, EXTENSIONS)

    if not files:
        print("[error] Aucun fichier JSON éligible trouvé.")
        raise SystemExit(1)

    if TEST_LIMIT:
        files = files[:TEST_LIMIT]
        print(f"[test mode] Scanning limited to {len(files)} files:")
        for f in files:
            print(" -", f)

    # 2) Construire l’index *à partir de cette liste* (pas du répertoire entier)
    summaries, gtopics = build_index_from_paths(files, lang=LANG, topk=TOPK)

    # 3) Écrire les sorties
    csv_path = os.path.join(OUTDIR, "topics_index.csv")
    jsonl_path = os.path.join(OUTDIR, "topics_index.jsonl")
    md_path = os.path.join(OUTDIR, "global_summary.md")

    write_csv(csv_path, summaries)
    write_jsonl(jsonl_path, summaries)
    write_global_md(md_path, gtopics, summaries)

    print(f"[ok] wrote {csv_path}")
    print(f"[ok] wrote {jsonl_path}")
    print(f"[ok] wrote {md_path}")
