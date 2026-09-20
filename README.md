# CommerceLens

## English

<!-- parity: product-positioning -->
### 1. Product positioning

**Evidence-governed commerce analytics for AI agents.** CommerceLens v0.2.0 is
a local, open-source Codex Skill/plugin that turns supported CSV and XLSX data
into validated, traceable claims and refuses conclusions the evidence cannot
support.

> No material claim without traceable evidence.

<!-- parity: why-different -->
### 2. Why CommerceLens is different

CommerceLens keeps analytical states separate:

```text
Executed Result != Validated Result
Validated Result != Admissible Evidence
Admissible Evidence != ClaimDecision
```

The deterministic runtime owns KPI values, validation, Evidence, and
`ClaimDecision`. The agent may interpret a supported question, inspect headers,
propose mappings, request missing facts, and explain authorized output. It may
not turn plausible prose into a material claim. Public output keeps
`MetricState` and `ClaimState` distinct. Unknown authority fails closed.

<!-- parity: governed-coverage -->
### 3. Governed coverage

Mapping confirmation and coverage confirmation are different gates. A source
column mapped to `line_revenue` does not prove that every relevant record was
exported. Request period does not equal coverage authority, and observed minimum
or maximum dates do not equal coverage authority.

When the source owner supplies reviewed export facts, CommerceLens prepares one
proposal covering all pages and records, eligible status treatment, hidden
filters, requested periods, and an explicit UTC cutoff. Confirmation creates
only `USER_DECLARED` authority. Source completeness has not been independently
verified by CommerceLens. Unknown, ambiguous, contradictory, or incomplete
coverage remains blocked.

<!-- parity: coverage-ux -->
### 4. Consolidated coverage UX

Resolved facts are displayed once. Only missing, ambiguous, or contradictory
facts trigger clarification. A complete proposal ends with:

```text
請確認以上資訊是否正確。
```

A plain affirmative such as `確認` is enough; no special phrase is required. The
confirmation is bound to the exact proposal fingerprint. Changing the source,
mapping, scope, periods, cutoff, or proposal makes stale confirmation invalid.

<!-- parity: retained-evidence -->
### 5. Retained evidence

Temporary execution is the default and creates no retained run. Retention is an
explicit opt-in made before execution. Formal retained mode persists the source
snapshot, canonical data, metadata, `AnalysisResult`, public response, manifest,
and completion marker. It reports `retained_complete` only after persistence
integrity passes.

Retained runs support cross-process `list`, `inspect`, and `verify` operations.
Persistence integrity does not make `ClaimDecision` more correct and never
upgrades `USER_DECLARED` to independent verification.

<!-- parity: governed-refusal -->
### 6. Governed refusal

For “Why did revenue drop?”, CommerceLens may support the descriptive absolute
Revenue Change while refusing the unsupported diagnostic conclusion:

```text
Insufficient evidence to conclude why Revenue declined.
```

It does not list speculative causes.

<!-- parity: public-scope -->
### 7. Public scope

| Supported | Unsupported |
|---|---|
| CSV and XLSX | Positive diagnostic or causal explanations |
| Revenue | Forecasting and predictive claims |
| Orders | Recommendations and prescriptive claims |
| AOV | Revenue Change Percentage |
| Absolute Revenue Change | Product/category contribution or ranking |
| Exact canonical mapping or confirmed mapping | Marketplace/vendor connectors |
| Descriptive positive claims | Hosted SaaS or REST API |

Grouping is `NONE`. Revenue means post-discount eligible merchandise value,
excluding tax and shipping, within the governed scope and period; it is not
accounting revenue or cash collected. `AOV` is `Undefined` when Orders is zero,
not numeric zero. CSV/XLSX are the public workflow; SQLite remains a lower-level
kernel capability.

<!-- parity: how-it-works -->
### 8. How it works

```text
Business Question
-> Metric Definition
-> Required Evidence
-> Data Sufficiency
-> Deterministic Execution
-> Deterministic Validation
-> Evidence
-> ClaimDecision
-> Supported Answer / Governed Refusal
```

The Skill creates a bounded structured intent; the runner invokes the same
application service used by tests. Material values never come from LLM mental
math.

<!-- parity: quick-start -->
### 9. Quick Start

Verify Codex and install the plugin:

```bash
codex --version
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin add commerce-lens --marketplace commerce-lens
codex plugin list
```

