from memoir.config import MemoirConfig
from memoir.core.loader import (
    LoadPlan,
    load_file_list,
    estimate_tokens,
    build_load_plan,
    render_context,
)


class TestLoadFileList:
    def test_parse_simple(self, tmp_path):
        idx = tmp_path / "MEMORY.md"
        idx.write_text(
            "# Index\n\n"
            "- [Title One](core/one.md) — desc #tag\n"
            "- [Title Two](core/two.md) — desc #tag\n",
            encoding="utf-8",
        )
        files = load_file_list(idx)
        assert "core/one.md" in files
        assert "core/two.md" in files

    def test_empty(self, tmp_path):
        idx = tmp_path / "MEMORY.md"
        idx.write_text("# Empty\n\nNo files here.\n", encoding="utf-8")
        assert load_file_list(idx) == []

    def test_missing(self):
        assert load_file_list("/nonexistent/MEMORY.md") == []


class TestEstimateTokens:
    def test_basic(self):
        assert estimate_tokens("hello world") == 2  # 2 words * 1.3 ≈ 2
        assert estimate_tokens("one two three four five") == 6  # 5 * 1.3 ≈ 6


class TestBuildLoadPlan:
    def test_always_layer(self, temp_store, default_config):
        default_config.store.path = str(temp_store)
        plan = build_load_plan(temp_store, default_config)
        # core/identity.md should be in the always-load core domain
        assert len(plan.files) >= 1
        assert any("identity" in f for f in plan.files)

    def test_trigger_layer(self, temp_store, default_config):
        default_config.store.path = str(temp_store)
        plan = build_load_plan(
            temp_store, default_config,
            conversation_text="I just finished eating lunch",
        )
        # trigger in triggers.md matches "finished eating"
        assert len(plan.files) >= 1

    def test_domain_layer(self, temp_store, default_config):
        # Add a second domain
        default_config.domains.append(
            type(default_config.domains[0])(
                name="code", index="MEMORY-code.md", always_load=False
            )
        )
        default_config.store.path = str(temp_store)

        # Create the domain index
        (temp_store / "MEMORY-code.md").write_text(
            "- [FP](code/fp.md) — functional style\n", encoding="utf-8"
        )
        (temp_store / "code").mkdir(exist_ok=True)
        (temp_store / "code" / "fp.md").write_text(
            "---\nname: fp\nweight: 4\ntags: [code]\n---\n# FP\n",
            encoding="utf-8",
        )

        plan = build_load_plan(
            temp_store, default_config,
            active_domains=["code"],
        )
        assert any("fp" in f for f in plan.files)

    def test_weight_layer(self, temp_store, default_config):
        default_config.store.path = str(temp_store)
        # Create a w=4 file not in any index
        (temp_store / "core" / "extra.md").write_text(
            "---\nname: extra\nweight: 4\ntags: [extra]\n---\n# Extra\n",
            encoding="utf-8",
        )

        plan = build_load_plan(temp_store, default_config)
        # w=4 file should be loaded by weight layer
        assert any("extra" in f for f in plan.files), (
            f"Expected extra.md in: {plan.files}"
        )

    def test_deduplication(self, temp_store, default_config):
        default_config.store.path = str(temp_store)
        plan = build_load_plan(temp_store, default_config)
        # No duplicates
        assert len(plan.files) == len(set(plan.files))

    def test_skips_archive(self, temp_store, default_config):
        default_config.store.path = str(temp_store)
        (temp_store / "archive" / "old.md").write_text(
            "---\nname: old\nweight: 1\ntags: [old]\n---\n# Old\n",
            encoding="utf-8",
        )
        plan = build_load_plan(temp_store, default_config)
        assert not any("old" in f for f in plan.files)


class TestRenderContext:
    def test_basic(self, temp_store, default_config):
        default_config.store.path = str(temp_store)
        plan = build_load_plan(temp_store, default_config)
        ctx = render_context(plan, temp_store)
        assert "Who Am I" in ctx
        assert "weight:" in ctx
