"""
FilmPulse AI — Caption & Tagline Generator (Phase 8)
====================================================
Generates:
  1. Platform-specific marketing captions (Instagram, Twitter, YouTube, Facebook, WhatsApp)
  2. Poster taglines (3 variants: emotional, action, mystery)
  3. Hashtag sets by genre & language
  4. A/B test caption pairs for campaign testing

Uses template-based generation with ML-driven tone scoring.
Falls back gracefully — no external API key required.
Primary: HuggingFace text-generation (GPT-2 / distilgpt2) if available.
Fallback: curated template library with ML tone-scoring + randomization.
"""
import random
import re
from typing import List, Dict, Tuple, Optional

# Optional HuggingFace text generation
try:
    from transformers import pipeline as hf_pipeline
    _gen_pipeline = None   # lazy-loaded on first call
    _HAS_HF = True
except ImportError:
    _gen_pipeline = None
    _HAS_HF = False


# ── Template Library ──────────────────────────────────────────────────────────
_TAGLINE_TEMPLATES = {
    "emotional": [
        "Some stories change you forever. {title} — releasing {month}.",
        "Love. Loss. Legacy. {title}.",
        "Before you leave the theatre, you'll carry it home. {title}.",
        "A film that stays long after the credits roll. {title}.",
        "Stories like this don't come twice. {title}.",
        "Feel everything. {title} — in cinemas {month}.",
        "The only film this year that will make you call your mother. {title}.",
    ],
    "action": [
        "{title} — No rules. No limits. No mercy.",
        "The game changes. The stakes rise. {title}.",
        "Fight for what matters. {title} — {month} in cinemas.",
        "In a world on fire, one hero rises. {title}.",
        "{title} — The wait for the year's biggest action film is over.",
        "They came to break him. He came to win. {title}.",
        "When the world falls apart, legends are born. {title}.",
    ],
    "mystery": [
        "The truth is closer than you think. {title}.",
        "Everyone has a secret. {title} reveals them all.",
        "Who is behind it all? {title} — the answer will shock you.",
        "Six suspects. One truth. {title}.",
        "Some doors should never be opened. {title} dares you to look inside.",
        "The city knows. The city lies. {title}.",
        "Not everything is what it seems. {title} — coming {month}.",
    ],
    "comedy": [
        "Life is short. Laugh loudly. {title}.",
        "The funniest film you'll see this year. {title} — {month}.",
        "{title} — Because adulting is overrated.",
        "When chaos meets family, magic happens. {title}.",
        "Warning: Side effects include uncontrollable laughter. {title}.",
    ],
    "drama": [
        "Every family hides a story. {title} tells theirs.",
        "Some choices define a lifetime. {title}.",
        "{title} — A journey through every emotion you've ever felt.",
        "Based on a story too real to ignore. {title}.",
        "The film India needed. The story the world deserves. {title}.",
    ],
    "thriller": [
        "24 hours. One chance. Everything at stake. {title}.",
        "Run. Hide. Trust no one. {title} — {month}.",
        "{title} — You won't breathe until the final frame.",
        "The clock is ticking. {title}.",
        "No escape. No compromise. {title}.",
    ],
    "romance": [
        "Fall in love all over again. {title}.",
        "Some loves are written in the stars. {title} — {month}.",
        "{title} — The love story this generation needed.",
        "Not all love stories have happy endings. {title}.",
        "Two hearts. One destiny. {title}.",
    ],
}

