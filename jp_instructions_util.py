# coding=utf-8
# Copyright 2025 The Google Research Authors.
#
# Apache License, Version 2.0 （以下「ライセンス」）の下でライセンスされています;
# このファイルはライセンスに従ってのみ使用することができます。
# ライセンスのコピーは以下から入手できます。
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# 適用法で要求されるか書面で同意されない限り、ソフトウェアは
# 「現状のまま」の基準で配布され、明示または暗示を問わず、
# いかなる種類の保証または条件もありません。
# ライセンスの下での権限と制限については、
# ライセンスをご覧ください。

"""インストラクションのユーティリティライブラリ（日本語対応版）"""

import functools
import random
import re
from typing import List, Optional

import immutabledict
import nltk

# 日本語処理用
try:
    from janome.tokenizer import Tokenizer
    _JANOME_AVAILABLE = True
except ImportError:
    _JANOME_AVAILABLE = False

try:
    import sudachipy
    _SUDACHI_AVAILABLE = True
except ImportError:
    _SUDACHI_AVAILABLE = False

WORD_LIST = ["western", "sentence", "signal", "dump", "spot", "opposite", "bottom", "potato", "administration", "working", "welcome", "morning", "good", "agency", "primary", "wish", "responsibility", "press", "problem", "president", "steal", "brush", "read", "type", "beat", "trainer", "growth", "lock", "bone", "case", "equal", "comfortable", "region", "replacement", "performance", "mate", "walk", "medicine", "film", "thing", "rock", "tap", "total", "competition", "ease", "south", "establishment", "gather", "parking", "world", "plenty", "breath", "claim", "alcohol", "trade", "dear", "highlight", "street", "matter", "decision", "mess", "agreement", "studio", "coach", "assist", "brain", "wing", "style", "private", "top", "brown", "leg", "buy", "procedure", "method", "speed", "high", "company", "valuable", "pie", "analyst", "session", "pattern", "district", "pleasure", "dinner", "swimming", "joke", "order", "plate", "department", "motor", "cell", "spend", "cabinet", "difference", "power", "examination", "engine", "horse", "dimension", "pay", "toe", "curve", "literature", "bother", "fire", "possibility", "debate", "activity", "passage", "hello", "cycle", "background", "quiet", "author", "effect", "actor", "page", "bicycle", "error", "throat", "attack", "character", "phone", "tea", "increase", "outcome", "file", "specific", "inspector", "internal", "potential", "staff", "building", "employer", "shoe", "hand", "direction", "garden", "purchase", "interview", "study", "recognition", "member", "spiritual", "oven", "sandwich", "weird", "passenger", "particular", "response", "reaction", "size", "variation", "a", "cancel", "candy", "exit", "guest", "condition", "fly", "price", "weakness", "convert", "hotel", "great", "mouth", "mind", "song", "sugar", "suspect", "telephone", "ear", "roof", "paint", "refrigerator", "organization", "jury", "reward", "engineering", "day", "possession", "crew", "bar", "road", "description", "celebration", "score", "mark", "letter", "shower", "suggestion", "sir", "luck", "national", "progress", "hall", "stroke", "theory", "offer", "story", "tax", "definition", "history", "ride", "medium", "opening", "glass", "elevator", "stomach", "question", "ability", "leading", "village", "computer", "city", "grand", "confidence", "candle", "priest", "recommendation", "point", "necessary", "body", "desk", "secret", "horror", "noise", "culture", "warning", "water", "round", "diet", "flower", "bus", "tough", "permission", "week", "prompt", "connection", "abuse", "height", "save", "corner", "border", "stress", "drive", "stop", "rip", "meal", "listen", "confusion", "girlfriend", "living", "relation", "significance", "plan", "creative", "atmosphere", "blame", "invite", "housing", "paper", "drink", "roll", "silver", "drunk", "age", "damage", "smoke", "environment", "pack", "savings", "influence", "tourist", "rain", "post", "sign", "grandmother", "run", "profit", "push", "clerk", "final", "wine", "swim", "pause", "stuff", "singer", "funeral", "average", "source", "scene", "tradition", "personal", "snow", "nobody", "distance", "sort", "sensitive", "animal", "major", "negotiation", "click", "mood", "period", "arrival", "expression", "holiday", "repeat", "dust", "closet", "gold", "bad", "sail", "combination", "clothes", "emphasis", "duty", "black", "step", "school", "jump", "document", "professional", "lip", "chemical", "front", "wake", "while", "inside", "watch", "row", "subject", "penalty", "balance", "possible", "adult", "aside", "sample", "appeal", "wedding", "depth", "king", "award", "wife", "blow", "site", "camp", "music", "safe", "gift", "fault", "guess", "act", "shame", "drama", "capital", "exam", "stupid", "record", "sound", "swing", "novel", "minimum", "ratio", "machine", "shape", "lead", "operation", "salary", "cloud", "affair", "hit", "chapter", "stage", "quantity", "access", "army", "chain", "traffic", "kick", "analysis", "airport", "time", "vacation", "philosophy", "ball", "chest", "thanks", "place", "mountain", "advertising", "red", "past", "rent", "return", "tour", "house", "construction", "net", "native", "war", "figure", "fee", "spray", "user", "dirt", "shot", "task", "stick", "friend", "software", "promotion", "interaction", "surround", "block", "purpose", "practice", "conflict", "routine", "requirement", "bonus", "hole", "state", "junior", "sweet", "catch", "tear", "fold", "wall", "editor", "life", "position", "pound", "respect", "bathroom", "coat", "script", "job", "teach", "birth", "view", "resolve", "theme", "employee", "doubt", "market", "education", "serve", "recover", "tone", "harm", "miss", "union", "understanding", "cow", "river", "association", "concept", "training", "recipe", "relationship", "reserve", "depression", "proof", "hair", "revenue", "independent", "lift", "assignment", "temporary", "amount", "loss", "edge", "track", "check", "rope", "estimate", "pollution", "stable", "message", "delivery", "perspective", "mirror", "assistant", "representative", "witness", "nature", "judge", "fruit", "tip", "devil", "town", "emergency", "upper", "drop", "stay", "human", "neck", "speaker", "network", "sing", "resist", "league", "trip", "signature", "lawyer", "importance", "gas", "choice", "engineer", "success", "part", "external", "worker", "simple", "quarter", "student", "heart", "pass", "spite", "shift", "rough", "lady", "grass", "community", "garage", "youth", "standard", "skirt", "promise", "blind", "television", "disease", "commission", "positive", "energy", "calm", "presence", "tune", "basis", "preference", "head", "common", "cut", "somewhere", "presentation", "current", "thought", "revolution", "effort", "master", "implement", "republic", "floor", "principle", "stranger", "shoulder", "grade", "button", "tennis", "police", "collection", "account", "register", "glove", "divide", "professor", "chair", "priority", "combine", "peace", "extension", "maybe", "evening", "frame", "sister", "wave", "code", "application", "mouse", "match", "counter", "bottle", "half", "cheek", "resolution", "back", "knowledge", "make", "discussion", "screw", "length", "accident", "battle", "dress", "knee", "log", "package", "it", "turn", "hearing", "newspaper", "layer", "wealth", "profile", "imagination", "answer", "weekend", "teacher", "appearance", "meet", "bike", "rise", "belt", "crash", "bowl", "equivalent", "support", "image", "poem", "risk", "excitement", "remote", "secretary", "public", "produce", "plane", "display", "money", "sand", "situation", "punch", "customer", "title", "shake", "mortgage", "option", "number", "pop", "window", "extent", "nothing", "experience", "opinion", "departure", "dance", "indication", "boy", "material", "band", "leader", "sun", "beautiful", "muscle", "farmer", "variety", "fat", "handle", "director", "opportunity", "calendar", "outside", "pace", "bath", "fish", "consequence", "put", "owner", "go", "doctor", "information", "share", "hurt", "protection", "career", "finance", "force", "golf", "garbage", "aspect", "kid", "food", "boot", "milk", "respond", "objective", "reality", "raw", "ring", "mall", "one", "impact", "area", "news", "international", "series", "impress", "mother", "shelter", "strike", "loan", "month", "seat", "anything", "entertainment", "familiar", "clue", "year", "glad", "supermarket", "natural", "god", "cost", "conversation", "tie", "ruin", "comfort", "earth", "storm", "percentage", "assistance", "budget", "strength", "beginning", "sleep", "other", "young", "unit", "fill", "store", "desire", "hide", "value", "cup", "maintenance", "nurse", "function", "tower", "role", "class", "camera", "database", "panic", "nation", "basket", "ice", "art", "spirit", "chart", "exchange", "feedback", "statement", "reputation", "search", "hunt", "exercise", "nasty", "notice", "male", "yard", "annual", "collar", "date", "platform", "plant", "fortune", "passion", "friendship", "spread", "cancer", "ticket", "attitude", "island", "active", "object", "service", "buyer", "bite", "card", "face", "steak", "proposal", "patient", "heat", "rule", "resident", "broad", "politics", "west", "knife", "expert", "girl", "design", "salt", "baseball", "grab", "inspection", "cousin", "couple", "magazine", "cook", "dependent", "security", "chicken", "version", "currency", "ladder", "scheme", "kitchen", "employment", "local", "attention", "manager", "fact", "cover", "sad", "guard", "relative", "county", "rate", "lunch", "program", "initiative", "gear", "bridge", "breast", "talk", "dish", "guarantee", "beer", "vehicle", "reception", "woman", "substance", "copy", "lecture", "advantage", "park", "cold", "death", "mix", "hold", "scale", "tomorrow", "blood", "request", "green", "cookie", "church", "strip", "forever", "beyond", "debt", "tackle", "wash", "following", "feel", "maximum", "sector", "sea", "property", "economics", "menu", "bench", "try", "language", "start", "call", "solid", "address", "income", "foot", "senior", "honey", "few", "mixture", "cash", "grocery", "link", "map", "form", "factor", "pot", "model", "writer", "farm", "winter", "skill", "anywhere", "birthday", "policy", "release", "husband", "lab", "hurry", "mail", "equipment", "sink", "pair", "driver", "consideration", "leather", "skin", "blue", "boat", "sale", "brick", "two", "feed", "square", "dot", "rush", "dream", "location", "afternoon", "manufacturer", "control", "occasion", "trouble", "introduction", "advice", "bet", "eat", "kill", "category", "manner", "office", "estate", "pride", "awareness", "slip", "crack", "client", "nail", "shoot", "membership", "soft", "anybody", "web", "official", "individual", "pizza", "interest", "bag", "spell", "profession", "queen", "deal", "resource", "ship", "guy", "chocolate", "joint", "formal", "upstairs", "car", "resort", "abroad", "dealer", "associate", "finger", "surgery", "comment", "team", "detail", "crazy", "path", "tale", "initial", "arm", "radio", "demand", "single", "draw", "yellow", "contest", "piece", "quote", "pull", "commercial", "shirt", "contribution", "cream", "channel", "suit", "discipline", "instruction", "concert", "speech", "low", "effective", "hang", "scratch", "industry", "breakfast", "lay", "join", "metal", "bedroom", "minute", "product", "rest", "temperature", "many", "give", "argument", "print", "purple", "laugh", "health", "credit", "investment", "sell", "setting", "lesson", "egg", "middle", "marriage", "level", "evidence", "phrase", "love", "self", "benefit", "guidance", "affect", "you", "dad", "anxiety", "special", "boyfriend", "test", "blank", "payment", "soup", "obligation", "reply", "smile", "deep", "complaint", "addition", "review", "box", "towel", "minor", "fun", "soil", "issue", "cigarette", "internet", "gain", "tell", "entry", "spare", "incident", "family", "refuse", "branch", "can", "pen", "grandfather", "constant", "tank", "uncle", "climate", "ground", "volume", "communication", "kind", "poet", "child", "screen", "mine", "quit", "gene", "lack", "charity", "memory", "tooth", "fear", "mention", "marketing", "reveal", "reason", "court", "season", "freedom", "land", "sport", "audience", "classroom", "law", "hook", "win", "carry", "eye", "smell", "distribution", "research", "country", "dare", "hope", "whereas", "stretch", "library", "if", "delay", "college", "plastic", "book", "present", "use", "worry", "champion", "goal", "economy", "march", "election", "reflection", "midnight", "slide", "inflation", "action", "challenge", "guitar", "coast", "apple", "campaign", "field", "jacket", "sense", "way", "visual", "remove", "weather", "trash", "cable", "regret", "buddy", "beach", "historian", "courage", "sympathy", "truck", "tension", "permit", "nose", "bed", "son", "person", "base", "meat", "usual", "air", "meeting", "worth", "game", "independence", "physical", "brief", "play", "raise", "board", "she", "key", "writing", "pick", "command", "party", "yesterday", "spring", "candidate", "physics", "university", "concern", "development", "change", "string", "target", "instance", "room", "bitter", "bird", "football", "normal", "split", "impression", "wood", "long", "meaning", "stock", "cap", "leadership", "media", "ambition", "fishing", "essay", "salad", "repair", "today", "designer", "night", "bank", "drawing", "inevitable", "phase", "vast", "chip", "anger", "switch", "cry", "twist", "personality", "attempt", "storage", "being", "preparation", "bat", "selection", "white", "technology", "contract", "side", "section", "station", "till", "structure", "tongue", "taste", "truth", "difficulty", "group", "limit", "main", "move", "feeling", "light", "example", "mission", "might", "wait", "wheel", "shop", "host", "classic", "alternative", "cause", "agent", "consist", "table", "airline", "text", "pool", "craft", "range", "fuel", "tool", "partner", "load", "entrance", "deposit", "hate", "article", "video", "summer", "feature", "extreme", "mobile", "hospital", "flight", "fall", "pension", "piano", "fail", "result", "rub", "gap", "system", "report", "suck", "ordinary", "wind", "nerve", "ask", "shine", "note", "line", "mom", "perception", "brother", "reference", "bend", "charge", "treat", "trick", "term", "homework", "bake", "bid", "status", "project", "strategy", "orange", "let", "enthusiasm", "parent", "concentrate", "device", "travel", "poetry", "business", "society", "kiss", "end", "vegetable", "employ", "schedule", "hour", "brave", "focus", "process", "movie", "illegal", "general", "coffee", "ad", "highway", "chemistry", "psychology", "hire", "bell", "conference", "relief", "show", "neat", "funny", "weight", "quality", "club", "daughter", "zone", "touch", "tonight", "shock", "burn", "excuse", "name", "survey", "landscape", "advance", "satisfaction", "bread", "disaster", "item", "hat", "prior", "shopping", "visit", "east", "photo", "home", "idea", "father", "comparison", "cat", "pipe", "winner", "count", "lake", "fight", "prize", "foundation", "dog", "keep", "ideal", "fan", "struggle", "peak", "safety", "solution", "hell", "conclusion", "population", "strain", "alarm", "measurement", "second", "train", "race", "due", "insurance", "boss", "tree", "monitor", "sick", "course", "drag", "appointment", "slice", "still", "care", "patience", "rich", "escape", "emotion", "royal", "female", "childhood", "government", "picture", "will", "sock", "big", "gate", "oil", "cross", "pin", "improvement", "championship", "silly", "help", "sky", "pitch", "man", "diamond", "most", "transition", "work", "science", "committee", "moment", "fix", "teaching", "dig", "specialist", "complex", "guide", "people", "dead", "voice", "original", "break", "topic", "data", "degree", "reading", "recording", "bunch", "reach", "judgment", "lie", "regular", "set", "painting", "mode", "list", "player", "bear", "north", "wonder", "carpet", "heavy", "officer", "negative", "clock", "unique", "baby", "pain", "assumption", "disk", "iron", "bill", "drawer", "look", "double", "mistake", "finish", "future", "brilliant", "contact", "math", "rice", "leave", "restaurant", "discount", "sex", "virus", "bit", "trust", "event", "wear", "juice", "failure", "bug", "context", "mud", "whole", "wrap", "intention", "draft", "pressure", "cake", "dark", "explanation", "space", "angle", "word", "efficiency", "management", "habit", "star", "chance", "finding", "transportation", "stand", "criticism", "flow", "door", "injury", "insect", "surprise", "apartment"]

