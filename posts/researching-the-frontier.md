---
title: "How Do You Learn the Frontier Fast?"
subtitle: "The research trail behind z0intelligence — and what using LLMs taught me about learning to think like a researcher"
status: research-synthesis
author: "Zer0 Research"
date: "September 29, 2026"
---

# How do you learn the frontier fast?

I did not start with a literature review.

I started with a practical annoyance:

> **Why are we paying an autoregressive language model to make decisions that look much smaller than language generation?**

That question eventually became z0intelligence.

The engineering posts tell the empirical story: what we ran, what failed, what survived, and what the receipts say. This post is the layer underneath them. It is about how the mental model changed as we moved between papers and experiments, and about a broader question I care about now:

> **How can someone enter a fast-moving technical field, build a research-grade understanding of the frontier, and begin forming useful original hypotheses much faster with LLMs — without outsourcing the part that actually requires judgment?**

The answer I have so far is not "read more papers."

It is:

```text
real phenomenon
→ smaller mathematical question
→ competing explanations
→ literature map
→ assumptions
→ cheapest discriminating experiment
→ frozen evidence
→ revised mental model
→ next question
```

LLMs compress the middle of this loop enormously.

They do not remove the need for the loop.

---

## 1. Start from the problem, not the paper

The first z0intelligence question was not "what is the best router?" It was not "how does Jev work?" It was not even "which small model should I run locally?"

It was:

> **How much expensive general intelligence does an agent actually need on each step?**

An agent loop looks like one continuous act of intelligence when you watch it from the outside. Zoom in and it fragments into very different jobs:

- understand an open-ended request;
- retrieve the relevant context;
- decide whether a tool is applicable;
- choose among a few legal actions;
- detect whether a retry is warranted;
- decide whether a result is complete;
- verify an outcome;
- choose whether to escalate;
- sometimes do genuinely novel reasoning.

Those are not the same computational problem.

That sounds obvious after writing it down. It was not obvious in the architecture we started with.

A frontier LLM is a fantastically general machine. If the runtime asks it to make a five-way decision, we are paying for a model capable of representing and generating an enormous language distribution and using a microscopic portion of that capability.

That gave us the question that survived every later architecture change:

> **What is the smallest mechanism that preserves the verified behavior required by this exact function?**

That formulation matters because it turns "which model is smartest?" into a much more productive research problem.

It also gives the first meta-research lesson:

> **Rename the problem in the vocabulary of older fields.**

The newest product may be six months old. The mathematical problem underneath it may be fifty years old.

---

## 2. A decision is not necessarily a generation problem

An autoregressive language model models a sequence:

[
p(x_1,ldots,x_T)=prod_t p(x_tmid x_{<t})
]

At inference time it predicts a token, appends it, predicts another token, and continues.

That interface is exactly what you want when the output is an arbitrary piece of language.

But many agent decisions look more like:

[
s in mathcal{S}
]

[
A(s)={a_1,ldots,a_k}
]

[
p(amid s,A(s))
]

Then the runtime chooses an action, abstains, or escalates.

The output domain is already known.

Once the problem is written this way, a much older research universe becomes relevant: classification, ranking, probabilistic forecasting, selective prediction, decision theory, contextual bandits, conditional computation, and scheduling.

This was the first major conceptual shift behind z0intelligence.

The goal was no longer "find a smaller chatbot."

It was "stop treating every decision as chatbot-shaped."

---

## 3. From text classifiers to modern decision models

Text classification existed long before transformers.

Bag-of-words and linear classifiers can still be excellent baselines when the relevant signal is mostly lexical. Recurrent and convolutional networks learned richer representations. The transformer era changed the economics of representation learning: one large pretrained representation could be adapted to many downstream problems.

