import type { Metadata } from "next";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import Callout from "@/components/Callout";

export const metadata: Metadata = {
  title: "how do you learn the frontier fast? — z0evals",
  description:
    "the research trail behind z0intelligence: classifiers, calibrated decisions, routing, conditional compute, tiny specialists, and using llms to learn a field by testing it.",
};

const meta: StoryMeta = {
  title: "how do you learn the frontier fast?",
  subtitle:
    "the research trail behind z0intelligence — and what using llms taught me about learning to think like a researcher",
  author: "zer0 research",
  date: "september 29, 2026",
  status: "research synthesis",
  lede:
    "i did not start with a literature review. i started with a practical annoyance: why was i paying an autoregressive language model to make decisions that looked much smaller than language generation? the answer pulled me through classifiers, calibration, selective prediction, routing, conditional compute, systems placement, connectomics, and eventually a different way of using llms for research.",
};

const banner: StoryBanner = {
  tag: "research companion · not another benchmark post",
  text:
    "the phase 1b and routing posts are the experimental record. this one is about the mental model behind them: what the papers say, which ideas survived contact with our evals, what we changed our mind about, and what the current frontier seems to imply.",
};

const toc: TocItem[] = [
  { id: "problem", label: "start from the problem, not the paper", depth: 0 },
  { id: "decision", label: "a decision is not necessarily generation", depth: 0 },
  { id: "classifiers", label: "from bert to decision models", depth: 0 },
  { id: "jev", label: "what jev actually changed", depth: 0 },
  { id: "compiler", label: "the compiler changed the question", depth: 0 },
  { id: "probability", label: "probability has to mean something", depth: 0 },
  { id: "abstention", label: "abstention is old and extremely useful", depth: 0 },
  { id: "conditional", label: "conditional compute is the bigger idea", depth: 0 },
  { id: "routing", label: "the router literature humbled us", depth: 0 },
  { id: "systems", label: "model choice became a systems problem", depth: 0 },
  { id: "composition", label: "more intelligence can be negative information", depth: 0 },
  { id: "specialists", label: "specialize the repeated cognition", depth: 0 },
  { id: "biology", label: "why we looked at flies", depth: 0 },
  { id: "compile", label: "the end state is downward compilation", depth: 0 },
  { id: "method", label: "how we actually did the research", depth: 0 },
  { id: "llms", label: "what llms accelerate — and what they do not", depth: 0 },
  { id: "sota", label: "our current synthesis of the frontier", depth: 0 },
  { id: "next", label: "the experiments that would change my mind", depth: 0 },
  { id: "learn", label: "a reusable way to learn a field fast", depth: 0 },
  { id: "explore", label: "paper map + evidence ledger", depth: 1 },
];

