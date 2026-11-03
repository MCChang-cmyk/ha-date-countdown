"""Use Home Assistant's current schema library, with legacy compatibility."""
try:
    import probatio as vol
except ImportError:
    import voluptuous as vol
