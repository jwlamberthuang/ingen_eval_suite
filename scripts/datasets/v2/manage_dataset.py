"""Validate v2 drafts, assemble lossless previews, and apply guarded review edits.

The JSONL is authoritative. Construction never grants review approval. This module
lives below v2/ so the frozen v1 construction-input glob remains unchanged.
"""

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.extended_evaluator import score_extended_case  # noqa: E402

CONFIG = ROOT / "configs/dataset-v2.json"
LEGACY_URI = "urn:ingen-eval-suite:w01-case:1.1.0"

# Evidence describes a scene independently of the dialogue speaker. The frozen
# v1 cohort is exempt; only new records pass through semantic_errors.
EVIDENCE_PRONOUNS = re.compile(
    r"\b(?:I|me|my|mine|myself|we|us|our|ours|ourselves|you|your|yours|yourself|"
    r"yourselves|he|him|his|himself|she|her|hers|herself|they|them|their|theirs|"
    r"themselves|it|its|itself)\b|(?<!其)[你您我他她它](?:们)?", re.IGNORECASE)


def evidence_referent_errors(record):
    """Flag personal pronouns in evidence/event labels, never in dialogue.

    This conservative lexical check does not prove that names and noun phrases
    are unambiguous. Chinese 其他 is not a personal-pronoun occurrence.
    """
    fields = [(f"context[{i}]", value) for i, value in enumerate(record["context"])]
    fields += [(f"event_descriptions.{key}", value) for key, value in
               record["task_input"].get("event_descriptions", {}).items()]
    return [f"Explicit evidence referent required in {field}: {match.group(0)}"
            for field, value in fields if (match := EVIDENCE_PRONOUNS.search(value))]


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def loads(text):
    def reject(value):
        raise ValueError(f"Nonfinite JSON number: {value}")
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def records_bytes(records):
    return "".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n"
                   for r in records).encode()


def read_records(path):
    raw = Path(path).read_bytes()
    if not raw.endswith(b"\n"):
        raise ValueError("JSONL must end with a newline")
    lines = raw.decode("utf-8").splitlines()
    if any(not line.strip() for line in lines):
        raise ValueError("Blank JSONL lines are not permitted")
    return [loads(line) for line in lines], raw


def config():
    return loads(CONFIG.read_text())


def content_hash(record):
    """Bind review to all substantive fields, excluding the review attestation."""
    value = deepcopy(record)
    value["annotations"].pop("review")
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode())


def schema_validator():
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource

    cfg = config()
    legacy = loads((ROOT / cfg["legacy_schema"]).read_text())
    schema = loads((ROOT / cfg["schema"]).read_text())
    registry = Registry().with_resource(LEGACY_URI, Resource.from_contents(legacy))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def expected_prediction(record):
    """An annotation smoke fixture, never a model generation or quality result."""
    kind, ref = record["evaluation_type"], record["reference"]
    if kind == "stum_spatial":
        return {"relation": ref["answer"]}
    if kind == "stum_temporal":
        return {"relations": [{"pair_id": k, "relation": v} for k, v in ref["answers"].items()]}
    if kind == "seom_entities":
        return {"entities": [{"mention": e["aliases"][0], "class": e["class"]}
                             for e in ref["entities"]]}
    if kind == "htd_task_alignment":
        pending, done, tasks = list(ref["goals"]), set(), []
        while pending:
            ready = next((g for g in pending if set(g["after"]) <= done), None)
            if ready is None:
                raise ValueError("Goal precedence does not resolve")
            tasks.append(deepcopy(ready["templates"][0]))
            done.add(ready["goal_id"])
            pending.remove(ready)
        return {"tasks": tasks}
    raise ValueError("RAG has a natural-language reference, not structured output")


