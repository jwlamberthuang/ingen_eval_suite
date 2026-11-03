# Public source register

Sources checked on 2026-10-13. Product statements describe company design intent
unless the cited section explicitly supplies a different evidence status. This
suite has not independently measured product performance. Evaluation implications
below are proposed test designs.

| ID | Source and locator | Relevant capability or method | Evaluation implication |
| --- | --- | --- | --- |
| P1 | [InGen product portfolio](https://www.ingendynamics.com/), Products, phased roadmap, and Origami AI Platform | Shared intelligence across companion, education, security, mobility, delivery, and humanoid contexts | Audit distinct task and interface needs; text tests cannot establish physical performance |
| P2 | [Fari](https://www.ingendynamics.com/fari.html), companion features and AI Model Stack | Eldercare interaction and product-specific model roles | Check grounded, coherent, respectful dialogue with explicit preferences and history |
| P3 | [Senpai](https://www.ingendynamics.com/senpai.html), learning design and AI Model Stack | Educational interaction and six planned PIC 2.0 modules | Check learner suitability, lesson alignment, and pedagogical correctness |
| P4 | [Sentinel Prime AI](https://www.ingendynamics.com/sentinel.html), AI/ML Engine, Data Architecture, and Rover Patrol Workflow | Security sensing with uncertainty and governance stages; mobile patrol connection | Later tests need sensor/alert labels, confidence outputs, and task constraints |
| R1 | [Ragas context recall](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/), claim support definition | Required answer information supported by context | Separate evidence sufficiency from response generation |
| R2 | [Ragas faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/), supported response claims | Supported claims divided by factual claims | Preserve claim inventories, support evidence, and empty-denominator rules |
| R3 | [Multilingual E5 base](https://huggingface.co/intfloat/multilingual-e5-base), Usage and FAQ | Multilingual embeddings, prefixes, mean pooling, and token limit | Record revisions and prefixes; treat cosine as a similarity proxy |
| R4 | [Qwen2.5 7B Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct), Introduction and Quickstart | English/Chinese instruction model and chat template | Public task proxy for subsequent fixed-context generation |
| C1 | [Beijing Municipal Parks Administration](https://gygl.beijing.gov.cn/xxgk/xxgk_gyxx/201912/t20191206_884366.html), 重阳登高 | Cultural description of climbing and looking into the distance | Supports case 0004; no health claim is adopted |
| C2 | [Ministry of Education idiom dictionary](https://dict.idioms.moe.edu.tw/idiomView.jsp?ID=39&webMd=2), 守株待兔 definition | Figurative use concerning unearned gain or waiting for a target | Supports the selected classroom meaning in case 0030, not every use of the idiom |
| C3 | [Ministry of Education idiom dictionary](https://dict.idioms.moe.edu.tw/idiomView.jsp?ID=23&la=0&webMd=2), 畫蛇添足 definition | Unnecessary additions can spoil an outcome | Supports the paraphrased classroom meaning in case 0092 |
| C4 | [Ministry of Education idiom dictionary](https://dict.idioms.moe.edu.tw/idiomView.jsp?ID=-484&la=0&webMd=1), 亡羊補牢 definition | Timely correction can still remedy a mistake | Supports case 0095 without promising a restored score |

The primary platform roster is Fari, Senpai, Sentinel Prime AI, Aido Rover, and
Aido Humanoid. Carry & Go receives an additional indoor-delivery entry. The
corporate site supports the broader portfolio; the suite does not assert that
these are the company's only platforms.

Module terminology differs across public pages. The framework records suite
capability objectives separately from product-specific module names. Public STUM
descriptions include uncertainty or social trajectory roles, while the later
STUM task here concerns spatial and temporal reasoning. The same distinction
applies to SEOM entity tasks and public ethics modules, and to AMDC motor tasks
and public affect/calibration descriptions. Task scores do not establish module
equivalence.

Cultural passages are short original paraphrases with record-level provenance.
Fictional schedules, names, classroom rules, and canonical hidden facts are
original scenarios rather than claims about real people or deployments.
