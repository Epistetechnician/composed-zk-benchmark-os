# Statebook Literature, Code, Media, and Incident Source Index

State slice: `statebook-whitepaper-prd-and-publication-media-boundary`.

Status: `DocumentationOnly`.

Evidence ceiling: `Level0DesignNote`.

Version: 0.1, 15 July 2026.

## Purpose and selection rule

This index supports the Statebook whitepaper and product requirements document.
It is a bounded, decision-relevant bibliography, not a claim to enumerate every
paper, market, codebase, regulation, or incident related to financial market
infrastructure. Sources were selected when they materially constrain at least
one of the following questions:

1. Can contracts with different product labels be represented as payoffs over
   common terminal states?
2. Can an economically equivalent portfolio be found and executed?
3. Can collateral and liquidation policy recognize the offset without hiding
   basis, oracle, liquidity, legal, or settlement risk?
4. Can externalization speed be adjusted using explicit assurance evidence,
   bounded loss budgets, and fail-closed state transitions?
5. Which AI, compute, energy, and macroeconomic developments are likely to
   create new frontier-risk underlyings or new attack capacity?

Every entry states what it supports and what it does not establish. A link,
paper, repository, or incident report does not validate the proposed Statebook,
authorize settlement, or raise this repository's evidence ceiling.

Observation date for mutable venue documentation, help-center pages, social
posts, and repository revisions: 15 July 2026. These sources record public
claims or code snapshots observed on that date; they do not establish deployment
state, current availability, liquidity, incident causation, or evidence above
`Level0DesignNote`.

## Evidence classes

| Class | Permitted use | Prohibited inference |
| --- | --- | --- |
| Seminal theory | Define the intellectual lineage and formal problem | Treat assumptions as observed market facts |
| Peer-reviewed or working research | Support models, empirical patterns, or design alternatives | Treat one model as universal or production calibrated |
| Public authority or standard | Establish legal, prudential, operational, or terminology constraints | Infer legal approval for this product |
| Venue or vendor documentation | Describe a venue's stated product and operating model | Infer implementation correctness or solvency |
| Pinned source code | Inspect a disclosed implementation path at one revision | Infer deployed bytecode identity, audit status, or exploit root cause |
| Incident evidence | Establish a bounded chronology or disclosed failure mode | Generalize causality beyond the evidence |
| Media or interview | Attribute a thesis, phrase, or operator view | Treat marketing or commentary as independent validation |
| Scenario source | Bound plausible macro or technology trajectories | Present a scenario as a forecast |

## A. Complete markets, state prices, and payoff spanning

### T01 - Arrow, risk-bearing securities

- Source: Kenneth J. Arrow, “The Role of Securities in the Optimal Allocation
  of Risk-bearing,” *Review of Economic Studies* 31(2), 1964.
- Link: <https://doi.org/10.2307/2296188>
- Supports: state-contingent claims as a basis for allocating risk across
  possible future states.
- Limit: assumes a stylized economy; it does not solve contract normalization,
  execution, settlement, or margin recognition in fragmented venues.

### T02 - Debreu, commodities indexed by state and time

- Source: Gérard Debreu, *Theory of Value: An Axiomatic Analysis of Economic
  Equilibrium*, Cowles Foundation Monograph 17, January 1959.
- Link: <https://cowles.yale.edu/research/cfm-17-theory-value-axiomatic-analysis-economic-equilibrium>
- Supports: treating time, location, and state as economically material parts
  of a commodity definition.
- Limit: provides a mathematical foundation, not an exchange architecture.

### T02A - Arrow-Debreu equilibrium

- Source: Kenneth J. Arrow and Gérard Debreu, “Existence of an Equilibrium for
  a Competitive Economy,” *Econometrica* 22(3), July 1954, pp. 265-290.
- Link: <https://doi.org/10.2307/1907353>
- Supports: date-state commodity indexing and the equilibrium foundation for
  complete contingent-claim markets.
- Limit: existence under strong assumptions, not uniqueness, computability,
  execution, margin, or settlement.

### T02B - Sequential incomplete markets

- Source: Roy Radner, “Existence of Equilibrium of Plans, Prices, and Price
  Expectations in a Sequence of Markets,” *Econometrica* 40(2), March 1972,
  pp. 289-303.
- Link: <https://doi.org/10.2307/1909407>
- Supports: sequential trading when a complete date-zero state-claim market is
  unavailable.
- Limit: strong theoretical assumptions and no modern venue, collateral, or
  settlement mechanics.

### T02C - Incomplete-market welfare limit

- Source: Oliver D. Hart, “On the Optimality of Equilibrium When the Market
  Structure Is Incomplete,” *Journal of Economic Theory* 11(3), December 1975,
  pp. 418-443.
- Link: <https://doi.org/10.1016/0022-0531(75)90028-9>
- Supports: incomplete markets can produce constrained inefficiency.
- Limit: a welfare theorem, not a Statebook architecture or empirical estimate.

### T02D - Generic existence in incomplete markets

- Source: Darrell Duffie and Wayne Shafer, “Equilibrium in Incomplete Markets:
  I: A Basic Model of Generic Existence,” *Journal of Mathematical Economics*
  14(3), 1985, pp. 285-300.
- Link: <https://doi.org/10.1016/0304-4068(85)90004-7>
- Supports: generic existence of equilibrium in a specified incomplete-market
  model.
- Limit: an existence result under declared assumptions does not establish
  welfare, computational tractability, venue interoperability, or Statebook
  feasibility.

### T03 - Ross, options and payoff completeness

- Source: Stephen A. Ross, “Options and Efficiency,” *Quarterly Journal of
  Economics* 90(1), 1976.
- Link: <https://doi.org/10.2307/1886087>
- Supports: options can expand the span of attainable payoffs and complete a
  market under stated assumptions.
- Limit: listing more options does not establish executable equivalence or
  collateral offsets in practice.

### T04 - Breeden and Litzenberger, state-contingent prices

- Source: Douglas T. Breeden and Robert H. Litzenberger, “Prices of
  State-Contingent Claims Implicit in Option Prices,” *Journal of Business*
  51(4), 1978.
- Link: <https://doi.org/10.1086/296025>
- Supports: option price surfaces can reveal prices for state-contingent
  payoffs under model assumptions.
- Limit: noisy, sparse, path-dependent, or differently settled contracts can
  violate the assumptions required for clean extraction.

### T05 - Harrison and Pliska, no-arbitrage pricing

- Source: J. Michael Harrison and Stanley R. Pliska, “Martingales and
  Stochastic Integrals in the Theory of Continuous Trading,” *Stochastic
  Processes and their Applications* 11(3), 1981.
- Link: <https://doi.org/10.1016/0304-4149(81)90026-0>
- Supports: the no-arbitrage and equivalent-martingale-measure foundation for
  comparing replicating portfolios.
- Limit: real execution has discrete books, costs, funding, liquidity, credit,
  and legal constraints absent from the idealized model.

### T05A - Option replication