Start a fresh Codex session after installation, provide a CSV or XLSX file, and
ask a supported question such as “How did revenue change from Q3 2026 to Q4
2026?” See [Public usage](docs/USAGE.md) for the complete workflow.

<!-- parity: schema-mapping -->
### 10. Schema mapping example

```text
Order Number -> order_id
Line Item ID -> order_line_id
Order Date   -> order_date
SKU          -> product_id
Quantity     -> quantity
Sales Amount -> line_revenue
Currency     -> currency
Order Status -> eligibility_status
```

The proposal is not authority. The user confirms or corrects it, then
deterministic `validate_mapping(...)` must pass. Source files are not renamed or
overwritten.

<!-- parity: coverage-example -->
### 11. Coverage confirmation example

```text
Coverage proposal:
- all export pages and all in-scope records included
- paid orders included; cancelled orders excluded
- no additional hidden filters
- data available through 2026-04-01T00:00:00Z
- Authority: USER_DECLARED; not independently verified by CommerceLens
請確認以上資訊是否正確。
```

`確認` is normalized to the canonical confirmed intent and bound to this exact
proposal. Mapping confirmation alone cannot perform this step.

<!-- parity: retention-example -->
### 12. Retained evidence example

After an explicit retention request, the host invokes retained mode. Operators
can then use the governed lifecycle commands:

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --list-retained
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --inspect-run RUN_ID
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --verify-run RUN_ID
```

Without the explicit request, execution stays temporary. Retained local storage
is plaintext and has no TTL, encryption, or secure erase.

<!-- parity: public-examples -->
### 13. Public examples

[Public examples](examples/public_v0_1/README.md) include canonical CSV, XLSX,
and zero-order AOV cases. The `public_v0_1` path is a compatibility identifier,
not the package version. [P14 fixture evidence](tests/fixtures/p14/README.md)
covers realistic synthetic source shapes without claiming vendor compatibility.

<!-- parity: engineering -->
### 14. Engineering credibility

CommerceLens uses typed contracts, deterministic CSV/XLSX intake, mapping and
coverage validation, governed Metric execution, evidence linkage, admissibility
evaluation, retained-bundle integrity checks, and fail-closed regressions. The
release candidate is verified with focused gates, P15 preflight, the complete
test suite, packaging checks, data-safety review, and an isolated fresh-install
gate. Developer commands are in [Development notes](docs/DEVELOPMENT.md).

<!-- parity: validation-status -->
### 15. Project and validation status

- Version: `0.2.0`.
- P00 internal expert protocol rehearsal: **PASS**.
- External participant contribution to P00: **0**.
- P01 external first-user pilot: **NOT RUN**.
- P15: **NOT PASS**; participant thresholds are unchanged.
- Release state: local release candidate only; publication requires explicit authorization.

P00 is internal rehearsal evidence, not external validation, usability proof, or
production-readiness evidence. See the [P00 closeout](validation/p15/P00_INTERNAL_PROTOCOL_REHEARSAL_CLOSEOUT.md).

<!-- parity: safety-limitations -->
### 16. Data safety and limitations

Public examples and fixtures are synthetic. Do not commit secrets, credentials,
private participant information, customer data, confidential employer data,
private URLs, retained runtime bundles, databases, logs, caches, or local
environments. CommerceLens does not claim enterprise security certification,
external user validation, production readiness, usability proof, or product-
market fit. It does not provide a hosted service, REST API, cloud deployment,
secure erase, or independent source-completeness verification.

Governance authority remains in the [Metric Dictionary](docs/frozen/CANONICAL_DATASET_AND_METRIC_DICTIONARY.md),
[Evidence Contract](docs/frozen/EVIDENCE_CONTRACT_SPECIFICATION.md), and
[Architecture Specification](docs/frozen/ARCHITECTURE_SPECIFICATION.md).

<!-- parity: license-release -->
### 17. License and release

CommerceLens is licensed under the [MIT License](LICENSE). Package and plugin
version: `0.2.0`. Release title: **CommerceLens v0.2.0 — Governed Coverage &
Retained Evidence**. Release notes are in [v0.2.0 release notes](release-notes/v0.2.0.md).
No tag, GitHub Release, package publication, or deployment is created by local
release preparation.

---

# 繁體中文

<!-- parity: product-positioning -->
### 1. 產品定位

**為 AI 代理提供證據治理的商務分析。** CommerceLens v0.2.0 是本機、開源的
Codex Skill/plugin，能把支援的 CSV 與 XLSX 資料轉為經驗證且可追溯的主張，
並拒絕現有證據無法支持的結論。

> 沒有可追溯證據，就不提出實質主張。

<!-- parity: why-different -->
### 2. CommerceLens 的差異

CommerceLens 將分析狀態明確分開：

```text
Executed Result != Validated Result
Validated Result != Admissible Evidence
Admissible Evidence != ClaimDecision
```

確定性執行環境負責 KPI 數值、驗證、Evidence 與 `ClaimDecision`。代理可解讀
支援的問題、檢查欄位、提出 mapping、詢問缺漏資訊，並解釋已獲授權的輸出；
但不能把看似合理的敘述變成實質主張。公開輸出會區分 `MetricState` 與
`ClaimState`；未知權限一律 fail closed。

<!-- parity: governed-coverage -->
### 3. 受治理的 coverage

Mapping 確認與 coverage 確認是不同關卡。把來源欄位對應到 `line_revenue`
不代表所有相關紀錄都已匯出。請求期間不等於 coverage authority，資料中觀察到
的最早或最晚日期也不等於 coverage authority。

來源擁有者提供經檢視的匯出事實後，CommerceLens 會準備單一 proposal，涵蓋
所有頁面與紀錄、合格狀態處理、隱藏篩選、請求期間，以及明確的 UTC cutoff。
確認後只會建立 `USER_DECLARED` authority；CommerceLens 並未獨立驗證來源完整
性。未知、模糊、矛盾或不完整的 coverage 仍會被阻擋。

<!-- parity: coverage-ux -->
### 4. 整合式 coverage UX

已確定的事實只顯示一次；只有缺漏、模糊或矛盾的事實才會觸發澄清。完整
proposal 的結尾為：

```text
請確認以上資訊是否正確。
```

一般肯定回覆如 `確認` 即可，不需要特殊詞句。確認會綁定精確的 proposal
fingerprint；來源、mapping、scope、期間、cutoff 或 proposal 有任何變更，舊確認
即失效。

<!-- parity: retained-evidence -->
### 5. 保留證據

預設為 temporary 執行，不建立 retained run。Retention 必須在執行前明確選擇。
正式 retained mode 會保存來源快照、canonical data、metadata、`AnalysisResult`、
公開回應、manifest 與 completion marker；只有 persistence integrity 通過後才回報
`retained_complete`。

Retained run 支援跨程序的 `list`、`inspect` 與 `verify`。Persistence integrity
不會讓 `ClaimDecision` 更正確，也不會把 `USER_DECLARED` 升級成獨立驗證。

<!-- parity: governed-refusal -->
### 6. 受治理的拒絕

面對「營收為何下降？」CommerceLens 可支持描述性的絕對 Revenue Change，
同時拒絕證據不足的診斷結論：

```text
Insufficient evidence to conclude why Revenue declined.
```

系統不會列出推測原因。

<!-- parity: public-scope -->
### 7. 公開範圍

| 支援 | 不支援 |
|---|---|
| CSV 與 XLSX | 正向診斷或因果解釋 |
| Revenue | 預測與 predictive claims |
| Orders | 建議與 prescriptive claims |
| AOV | Revenue Change Percentage |
| 絕對 Revenue Change | 產品／類別 contribution 或 ranking |
| 精確 canonical mapping 或已確認 mapping | Marketplace／vendor connectors |
| 描述性正向主張 | Hosted SaaS 或 REST API |

Grouping 為 `NONE`。Revenue 指治理範圍與期間內，折扣後、符合資格的商品價值，
不含稅與運費；它不是會計營收或實收現金。Orders 為零時，`AOV` 是
`Undefined`，不是數值零。CSV/XLSX 是公開工作流程；SQLite 仍是較底層的 kernel
能力。

<!-- parity: how-it-works -->
### 8. 運作方式

```text
Business Question
-> Metric Definition
-> Required Evidence
-> Data Sufficiency
-> Deterministic Execution
-> Deterministic Validation
-> Evidence
-> ClaimDecision
-> Supported Answer / Governed Refusal
```

Skill 建立有界的 structured intent；runner 呼叫與測試相同的 application service。
實質數值絕不來自 LLM 心算。

<!-- parity: quick-start -->
### 9. 快速開始

確認 Codex 並安裝 plugin：

```bash
codex --version
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin add commerce-lens --marketplace commerce-lens
codex plugin list
```

安裝後請啟動新的 Codex session，提供 CSV 或 XLSX 檔案，並提出支援的問題，
例如「How did revenue change from Q3 2026 to Q4 2026?」。完整流程請見
[公開使用說明](docs/USAGE.md)。

<!-- parity: schema-mapping -->
### 10. Schema mapping 範例

```text
Order Number -> order_id
Line Item ID -> order_line_id
Order Date   -> order_date
SKU          -> product_id
Quantity     -> quantity
Sales Amount -> line_revenue
Currency     -> currency
Order Status -> eligibility_status
```

Proposal 本身不是 authority。使用者必須確認或修正，之後確定性的
`validate_mapping(...)` 必須通過。來源檔不會被重新命名或覆寫。

<!-- parity: coverage-example -->
### 11. Coverage 確認範例

```text
Coverage proposal:
- all export pages and all in-scope records included
- paid orders included; cancelled orders excluded
- no additional hidden filters
- data available through 2026-04-01T00:00:00Z
- Authority: USER_DECLARED; not independently verified by CommerceLens
請確認以上資訊是否正確。
```

`確認` 會正規化為 canonical confirmed intent，並綁定這個精確 proposal。僅有
mapping 確認不能完成此步驟。

<!-- parity: retention-example -->
### 12. Retained evidence 範例

收到明確 retention 要求後，host 才會啟用 retained mode。操作者可使用治理後的
lifecycle 指令：

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --list-retained
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --inspect-run RUN_ID
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --verify-run RUN_ID
```

