from memoir.core.triggers import (
    TriggerRule,
    TriggerTable,
    load_triggers,
    load_domain_triggers,
    match_triggers,
    match_tables,
    cascade,
)


class TestTriggerRule:
    def test_exact_match(self):
        rule = TriggerRule(
            phrases=["finished eating"],
            action="callback:remind_vitamins",
            source_file="feedback_vitamin",
            match_mode="exact",
        )
        assert rule.match("I just finished eating lunch")
        assert not rule.match("I am hungry")

    def test_stem_match(self):
        rule = TriggerRule(
            phrases=["immutab"],
            action="load-file:fp.md",
            source_file="code_fp",
            match_mode="stem",
        )
        assert rule.match("I prefer immutable data structures")
        assert not rule.match("mutable state")

    def test_phrase_match(self):
        rule = TriggerRule(
            phrases=["side effect"],
            action="load-file:fp.md",
            source_file="code_fp",
            match_mode="phrase",
        )
        assert rule.match("this function has a side effect")
        assert not rule.match("the effect is on the side")

    def test_regex_match(self):
        rule = TriggerRule(
            phrases=[r"python\s+3\.\d+"],
            action="load-file:python.md",
            source_file="code_python",
            match_mode="regex",
        )
        assert rule.match("I use python 3.12 for this project")
        assert not rule.match("python 2.7 is old")

    def test_fuzzy_match(self):
        rule = TriggerRule(
            phrases=["functional programming"],
            action="load-file:fp.md",
            source_file="code_fp",
            match_mode="fuzzy",
        )
        assert rule.match("functionnal programing")  # typos
        assert not rule.match("object oriented design")


class TestLoadTriggers:
    def test_parse_triggers_file(self, tmp_path):
        tf = tmp_path / "triggers.md"
        tf.write_text(
            "# My triggers\n"
            "finished eating → callback:remind → [[vitamin]]\n"
            "going to sleep → load-domain:core → [[closing]]\n"
            "/going (to|for) (sleep|bed)/ → load-file:sleep.md → [[sleep]]\n"
            "~functoinal programing~ → load-domain:code → [[fp]]\n",
            encoding="utf-8",
        )

        rules = load_triggers(tf)
        assert len(rules) == 4

        # Exact/stem
        assert rules[0].match_mode == "phrase"
        assert rules[0].action == "callback:remind"

        # Regex
        assert rules[2].match_mode == "regex"
        assert rules[2].phrases[0] == r"going (to|for) (sleep|bed)"

        # Fuzzy
        assert rules[3].match_mode == "fuzzy"

    def test_missing_file(self):
        assert load_triggers("/nonexistent/triggers.md") == []


class TestLoadDomainTriggers:
    def test_parse_trigger_table(self, tmp_path):
        idx = tmp_path / "MEMORY-code.md"
        idx.write_text(
            "# Code Domain\n\n"
            "## Patterns\n"
            "- [FP](fp.md) — functional programming\n\n"
            "## Trigger Table\n"
            "| #Concept | Keywords | → Files |\n"
            "|---|---|---|\n"
            "| fp | pure, immutab, side effect | fp.md |\n"
            "| naming | rename, variable, function | naming.md |\n",
            encoding="utf-8",
        )

        tables = load_domain_triggers(idx)
        assert len(tables) == 2
        assert tables[0].concept == "fp"
        assert "immutab" in tables[0].keywords
        assert "fp.md" in tables[0].target_files


class TestMatch:
    def test_match_triggers(self):
        rules = [
            TriggerRule(["sleep"], "load-domain:core", "src", "stem"),
            TriggerRule(["eat"], "callback:remind", "src", "stem"),
        ]
        matched = match_triggers("I am going to sleep now", rules)
        assert len(matched) == 1
        assert matched[0].action == "load-domain:core"

    def test_match_tables(self):
        tables = [
            TriggerTable("fp", ["pure", "immutab"], ["fp.md"]),
            TriggerTable("naming", ["rename", "variable"], ["naming.md"]),
        ]
        matched = match_tables("I prefer immutable data", tables)
        assert len(matched) == 1
        assert matched[0].concept == "fp"


class TestCascade:
    def test_load_file(self):
        rules = [TriggerRule(["x"], "load-file:target.md", "src", "stem")]
        files = cascade(rules, [])
        assert "target.md" in files

    def test_load_domain(self):
        rules = [TriggerRule(["x"], "load-domain:code", "src", "stem")]
        domain_files = {"code": ["a.md", "b.md"]}
        files = cascade(rules, [], index_files=domain_files)
        assert "a.md" in files
        assert "b.md" in files

    def test_table_files(self):
        tables = [TriggerTable("fp", ["pure"], ["fp.md", "fp2.md"])]
        files = cascade([], tables)
        assert "fp.md" in files
        assert "fp2.md" in files