- Source: Fischer Black and Myron Scholes, “The Pricing of Options and Corporate
  Liabilities,” *Journal of Political Economy* 81(3), May-June 1973.
- Link: <https://doi.org/10.1086/260062>
- Supports: no-arbitrage replication and decomposition of liabilities into
  option exposures.
- Limit: frictionless continuous-trading assumptions; no cross-venue, legal,
  funding, or oracle equivalence.

### T05B - Compositional financial-contract semantics

- Source: Simon Peyton Jones, Jean-Marc Eber, and Julian Seward, “Composing
  Contracts: An Adventure in Financial Engineering,” *ICFP 2000*, pp. 280-292.
- Links: <https://doi.org/10.1145/351240.351267> and
  <https://www.microsoft.com/en-us/research/publication/composing-contracts-an-adventure-in-financial-engineering/>
- Supports: a compositional contract DSL, denotational semantics, and executable
  interpretation.
- Limit: formal semantics do not establish legal enforceability, market
  liquidity, settlement, or correct reference data.

### T05C - ACTUS contract-event semantics

- Source: ACTUS Financial Research Foundation, “Technical Specifications” and
  “Methodology,” living standard observed 15 July 2026.
- Links: <https://www.actusfrf.org/techspecs> and
  <https://www.actusfrf.org/methodology>
- Supports: mapping contract terms into deterministic contract events, states,
  and cash flows.
- Limit: living source requiring an implementation-version pin; not arbitrary
  payoff equivalence or venue authority.

### T05D - Certified compilation of financial contracts

- Source: Danil Annenkov and Martin Elsman, “Certified Compilation of Financial
  Contracts,” *PPDP 2018*, pp. 5:1-5:13.
- Link: <https://doi.org/10.1145/3236950.3236955>
- Supports: compilation from a financial-contract language to payoff code with
  machine-checked semantic-preservation results under the formalized model.
- Limit: certified compilation relative to a semantics does not establish legal
  interpretation, reference-data correctness, liquidity, collateral
  recognition, or settlement authority.

### T06 - Duffie, dynamic asset pricing

- Source: Darrell Duffie, *Dynamic Asset Pricing Theory*, 3rd ed., Princeton
  University Press, 2001.
- Link: <https://press.princeton.edu/books/hardcover/9780691090221/dynamic-asset-pricing-theory>
- Supports: formal language for dynamic trading, contingent claims, and
  incomplete markets.
- Limit: textbook theory does not determine Statebook product policy.

### T07 - Shiller, perpetual futures

- Source: Robert J. Shiller, “Measuring Asset Values for Cash Settlement in
  Derivative Markets: Hedonic Repeated Measures Indices and Perpetual Futures,”
  *Journal of Finance* 48(3), 1993.
- Link: <https://doi.org/10.1111/j.1540-6261.1993.tb04024.x>
- Supports: perpetual futures as continuing exposures tied to a reference
  measure rather than ordinary terminal claims.
- Limit: it does not establish that a modern crypto perpetual is equivalent to
  a terminal event contract or option portfolio.

### T08 - Modern perpetual-contract pricing

- Source: Songrun He, Asaf Manela, Omri Ross, and Victor von Wachter,
  “Fundamentals of Perpetual Futures,” arXiv:2212.06888, submitted 13 December
  2022; version 6 revised 21 August 2024.
- Link: <https://arxiv.org/abs/2212.06888>
- Supports: formal treatment of funding mechanisms and prices in perpetual
  contracts.
- Limit: venue-specific funding, liquidation, and oracle mechanics remain
  decisive.

### T09 - Replication of perpetual contracts

- Source: Damien Ackerer, Julien Hugonnier, and Urban Jermann, “Perpetual
  Futures Pricing,” *Mathematical Finance* 36(3), July 2026, pp. 481-499; first
  published online 20 November 2025.
- Link: <https://doi.org/10.1111/mafi.70018>
- Supports: pricing and arbitrage relations for perpetual futures under
  explicit mechanisms.
- Limit: does not imply cross-venue execution or collateral completeness.

## B. Market microstructure, information markets, and execution

### T10 - Kyle, informed trading and liquidity

- Source: Albert S. Kyle, “Continuous Auctions and Insider Trading,”
  *Econometrica* 53(6), 1985.
- Link: <https://doi.org/10.2307/1913210>
- Supports: liquidity, informed order flow, and price impact as endogenous
  market properties.
- Limit: a semantic payoff match does not remove market impact.

### T11 - Glosten and Milgrom, bid-ask spreads

- Source: Lawrence R. Glosten and Paul R. Milgrom, “Bid, Ask and Transaction
  Prices in a Specialist Market with Heterogeneously Informed Traders,”
  *Journal of Financial Economics* 14(1), 1985.
- Link: <https://doi.org/10.1016/0304-405X(85)90044-3>
- Supports: adverse selection as a source of spreads and execution cost.
- Limit: does not cover the full operational and settlement stack.

### T11A - Electronic limit-order-book structure

- Source: Lawrence R. Glosten, “Is the Electronic Open Limit Order Book
  Inevitable?”, *Journal of Finance* 49(4), September 1994, pp. 1127-1161.
- Link: <https://doi.org/10.1111/j.1540-6261.1994.tb02450.x>
- Supports: liquidity provision and adverse selection in a single-instrument
  electronic order book.
- Limit: does not establish semantic or operational equivalence across
  contracts.

### T12 - Frequent batch auctions

- Source: Eric Budish, Peter Cramton, and John Shim, “The High-Frequency Trading
  Arms Race: Frequent Batch Auctions as a Market Design Response,” *Quarterly
  Journal of Economics* 130(4), 2015.
- Link: <https://doi.org/10.1093/qje/qjv027>
- Supports: discrete batching as a response to continuous-time speed races and
  mechanical arbitrage.
- Limit: batching execution is not the same as delaying asset externalization.

### T13 - Prediction-market synthesis

- Source: Justin Wolfers and Eric Zitzewitz, “Prediction Markets,” *Journal of
  Economic Perspectives* 18(2), 2004.
- Link: <https://doi.org/10.1257/0895330041371321>
- Supports: prediction-market information aggregation, calibration, and design
  tradeoffs.
- Limit: binary-event calibration does not establish derivative replication or
  legal fungibility.

### T13A - Prediction-price interpretation limit

- Source: Charles F. Manski, “Interpreting the Predictions of Prediction
  Markets,” *Economics Letters* 91(3), June 2006, pp. 425-429.
- Link: <https://doi.org/10.1016/j.econlet.2006.01.004>
- Supports: a binary-contract price is not automatically an objective
  probability outside restrictive assumptions.
- Limit: stylized risk-neutral, price-taking model.

### T14 - Combinatorial information markets

- Source: Robin Hanson, “Combinatorial Information Market Design,”
  *Information Systems Frontiers* 5, 2003.
- Link: <https://doi.org/10.1023/A:1022058209073>
- Supports: markets over combinatorial state spaces and the computational
  difficulty of coherent pricing.
