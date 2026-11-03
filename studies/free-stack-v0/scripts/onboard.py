#!/usr/bin/env python3
"""Get every free LLM API key in one pass, check it works, and export it where your tools look.

    python3 onboard.py              # walk through each missing provider: opens its key page, you paste, it checks
    python3 onboard.py --open-all   # open every key page in browser tabs at once, then paste them one by one
    python3 onboard.py --check      # re-check saved keys and count the free models each one can see
    python3 onboard.py --export env|opencode

Keys are saved to ~/.config/free-stack/keys.env (mode 600) and never printed. Keys already in your
environment are reused. Account creation itself (email confirmation, CAPTCHA, terms) stays with you:
most providers below offer sign-in with GitHub or Google, so each one is usually a few clicks and a paste.
Standard library only."""
import argparse, getpass, json, os, ssl, stat, sys, urllib.error, urllib.request, webbrowser
from pathlib import Path

STORE = Path(os.environ.get("FREE_STACK_HOME", Path.home() / ".config" / "free-stack")) / "keys.env"
CTX = ssl.create_default_context()

# name, env var, key page, OpenAI-compatible base, how free it is
PROVIDERS = [
    ("Groq", "GROQ_API_KEY", "https://console.groq.com/keys", "https://api.groq.com/openai/v1",
     "free tier, per-model limits (e.g. 30 RPM / 8K TPM)"),
    ("OpenRouter", "OPENROUTER_API_KEY", "https://openrouter.ai/settings/keys", "https://openrouter.ai/api/v1",
     "free `:free` models; daily cap rises after a one-time $10 credit purchase"),
    ("NVIDIA NIM", "NVIDIA_API_KEY", "https://build.nvidia.com/settings/api-keys", "https://integrate.api.nvidia.com/v1",
     "free with the NVIDIA Developer Program, ~40 RPM, prototyping only"),
    ("Google AI Studio", "GEMINI_API_KEY", "https://aistudio.google.com/apikey",
     "https://generativelanguage.googleapis.com/v1beta/openai", "free tier; prompts may be used to improve products"),
    ("Vercel AI Gateway", "AI_GATEWAY_API_KEY", "https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai%2Fapi-keys",
     "https://ai-gateway.vercel.sh/v1", "monthly free credit for unpaid teams, free-eligible models only"),
    ("Nous Portal", "NOUS_API_KEY", "https://portal.nousresearch.com/", "https://inference-api.nousresearch.com/v1",
     "free plan: free models only, 50 RPM / 500K TPM"),
    ("Cerebras", "CEREBRAS_API_KEY", "https://cloud.cerebras.ai/", "https://api.cerebras.ai/v1",
     "trial credit, not a permanent free tier (optional)"),
    ("OpenCode Zen", "OPENCODE_API_KEY", "https://opencode.ai/auth", "https://opencode.ai/zen/v1",
     "rotating `-free` models; also usable keyless inside the OpenCode CLI"),
]


def load():
    keys = {}
    if STORE.exists():
        for line in STORE.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                keys[k.strip()] = v.strip()
    for _, env, *_ in PROVIDERS:
        if os.environ.get(env) and env not in keys:
            keys[env] = os.environ[env]
    return keys


def save(keys):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.touch(mode=0o600, exist_ok=True)
    os.chmod(STORE, stat.S_IRUSR | stat.S_IWUSR)
    STORE.write_text("".join(f"{k}={v}\n" for k, v in sorted(keys.items())))


def check(base, key):
    """Return (ok, model_count_or_reason). Uses GET /models, which costs no tokens."""
    req = urllib.request.Request(base + "/models", headers={"Authorization": f"Bearer {key}", "User-Agent": "Mozilla/5.0 free-stack/1"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            data = json.loads(r.read()).get("data", [])
            free = [m for m in data if "free" in json.dumps(m).lower()]
            return True, f"{len(data)} models visible" + (f", {len(free)} marked free" if free else "")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return False, type(e).__name__


def onboard(open_all):
    keys = load()
    missing = [p for p in PROVIDERS if p[1] not in keys]
    if not missing:
        print("All providers already have keys. Run --check to verify them.")
        return
    if open_all:
        for name, _, url, *_ in missing:
            webbrowser.open_new_tab(url)
        print(f"Opened {len(missing)} key pages. Sign in with GitHub or Google, create a key, then paste it below.\n")
    for name, env, url, base, terms in missing:
        print(f"== {name} ({terms})")
        if not open_all:
            print(f"   opening {url}")
            webbrowser.open_new_tab(url)
        key = getpass.getpass(f"   paste {env} (Enter to skip): ").strip()
        if not key:
            continue
        ok, info = check(base, key)
        print(f"   {'ok' if ok else 'FAILED'}: {info}")
        if ok:
            keys[env] = key
            save(keys)
    print(f"\nSaved to {STORE}. Next: `python3 onboard.py --export env >> ~/.bashrc` or `--export opencode`.")


def do_check():
    keys = load()
    for name, env, url, base, terms in PROVIDERS:
        if env not in keys:
            print(f"{name:18} missing  -> {url}")
            continue
        ok, info = check(base, keys[env])
        print(f"{name:18} {'ok     ' if ok else 'FAILED '} {info}")


def export(kind):
    keys = load()
    if kind == "env":
        print(f"set -a; . {STORE}; set +a")
    elif kind == "opencode":
        # OpenCode reads GROQ_API_KEY, OPENROUTER_API_KEY, CEREBRAS_API_KEY ... from the environment by itself.
        # This adds the OpenAI-compatible ones it has no built-in provider for.
        extra = {n: (env, base) for n, env, _, base, _ in PROVIDERS if n in ("NVIDIA NIM", "Vercel AI Gateway", "Nous Portal") and env in keys}
        cfg = {"$schema": "https://opencode.ai/config.json", "provider": {
            n.split()[0].lower(): {"npm": "@ai-sdk/openai-compatible", "name": n,
                                   "options": {"baseURL": base, "apiKey": "{env:%s}" % env}}
            for n, (env, base) in extra.items()}}
        print(json.dumps(cfg, indent=2))
        print(f"# merge into ~/.config/opencode/opencode.json, then: set -a; . {STORE}; set +a", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--open-all", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--export", choices=["env", "opencode"])
    a = ap.parse_args()
    if a.check:
        do_check()
    elif a.export:
        export(a.export)
    else:
        onboard(a.open_all)
