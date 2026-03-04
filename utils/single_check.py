import re
from collections import defaultdict

STOPWORDS = {
    'the','a','an','and','or','but','in','on','at','to','for','of','with',
    'is','are','was','were','be','been','being','have','has','had','do','does',
    'did','will','would','could','should','may','might','shall','can','this',
    'that','these','those','it','its','i','you','he','she','we','they','me',
    'him','her','us','them','my','your','his','our','their','by','from','as',
    'into','through','during','about','above','below','between','each','more',
    'also','than','then','so','if','not','no','up','out','there','here','when',
    'where','who','which','what','how','all','both','any','some','such','own',
    'just','very','too','only','even','well','back','still','way','get','go',
    'know','think','say','make','see','come','take','want','use','find','give'
}

def tokenize_with_positions(text):
    tokens = []
    for m in re.finditer(r'\b[a-zA-Z]{3,}\b', text):
        tokens.append({
            'word': m.group().lower(),
            'original': m.group(),
            'start': m.start(),
            'end': m.end()
        })
    return tokens

def get_sentences_with_positions(text):
    sentences = []
    for m in re.finditer(r'[^.!?\n]+[.!?\n]?', text):
        s = m.group().strip()
        if len(s.split()) >= 5:
            sentences.append({'text': s, 'start': m.start(), 'end': m.end()})
    return sentences

def get_ngrams_with_positions(tokens, n=4):
    ngrams = []
    for i in range(len(tokens) - n + 1):
        words = tokens[i:i+n]
        content_words = [w for w in words if w['word'] not in STOPWORDS]
        if len(content_words) >= 2:
            phrase = ' '.join(t['word'] for t in words)
            ngrams.append({
                'phrase': phrase,
                'indices': list(range(i, i+n)),
                'start': words[0]['start'],
                'end': words[-1]['end']
            })
    return ngrams

def analyze_single_document(text):
    tokens = tokenize_with_positions(text)
    sentences = get_sentences_with_positions(text)

    # ── 1. Find repeated n-grams (4-word phrases) ──
    ngrams = get_ngrams_with_positions(tokens, 4)
    phrase_map = defaultdict(list)
    for ng in ngrams:
        phrase_map[ng['phrase']].append(ng['indices'])

    # Repeated = appears more than once
    repeated_phrases = {p: idxlists for p, idxlists in phrase_map.items() if len(idxlists) > 1}

    # ── 2. Word frequency flagging ──
    word_freq = defaultdict(list)
    for i, t in enumerate(tokens):
        if t['word'] not in STOPWORDS and len(t['word']) > 3:
            word_freq[t['word']].append(i)
    repeated_words = {w: idxs for w, idxs in word_freq.items() if len(idxs) >= 3}

    # ── 3. Build character-level flag map ──
    # 'high' = repeated phrase match, 'medium' = repeated word
    char_flags = {}

    for phrase, all_occurrences in repeated_phrases.items():
        for occurrence in all_occurrences:
            for idx in occurrence:
                if idx < len(tokens):
                    t = tokens[idx]
                    for pos in range(t['start'], t['end']):
                        char_flags[pos] = 'high'

    for word, idxs in repeated_words.items():
        for idx in idxs:
            if idx < len(tokens):
                t = tokens[idx]
                for pos in range(t['start'], t['end']):
                    if pos not in char_flags:
                        char_flags[pos] = 'medium'

    # ── 4. Build highlighted HTML ──
    highlighted_html = build_highlighted_html(text, char_flags)

    # ── 5. Sentence-level scoring ──
    sentence_results = []
    for sent in sentences:
        sent_tokens = [t for t in tokens if t['start'] >= sent['start'] and t['end'] <= sent['end']]
        if not sent_tokens:
            continue
        flagged = sum(1 for t in sent_tokens if char_flags.get(t['start']) in ('high', 'medium'))
        pct = round(flagged / len(sent_tokens) * 100, 1)
        if pct >= 10:
            sentence_results.append({
                'sentence': sent['text'][:150] + ('...' if len(sent['text']) > 150 else ''),
                'flagged_pct': pct,
                'flagged_words': flagged,
                'total_words': len(sent_tokens),
                'level': 'high' if pct >= 60 else 'medium' if pct >= 30 else 'low'
            })
    sentence_results.sort(key=lambda x: -x['flagged_pct'])

    # ── 6. Flagged word details ──
    flagged_word_details = []
    seen_words = set()
    for t in tokens:
        level = char_flags.get(t['start'])
        if level and t['word'] not in seen_words and t['word'] not in STOPWORDS:
            seen_words.add(t['word'])
            count = len(word_freq.get(t['word'], []))
            flagged_word_details.append({
                'word': t['original'],
                'level': level,
                'count': count,
                'positions': [tokens[i]['start'] for i in word_freq.get(t['word'], [])[:5]]
            })
    flagged_word_details.sort(key=lambda x: (-({'high':2,'medium':1}.get(x['level'],0)), -x['count']))

    # ── 7. Overall score ──
    content_tokens = [t for t in tokens if t['word'] not in STOPWORDS]
    total = len(content_tokens)
    flagged_count = sum(1 for t in content_tokens if char_flags.get(t['start']) in ('high', 'medium'))
    overall_score = round((flagged_count / total * 100) if total > 0 else 0, 2)

    if overall_score >= 60:
        verdict = {'label': 'High Plagiarism Detected', 'color': 'danger', 'icon': '🚨'}
    elif overall_score >= 35:
        verdict = {'label': 'Moderate Plagiarism Detected', 'color': 'warning', 'icon': '⚠️'}
    elif overall_score >= 15:
        verdict = {'label': 'Low Plagiarism / Repetition', 'color': 'info', 'icon': '🔍'}
    else:
        verdict = {'label': 'Likely Original Content', 'color': 'success', 'icon': '✅'}

    top_phrases = sorted(
        [{'phrase': p, 'count': len(v), 'occurrences': len(v)} for p, v in repeated_phrases.items()],
        key=lambda x: -x['count']
    )[:20]

    return {
        'highlighted_html': highlighted_html,
        'overall_score': overall_score,
        'verdict': verdict,
        'total_words': len(tokens),
        'content_words': total,
        'flagged_words': flagged_count,
        'clean_words': total - flagged_count,
        'repeated_phrases': top_phrases,
        'sentence_analysis': sentence_results[:15],
        'flagged_word_details': flagged_word_details[:50],
    }


def build_highlighted_html(text, char_flags):
    if not char_flags:
        return escape_html(text)

    result = []
    i = 0
    current_level = None
    chunk_start = 0

    while i <= len(text):
        level = char_flags.get(i) if i < len(text) else None

        if level != current_level:
            chunk = text[chunk_start:i]
            if chunk:
                escaped = escape_html(chunk)
                if current_level == 'high':
                    result.append(f'<mark class="flag-high" title="Repeated phrase detected">{escaped}</mark>')
                elif current_level == 'medium':
                    result.append(f'<mark class="flag-medium" title="Repeated word detected">{escaped}</mark>')
                else:
                    result.append(escaped)
            current_level = level
            chunk_start = i
        i += 1

    return ''.join(result)


def escape_html(s):
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;')
             .replace('\n', '<br>'))
