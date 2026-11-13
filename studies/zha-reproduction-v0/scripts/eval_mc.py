"""Multiple-choice reasoning (MMLU-Pro subset): dense vs ZHA arms, shared dense prefill, greedy short CoT.

Thinking is disabled (protocol deviation from the paper's 81,920-token thinking budget; see study README).
Resumable by question id.
"""
from __future__ import annotations

import argparse
import json
import re
import string
from pathlib import Path

import zha_run

INSTR = ("Answer the following multiple choice question. Think step by step briefly, then finish with "
         "\"The answer is (X)\" where X is the letter of the correct option.\n\n")


def prompt_text(ex):
    opts = "\n".join(f"({string.ascii_uppercase[i]}) {o}" for i, o in enumerate(ex["options"]))
    return f"{INSTR}Question: {ex['question']}\n\nOptions:\n{opts}"


def extract(text: str, n_opts: int) -> str | None:
    """MMLU-Pro style: 'answer is (X)' first, then the last standalone option letter in parentheses."""
    letters = string.ascii_uppercase[:n_opts]
    m = re.findall(rf"answer is \(?([{letters}])\)?", text)
    if m:
        return m[-1]
    m = re.findall(rf"\(([{letters}])\)", text)
    return m[-1] if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--routers", nargs="+", required=True)
    ap.add_argument("--max-new", type=int, default=512)
    args = ap.parse_args()
    r = zha_run.Runner(args.model)
    arms = [("dense", None, None, 1.0)]
    for spec in args.routers:
        g, refs, _ = zha_run.load_refs(spec.split("=")[1])
        arms.append((f"{g.name}@0.95", g, refs, 0.95))
    out_path = Path(args.out)
    done = {json.loads(l)["id"] for l in out_path.open()} if out_path.exists() else set()
    out = out_path.open("a")
    stop = {t for t in [r.tok.eos_token_id, r.tok.convert_tokens_to_ids("<|im_end|>")] if isinstance(t, int) and t >= 0}
    for path in args.data:
        for line in open(path):
            ex = json.loads(line)
            if ex["id"] in done:
                continue
            kw = {"enable_thinking": False} if "qwen3" in args.model else {}
            ptxt = r.tok.apply_chat_template([{"role": "user", "content": prompt_text(ex)}], tokenize=False,
                                             add_generation_prompt=True, **kw)
            ids = r.tok(ptxt, add_special_tokens=False).input_ids
            res = zha_run.retry_oom(lambda: r.generate_arms(ids, arms, args.max_new, stop))
            for arm, (text, share, ntok) in res.items():
                pred = extract(text, len(ex["options"]))
                out.write(json.dumps({"model": args.model, "id": ex["id"], "source": ex["source"], "arm": arm,
                                      "pred": pred, "answer": ex["answer"], "correct": pred == ex["answer"],
                                      "key_share": share, "gen_tokens": ntok, "prompt_tokens": len(ids),
                                      "tail": text[-160:]}) + "\n")
            out.flush()


if __name__ == "__main__":
    main()