- Limit: computational market making does not guarantee executable portfolios
  across external venues.

### T15 - Logarithmic market scoring rule

- Source: Robin Hanson, “Logarithmic Market Scoring Rules for Modular
  Combinatorial Information Aggregation,” *Journal of Prediction Markets* 1(1),
  February 2007, pp. 3-15.
- Link: <https://doi.org/10.5750/jpm.v1i1.417>
- Supports: bounded-loss automated market making and modular conditional
  markets.
- Limit: the bounded-loss property depends on the specified market-maker model,
  not on the Statebook as a whole.

### T16 - Automated market makers and loss-versus-rebalancing

- Source: Jason Milionis, Ciamac C. Moallemi, Tim Roughgarden, and Anthony Lee
  Zhang, “Automated Market Making and Loss-Versus-Rebalancing,” arXiv:2208.06046,
  submitted 11 August 2022; version 5 revised 27 May 2024.
- Link: <https://arxiv.org/abs/2208.06046>
- Supports: decomposition of AMM performance and adverse selection costs.
- Limit: does not directly calibrate central-limit-order-book or clearing risk.

## C. Clearing, collateral, settlement, and linked obligations

### I01 - Principles for Financial Market Infrastructures

- Source: Committee on Payment and Settlement Systems and Technical Committee of
  IOSCO, *Principles for Financial Market Infrastructures*, 16 April 2012.
- Link: <https://www.bis.org/cpmi/publ/d101.htm>
- Supports: legal basis, governance, credit, collateral, margin, liquidity,
  settlement finality, operational risk, links, default management, and
  disclosure as distinct infrastructure obligations.
- Limit: application depends on jurisdiction, legal form, and supervisory
  perimeter.

### I02 - Tokenisation arrangements

- Source: CPMI, *Tokenisation in the Context of Money and Other Assets: Concepts
  and Implications for Central Banks*, 2024.
- Link: <https://www.bis.org/cpmi/publ/d225.htm>
- Supports: atomic delivery-versus-payment, principal-risk reduction,
  governance, liquidity, interoperability, and netting tradeoffs.
- Limit: atomicity can reduce one risk while increasing liquidity or
  operational concentration; tokenisation does not itself create coherence.

### I02A - Delivery versus payment

- Source: CPSS, *Delivery versus Payment in Securities Settlement Systems*, 9
  September 1992.
- Link: <https://www.bis.org/cpmi/publ/d06.htm>
- Supports: principal-risk reduction and three gross/net DvP models.
- Limit: predates tokenisation; DvP linkage does not always mean technical
  simultaneity.

### I02B - Technical and legal finality

- Source: CPMI, *Distributed Ledger Technology in Payment, Clearing and
  Settlement: An Analytical Framework*, February 2017.
- Link: <https://www.bis.org/cpmi/publ/d157.htm>
- Supports: separating ledger consensus or operational transfer from legally
  irrevocable, unconditional, and insolvency-resistant settlement finality.
- Limit: analytical framework, not governing law or a legal opinion.

### I03 - Securities settlement tradeoffs

- Source: Morten Linnemann Bech, Jenny Hancock, Tara Rice, and Amber Wadsworth,
  “On the Future of Securities Settlement,” *BIS Quarterly Review*, 1 March 2020.
- Link: <https://www.bis.org/publ/qtrpdf/r_qt2003i.htm>
- Supports: shorter settlement and tokenisation can reduce replacement-cost
  exposure while increasing cash and securities liquidity needs; credit-
  liquidity tradeoffs remain.
- Limit: institutional analysis, not Statebook approval, legal advice, or
  production calibration.

### I04 - Payment-versus-payment settlement

- Source: CPMI, *Facilitating Increased Adoption of Payment versus Payment
  (PvP): Final Report*, 27 March 2023.
- Link: <https://www.bis.org/cpmi/publ/d216.htm>
- Supports: principal risk, settlement windows, interoperability, and barriers
  to PvP adoption.
- Limit: Statebook portfolios can contain obligations outside eligible PvP
  rails.

### I05 - Fast payments

- Source: CPMI, *Fast Payments - Enhancing the Speed and Availability of Retail
  Payments*, 2016.
- Link: <https://www.bis.org/cpmi/publ/d154.pdf>
- Supports: faster final-funds availability changes fraud, liquidity, credit,
  security, and consumer-protection demands.
- Limit: retail payment systems are not derivatives clearing systems.

### I06 - CCP counterparty-risk netting

- Source: Darrell Duffie and Haoxiang Zhu, “Does a Central Clearing Counterparty
  Reduce Counterparty Risk?”, *Review of Asset Pricing Studies* 1(1), 2011.
- Link: <https://doi.org/10.1093/rapstu/rar001>
- Supports: introducing a CCP can increase or decrease netting efficiency
  depending on product scope and existing bilateral netting sets.
- Limit: centralization is not automatically risk reducing.

### I06A - Close-out netting legal basis

- Source: ISDA, *2018 Model Netting Act and Guide*, 15 October 2018.
- Link: <https://www.isda.org/book/2018-model-netting-act-and-guide/>
- Supports: legal certainty and enforceability as prerequisites for close-out
  netting and capital recognition.
- Limit: model legislation only until enacted; jurisdiction-specific law and
  legal opinions remain necessary.

### I06B - Regulated cross-margin example

- Source: CFTC, “Order Providing Exemptive Relief To Facilitate Cross-Margining
  of Customer Positions Cleared at Chicago Mercantile Exchange, Inc. and Fixed
  Income Clearing Corporation,” 91 FR 20880, applicable 15 April 2026.
- Link: <https://www.cftc.gov/LawRegulation/FederalRegister/final-rules/2026-07643.html>
- Supports: capital offsets require defined products, accounts, margin
  calculations, operational coordination, customer protection, and legal
  conditions.
- Limit: narrow regulated arrangement, not general cross-venue offset
  authorization or Statebook calibration.

### I07 - CCP resilience guidance

- Source: CPMI-IOSCO, *Resilience of Central Counterparties: Further Guidance
  on the PFMI*, 2017.
- Link: <https://www.bis.org/cpmi/publ/d163.htm>
- Supports: governance, credit and liquidity stress, margin, prefunded
  resources, and recovery planning.
- Limit: does not authorize a Statebook to recognize cross-venue offsets.

### I08 - CME SPAN

- Source: CME Group, “SPAN Methodology Overview.”
- Link: <https://www.cmegroup.com/solutions/risk-management/performance-bonds-margins/span-methodology-overview.html>
- Supports: scenario-based portfolio risk and performance-bond methodology as
  an institutional example of portfolio margin.
- Limit: methodology and parameterization are venue governed; this reference
  does not license SPAN or reproduce its full implementation.

### I09 - OCC STANS

- Source: Options Clearing Corporation, “Margin Methodology.”
- Link: <https://www.theocc.com/risk-management/margin-methodology>
- Supports: Monte Carlo portfolio margin and dependence-sensitive risk
  measurement in a regulated clearing context.
