export default function ResearchDeepDive() {
  return (
    <section className="reference-map">
      <h2 id="research-deep-dive">deep dive: why this shape keeps reappearing</h2>
      <p>
        sebastian raschka&apos;s <a href="https://magazine.sebastianraschka.com/p/classifier-history-and-jev">classifier history + jev essay</a>{" "}
        is a useful map of the territory. i wanted to go one layer lower and follow the papers it
        points at, because the interesting part for zer0 is not &ldquo;jev is fast.&rdquo; it is why
        bounded decisions, calibrated probabilities, cheap baselines and explicit control flow keep
        showing up whenever we stop asking a model to write prose.
      </p>

      <h3>1. this is an old classifier idea at a new operating point</h3>
      <p>
        bag-of-words + logistic regression is still an annoyingly good baseline when lexical cues
        dominate. the important transformer-era change was not that classification suddenly became
        possible. it was that pretrained representations made one backbone transferable across many
        tasks. <a href="https://aclanthology.org/N19-1423/">bert</a> made the encoder version of that
        pattern obvious: read both left and right context, then attach a small task head. later work
        on <a href="https://aclanthology.org/2022.findings-emnlp.293/">bidirectionality</a> found the
        best attention direction is application-dependent; bidirectional attention is especially
        useful for fine-tuning/classification, while causal attention remains natural for generation.
      </p>
      <p>
        <a href="https://arxiv.org/abs/2412.13663">modernbert</a> is the modern version of the same
        efficiency argument: encoder-only models can sit on a strong performance / size / memory
        frontier for classification and retrieval. that makes raschka&apos;s guess that jev could
        be something in this neighborhood technically plausible. it is still only a guess.
        typesafe has <strong>not published jev&apos;s architecture, parameter count or training
        recipe</strong>.
      </p>

      <h3>2. the interface changes the problem</h3>
      <p>
        a normal decoder spends compute predicting a sequence of vocabulary tokens even when the
        program only needs one of five legal actions. jev&apos;s public contract instead accepts
        state plus typed questions and returns bounded choices / binary judgments / scores with
        probabilities. typesafe&apos;s own launch post says its system-one stack uses a new
        architecture, a parallel sampler and a training method it calls rlcd. those are
        <strong> vendor-reported facts about the product</strong>, not enough information to infer
        the hidden architecture.
      </p>
      <p>
        you can build a jev-like interface without building jev. raschka sketches one clean version:
        score each candidate with the same scalar head and normalize across the legal candidates.
        that matters for aodl/z0intelligence because legality can be compiled before inference. the
        learned system does not need to invent an action; it only ranks the actions the program says
        exist.
      </p>

      <h3>what is public, and what is still a black box</h3>
      <div className="x-table-wrap">
        <table className="x-table">
          <thead>
            <tr><th>statement</th><th>evidence state</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>jev emits typed probabilistic decisions through choice / binary / score-shaped APIs</td>
              <td>public product contract</td>
            </tr>
            <tr>
              <td>typesafe says the system-one stack uses a new architecture, parallel sampler and rlcd</td>
              <td>vendor-reported; independently inspectable only at the API behavior layer</td>
            </tr>
            <tr>
              <td>jev is a modernbert-like encoder</td>
              <td>unverified hypothesis; raschka&apos;s educated guess, not a published architecture fact</td>
            </tr>
            <tr>
              <td>rlcd works like rlcr / brier-reward training</td>
              <td>unverified analogy; no published algorithmic equivalence</td>
            </tr>
            <tr>
              <td>jev is useful as a bounded decision primitive on some tasks</td>
              <td>testable claim; evaluate task-by-task with frozen baselines and calibration metrics</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3>3. calibration is the whole point if confidence changes control flow</h3>
      <p>
        top-1 accuracy is insufficient once confidence decides whether we act, abstain or escalate.
        a model that is right 90% of the time but says 99.9% on everything is a worse runtime
        primitive than the same classifier with probabilities that track empirical correctness.
        <a href="https://proceedings.mlr.press/v70/guo17a.html">guo et al. (2017)</a> showed modern
        neural networks can be badly calibrated even when their classification accuracy is strong;
        simple temperature scaling was surprisingly effective across their experiments.
      </p>
      <p>
        the deeper statistical reason comes from{" "}
        <a href="https://doi.org/10.1198/016214506000001437">proper scoring rules</a>. scores such as
        log loss and the brier score are designed so the expected score is optimized by reporting
        the true probability. that is why ece / brier / risk-coverage belong next to accuracy in
        these evals: the probability is itself part of the output contract.
      </p>
      <p>
        typesafe calls its unpublished training method <strong>reinforcement learning for calibrated
        decisions (rlcd)</strong>. a public paper with a related objective is{" "}
        <a href="https://arxiv.org/abs/2507.16806">rlcr</a>, which adds a brier-style confidence
        term to correctness reward. the paper reports much lower expected calibration error than
        ordinary rlvr on its evaluated tasks without the usual accuracy tradeoff. <strong>rlcd is
        not rlcr.</strong> there is no published evidence that the algorithms are the same; rlcr is
        useful here as a public mechanism for understanding why calibration-aware objectives can
        matter.
      </p>

      <h3>3b. abstention turns probabilities into a systems primitive</h3>
      <p>
        once confidence controls escalation, the relevant curve is not just accuracy. it is
        <strong> risk versus coverage</strong>: how much traffic can the cheap policy accept while
        staying under an error budget?{" "}
        <a href="https://arxiv.org/abs/1705.08500">geifman &amp; el-yaniv (2017)</a> formalized
        selective classification as prediction with a reject option, and{" "}
        <a href="https://proceedings.mlr.press/v97/geifman19a.html">selectivenet</a> later trained
        prediction and rejection jointly. this is almost exactly the operational question behind
        our risk/coverage work: the small model does not need to be correct everywhere. it needs to
        know a useful region where it is cheap <em>and</em> acceptably reliable, then hand the rest
        upward.
      </p>
      <p>
        calibration and selectivity are related but not identical. calibration asks whether a 0.8
        score behaves like 80% correctness over a population. selective prediction asks what happens
        to error as we reject lower-confidence cases. a router used for escalation should measure
        both. a beautiful ece can still hide poor class ranking, and a useful risk/coverage curve can
        coexist with imperfect global calibration.
      </p>

      <h3>4. this explains why our jev result and our nanojev failure can both be true</h3>
      <p>
        our jev measurements say something narrow: on the exact bounded slices we tested, jev&apos;s
        ranking / verification behavior held up, including useful calibration measurements. our
        nanojev result says something equally important: matching the <em>api shape</em> does not
        mean a checkpoint learned the capability behind that shape. nanojev was trained for action
        choice; treating its boolean affordance as a calibrated verifier produced a fake-looking
        win until we inspected the objective.
      </p>
      <p>
        that is basically the classifier literature in miniature. architecture, pretraining,
        objective, calibration set and target distribution all matter. &ldquo;it has a classifier
        head&rdquo; is not evidence that it is the classifier you need.
      </p>

      <h3>5. routing needs brutal baselines, not router vibes</h3>
      <p>
        the routing literature is converging on the same warning.{" "}
        <a href="https://arxiv.org/abs/2510.00202">routerarena</a> argues for standardized,
        multi-metric comparisons instead of bespoke router wins.{" "}
        <a href="https://aclanthology.org/2026.findings-acl.1881/">llmrouterbench</a> goes further:
        across 400k+ instances, 21 datasets and 33 models, many routing methods become hard to
        distinguish under one evaluation framework, and several do not reliably beat simple
        baselines.
      </p>
      <p>
        there is already a useful jev-specific negative result too. the independent{" "}
        <a href="https://github.com/TokenTrim/jev-routing-experiment">tokentrim experiment</a> used
        jev difficulty estimates plus retrieval evidence on llmrouterbench. the combined router beat
        the best single model on one reported frontier — but the no-jev ablation landed in basically
        the same place. retrieval was doing the work. that is exactly the kind of ablation i want in
        z0evals: if the fancy component contributes zero marginal value, say so.
      </p>
      <p>
        our own sealed traces rhyme with that result: five deterministic rules beat both learned
        fast paths. this does <em>not</em> prove rules beat learned routers in general. it proves
        that a router only earns its place when it beats the strongest cheap baseline on the actual
        distribution we care about.
      </p>

      <h3>6. the public jev ecosystem is already telling us what the primitive is for</h3>
      <p>
        the recent <a href="https://arxiv.org/abs/2609.30216">jev in the wild</a> preprint analyzed
        2,170 public jev projects collected through september 22, 2026. usage spans attribute
        judgment, scoring, action selection, filtering, and model/tool selection; the mix varies by
        domain. that is more consistent with a reusable decision primitive embedded inside workflows
        than with a tiny replacement for a general agent.
      </p>

      <h3>7. what i would actually build from the literature</h3>
      <div className="x-table-wrap">
        <table className="x-table">
          <thead>
            <tr><th>layer</th><th>default</th><th>why</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>legal action space</td>
              <td>compiler / deterministic code</td>
              <td>never spend model capacity rediscovering impossible actions</td>
            </tr>
            <tr>
              <td>obvious routing</td>
              <td>rules + retrieval baselines</td>
              <td>cheap, inspectable, and surprisingly hard to beat on narrow traces</td>
            </tr>
            <tr>
              <td>ambiguous bounded decision</td>
              <td>task-fit calibrated decision model</td>
              <td>probabilities are useful when they control abstention and escalation</td>
            </tr>
            <tr>
              <td>novel / open-ended work</td>
              <td>general language model</td>
              <td>pay for generation and reasoning only when the task actually needs them</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p>
        this is an architecture implication, not a claim that one paper proved the whole stack.
        the falsifiable question stays the same at each layer: <strong>does this cheaper mechanism
        preserve the verified outcome on the real distribution?</strong>
      </p>

      <h3>paper trail</h3>
      <ul>
        <li><a href="https://magazine.sebastianraschka.com/p/classifier-history-and-jev">raschka — language models for text classification: from bag-of-words to jev</a> — synthesis and the jumping-off point for this section.</li>
        <li><a href="https://typesafe.ai/blog/introducing-system-one-models-and-jev">typesafe — introducing system one models &amp; jev</a> — primary source for the public product/training claims; vendor evidence, not independent validation.</li>
        <li><a href="https://aclanthology.org/N19-1423/">devlin et al. — bert</a> — pretrained bidirectional encoder + small downstream head.</li>
        <li><a href="https://aclanthology.org/2022.findings-emnlp.293/">artetxe et al. — role of bidirectionality</a> — why attention direction depends on the application.</li>
        <li><a href="https://arxiv.org/abs/2412.13663">warner et al. — modernbert</a> — modern encoder efficiency/classification reference; not evidence of jev&apos;s hidden architecture.</li>
        <li><a href="https://proceedings.mlr.press/v70/guo17a.html">guo et al. — calibration of modern neural networks</a> — accuracy and calibrated confidence are different properties.</li>
        <li><a href="https://arxiv.org/abs/1705.08500">geifman &amp; el-yaniv — selective classification</a> and <a href="https://proceedings.mlr.press/v97/geifman19a.html">selectivenet</a> — risk/coverage and explicit abstention.</li>
        <li><a href="https://doi.org/10.1198/016214506000001437">gneiting &amp; raftery — strictly proper scoring rules</a> — formal grounding for probability-quality objectives.</li>
        <li><a href="https://arxiv.org/abs/2507.16806">damani et al. — rlcr</a> — public calibration-aware rl reference; related objective, not disclosed jev training.</li>
        <li><a href="https://arxiv.org/abs/2510.00202">routerarena</a> and <a href="https://aclanthology.org/2026.findings-acl.1881/">llmrouterbench</a> — standardized routing evaluation and strong-baseline pressure.</li>
        <li><a href="https://arxiv.org/abs/2609.30216">ling et al. — jev in the wild</a> — early empirical map of 2,170 public projects.</li>
        <li><a href="https://github.com/TokenTrim/jev-routing-experiment">tokentrim — jev routing experiment</a> — third-party ablation where retrieval, not jev difficulty, explains the reported gain.</li>
      </ul>
    </section>
  );
}