def rag_errors(record):
    ref = record["reference"]
    errors = []
    sources = [s["source_id"] for s in ref["sources"]]
    passages = [p["passage_id"] for p in ref["passages"]]
    facts = [f["fact_id"] for f in ref["required_facts"]]
    if any(len(values) != len(set(values)) for values in (sources, passages, facts)):
        errors.append("Duplicate RAG source, passage, or fact ID")
    if sorted(p["context_index"] for p in ref["passages"]) != list(range(len(record["context"]))):
        errors.append("Passages must cover context indices exactly once")
    for item in ref["passages"] + ref["required_facts"]:
        if not set(item["source_ids"]) <= set(sources):
            errors.append("Unresolved RAG source link")
    for fact in ref["required_facts"]:
        if not set(fact["evidence_passage_ids"]) <= set(passages):
            errors.append("Unresolved RAG evidence link")
    if ref["expected_behavior"] not in ref["accepted_behaviors"]:
        errors.append("Primary RAG behavior must be accepted")
    if record["annotations"]["provenance"]["source_id"] not in sources:
        errors.append("Provenance source must resolve in RAG references")
    if record["annotations"]["allocation_group"] == "adversarial_rag" and not ref["metric_probes"]:
        errors.append("Adversarial RAG requires a fixed metric probe")
    probe_ids = [p["probe_id"] for p in ref["metric_probes"]]
    if len(set(probe_ids)) != len(probe_ids):
        errors.append("Duplicate metric probe ID")
    for probe in ref["metric_probes"]:
        fraction = sum(c["support"] == "supported" for c in probe["claims"]) / len(probe["claims"])
        if abs(fraction - probe["ideal_property_score"]) > 1e-12:
            errors.append("Probe ideal faithfulness must match manually labeled claim fraction")
    return errors


def semantic_errors(record):
    cfg, errors = config(), []
    errors.extend(evidence_referent_errors(record))
    kind, ann = record["evaluation_type"], record["annotations"]
    marker = f"w03-{kind.replace('_', '-')}-{record['domain']}-"
    if not record["id"].startswith(marker) or record["domain"].split("-")[-1] != record["language"]:
        errors.append("ID, type, domain, and language disagree")
    if record["id"].split("-")[-2] != ann["family_id"].split("-")[-1]:
        errors.append("New base ID must identify its scenario family")
    expected_group = {"stum_spatial": "stum", "stum_temporal": "stum",
                      "seom_entities": "seom", "htd_task_alignment": "htd"}.get(kind)
    if (expected_group and ann["allocation_group"] != expected_group or
            kind == "rag" and ann["allocation_group"] not in {"hard_rag", "adversarial_rag", "targeted_rag"}):
        errors.append("Allocation group does not match task type")
    if ann["allocation_group"] == "hard_rag" and record["difficulty"] != "hard":
        errors.append("Hard RAG allocation requires a Hard case")
    if ann["difficulty_rule"][0].lower() != record["difficulty"][0]:
        errors.append("Difficulty rule and tier disagree")

    def evidence(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "evidence_indices" and any(i >= len(record["context"]) for i in item):
                    errors.append("Evidence index outside visible context")
                evidence(item)
        elif isinstance(value, list):
            for item in value:
                evidence(item)
    evidence(record["reference"])
    if kind == "rag":
        errors.extend(rag_errors(record))
    else:
        try:
            output = json.dumps(expected_prediction(record), ensure_ascii=False)
            score = score_extended_case(record, output)
            if score["status"] != "ok" or score["task_success"]["value"] != 1:
                errors.append("Symbolic reference or expected-output smoke fixture fails")
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f"Invalid structured reference: {exc}")
        if kind == "stum_temporal":
            task = record["task_input"]
            if set(task["event_descriptions"]) != set(task["events"]):
                errors.append("Every temporal event needs a visible description")
        if kind == "seom_entities" and record["task_input"]["classes"] != cfg["entity_classes"]:
            errors.append("Class vocabulary differs from construction configuration")
        if kind == "htd_task_alignment" and record["task_input"]["action_catalog"] != cfg["action_catalog"]:
            errors.append("Action vocabulary differs from construction configuration")
    review = ann["review"]
    if record["language"] == "en":
        if (review["native_zh_authorship_status"] != "not_applicable" or
                review["native_zh_review_status"] != "not_applicable" or review["native_zh_author_id"] is not None):
            errors.append("English case has inconsistent Chinese review metadata")
    else:
        if "not_applicable" in (review["native_zh_authorship_status"], review["native_zh_review_status"]):
            errors.append("Chinese case requires native authorship and review status")
        if review["native_zh_authorship_status"] == "confirmed" and not review["native_zh_author_id"]:
            errors.append("Confirmed Chinese authorship needs an actual author identifier")
    if review["status"] == "approved":
        if not review["reviewer_ids"] or not review["reviewed_on"] or review["content_sha256"] != content_hash(record):
            errors.append("Approval must identify reviewer/date and match current content hash")
        if record["language"] == "zh" and (review["native_zh_authorship_status"] != "confirmed" or
                                            review["native_zh_review_status"] != "approved"):
            errors.append("Chinese approval requires confirmed native authorship and review")
    return errors


