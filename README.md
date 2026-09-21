# CommerceLens

[English](#english) | [繁體中文](#traditional-chinese)

<a id="english"></a>

## English

Ask questions about your commerce CSV or Excel data—without letting the AI
guess when the data is incomplete.

CommerceLens is an open-source Codex plugin for Revenue, Orders, AOV, and
absolute Revenue Change. Before returning a business conclusion, it checks
whether the available data actually supports that conclusion. To try it,
[install the plugin](#quick-start), provide a CSV or XLSX file, and ask a
supported question.

<!-- fact: inputs=csv,xlsx -->
<!-- fact: metrics=revenue,orders,aov,absolute-revenue-change -->

> CommerceLens calculates what the data supports and refuses to guess what it
> does not.

### A 30-second synthetic example

**Synthetic example — not real merchant or customer data.**

You ask:

> How did revenue change from 2025 Q1 to 2026 Q1, and why did it decline?

After source completeness is confirmed, CommerceLens can report:

| Supported by the data | Not supported by the data |
|---|---|
| Revenue: `12,000 USD` → `10,800 USD` | The reason revenue declined |
| Absolute Revenue Change: `-1,200 USD` | Any guessed cause or recommendation |

The calculation is supported. The reason is not, so CommerceLens does not
invent one.

![CommerceLens product flow: provide a CSV or Excel file, ask a business question, confirm columns and source completeness, calculate and validate, then receive a supported answer or a request for clarification.](docs/assets/readme/commerce-lens-flow-en.svg)

### Why this is different from asking an AI to analyze a file

A number can be calculated correctly and still be unsupported if the source
file is incomplete. CommerceLens separates calculation from the decision to
present a business conclusion:

- the Codex plugin interprets the question, inspects columns, and asks for
  missing information;
- the deterministic runtime calculates and validates supported metrics;
- the evidence checks decide whether the conclusion can be stated;
- unsupported gaps stay blocked instead of being filled with plausible prose.

### What CommerceLens can and cannot do

<!-- fact: unsupported=diagnostic,causal,predictive,prescriptive,revenue-change-percentage,product-category-contribution-ranking -->

| Available now | Not available now |
|---|---|
| Calculate Revenue | Explain why Revenue changed |
| Count Orders | Make causal claims |
| Calculate AOV | Forecast future Revenue |
| Compare absolute Revenue Change between two periods | Recommend business actions |
| Read CSV and XLSX files | Calculate Revenue Change Percentage |
| Analyze non-standard column names after confirmed mapping | Rank product/category contribution |

Metric meanings are intentionally narrow:

- **Revenue** is post-discount eligible merchandise value, excluding tax and
  shipping, within the confirmed scope and period. It is not accounting revenue
  or cash collected.
- **Orders** counts distinct eligible orders.
- **AOV** is Revenue divided by Orders for the same governed population. When
  Orders is zero, AOV is `Undefined`, not numeric zero.
- **Absolute Revenue Change** is comparison-period Revenue minus baseline-period
  Revenue. Percentage change is not supported.

### Quick Start

Verify Codex and install the plugin:

```bash
codex --version
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin add commerce-lens --marketplace commerce-lens
codex plugin list
```

Start a fresh Codex session after installation, provide a CSV or XLSX file, and
ask a supported question such as:

> How did revenue change from Q3 2026 to Q4 2026?

See [Public usage](docs/USAGE.md) for the complete workflow and supported input
formats.

### What the user workflow looks like

1. Provide a CSV or XLSX file and ask a supported business question.
2. Confirm or correct any proposed source-column mapping. CommerceLens does not
   rename or overwrite the source file.
3. Confirm whether the export includes all relevant pages, records, statuses,
   periods, and filters.
4. CommerceLens calculates and validates the supported metric.
5. It returns a supported answer or explains what evidence is still missing.

### How source completeness is confirmed

A file containing the requested dates does not prove that the export is
complete. CommerceLens separately checks whether all relevant pages and records
were included, how order statuses were handled, whether hidden filters existed,
and how current the export is.

Known facts are shown once. Only missing, ambiguous, or contradictory facts
trigger clarification. A complete English confirmation ends with:

```text
Please confirm that the information above is correct.
```

A simple reply such as `Confirm` is enough. Confirmation is bound to the exact
source, mapping, scope, periods, and completeness statement shown at that time;
changing them invalidates the old confirmation.

When completeness is confirmed by the user, the system records the formal
identifier `USER_DECLARED`. This is user-provided authority, not independent
verification by CommerceLens. Mapping confirmation and source-completeness
confirmation are separate steps.

### What happens when evidence is insufficient

Unknown, ambiguous, contradictory, or incomplete source coverage blocks
material conclusions. CommerceLens may calculate that Revenue decreased by
`1,200 USD`, but if the file contains no evidence explaining why, it refuses the
reason request and does not list speculative causes.

### Optional retained evidence

<!-- fact: retention=temporary-default,opt-in,list-inspect-verify,plaintext,no-ttl,no-encryption,no-secure-erase -->

If you need an audit trail, CommerceLens can explicitly save the source
snapshot, analysis result, and verification metadata for later inspection.
Retention is opt-in; the default temporary mode creates no retained run.

After an explicit retention request, operators can list, inspect, and verify a
retained run:

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --list-retained
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --inspect-run RUN_ID
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --verify-run RUN_ID
```

A successfully saved bundle is reported as `retained_complete` only after its
stored data passes integrity checks. Retention does not make the analytical
conclusion more correct and does not upgrade `USER_DECLARED` to independent
verification. Retained local data is plaintext and has no TTL, encryption, or
secure erase.

### How reliability is enforced

CommerceLens keeps calculation, validation, evidence, and claim authorization
separate. The deterministic runtime—not language-model mental math—owns metric
values and validation. Stale confirmations, unsupported mappings, incomplete
coverage, inconsistent currency, or failed retention finalization do not become
supported conclusions or successful retained runs.

The formal contracts, states, proposal binding, persistence manifest, and
completion-marker design are documented in [Development notes](docs/DEVELOPMENT.md).

### Current release and validation status

<!-- fact: release=v0.2.0,public,tag-v0.2.0 -->
<!-- fact: validation=p00-pass-internal,p01-not-run,p15-not-pass -->

- Current version: `v0.2.0`.
- Release: **[PUBLICLY RELEASED](https://github.com/daniel-j-lin/commerce-lens/releases/tag/v0.2.0)** on GitHub.
- Git tag: `v0.2.0`.
- P00: **PASS** — internal expert protocol rehearsal with 0 external participants.
- P01 external first-user pilot: **NOT RUN**.
- P15: **NOT PASS**.

P00 is internal rehearsal evidence only. It is not external validation,
usability proof, or production-readiness evidence. See the
[P00 closeout](validation/p15/P00_INTERNAL_PROTOCOL_REHEARSAL_CLOSEOUT.md).

### Current limitations and data safety

- The public workflow supports ungrouped CSV/XLSX analysis only. It does not
  directly connect to Shopify, Amazon, or other marketplace/vendor systems.
- CommerceLens is not a hosted SaaS, REST API, or cloud deployment.
- Source completeness is not independently verified by CommerceLens.
- Public examples and fixtures are synthetic.
- Do not commit secrets, credentials, participant information, customer data,
  confidential employer data, private URLs, retained runtime bundles,
  databases, logs, caches, or local environments.
- CommerceLens does not claim external user validation, production readiness,
  proven usability, enterprise security certification, or product-market fit.

### Documentation, license, and release

- [Public usage](docs/USAGE.md)
- [Development notes](docs/DEVELOPMENT.md)
- [Public examples](examples/public_v0_1/README.md)
- [Metric Dictionary](docs/frozen/CANONICAL_DATASET_AND_METRIC_DICTIONARY.md)
- [Evidence Contract](docs/frozen/EVIDENCE_CONTRACT_SPECIFICATION.md)
- [Architecture Specification](docs/frozen/ARCHITECTURE_SPECIFICATION.md)
- [v0.2.0 release notes](release-notes/v0.2.0.md)
- [MIT License](LICENSE)

The frozen specifications remain the project authority. This README explains
the current public surface in user-facing language; it does not replace those
specifications.

---

<a id="traditional-chinese"></a>

## 繁體中文

用自然語言分析電商 CSV 或 Excel 資料；資料不完整時，CommerceLens 不會自行猜測。

CommerceLens 是開源的 Codex 外掛程式，目前可以計算營收、訂單數、平均客單價，
以及兩個期間之間的絕對營收變化。在提出商務結論前，它會先檢查現有資料是否真的
足以支持該結論。若要開始使用，請先[安裝外掛程式](#快速開始)，再提供 CSV 或
XLSX 檔案並提出支援的問題。

<!-- fact: inputs=csv,xlsx -->
<!-- fact: metrics=revenue,orders,aov,absolute-revenue-change -->

> CommerceLens 只計算資料真正支持的結果；資料沒有證明的部分，不會自行猜測。

### 30 秒合成資料範例

**這是合成資料範例，不是真實商家或客戶案例。**

你問：

> 2025 年第一季到 2026 年第一季，營收變化多少？為什麼下降？

確認來源資料完整後，CommerceLens 可以回答：

| 資料可以支持 | 資料無法支持 |
|---|---|
| 營收：`12,000 USD` → `10,800 USD` | 營收下降的原因 |
| 絕對營收變化：`-1,200 USD` | 猜測的原因或經營建議 |

計算結果有資料支持，但下降原因沒有，因此 CommerceLens 不會自行編造理由。

![CommerceLens 產品流程：提供 CSV 或 Excel 檔案、提出商務問題、確認欄位與資料是否完整、執行並驗證計算，最後回答有證據支持的結果，或在證據不足時要求補充資料。](docs/assets/readme/commerce-lens-flow-zh-TW.svg)

### 與一般 AI 分析檔案有什麼不同

數字可能算對了，卻仍然無法支持商務結論，例如來源檔案漏了部分訂單。
CommerceLens 會把計算與「這個結論能不能說」分開處理：

- Codex 外掛程式負責理解問題、檢查欄位，並詢問缺少的資訊；
- 確定性的程式負責計算與驗證目前支援的指標；
- 證據檢查會判斷資料是否足以支持結論；
- 資料不足時會停止回答，不會用看似合理的文字填補空缺。

### 現在可以做與不會做的事

<!-- fact: unsupported=diagnostic,causal,predictive,prescriptive,revenue-change-percentage,product-category-contribution-ranking -->

| 現在可以做 | 現在不會做 |
|---|---|
| 計算營收 | 解釋營收變動原因 |
| 計算訂單數 | 推論因果關係 |
| 計算平均客單價 | 預測未來營收 |
| 比較兩個期間的絕對營收變化 | 提供經營建議 |
| 讀取 CSV 與 XLSX 檔案 | 計算營收變化百分比 |
| 確認非標準欄名後進行分析 | 計算商品或類別的貢獻與排名 |

各項指標採用明確而有限的定義：

- **營收（Revenue）**是已確認範圍與期間內，折扣後、符合條件的商品價值，
  不含稅金與運費；它不是會計營收或實際收款金額。
- **訂單數（Orders）**計算不重複且符合條件的訂單。
- **平均客單價（AOV）**是同一資料範圍內的營收除以訂單數。訂單數為零時，
  結果是「無法定義」（系統狀態：`Undefined`），不是數字零。
- **絕對營收變化（Revenue Change）**是比較期間營收減去基準期間營收；目前
  不支援百分比變化。

### 快速開始

先確認 Codex 可用，再安裝外掛程式：

```bash
codex --version
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin add commerce-lens --marketplace commerce-lens
codex plugin list
```

安裝後請開啟新的 Codex 工作階段，提供 CSV 或 XLSX 檔案，並提出支援的問題，
例如：

> 2026 年第三季到第四季，營收變化多少？

完整操作流程與支援的輸入格式請見[公開使用說明](docs/USAGE.md)。

### 實際使用流程

1. 提供 CSV 或 XLSX 檔案，並提出支援的商務問題。
2. 確認或修正系統提出的來源欄位對應。CommerceLens 不會重新命名或覆寫來源檔。
3. 確認匯出內容是否包含所有相關頁面、紀錄、訂單狀態、期間與篩選條件。
4. CommerceLens 執行並驗證目前支援的計算。
5. 系統回答有足夠證據支持的結果，或說明還缺少哪些資料。

簡化後的流程是：

```text
提出商務問題
→ 確認要計算的指標與期間
→ 確認來源欄位
→ 確認匯出資料是否完整
→ 執行並驗證計算
→ 檢查證據是否足以支持結論
→ 回答，或因證據不足而停止下結論
```

### 如何確認來源資料是否完整

檔案裡看得到要求的日期，不代表匯出資料一定完整。CommerceLens 會另外確認是否
包含所有相關頁面與紀錄、如何處理訂單狀態、是否有隱藏篩選條件，以及資料更新到
什麼時間。

已知資訊只顯示一次；只有缺漏、模糊或互相矛盾的內容才會要求補充。完整的中文
確認內容會以這句話結尾：

```text
請確認以上資訊是否正確。
```

直接回覆 `確認` 即可。這次確認只適用於當下顯示的來源、欄位對應、分析範圍、
期間與資料完整性聲明；其中任何一項改變後，都必須重新確認。

如果資料完整性是由使用者確認，系統會記錄為「由使用者提供判定依據」
（系統識別為 `USER_DECLARED`）。這不代表 CommerceLens 已獨立驗證來源。
欄位對應確認與資料完整性確認是兩個不同步驟。

### 證據不足時會發生什麼

來源資料的涵蓋範圍未知、模糊、互相矛盾或不完整時，CommerceLens 會阻止缺乏
支持的實質結論。它可能算出營收減少 `1,200 USD`；但如果檔案沒有說明原因的
證據，就會拒絕回答原因，也不會列出猜測。

### 選擇性保留完整分析證據

<!-- fact: retention=temporary-default,opt-in,list-inspect-verify,plaintext,no-ttl,no-encryption,no-secure-erase -->

如果需要留下可供日後查核的分析紀錄，CommerceLens 可以在你明確要求後，保存
來源快照、分析結果與驗證資訊。保存功能必須主動選擇；預設的臨時分析模式不會
建立保留紀錄。

明確要求保存後，可以用以下指令列出、查看與驗證紀錄：

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --list-retained
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --inspect-run RUN_ID
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --verify-run RUN_ID
```

只有保存的資料通過完整性檢查後，系統才會回報「證據已完整保存」
（系統狀態：`retained_complete`）。保存成功不會讓分析結論變得更正確，也不會把
`USER_DECLARED` 提升為獨立驗證。保留在本機的資料是明文，沒有自動保存期限
（TTL）、加密或安全抹除功能。

### 如何維持分析可靠性

CommerceLens 將計算、驗證、證據與結論是否可以提出分開處理。指標數值與驗證
由確定性的程式負責，不是由語言模型心算。過期的確認、不支援的欄位對應、
不完整的資料範圍、幣別不一致，或保存流程失敗，都不會被當成有證據支持的結論
或成功保存的紀錄。

正式的資料結構、系統狀態、確認綁定方式、保存清單及完成標記設計，請見
[開發說明](docs/DEVELOPMENT.md)。

### 目前版本與驗證狀態

<!-- fact: release=v0.2.0,public,tag-v0.2.0 -->
<!-- fact: validation=p00-pass-internal,p01-not-run,p15-not-pass -->

- 目前版本：`v0.2.0`。
- 發布狀態：已在 GitHub **[公開發布](https://github.com/daniel-j-lin/commerce-lens/releases/tag/v0.2.0)**。
- Git 標籤：`v0.2.0`。
- P00：**PASS**——內部專家流程演練，外部參與者為 0。
- P01 外部首次使用者試行：**NOT RUN**（尚未執行）。
- P15：**NOT PASS**（尚未通過）。

P00 只代表內部流程演練，不是外部驗證、可用性證明或已適合正式環境的證據。
詳情請見 [P00 結案紀錄](validation/p15/P00_INTERNAL_PROTOCOL_REHEARSAL_CLOSEOUT.md)。

### 目前限制與資料安全

- 公開流程只支援不分組的 CSV／XLSX 分析，不會直接連接 Shopify、Amazon 或其他
  外部電商平台。
- CommerceLens 不是託管式線上服務、REST API 或雲端部署服務。
- CommerceLens 不會獨立驗證來源資料是否完整。
- 公開範例與測試資料都是合成資料。
- 請勿提交密碼、憑證、參與者個人資訊、客戶資料、雇主機密資料、私人網址、
  保留的執行資料、資料庫、紀錄檔、快取或本機環境。
- CommerceLens 不宣稱已完成外部使用者驗證、已適合正式環境、已證明可用性、
  具備企業安全認證或已達成產品市場契合度。

### 詳細文件、授權與版本發布

- [公開使用說明](docs/USAGE.md)
- [開發說明](docs/DEVELOPMENT.md)
- [公開範例](examples/public_v0_1/README.md)
- [指標定義文件](docs/frozen/CANONICAL_DATASET_AND_METRIC_DICTIONARY.md)
- [證據契約](docs/frozen/EVIDENCE_CONTRACT_SPECIFICATION.md)
- [架構規格](docs/frozen/ARCHITECTURE_SPECIFICATION.md)
- [v0.2.0 版本說明](release-notes/v0.2.0.md)
- [MIT 授權條款](LICENSE)

凍結規格仍是專案的正式依據。本 README 以使用者容易理解的方式說明目前公開
功能，不會取代正式規格。
