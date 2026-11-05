---
title: "a bigger upload scores higher in a simulator"
subtitle: "fframestudio's delivery recipes, five playback simulators, four short clips, and one gradient where we lose."
study: fframes-delivery-v0
status: source-reported
author: "zer0 research"
date: "november 2, 2026"
published: 2026-11-02
area: research
kind: study
dek: "fframestudio export recipes against naive x264 after five simulated platform re-encodes."
mock_data: false
toc:
  - id: result
    label: the result
  - id: cost
    label: what it cost
  - id: limits
    label: what this does not show
---

<div class="lede">
fframes renders a film. this post is about the step after that: the export recipe, and what a viewer sees once a platform re-encodes the upload. the interactive version with every scored frame lives on its own page.
</div>

<div class="hero-rule"></div>

## the result {#result}

fframestudio built a playback simulator for each of youtube, shorts, tiktok, reels, and x, then encoded four three-second clips two ways. naive is x264 medium at CRF23. ours is NVENC H.264 at CQ14, with mild CAS sharpening for x. both go through the same simulator and libvmaf scores all 90 frames of each clip.

ours has higher pooled mean and p5 VMAF in all five simulators. the largest move is x, where p5 goes from 88.52 to 92.48. the other four move less than one point on the mean. these are source-reported scores from `kvnloo/fframestudio` at `1a68268`. we re-derived every pooled mean and p5 from the 3,600 per-frame rows and they match.

## what it cost {#cost}

our uploads are 3.23x to 3.92x the size of naive uploads. this is not an equal-bitrate comparison. on a synthetic 10-bit blue ramp, the selected H.264 recipe loses mean and p5 VMAF to naive in both simulators that ran it.

## what this does not show {#limits}

nothing was uploaded to a real platform. the recipes were tuned and scored on the same four clips, with no held-out set. four clips is too few for a significance claim, and VMAF is not calibrated for small UI text on a phone. the frozen study is `studies/fframes-delivery-v0`.