- Limit: production methodology is not reducible to a public summary and is
  not a Statebook calibration source.

### I10 - 24/7 derivatives risk advisory

- Source: CFTC Divisions of Clearing and Risk, Market Oversight, and Market
  Participants, *Staff Advisory for Extending Trading and/or Clearing Operations
  to a 24 Hours-a-Day, 7 Days-a-Week Basis*, CFTC Letter No. 26-16, 29 May 2026.
- Link: <https://www.cftc.gov/csl/26-16/download>
- Supports: staff expectations concerning surveillance, thin liquidity,
  reference-market closures, staffing, collateral, settlement, and system
  safeguards for registrants considering 24/7 operations.
- Limit: informational staff views; the advisory creates no new obligations and
  is not Commission action.

### I11 - Event-contract rulemaking inquiry

- Source: CFTC, *Prediction Markets*, Advance Notice of Proposed Rulemaking, 91
  FR 12516, published 16 March 2026.
- Link: <https://www.cftc.gov/LawRegulation/FederalRegister/proposedrules/2026-05105.html>
- Supports: event contracts remain subject to public-law boundaries even as
  payoff forms converge technologically.
- Limit: an inquiry is not a final rule or a legal opinion for this product.

### I12 - Tokenized securities distinctions

- Source: U.S. Securities and Exchange Commission Divisions of Corporation
  Finance, Investment Management, and Trading and Markets, “Statement on
  Tokenized Securities,” 28 January 2026.
- Link: <https://www.sec.gov/newsroom/speeches-statements/corp-fin-statement-tokenized-securities-012826-statement-tokenized-securities>
- Supports: issuer-sponsored, custodial third-party, and synthetic tokenized
  instruments can encode materially different rights despite similar economic
  references.
- Limit: a joint staff statement, not a Commission rule or adjudication; its
  scope is U.S. federal securities law.

### I12A - Benchmark governance

- Source: IOSCO Board, *Principles for Financial Benchmarks*, Final Report
  FR07/13, July 2013.
- Link: <https://www.iosco.org/library/pubdocs/pdf/ioscopd415.pdf>
- Supports: governance, input data, methodology, conflicts, accountability, and
  review for financial benchmarks.
- Limit: principles do not prove oracle integrity, manipulation resistance, or
  legal suitability for a specific contract.

### I13 - FINOS Common Domain Model

- Source: FINOS, *Common Domain Model 6.0.0*, “The Common Domain Model” and
  “Product Model,” release revision observed 15 July 2026.
- Documentation: <https://cdm.finos.org/docs/common-domain-model/> and
  <https://cdm.finos.org/docs/product-model/>
- Code at the `6.0.0` tag commit
  `2f86259ee6002e173c7ab3e6f8b0df33ac9754cc`:
  <https://github.com/finos/common-domain-model/tree/2f86259ee6002e173c7ab3e6f8b0df33ac9754cc>
- Supports: composable payout, economic-terms, observable, product, legal-
  agreement, and lifecycle representations.
- Limit: representation does not supply price truth, executable equivalence,
  collateral recognition, legal fungibility, custody, or settlement authority.

### I13A - FpML lifecycle messaging

- Source: ISDA/FpML Standards Committee, *FpML 5.13 Recommendation*, build 7,
  12 May 2025.
- Link: <https://www.fpml.org/spec/fpml-5-13-7-rec-1/>
- Supports: OTC-derivative and structured-product messaging across trade
  lifecycle events.
- Limit: message representation is not payoff equivalence, execution, or legal
  fungibility.

### I13B - ISO 20022 conceptual interoperability

- Source: ISO, *ISO 20022-5:2026 — Financial Services — Universal Financial
  Industry Message Scheme — Part 5: Conceptual Interoperability and Reverse
  Engineering*, 2nd ed., April 2026.
- Link: <https://www.iso.org/standard/20022-5>
- Supports: business-concept and logical-model alignment across financial
  messaging.
- Limit: methodology, not financial payoff normalization or settlement
  authority.

### I13C - Unique Product Identifier

- Source: CFTC, “Order Designating the Unique Product Identifier and Product
  Classification System To Be Used in Recordkeeping and Swap Data Reporting,”
  88 FR 11790, 24 February 2023.
- Link: <https://www.cftc.gov/LawRegulation/FederalRegister/final-rules/2023-03661.html>
- Supports: product and reference classification and aggregation across
  reporting systems.
- Limit: an identifier or taxonomy is not economic equivalence.

### I14 - Basel operational resilience

- Source: Basel Committee on Banking Supervision, *Principles for Operational
  Resilience*, 2021.
- Link: <https://www.bis.org/bcbs/publ/d516.htm>
- Supports: tolerance for disruption, dependency mapping, business continuity,
  and resilient operations.
- Limit: principles require institution-specific implementation.

### I15 - Basel third-party and ICT risk

- Sources: Basel Committee on Banking Supervision, *Principles for the Sound
  Management of Third-Party Risk*, 10 December 2025,
  <https://www.bis.org/bcbs/publ/d605.htm>; and *Information and Communication
  Technology Risk Management: Range of Practices*, 2 June 2026,
  <https://www.bis.org/bcbs/publ/d611.htm>.
- Supports: third-party lifecycle management, supply-chain and nth-party
  dependencies, concentration, contingency, exit, and non-malicious ICT-
  incident risk in banking.
- Limit: banking-sector principles and observed practices, not a quantitative
  Statebook dependency model.

## D. Venue convergence and programmable market infrastructure

### M00 - Cloud economics behind the AWS analogy

- Sources: Amazon Web Services, “What Is Cloud Computing?”, vendor
  documentation observed 15 July 2026,
  <https://docs.aws.amazon.com/whitepapers/latest/aws-overview/what-is-cloud-computing.html>;
  Michael Armbrust et al., “Above the Clouds: A Berkeley View of Cloud
  Computing,” Technical Report UCB/EECS-2009-28, 2009,
  <https://amplab.cs.berkeley.edu/publication/above-the-clouds-a-berkeley-view-of-cloud-computing/>.
- Supports: the cloud shift from large upfront hardware ownership toward
  metered, on-demand service consumption and elastic capacity.
- Limit: AWS is vendor documentation, and cloud economics does not establish
  financial semantics, custody safety, legal finality, collateral recognition,
  or Statebook feasibility.

### M01 - Hyperliquid portfolio margin

- Source: Hyperliquid Docs, “Portfolio Margin,” alpha-labelled documentation
  observed 15 July 2026.
- Link: <https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-margin>
- Supports: the page is headed “Alpha mode” while retaining several “pre-alpha”
  statements, and describes collectively margining selected spot balances,
  perpetuals, and HIP-3 DEXs within one account.
- Limit: eligibility, borrow and supply caps, fallback behavior, and mutable
  internally inconsistent phase labels prevent treating the page as a frozen
  rollout phase, broad availability, proven liquidation safety, or cross-venue
  capital completeness.

