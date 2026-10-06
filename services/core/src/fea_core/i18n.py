from functools import cache
from pathlib import Path

from babel.messages.pofile import read_po

LOCALE_DIR = Path(__file__).parent / "locale"
DEFAULT_LOCALE = "es_MX"


def normalize_locale(locale: str) -> str:
    return locale.replace("-", "_")


@cache
def load_catalog(locale: str) -> dict[str, str]:
    path = LOCALE_DIR / normalize_locale(locale) / "messages.po"
    with path.open("rb") as handle:
        catalog = read_po(handle)
    return {
        str(message.id): str(message.string) for message in catalog if message.id and message.string
    }


def available_locales() -> list[str]:
    return sorted(p.name for p in LOCALE_DIR.iterdir() if (p / "messages.po").is_file())


def translate(key: str, locale: str = DEFAULT_LOCALE, **params: object) -> str:
    """Resuelve una clave de traducción; una clave desconocida se devuelve tal cual."""
    for candidate in (normalize_locale(locale), DEFAULT_LOCALE):
        try:
            template = load_catalog(candidate).get(key)
        except FileNotFoundError:
            continue
        if template is not None:
            return template.format(**params) if params else template
    return key
