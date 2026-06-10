from flask import Flask, render_template, request, jsonify
import requests
import re
import os
from collections import Counter
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)

# ─────────────────────────────────────────────
#  STOPWORDS FR
# ─────────────────────────────────────────────
STOPWORDS = {
    'le','la','les','un','une','des','de','du','en','et','ou','mais','donc',
    'or','ni','car','que','qui','quoi','dont','où','je','tu','il','elle',
    'nous','vous','ils','elles','me','te','se','lui','leur','y','ce','cet',
    'cette','ces','mon','ton','son','ma','ta','sa','nos','vos','leurs','au',
    'aux','pour','par','sur','sous','dans','avec','sans','entre','vers','chez',
    'dès','depuis','avant','après','pendant','lors','si','pas','plus','moins',
    'très','trop','peu','bien','mal','aussi','comme','quand','est','sont',
    'être','avoir','faire','tout','tous','toute','toutes','autre','autres',
    'même','mêmes','on','a','à','ça','cela','votre','notre','ne','n','s',
    'd','l','j','m','c','qu','its','the','and','for','are','this','with',
    'that','from','your','our','all','has','was','but','not','have','been',
    'they','will','can','get','how','what','when','which','more','use',
    'find','best','top','make','need','want','know','than','also','any',
    'out','new','one','two','see','may','its','their','here','do','so',
}

# ─────────────────────────────────────────────
#  MOTS INTERDITS
# ─────────────────────────────────────────────
FORBIDDEN = [
    'boostez', 'découvrez', 'essayez', 'profitez', 'cliquez', 'obtenez',
    'ne manquez pas', 'offre exclusive', 'meilleur prix', 'incroyable',
    'révolutionnaire', 'fantastique', 'exceptionnel',
]

# ─────────────────────────────────────────────
#  ANGLES SERP
# ─────────────────────────────────────────────
ANGLE_SIGNALS = {
    'criteria':  ['éligible', 'éligibilité', 'conditions', 'critères', 'profil', 'cas', 'situation', 'qui'],
    'price':     ['prix', 'coût', 'tarif', 'gratuit', 'montant', 'aide', 'budget', 'euro', 'subvention'],
    'speed':     ['rapide', 'délai', 'jours', 'heures', 'immédiat', 'vite', 'durée', 'rapidement', 'disponible'],
    'process':   ['comment', 'étape', 'démarche', 'dossier', 'demande', 'procédure', 'guide', 'faire'],
    'trust':     ['certifié', 'garanti', 'agréé', 'professionnel', 'expert', 'reconnu', 'qualifié', 'fiable'],
}

ANGLE_LABELS = {
    'criteria': '🎯 Angle critères',
    'price':    '💰 Angle prix',
    'speed':    '⚡ Angle rapidité',
    'process':  '📋 Angle démarches',
    'trust':    '🛡 Angle confiance',
}

# ─────────────────────────────────────────────
#  RECHERCHE SERPAPI
# ─────────────────────────────────────────────
def scrape_google(keyword: str) -> list[dict]:
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []

    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={"q": keyword, "api_key": api_key, "num": 10, "hl": "fr", "gl": "fr", "engine": "google"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        organic = data.get("organic_results", [])
    except Exception:
        return []

    results = []
    for r in organic:
        url    = r.get("link", "")
        domain = re.sub(r"https?://", "", url).split("/")[0]
        results.append({
            "title":       (r.get("title") or "")[:80],
            "url":         url[:120],
            "domain":      domain,
            "description": (r.get("snippet") or "")[:300],
        })

    return results

# ─────────────────────────────────────────────
#  EXTRACTION DE MOTS-CLÉS FRÉQUENTS
# ─────────────────────────────────────────────
def extract_keywords(texts: list[str], top_n: int = 30) -> list[str]:
    words = []
    for text in texts:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ]{3,}", text.lower())
        words.extend([w for w in tokens if w not in STOPWORDS])
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_n)]