### M02 - Hyperliquid builder-deployed perpetuals

- Source: Hyperliquid Improvement Proposal 3.
- Link: <https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-3-builder-deployed-perpetuals>
- Supports: permissionless builder-deployed perpetuals whose deployer controls
  market definition, oracle, leverage, and settlement; each DEX begins with
  independent books and margin, while eligible assets may enable validator-
  governed cross-margin.
- Limit: cross-margin is not automatic and its enabling action is documented as
  irreversible; mutable deployer and validator rules do not establish semantic
  equivalence or cross-venue capital completeness.

### M03 - Kalshi BTC perpetual futures

- Source: Kalshi Help Center, “BTC Perpetual Futures — Contract
  Specifications,” 3 June 2026; observed 15 July 2026.
- Link: <https://help.kalshi.com/en/articles/15357587-btc-perpetual-futures-contract-specifications>
- Supports: product-form convergence between a regulated event-market brand and
  perpetual futures.
- Limit: a mutable product specification does not independently establish
  listing continuity, liquidity, execution quality, or portfolio offsets.

### M04 - Architect compute futures

- Source: Architect Financial Technologies, “Architect Partners with Compute
  Index Provider Ornn to Launch Exchange-Traded Futures on GPU and RAM Prices,”
  21 January 2026.
- Link: <https://architect.co/insights/press/architect-ornn-compute-futures/>
- Supports: announced perpetual futures linked to GPU-rental and DRAM-price
  indexes, pending regulatory approval.
- Additional source: Architect Financial Technologies, “Architect Financial
  Technologies Partners with Compute Desk to Launch Exchange-for-Physical
  Market for GPU Compute,” 8 July 2026,
  <https://architect.co/insights/press/architect-compute-desk-computeconnect/>.
- Limit: announcements establish product intent and intended financial-to-
  physical linkage, not listing approval, current availability, liquidity,
  benchmark quality, or hedge effectiveness.

### M04A - Electricity-forward hedging

- Source: Hendrik Bessembinder and Michael L. Lemmon, “Equilibrium Pricing and
  Optimal Hedging in Electricity Forward Markets,” *Journal of Finance* 57(3),
  June 2002, pp. 1347-1382.
- Link: <https://doi.org/10.1111/1540-6261.00463>
- Supports: nonstorability, demand skewness, production risk, and hedging
  pressure in electricity forwards.
- Limit: GPU compute is only partially analogous to electricity and requires
  separate deliverability, obsolescence, benchmark, and quality modelling.

### M05 - Gnosis Conditional Tokens

- Source: Gnosis, Conditional Tokens contracts and glossary.
- Link at observed commit `eeefca66`:
  <https://github.com/gnosis/conditional-tokens-contracts/blob/eeefca66eb46c800a9aaab88db2064a99026fde5/docs/glossary.rst>
- Supports: onchain condition, outcome collection, position split, merge, and
  redemption primitives.
- Limit: token combinatorics do not establish truthful resolution, legal
  equivalence, or sufficient liquidity. Revision observed 15 July 2026; source
  inspection is not deployed-bytecode identity, audit, liquidity, solvency, or
  correctness evidence.

### M06 - Polymarket negative-risk adapter

- Source: Polymarket, Negative Risk Conditional Tokens Framework Adapter.
- Link at observed commit `f78b35b0`:
  <https://github.com/Polymarket/neg-risk-ctf-adapter/blob/f78b35b0863b4308a431ca307d06f49b2ea65e78/docs/index.md>
- Supports: explicit conversion among mutually exclusive event outcomes and
  capital-efficiency improvements within a declared condition set.
- Limit: “negative risk” conversion relies on correct market grouping and
  resolution; it is not general semantic equivalence. Revision observed 15 July
  2026; source inspection is not deployed-bytecode identity, audit, liquidity,
  solvency, or correctness evidence.

### M07 - Polymarket CTF exchange

- Source: Polymarket, CTF Exchange v2.
- Link at observed commit `ccc05960`:
  <https://github.com/Polymarket/ctf-exchange-v2/tree/ccc0596074f4dfd62c944fbca4de252893b82b4b>
- Supports: an open-source order and settlement surface for outcome tokens.
- Limit: revision observed 15 July 2026; source inspection is not deployed-
  bytecode identity, audit, liquidity, solvency, or correctness evidence.

### M08 - CoW Protocol batch-auction services

- Source: CoW Protocol services.
- Link at observed commit `6b2a4ce9`:
  <https://github.com/cowprotocol/services/tree/6b2a4ce9dcfc5731f3bfd1f68457ed0379488707>
- Supports: intent-based order collection, solver competition, and batch
  settlement as an alternative execution architecture.
- Limit: solver-based token exchange does not solve derivative semantics or
  collateral recognition. Revision observed 15 July 2026; source inspection is
  not deployed-bytecode identity, audit, liquidity, solvency, or correctness
  evidence.

### M09 - CoW flash-loan router

- Source: CoW Protocol flash-loan router.
- Link at observed commit `90b18bca`:
  <https://github.com/cowprotocol/flash-loan-router/tree/90b18bca67a01dab2e55bccbc92e71f0d729b9df>
- Supports: composable atomic liquidity in a bounded transaction context.
- Limit: atomic capital access can amplify failure if validation or downstream
  assumptions are wrong. Revision observed 15 July 2026; source inspection is
  not deployed-bytecode identity, audit, liquidity, solvency, or correctness
  evidence.

### M10 - UMA Optimistic Oracle

- Source: UMA Protocol, Optimistic Oracle v3 developer quickstart.
- Link at observed commit `5c960363`:
  <https://github.com/UMAprotocol/dev-quickstart-oov3/tree/5c9603634bdf24b6dad6bbf85195c74bde22715c>
- Supports: assertion, challenge, and dispute windows as an oracle design
  pattern.
- Limit: optimistic resolution is not appropriate for every price, latency, or
  finality requirement. Revision observed 15 July 2026; source inspection is
  not deployed-bytecode identity, audit, liquidity, solvency, or correctness
  evidence.

## E. Assurance, zero trust, and secure externalization

### S01 - NIST Zero Trust Architecture

- Source: NIST Special Publication 800-207, *Zero Trust Architecture*, 2020.
- Link: <https://csrc.nist.gov/pubs/sp/800/207/final>
- Supports: no implicit trust based on network location or ownership and
  continuous, resource-specific access decisions.
- Limit: zero trust is an access architecture, not a collateral or settlement
  model.

### S02 - IETF RATS architecture

- Source: RFC 9334, *Remote ATtestation procedureS Architecture*, 2023.
- Link: <https://www.rfc-editor.org/rfc/rfc9334.html>
- Supports: separation of evidence, appraisal policy, attestation results, and
  relying-party decisions.
- Limit: an attestation result establishes only the claims and trust roots
  actually appraised; it is not semantic correctness or financial solvency.

