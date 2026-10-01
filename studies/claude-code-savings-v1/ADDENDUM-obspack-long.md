# Addendum: ObservationPack on long, output-heavy sessions (obspack-long-v1)

**Result: the pre-registered primary test passed, but the entire saving came from one task type.**

ObservationPack archives any Bash result over 6000 chars and shows the model only the head and tail, plus a recall handle. v1 found it had no effect on short tasks, whose median was about 5 tool calls. On its single long recall task it cut cost 41.5% (n=4, exploratory). This follow-up tests the regime ObservationPack was built for: long sessions with large outputs.

The work is on kvnloo/z0intelligence `study/obspack-long-v1`:

- Pre-registration: `69f4ca2`, pushed before any measured run.
- Runner fix for session limits: `53b259b`.
- Results: `df4f3f4`, imported unchanged into `data/obspack-long/`.

**Design.** 208 real `claude -p` sessions (Sonnet, Claude Code 2.1.286, effort medium), 4 reps each, run in four arms: lean and stock, each with and without ObservationPack.

- **Primary population: 10 long tasks** from four z0 repos at v1's pinned SHAs:
  - 7 multi-bug debugging tasks: 8 independent bugs each, with a verbose test suite.
  - 3 directed-recall tasks: `cat` 25 source files, then answer 10 questions.
- **Exploratory:**
  - 2 log-forensics tasks.
  - v1's long recall task, run as an anchor.
- **Validation:** every task was checked programmatically. It fails as given, passes with the reference, and for multi-bug tasks each bug alone fails the check.
- **Primary metric:** Claude Code's estimated cost, because it is billing-weighted. Tokens are secondary.

| 10 long tasks, n=40 pairs | cost | 95% CI | cheaper | p | tokens | success | guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **lean → lean+obspack** (primary) | **−30.7%** | −50.0 … −1.9 | 26/40 | 0.012 | −9.5% (n.s.) | 39 → 39 | PASS |
| stock → stock+obspack | −26.9% | −48.1 … +3.4 | 21/40 | 0.089 | −9.5% (n.s.) | 40 → 40 | PASS |
| stock → lean+obspack | −39.9% | −54.5 … −20.4 | 35/40 | 8e-9 | −28.6% | 40 → 39 | PASS |

Results by task type (lean → lean+obspack):

| task type | cost change | outputs packed per session |
| --- | --- | --- |
| directed recall | **−64.2%** (12/12 cheaper; stock −66.5%) | 25 |
| multi-bug debugging | **+1.3%** (CI −4.2 … +6.7; stock **+5.3%**, CI +2.4 … +8.0) | 1.2 |
| log forensics (exploratory) | −8.4% | ~0 |
| v1 anchor | −52.9% (v1: −41.5%) | — |

**What this means:**

- **ObservationPack saves money only when large Bash outputs reach the context.** The multi-bug prompts asked for a verbose suite after every fix, and those sessions were long (median about 22 calls). Even so, the model mostly kept each output under the threshold: it targeted single test files, failures got shorter as bugs were fixed, and it read source through the Read tool, which is not packed. So packing almost never fired. Under stock it added about 2.5 tool calls per session and cost 5% more.
- **The pooled −31% passes the bar, but don't quote it as a general number.** It averages a two-thirds saving on dump-heavy work with no saving on debugging.
- **Token counts understate the saving again.** Cache-write tokens fell 49% while total tokens fell 9.5%. On the anchor task under stock, tokens rose 24% while cost fell 26%.
- **Quality held in aggregate (39/40 → 39/40).** One recall session with ObservationPack got 1 of 10 answers wrong after 13 recall calls. Taken alone, the recall subgroup fails the guard (12 → 11), and n is too small to rule out a small accuracy cost.

**Caveats:**

- **Session limit.** The account hit its session limit mid-run (20:51 CDT, shared with other studies). 44 zero-token aborts counted as no-result, as pre-registered, and those cells were rerun after the 22:10 reset. Some "warm" reps therefore ran cold.
- **Tasks were shaped by a pilot.** After a one-arm pilot, and before the pre-registration commit, the multi-bug tasks were raised from 5 to 8 bugs and log forensics was moved to exploratory.
- **Two task types direct how the model works.** The recall tasks are close to an upper bound for ObservationPack.
- **Small sample.** One host, one model, one night. The CIs are clustered over 10 tasks, only 3 of them recall.
