"""RULER-13 (NVIDIA/RULER synthetic generator) evaluation: dense vs ZHA arms on a shared dense prefill.

Greedy, thinking disabled, official per-task token caps. Resumable: rows already present
in --out (same length, task and index) are skipped.

  python eval_ruler.py --model qwen3-0.6b --data DIR --out raw.jsonl --routers deep=ck1.pt wide=ck2.pt
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import zha_run

TASKS = ["niah_single_1", "niah_single_2", "niah_single_3", "niah_multikey_1", "niah_multikey_2", "niah_multikey_3",
         "niah_multivalue", "niah_multiquery", "vt", "cwe", "fwe", "qa_1", "qa_2"]
CAPS = {"niah": 128, "vt": 30, "cwe": 120, "fwe": 50, "qa": 32}


def cap(task: str) -> int:
    return CAPS[task.split("_")[0]]


def postprocess(pred: str) -> str:
    """RULER eval/evaluate.py postprocess_pred: drop non-printable characters."""
    return re.sub(r"[\x00-\x1f]", "\n", pred).strip()


def sample_score(task: str, pred: str, refs: list[str]) -> float:
    """RULER eval/synthetic/constants.py: string_match_part for qa, string_match_all otherwise."""
    p = pred.lower()
    if task.startswith("qa"):
        return max(1.0 if r.lower() in p else 0.0 for r in refs)
    return sum(1.0 if r.lower() in p else 0.0 for r in refs) / len(refs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lengths", type=int, nargs="+", default=[4096, 16384])
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--routers", nargs="+", required=True, help="name=ckpt.pt")
    ap.add_argument("--ps", type=float, nargs="+", default=[0.95])
    ap.add_argument("--extra", nargs="*", default=["deep-c4l6@0.9", "deep-c4l6@0.8"], help="geometry@p arms")
    args = ap.parse_args()
    r = zha_run.Runner(args.model)
    routers = {}
    for spec in args.routers:
        name, path = spec.split("=")
        g, refs, ck = zha_run.load_refs(path)
        routers[g.name] = (g, refs)
    arms = [("dense", None, None, 1.0)]
    for gname, (g, refs) in routers.items():
        for p in args.ps:
            arms.append((f"{gname}@{p}", g, refs, p))
    for spec in args.extra:
        gname, p = spec.split("@")
        if gname in routers:
            arms.append((spec, routers[gname][0], routers[gname][1], float(p)))
    done = set()
    out_path = Path(args.out)
    if out_path.exists():
        for line in out_path.open():
            row = json.loads(line)
            done.add((row["length"], row["task"], row["index"]))
    out = out_path.open("a")
    stop = {t for t in [r.tok.eos_token_id, r.tok.convert_tokens_to_ids("<|im_end|>"), r.tok.convert_tokens_to_ids("<|endoftext|>")] if isinstance(t, int) and t >= 0}
    for length in args.lengths:
        for task in TASKS:
            path = Path(args.data) / str(length) / task / "validation.jsonl"
            rows = [json.loads(l) for l in path.open()][: args.n]
            for ex in rows:
                key = (length, task, ex["index"])
                if key in done:
                    continue
                kw = {"enable_thinking": False} if "qwen3" in args.model else {}
                prompt = r.tok.apply_chat_template([{"role": "user", "content": ex["input"]}], tokenize=False,
                                                   add_generation_prompt=True, **kw)
                prompt += ex["answer_prefix"].lstrip()
                ids = r.tok(prompt, add_special_tokens=False).input_ids
                res = zha_run.retry_oom(lambda: r.generate_arms(ids, arms, cap(task), stop))
                for arm, (text, share, ntok) in res.items():
                    pred = postprocess(text)
                    out.write(json.dumps({"model": args.model, "length": length, "task": task, "index": ex["index"],
                                          "arm": arm, "score": sample_score(task, pred, ex["outputs"]),
                                          "pred": pred[:200], "refs": ex["outputs"], "key_share": share,
                                          "gen_tokens": ntok, "prompt_tokens": len(ids)}) + "\n")
                out.flush()
            print(f"{args.model} {length} {task} done", flush=True)


if __name__ == "__main__":
    main()