const story = (
  <>
    <h2 id="problem">start from the problem, not the paper</h2>
    <p>
      the first z0intelligence question was not “what is the best router?” or “how does jev work?”
      it was more primitive: <strong>how much expensive general intelligence does an agent actually
      need on each step?</strong>
    </p>
    <p>
      from the outside an agent loop looks like one continuous act of intelligence. zoom in and the
      loop fractures into very different computational jobs: understand an open-ended request,
      retrieve context, decide whether a tool is relevant, choose among a few legal actions, notice
      a retry condition, verify an outcome, decide whether to escalate, and only sometimes do
      genuinely novel reasoning.
    </p>
    <p>
      that distinction matters because a frontier language model is an incredibly general machine.
      if the runtime asks it to solve a five-way choice, we are buying the ability to generate the
      entire language distribution and then using a microscopic slice of that capability.
    </p>
    <Callout kind="info" title="the question that kept surviving">
      <p>
        what is the smallest mechanism that preserves the verified behavior required by this exact
        decision?
      </p>
    </Callout>
    <p>
      that question became more useful than “which model is smartest?” because it forces us to
      identify the <em>function</em> before choosing the implementation.
    </p>

    <h2 id="decision">a decision is not necessarily a generation problem</h2>
    <p>
      an autoregressive language model learns a distribution over sequences. at inference time it
      repeatedly predicts the next token, appends it, and predicts again. that interface is
      beautiful when the desired output is language. it is less obviously necessary when the
      desired output is one element from a set that the program already knows.
    </p>
    <p>
      for a bounded decision, the mathematical object we usually care about is closer to:
    </p>
    <pre><code>{"state s\nlegal actions A(s) = {a1, a2, ... ak}\nlearn or estimate p(a | s, A(s))\nchoose, abstain, or escalate"}</code></pre>
    <p>
      once you write the problem that way, decades of classification, ranking, selective
      prediction, calibration and decision theory become relevant. “use a chatbot” stops being the
      default formulation.
    </p>
    <p>
      this was the first big meta-research lesson: <strong>rename the problem in the language of
      older fields.</strong> the newest product may be six months old while the core mathematical
      problem is fifty years old.
    </p>

    <h2 id="classifiers">from bert to decision models</h2>
    <p>
      modern language models did not invent text classification. the interesting transition was
      representation learning. bag-of-words models could already map text to labels, but their
      representation was mostly lexical. recurrent and convolutional models learned more structure.
      transformers then made it practical to pretrain a reusable representation on enormous text
      corpora and adapt it to many downstream tasks.
    </p>
    <p>
      <a href="https://aclanthology.org/N19-1423/">bert</a> is the obvious landmark. its encoder
      sees left and right context together, and the paper showed that a pretrained representation
      could be adapted to many tasks with a small output layer. the important conceptual point for
      us was not “bert is good.” it was that <strong>language understanding and language generation
      do not have to be the same computation.</strong>
    </p>
    <p>
      that line did not disappear when decoder-only llms took over the cultural conversation.
      <a href="https://arxiv.org/abs/2412.13663">modernbert</a> revisited the encoder-only design
      with modern training and systems optimizations and found a strong performance/size/memory
      frontier for classification and retrieval. meanwhile, a large controlled study of
      <a href="https://proceedings.mlr.press/v162/wang22u.html">architecture and pretraining
      objective</a> found that causal autoregressive models are especially strong after pure
      unsupervised pretraining, while non-causal visibility plus multitask adaptation can be
      extremely competitive after task training.
    </p>
    <p>
      the lesson is not “encoders beat decoders.” the lesson is that the right inductive bias
      depends on the job. generation rewards a model that can continue arbitrary sequences.
      classification and ranking can exploit the fact that the output space is already constrained.
    </p>

    <h2 id="jev">what jev actually changed</h2>
    <p>
      this is why jev was interesting to us. not because classification was new, but because
      <a href="https://typesafe.ai/blog/introducing-system-one-models-and-jev">typesafe</a> made a
      different interface culturally legible again: unstructured state in, typed probabilistic
      decisions out. choice, binary judgment and score-shaped questions are first-class outputs
      rather than text that another parser has to interpret.
    </p>
    <p>
      there is a temptation to reverse-engineer the secret model from that behavior. we should not.
      typesafe publicly says jev uses a new architecture, a parallel sampler and a training method
      called reinforcement learning for calibrated decisions. it does <strong>not</strong> publish
      the architecture, parameter count, full corpus or RLCD algorithm. sebastian raschka&apos;s
      <a href="https://magazine.sebastianraschka.com/p/classifier-history-and-jev">excellent
      classifier history</a> argues that a modern encoder-like design is a plausible explanation.
      plausible is not the same as known.
    </p>
    <p>
      that distinction changed OpenJev and later z0intelligence. instead of pretending we could
      reproduce a hidden checkpoint, we reproduced the <strong>useful systems pattern</strong>:
      runtime-defined options, direct logit readout, shared-state reuse, trainable bounded scorers,
      probabilities, and explicit abstention.
    </p>
    <p>
      on one committed local benchmark, our direct typed-logit path returned 21 probability pairs
      in about 1.023 seconds median versus 5.332 seconds for the compact autoregressive baseline.
      that measurement did not prove we had recreated jev. it proved that changing the output
      contract alone could remove a lot of unnecessary generation.
    </p>

    <h2 id="compiler">then the compiler changed the question</h2>
    <p>
      our first instinct was still model-centric: find a tiny model that makes the right choice.
      the compiler-first experiments changed that.
    </p>
    <p>
      if an action violates authority, dependencies, privacy constraints or the task grammar, why
      should a learned policy receive that action as an option? a deterministic layer can remove it
      before inference. this is the same separation that later became explicit in AODL: intent,
      constraints and authority are not merely hints in a prompt; they can be represented as typed
      structure outside the model.
    </p>
    <pre><code>{"raw state\n   ↓\ncompile constraints + legal action set\n   ↓\nonly then ask a learned policy to rank the legal residue"}</code></pre>
    <p>
      in our early bounded-choice runs, removing illegal actions eliminated dangerous selections
      that appeared in the unfiltered control. more importantly, the compiler made the learned job
      easier. this is a recurring systems pattern: <strong>the best model optimization may be to
      shrink the model&apos;s problem.</strong>
    </p>
    <p>
      this was the origin of the current z0intelligence boundary. the model is not the authority.
      code owns legality, budgets, side effects and verification. learned systems operate inside the
      remaining uncertainty.
    </p>

    <h2 id="probability">probability has to mean something</h2>
    <p>
      once a model&apos;s confidence controls execution, confidence stops being decorative metadata.
      it becomes part of the program.
    </p>
    <p>
      suppose two classifiers both get 90% accuracy. one says 0.9 on the cases it gets right and
      0.1 on the cases it gets wrong. the other says 0.999 on everything. they have similar top-1
      accuracy and radically different value as routing primitives.
    </p>
    <p>
      the statistical literature has a language for this. the
      <a href="https://doi.org/10.1175/1520-0493%281950%29078%3C0001%3AVOFEIT%3E2.0.CO%3B2">
      brier score</a> dates to probability forecasting in 1950.
      <a href="https://doi.org/10.1198/016214506000001437">gneiting and raftery</a> explain the
      broader theory of strictly proper scoring rules: if the score is proper, a forecaster
      maximizes expected reward by reporting its real belief rather than gaming the score.
    </p>
    <p>
      deep neural networks complicated the picture. <a href="https://proceedings.mlr.press/v70/guo17a.html">
      guo et al.</a> showed that modern neural networks can be accurate and badly calibrated at the
      same time, and that simple temperature scaling often repairs a surprising amount of the gap.
    </p>
    <p>
      this is also why the distinction between RLCD and public calibration-aware RL work matters.
      <a href="https://arxiv.org/abs/2507.16806">RLCR</a> adds a proper-scoring component to the
      reinforcement-learning reward so a reasoning model is rewarded for calibrated confidence as
      well as correctness. it is a useful public mechanism for understanding why a calibration
      objective can work. there is no evidence that typesafe&apos;s unpublished RLCD algorithm is
      the same algorithm.
    </p>
    <Callout kind="warning" title="a recurring rule in this project">
      <p>
        when a company publishes behavior but not mechanism, treat the behavior as evidence and the
        mechanism as a hypothesis.
      </p>
    </Callout>

    <h2 id="abstention">abstention is old and extremely useful</h2>
    <p>
      if confidence is meaningful, the next question is obvious: why force the cheap model to answer
      every case?
    </p>
    <p>
      this is not a new trick. <a href="https://doi.org/10.1109/TIT.1970.1054406">chow&apos;s 1970
      reject-option work</a> studies the optimal tradeoff between recognition error and rejection.
      modern selective classification asks the same systems question: how much of the input
      distribution can a model cover while keeping risk below a target?
    </p>
    <p>
      <a href="https://proceedings.mlr.press/v97/geifman19a">selectivenet</a> goes further by
      learning prediction and rejection together. the important object is the
      <strong> risk-coverage curve</strong>, not one global accuracy number.
    </p>
    <p>
      this directly changed our metric. early z0intelligence experiments kept asking “which tiny
      policy has the highest accuracy?” the better production question became:
      <strong>at 95% precision, what fraction of real decisions can this cheap policy safely
      absorb?</strong>
    </p>
    <p>
      that reframing is enormous. a 400-million-parameter policy does not need to replace a frontier
      model. if it can safely absorb 20% of a high-volume decision family, it may already be useful.
      the hard tail can remain hard.
    </p>

    <h2 id="conditional">conditional compute is the bigger idea</h2>
    <p>
      at this point the research trail expands beyond classifiers. what we were really building was
      a form of <strong>conditional computation</strong>: spend more compute only when the current
      state earns it.
    </p>
    <p>
      mixture-of-experts models are one famous version. in
      <a href="https://arxiv.org/abs/1701.06538">sparsely gated mixture of experts</a>, a learned
      gate activates only a subset of a huge network. <a href="https://www.jmlr.org/papers/v23/21-0998.html">
      switch transformers</a> simplify that routing and show how sparse activation can increase
      capacity without proportional per-example compute.
    </p>
    <p>
      early-exit networks attack the problem along depth instead of width.
      <a href="https://aclanthology.org/2020.acl-main.204/">deebert</a> lets easy examples leave
      before traversing the full transformer; <a href="https://aclanthology.org/2020.acl-main.537/">
      fastbert</a> similarly makes inference depth adaptive.
    </p>
    <p>
      llm cascades lift the same idea to whole models.
      <a href="https://arxiv.org/abs/2305.05176">frugalgpt</a> formalized a family of strategies
      including cascades that conditionally move from cheap models to expensive ones.
      <a href="https://arxiv.org/abs/2406.18665">routellm</a> learns a router between stronger and
      weaker llms from preference data.
    </p>
    <p>
      these are different implementations of one principle:
    </p>
    <pre><code>{"easy state → stop early\nambiguous state → spend more\nhard state → spend the expensive capability"}</code></pre>
    <p>
      our first z0intelligence ladder was basically this principle drawn as a stack of products:
      rule → tiny specialist → nanojev/jev → small slm → orchestrator → frontier model.
    </p>

    <h2 id="routing">then the router literature humbled us</h2>
    <p>
      a beautiful cascade diagram is not evidence that routing works.
    </p>
    <p>
      the recent routing literature is increasingly useful because it is becoming harder on itself.
      <a href="https://arxiv.org/abs/2510.00202">routerarena</a> exists because router papers were
      difficult to compare under different pools, datasets and metrics.
      <a href="https://aclanthology.org/2026.findings-acl.1881/">llmrouterbench</a> re-evaluated
      routing over more than 400,000 instances, 21 datasets and 33 models. its uncomfortable result
      is that many seemingly different routers become nearly indistinguishable under one framework,
      and several fail to reliably beat simple baselines.
    </p>
    <p>
      this was exactly the kind of result our own traces were starting to produce. on a sealed
      real-trace tool-family routing cohort, a tiny deterministic keyword policy beat the learned
      Laya and Julia fast paths by a large margin. after fixing Julia&apos;s adapter until its
      publisher benchmark reproduced, the real-task result still did not improve. faithful
      integration was not the problem. task fit was.
    </p>
    <p>
      a useful independent Jev routing experiment tells the same story from another angle.
      <a href="https://github.com/TokenTrim/jev-routing-experiment">TokenTrim</a> combined retrieval
      evidence with a Jev difficulty score and reached a strong cost/accuracy frontier on
      LLMRouterBench. then the no-Jev ablation reached essentially the same frontier. retrieval was
      carrying the gain.
    </p>
    <p>
      this is what good research looks like: the ablation makes the headline less exciting and the
      understanding more useful.
    </p>

    <h2 id="systems">model choice became a systems problem</h2>
    <p>
      the machine-learning framing still missed something important: a model has to be loaded,
      served, scheduled and given context.
    </p>
    <p>
      phase 1b measured a local cold-load p50 around 13.9 seconds and model swaps around 12.9
      seconds on the relevant path. some warm decisions were hundreds of milliseconds. once the
      load cost is two orders of magnitude larger than the forward pass, a router that ignores
      residency can make a mathematically “better” choice and a systemically terrible one.
    </p>
    <p>
      this produced one of the cleaner architecture boundaries in the project:
    </p>
    <pre><code>{"z0intelligence: should this cognition happen, and what capability is justified?\nkerdoios: where should the residual allowed computation run?\nharness: execute it\ntokenomics: record what actually happened and cost\nz0evals: freeze the evidence before we believe the promotion"}</code></pre>
    <p>
      the same lesson appears inside sparse models: switch transformers are not just about a gate;
      communication, load balancing and hardware behavior matter. conditional compute is always a
      systems problem eventually.
    </p>

    <h2 id="composition">more intelligence can be negative information</h2>
    <p>
      another assumption that sounded obvious was that two useful models should compose into a more
      useful system.
    </p>
    <p>
      our composition experiments did the opposite. a NanoJev artifact was actually produced and
      consumed on almost every state, yet adding it in front of Qwen4B hurt the downstream result.
      Hammer pre-composition was worse again. the extra model output was real. the gain was not.
    </p>
    <p>
      this changed how we think about delegation too. a fast Cerebras worker later completed its
      assigned work cleanly, but the parent still consumed the original task plus a large worker
      response. the worker got faster; the parent did not do less.
    </p>
    <p>
      the relevant optimization target is therefore not “did a worker run?” it is
      <strong> how much expensive cognition disappeared while verified outcome quality stayed
      fixed?</strong>
    </p>
    <p>
      that pushes the architecture toward typed, compressed intermediate representations. a worker
      that can return one validated decision, artifact handle or minimal evidence packet can be more
      valuable than a smarter worker that returns another essay for the parent to reread.
    </p>

    <h2 id="specialists">specialize the repeated cognition</h2>
    <p>
      the original personal-intelligence idea was much simpler: train a small language or
      vision-language model on a user&apos;s history so it understands how they work.
    </p>
    <p>
      the research above made that idea more compositional. mutable facts should be retrieved with
      provenance. stable repeated behavior can be learned. and each repeated behavior should be
      allowed to choose its own cheapest representation.
    </p>
    <pre><code>{"history → episodes of state / action / outcome\n\nthen compete:\nrule\nridge / linear\nmlp\nmushroom-body policy\ntemporal recurrent policy\nsmall semantic model\nfrontier model"}</code></pre>
    <p>
      that is why z0intelligence now looks more like a population of specialists than one student
      model. the model family is not sacred. deterministic rules remain mandatory controls. a
      learned model only earns traffic if it expands the measured quality/coverage/latency frontier.
    </p>
    <p>
      this also explains why observed trajectories are more valuable than giant manual labeling
      projects. agent histories already contain weak and strong supervision: actions, retries,
      tests, tool results, corrections, merges, rejections and downstream outcomes. the research
      problem is to compile those traces into causally honest episodes without leaking future
      information into the input.
    </p>

    <h2 id="biology">why we looked at flies</h2>
    <p>
      the fly work can look like a strange detour if you start from llm routing. it makes more sense
      if you start from the question “what is the smallest trainable mechanism that can reliably
      associate a high-dimensional state with a bounded action?”
    </p>
    <p>
      the drosophila mushroom body is a compact associative-learning system.
      the <a href="https://www.nature.com/articles/nature23455">2017 larval mushroom-body
      connectome</a> found that most Kenyon cells integrate combinations of projection-neuron
      inputs, producing a sparse expanded representation that feeds learned output pathways. this
      resembles a useful machine-learning recipe: expand, sparsify, then train a tiny readout.
    </p>
    <p>
      connectomics later scaled dramatically. the 2023
      <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC7614541/">larval whole-brain connectome</a>
      mapped 3,016 neurons and 548,000 synapses. the 2024
      <a href="https://www.nature.com/articles/s41586-024-07558-y">adult FlyWire connectome</a>
      reached roughly 139,000 neurons and tens of millions of synapses.
    </p>
    <p>
      our first reaction was predictable: maybe a whole evolved circuit gives us a better tiny
      controller. the better research stance is stricter. biology is a
      <strong> hypothesis generator, not an authority.</strong>
    </p>
    <p>
      full MaleCNS-scale simulation has to compete with a GRU, random reservoir, rewired topology,
      ridge model and the distilled motif itself. if a tiny mushroom-body-style readout preserves
      the useful effect, deploy the tiny readout. the interesting biological circuit can stay in
      the lab.
    </p>

    <h2 id="compile">the end state is downward compilation</h2>
    <p>
      this is the idea that now unifies the whole project.
    </p>
    <pre><code>{"novel task\n  ↓\nfrontier reasoning\n  ↓ repeated evidence\nbounded learned specialist\n  ↓ stable region\ndeterministic routine\n  ↓\nno model call"}</code></pre>
    <p>
      we call this “compiling cognition downward.” it resembles distillation, cascades and early
      exit, but the representation is allowed to change completely. a frontier decision can become
      an slm policy; the slm policy can become a sparse tiny classifier; the stable region of that
      classifier can become a declarative rule.
    </p>
    <p>
      the routine compiler in z0intelligence is deliberately conservative: discover on open data,
      tune on development data, credit only on sealed data, preserve fallback, and demote when
      future evidence drifts. the point is not to generate clever rules with an llm. the point is
      to prove that a region no longer needs a learned model.
    </p>

    <h2 id="method">how we actually did the research</h2>
    <p>
      the most important thing llms changed for me was not that they could summarize papers. paper
      summaries are cheap. the useful change was that i could keep a much larger hypothesis graph
      alive at once.
    </p>
    <p>
      the loop that emerged eventually got a name in our repos — ABAB — but the structure is older
      than the name:
    </p>
    <pre><code>{"A: diagnose the phenomenon and propose rival explanations\nB: run a frozen experiment that could falsify them\nA: update the mental model from the result\nB: run the smallest next experiment that distinguishes what remains"}</code></pre>
    <p>
      this is closely related to Bayesian experimental design and active learning. in
      <a href="https://authors.library.caltech.edu/records/efefp-2j353">MacKay&apos;s 1992
      information-based active data selection</a>, candidate measurements are valued by how much
      information they are expected to provide. our practical version is:
      <strong>prefer the cheapest experiment whose possible outcomes would make us choose different
      architectures.</strong>
    </p>
    <p>
      that rule saved us from endless benchmark sweeps. when two explanations remain, adding ten
      more models is often lower-value than one test designed so hypothesis A and hypothesis B make
      opposite predictions.
    </p>
    <p>
      the other half is the frozen judge. the system proposing the experiment cannot be allowed to
      rewrite the criterion that decides whether it won. that is why z0evals, sealed cohorts,
      independent outcomes and exact execution receipts became architectural components rather than
      paperwork.
    </p>

    <h2 id="llms">what llms accelerate — and what they do not</h2>
    <p>
      recent work on llms for science makes the opportunity and the limitation pretty clear.
      systems such as <a href="https://arxiv.org/abs/2502.18864">the ai co-scientist</a> and
      <a href="https://aclanthology.org/2025.findings-emnlp.320/">agent laboratory</a> show that
      llms can help with literature search, hypothesis generation, code, experimentation and
      writing. at the same time, a recent
      <a href="https://arxiv.org/abs/2512.15567">scientific-discovery evaluation</a> finds a
      substantial gap between doing well on science questions and succeeding at iterative,
      scenario-grounded discovery.
    </p>
    <p>
      that matches our experience. llms are extraordinary research compressors when they are used
      to:
    </p>
    <ul>
      <li>translate a vague phenomenon into the vocabulary of several fields;</li>
      <li>walk backward through citations until the idea stops looking new;</li>
      <li>explain prerequisite mathematics at exactly the depth needed for the next paper;</li>
      <li>compare methods under one set of assumptions;</li>
      <li>generate competing explanations instead of one confident story;</li>
      <li>turn those explanations into runnable discriminating experiments;</li>
      <li>write instrumentation, replay harnesses and analysis code quickly;</li>
      <li>preserve a research ledger so yesterday&apos;s failed hypothesis is not rediscovered next week.</li>
    </ul>
    <p>
      but the llm should not get to decide that its own explanation is correct. the expensive human
      skill is still <strong>research judgment</strong>: deciding what question matters, what
      evidence would change the architecture, whether a benchmark represents the real distribution,
      and whether two measurements are actually comparable.
    </p>

    <h2 id="sota">our current synthesis of the frontier</h2>
    <p>
      “state of the art” is usually presented as a model leaderboard. the z0intelligence research
      trail makes me think the more interesting frontier is architectural.
    </p>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead>
          <tr><th>problem</th><th>frontier pattern</th><th>why it matters</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>legal action space</td>
            <td>typed compiler / deterministic constraints</td>
            <td>remove impossible decisions before learning</td>
          </tr>
          <tr>
            <td>bounded semantic choice</td>
            <td>task-fit discriminative / decision model</td>
            <td>do not pay for arbitrary text generation when the output is finite</td>
          </tr>
          <tr>
            <td>confidence</td>
            <td>proper scoring + calibration</td>
            <td>probability must be usable as a control signal</td>
          </tr>
          <tr>
            <td>hard tail</td>
            <td>selective prediction / abstention</td>
            <td>optimize safe coverage instead of forcing one model to solve everything</td>
          </tr>
          <tr>
            <td>heterogeneous models</td>
            <td>routing + strong simple baselines + online feedback</td>
            <td>model complementarity is real; router value is not automatic</td>
          </tr>
          <tr>
            <td>compute</td>
            <td>conditional execution + residency-aware placement</td>
            <td>forward latency is only one component of system cost</td>
          </tr>
          <tr>
            <td>repeated behavior</td>
            <td>specialists → deterministic routines</td>
            <td>stable cognition should eventually stop being a model call</td>
          </tr>
          <tr>
            <td>learning loop</td>
            <td>outcome-backed episodes + sealed credit</td>
            <td>imitating a teacher is not the same as improving the system</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p>
      there are already routing systems moving toward online feedback. for example,
      <a href="https://arxiv.org/abs/2510.07429">bandit-feedback routing</a> treats model selection
      as a contextual-bandit problem where only the chosen model&apos;s outcome may be observed,
      which is much closer to deployment than assuming a complete reward matrix.
      <a href="https://arxiv.org/abs/2605.30736">orcarouter</a> similarly combines offline
      initialization with optional online contextual-bandit updates.
    </p>
    <p>
      the z0intelligence version adds another axis: <strong>the action is not always “choose an
      llm.”</strong> the action may be “use a rule,” “retrieve context,” “run a tiny specialist,”
      “ask a calibrated decision model,” “load a local slm,” or “spend the frontier model.”
    </p>

    <h2 id="next">the experiments that would change my mind</h2>
    <p>
      a research synthesis should end with falsifiers, not vibes. these are the experiments that
      matter most to the current theory:
    </p>
    <ol>
      <li>
        <strong>option-conditioned tiny policy vs direct semantic scorer.</strong> can one small
        dynamic-option specialist generalize across changing tool/skill sets while preserving
        calibrated risk/coverage?
      </li>
      <li>
        <strong>residency-aware routing.</strong> does adding current memory residency, swap cost
        and queue state materially beat a quality-only router on end-to-end verified utility?
      </li>
      <li>
        <strong>typed delegation.</strong> if a worker returns a compact typed artifact instead of
        prose, does parent token use finally fall without lowering task success?
      </li>
      <li>
        <strong>routine compilation.</strong> what fraction of a credited specialist&apos;s stable
        region can be replaced by deterministic rules on future traffic?
      </li>
      <li>
        <strong>mushroom-body vs boring controls.</strong> on real outcome-backed decision families,
        does sparse local plasticity beat ridge/MLP at the same footprint and safe-coverage target?
      </li>
      <li>
        <strong>active-label allocation.</strong> does asking Jev/frontier teachers only on
        disagreement and high-information states outperform labeling everything at equal cost?
      </li>
      <li>
        <strong>cross-harness transfer.</strong> does a policy learned from one harness preserve its
        lift on another, or are we mostly learning harness-specific surface cues?
      </li>
    </ol>
    <p>
      if these fail, the architecture should get simpler again.
    </p>

    <h2 id="learn">a reusable way to learn a field fast</h2>
    <p>
      if i had to turn this experience into a playbook for learning a technical frontier with llms,
      it would look like this:
    </p>
    <ol>
      <li>
        <strong>start with a painful real phenomenon.</strong> “why is this slow?” is better than
        “teach me model routing.”
      </li>
      <li>
        <strong>decompose the phenomenon into smaller mathematical jobs.</strong> generation,
        classification, ranking, retrieval, control, scheduling, verification and optimization have
        different literatures.
      </li>
      <li>
        <strong>use the llm to discover vocabulary and walk the citation graph backward.</strong>
        keep asking “what older field already studied this?”
      </li>
      <li>
        <strong>build rival explanations.</strong> do not let the research session collapse into
        one persuasive narrative.
      </li>
      <li>
        <strong>run the smallest discriminating experiment.</strong> maximize expected information
        gain, not benchmark volume.
      </li>
      <li>
        <strong>freeze evidence before interpretation.</strong> preserve traces, revisions,
        negatives and failed hypotheses.
      </li>
      <li>
        <strong>compress the result into a new mental model, then repeat.</strong> the output of
        research is not the paper summary. it is a model that predicts what the next experiment
        should do.
      </li>
    </ol>
    <p>
      this is the part that feels genuinely new in the llm era. the barrier to entering a field used
      to include an enormous amount of mechanical search, prerequisite lookup, code translation and
      notation decoding. llms can compress much of that. they cannot remove the need to decide what
      is true.
    </p>
    <Callout kind="info" title="the meta-thesis">
      <p>
        llms make access to research cheap. the scarce skill becomes building a falsifiable mental
        model of the field faster than you fool yourself.
      </p>
    </Callout>
  </>
);

