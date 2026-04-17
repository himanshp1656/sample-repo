"""
cross_repo_cases.py — Simulates cross-repo inheritance patterns.

These classes mimic the CloudSqlApp → SqlMetadataExtractor → BaseMetadataExtractor → App
chain to test self.method() and super().method() lineage resolution.
"""


# ── Simulated "other repo" base classes ───────────────────────────────────────
# In real cross-repo usage, these would live in a separate crawled repo.

class App:
    """Top-level base (simulates application_sdk.App)."""

    def run(self, input):
        """Base run — subclasses override this."""
        return {"status": "ok"}

    def upload(self, path: str) -> bool:
        """Upload output to object store."""
        return True

    def health_check(self) -> str:
        return "healthy"


class BaseExtractor(App):
    """Mid-level base (simulates BaseMetadataExtractor)."""

    def fetch_data(self, query: str) -> list:
        return []

    def transform_data(self, raw: list) -> list:
        return raw

    def run(self, input):
        result = self.fetch_data(input.get("query", ""))
        return self.transform_data(result)


class SqlExtractor(BaseExtractor):
    """SQL-specific base (simulates SqlMetadataExtractor)."""

    def fetch_procedures(self, schema: str) -> list:
        return []

    def run(self, input):
        procs = self.fetch_procedures(input.get("schema", "public"))
        base_result = super().run(input)
        return {**base_result, "procedures": procs}


# ── Concrete class that calls inherited methods ────────────────────────────────

class CloudSqlProcessor(SqlExtractor):
    """
    Concrete processor — calls self.upload, self.transform_data,
    self.fetch_procedures, and super().run().

    These are all inherited — none defined in this class.
    This tests cross-repo (or deep-hierarchy) self/super resolution.
    """

    def process(self, input: dict) -> dict:
        # self.fetch_procedures — defined in SqlExtractor ✓
        procs = self.fetch_procedures(input.get("schema", "public"))

        # self.transform_data — defined in BaseExtractor ✓
        transformed = self.transform_data(procs)

        # self.upload — defined in App (2 levels up) ✓
        self.upload("/output/results.json")

        # super().run — defined in SqlExtractor ✓
        base = super().run(input)

        return {**base, "transformed": transformed}

    def full_pipeline(self, input: dict) -> dict:
        # self.health_check — defined in App (3 levels up) ✓
        status = self.health_check()

        result = self.process(input)
        return {"status": status, **result}


# ── Second chain to test multiple inheritance resolution ──────────────────────

class StorageMixin:
    def save_to_disk(self, data: dict, path: str) -> bool:
        return True

    def load_from_disk(self, path: str) -> dict:
        return {}


class CachedExtractor(StorageMixin, BaseExtractor):
    """Uses both StorageMixin and BaseExtractor."""

    def run_with_cache(self, input: dict, cache_path: str) -> dict:
        # self.load_from_disk — defined in StorageMixin ✓
        cached = self.load_from_disk(cache_path)
        if cached:
            return cached

        # self.fetch_data — defined in BaseExtractor ✓
        raw = self.fetch_data(input.get("query", ""))

        # self.transform_data — defined in BaseExtractor ✓
        result = self.transform_data(raw)

        # self.save_to_disk — defined in StorageMixin ✓
        self.save_to_disk(result, cache_path)
        return result

    def run(self, input: dict) -> dict:
        # super().run — defined in BaseExtractor ✓
        return super().run(input)