# ─────────────────────────────────────────────
#  TRONCATURE INTELLIGENTE
# ─────────────────────────────────────────────
def smart_trim(text: str, min_len: int = 140, max_len: int = 160) -> str:
    if len(text) <= max_len:
        if len(text) < min_len:
            fillers = [
                " Comparez les solutions disponibles.",
                " Vérifiez les conditions applicables.",
                " Renseignez-vous auprès d'un professionnel.",
                " Consultez les offres en vigueur.",
                " Regardez les options selon votre situation.",
                " Prenez le temps de comparer avant de choisir.",
            ]
            for f in fillers:
                candidate = text + f
                if min_len <= len(candidate) <= max_len:
                    return candidate
            text = text.rstrip(".")
            text = (text + " Vérifiez les conditions applicables.")[:max_len]
        return text

    trimmed = text[:max_len].rsplit(" ", 1)[0].rstrip(".,!?;:")
    return trimmed + "."

# ─────────────────────────────────────────────
#  CONSTRUCTION DU TEXTE PAR ANGLE
# ─────────────────────────────────────────────
def build_angle_text(angle: str, kw: str, kw_cap: str, w1: str, w2: str) -> str:
    w1l = w1.lower()
    w2l = w2.lower()
    w1c = w1l.capitalize()

    variants = {
        'criteria': [
            f"{kw_cap} : pour qui et dans quelles situations ? {w1c} et {w2l} sont les éléments clés à vérifier pour savoir si cette option correspond à votre cas.",
            f"{kw_cap}, selon votre {w1l} et votre {w2l}. Vérifiez que cette solution est adaptée à votre profil avant de vous engager dans une démarche.",
        ],
        'price': [
            f"{kw_cap} : quel budget prévoir selon votre projet ? {w1c} et {w2l} influencent directement le coût final de votre prestation ou prise en charge.",
            f"{kw_cap} : le tarif varie selon le {w1l} et le {w2l} du demandeur. Comparez les offres du marché pour choisir la solution adaptée à vos moyens.",
        ],
        'speed': [
            f"{kw_cap} : quels délais pour votre projet ? {w1c}, {w2l} et disponibilité des intervenants sont les facteurs à anticiper pour une bonne planification.",
            f"{kw_cap} avec une réponse dans les meilleurs délais : {w1l} et {w2l} traités en priorité pour avancer sans attente inutile selon votre situation.",
        ],
        'process': [
            f"{kw_cap} : comment ça marche, étape par étape ? {w1c}, {w2l} et points de vigilance à connaître avant de faire appel à un intervenant qualifié.",
            f"{kw_cap} en pratique : {w1l}, {w2l} et questions à anticiper avant de vous lancer. Un aperçu complet pour avancer sereinement dans votre démarche.",
        ],
        'trust': [
            f"{kw_cap} avec des professionnels qualifiés : {w1l} et {w2l} vérifiés, expérience reconnue et interventions garanties pour un résultat à la hauteur.",
            f"Choisir le bon prestataire pour {kw} : {w1l}, {w2l} et références à contrôler pour un travail fiable, dans les règles de l'art et sans mauvaises surprises.",
        ],
    }

    options = variants.get(angle, variants['process'])
    # Prefer the variant closest to the ideal length range
    for lo, hi in [(130, 170), (110, 185), (0, 9999)]:
        for t in options:
            if lo <= len(t) <= hi:
                return t
    return options[0]

