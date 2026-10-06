"""Execute the workflow's real shell guards with offline curl stubs."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml
ROOT = Path(__file__).resolve().parents[1]

def steps(job: str) -> list[dict]:
    return yaml.safe_load((ROOT / '.github/workflows/pages.yml').read_text())['jobs'][job]['steps']

def script(job: str, name: str) -> str:
    return next(s['run'] for s in steps(job) if s.get('name') == name)

class PagesPublicationTests(unittest.TestCase):
    def build_guard(self, branch: str, ok: str) -> subprocess.CompletedProcess:
        source = script('build', 'Build every channel')
        start = source.index('if [ "$ok" = yes ]; then')
        end = source.index('git worktree remove', start)
        return subprocess.run(['bash', '-c', 'set -eu\nbuilt=""\n' + source[start:end] + '\necho "$built"'], env={**os.environ, 'BRANCH': branch, 'ok': ok, 'SUB': branch+'/', 'paths': ''}, capture_output=True, text=True, timeout=5)

    def test_failed_channel_never_publishes_partial_site(self):
        for branch in ('main', 'nightly', 'preview', 'dev'):
            with self.subTest(branch=branch):
                self.assertNotEqual(self.build_guard(branch, 'no').returncode, 0)

    def test_successful_channel_is_recorded(self):
        for branch in ('main', 'nightly', 'preview', 'dev'):
            with self.subTest(branch=branch):
                result = self.build_guard(branch, 'yes')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(branch, result.stdout)

    def run_live_guard(self, broken: str = '', omit: str = '', paths: str = 'nightly/ next/ dev/') -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            target = str(Path(tmp) / 'response.html')
            source = script('deploy', 'Verify every published channel').replace('/tmp/chan.html', target)
            stub = r'''curl() {
  local url="" out="/dev/null"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      -o) out="$2"; shift ;;
      https://example.invalid/*) url="$1" ;;
    esac
    shift
  done
  [ "$url" != "$BROKEN" ] || return 22
  local body='z0evals how much of the llm do we actually need? what actually deserves a model? can four agents remember the same thing? does optchat stay small after fifty tool calls? how do you learn the frontier fast? optmem-update optchat-update z0evals channels'
  if [ -n "$OMIT" ]; then body="${body//$OMIT/}"; fi
  printf '%s' "$body" > "$out"
}
seq() { printf '1\n'; }
sleep() { :; }
'''
            env = {**os.environ, 'PAGE_URL': 'https://example.invalid/z0evals/', 'CHANNEL_PATHS': paths, 'BROKEN': broken, 'OMIT': omit}
            return subprocess.run(['bash', '-c', stub + source], env=env, capture_output=True, text=True, timeout=5)

    def test_missing_expected_live_channel_fails(self):
        self.assertNotEqual(self.run_live_guard('https://example.invalid/z0evals/dev/').returncode, 0)

    def test_complete_live_site_passes(self):
        result = self.run_live_guard()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_stale_memory_page_fails_even_with_old_title(self):
        for marker in ('optmem-update', 'optchat-update'):
            with self.subTest(marker=marker):
                self.assertNotEqual(self.run_live_guard(omit=marker).returncode, 0)

    def test_missing_optchat_article_fails(self):
        self.assertNotEqual(self.run_live_guard(omit='does optchat stay small after fifty tool calls?').returncode, 0)

    def test_unpublished_channel_is_not_required(self):
        result = self.run_live_guard('https://example.invalid/z0evals/dev/', paths='nightly/ next/')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shell_syntax(self):
        for job in ('build', 'deploy'):
            for step in steps(job):
                if 'run' in step:
                    result = subprocess.run(['bash', '-n'], input=step['run'], capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == '__main__':
    unittest.main()
