"""Validate structure and annotation relationships without scoring a model.

Truth, Chinese authorship, cultural suitability, and response adequacy require
human review. A pilot pass deliberately permits unapproved drafts.
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/w01_dialogue_case.schema.json"
DOMAINS = {"fari-en": 40, "fari-zh": 20, "senpai-en": 25, "senpai-zh": 15}
TIERS = ("easy", "medium", "hard")
EDGE_TYPES = {"mixed_language", "culturally_specific_zh", "no_relevant_context", "partial_context", "adversarial"}
RULES = {"easy": {"E1"}, "medium": {"M1", "M2"}, "hard": {"H1", "H2", "H3"}}
FARI_RUBRICS = {"fari_coherence", "fari_emotional_register"}
SENPAI_RUBRICS = {"senpai_correctness", "senpai_learner_suitability", "senpai_curriculum_alignment"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Non-finite JSON number: {value}")


def load_jsonl(path):
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line, object_pairs_hook=unique_object, parse_constant=reject_constant)
        except ValueError as exc:
            raise ValueError(f"Line {line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"Line {line_number}: expected a JSON object")
        records.append(record)
    return records


def string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from string_values(item)


def validate_records(records, profile="draft", schema=None):
    schema = schema if schema is not None else json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors, warnings, valid = [], [], []

    def fail(code, identifier, message):
        errors.append({"code": code, "case_id": identifier, "message": message})

    for index, record in enumerate(records, 1):
        identifier = record.get("id", f"record-{index}")
        failures = list(validator.iter_errors(record))
        if failures:
            for error in failures:
                location = "/".join(str(p) for p in error.absolute_path) or "record"
                fail("schema", identifier, f"{location}: {error.message}")
            continue
        valid.append(record)
        labels = record["evaluation_labels"]
        review = labels["review"]
        facts, passages, sources = labels["required_facts"], labels["passages"], labels["sources"]
        for field, items in [("fact_id", facts), ("passage_id", passages), ("source_id", sources)]:
            values = [item[field] for item in items]
            if len(set(values)) != len(values):
                fail("duplicate_annotation_id", identifier, f"Duplicate {field} within the record")
        passage_ids = {p["passage_id"] for p in passages}
        source_ids = {s["source_id"] for s in sources}
        indices = [p["context_index"] for p in passages]
        if sorted(indices) != list(range(len(record["context"]))):
            fail("passage_indices", identifier, "Passages must map once to every context string")
        for item in [*facts, *passages]:
            if not set(item["source_ids"]) <= source_ids:
                fail("source_reference", identifier, "An annotation cites an absent source")
        for f in facts:
            if not set(f["evidence_passage_ids"]) <= passage_ids:
                fail("evidence_reference", identifier, f"{f['fact_id']} cites an absent passage")
        if labels["expected_behavior"] not in labels["accepted_behaviors"]:
            fail("behavior", identifier, "Accepted behaviors must include the primary behavior")
        if review["difficulty_rule"] not in RULES[record["difficulty"]]:
            fail("tier_rule", identifier, "Difficulty and rule code disagree")
        if labels["query_language"] not in {record["language"], "mixed"}:
            fail("query_language", identifier, "Query language and primary language disagree")
        if labels["query_language"] == "mixed" and "mixed_language" not in labels["edge_case_tags"]:
            fail("mixed_tag", identifier, "Mixed queries require the mixed_language tag")
        suffix = "-base" if labels["record_kind"] == "base" else "-v[0-9]{2}"
        if not re.search(suffix + "$", identifier):
            fail("record_kind", identifier, "ID suffix and record kind disagree")
        supported = sum(f["context_support"] == "supported" for f in facts)
        condition, answerability = labels["context_condition"], labels["answerability"]
        if condition == "full" and supported != len(facts):
            fail("context_support", identifier, "Full context must support every reference fact")
        if condition == "partial" and not 0 < supported < len(facts):
            fail("context_support", identifier, "Partial context must support a nonempty proper subset")
        if condition == "none" and supported:
            fail("context_support", identifier, "None context must not support a requested reference fact")
        if answerability == "full" and supported != len(facts):
            fail("answerability", identifier, "Full answerability conflicts with reference support")
        if answerability == "partial" and not 0 < supported < len(facts):
            fail("answerability", identifier, "Partial answerability requires a supported proper subset")
        if answerability == "none" and supported:
            fail("answerability", identifier, "None answerability conflicts with supported facts")
        if any(f["context_support"] == "conflicting" for f in facts) and not labels["conflict_resolution"]:
            fail("conflict_rule", identifier, "Unresolved conflicting facts require an explicit behavior rule")
        if "no_relevant_context" in labels["edge_case_tags"] and supported:
            fail("edge_support", identifier, "No-relevant-context tag conflicts with supported facts")
        applicable = set(labels["rubric_criteria"])
        if record["domain"].startswith("fari"):
            if not applicable <= FARI_RUBRICS:
                fail("rubric_platform", identifier, "Fari case has a Senpai rubric")
            if "fari_coherence" in applicable:
                roles = {t["role"] for t in record.get("input_metadata", {}).get("dialogue_history", [])}
                if not {"user", "assistant"} <= roles:
                    fail("coherence_history", identifier, "Coherence requires prior user and assistant turns")
        elif applicable != SENPAI_RUBRICS:
            fail("rubric_platform", identifier, "Senpai cases require the three specified teaching criteria")
        if any(unicodedata.normalize("NFC", s) != s for s in string_values(record)):
            fail("unicode_nfc", identifier, "A string is not normalized to Unicode NFC")
        if profile == "release":
            if review["status"] != "approved" or labels["subset"] == "unassigned":
                fail("release_review", identifier, "Release requires approval and assigned subset")
            if not review["reviewer_ids"] or all(r in {"draft-reviewer", "automated-reviewer"} for r in review["reviewer_ids"]):
                fail("human_review", identifier, "An actual human reviewer is required for release")

    ids = [r["id"] for r in valid]
    for identifier, count in Counter(ids).items():
        if count > 1:
            fail("duplicate_case_id", identifier, "Case ID is repeated")
    lookup = {r["id"]: r for r in valid}
    families, provenance = defaultdict(set), {}
    for record in valid:
        labels = record["evaluation_labels"]
        families[labels["family_id"]].add(labels["subset"])
        for source in labels["sources"]:
            previous = provenance.setdefault(source["source_id"], source)
            if source != previous:
                fail("source_consistency", record["id"], "Source ID reused with different provenance")
        if labels["record_kind"] == "context_variant":
            parent = lookup.get(labels["base_case_id"])
            if parent is None or parent["evaluation_labels"]["record_kind"] != "base":
                fail("variant_parent", record["id"], "Variant needs an existing base parent")
                continue
            pl = parent["evaluation_labels"]
            for field in ["query", "domain", "language", "input_metadata"]:
                if record.get(field) != parent.get(field):
                    fail("variant_invariant", record["id"], f"Variant changed {field}")
            if labels["family_id"] != pl["family_id"] or labels["subset"] != pl["subset"]:
                fail("variant_invariant", record["id"], "Variant changed parent family or subset")
            keys = ["fact_id", "text", "equivalence_notes", "source_ids"]
            canonical = lambda fs: [{k: f[k] for k in keys} for f in fs]
            if canonical(labels["required_facts"]) != canonical(pl["required_facts"]):
                fail("variant_invariant", record["id"], "Variant changed canonical facts")
            if record["id"].rsplit("-", 1)[0] != parent["id"].rsplit("-", 1)[0]:
                fail("variant_id", record["id"], "Variant ID must use the parent's identifier")
    for family, subsets in families.items():
        if len(subsets) > 1:
            fail("family_leakage", family, "Family spans more than one subset")

    bases = [r for r in valid if r["evaluation_labels"]["record_kind"] == "base"]
    domains = Counter(r["domain"] for r in bases)
    tiers = Counter(r["difficulty"] for r in bases)
    cells = Counter(f"{r['domain']}/{r['difficulty']}" for r in bases)
    edges = Counter(tag for r in bases for tag in r["evaluation_labels"]["edge_case_tags"])
    edge_records = sum(bool(r["evaluation_labels"]["edge_case_tags"]) for r in bases)
    pending = sum(r["evaluation_labels"]["review"]["status"] != "approved" for r in valid)
    pending_zh = sum(r["language"] == "zh" and r["evaluation_labels"]["review"]["native_zh_review_status"] != "approved" for r in valid)
    if pending:
        warnings.append(f"{pending} records remain unapproved; structural validity is not release acceptance.")
    if pending_zh:
        warnings.append(f"{pending_zh} Chinese records still require native authorship and review.")
    if profile == "pilot":
        if len(valid) != 12 or len(bases) != 12:
            fail("pilot_size", None, "Pilot requires exactly twelve base records")
        for domain in DOMAINS:
            for tier in TIERS:
                if cells[f"{domain}/{tier}"] != 1:
                    fail("pilot_cell", None, f"Need one {domain}/{tier} pilot case")
        if any(r["evaluation_labels"]["subset"] != "calibration" for r in valid):
            fail("pilot_subset", None, "Pilot families belong to calibration")
    if profile in {"pilot", "release"}:
        for tag in sorted(EDGE_TYPES):
            if not edges[tag]:
                fail("edge_coverage", None, f"Required edge type absent: {tag}")
    if profile == "release":
        for domain, target in DOMAINS.items():
            if domains[domain] < target:
                fail("release_count", None, f"Need at least {target} base cases for {domain}")
            for tier in TIERS:
                if not cells[f"{domain}/{tier}"]:
                    fail("release_tier", None, f"Missing {domain}/{tier}")
        if edge_records < 10:
            fail("release_edges", None, "Need at least ten distinct tagged base cases")
    if not records:
        fail("empty_dataset", None, "Dataset is empty")
    return {
        "profile": profile, "valid": not errors, "errors": errors, "warnings": warnings,
        "record_count": len(records), "schema_valid_count": len(valid),
        "base_count": len(bases), "variant_count": len(valid) - len(bases),
        "family_count": len(families), "base_domain_counts": dict(domains),
        "base_difficulty_counts": dict(tiers), "base_cell_counts": dict(cells),
        "base_edge_tag_counts": dict(edges), "base_tagged_case_count": edge_records,
        "unapproved_count": pending, "pending_native_zh_count": pending_zh,
        "limitations": ["No automatic verification of factual truth or Chinese authorship.",
                        "No model generation, metrics, or production adapter boundary tests are run."],
    }


def check_manifest(dataset_path, manifest):
    actual = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    return actual == manifest.get("dataset_sha256")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--profile", choices=["draft", "pilot", "release"], default="draft")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        records = load_jsonl(args.dataset)
        report = validate_records(records, args.profile)
        report["dataset_sha256"] = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
        report["schema_sha256"] = hashlib.sha256(SCHEMA.read_bytes()).hexdigest()
        if args.manifest:
            manifest = json.loads(args.manifest.read_text())
            if not check_manifest(args.dataset, manifest):
                report["valid"] = False
                report["errors"].append({"code": "manifest_hash", "case_id": None, "message": "Dataset differs from the manifest hash; review changes and version the manifest."})
            if manifest.get("schema_sha256") != report["schema_sha256"]:
                report["valid"] = False
                report["errors"].append({"code": "manifest_schema_hash", "case_id": None, "message": "Schema differs from the manifest hash; review the contract and version the manifest."})
    except (ValueError, OSError) as exc:
        report = {"valid": False, "errors": [{"code": "input", "message": str(exc)}]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