# 日本語の頻出単語リスト（サンプル）
JAPANESE_WORD_LIST = [
    "会社", "時間", "仕事", "人", "日本", "場合", "問題", "情報", "今", "方法",
    "必要", "可能", "利用", "サービス", "商品", "開発", "技術", "システム", "データ", "管理",
    "顧客", "市場", "ビジネス", "プロジェクト", "チーム", "コミュニケーション", "目標", "計画", "実現", "成功",
    "効果", "結果", "分析", "改善", "品質", "価値", "機能", "性能", "安全", "環境",
    "社会", "経済", "文化", "教育", "研究", "学習", "知識", "経験", "スキル", "能力"
]

# ISO 639-1 コードから言語名への対応表
LANGUAGE_CODES = immutabledict.immutabledict({
    "en": "English",
    "es": "Spanish", 
    "pt": "Portuguese",
    "ar": "Arabic",
    "hi": "Hindi",
    "fr": "French",
    "ru": "Russian", 
    "de": "German",
    "ja": "Japanese",
    "it": "Italian",
    "bn": "Bengali",
    "uk": "Ukrainian",
    "th": "Thai",
    "ur": "Urdu",
    "ta": "Tamil",
    "te": "Telugu",
    "bg": "Bulgarian", 
    "ko": "Korean",
    "pl": "Polish",
    "he": "Hebrew", 
    "fa": "Persian",
    "vi": "Vietnamese",
    "ne": "Nepali",
    "sw": "Swahili",
    "kn": "Kannada",
    "mr": "Marathi",
    "gu": "Gujarati", 
    "pa": "Punjabi",
    "ml": "Malayalam",
    "fi": "Finnish",
})

