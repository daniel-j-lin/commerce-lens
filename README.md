# CommerceLens

[English](#english) | [繁體中文](#traditional-chinese) | [简体中文](#simplified-chinese)

<a id="english"></a>

## English

CommerceLens is an open-source Codex plugin and evidence-governed analytics repository for commerce CSV/XLSX data. It separates what happened, how an observed Revenue change was composed, and whether one approved diagnostic hypothesis meets a predefined evidence-backed criterion.

The installed public plugin currently supports descriptive analysis. The repository/MVP additionally implements mechanical product-level Revenue decomposition and one governed diagnostic family; those two capabilities are not yet wired into the installed public plugin interaction surface.

<!-- fact: inputs=csv,xlsx -->
<!-- fact: metrics=revenue,orders,aov,absolute-revenue-change -->
<!-- fact: analytical-layers=descriptive,mechanical-decomposition,governed-diagnostic-testing -->
<!-- fact: diagnostic-scope=repository-mvp-only,product_composition_association,weekly_product_presence_revenue_association@1.0.0 -->

> CommerceLens states only conclusions supported by governed evidence and refuses unsupported explanations.

### Three analytical levels

1. **Descriptive — What happened?** Calculate Revenue, Orders, AOV, and absolute Revenue Change within a governed scope and period.
2. **Mechanical decomposition — How was the observed Revenue change composed?** Decompose product-level Revenue contributions where applicable, without treating contribution as causation.
3. **Governed diagnostic testing — Does one approved hypothesis meet a predefined evidence-backed criterion?** The MVP supports exactly `product_composition_association` through `weekly_product_presence_revenue_association@1.0.0` in the repository R7 service. This is not currently available through the installed public plugin workflow.

### Synthetic examples

#### Example 1 — insufficient evidence

**Synthetic example — not real merchant or customer data.**

> **Question:** Why did Revenue decline from Q3 to Q4?
>
> **Illustrative output:** Revenue declined by 18%. The available evidence is sufficient to calculate the Revenue change, but insufficient to test a governed diagnostic explanation. Insufficient evidence to conclude why Revenue declined.

No possible cause is invented. This is the behavior of the current installed public plugin for a diagnostic question.

#### Example 2 — sufficient evidence in the repository/MVP diagnostic service

**Synthetic example — not real merchant or customer data.**

These values come from the independently recomputed canonical R7 conformance fixture `FX-R7-PROD-001A`, not from a production benchmark:

| Item | Synthetic value |
|---|---:|
| Revenue decline | 18% |
| Valid weekly observations | 8 |
| Baseline weeks | 4 |
| Comparison weeks | 4 |
| Validated Spearman rho | -1.0 |
| Support criterion | rho <= -0.50 |
| Analytical outcome | `CRITERION_MET` |

Product composition was tested as one governed diagnostic hypothesis. Across the governed weekly observations, greater product-presence composition distance was associated with lower weekly Revenue performance. The independently validated Spearman rho was -1.0, which met the predefined support criterion of rho <= -0.50. The evidence therefore supports product composition as one plausible contributor to retain in the diagnostic explanation.

This does not establish causality and does not show that product composition was the sole or primary cause. Seasonality, discounting, inventory, overall demand, promotions, customer mix, time trend, and external market conditions remain alternative explanations.

`CRITERION_MET` is not causality, a sole-cause determination, a `ClaimDecision`, or a `Finding`.

![CommerceLens workflow from business question through evidence admission, with refusal on insufficient evidence and a validated bounded diagnostic explanation on sufficient evidence.](docs/assets/readme/commerce-lens-flow-en.svg)

### Core workflow

```text
Business Question
↓
Metric / Scope / Period Definition
↓
Source Mapping
↓
Source Completeness Check
↓
Deterministic Metric Calculation
↓
Mechanical Decomposition where applicable
↓
Governed Hypothesis Generation
↓
Required Evidence / Admission Check
↓
Evidence sufficient?
├─ NO  → refuse unsupported explanation → explain missing evidence
└─ YES → approved diagnostic test → deterministic execution
        → independent validation → bounded analytical outcome
        → bounded why-explanation → limitations + alternative explanations
```

**Association != causation.**

### Capabilities and boundaries

| Capability | Status |
|---|---|
| Calculate Revenue, count Orders, calculate AOV, compare absolute Revenue Change | Installed public plugin |
| Read CSV/XLSX; use confirmed non-standard mapping | Installed public plugin |
| Mechanical product-level Revenue decomposition where applicable | Repository/MVP only; not wired into the installed public plugin |
| Generate governed diagnostic hypotheses | Repository/MVP only; not wired into the installed public plugin |
| Test `product_composition_association` with `weekly_product_presence_revenue_association@1.0.0` when evidence is sufficient | Repository/MVP only; not wired into the installed public plugin |
| Return a bounded supported why-explanation for that one diagnostic lane | Repository/MVP only; not wired into the installed public plugin |
| Causal explanation; primary/sole-cause determination; arbitrary root-cause analysis | Not established |
| Discount, inventory, or external-market diagnostic execution | Not available |
| Forecasting; prescriptive recommendations; statistical-significance claims | Not available / not established |
| Revenue Change Percentage; generic product/category ranking | Not supported by the installed public plugin |

<!-- fact: public-plugin=revenue,orders,aov,absolute-revenue-change,csv,xlsx,confirmed-mapping -->
<!-- fact: repository-mvp=mechanical-product-revenue-decomposition,governed-hypothesis-generation,one-product-composition-diagnostic,bounded-why-explanation -->
<!-- fact: unavailable=causal,primary-or-sole-cause,general-root-cause,discount-diagnostic,inventory-diagnostic,external-market-diagnostic,forecasting,prescriptive,statistical-significance -->

Revenue is eligible post-discount merchandise value excluding tax and shipping. Orders counts distinct eligible orders. AOV is Revenue divided by Orders for the same population and is `Undefined` when Orders is zero. Absolute Revenue Change is comparison Revenue minus baseline Revenue.

### Quick start for the installed public plugin

```bash
codex --version
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin add commerce-lens --marketplace commerce-lens
codex plugin list
```

Start a fresh Codex session, provide a CSV or XLSX file, and ask a supported descriptive question such as: “How did Revenue change from Q3 2026 to Q4 2026?” The public workflow asks for mapping or completeness clarification when needed, then calculates and validates the supported metric. A normal installed user cannot yet execute R7 or receive its positive bounded why-explanation through the public runner. See [Public usage](docs/USAGE.md).

### Evidence, reliability, and retention

Source completeness is separate from column mapping. A date range does not prove every relevant page, record, status, or filter is present. Confirmed user-provided completeness is `USER_DECLARED`, not independent verification.

Execution and validation are separate. For R7, validation independently recomputes the diagnostic result, evidence admission is authenticated, and complete R6→R7 lineage is verified before authoritative completion. Language-model reasoning never substitutes for deterministic execution evidence or a `ClaimDecision`.

Retention is opt-in; temporary execution is the default. Operators may list, inspect, and verify an explicitly retained run:

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --list-retained
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --inspect-run RUN_ID
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --verify-run RUN_ID
```

A retained bundle reports `retained_complete` only after integrity checks and the completion marker succeed. Local retained data is plaintext with no TTL, encryption, or secure erase. See [Development notes](docs/DEVELOPMENT.md).

<!-- fact: retention=temporary-default,opt-in,list-inspect-verify,plaintext,no-ttl,no-encryption,no-secure-erase -->

### Diagnostic limitations

- Only one governed diagnostic family/method is implemented for the MVP.
- The result is an observed association, not causal proof, a primary-cause determination, or a statistical-significance claim.
- Time trend, seasonality, promotions, inventory, demand, customer mix, discounting, and external conditions remain possible alternative explanations.
- The method requires sufficient valid full-week observations and governed `product_id` / Revenue evidence.
- The installed public plugin is narrower than the repository/MVP and currently refuses positive diagnostic explanations.
- External validation is not established; public examples and fixtures are synthetic.

### Current release and validation status

<!-- fact: release=v0.3.0,public,tag-v0.3.0 -->
<!-- fact: validation=p00-pass-internal,p01-not-run,p15-not-pass -->

- Current version: `v0.3.0`; Git tag: `v0.3.0`; GitHub release: public after the publication gate.
- P00: **PASS** — internal expert rehearsal with 0 external participants.
- P01 external first-user pilot: **NOT RUN**. P15: **NOT PASS**.

P00 is internal rehearsal evidence only, not external validation, usability proof, or production-readiness evidence. See the [P00 closeout](validation/p15/P00_INTERNAL_PROTOCOL_REHEARSAL_CLOSEOUT.md).

### Documentation, license, and release

- [Public usage](docs/USAGE.md)
- [Development notes](docs/DEVELOPMENT.md)
- [Public examples](examples/public_v0_1/README.md)
- [R7 method authority](decisions/R7-001-first-diagnostic-method-authority.md)
- [v0.3.0 release notes](release-notes/v0.3.0.md)
- [v0.2.0 historical release notes](release-notes/v0.2.0.md)
- [MIT License](LICENSE)

The frozen specifications remain authoritative. This README describes the current public surface and repository/MVP capability without replacing them.

---

<a id="traditional-chinese"></a>

## 繁體中文

CommerceLens 是開源 Codex 外掛程式與受證據治理的電商 CSV/XLSX 分析 repository。它將「發生了什麼」、「觀察到的 Revenue 變化如何組成」，以及「一個已核准的診斷假設是否符合預先定義、由證據支持的準則」分開處理。

目前安裝後的公開外掛程式支援描述性分析。repository/MVP 另外實作產品層級 Revenue 機械式分解與一個受治理的診斷 family；這兩項能力尚未接到安裝後的公開外掛程式互動介面。

<!-- fact: inputs=csv,xlsx -->
<!-- fact: metrics=revenue,orders,aov,absolute-revenue-change -->
<!-- fact: analytical-layers=descriptive,mechanical-decomposition,governed-diagnostic-testing -->
<!-- fact: diagnostic-scope=repository-mvp-only,product_composition_association,weekly_product_presence_revenue_association@1.0.0 -->

> CommerceLens 只陳述受治理證據支持的結論，並拒絕不受支持的解釋。

### 三個分析層級

1. **描述性——發生了什麼？** 在受治理的範圍與期間內計算 Revenue、Orders、AOV 與絕對 Revenue Change。
2. **機械式分解——觀察到的 Revenue 變化如何組成？** 在適用時分解產品層級 Revenue contribution，但不把 contribution 視為因果關係。
3. **受治理的診斷測試——一個已核准的假設是否符合預先定義、由證據支持的準則？** MVP 只支援 repository R7 service 中的 `product_composition_association`，方法為 `weekly_product_presence_revenue_association@1.0.0`。安裝後的公開外掛程式目前尚未提供此能力。

### 合成資料範例

#### 範例 1——證據不足

**合成資料範例——不是真實商家或客戶資料。**

> **問題：** Revenue 為什麼從 Q3 下降到 Q4？
>
> **示意輸出：** Revenue 下降 18%。現有證據足以計算 Revenue 變化，但不足以測試受治理的診斷解釋。證據不足，無法判定 Revenue 下降的原因。

系統不會編造任何可能原因。這是目前安裝後的公開外掛程式面對診斷問題的行為。

#### 範例 2——repository/MVP 診斷 service 的證據充足情境

**合成資料範例——不是真實商家或客戶資料。**

下列數值來自經獨立重新計算的 canonical R7 conformance fixture `FX-R7-PROD-001A`，不是 production benchmark：

| 項目 | 合成數值 |
|---|---:|
| Revenue 降幅 | 18% |
| 有效每週觀察值 | 8 |
| Baseline 週數 | 4 |
| Comparison 週數 | 4 |
| 經驗證的 Spearman rho | -1.0 |
| 支持準則 | rho <= -0.50 |
| 分析結果 | `CRITERION_MET` |

系統將產品組合作為一個受治理的診斷假設進行測試。在受治理的每週觀察值中，較大的 product-presence composition distance 與較低的每週 Revenue 表現有關。獨立驗證的 Spearman rho 為 -1.0，符合預先定義的支持準則 rho <= -0.50。因此，證據支持把產品組合保留為診斷解釋中的一個可能貢獻因素。

這不建立因果關係，也不表示產品組合是唯一或主要原因。季節性、折扣、庫存、整體需求、促銷、客戶組合、時間趨勢與外部市場狀況仍是其他可能解釋。

`CRITERION_MET` 不等於因果關係、唯一原因判定、`ClaimDecision` 或 `Finding`。

![CommerceLens 流程：商務問題經過證據 admission；證據不足時拒絕不受支持的解釋，證據充足時才產生經驗證且有界的診斷解釋。](docs/assets/readme/commerce-lens-flow-zh-TW.svg)

### 核心流程

```text
商務問題
↓
指標／範圍／期間定義
↓
來源 mapping
↓
來源完整性檢查
↓
確定性指標計算
↓
適用時執行機械式分解
↓
產生受治理的假設
↓
必要證據／admission 檢查
↓
證據是否充足？
├─ 否 → 拒絕不受支持的解釋 → 說明缺少的證據
└─ 是 → 已核准的診斷測試 → 確定性執行
        → 獨立驗證 → 有界的分析結果
        → 有界的原因解釋 → 限制 + 其他可能解釋
```

**關聯不等於因果。**

### 能力與界線

| 能力 | 狀態 |
|---|---|
| 計算 Revenue、Orders、AOV，以及比較絕對 Revenue Change | 安裝後的公開外掛程式 |
| 讀取 CSV/XLSX；使用已確認的非標準欄位 mapping | 安裝後的公開外掛程式 |
| 適用時執行產品層級 Revenue 機械式分解 | Repository/MVP；尚未接到公開外掛程式 |
| 產生受治理的診斷假設 | Repository/MVP；尚未接到公開外掛程式 |
| 證據充足時，以 `weekly_product_presence_revenue_association@1.0.0` 測試 `product_composition_association` | Repository/MVP；尚未接到公開外掛程式 |
| 為該單一診斷 lane 回傳有界且受支持的原因解釋 | Repository/MVP；尚未接到公開外掛程式 |
| 因果解釋、主要／唯一原因判定、任意 root-cause analysis | 尚未建立 |
| 折扣、庫存或外部市場診斷執行 | 不提供 |
| Forecasting、prescriptive recommendations、統計顯著性主張 | 不提供／尚未建立 |
| Revenue Change Percentage、一般產品／類別排名 | 公開外掛程式不支援 |

<!-- fact: public-plugin=revenue,orders,aov,absolute-revenue-change,csv,xlsx,confirmed-mapping -->
<!-- fact: repository-mvp=mechanical-product-revenue-decomposition,governed-hypothesis-generation,one-product-composition-diagnostic,bounded-why-explanation -->
<!-- fact: unavailable=causal,primary-or-sole-cause,general-root-cause,discount-diagnostic,inventory-diagnostic,external-market-diagnostic,forecasting,prescriptive,statistical-significance -->

Revenue 是合格、折扣後且不含稅與運費的商品價值。Orders 計算不同的合格訂單。AOV 是同一 population 的 Revenue 除以 Orders，當 Orders 為零時是 `Undefined`。絕對 Revenue Change 是 comparison Revenue 減去 baseline Revenue。

### 安裝後公開外掛程式的快速開始

```bash
codex --version
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin add commerce-lens --marketplace commerce-lens
codex plugin list
```

重新開啟 Codex session，提供 CSV 或 XLSX 檔案，並提出支援的描述性問題，例如：「2026 年 Q3 到 Q4 的 Revenue 變化多少？」公開流程會在需要時詢問 mapping 或完整性資訊，再計算與驗證支援的指標。一般安裝使用者目前無法透過公開 runner 執行 R7 或取得其正向、有界的原因解釋。請參閱[公開使用說明](docs/USAGE.md)。

### 證據、可靠性與保留

來源完整性與欄位 mapping 是分開的。日期範圍不能證明所有相關頁面、record、status 或 filter 都已包含。使用者確認的完整性是 `USER_DECLARED`，不是獨立驗證。

執行與驗證是分開的。對 R7 而言，validation 會獨立重新計算診斷結果、evidence admission 會經過身分驗證，而且在 authoritative completion 前會驗證完整 R6→R7 lineage。語言模型推理不能取代確定性執行證據或 `ClaimDecision`。

Retention 是 opt-in；temporary execution 是預設。Operator 可列出、檢視與驗證明確保留的 run：

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --list-retained
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --inspect-run RUN_ID
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --verify-run RUN_ID
```

Retained bundle 只有在 integrity checks 與 completion marker 都成功後才回報 `retained_complete`。本機保留資料是明文，沒有 TTL、加密或安全抹除。請參閱[開發說明](docs/DEVELOPMENT.md)。

<!-- fact: retention=temporary-default,opt-in,list-inspect-verify,plaintext,no-ttl,no-encryption,no-secure-erase -->

### 診斷限制

- MVP 只實作一個受治理的診斷 family/method。
- 結果是觀察到的關聯，不是因果證明、主要原因判定或統計顯著性主張。
- 時間趨勢、季節性、促銷、庫存、需求、客戶組合、折扣與外部狀況仍是其他可能解釋。
- 方法需要足夠的有效完整週觀察值，以及受治理的 `product_id` / Revenue 證據。
- 安裝後的公開外掛程式範圍比 repository/MVP 窄，目前會拒絕正向診斷解釋。
- 尚未建立外部驗證；公開範例與 fixture 都是合成資料。

### 目前 release 與驗證狀態

<!-- fact: release=v0.3.0,public,tag-v0.3.0 -->
<!-- fact: validation=p00-pass-internal,p01-not-run,p15-not-pass -->

- 目前版本：`v0.3.0`；Git tag：`v0.3.0`；GitHub release：publication gate 通過後公開。
- P00：**PASS**——內部專家 rehearsal，外部參與者為 0。
- P01 外部 first-user pilot：**NOT RUN**。P15：**NOT PASS**。

P00 只是內部 rehearsal 證據，不是外部驗證、usability proof 或 production-readiness evidence。請參閱 [P00 closeout](validation/p15/P00_INTERNAL_PROTOCOL_REHEARSAL_CLOSEOUT.md)。

### 文件、授權與 release

- [公開使用說明](docs/USAGE.md)
- [開發說明](docs/DEVELOPMENT.md)
- [公開範例](examples/public_v0_1/README.md)
- [R7 方法 authority](decisions/R7-001-first-diagnostic-method-authority.md)
- [v0.3.0 release notes](release-notes/v0.3.0.md)
- [v0.2.0 歷史 release notes](release-notes/v0.2.0.md)
- [MIT License](LICENSE)

Frozen specifications 仍是權威。本 README 描述目前公開介面與 repository/MVP 能力，不會取代這些規格。

---

<a id="simplified-chinese"></a>

## 简体中文

CommerceLens 是开源 Codex 插件与受证据治理的电商 CSV/XLSX 分析 repository。它将“发生了什么”、“观察到的 Revenue 变化如何组成”，以及“一个已批准的诊断假设是否满足预先定义、由证据支持的准则”分开处理。

目前安装后的公开插件支持描述性分析。repository/MVP 另外实现产品级 Revenue 机械分解与一个受治理的诊断 family；这两项能力尚未接入安装后的公开插件交互界面。

<!-- fact: inputs=csv,xlsx -->
<!-- fact: metrics=revenue,orders,aov,absolute-revenue-change -->
<!-- fact: analytical-layers=descriptive,mechanical-decomposition,governed-diagnostic-testing -->
<!-- fact: diagnostic-scope=repository-mvp-only,product_composition_association,weekly_product_presence_revenue_association@1.0.0 -->

> CommerceLens 只陈述受治理证据支持的结论，并拒绝不受支持的解释。

### 三个分析层级

1. **描述性——发生了什么？** 在受治理的范围与期间内计算 Revenue、Orders、AOV 与绝对 Revenue Change。
2. **机械分解——观察到的 Revenue 变化如何组成？** 在适用时分解产品级 Revenue contribution，但不把 contribution 视为因果关系。
3. **受治理的诊断测试——一个已批准的假设是否满足预先定义、由证据支持的准则？** MVP 只支持 repository R7 service 中的 `product_composition_association`，方法为 `weekly_product_presence_revenue_association@1.0.0`。安装后的公开插件目前尚未提供此能力。

### 合成数据示例

#### 示例 1——证据不足

**合成数据示例——不是真实商家或客户数据。**

> **问题：** Revenue 为什么从 Q3 下降到 Q4？
>
> **示意输出：** Revenue 下降 18%。现有证据足以计算 Revenue 变化，但不足以测试受治理的诊断解释。证据不足，无法判断 Revenue 下降的原因。

系统不会编造任何可能原因。这是目前安装后的公开插件面对诊断问题的行为。

#### 示例 2——repository/MVP 诊断 service 的证据充足情形

**合成数据示例——不是真实商家或客户数据。**

以下数值来自经独立重新计算的 canonical R7 conformance fixture `FX-R7-PROD-001A`，不是 production benchmark：

| 项目 | 合成数值 |
|---|---:|
| Revenue 降幅 | 18% |
| 有效每周观察值 | 8 |
| Baseline 周数 | 4 |
| Comparison 周数 | 4 |
| 经验证的 Spearman rho | -1.0 |
| 支持准则 | rho <= -0.50 |
| 分析结果 | `CRITERION_MET` |

系统将产品组合作为一个受治理的诊断假设进行测试。在受治理的每周观察值中，较大的 product-presence composition distance 与较低的每周 Revenue 表现有关。独立验证的 Spearman rho 为 -1.0，满足预先定义的支持准则 rho <= -0.50。因此，证据支持把产品组合保留为诊断解释中的一个可能贡献因素。

这不建立因果关系，也不表示产品组合是唯一或主要原因。季节性、折扣、库存、整体需求、促销、客户组合、时间趋势与外部市场状况仍是其他可能解释。

`CRITERION_MET` 不等于因果关系、唯一原因判定、`ClaimDecision` 或 `Finding`。

![CommerceLens 流程：业务问题经过证据 admission；证据不足时拒绝不受支持的解释，证据充足时才产生经验证且有边界的诊断解释。](docs/assets/readme/commerce-lens-flow-zh-CN.svg)

### 核心流程

```text
业务问题
↓
指标／范围／期间定义
↓
来源 mapping
↓
来源完整性检查
↓
确定性指标计算
↓
适用时执行机械分解
↓
生成受治理的假设
↓
必要证据／admission 检查
↓
证据是否充足？
├─ 否 → 拒绝不受支持的解释 → 说明缺少的证据
└─ 是 → 已批准的诊断测试 → 确定性执行
        → 独立验证 → 有边界的分析结果
        → 有边界的原因解释 → 限制 + 其他可能解释
```

**关联不等于因果。**

### 能力与边界

| 能力 | 状态 |
|---|---|
| 计算 Revenue、Orders、AOV，以及比较绝对 Revenue Change | 安装后的公开插件 |
| 读取 CSV/XLSX；使用已确认的非标准字段 mapping | 安装后的公开插件 |
| 适用时执行产品级 Revenue 机械分解 | Repository/MVP；尚未接入公开插件 |
| 生成受治理的诊断假设 | Repository/MVP；尚未接入公开插件 |
| 证据充足时，以 `weekly_product_presence_revenue_association@1.0.0` 测试 `product_composition_association` | Repository/MVP；尚未接入公开插件 |
| 为该单一诊断 lane 返回有边界且受支持的原因解释 | Repository/MVP；尚未接入公开插件 |
| 因果解释、主要／唯一原因判定、任意 root-cause analysis | 尚未建立 |
| 折扣、库存或外部市场诊断执行 | 不提供 |
| Forecasting、prescriptive recommendations、统计显著性主张 | 不提供／尚未建立 |
| Revenue Change Percentage、通用产品／类别排名 | 公开插件不支持 |

<!-- fact: public-plugin=revenue,orders,aov,absolute-revenue-change,csv,xlsx,confirmed-mapping -->
<!-- fact: repository-mvp=mechanical-product-revenue-decomposition,governed-hypothesis-generation,one-product-composition-diagnostic,bounded-why-explanation -->
<!-- fact: unavailable=causal,primary-or-sole-cause,general-root-cause,discount-diagnostic,inventory-diagnostic,external-market-diagnostic,forecasting,prescriptive,statistical-significance -->

Revenue 是合格、折扣后且不含税与运费的商品价值。Orders 计算不同的合格订单。AOV 是同一 population 的 Revenue 除以 Orders，当 Orders 为零时是 `Undefined`。绝对 Revenue Change 是 comparison Revenue 减去 baseline Revenue。

### 安装后公开插件的快速开始

```bash
codex --version
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin add commerce-lens --marketplace commerce-lens
codex plugin list
```

重新启动 Codex session，提供 CSV 或 XLSX 文件，并提出支持的描述性问题，例如：“2026 年 Q3 到 Q4 的 Revenue 变化是多少？”公开流程会在需要时询问 mapping 或完整性信息，再计算与验证支持的指标。普通安装用户目前无法通过公开 runner 执行 R7 或获得其正向、有边界的原因解释。请参阅[公开使用说明](docs/USAGE.md)。

### 证据、可靠性与保留

来源完整性与字段 mapping 是分开的。日期范围不能证明所有相关页面、record、status 或 filter 都已包含。用户确认的完整性是 `USER_DECLARED`，不是独立验证。

执行与验证是分开的。对 R7 而言，validation 会独立重新计算诊断结果、evidence admission 会经过身份验证，而且在 authoritative completion 前会验证完整 R6→R7 lineage。语言模型推理不能替代确定性执行证据或 `ClaimDecision`。

Retention 是 opt-in；temporary execution 是默认方式。Operator 可列出、检查与验证明确保留的 run：

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --list-retained
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --inspect-run RUN_ID
python3.11 skills/commerce-lens/scripts/run_public_analysis.py --retention-root ROOT --verify-run RUN_ID
```

Retained bundle 只有在 integrity checks 与 completion marker 都成功后才报告 `retained_complete`。本地保留数据是明文，没有 TTL、加密或安全擦除。请参阅[开发说明](docs/DEVELOPMENT.md)。

<!-- fact: retention=temporary-default,opt-in,list-inspect-verify,plaintext,no-ttl,no-encryption,no-secure-erase -->

### 诊断限制

- MVP 只实现一个受治理的诊断 family/method。
- 结果是观察到的关联，不是因果证明、主要原因判定或统计显著性主张。
- 时间趋势、季节性、促销、库存、需求、客户组合、折扣与外部状况仍是其他可能解释。
- 方法需要足够的有效完整周观察值，以及受治理的 `product_id` / Revenue 证据。
- 安装后的公开插件范围比 repository/MVP 窄，目前会拒绝正向诊断解释。
- 尚未建立外部验证；公开示例与 fixture 都是合成数据。

### 当前 release 与验证状态

<!-- fact: release=v0.3.0,public,tag-v0.3.0 -->
<!-- fact: validation=p00-pass-internal,p01-not-run,p15-not-pass -->

- 当前版本：`v0.3.0`；Git tag：`v0.3.0`；GitHub release：publication gate 通过后公开。
- P00：**PASS**——内部专家 rehearsal，外部参与者为 0。
- P01 外部 first-user pilot：**NOT RUN**。P15：**NOT PASS**。

P00 只是内部 rehearsal 证据，不是外部验证、usability proof 或 production-readiness evidence。请参阅 [P00 closeout](validation/p15/P00_INTERNAL_PROTOCOL_REHEARSAL_CLOSEOUT.md)。

### 文档、许可与 release

- [公开使用说明](docs/USAGE.md)
- [开发说明](docs/DEVELOPMENT.md)
- [公开示例](examples/public_v0_1/README.md)
- [R7 方法 authority](decisions/R7-001-first-diagnostic-method-authority.md)
- [v0.3.0 release notes](release-notes/v0.3.0.md)
- [v0.2.0 历史 release notes](release-notes/v0.2.0.md)
- [MIT License](LICENSE)

Frozen specifications 仍是权威。本 README 描述当前公开界面与 repository/MVP 能力，不会替代这些规范。