def validate_records(records, profile="draft", raw=None):
    if profile not in {"draft", "pilot", "collection", "release"}:
        raise ValueError("Unknown validation profile")
    cfg, validator = config(), schema_validator()
    original, legacy_raw = read_records(ROOT / cfg["legacy_dataset"])
    legacy = {r["id"]: r for r in original}
    errors, warnings, new, old_ids, families = [], [], [], [], defaultdict(set)
    if digest(legacy_raw) != cfg["legacy_sha256"]:
        errors.append("Frozen legacy dataset checksum changed")
    if digest((ROOT / cfg["legacy_schema"]).read_bytes()) != cfg["legacy_schema_sha256"]:
        errors.append("Frozen legacy schema checksum changed")
    identifiers = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"Line {index + 1}: record must be an object")
            continue
        identifier = record.get("id", f"line-{index + 1}")
        identifiers.append(identifier)
        problems = list(validator.iter_errors(record))
        if problems:
            details = problems[0].context or problems
            errors.append(f"{identifier}: schema: " + "; ".join(e.message for e in details[:4]))
            continue
        if "evaluation_type" not in record:
            if identifier not in legacy or record != legacy[identifier]:
                errors.append(f"{identifier}: legacy compatibility accepts only unchanged original records")
            old_ids.append(identifier)
            continue
        new.append(record)
        errors.extend(f"{identifier}: {message}" for message in semantic_errors(record))
        ann, review = record["annotations"], record["annotations"]["review"]
        families[ann["family_id"]].add(ann["subset"])
        if review["status"] != "approved":
            (errors if profile == "release" else warnings).append(f"{identifier}: review pending")
        if record["language"] == "zh" and (review["native_zh_authorship_status"] != "confirmed" or
                                            review["native_zh_review_status"] != "approved"):
            (errors if profile == "release" else warnings).append(f"{identifier}: native Chinese authorship/review pending")
    if len(set(identifiers)) != len(identifiers):
        errors.append("Duplicate case ID")
    if len(families) != len(new):
        errors.append("Additions must be distinct new scenario families, not variants")
    if any(len(subsets) != 1 for subsets in families.values()):
        errors.append("Scenario family crosses evaluation subsets")
    bytes_checked = False
    if old_ids:
        if old_ids != [r["id"] for r in original] or len(records) < len(original):
            errors.append("Legacy collection must include all 100 original cases in original order")
        if raw is None or not raw.startswith(legacy_raw):
            errors.append("Legacy prefix must preserve original line bytes exactly")
        else:
            bytes_checked = True
    counts = lambda field: dict(sorted(Counter(r[field] for r in new).items()))
    groups = Counter(r["annotations"]["allocation_group"] for r in new)
    subsets = Counter(r["annotations"]["subset"] for r in new)
    if profile == "pilot":
        if len(records) != cfg["pilot_count"] or len(new) != cfg["pilot_count"]:
            errors.append("Pilot requires exactly twelve new cases")
        if identifiers != cfg["pilot_case_ids"]:
            errors.append("Pilot IDs/order differ from the construction configuration")
        if subsets != {"calibration": cfg["pilot_count"]}:
            errors.append("Pilot must remain entirely in calibration")
        if set(counts("evaluation_type")) != set(cfg["new_targets"]["types"]):
            errors.append("Pilot must cover every evaluation type")
    for name, group in cfg["new_targets"]["groups"].items():
        members = [r for r in new if r["annotations"]["allocation_group"] == name]
        for key in ("count", "en", "zh", "calibration", "held_out"):
            actual = len(members) if key == "count" else sum(
                (r["language"] if key in {"en", "zh"} else r["annotations"]["subset"]) == key
                for r in members)
            if actual > group[key] or profile in {"collection", "release"} and actual != group[key]:
                errors.append(f"Allocation mismatch: {name}/{key}: {actual}, target {group[key]}")
    if profile in {"collection", "release"}:
        if len(records) != 200 or len(new) != 100 or len(old_ids) != 100:
            errors.append("Collection/release requires 100 preserved legacy plus 100 new cases")
        for target, field in (("languages", "language"), ("domains", "domain"),
                              ("difficulty", "difficulty"), ("types", "evaluation_type")):
            if counts(field) != cfg["new_targets"][target]:
                errors.append(f"Collection/release {target} allocation mismatch")
        pilot, pilot_raw = read_records(ROOT / cfg["pilot"])
        if new[:len(pilot)] != pilot or raw is None or not raw.startswith(legacy_raw + pilot_raw):
            errors.append("Collection must preserve the revised pilot content, order, and original line bytes")
        for subset in ("calibration", "held_out"):
            selected = [r["id"] for r in new if r["annotations"]["subset"] == subset]
            if selected != cfg["split_policy"][f"new_{subset}_case_ids"]:
                errors.append(f"Collection {subset} IDs/order differ from the recorded family allocation")
        hard_tags = {tag for r in new if r["annotations"]["allocation_group"] == "hard_rag"
                     for tag in r["annotations"]["edge_case_tags"]}
        if not {"hallucination", "out_of_domain"} <= hard_tags:
            errors.append("Hard RAG must include hallucination and out-of-domain probes")
    return {"valid": not errors, "profile": profile, "record_count": len(records),
            "legacy_count": len(old_ids), "new_count": len(new), "legacy_bytes_checked": bytes_checked,
            "new_type_counts": counts("evaluation_type"), "new_language_counts": counts("language"),
            "new_domain_counts": counts("domain"), "new_difficulty_counts": counts("difficulty"),
            "new_group_counts": dict(sorted(groups.items())), "new_subset_counts": dict(sorted(subsets.items())),
            "unapproved_count": sum(r["annotations"]["review"]["status"] != "approved" for r in new),
            "pending_native_zh_count": sum(r["language"] == "zh" and
                (r["annotations"]["review"]["native_zh_authorship_status"] != "confirmed" or
                 r["annotations"]["review"]["native_zh_review_status"] != "approved") for r in new),
            "release_ready": profile == "release" and not errors,
            "errors": errors, "warnings": warnings,
            "limitations": ["Schema and symbolic checks do not establish natural-language truth, scenario originality, authorship, or human review.",
                            "Reference smoke outputs are annotation fixtures, not measured model responses."]}