# 英語文分割用の正規表現パターン
_ALPHABETS = "([A-Za-z])"
_PREFIXES = "(Mr|St|Mrs|Ms|Dr)[.]"
_SUFFIXES = "(Inc|Ltd|Jr|Sr|Co)"
_STARTERS = r"(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
_ACRONYMS = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
_WEBSITES = "[.](com|net|org|io|gov|edu|me)"
_DIGITS = "([0-9])"
_MULTIPLE_DOTS = r"\.{2,}"


def _detect_language(text: str) -> str:
    """テキストの言語を簡易的に検出します
    
    Args:
        text: 検出対象のテキスト
        
    Returns:
        言語コード ('ja' または 'en')
    """
    # 日本語の文字（ひらがな、カタカナ、漢字）が含まれているかチェック
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
    if japanese_pattern.search(text):
        return 'ja'
    return 'en'


def split_into_sentences(text: str, lang: Optional[str] = None) -> List[str]:
    """テキストを文に分割します
    
    Args:
        text: 1つ以上の文で構成される文字列
        lang: 言語コード ('ja', 'en' など) Noneの場合は自動検出
        
    Returns:
        各文字列が1つの文である文字列のリスト
    """
    if not text:
        return []
    
    if lang is None:
        lang = _detect_language(text)
    
    if lang == 'ja':
        return _split_into_sentences_ja(text)
    else:
        return _split_into_sentences_en(text)