### S03 - NIST digital identity session monitoring

- Source: NIST SP 800-63B-4, *Digital Identity Guidelines: Authentication and
  Authenticator Management*, July 2025, section 5.3, “Session Monitoring.”
- Links: <https://doi.org/10.6028/NIST.SP.800-63b-4> and
  <https://pages.nist.gov/800-63-4/sp800-63b/session/>
- Supports: ongoing session risk evaluation, reauthentication, and response to
  changing fraud indicators.
- Limit: identity-session controls do not validate a trade or oracle price.

### S04 - NIST incident-response guidance

- Source: Alexander Nelson, Sanjay Rekhi, Murugiah Souppaya, and Karen Scarfone,
  NIST SP 800-61 Rev. 3, *Incident Response Recommendations and Considerations
  for Cybersecurity Risk Management: A CSF 2.0 Community Profile*, April 2025.
- Link: <https://doi.org/10.6028/NIST.SP.800-61r3>
- Supports: preparation, detection, response, recovery, learning, and evidence
  preservation as an integrated risk process.
- Limit: general guidance does not determine a protocol-specific pause policy.

### S05 - OpenZeppelin TimelockController

- Source: OpenZeppelin Contracts v5.6.1, `TimelockController.sol`, observed at
  commit `5fd1781b1454fd1ef8e722282f86f9293cacf256`.
- Link: <https://github.com/OpenZeppelin/openzeppelin-contracts/blob/5fd1781b1454fd1ef8e722282f86f9293cacf256/contracts/governance/TimelockController.sol>
- Supports: delayed governance execution as a transparent review and reaction
  window.
- Limit: a reusable control primitive is not financial-settlement proof, correct
  governance configuration, or evidence that every externalization path can be
  paused. A timelock can impede urgent response if poorly governed.

### S06 - OpenZeppelin emergency-stop patterns

- Source: OpenZeppelin Contracts v5.6.1, `Pausable.sol`, observed at commit
  `5fd1781b1454fd1ef8e722282f86f9293cacf256`.
- Link: <https://github.com/OpenZeppelin/openzeppelin-contracts/blob/5fd1781b1454fd1ef8e722282f86f9293cacf256/contracts/utils/Pausable.sol>
- Supports: explicit pause states and guarded operations as reusable control
  patterns.
- Limit: a reusable control primitive is not financial-settlement proof, correct
  governance configuration, or evidence that every externalization path can be
  paused. Pause authority also creates governance and availability risk and
  cannot reverse already-final settlement.

### S07 - Reported Ostium incident acknowledgement

- Source: Kyle Baird, “Ostium pauses trading after apparent $18 million vault
  exploit,” *The Block*, 15 July 2026, reporting and quoting an Ostium X post.
- Links: <https://www.theblock.co/post/408450/ostium-pauses-trading-after-apparent-18-million-vault-exploit>
  and the reported original URL
  <https://x.com/Ostium/status/2077412452392652917>.
- Supports: contemporaneous reporting quoted the project as stating that it was
  aware of an OLP-vault issue, had paused all trading, and was investigating.
- Limit: this is reporting of a first-party statement, not a retained first-party
  artifact. The original post was not independently retrievable or retained
  during this review. Neither source establishes final root cause, exact loss,
  recovery, or whether a delay would have prevented harm. The article is a
  developing report and may be superseded.

### S08 - Reported Ostium investigation-update URL

- Source: a URL reported as an Ostium investigation update on 15 July 2026.
- Link: <https://x.com/Ostium/status/2077438120354603396>
- Supports: no distinct substantive claim in this index until the exact official
  content, timestamp, retrieval date, and content hash or archived capture are
  recovered.
- Limit: an inaccessible social URL cannot independently support an update
  claim; subsequent findings may also supersede any recovered content.

### S09 - Blockaid preliminary Ostium attribution

- Source: Blockaid preliminary incident analysis, 15 July 2026.
- Link: <https://x.com/blockaid_/status/2077405527428989363>
- Supports: Blockaid's preliminary claim that a registered forwarder and
  prepared or future-dated authorized oracle reports were involved.
- Limit: no reviewed official postmortem confirms the report-preparation
  mechanism, signer compromise, exact loss, or final root cause. Do not
  paraphrase the allegation as the router accepting a request timestamp that
  was still in the future.

### S10 - Ostium incident transaction

- Source: Arbiscan transaction
  `0x359f8c05b86a4409d60cfba02084334313fd94b19f74a294fb7fc4ea7d4870e0`,
  successful at 14:18:48 UTC on 15 July 2026.
- Link: <https://arbiscan.io/tx/0x359f8c05b86a4409d60cfba02084334313fd94b19f74a294fb7fc4ea7d4870e0>
- Supports: direct transaction and event-log evidence for the observed same-
  transaction execution sequence.
- Limit: the transaction establishes executed state transitions, not attacker
  identity, upstream compromise, intent, or complete root cause.

### S11 - Ostium current protocol-flow documentation

- Source: Ostium, “How Ostium Works,” current mutable documentation observed 15
  July 2026.
- Link: <https://docs.ostium.com/protocol/how-ostium-works>
- Supports: Ostium's current stated use of Chainlink and Stork oracle inputs,
  Chainlink and Gelato automation, immediate onchain trader-PnL payment, and
  daily reconciliation with an offchain hedge.
- Limit: mutable provider documentation may postdate the incident, does not
  prove incident-time deployed configuration, and does not independently
  validate provider independence or solvency claims.

### S12 - Ostium withdrawal documentation

- Source: Ostium, “How to Withdraw,” current mutable documentation observed 15
  July 2026.
- Links: <https://docs.ostium.com/vault/getting-started/withdraw> and the legacy
  GitBook page observed 15 July 2026,
  <https://ostium-labs.gitbook.io/ostium-docs/vault/withdraw>.
- Supports: current documentation describes a dynamic request-and-settle LP
  withdrawal flow, typically two to three days.
- Limit: legacy Ostium GitBook documentation described a fixed 24-48-hour flow.
  Neither mutable page is a frozen incident-time specification, and LP
  withdrawal delay does not govern immediate trader-profit payout.

### S13 - Ostium pinned public close and transfer paths

- Sources at commit `8390ce497f68fb128900840e0ec30683afa945d3`:
  - <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/lib/TradingCallbacksLib.sol#L620-L653>
  - <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/OstiumVault.sol#L731-L754>
- Supports: inspection of one public source revision's profitable-close and
  vault-transfer paths.
- Limit: no claim is made that this commit equals incident-time deployed
  bytecode or contains the root cause.

### S14 - Ostium pinned signer, upkeep, and timestamp paths

- Sources at commit `8390ce497f68fb128900840e0ec30683afa945d3`:
  - <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/OstiumVerifier.sol#L51-L64>
  - <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/OstiumPrivatePriceUpKeep.sol#L77-L121>
  - <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/OstiumPriceRouter.sol#L70-L87>
- Supports: inspection of one revision's authorization, binding, and freshness
  checks.