def make_manifest(dataset_path, raw, report):
    cfg = config()
    inputs = [CONFIG, ROOT / cfg["schema"], ROOT / cfg["legacy_schema"],
              ROOT / "src/extended_evaluator.py", Path(__file__).resolve()]
    if report["legacy_count"]:
        inputs.append(ROOT / cfg["pilot"])
    elif "collection" in cfg and (ROOT / cfg["collection"]).exists():
        inputs.append(ROOT / cfg["collection"])
    return {"dataset_file": Path(dataset_path).name, "dataset_sha256": digest(raw),
            "schema_version": cfg["schema_version"], "schema_file": cfg["schema"],
            "schema_sha256": digest((ROOT / cfg["schema"]).read_bytes()),
            "legacy_dataset": cfg["legacy_dataset"], "legacy_dataset_sha256": cfg["legacy_sha256"],
            "status": ("release" if report["release_ready"] else "reviewed_subset" if
                       not report["unapproved_count"] and not report["pending_native_zh_count"] else "review_draft"),
            "validation": report,
            "construction_inputs": [{"file": str(p.relative_to(ROOT)), "sha256": digest(p.read_bytes())}
                                    for p in inputs]}


def verify_manifest(manifest, dataset_path, raw, report):
    return manifest == make_manifest(dataset_path, raw, report)


