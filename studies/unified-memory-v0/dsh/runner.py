#!/usr/bin/env python3
"""Study-owned DSH launcher. No profile boot, receipt emission, or scoring."""
import argparse
import hashlib
import json
import os
import resource
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

QUESTION_IDS = ("exact-identifier", "supersession", "cross-harness", "contradiction", "missing-evidence", "minimal-context")
EVIDENCE_FIELDS = ("slot", "source_id", "source_version", "trust_class", "locator", "origin_harness", "origin_session_id", "key", "text")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


class Refusal(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def validate_plan(plan, approval, runtime_hash, contract):
    """Validate the parent's hash-bound whole cohort, then allowlist model input.

    Approval custody is the caller's responsibility; a local hash is integrity,
    not authentication against a malicious same-UID process.
    """
    require(approval.get("schema") == "z0eval.dsh_approval.v1" and approval.get("preflight_passed") is True, "APPROVAL_INVALID")
    require(plan.get("schema") == "z0eval.unified_memory_run_plan.v1" and plan.get("preflight_passed") is True, "PREFLIGHT_REQUIRED")
    require(approval.get("plan_sha256") == digest(plan), "PLAN_HASH_MISMATCH")
    require(approval.get("runtime_pin_sha256") == runtime_hash, "RUNTIME_HASH_MISMATCH")
    require(plan.get("contract_sha256") == approval.get("contract_sha256") == digest(contract), "CONTRACT_HASH_MISMATCH")
    for key in ("binding_id", "binding_sha256", "source_versions"):
        require(bool(plan.get(key)) and plan[key] == approval.get(key), "BINDING_MISMATCH")
    require(contract.get("schema") == "z0eval.unified_memory_case_contract.v1"
            and tuple(q.get("question_id") for q in contract["questions"]) == QUESTION_IDS, "CONTRACT_CHANGED")
    cases = plan.get("cases", [])
    require(tuple(c.get("question_id") for c in cases[:6]) == QUESTION_IDS
            and all(c.get("variant") == "canonical" for c in cases[:6]), "SIX_CASES_REQUIRED")
    require(approval.get("question_ids") == list(QUESTION_IDS), "SIX_APPROVALS_REQUIRED")
    controls = cases[6:] + plan.get("controls", [])
    require(len(cases) >= 6, "SIX_CASES_REQUIRED")
    require(set(plan["source_versions"]) == set(contract["source_slots"]), "SOURCE_VERSIONS_REQUIRED")
    canonical_sources = {}
    safe_cases = []
    for case, question in zip(cases[:6], contract["questions"], strict=True):
        require(case.get("variant") == "canonical", "UNSUPPORTED_VARIANT")
        missing = ["identifier"] if case["question_id"] == "missing-evidence" else []
        require(case.get("intentional_missing_slots") == missing, "OMISSION_MISMATCH")
        require([e.get("slot") for e in case["evidence"]] == [s for s in question["required_source_slots"] if s not in missing], "EVIDENCE_SLOTS_MISMATCH")
        safe = {key: case[key] for key in ("question_id", "variant", "prompt_id", "prompt", "intentional_missing_slots")}
        safe["evidence"] = []
        for evidence in case["evidence"]:
            require(all(isinstance(evidence.get(k), str) and evidence[k] for k in EVIDENCE_FIELDS), "EVIDENCE_FIELD_MISSING")
            item = {k: evidence[k] for k in EVIDENCE_FIELDS}
            slot = item["slot"]
            require(item["source_version"] == plan["source_versions"][slot], "SOURCE_REVISION_MISMATCH")
            require(slot not in canonical_sources or item == canonical_sources[slot], "SOURCE_PACKET_MISMATCH")
            canonical_sources[slot] = item
            safe["evidence"].append(item)
        safe_cases.append(safe)
    for case, question in zip(safe_cases, contract["questions"], strict=True):
        prompt = question["prompt_template"]
        for slot, source in canonical_sources.items():
            prompt = prompt.replace("{" + slot + ".fact.key}", source["key"])
        prompt += "\n\n" + contract["response_instruction"]
        require(case["prompt"] == prompt and case["prompt_id"] == case["question_id"] + ":" + hashlib.sha256(prompt.encode()).hexdigest(), "PROMPT_MISMATCH")
    variants = {"supersession-old-only": ("supersession", ["state_old"], ["state_new"]),
                "supersession-after-new": ("supersession", ["state_old", "state_new"], []),
                "missing-evidence-mutation": ("exact-identifier", [], ["identifier"])}
    seen_variants = set()
    for control in controls:
        variant = control.get("variant")
        require(variant in variants and variant not in seen_variants, "UNSUPPORTED_OR_DUPLICATE_CONTROL")
        seen_variants.add(variant)
        qid, supplied, missing = variants[variant]
        base = next(c for c in safe_cases[:6] if c["question_id"] == qid)
        require(control.get("question_id") == qid and control.get("prompt") == base["prompt"] and control.get("prompt_id") == base["prompt_id"], "CONTROL_PROMPT_MISMATCH")
        require(control.get("intentional_missing_slots") == missing and control.get("evidence") == [canonical_sources[s] for s in supplied], "CONTROL_EVIDENCE_MISMATCH")
        safe_cases.append({**base, "variant": variant, "evidence": [canonical_sources[s] for s in supplied], "intentional_missing_slots": missing})
    return {"cases": safe_cases, "plan_sha256": digest(plan),
            "contract_sha256": plan["contract_sha256"], "binding_sha256": plan["binding_sha256"],
            "binding_id": plan["binding_id"], "source_versions": plan["source_versions"]}


def validate_source_preflight(proof, payload, runtime_hash, approval_hash):
    require(proof.get("schema") == "z0eval.dsh_stage_capture.v1" and proof.get("mode") == "preflight"
            and proof.get("status") == "no-model-preflight", "SOURCE_PREFLIGHT_REQUIRED")
    require(proof.get("runtime_sha256") == runtime_hash and proof.get("approval_sha256") == approval_hash, "SOURCE_PREFLIGHT_IDENTITY_MISMATCH")
    for key in ("plan_sha256", "binding_sha256", "contract_sha256"):
        require(proof.get(key) == payload[key], "SOURCE_PREFLIGHT_IDENTITY_MISMATCH")
    require(proof.get("native_fetch_calls") == 0 and proof.get("fetch_boundary_calls") == 0 and proof.get("neutral_requests") == 0
            and proof.get("configuration_unchanged") is True, "SOURCE_PREFLIGHT_NOT_NO_MODEL")
    require(len(proof.get("cases", [])) == len(payload["cases"]), "SOURCE_PREFLIGHT_INCOMPLETE")
    for case, observed in zip(payload["cases"], proof["cases"], strict=True):
        require(all(observed.get(k) == case[k] for k in ("question_id", "variant", "prompt_id")), "SOURCE_PREFLIGHT_CASE_MISMATCH")
        packet = {"evidence": case["evidence"], "intentional_missing_slots": case["intentional_missing_slots"]}
        require(observed.get("packet_sha256") == digest(packet) and observed.get("assembly_calls") == 1
                and observed.get("pre_step_calls") == 1 and observed.get("system_admissions") == 0
                and observed.get("neutral_requests") == 0 and observed.get("turn_end_kind") == "blocked"
                and observed.get("status") == "no-model-preflight", "SOURCE_PREFLIGHT_CASE_FAILED")


SOURCE_HEAD = "8acd443c91b679e3f4fabf6f66639e8ebe38ce97"
BUN = Path("/home/kvn/.bun/bin/bun")
BUN_SHA256 = "9fd36f87e4b90b07632b987a2e4ec81ca15a62c81bf983190cea6d715be2ad74"
BORROWED = "/usr/lib/node_modules/@deepseek-ai/dsh/node_modules"


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def private_json(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def source_runtime(root):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    require(git("rev-parse", "HEAD") == SOURCE_HEAD, "SOURCE_HEAD_MISMATCH")
    require(not git("status", "--porcelain", "--untracked-files=all"), "SOURCE_DIRTY")
    require(file_hash(BUN) == BUN_SHA256, "BUN_HASH_MISMATCH")
    require(subprocess.check_output([str(BUN), "--version"], text=True).strip() == "1.3.14", "BUN_VERSION_MISMATCH")
    return {"source_head": SOURCE_HEAD, "source_root": str(root),
            "bun": {"path": str(BUN.resolve()), "version": "1.3.14", "sha256": BUN_SHA256},
            "launcher_sha256": file_hash(__file__), "program_sha256": file_hash(HERE / "runtime.mjs"),
            "resolution_files": {str(root / p): file_hash(root / p) for p in ("tsconfig.json", "tsconfig.base.json", "pnpm-lock.yaml", "package.json")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "run", "seam"), default="preflight")
    parser.add_argument("--plan")
    parser.add_argument("--approval")
    parser.add_argument("--approved-approval-sha256", help="Parent-supplied canonical approval digest, not read from the plan")
    parser.add_argument("--runtime-pin")
    parser.add_argument("--source-preflight", help="Successful full-cohort no-model summary.json")
    parser.add_argument("--approved-source-preflight-sha256", help="Parent-approved canonical summary digest; required only for --mode run")
    parser.add_argument("--contract", default=str(HERE.parent / "executable-cohort.v1.json"))
    parser.add_argument("--binding")
    parser.add_argument("--dsh-root", required=True)
    parser.add_argument("--task-cwd", default=os.getcwd())
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        payload = {}
        gate = {}
        pin = None
        if args.mode != "seam":
            require(args.approval and args.approved_approval_sha256 and args.runtime_pin and args.binding, "APPROVAL_REQUIRED")
            approval = read_json(args.approval)
            require(digest(approval) == args.approved_approval_sha256, "APPROVAL_HASH_MISMATCH")
            require(args.plan, "PLAN_REQUIRED")
            plan = read_json(args.plan)
            require(digest(read_json(args.binding)) == plan.get("binding_sha256"), "BINDING_HASH_MISMATCH")
            pin = read_json(args.runtime_pin)
            payload = validate_plan(plan, approval, digest(pin), read_json(args.contract))
            gate["approval_sha256"] = args.approved_approval_sha256
            if args.mode == "run":
                require(args.source_preflight and args.approved_source_preflight_sha256, "SOURCE_PREFLIGHT_REQUIRED")
                proof = read_json(args.source_preflight)
                require(digest(proof) == args.approved_source_preflight_sha256, "SOURCE_PREFLIGHT_HASH_MISMATCH")
                validate_source_preflight(proof, payload, digest(pin), args.approved_approval_sha256)
                gate["source_preflight_sha256"] = args.approved_source_preflight_sha256
        else:
            require(not any((args.plan, args.approval, args.runtime_pin, args.approved_approval_sha256)), "SEAM_IS_NOT_A_COHORT")
        root = Path(args.dsh_root).resolve(strict=True)
        task = Path(args.task_cwd).resolve(strict=True)
        program = (HERE / "runtime.mjs").read_text()
        base = source_runtime(root)
        require(hashlib.sha256(program.encode()).hexdigest() == base["program_sha256"], "RUNNER_CHANGED")
        out = Path(args.out)
        require(out.is_absolute() and out == out.resolve() and not out.exists(), "OUTPUT_MUST_BE_NEW_ABSOLUTE_DIRECTORY")
        require(not any(p.is_symlink() for p in (out, *out.parents)), "OUTPUT_SYMLINK")
        git_probe = subprocess.run(["git", "-C", str(out.parent), "rev-parse", "--show-toplevel"], capture_output=True)
        require(git_probe.returncode != 0, "OUTPUT_INSIDE_REPOSITORY")
        require(out.parent.is_dir() and task.is_dir(), "DIRECTORY_REQUIRED")
        out.mkdir(mode=0o700)
        config = {"mode": args.mode, "root": str(root), "out": str(out), "taskCwd": str(task),
                  "runtime": base, "borrowed": BORROWED, "payload": payload, "gate": gate,
                  "pin": pin}
        private_json(out / "runtime-input.json", config)
        env = {**os.environ, "NODE_PATH": BORROWED, "BUN_RUNTIME_TRANSPILER_CACHE_PATH": "0",
               "DSH_STUDY_INPUT": str(out / "runtime-input.json")}
        def limits():
            os.umask(0o077)
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        result = subprocess.run([str(BUN), "-e", program], cwd=root, env=env,
                                preexec_fn=limits, capture_output=True)
        # Never relay product stderr: parser/transport diagnostics can contain secrets.
        print(json.dumps({"status": "captured" if result.returncode == 0 else "blocked", "out": str(out), "child_exit": result.returncode}))
        return result.returncode if result.returncode in (0, 1, 2) else 1
    except Refusal as exc:
        print(json.dumps({"status": "refused", "code": str(exc), "fetch_calls": 0}))
        return 2
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError, subprocess.SubprocessError):
        print(json.dumps({"status": "refused", "code": "INVALID_LOCAL_INPUT", "fetch_calls": 0}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
