| arm | engine | decisions | correct (gated) | raw argmax correct | uncertain | wrong | false autonomy | p50 ms | p95 ms | calls/decision | cold load s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| jev:flat | jev-api | 138 | 110 (80%) | 126 (91%) | 22 | 6 | 0 | 152.6 | 268.3 | 1 | 0.0 |
| jev:flat+bt | jev-api | 138 | 122 (88%) | 122 (88%) | 7 | 9 | 0 | 159.8 | 548.6 | 3.09 | 0.0 |
| llamacpp:http://127.0.0.1:46847|qwen3-4b-q4km | llama.cpp | 138 | 93 (67%) | 93 (67%) | 8 | 37 | 0 | 161.4 | 619.8 | 1 | 0.7 |
| ollama:qwen2.5:3b | ollama | 138 | 79 (57%) | 79 (57%) | 13 | 46 | 0 | 85.8 | 170.2 | 1 | 57.4 |
| llamacpp:http://127.0.0.1:18421|qwen3-1.7b-q4km | llama.cpp | 138 | 71 (51%) | 71 (51%) | 0 | 67 | 0 | 114.7 | 152.0 | 1 | 3.5 |
| rule:lexical | deterministic | 46 | 20 (44%) | 20 (44%) | 0 | 26 | 0 | 0.0 | 0.1 | 0 | 0.0 |
| z0int:openjev_06b | z0int-transformers | 138 | 48 (35%) | 48 (35%) | 0 | 90 | 0 | 42.7 | 105.1 | 1.85 | 17.1 |
| z0int:laya_421m | z0int-transformers | 138 | 42 (30%) | 42 (30%) | 0 | 96 | 3 | 1781.3 | 5093.0 | 1.85 | 13.7 |
| z0int:julia_1 | z0int-transformers | 138 | 24 (17%) | 24 (17%) | 0 | 105 | 3 | 264.8 | 779.4 | 1.17 | 19.1 |
| z0int:nanojev | z0int-transformers | 138 | 24 (17%) | 24 (17%) | 0 | 114 | 6 | 186.7 | 324.8 | 1 | 16.2 |
| z0int:decider_2b | z0int-transformers | 138 | 0 (0%) | 0 (0%) | 0 | 0 | 0 | None | None | 0 | 11.6 |

Capability profile (raw-argmax correct / decisions by case kind):

| arm | clear | split | multi | trap |
| --- | --- | --- | --- | --- |
| jev:flat | 72/75 | 15/18 | 12/12 | 27/33 |
| jev:flat+bt | 72/75 | 15/18 | 11/12 | 24/33 |
| llamacpp:http://127.0.0.1:18421|qwen3-1.7b-q4km | 52/75 | 0/18 | 9/12 | 10/33 |
| llamacpp:http://127.0.0.1:46847|qwen3-4b-q4km | 63/75 | 3/18 | 6/12 | 21/33 |
| ollama:qwen2.5:3b | 56/75 | 2/18 | 9/12 | 12/33 |
| rule:lexical | 14/25 | 2/6 | 2/4 | 2/11 |
| z0int:decider_2b | 0/75 | 0/18 | 0/12 | 0/33 |
| z0int:julia_1 | 9/75 | 0/18 | 6/12 | 9/33 |
| z0int:laya_421m | 21/75 | 3/18 | 3/12 | 15/33 |
| z0int:nanojev | 6/75 | 0/18 | 6/12 | 12/33 |
| z0int:openjev_06b | 30/75 | 0/18 | 6/12 | 12/33 |

Offload simulation (incumbent jev:flat; dev/holdout split by screen lineage; {'holdout': 25, 'dev': 21} cases):

| candidate | tau (dev) | dev offload | dev acc | holdout offload | holdout acc | holdout false autonomy | holdout mean ms | incumbent holdout acc / mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| z0int:laya_421m | none credited | - | - | - | - | - | - | 0.8 / 173.2 |
| z0int:nanojev | 0.5 | 0% | 0.794 | 0% | 0.8 | 0 | 359.8 | 0.8 / 173.2 |
| z0int:openjev_06b | none credited | - | - | - | - | - | - | 0.8 / 173.2 |