def _split_into_sentences_ja(text: str) -> List[str]:
    """日本語テキストを文に分割します"""
    sentences = []
    current = []
    in_quote = False
    
    for char in text:
        current.append(char)
        
        # 引用符の開始・終了を追跡
        if char in ['「', '『', '（', '(']:
            in_quote = True
        elif char in ['」', '』', '）', ')']:
            in_quote = False
        
        # 文の終わりを検出
        if char in ['。', '！', '？', '．'] and not in_quote:
            sentence = ''.join(current).strip()
            if sentence:
                sentences.append(sentence)
            current = []
    
    # 残りの文字を処理
    if current:
        sentence = ''.join(current).strip()
        if sentence:
            sentences.append(sentence)
    
    return sentences


def _split_into_sentences_en(text: str) -> List[str]:
    """英語テキストを文に分割します (既存の実装)"""
    text = " " + text + "  "
    text = text.replace("\n", " ")
    text = re.sub(_PREFIXES, "\\1<prd>", text)
    text = re.sub(_WEBSITES, "<prd>\\1", text)
    text = re.sub(_DIGITS + "[.]" + _DIGITS, "\\1<prd>\\2", text)
    text = re.sub(
        _MULTIPLE_DOTS,
        lambda match: "<prd>" * len(match.group(0)) + "<stop>",
        text,
    )
    if "Ph.D" in text:
        text = text.replace("Ph.D.", "Ph<prd>D<prd>")
    text = re.sub(r"\s" + _ALPHABETS + "[.] ", " \\1<prd> ", text)
    text = re.sub(_ACRONYMS + " " + _STARTERS, "\\1<stop> \\2", text)
    text = re.sub(
        _ALPHABETS + "[.]" + _ALPHABETS + "[.]" + _ALPHABETS + "[.]",
        "\\1<prd>\\2<prd>\\3<prd>",
        text,
    )
    text = re.sub(
        _ALPHABETS + "[.]" + _ALPHABETS + "[.]", "\\1<prd>\\2<prd>", text
    )
    text = re.sub(" " + _SUFFIXES + "[.] " + _STARTERS, " \\1<stop> \\2", text)
    text = re.sub(" " + _SUFFIXES + "[.]", " \\1<prd>", text)
    text = re.sub(" " + _ALPHABETS + "[.]", " \\1<prd>", text)
    if '"' in text:
        text = text.replace('."', '".')
    if "!" in text:
        text = text.replace('!"', '"!')
    if "?" in text:
        text = text.replace('?"', '"?')
    text = text.replace(".", ".<stop>")
    text = text.replace("?", "?<stop>")
    text = text.replace("!", "!<stop>")
    text = text.replace("<prd>", ".")
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences and not sentences[-1]:
        sentences = sentences[:-1]
    return sentences