沒有明確要求時仍採 temporary。保留的本機資料為明文，沒有 TTL、加密或安全
抹除。

<!-- parity: public-examples -->
### 13. 公開範例

[公開範例](examples/public_v0_1/README.md)包含 canonical CSV、XLSX，以及零訂單
AOV 案例。`public_v0_1` 路徑是相容性識別符，不是 package version。
[P14 fixture 證據](tests/fixtures/p14/README.md)涵蓋貼近真實的合成來源形態，但不
宣稱 vendor compatibility。

<!-- parity: engineering -->
### 14. 工程可信度

CommerceLens 採用 typed contracts、確定性 CSV/XLSX intake、mapping 與 coverage
驗證、受治理的 Metric 執行、evidence linkage、admissibility evaluation、retained
bundle integrity checks，以及 fail-closed regressions。Release candidate 會通過
focused gates、P15 preflight、完整 test suite、packaging checks、data-safety review
與 isolated fresh-install gate。開發指令請見[開發說明](docs/DEVELOPMENT.md)。

<!-- parity: validation-status -->
### 15. 專案與驗證狀態

- 版本：`0.2.0`。
- P00 內部專家 protocol rehearsal：**PASS**。
- P00 外部參與者貢獻：**0**。
- P01 外部 first-user pilot：**NOT RUN**。
- P15：**NOT PASS**；參與者門檻未變更。
- Release state：僅為本機 release candidate；發布仍需明確授權。

