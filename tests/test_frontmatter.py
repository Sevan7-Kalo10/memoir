from memoir.core.frontmatter import parse, write, extract_tags, validate


class TestParse:
    def test_parse_valid_frontmatter(self, sample_memory):
        fm, body = parse(sample_memory)
        assert fm["name"] == "test-memory"
        assert fm["weight"] == 4
        assert fm["tags"] == ["test", "unit"]
        assert "Test Memory" in body

    def test_parse_no_frontmatter(self, tmp_path):
        mem = tmp_path / "plain.md"
        mem.write_text("# Just a header\n\nSome content.\n", encoding="utf-8")
        fm, body = parse(mem)
        assert fm == {}
        assert "Just a header" in body

    def test_parse_empty_frontmatter(self, tmp_path):
        mem = tmp_path / "empty.md"
        mem.write_text("---\n---\nBody here.\n", encoding="utf-8")
        fm, body = parse(mem)
        assert fm == {}
        assert "Body here" in body

    def test_parse_invalid_yaml(self, tmp_path):
        mem = tmp_path / "bad.md"
        mem.write_text("---\n{\n---\nBody.\n", encoding="utf-8")
        fm, body = parse(mem)
        assert fm == {}
        assert "Body" in body

    def test_parse_missing_file(self):
        try:
            parse("/nonexistent/path.md")
        except FileNotFoundError:
            pass


class TestWrite:
    def test_write_creates_file(self, tmp_path):
        mem = tmp_path / "new.md"
        fm = {"name": "new", "weight": 3, "tags": ["test"]}
        write(mem, fm, "# New\n\nContent.")
        assert mem.exists()
        fm2, body2 = parse(mem)
        assert fm2["name"] == "new"
        assert "updated" in fm2

    def test_write_creates_bak(self, sample_memory):
        fm = {"name": "updated", "weight": 2, "tags": ["test"]}
        write(sample_memory, fm, "# Updated")
        bak = sample_memory.with_suffix(".md.bak")
        assert bak.exists()


class TestExtractTags:
    def test_normal_list(self):
        tags = extract_tags({"tags": ["Python", "Code", "python"]})
        assert tags == ["python", "code"]

    def test_empty(self):
        assert extract_tags({}) == []

    def test_not_a_list(self):
        assert extract_tags({"tags": "not-a-list"}) == []


class TestValidate:
    def test_valid(self):
        fm = {"name": "x", "weight": 3, "tags": ["a"]}
        assert validate(fm) == []

    def test_missing_required(self):
        assert len(validate({"name": "x"})) >= 2  # missing weight, tags

    def test_bad_weight(self):
        fm = {"name": "x", "weight": 10, "tags": ["a"]}
        assert any("weight" in e for e in validate(fm))

    def test_bad_tags(self):
        fm = {"name": "x", "weight": 3, "tags": "not-list"}
        assert any("tags" in e for e in validate(fm))