def count_words(text: str, lang: Optional[str] = None) -> int:
    """単語数をカウントします
    
    Args:
        text: カウント対象のテキスト
        lang: 言語コード ('ja', 'en' など) Noneの場合は自動検出
        
    Returns:
        単語数
    """
    if not text:
        return 0
    
    if lang is None:
        lang = _detect_language(text)
    
    if lang == 'ja':
        return _count_words_ja(text)
    else:
        return _count_words_en(text)


def _count_words_ja(text: str) -> int:
    """日本語テキストの単語数をカウントします"""
    # Sudachiが利用可能な場合は優先的に使用
    if _SUDACHI_AVAILABLE:
        tokenizer = _get_sudachi_tokenizer()
        tokens = tokenizer.tokenize(text)
        # 内容語（名詞、動詞、形容詞、副詞など）のみをカウント
        content_words = [token for token in tokens 
                        if token.part_of_speech()[0] not in ['補助記号', '空白', '助詞', '助動詞']]
        return len(content_words)
    
    # Sudachiが利用できない場合はJanomeを使用
    if _JANOME_AVAILABLE:
        tokenizer = _get_japanese_tokenizer()
        tokens = tokenizer.tokenize(text, wakati=True)
        return len([t for t in tokens if len(t.strip()) > 0])
    
    # どちらも利用できない場合は文字数を返す（簡易的な代替）
    text = re.sub(r'[\s。、！？・\.,!?]', '', text)
    return len(text)


