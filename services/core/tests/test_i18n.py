import pytest

from fea_core.i18n import DEFAULT_LOCALE, available_locales, load_catalog, translate


def test_translates_known_key_in_default_locale() -> None:
    assert translate("error.unauthorized") == "Necesitas iniciar sesión."


def test_accepts_bcp47_locale_tag() -> None:
    assert translate("error.unauthorized", "es-MX") == translate("error.unauthorized")


def test_unknown_key_returns_the_key() -> None:
    assert translate("no.existe") == "no.existe"


def test_unknown_locale_falls_back_to_default() -> None:
    assert translate("error.unauthorized", "fr-FR") == translate("error.unauthorized")


def test_default_locale_is_available() -> None:
    assert DEFAULT_LOCALE in available_locales()


@pytest.mark.parametrize("locale", available_locales())
def test_every_locale_has_the_same_keys_as_default(locale: str) -> None:
    assert set(load_catalog(locale)) == set(load_catalog(DEFAULT_LOCALE))