# ─────────────────────────────────────────────
#  SCORE /100
# ─────────────────────────────────────────────
def score_proposal(text: str, keyword: str, semantic_kws: list[str]) -> int:
    score = 0
    kw_lower   = keyword.lower()
    text_lower = text.lower()

    # 1. Présence du mot-clé (25 pts)
    if text_lower.startswith(kw_lower):
        score += 25
    elif kw_lower in text_lower:
        score += 15

    # 2. Longueur optimale (30 pts)
    length = len(text)
    if 140 <= length <= 160:
        score += 30
    elif 130 <= length < 140 or 160 < length <= 170:
        score += 18
    elif 120 <= length < 130 or 170 < length <= 180:
        score += 8

    # 3. Absence de mots interdits (20 pts)
    forbidden_hits = sum(1 for f in FORBIDDEN if f in text_lower)
    score += max(0, 20 - forbidden_hits * 7)

    # 4. Richesse sémantique vs concurrents (15 pts)
    sem_hits = sum(1 for w in semantic_kws[:20] if w in text_lower)
    score += min(15, sem_hits * 3)

    # 5. Naturel de la phrase (10 pts)
    if '—' not in text and ' - ' not in text:
        score += 5
    if not re.search(r',\s+[A-Z]', text):
        score += 5

    return min(100, score)

# ─────────────────────────────────────────────
#  GÉNÉRATION DES 5 PROPOSITIONS
# ─────────────────────────────────────────────
def generate_proposals(keyword: str, results: list[dict]) -> list[dict]:
    kw     = keyword.strip()
    kw_cap = kw.capitalize()

    # Analyse sémantique profonde du SERP
    all_text   = ' '.join(
        (r.get('title', '') + ' ' + r.get('description', ''))
        for r in results
    ).lower()
    all_descs  = [r['description'] for r in results if r['description']]
    all_titles = [r['title'] for r in results if r['title']]
    semantic_kws = extract_keywords(all_descs + all_titles, top_n=30)

    # Retirer les mots du mot-clé principal
    kw_words = set(kw.lower().split())
    semantic_kws = [w for w in semantic_kws if w not in kw_words]

    # Détecter la force de chaque angle dans le SERP
    angle_relevance = {
        angle: sum(1 for s in signals if s in all_text)
        for angle, signals in ANGLE_SIGNALS.items()
    }

    # Attribuer 2 mots-clés sémantiques distincts à chaque angle
    used_kws = set(kw_words)
    angle_kws: dict[str, tuple[str, str]] = {}

    for angle in ['criteria', 'price', 'speed', 'process', 'trust']:
        # Préférer les mots proches thématiquement de l'angle
        angle_signals = ANGLE_SIGNALS.get(angle, [])
        preferred = [
            w for w in semantic_kws
            if any(s[:5] in w for s in angle_signals) and w not in used_kws
        ]
        fallback = [w for w in semantic_kws if w not in used_kws and w not in preferred]
        pool = preferred + fallback

        w1 = pool[0] if len(pool) > 0 else (semantic_kws[0] if semantic_kws else "service")
        w2 = pool[1] if len(pool) > 1 else (semantic_kws[1] if len(semantic_kws) > 1 else "résultat")
        used_kws.add(w1)
        used_kws.add(w2)
        angle_kws[angle] = (w1, w2)

    # Construire, scorer et trier
    final = []
    for angle in ['criteria', 'price', 'speed', 'process', 'trust']:
        w1, w2 = angle_kws[angle]
        raw_text = build_angle_text(angle, kw, kw_cap, w1, w2)
        text     = smart_trim(raw_text)
        length   = len(text)
        sc       = score_proposal(text, kw, semantic_kws)
        final.append({
            "format": ANGLE_LABELS[angle],
            "text":   text,
            "length": length,
            "status": "ok" if 140 <= length <= 160 else "warning",
            "score":  sc,
        })

    final.sort(key=lambda x: x['score'], reverse=True)
    return final

# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data    = request.get_json(silent=True) or {}
    keyword = data.get("keyword", "").strip()

    if not keyword or len(keyword) < 2:
        return jsonify({"error": "Veuillez entrer un mot-clé valide (min. 2 caractères)."}), 400

    results = scrape_google(keyword)

    if not results:
        return jsonify({
            "error": "Aucun résultat trouvé. Vérifiez votre mot-clé et réessayez."
        }), 503

    proposals = generate_proposals(keyword, results)

    return jsonify({
        "keyword":   keyword,
        "results":   results,
        "proposals": proposals,
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