const explore = (
  <>
    <h2>paper map</h2>
    <p>
      this is the compact research trail behind the story. “used by us” means it influenced a
      hypothesis or interpretation; it does not imply that the paper proves our architecture.
    </p>

    <div className="x-table-wrap">
      <table className="x-table">
        <thead><tr><th>thread</th><th>references</th><th>what we took from it</th></tr></thead>
        <tbody>
          <tr>
            <td>representation + classifiers</td>
            <td>
              <a href="https://aclanthology.org/N19-1423/">bert</a>,{" "}
              <a href="https://proceedings.mlr.press/v162/wang22u.html">architecture/objective study</a>,{" "}
              <a href="https://arxiv.org/abs/2412.13663">modernbert</a>
            </td>
            <td>understanding text and generating text can justify different computation</td>
          </tr>
          <tr>
            <td>calibration</td>
            <td>
              <a href="https://doi.org/10.1175/1520-0493%281950%29078%3C0001%3AVOFEIT%3E2.0.CO%3B2">brier</a>,{" "}
              <a href="https://doi.org/10.1198/016214506000001437">proper scoring rules</a>,{" "}
              <a href="https://proceedings.mlr.press/v70/guo17a.html">guo et al.</a>,{" "}
              <a href="https://arxiv.org/abs/2507.16806">rlcr</a>
            </td>
            <td>confidence is a prediction target, not a cosmetic logit</td>
          </tr>
          <tr>
            <td>selective prediction</td>
            <td>
              <a href="https://doi.org/10.1109/TIT.1970.1054406">chow</a>,{" "}
              <a href="https://proceedings.mlr.press/v97/geifman19a">selectivenet</a>
            </td>
            <td>optimize risk vs coverage and escalate the hard tail</td>
          </tr>
          <tr>
            <td>conditional compute</td>
            <td>
              <a href="https://arxiv.org/abs/1701.06538">sparse moe</a>,{" "}
              <a href="https://www.jmlr.org/papers/v23/21-0998.html">switch transformer</a>,{" "}
              <a href="https://aclanthology.org/2020.acl-main.204/">deebert</a>,{" "}
              <a href="https://arxiv.org/abs/2305.05176">frugalgpt</a>
            </td>
            <td>easy states should stop before paying for full capacity</td>
          </tr>
          <tr>
            <td>llm routing</td>
            <td>
              <a href="https://arxiv.org/abs/2406.18665">routellm</a>,{" "}
              <a href="https://arxiv.org/abs/2510.00202">routerarena</a>,{" "}
              <a href="https://aclanthology.org/2026.findings-acl.1881/">llmrouterbench</a>,{" "}
              <a href="https://arxiv.org/abs/2510.07429">bandit routing</a>
            </td>
            <td>complementarity is real; sophisticated routers still have to beat trivial controls</td>
          </tr>
          <tr>
            <td>jev</td>
            <td>
              <a href="https://typesafe.ai/blog/introducing-system-one-models-and-jev">typesafe launch</a>,{" "}
              <a href="https://magazine.sebastianraschka.com/p/classifier-history-and-jev">raschka history</a>,{" "}
              <a href="https://arxiv.org/abs/2609.30216">jev in the wild</a>,{" "}
              <a href="https://github.com/TokenTrim/jev-routing-experiment">routing ablation</a>
            </td>
            <td>typed probabilistic decisions are useful; hidden architecture claims stay unknown</td>
          </tr>
          <tr>
            <td>biological specialists</td>
            <td>
              <a href="https://www.nature.com/articles/nature23455">mushroom body connectome</a>,{" "}
              <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC7614541/">larval brain connectome</a>,{" "}
              <a href="https://www.nature.com/articles/s41586-024-07558-y">adult FlyWire</a>
            </td>
            <td>biology supplies motifs to test, not exemptions from controls</td>
          </tr>
          <tr>
            <td>research acceleration</td>
            <td>
              <a href="https://authors.library.caltech.edu/records/efefp-2j353">information gain</a>,{" "}
              <a href="https://arxiv.org/abs/2502.18864">ai co-scientist</a>,{" "}
              <a href="https://aclanthology.org/2025.findings-emnlp.320/">agent laboratory</a>,{" "}
              <a href="https://arxiv.org/abs/2512.15567">scientific-discovery eval</a>
            </td>
            <td>llms can compress search and experimentation; research judgment still needs external evidence</td>
          </tr>
        </tbody>
      </table>
    </div>

    <h2>our evidence checkpoints</h2>
    <ul>
      <li>
        <a href="../">phase 1b: how much of the llm do we actually need?</a> — compiler-first
        legality, Hammer/Qwen/Nemotron/FunctionGemma/NanoJev comparisons, residency, composition,
        orchestration and the first architecture collapse.
      </li>
      <li>
        <a href="../z0intelligence-function-routing/">what actually deserves a model?</a> — the
        later evidence: real Jev reproduction correction, NanoJev objective failure, Laya/Julia,
        real-trace rule routing, physical provider execution, free-tier and Cerebras delegation.
      </li>
      <li>
        <a href="https://github.com/kvnloo/z0intelligence/blob/master/docs/RESEARCH.md">
          z0intelligence research context
        </a> — the durable research ledger: retrieve truth / learn behavior, safe coverage,
        specialists, mushroom bodies, ABAB and downward compilation.
      </li>
    </ul>

    <h2>claim discipline</h2>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead><tr><th>kind</th><th>example</th><th>how to read it</th></tr></thead>
        <tbody>
          <tr>
            <td>published result</td>
            <td>llmrouterbench simple-baseline findings</td>
            <td>the paper&apos;s result on its stated benchmark</td>
          </tr>
          <tr>
            <td>vendor claim</td>
            <td>jev uses RLCD / new architecture / parallel sampler</td>
            <td>attributed to typesafe; not independently inspectable mechanism</td>
          </tr>
          <tr>
            <td>our measurement</td>
            <td>phase 1b bounded-routing and residency receipts</td>
            <td>only the frozen cohort/hardware/path we actually measured</td>
          </tr>
          <tr>
            <td>our synthesis</td>
            <td>continuous downward compilation is the useful architecture</td>
            <td>a falsifiable theory assembled from literature + experiments, not a paper result</td>
          </tr>
          <tr>
            <td>future hypothesis</td>
            <td>mushroom-body specialists will expand the safe-coverage frontier</td>
            <td>interesting only after it beats boring controls on sealed outcomes</td>
          </tr>
        </tbody>
      </table>
    </div>

    <h2>the research loop in one screen</h2>
    <pre><code>{"real phenomenon\n→ name the smaller mathematical problem\n→ map the literature backward\n→ keep rival explanations\n→ choose the cheapest discriminating experiment\n→ freeze execution + outcome evidence\n→ update the theory\n→ compile the winning behavior downward\n→ repeat"}</code></pre>
  </>
);

export default function Page() {
  return (
    <StoryShell
      meta={meta}
      banner={banner}
      toc={toc}
      story={story}
      explore={explore}
      exploreLabel="show me the research map"
      storyLabel="back to the theory"
    />
  );
}
