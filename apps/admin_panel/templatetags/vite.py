import json
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()
_manifest_cache = None


def _load_manifest():
    global _manifest_cache
    if _manifest_cache is not None:
        return _manifest_cache

    manifest_path = (
        Path(settings.BASE_DIR) / "static" / "dist" / ".vite" / "manifest.json"
    )
    if not manifest_path.exists():
        _manifest_cache = {}
        return _manifest_cache

    _manifest_cache = json.loads(manifest_path.read_text(encoding="utf-8"))
    return _manifest_cache


@register.simple_tag
def vite_asset(asset_path):
    manifest = _load_manifest()
    entry = manifest.get(asset_path) or manifest.get(f"/{asset_path}")
    if entry:
        return static(f"dist/{entry['file']}")
    return static(asset_path)
