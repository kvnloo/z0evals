| goal | arm | verified/runs | wall ms p50 | range | model calls (median) | phone actions (median) | errors |
| --- | --- | --- | --- | --- | --- | --- | --- |
| android-version | compiled_macro | 3/3 | 3809.0 | 2600-3890 | 0 | 2 | 0 |
| android-version | deterministic_adb | 3/3 | 140.0 | 127-156 | 0 | 0 | 0 |
| android-version | phone_goal:flat | 3/3 | 12906.0 | 11338-15998 | 6 | 6 | 0 |
| android-version | phone_goal:flat+bt | 3/3 | 14299.0 | 11612-15003 | 6 | 6 | 0 |
| battery-level | compiled_macro | 3/3 | 2101.0 | 1504-2179 | 0 | 1 | 0 |
| battery-level | deterministic_adb | 3/3 | 144.0 | 115-302 | 0 | 0 | 0 |
| battery-level | phone_goal:flat | 2/3 | 9800.0 | 7231-9899 | 3 | 3 | 0 |
| battery-level | phone_goal:flat+bt | 3/3 | 8718.0 | 8008-9331 | 3 | 3 | 0 |
| model-name | compiled_macro | 3/3 | 2260.0 | 1655-2289 | 0 | 1 | 0 |
| model-name | deterministic_adb | 3/3 | 152.0 | 116-248 | 0 | 0 | 0 |
| model-name | phone_goal:flat | 3/3 | 12726.0 | 10642-13099 | 5 | 5 | 0 |
| model-name | phone_goal:flat+bt | 2/3 | 12628.0 | 11943-13313 | 5.0 | 5.0 | 1 |

| arm (all goals) | verified/runs | wall ms p50 | p95 |
| --- | --- | --- | --- |
| compiled_macro | 9/9 | 2260 | 3890 |
| deterministic_adb | 9/9 | 144 | 302 |
| phone_goal:flat | 8/9 | 11338 | 15998 |
| phone_goal:flat+bt | 8/9 | 11777 | 15003 |