def _count_words_en(text: str) -> int:
    """英語テキストの単語数をカウントします (既存の実装)"""
    tokenizer = nltk.tokenize.RegexpTokenizer(r"\w+")
    tokens = tokenizer.tokenize(text)
    return len(tokens)


@functools.lru_cache(maxsize=None)
def _get_sudachi_tokenizer():
    """Sudachi形態素解析器を取得します (キャッシュ付き)"""
    if not _SUDACHI_AVAILABLE:
        raise ImportError("Sudachiがインストールされていません pip install sudachipy sudachidict_core を実行してください")
    return sudachipy.Dictionary().create()

@functools.lru_cache(maxsize=None)
def _get_japanese_tokenizer():
    """日本語形態素解析器を取得します (キャッシュ付き)"""
    if not _JANOME_AVAILABLE:
        raise ImportError("janomeがインストールされていません pip install janome を実行してください")
    return Tokenizer()


@functools.lru_cache(maxsize=None)
def _get_sentence_tokenizer():
    """英語文分割器を取得します"""
    return nltk.data.load("nltk:tokenizers/punkt/english.pickle")


def count_sentences(text: str, lang: Optional[str] = None) -> int:
    """文の数をカウントします
    
    Args:
        text: カウント対象のテキスト
        lang: 言語コード ('ja', 'en' など) Noneの場合は自動検出
        
    Returns:
        文の数
    """
    if not text:
        return 0
    
    if lang is None:
        lang = _detect_language(text)
    
    if lang == 'ja':
        return len(split_into_sentences(text, lang='ja'))
    else:
        tokenizer = _get_sentence_tokenizer()
        tokenized_sentences = tokenizer.tokenize(text)
        return len(tokenized_sentences)


def generate_keywords(num_keywords: int, lang: Optional[str] = None) -> List[str]:
    """いくつかのキーワードをランダムに生成します
    
    Args:
        num_keywords: 生成するキーワードの数
        lang: 言語コード ('ja', 'en' など) Noneの場合は 'en'
        
    Returns:
        ランダムに選ばれたキーワードのリスト
    """
    if lang == 'ja':
        if num_keywords > len(JAPANESE_WORD_LIST):
            raise ValueError(f"要求されたキーワード数 ({num_keywords}) が利用可能な日本語単語数 ({len(JAPANESE_WORD_LIST)}) を超えています")
        return random.sample(JAPANESE_WORD_LIST, k=num_keywords)
    else:
        if num_keywords > len(WORD_LIST):
            raise ValueError(f"Requested number of keywords ({num_keywords}) exceeds available words ({len(WORD_LIST)})")
        return random.sample(WORD_LIST, k=num_keywords)