- Limit: field checks do not prove upstream data integrity or complete system
  safety.

### S15 - Nomad bridge incident analyses

- Sources:
  - Nomad first-party RCA:
    <https://medium.com/nomad-xyz-blog/nomad-bridge-hack-root-cause-analysis-875ad2e5aacd>
  - Mandiant: <https://cloud.google.com/blog/topics/threat-intelligence/dissecting-nomad-bridge-hack/>
  - Coinbase: <https://medium.com/the-coinbase-blog/nomad-bridge-incident-analysis-899b425b0f34>
- Supports: how an initialization or validation defect can turn a bridge into a
  copyable, machine-speed loss path.
- Limit: the first-party RCA is supplemented by independent analysis; Nomad's
  bridge architecture and 2022 incident do not generalize directly to Statebook
  or Ostium.

### S16 - Bybit 2025 incident disclosures

- Sources:
  - Bybit incident notice, 21 February 2025:
    <https://announcements.bybit.com/en/article/incident-update---eth-cold-wallet-incident-blt292c0454d26e9140/>
  - Bybit timeline, 3 March 2025:
    <https://www.bybit.com/en/learn/this-week-in-bybit/bybit-security-incident-timeline>
  - FBI attribution, 26 February 2025:
    <https://www.ic3.gov/PSA/2025/PSA250226>
- Supports: operational evidence that interface, signing, and supply-chain
  compromise can bypass assumptions associated with cold-wallet workflows.
- Limit: Bybit's chronology is first-party; the FBI source supports attribution
  and approximate loss, not a complete technical root-cause analysis. None of
  the sources implies that mandatory delay alone solves signing compromise.

### S17 - Verichains preliminary Bybit forensic report

- Source: Thanh Nguyen / Verichains, *Bybit Incident Investigation: Preliminary
  Report*, version 1.0, 24 February 2025.
- Link: <https://github.com/verichains/public-audit-reports/blob/ba7ff5154659cc0f121f59371e419f7e5d6a71e4/Bybit%20Incident%20Investigation%20-%20Preliminary%20Report%20v1.0%20(for%20public%20release).pdf>
- Supports: a preliminary account of a malicious Safe UI flow and targeted
  signing-process compromise.
- Limit: Verichains, not Safe, authored the report; preliminary findings do not
  establish a universal custody-incident model.

## F. AI, compute, energy, and macroeconomic context

### A01 - IEA energy and AI outlook

- Source: International Energy Agency, *Key Questions on Energy and AI*, 16
  April 2026.
- Link: <https://www.iea.org/reports/key-questions-on-energy-and-ai>
- Supports: the IEA central projection increases global data-centre electricity
  demand from about 485 TWh in 2025 to about 950 TWh in 2030, while identifying
  grid, chip, equipment, capital, and social-acceptance constraints.
- Limit: a conditional projection, not an observed outcome, forecast certainty,
  or tradable oracle.

### A02 - IMF July 2026 World Economic Outlook Update

- Source: International Monetary Fund, *World Economic Outlook Update: Global
  Economy in Crosscurrents of War and Technology*, 8 July 2026.
- Link: <https://www.imf.org/-/media/files/publications/weo/2026/update/july/english/text.pdf>
- Supports: opposing energy/geopolitical and technology-investment forces,
  uneven country exposure, and a 3.0 percent 2026 and 3.4 percent 2027 global
  growth baseline at publication.
- Limit: the baseline can change and is not a product forecast.

### A03 - World Bank June 2026 Global Economic Prospects

- Source: World Bank Prospects Group, *Global Economic Prospects — June 2026*,
  16 June 2026.
- Link: <https://thedocs.worldbank.org/en/doc/2b672b3b0415d6b66c45b66579db4ef5-0050012026/global-economic-prospects-june-2026>
- Supports: a slowing global-growth baseline, energy and geopolitical stress,
  debt constraints, AI investment, productivity uncertainty, and uneven
  diffusion.
- Limit: macro projections do not validate a Statebook demand forecast.

### A04 - World Bank AI foundations

- Source: World Bank, *Digital Progress and Trends Report 2025: Strengthening AI
  Foundations*, published 9 January 2026.
- Link: <https://doi.org/10.1596/978-1-4648-2264-3>
- Supports: cross-country differences in four AI foundations: connectivity,
  compute, context, and competency.
- Limit: country-level foundations do not map directly to contract liquidity.

### A04A - FERC large-load integration action

- Source: Federal Energy Regulatory Commission, “FERC Launches Aggressive
  Targeted Action to Speed Large Load Integration,” 18 June 2026.
- Link: <https://www.ferc.gov/news-events/news/ferc-launches-aggressive-targeted-action-speed-large-load-integration>
- Supports: a public regulatory and grid-governance response to rapidly growing
  large-load interconnection demand.
- Limit: the action does not prove AI-specific market demand, forecast power
  prices, or establish a tradable reference methodology.

### A05 - OECD AI productivity scenarios

- Source: Francesco Filippucci, Peter Gal, Katharina Laengle, and Matthias
  Schief, “Macroeconomic Productivity Gains from Artificial Intelligence in G7
  Economies,” *OECD Artificial Intelligence Papers* No. 41, 30 June 2025.
- Link: <https://doi.org/10.1787/a5319ab5-en>
- Supports: across ten-year scenarios, estimated annual aggregate labour-
  productivity growth attributable to AI ranges from roughly 0.4 to 1.3
  percentage points in highly exposed G7 economies, with lower estimates
  elsewhere.
- Limit: scenario ranges are not realized effects, global averages, or price
  oracles.

### A05A - Firm-level generative-AI productivity evidence

- Source: Erik Brynjolfsson, Danielle Li, and Lindsey R. Raymond, “Generative AI
  at Work,” *Quarterly Journal of Economics* 140(2), 2025, pp. 889-942.
- Link: <https://doi.org/10.1093/qje/qjae044>
- Supports: an average productivity increase near 15 percent in one 5,172-agent
  customer-support setting, concentrated among less-experienced workers.
- Limit: one firm, occupation, and tool; not aggregate GDP, universal labour
  substitution, or a forecast.

### A05B - Task-based macroeconomic AI scenario

- Source: Daron Acemoglu, “The Simple Macroeconomics of AI,” *Economic Policy*,
  2024.
- Link: <https://doi.org/10.1093/epolic/eiae042>
- Supports: a task-based framework for disciplined ten-year productivity and
  distribution scenarios.
- Limit: outcomes are assumption-sensitive and not observed effects.

### A06 - Stanford AI Index 2026

- Source: AI Index Steering Committee, Stanford Institute for Human-Centered AI,
  *The 2026 AI Index Report*, 13 April 2026.
- Links:
  - <https://hai.stanford.edu/ai-index/2026-ai-index-report>
  - <https://hai.stanford.edu/assets/files/ai_index_report_2026_chapter_4_economy.pdf>
- Supports: current indicators for investment, adoption, cost, labour, models,
  and economic diffusion.