[BERT](https://aclanthology.org/N19-1423/) is the obvious landmark. Its bidirectional encoder learns a representation from both left and right context and can be adapted to downstream tasks with a small output head.

The theoretical lesson for us was more important than the particular model:

> **language understanding and language generation do not have to be the same computation.**

Decoder-only LLMs became culturally dominant because generation is so general and useful. That did not erase the inductive advantages of discriminative models when the output is constrained.

[ModernBERT](https://arxiv.org/abs/2412.13663) revisits the encoder-only design with modern training and systems improvements and reports a strong performance/size/memory frontier across classification and retrieval workloads.

A large controlled study of [architecture and pretraining objectives](https://proceedings.mlr.press/v162/wang22u.html) makes the picture more nuanced. Causal autoregressive models can be particularly strong after pure unsupervised pretraining, while non-causal visibility and masked objectives can become highly competitive after multitask adaptation.

So the conclusion is not:

> encoders beat decoders.

It is:

> **the best inductive bias depends on the job and the adaptation regime.**

Generation benefits from an architecture designed to continue arbitrary sequences.

Classification and ranking can exploit the fact that the output space is already bounded.

That distinction becomes even more important when the classifier sits inside a runtime loop rather than at the end of an offline benchmark.

---

## 4. What Jev actually changed for us

This is why [TypeSafe Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev) was interesting.

The novelty was not that neural networks could classify things. The interesting part was the systems interface:

```text
unstructured state
     ↓
typed question
     ↓
bounded choice / boolean / score
     ↓
probability distribution
```

That is a much better primitive for many agent decisions than "generate some JSON and hope the parser agrees."

TypeSafe publicly describes Jev as part of a "System One" stack using a new architecture, a parallel sampler, and a training approach it calls Reinforcement Learning for Calibrated Decisions (RLCD).

What TypeSafe does **not** publish is just as important:

- the exact architecture;
- the parameter count;
- the full training corpus;
- the sampler internals;
- the RLCD algorithm.

Sebastian Raschka's [classifier-history article](https://magazine.sebastianraschka.com/p/classifier-history-and-jev) makes a technically plausible argument that a modern encoder-like design could explain some of Jev's properties.

That is an educated hypothesis.

It is not evidence that Jev *is* ModernBERT or any other particular architecture.

That distinction changed how we approached OpenJev and then z0intelligence.

We stopped trying to "reproduce Jev" as though the hidden model were known.

Instead, we reproduced the systems pattern we could actually inspect:

- runtime-defined options;
- generation-free scoring;
- direct probability readout;
- shared-state reuse;
- trainable bounded scorers;
- explicit abstention;
- reproducible evaluation.

On one committed OpenJev benchmark, 21 direct typed decisions took about 1.023 seconds median versus 5.332 seconds for the compact autoregressive JSON-array baseline.

That does not show that we rebuilt TypeSafe's model.

It shows something more useful:

> **changing the output contract can remove a large amount of unnecessary generation even before inventing a new architecture.**

---

## 5. Then the compiler changed the question

Our first instinct was still model-centric.

Find a model that chooses the correct action.

Then the compiler-first experiments changed the framing.

Suppose the runtime already knows:

- an action violates authority;
- a dependency is missing;
- a resource is unavailable;
- an operation violates a privacy policy;
- the current task grammar makes an action impossible.

Why present that action to a learned policy?

A deterministic layer can remove it first.

```text
raw state
   ↓
compile constraints
   ↓
construct legal action set
   ↓
learned policy ranks only the residue
```

In the Phase 1/1B bounded-choice work, the unfiltered controls selected dangerous actions. Compiler-first arms eliminated those selections.

More importantly, the compiler made the machine-learning problem smaller.

This is an underappreciated form of intelligence:

> **the best model optimization can be to reduce the problem before the model sees it.**

The same idea later became cleaner through AODL. Intent, authority, constraints, budgets, and participation do not have to live as prose suggestions inside a prompt. They can exist as typed structure outside the model.

That gave z0intelligence one of its most durable boundaries:

- code owns legality and authority;
- verifiers own observable success criteria;
- learned policies operate inside the remaining uncertainty.

The model is not the constitution.

---

## 6. If confidence changes control flow, probability quality matters

Once the output is probabilistic, it is tempting to treat confidence as a nice UI feature.

For z0intelligence it is part of the program.

Consider two classifiers with the same top-1 accuracy.

Classifier A says 0.9 on cases it gets right and becomes uncertain near its errors.

Classifier B says 0.999 on everything.

Those classifiers are not equally useful if the runtime uses confidence to decide whether to act or escalate.

The statistical literature on this is old.

The [Brier score](https://doi.org/10.1175/1520-0493%281950%29078%3C0001%3AVOFEIT%3E2.0.CO%3B2) comes from probabilistic forecasting in 1950.

[Gneiting and Raftery's treatment of proper scoring rules](https://doi.org/10.1198/016214506000001437) gives the general idea: a scoring rule is *proper* when a forecaster optimizes expected score by reporting its true belief.

This is exactly what we want from a decision model whose probability becomes a control signal.

Modern neural networks complicated that story. [Guo et al.](https://proceedings.mlr.press/v70/guo17a.html) showed that deep networks can be accurate and poorly calibrated at the same time, and that temperature scaling can repair a surprising amount of the mismatch.

Recent reinforcement-learning work asks whether probability quality can be trained directly. [RLCR](https://arxiv.org/abs/2507.16806) adds a Brier-style confidence component to a correctness reward and reports substantially improved calibration in its evaluated reasoning settings.

This is relevant to understanding the motivation behind a phrase like "reinforcement learning for calibrated decisions."

It does **not** establish that TypeSafe's undisclosed RLCD algorithm is RLCR.

One of the rules we learned to apply repeatedly is:

> **when a company publishes behavior but not mechanism, treat the behavior as evidence and the mechanism as a hypothesis.**

---

## 7. Abstention is not a hack

If confidence is meaningful, the next question becomes obvious:

Why force the cheap model to answer every input?

The reject option has a long history.

[Chow's 1970 work](https://doi.org/10.1109/TIT.1970.1054406) studies the tradeoff between recognition error and rejection.

Modern selective classification makes the same idea operational. [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a) learns prediction and rejection jointly.

The relevant object is not only accuracy.

It is the **risk-coverage curve**:

> as I allow the cheap model to handle more traffic, how quickly does its error increase?

This was one of the most important metric changes inside z0intelligence.

Early experiments asked:

> which tiny policy has the highest accuracy?

The production question became:

> **at a required precision, what fraction of the real distribution can this cheap policy safely absorb?**

That changes the architecture completely.

A 400M model does not have to replace a frontier model.

If it reliably absorbs 20% of a high-volume decision family while escalating the rest, that may already be a major systems win.

The hard tail is allowed to remain hard.

---

## 8. We were rediscovering conditional computation

At this point the research trail stopped being only about classifiers.

What we were really building was a form of **conditional computation**:

> spend additional compute only when the current state earns it.

There are many versions of this idea.

[Sparsely gated mixture-of-experts](https://arxiv.org/abs/1701.06538) activates only a subset of a huge network for each example.

[Switch Transformers](https://www.jmlr.org/papers/v23/21-0998.html) simplify sparse expert routing and show how model capacity can grow without proportional per-token computation.

Early-exit models vary depth rather than expert selection. [DeeBERT](https://aclanthology.org/2020.acl-main.204/) allows easy examples to exit before traversing the full transformer. FastBERT explores a similar adaptive-inference idea.

Model cascades move the conditional-compute boundary outside a single network. [FrugalGPT](https://arxiv.org/abs/2305.05176) formalizes strategies for combining models under cost constraints, including cascades that try cheap systems before expensive ones.

[RouteLLM](https://arxiv.org/abs/2406.18665) learns when to route between weaker and stronger LLMs using preference information.

Different mechanism, same deeper principle:

```text
easy state
→ stop

ambiguous state
→ spend more

hard state
→ unlock the expensive capability
```

Our first z0intelligence ladder was essentially this idea expressed as products:

```text
rule
→ mushroom / tiny policy
→ nanojev / jev
→ small SLM
→ orchestrator
→ frontier model
```

It looked elegant.

Then we evaluated it.

---

## 9. The router literature — and our own traces — humbled the elegant diagram

A routing architecture can sound obviously correct while contributing almost nothing.

This is why recent routing evaluation work became unusually useful to us.

[RouterArena](https://arxiv.org/abs/2510.00202) responds to a basic problem: router results are hard to compare when each paper changes the model pool, datasets, constraints, and metrics.

[LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/) re-evaluates routing methods over more than 400,000 instances, 21 datasets, and 33 models.

One of its uncomfortable conclusions is that many methods that look different in isolation become difficult to distinguish under a common evaluation, and several fail to reliably beat strong simple baselines.

Our real traces produced the same kind of correction.

On a sealed tool-family routing cohort:

- a deterministic keyword rule won;
- Laya performed much worse;
- Julia performed worse still.

We did not stop at "Julia is bad."

We repaired its adapter until the publisher's reference tasks reproduced correctly.

Then we ran the real routing task again.

It still lost.

That is an important distinction:

> **faithful integration is not the same thing as task fit.**

A third-party Jev routing experiment from [TokenTrim](https://github.com/TokenTrim/jev-routing-experiment) contains an even cleaner lesson.

The combined Jev-difficulty + retrieval router reached a strong cost/accuracy frontier.

Then the authors ablated Jev.

The no-Jev version landed essentially on the same frontier.

Retrieval was doing the work.

That ablation makes the marketing story weaker and the science stronger.

---

## 10. Then "model routing" became a systems problem

The machine-learning framing still omitted a huge variable.

A model has to be loaded.

It has to remain resident.

It competes for VRAM.

It may sit behind a server queue.

It receives context.

It may trigger a swap before doing one tiny forward pass.

In Phase 1B we observed cold-load and swap costs on the order of tens of seconds for parts of the local path, while warm decisions could be hundreds of milliseconds.

At that point:

> "which model is best for this state?"

is not a complete question.

The router also needs to know:

- what is already resident;
- what loading the model costs;
- what is queued;
- what its expected future reuse is;
- whether the quality improvement is worth the transition cost.

That is why z0intelligence and Kerdoios separated.

```text
z0intelligence
  should this cognition happen?
  what capability is justified?

kerdoios
  where should the allowed residual computation run?

harness
  execute it

tokenomics
  record what actually happened and cost

z0evals
  freeze the evidence before promotion
```

This is not just software modularity.

It reflects two different optimization problems.

---

## 11. More intelligence can be negative information

Another assumption we had to kill was:

> if model A is useful and model B is useful, A → B should be better.

Our composition experiments did not cooperate.

A NanoJev artifact was actually delivered and consumed on almost all states, yet feeding it into Qwen4B made the downstream result worse.

A Hammer pre-composition was worse again.

This was not a serialization failure.

The additional signal existed.

It simply did not help.

That changed the way we thought about delegation too.

Later, a Cerebras worker could execute its task quickly and correctly, yet delegation still caused the parent to consume more work because the parent read the original problem **and** a large worker response.

The worker got faster.

The system did not necessarily get cheaper.

The optimization target therefore became:

> **How much expensive cognition disappears while verified outcome quality remains fixed?**

This strongly favors typed and compressed intermediate representations.

A worker that returns one bounded decision, a validated artifact reference, or a minimal evidence packet can be more useful than a brilliant worker that sends another page of prose back to the parent.

---

## 12. The personal-model idea decomposed into specialists

Before z0intelligence, the idea was closer to:

> train a small language / vision-language model on my history so it learns how I work.

I still think the motivation is right.

The architecture changed.

The crucial distinction became:

> **retrieve what is currently true; learn what is stable about behavior.**

Mutable project state, relationships, documents, schedules, and current facts belong in retrieval with provenance.

Stable patterns are better candidates for learning:

- preferences;
- recurring judgments;
- tool selection;
- retry policies;
- verification decisions;
- intent transformations;
- routing;
- recovery;
- familiar workflow fragments.

And even then, one model family should not be assumed to own all of them.

For each capability we can let candidates compete:

```text
deterministic rule
ridge / linear
MLP
mushroom-body policy
small recurrent policy
semantic scorer
SLM
frontier model
```

The winner is the cheapest representation that preserves the verified outcome and satisfies the coverage requirement.

This is why z0intelligence became an **army of specialists** rather than one personalized student model.

---

## 13. Why we ended up reading fly neuroscience

If you start from "LLM routing," the fly research looks like a bizarre detour.

If you start from the actual question, it is more reasonable:

> what is the smallest trainable mechanism that can associate a high-dimensional state with a bounded action?

The Drosophila mushroom body is an extremely compact associative-learning system.

The [2017 larval mushroom-body connectome](https://www.nature.com/articles/nature23455) showed Kenyon cells integrating combinations of projection-neuron inputs and feeding learned output pathways.

As an engineering abstraction this suggests a simple candidate:

```text
structured inputs
→ expansion
→ sparse k-winner code
→ tiny plastic readout
→ bounded decision
```

Connectomics then made much larger biological circuits experimentally accessible.

The [larval whole-brain connectome](https://pmc.ncbi.nlm.nih.gov/articles/PMC7614541/) mapped 3,016 neurons and roughly 548,000 synapses.

The adult [FlyWire connectome](https://www.nature.com/articles/s41586-024-07558-y) later scaled to roughly 139,000 neurons and tens of millions of chemical synapses.

It is easy to become hypnotized by the complexity.

Our research rule is the opposite:

> **biology is a hypothesis generator, not an authority.**

If a mushroom-body topology is useful, it must beat ridge and MLP controls.

If a MaleCNS-derived recurrent motif helps, it must beat a GRU, random reservoir, and rewired topology.

If a useful biological circuit can be distilled into a tiny ordinary computation, deploy the tiny computation.

The full simulation can stay a research instrument.

---

## 14. The end state is not routing. It is downward compilation.

This is the idea that now unifies z0intelligence.

```text
novel task
  ↓
frontier reasoning
  ↓ repeated evidence
learned bounded specialist
  ↓ stable region
deterministic routine
  ↓
no model call
```

A lot of ML research assumes the representation remains a neural model while training improves it.

We want to allow the representation to change completely.

A frontier decision can become a smaller learned policy.

A stable region of that policy can become a rule.

Eventually the best "model" for a repeated decision can be no model at all.

That is why the Routine Compiler exists.

It does not ask an LLM to generate clever production code and trust it.

The intended lifecycle is:

1. discover a candidate rule on open evidence;
2. prune/tune on development data;
3. credit on sealed data;
4. preserve fail-open fallback;
5. observe future traffic;
6. demote or split the rule when drift appears.

Repeated cognition should continuously migrate to the cheapest representation that still passes its verifier.

---

## 15. The research method became part of the architecture

The most important thing LLMs changed for me was not paper summarization.

Summaries are cheap.

The useful change was that I could keep a much larger *hypothesis graph* alive at once.

Eventually we formalized the loop as ABAB:

```text
A — diagnose
    what phenomenon are we seeing?
    what rival explanations survive?

B — experiment
    run a frozen test that can falsify them

A — update
    revise the mental model from the evidence

B — discriminate
    run the cheapest test whose outcomes separate what remains
```

This has a close relationship to active learning and Bayesian experimental design.

[David MacKay's 1992 information-based active-data-selection paper](https://authors.library.caltech.edu/records/efefp-2j353) frames observations in terms of expected information.

Our rough operational version became:

[
priority
propto
rac{
EIG 	imes impact 	imes decision change 	imes transferability
}{
cost
}
]

The exact formula is not sacred.

The principle is:

> **prefer an experiment when its possible outcomes would cause you to choose different architectures.**

This is a much better stop rule than "run another benchmark sweep."

If two hypotheses remain and a single cheap test makes opposite predictions under them, that test is often worth more than evaluating another ten models.

The other critical boundary is the judge.

The system proposing experiments cannot silently modify the thing deciding whether it won.

That is why sealed cohorts, frozen evaluation code, external outcomes, exact execution receipts, and z0evals itself became part of the architecture.

---

## 16. What LLMs make dramatically faster

There is now a growing literature on LLMs as scientific collaborators.

Systems such as the [AI co-scientist](https://arxiv.org/abs/2502.18864) and [Agent Laboratory](https://aclanthology.org/2025.findings-emnlp.320/) explore literature search, hypothesis generation, experiment design, implementation, and report writing.

At the same time, evaluations of iterative scientific discovery show that doing well on scientific QA is not the same as conducting reliable open-ended discovery.

That distinction matches my experience.

LLMs are extraordinary research compressors when I use them to:

- translate a vague phenomenon into the vocabulary of several disciplines;
- discover the search terms I did not know existed;
- walk backward through citation graphs;
- explain mathematical prerequisites at the exact depth needed for the next paper;
- compare two papers under the same assumptions;
- generate *rival* explanations instead of one plausible narrative;
- turn hypotheses into runnable experiments;
- write benchmark/replay/instrumentation code;
- preserve a durable ledger of failed hypotheses;
- search our own past experiments for contradictory evidence;
- repeatedly ask "what would falsify this?"

The thing I do **not** want the LLM to own is the final epistemic loop:

```text
model proposes story
→ model grades story
→ model declares story correct
```

That is just a very fast way to become confident.

The expensive researcher skill remains judgment:

- what question is actually worth resolving?
- what measurement represents the real problem?
- what evidence would change the architecture?
- what assumptions are silently different between papers?
- what is source-reported versus independently reproduced?
- is a gain causal or did another component produce it?
- are we learning the benchmark instead of the phenomenon?

LLMs make research access cheap.

They do not make research judgment cheap.

---

## 17. What "SOTA" looks like from here

The phrase state of the art often collapses into one leaderboard number.

Our research trail suggests a different view.

The frontier is a composition of techniques at different layers:

| problem | frontier pattern | why |
| --- | --- | --- |
| illegal/impossible actions | typed compiler / deterministic constraints | do not ask a model to rediscover impossibility |
| bounded semantic decisions | task-fit discriminative decision model | finite outputs do not require arbitrary generation |
| probability quality | proper scoring + calibration | confidence must be usable by the runtime |
| hard tail | selective prediction / abstention | optimize safe coverage rather than universal prediction |
| heterogeneous models | routing + strong baselines | model complementarity exists; router value is not automatic |
| changing traffic | contextual-bandit / online feedback | deployment reveals only partial counterfactual information |
| system cost | residency-aware conditional execution | forward latency is only part of cost |
| repeated behavior | specialists → routines | stable cognition should eventually stop being a model call |
| learning | outcome-backed episodes | teacher imitation cannot prove system improvement |
| research | sealed credit + discriminating tests | optimize understanding, not experiment volume |

Recent routing work is already moving toward online feedback.

Contextual-bandit formulations such as [bandit-feedback routing](https://arxiv.org/abs/2510.07429) are attractive because deployment rarely reveals the reward of every model — you usually observe only the system you actually selected.

The z0intelligence version makes the action space broader.

The action is not necessarily:

> choose model A or model B.

It can be:

```text
use deterministic rule
retrieve more context
ask tiny specialist
ask calibrated decision model
load local SLM
delegate typed subtask
call frontier model
abstain
```

That is the research direction I currently find most interesting.

Not a universal router.

A **compiler for cognition**.

---

## 18. The next experiments that could kill this theory

A useful synthesis should end with falsifiers.

These are the experiments I currently care about most.

### Dynamic-option tiny policies

Can one tiny option-conditioned policy generalize across runtime-defined skill/tool sets while preserving calibrated risk/coverage?

If not, Jev-like generality may require substantially more semantic machinery than our sparse specialists can provide.

### Residency-aware routing

Does adding model residency, swap cost, queue state, and expected reuse materially beat quality-only routing on end-to-end verified utility?

If not, the separation between cognition selection and placement may be less valuable than we think.

### Typed delegation

If workers return bounded typed outputs or artifact references instead of prose, does parent token consumption actually fall without reducing verified outcomes?

If not, delegation may simply be shifting rather than eliminating cognition.

### Routine compilation

What fraction of a credited specialist's stable region can be replaced by deterministic rules on future traffic?

If the fraction is tiny, "downward compilation" may be more metaphor than useful systems primitive.

### Mushroom body versus boring controls

On real outcome-backed decisions, does sparse local plasticity expand the Pareto frontier over ridge/MLP at the same footprint and safe-coverage target?

If not, use ridge/MLP.

### Active teacher allocation

Does calling Jev/frontier teachers only on disagreement and high-expected-information states beat labeling everything under equal cost?

If not, the active-learning layer may be needless complexity.

### Cross-harness transfer

Does a policy learned from one harness preserve lift in another?

If not, we may be learning harness-specific surface syntax rather than reusable decision structure.

The point is not to protect the theory from these tests.

The point is to design the theory so these tests can kill it.

---

## 19. A reusable way to learn a frontier quickly

If I compress the z0intelligence research process into something another person can reuse, it looks like this.

### 1. Start with a painful real phenomenon

"Why is this slow?" or "why did this fail?" is a better starting point than "teach me model routing."

The real phenomenon supplies relevance and a falsifiable target.

### 2. Decompose it into mathematical jobs

Ask whether each piece is really:

- generation;
- classification;
- ranking;
- retrieval;
- forecasting;
- control;
- scheduling;
- optimization;
- verification.

That tells you which older research communities to search.

### 3. Use the LLM to discover vocabulary, then walk backward

Do not only ask for "the latest papers."

Ask:

- what problem was this called before LLMs?
- what is the canonical formulation?
- what assumptions changed?
- which older result is this rediscovering?
- what papers disagree?
- what baseline keeps surviving?

### 4. Maintain multiple explanations

The goal of a literature review is not to produce one coherent story as fast as possible.

It is to produce a small set of explanations that make different predictions.

### 5. Design the cheapest discriminating experiment

Ask what observation would cause you to choose a different architecture.

Run that before a broad benchmark when possible.

### 6. Freeze the evidence before interpreting it

Record:

- exact revision;
- actual execution path;
- cohort;
- source;
- outcome;
- negative results;
- failed hypotheses.

Otherwise your research memory slowly turns into mythology.

### 7. Synthesize instead of summarize

Thirty paper summaries are not thirty units of understanding.

The useful output is a smaller model of the field that predicts:

> **what experiment should I run next, and what result would make me change my mind?**

Then repeat.

---

## Conclusion

I used to think becoming technically fluent in a new research area was mostly a bandwidth problem.

Read enough textbooks. Read enough papers. Accumulate enough background.

There is still no substitute for depth.

But LLMs change the bottleneck.

They can compress search, translation, prerequisite learning, code, citation traversal, comparison, and experimentation enough that a motivated person can move through a field shockingly quickly.

That does not turn everyone into a PhD researcher overnight.

It moves the scarce skill upward.

The scarce skill becomes:

> **building a falsifiable mental model of the field faster than you fool yourself.**

That is what z0intelligence has become for me as much as it is a software project.

The architecture is a record of changed beliefs:

- the personal SLM became a population of specialists;
- the smart router kept losing to simpler structure;
- the model chooser became a capability selector;
- confidence became a control signal;
- accuracy became safe coverage;
- model latency became systems residency;
- delegation became information compression;
- biological complexity became a hypothesis source;
- learned policies started becoming candidates for deterministic compilation;
- and evaluation stopped being a report at the end and became part of the machinery that decides what we are allowed to believe.

The frontier is not one model.

It is learning how to keep moving work toward the cheapest mechanism that still deserves to do it.

---

## Research map

### Representation and classifiers
- [BERT](https://aclanthology.org/N19-1423/)
- [Architecture / pretraining objective study](https://proceedings.mlr.press/v162/wang22u.html)
- [ModernBERT](https://arxiv.org/abs/2412.13663)

### Calibration and probabilistic decisions
- [Brier score](https://doi.org/10.1175/1520-0493%281950%29078%3C0001%3AVOFEIT%3E2.0.CO%3B2)
- [Strictly proper scoring rules](https://doi.org/10.1198/016214506000001437)
- [On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html)
- [RLCR](https://arxiv.org/abs/2507.16806)

### Abstention / selective prediction
- [Chow reject option](https://doi.org/10.1109/TIT.1970.1054406)
- [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a)

### Conditional computation
- [Sparsely-Gated Mixture-of-Experts](https://arxiv.org/abs/1701.06538)
- [Switch Transformers](https://www.jmlr.org/papers/v23/21-0998.html)
- [DeeBERT](https://aclanthology.org/2020.acl-main.204/)
- [FrugalGPT](https://arxiv.org/abs/2305.05176)

### Routing
- [RouteLLM](https://arxiv.org/abs/2406.18665)
- [RouterArena](https://arxiv.org/abs/2510.00202)
- [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/)
- [Bandit-feedback routing](https://arxiv.org/abs/2510.07429)
- [TokenTrim Jev routing experiment](https://github.com/TokenTrim/jev-routing-experiment)

### Jev
- [TypeSafe: Introducing System One Models and Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [Raschka: From Bag-of-Words to Jev](https://magazine.sebastianraschka.com/p/classifier-history-and-jev)
- [Jev in the Wild](https://arxiv.org/abs/2609.30216)

### Biological specialist research
- [Drosophila mushroom body connectome](https://www.nature.com/articles/nature23455)
- [Larval whole-brain connectome](https://pmc.ncbi.nlm.nih.gov/articles/PMC7614541/)
- [Adult FlyWire connectome](https://www.nature.com/articles/s41586-024-07558-y)

### Research acceleration
- [MacKay: Information-Based Objective Functions for Active Data Selection](https://authors.library.caltech.edu/records/efefp-2j353)
- [AI Co-Scientist](https://arxiv.org/abs/2502.18864)
- [Agent Laboratory](https://aclanthology.org/2025.findings-emnlp.320/)
- [Scientific-discovery evaluation](https://arxiv.org/abs/2512.15567)

## Our evidence trail

- [Phase 1B: how much of the LLM do we actually need?](../web/app/page.tsx)
- [What actually deserves a model?](../web/app/z0intelligence-function-routing/page.tsx)
- [z0intelligence durable research context](https://github.com/kvnloo/z0intelligence/blob/master/docs/RESEARCH.md)

The research papers are not evidence for our particular architecture.

Our experiments are not universal evidence for the field.

The point is the loop between them.