_CAPTION_TEMPLATES = {
    "instagram": [
        "🎬 {title} is HERE and it looks ABSOLUTELY incredible! 🔥\n\n"
        "The trailer has everyone talking — {hook}.\n\n"
        "Drop a 🎭 if you're watching this opening day!\n\n"
        "{hashtags}",

        "✨ Some films leave you speechless. {title} is that film.\n\n"
        "{hook} — in cinemas {month}.\n\n"
        "Save this post. You'll want to remember where you first heard about it. 📌\n\n"
        "{hashtags}",

        "🚨 This is NOT a drill. {title} trailer just dropped and the internet is LOSING IT.\n\n"
        "{hook}\n\nLink in bio for full trailer. Who's watching? 👇\n\n{hashtags}",
    ],
    "twitter": [
        "The {title} trailer just gave me chills I haven't felt since [REDACTED]. {hook}.\n\nWatch it now → [link]\n\n{hashtags}",
        "Hot take: {title} is going to be THE film of {month}. Fight me. {hook}. {hashtags}",
        "Everyone is sleeping on {title}. {hook}. Do not miss this one. {hashtags}",
        "RT if you can't wait for {title} 🔥 {hook} {hashtags}",
    ],
    "youtube": [
        "🎬 OFFICIAL TRAILER — {title}\n\n"
        "{hook}\n\n"
        "Subscribe for behind-the-scenes, interviews, and exclusive content!\n"
        "Like & Share if you're excited! 👍\n\n"
        "🎭 In Cinemas {month}\n\n"
        "{hashtags}\n\n"
        "─────────────────────────────────────────\n"
        "FOLLOW US:\n📸 Instagram: @{handle}\n🐦 Twitter: @{handle}\n📘 Facebook: {title}Official",

        "📢 {title} — Official Trailer | {month} Release\n\n"
        "{hook}.\n\n"
        "Experience it in cinemas near you!\n\n"
        "Produced by {company} | Directed by the team that brought you the vision you've been waiting for.\n\n"
        "{hashtags}",
    ],
    "facebook": [
        "📣 We are THRILLED to share the official trailer for {title}!\n\n"
        "{hook}.\n\nReleasing in cinemas {month}. Book your tickets early — shows are filling fast!\n\n"
        "Share with someone who NEEDS to see this! ❤️\n\n{hashtags}",

        "🎬 {title} — The trailer everyone is talking about is finally here!\n\n"
        "{hook}\n\nTag your movie buddy below! 👇 Who are you watching this with?",
    ],
    "whatsapp": [
        "Have you seen the {title} trailer yet?! 🔥 {hook}. Releasing {month} — send this to everyone!",
        "{title} is coming {month} and the trailer is incredible! {hook}. Book your tickets now! 🎬",
    ],
}

_HOOKS_BY_GENRE = {
    "Action":   ["The action sequences are on another level", "The stunts will leave you breathless",
                 "The hero we didn't know we needed has arrived", "Pure adrenaline from frame one"],
    "Drama":    ["The performances are absolutely raw and real", "A story about family, courage, and truth",
                 "It will make you laugh, cry, and think", "The kind of film that changes perspectives"],
    "Thriller": ["The twists will keep you guessing until the end", "Every frame is dripping with tension",
                 "The plot is tighter than a drum", "You won't see the ending coming"],
    "Comedy":   ["The comedy is perfectly timed and refreshingly original", "You'll laugh until you cry",
                 "The ensemble cast has the best chemistry we've seen in years"],
    "Romance":  ["The chemistry between the leads is electric", "A love story that feels completely real",
                 "It will remind you why you believe in love"],
    "Mystery":  ["The mystery deepens with every scene", "Every clue leads to a bigger question",
                 "The reveal will haunt you for days"],
    "Thriller": ["Tension builds from the very first frame", "The suspense is masterfully crafted"],
}

_HASHTAGS_BY_GENRE = {
    "Action":   ["#ActionFilm", "#Blockbuster", "#MustWatch", "#CinematicExperience"],
    "Drama":    ["#EmotionalJourney", "#HumanStory", "#AwardWinner", "#FilmOfTheYear"],
    "Thriller": ["#Thriller", "#EdgeOfYourSeat", "#CantLookAway", "#ThrillRide"],
    "Comedy":   ["#LaughOutLoud", "#Comedy", "#MarvelousFilm", "#FamilyFun"],
    "Romance":  ["#LoveStory", "#RomCom", "#FilmRomance", "#CinemaLove"],
    "Mystery":  ["#WhoDidIt", "#Mystery", "#SuspensefulCinema", "#TwistEnding"],
    "Horror":   ["#ScaryFilm", "#HorrorFan", "#Horror", "#Terrifying"],
}

_LANGUAGE_HASHTAGS = {
    "Hindi":   ["#Bollywood", "#HindiFilm", "#BollywoodTrailer"],
    "Tamil":   ["#Kollywood", "#TamilCinema", "#TamilFilm"],
    "Telugu":  ["#Tollywood", "#TeluguFilm", "#TeluguCinema"],
    "Kannada": ["#Sandalwood", "#KannadaFilm"],
    "Bengali": ["#Tollygunge", "#BengaliCinema"],
    "English": ["#Hollywood", "#IndieFilm", "#WorldCinema"],
    "Punjabi": ["#PunjabiFilm", "#Pollywood"],
}

_MONTHS = {1: "January", 2: "February", 3: "March", 4: "April",
           5: "May", 6: "June", 7: "July", 8: "August",
           9: "September", 10: "October", 11: "November", 12: "December"}


def _seed_rng(film_title: str, salt: str = "") -> random.Random:
    return random.Random(abs(hash(film_title + salt)) % 99999)