- Limit: compiled indicators have differing methods and lags; they are not one
  causal forecast.

### A07 - BIS artificial intelligence and the economy

- Source: Bank for International Settlements, *Artificial Intelligence and the
  Economy: Implications for Central Banks*, Annual Economic Report 2024,
  Chapter III.
- Link: <https://www.bis.org/publ/arpdf/ar2024e3.htm>
- Supports: productivity, inflation, labour-market, and central-bank
  implications of AI adoption.
- Limit: macroeconomic analysis does not determine exchange architecture.

### A08 - BIS AI data governance

- Source: Juan Carlos Crisanto, Adrien Currat, Johannes Ehrentraud, and Wenguang
  Wu, “In Data We Trust? Emerging Policy and Supervisory Approaches to AI Data
  Use in Financial Services,” *FSI Insights* No. 73, 26 March 2026.
- Link: <https://www.bis.org/fsi/publ/insights73.htm>
- Supports: data privacy, quality, security, third-party dependency, and market-
  concentration concerns in financial-services AI use.
- Limit: author views and supervisory analysis, not calibrated Statebook risk
  weights.

### A09 - FSB AI vulnerabilities in finance

- Source: Financial Stability Board, *Monitoring Adoption of Artificial
  Intelligence and Related Vulnerabilities in the Financial Sector*, 10 October
  2025.
- Link: <https://www.fsb.org/2025/10/monitoring-adoption-of-artificial-intelligence-and-related-vulnerabilities-in-the-financial-sector/>
- Supports: third-party concentration, market correlation, cyber risk, model
  risk, and governance vulnerabilities.
- Limit: monitoring categories are not calibrated Statebook risk weights.

### A10 - BIS tokenisation and monetary-system trust

- Source: Bank for International Settlements, “Anchoring Trust in Money:
  Innovation Beyond Stablecoins,” *Annual Economic Report 2026*, Chapter III,
  23 June 2026.
- Link: <https://www.bis.org/publ/arpdf/ar2026e3.htm>
- Supports: trust, governance, tokenisation, composability, and monetary-system
  integrity as inseparable design concerns.
- Limit: the institutional model is not equivalent to permissionless venue
  architecture.

## G. Thesis attribution and media

### X01 - “AWS of finance” attribution

- Source: Ben Weiss and Leo Schwartz, “How a Harvard Grad Helped Make
  Hyperliquid the Biggest New Player in Crypto—with Just 11 People and No
  Venture Funding,” *Fortune*, 12 January 2026.
- Link: <https://fortune.com/2026/01/12/hyperliquid-jeff-yan-defi-perpetuals-perps-exchange-defi/>
- Supports: Fortune reports that Yan views Hyperliquid as the “AWS of financial
  infrastructure”; this supports attribution only, not independent validation.
- Limit: a founder analogy is a strategy claim, not neutral proof of convergence
  or infrastructure quality. Do not format the phrase as a direct Yan quotation
  unless a primary transcript or recording contains it.

### X02 - Long-form Jeff Yan interview

- Source: VALR podcast interview with Jeff Yan, 9 July 2026.
- Link: <https://blog.valr.com/blog/cedefi-valrs-integration-of-hyperliquid-ft-jeff-yan>
- Supports: contemporary operator commentary on integration and market
  infrastructure.
- Limit: first-party promotional media, not implementation, liquidity, or
  benchmark evidence.

### X03 - Original Statebook visual system

- Source: the SVG files under `docs/media/statebook/` created for this
  publication.
- Supports: original diagrams and satirical teaching artifacts that explain the
  architecture, completeness distinctions, and security tradeoff.
- Limit: a diagram or meme is explanatory media, not evidence.

## H. Repository-grounded implementation lineage

### R01 - Statebook boundary specification

- Source: `docs/integrations/statebook_terminal_payoff_and_trust_settlement.md`.
- Supports: the governing docs-only Statebook model, invariants, horizon
  scenarios, assurance-adjusted settlement policy, and explicit nonclaims.
- Limit: it is `Level0DesignNote` material, not runtime code or validation.

### R02 - HSAI claim envelopes

- Source: `crates/hsai-claim-envelope/src/lib.rs` and its governing phase docs.
- Supports: a local implemented algebra for maturity, predicates, trust roots,
  provenance, conjunction, and acceptance policy.
- Limit: HSAI claim envelopes do not verify market semantics, prices, solvency,
  legality, or settlement.

### R03 - Benchmark Semantic IR and evidence boundaries

- Source: `crates/zkbench-core/src/dsl/ir.rs`,
  `crates/zkbench-core/src/evidence/mod.rs`, and governing architecture docs.
- Supports: repository precedent for separating source syntax, normalized
  semantics, execution outcomes, Evidence Records, and Claim Boundaries.
- Limit: the benchmark IR is not a financial-contract IR and must not be reused
  by name alone.

### R04 - HSAI admission boundary

- Source: `crates/hsai-agent-admission/src/lib.rs` at local committed revision
  `b4b644cd96d9b70eb21ff6681a0014245773cd0f`, inspected 15 July 2026.
- Supports: repository precedent for explicit action proposals, evidence gates,
  fail-closed admission, replay protection, and non-authority claims.
- Limit: the revision was not present on the configured GitHub remote when
  checked, the current dirty working tree is excluded, admission metadata is not
  settlement authority, and the current Statebook slice does not mutate this
  crate.

## Synthesis rules used by the whitepaper and PRD

1. **Semantic equivalence is narrower than shared reference.** Reference,
   observation window, maturity, comparator, settlement source, currency,
   rounding, dispute, legal, and path-dependence terms all matter.
2. **Semantic, payoff, execution, capital, settlement, assurance, and recovery
   completeness are separate verdicts.** A pause or challenge window is not
   recovery unless all externalization paths can stop, in-flight state can
   reconcile, evidence survives, and reopening cannot duplicate or orphan
   liabilities.
3. **A perpetual is a continuing hedge profile, not silently a terminal claim.**
4. **Atomic settlement and delayed externalization solve different problems.**
   Atomic linked exchange can reduce principal risk; a challenge window can
   reduce irreversible propagation after suspicious state transitions.
5. **Assurance determines release permission and exposure, not truth.** Hard
   gates decide whether release is possible, loss budgets decide how much,
   delay tiers decide when, and a challenge queue decides what happens next.
6. **No evidence class substitutes for another.** A signature is not semantic
   correctness; source code is not deployed-state proof; documentation is not
   solvency; a scenario is not a forecast; a meme is not evidence.
7. **All external facts are observation-time facts.** Venue designs,
   regulations, incidents, and macro baselines can change after 15 July 2026.

## Nonclaims

This index does not claim exhaustive literature coverage, legal advice,
investment advice, independent incident forensics, empirical calibration,
production readiness, semantic correctness, full security, benchmark evidence,
or authorization to implement exchange, custody, pause, routing, oracle,
margin, liquidation, signing, or settlement powers.
