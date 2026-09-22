export default function ReferenceMap() {
  return (
    <div className="reference-map">
      <p>
        this project is obviously not happening in a vacuum. some of these are direct references,
        some gave us a primitive or eval pattern, and some were useful specifically because our
        measurements disagreed with what i expected going in.
      </p>

      <details>
        <summary><strong>closest conceptual references</strong></summary>
        <ul>
          <li><a href="https://www.southbridge.ai/blog/jev-watching-the-agents">southbridge — “jev: watching the agents”</a> — the closest conceptual and visual reference for the article.</li>
          <li><a href="https://github.com/southbridgeai/jev">jev</a> — bounded probabilistic decisions without generating prose token by token.</li>
          <li><a href="https://github.com/kvnloo/z0intelligence">openjev / z0intelligence</a> — our local path for direct logit readout, nanojev, q-route and a common decision backend.</li>
          <li><a href="https://github.com/NousResearch/hermes-agent/pull/113020">hermes pr #113020 — probabilistic decision providers</a> — provider-neutral typed decisions, abstention and replay metrics. authored by <code>fangliquanflq</code>, not tek.</li>
        </ul>
      </details>

      <details>
        <summary><strong>tek&apos;s eval work in hermes</strong></summary>
        <ul>
          <li><a href="https://github.com/NousResearch/hermes-agent/pull/88663">teknium1 — pr #88663: browser use a/b eval</a> — 204-run benchmark turned into a permanent rerunnable eval.</li>
          <li><a href="https://github.com/NousResearch/hermes-agent/pull/79162">teknium1 — pr #79162: core-toolset a/b harness</a> — one variable at a time, production-derived trap tasks, trace scoring, programmatic success.</li>
          <li><a href="https://github.com/NousResearch/hermes-agent/pull/87326">teknium1 — pr #87326: lean-tail compaction recall eval</a> — quality and retained tokens measured together.</li>
          <li><a href="https://github.com/NousResearch/hermes-agent/pull/109903">teknium1 — pr #109903: move living benchmarks into evals/</a> — evals as durable repo artifacts instead of one-off scripts.</li>
        </ul>
      </details>

      <details>
        <summary><strong>agent harnesses & execution systems</strong></summary>
        <ul>
          <li><a href="https://github.com/NousResearch/hermes-agent">nousresearch/hermes-agent</a></li>
          <li><a href="https://github.com/deepseek-ai/deepseek-harness">deepseek-ai/deepseek-harness</a></li>
          <li><a href="https://github.com/can1357/oh-my-pi">can1357/oh-my-pi</a></li>
          <li><a href="https://modelcontextprotocol.io/">model context protocol</a></li>
          <li><a href="https://github.com/openai/openai-agents-python">openai agents sdk</a></li>
          <li><a href="https://github.com/SWE-agent/SWE-agent">swe-agent</a></li>
          <li><a href="https://github.com/All-Hands-AI/OpenHands">openhands</a></li>
        </ul>
      </details>

      <details>
        <summary><strong>zer0 architecture</strong></summary>
        <ul>
          <li><a href="https://github.com/kvnloo/aodl">aodl</a> — typed intent, constraints and legal-action structure.</li>
          <li><a href="https://github.com/kvnloo/z0intelligence">z0intelligence</a> — cognition selection, escalation, DecisionBackend, nanojev and q-route.</li>
          <li><a href="https://github.com/kvnloo/kerdoios">kerdoios</a> — residency, provider quota and resource placement.</li>
          <li><a href="https://github.com/kvnloo/evolution-lab">evolution-lab</a> — q-route, mushroom/fly experiments and training.</li>
          <li><a href="https://github.com/kvnloo/tokenomics">tokenomics</a> — neutral token/context/latency/cost/outcome accounting.</li>
          <li><a href="https://github.com/kvnloo/z0evals">z0evals</a> — frozen evaluation and publication.</li>
          <li><a href="https://github.com/kvnloo/verified-oss-loop">verified-oss-loop</a> — exact-head evidence and staged promotion.</li>
          <li><a href="https://github.com/kvnloo/frontier-kb">frontier-kb</a> — literature and research evidence trail.</li>
        </ul>
      </details>

      <details>
        <summary><strong>models, serving & placement</strong></summary>
        <ul>
          <li><a href="https://huggingface.co/collections/ibm-granite/hammer">hammer / hammer2.1</a></li>
          <li><a href="https://github.com/QwenLM/Qwen3">qwen</a></li>
          <li><a href="https://developer.nvidia.com/nemotron">nvidia nemotron</a></li>
          <li><a href="https://huggingface.co/google/functiongemma-270m-it">functiongemma</a></li>
          <li><a href="https://github.com/ggml-org/llama.cpp">llama.cpp</a></li>
          <li><a href="https://github.com/vllm-project/vllm">vllm</a></li>
          <li><a href="https://github.com/BerriAI/litellm">litellm</a></li>
          <li><a href="https://console.groq.com/docs/overview">groq</a></li>
          <li><a href="https://inference-docs.cerebras.ai/">cerebras inference</a></li>
          <li><a href="https://openrouter.ai/docs">openrouter</a></li>
          <li><a href="https://kubernetes.io/">kubernetes</a></li>
        </ul>
      </details>

      <details>
        <summary><strong>fly, mushroom & tiny learned policies</strong></summary>
        <ul>
          <li><a href="https://flywire.ai/">flywire</a> — whole-brain drosophila connectomics.</li>
          <li><a href="https://www.science.org/doi/10.1126/science.add9330">the connectome of an insect brain</a></li>
          <li><a href="https://www.nature.com/articles/nature23455">mushroom-body learning literature</a></li>
          <li><a href="https://github.com/kvnloo/frontier-kb">flyforge research trail</a> — MaleCNS, TMNF-C and the sensorimotor-specialist framing.</li>
          <li><a href="https://github.com/kvnloo/z0intelligence/tree/main/omp-extensions">flyforge integration</a> — current shadow/recovery integrations.</li>
        </ul>
      </details>

      <details>
        <summary><strong>“make the model do less” & evaluation methodology</strong></summary>
        <ul>
          <li>agentrun — “a harness for repetitive knowledge work” by miguel ríos berríos / grep — compile repeated agent behavior into a workflow and skip work that cannot change the answer.</li>
          <li><a href="https://arxiv.org/abs/2512.24601">recursive language-model work</a> — context virtualization / evidence addressing.</li>
          <li><a href="https://github.com/stanfordnlp/dspy">dspy</a> — prompts/programs as optimizable components.</li>
          <li><a href="https://en.wikipedia.org/wiki/Brier_score">brier score</a>, <a href="https://en.wikipedia.org/wiki/Cross-entropy">log loss</a>, and <a href="https://scikit-learn.org/stable/modules/calibration.html">calibration</a> — probability quality rather than only top-1 accuracy.</li>
          <li><a href="https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval">wilson intervals</a> — the intervals used in the bounded-choice table.</li>
          <li><a href="https://opentelemetry.io/">opentelemetry</a>, <a href="https://github.com/mlflow/mlflow">mlflow</a>, and <a href="https://wandb.ai/">weights & biases</a> — surrounding lineage/trace/experiment-tracking references.</li>
        </ul>
        <pre><code>{`record the real execution
→ replay the same state
→ change one thing
→ verify externally
→ preserve the evidence`}</code></pre>
      </details>

      <details>
        <summary><strong>future directions — not claims of phase 1b</strong></summary>
        <ul>
          <li>mushroom-body learned specialists</li>
          <li>fly-derived temporal/recovery policies</li>
          <li>nanojev risk/coverage routing</li>
          <li>q-route progressively compiling expensive decisions into cheaper policies</li>
          <li>kubernetes as an optional execution substrate</li>
          <li>groq/cerebras free-tier capacity as experimental compute</li>
          <li>agentrun-style workflow compilation</li>
          <li>rlm-style context/evidence offloading</li>
          <li>learned residency-aware placement</li>
          <li>cross-harness shadow evaluation across hermes / dsh / omp</li>
        </ul>
        <p><strong>the question stays the same:</strong> does this let the expensive model do less without making the system worse?</p>
      </details>
    </div>
  );
}