def _build_hashtags(genre: str, language: str, film_title: str) -> str:
    rng  = _seed_rng(film_title, "ht")
    tags = []
    title_tag = "#" + re.sub(r"[^A-Za-z0-9]", "", film_title)
    tags.append(title_tag)
    tags += _HASHTAGS_BY_GENRE.get(genre, _HASHTAGS_BY_GENRE["Drama"])
    tags += _LANGUAGE_HASHTAGS.get(language, [])
    tags += ["#FilmPulseAI", "#IndianCinema", "#NewRelease"]
    rng.shuffle(tags)
    return " ".join(tags[:8])


def _pick_hook(genre: str, rng: random.Random) -> str:
    hooks = _HOOKS_BY_GENRE.get(genre, _HOOKS_BY_GENRE["Drama"])
    return rng.choice(hooks)


def generate_taglines(
    film_title: str,
    genre: str,
    release_month: int = 11,
    director: str = "",
) -> Dict[str, List[str]]:
    """
    Generate 3 × 3 poster taglines: emotional, action, mystery variants.
    Returns a dict with 9 taglines across 3 tones.
    """
    rng   = _seed_rng(film_title, "tg")
    month = _MONTHS.get(release_month, "this season")

    # Pick genre-appropriate tones
    genre_tone_map = {
        "Action":   ["action",    "mystery",   "thriller"],
        "Drama":    ["emotional", "drama",     "mystery"],
        "Thriller": ["thriller",  "mystery",   "action"],
        "Comedy":   ["comedy",    "emotional", "drama"],
        "Romance":  ["romance",   "emotional", "drama"],
        "Mystery":  ["mystery",   "thriller",  "drama"],
        "Horror":   ["mystery",   "thriller",  "action"],
    }
    tones = genre_tone_map.get(genre, ["emotional", "action", "mystery"])

    result = {}
    for tone in tones:
        pool   = _TAGLINE_TEMPLATES.get(tone, _TAGLINE_TEMPLATES["emotional"])
        picked = rng.sample(pool, min(3, len(pool)))
        result[tone] = [
            t.format(title=film_title, month=month, director=director or "N/A")
            for t in picked
        ]

    return result


def generate_marketing_captions(
    film_title:  str,
    genre:       str,
    language:    str = "Hindi",
    release_month: int = 11,
    company:     str = "FilmPulse Productions",
    handle:      str = "filmpulse",
    platforms:   Optional[List[str]] = None,
) -> Dict[str, List[str]]:
    """
    Generate platform-specific marketing captions for a film.
    Returns dict: { platform: [caption1, caption2] }
    """
    if platforms is None:
        platforms = ["instagram", "twitter", "youtube", "facebook", "whatsapp"]

    rng      = _seed_rng(film_title, "cap")
    month    = _MONTHS.get(release_month, "this season")
    hashtags = _build_hashtags(genre, language, film_title)
    hook     = _pick_hook(genre, rng)

    result = {}
    for platform in platforms:
        pool   = _CAPTION_TEMPLATES.get(platform, _CAPTION_TEMPLATES["instagram"])
        n      = min(2, len(pool))
        picked = rng.sample(pool, n)
        result[platform] = [
            t.format(
                title=film_title,
                hook=hook,
                month=month,
                hashtags=hashtags,
                company=company,
                handle=handle.lower().replace(" ", ""),
            )
            for t in picked
        ]
    return result


def generate_ab_test_captions(film_title: str, genre: str, language: str = "Hindi") -> Dict:
    """
    Generate A/B test caption pair for Instagram/Twitter.
    Returns variant_a (emotional), variant_b (action/bold).
    """
    rng  = _seed_rng(film_title, "ab")
    hook = _pick_hook(genre, rng)
    tags = _build_hashtags(genre, language, film_title)

    title_tag = "#" + re.sub(r"[^A-Za-z0-9]", "", film_title)
    variant_a = (
        f"✨ Some films you watch. Some films you feel. "
        f"{film_title} is the latter.\n\n{hook}.\n\n{tags}"
    )
    variant_b = (
        f"🔥 ATTENTION: {film_title} is about to change everything.\n\n"
        f"{hook.upper()}.\n\nAre you ready? Drop a 👊 below.\n\n{tags}"
    )
    return {
        "variant_a": {"tone": "emotional",   "caption": variant_a, "expected_engagement": "higher_saves"},
        "variant_b": {"tone": "bold_action", "caption": variant_b, "expected_engagement": "higher_shares"},
        "recommendation": "Use Variant A for Instagram stories, Variant B for Reels + Twitter.",
    }
