# Apply the minimal "speed" config to the profile named in HERMES_HOME (set for this process only).
import os, sys, json
sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))
os.chdir(os.path.expanduser("~/.hermes/hermes-agent"))
from hermes_cli.config import load_config, save_config, get_hermes_home
guided = "--guided" in sys.argv
home = str(get_hermes_home()); assert home.endswith(("/profiles/speed", "/profiles/speed-guided")), home
cfg = load_config()
from hermes_cli.setup_quick import _blank_slate_minimize_config
import hermes_cli.setup_quick as sq
# Blank Slate's toolset routine, with keep = {file, terminal} (no vision, no skills).
keep = {"file", "terminal"}
cfg.setdefault("platform_toolsets", {})["cli"] = sorted(keep)
from toolsets import TOOLSETS
from hermes_cli.tools_config import CONFIGURABLE_TOOLSETS, _get_plugin_toolset_keys
all_keys = {k for k, _, _ in CONFIGURABLE_TOOLSETS}; all_keys.update(_get_plugin_toolset_keys())
for k, tdef in TOOLSETS.items():
    if k.startswith("hermes-") or (isinstance(tdef, dict) and (tdef.get("includes") or tdef.get("posture"))):
        continue
    all_keys.add(k)
cfg.setdefault("agent", {})["disabled_toolsets"] = sorted(all_keys - keep)
_blank_slate_minimize_config(cfg)          # compression/memory/checkpoints/smart routing off, max_turns 90
cfg["model"] = {"provider": "openai-codex", "default": "gpt-6.1-sol"}
a = cfg["agent"]; a["reasoning_effort"] = "low"; a["max_turns"] = 60
if not guided:
    a["execution_guidance"] = False        # drops "<mandatory_tool_use> Arithmetic -> use terminal" block
    a["tool_use_enforcement"] = False
cfg.setdefault("memory", {})["nudge_interval"] = 0
cfg.setdefault("skills", {})["creation_nudge_interval"] = 0
cfg["plugins"] = {"enabled": [], "disabled": []}
cfg["prompt_caching"] = {"cache_ttl": "5m"}
cfg["fallback_providers"] = []
cfg.setdefault("telemetry", {})["shared_metrics"] = {"enabled": False, "send": False}
save_config(cfg)
print(json.dumps({k: cfg.get(k) for k in ("model","platform_toolsets","agent","memory","compression","checkpoints","smart_model_routing","plugins","skills")}, indent=1, default=str)[:3000])