def write_new(path, payload):
    """Exclusive creation protects canonical data, reviewed edits, and old artifacts."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)


def assemble(additions, output):
    records, added_raw = read_records(additions)
    if any("evaluation_type" not in r for r in records):
        raise ValueError("Additions must contain only explicitly typed new cases")
    cfg = config()
    legacy, legacy_raw = read_records(ROOT / cfg["legacy_dataset"])
    combined = legacy_raw + added_raw
    report = validate_records(legacy + records, "draft", combined)
    if not report["valid"]:
        raise ValueError(report["errors"])
    write_new(output, combined)
    return report


def reproduce_collection(output_dir):
    """Reproduce the master, derived pilot, and manifests in a fresh directory."""
    cfg = config()
    collection_path = ROOT / cfg["collection"]
    records, raw = read_records(collection_path)
    report = validate_records(records, "collection", raw)
    if not report["valid"]:
        raise ValueError(report["errors"])
    selected = set(cfg["pilot_case_ids"])
    pilot_raw = b"".join(line for r, line in zip(records, raw.splitlines(keepends=True))
                         if r["id"] in selected)
    pilot_records = [r for r in records if r["id"] in selected]
    pilot_report = validate_records(pilot_records, "pilot", pilot_raw)
    if not pilot_report["valid"]:
        raise ValueError(pilot_report["errors"])
    output_dir = Path(output_dir)
    # Reserve a fresh directory before writing any output.
    output_dir.mkdir(parents=True, exist_ok=False)
    for source, payload, validation in ((collection_path, raw, report),
                                        (ROOT / cfg["pilot"], pilot_raw, pilot_report)):
        target = output_dir / source.name
        write_new(target, payload)
        previous = loads(source.with_suffix(".manifest.json").read_text())
        profile = previous["validation"]["profile"]
        current = validate_records(records if source == collection_path else pilot_records, profile, payload)
        if not current["valid"] or not verify_manifest(previous, source, payload, current):
            raise ValueError("Rebuild requires a valid current manifest with its original profile")
        write_new(target.with_suffix(".manifest.json"), source.with_suffix(".manifest.json").read_bytes())
    return report


def apply_edits(source, edits_path, output):
    """Apply explicit before/after field edits to a new preview; reset attestations."""
    records, raw = read_records(source)
    edits = loads(Path(edits_path).read_text())
    if edits["base_sha256"] != digest(raw):
        raise ValueError("Edit base hash does not match current source")
    by_id = {r["id"]: r for r in records}
    changed = set()
    allowed = {"query", "context", "input_metadata", "task_input", "reference", "construction_notes"}
    for edit in edits["edits"]:
        record = by_id[edit["id"]]
        path = edit["path"]
        if "evaluation_type" not in record or not isinstance(path, list) or not path or path[0] not in allowed:
            raise ValueError("Edits cannot change legacy records, identity, split, or review attestations")
        parent = record
        for component in path[:-1]:
            parent = parent[component]
        if parent[path[-1]] != edit["before"]:
            raise ValueError("Edit before-value mismatch")
        parent[path[-1]] = edit["after"]
        changed.add(record["id"])
        review = record["annotations"]["review"]
        review.update(status="draft", reviewer_ids=[], reviewed_on=None, content_sha256=None,
                      notes="Content edited; annotation and language review must be renewed.")
        if record["language"] == "zh":
            review.update(native_zh_authorship_status="pending", native_zh_author_id=None,
                          native_zh_review_status="pending")
    output_raw = b"".join(records_bytes([r]) if r["id"] in changed else line
                          for r, line in zip(records, raw.splitlines(keepends=True)))
    report = validate_records(records, "draft", output_raw)
    if not report["valid"]:
        raise ValueError(report["errors"])
    write_new(output, output_raw)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("dataset", type=Path)
    validate.add_argument("--profile", choices=("draft", "pilot", "collection", "release"), default="draft")
    validate.add_argument("--manifest", type=Path)
    validate.add_argument("--report", type=Path)
    manifest = commands.add_parser("manifest")
    manifest.add_argument("dataset", type=Path)
    manifest.add_argument("--profile", choices=("draft", "pilot", "collection", "release"), default="pilot")
    manifest.add_argument("--output", type=Path, required=True)
    preview = commands.add_parser("assemble")
    preview.add_argument("additions", type=Path)
    preview.add_argument("--output", type=Path, required=True)
    build = commands.add_parser("build")
    build.add_argument("--output-dir", type=Path, required=True)
    update = commands.add_parser("update")
    update.add_argument("source", type=Path)
    update.add_argument("--edits", type=Path, required=True)
    update.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "assemble":
            report = assemble(args.additions, args.output)
        elif args.command == "build":
            report = reproduce_collection(args.output_dir)
        elif args.command == "update":
            report = apply_edits(args.source, args.edits, args.output)
        else:
            records, raw = read_records(args.dataset)
            report = validate_records(records, args.profile, raw)
            if args.command == "manifest":
                if not report["valid"]:
                    raise ValueError(report["errors"])
                write_new(args.output, json_bytes(make_manifest(args.dataset, raw, report)))
            elif args.manifest and not verify_manifest(loads(args.manifest.read_text()), args.dataset, raw, report):
                report["valid"] = False
                report["release_ready"] = False
                report["errors"].append("Manifest differs from dataset/schema/tooling or validation profile")
            if args.command == "validate" and args.report:
                write_new(args.report, json_bytes(report))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["valid"] else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