P00 是內部 rehearsal 證據，不是外部驗證、可用性證明或 production-readiness
證據。請見 [P00 closeout](validation/p15/P00_INTERNAL_PROTOCOL_REHEARSAL_CLOSEOUT.md)。

<!-- parity: safety-limitations -->
### 16. 資料安全與限制

公開範例與 fixtures 都是合成資料。請勿提交 secrets、credentials、私人參與者
資訊、客戶資料、雇主機密資料、私人網址、retained runtime bundles、databases、
logs、caches 或本機 environments。CommerceLens 不宣稱 enterprise security
certification、外部使用者驗證、production readiness、usability proof 或 product-
market fit；也不提供 hosted service、REST API、cloud deployment、安全抹除或
來源完整性的獨立驗證。

治理權威仍在 [Metric Dictionary](docs/frozen/CANONICAL_DATASET_AND_METRIC_DICTIONARY.md)、
[Evidence Contract](docs/frozen/EVIDENCE_CONTRACT_SPECIFICATION.md)與
[Architecture Specification](docs/frozen/ARCHITECTURE_SPECIFICATION.md)。

<!-- parity: license-release -->
### 17. 授權與 release

CommerceLens 採用 [MIT License](LICENSE)。Package 與 plugin 版本：`0.2.0`。
Release title：**CommerceLens v0.2.0 — Governed Coverage & Retained Evidence**。
Release notes 位於 [v0.2.0 release notes](release-notes/v0.2.0.md)。本機 release
準備不會建立 tag、GitHub Release、package publication 或 deployment。
