# Methodology notes

Running record of assumptions, sources and parameters. Every change is logged here with its effect.

Written for: me, returning to the project later, and anyone checking the work.

## Scope

- Model: AM peak four-step model (trip generation, trip distribution, mode choice, assignment).
- Period: AM peak hour, 08:00–09:00, weekday.
- Coordinate system: EPSG:27700 (British National Grid) for all distances.

## Phase 0: toy model

_Notebook built: `notebooks/toy_model.ipynb`. Four zones, made-up numbers, checked by hand. Every decision in it is referenced to TAG below._

Level 0 of the notebook (real places, then zones, nodes and links, and what each step leaves out) has no model numbers and adds no TAG decisions. It explains the simplifications behind the rest of the notebook.

The notebook is built in seven levels, each adding one idea: 0 real world to network (Steps 1 to 6), 1 work trips with travel time only (Parts A to E), 2 a second trip purpose (F), 3 generalised cost (G), 4 mode choice (H to I), 5 assignment (J to K), 6 validation (L to N). Floyd–Warshall sits in an Appendix. Part A works the shortest times out by hand and the Appendix checks them with the algorithm.

## Assumptions log

| Date | Item | Value / choice | Source | Effect of change |
|------|------|----------------|--------|------------------|
| | | | | |

## TAG references by decision

Each modelling decision in `notebooks/toy_model.ipynb` is listed with the TAG unit and paragraph it follows. "Section" numbers were located by searching the text of the gov.uk copies, so check them against the current published version before citing them externally.

Status key:
- **Matches TAG**: the value or rule is the one TAG gives.
- **Within TAG range**: a value TAG gives as indicative, and it falls inside the range.
- **Outside TAG range**: TAG gives an indicative range and the value falls outside it. Change it or justify it.
- **Not in TAG**: our own choice, or TAG does not specify it. Say so in the write-up.
- **Placeholder**: a made-up value, to be replaced with a sourced value.
- **Not checked**: no TAG reference found yet.

Sources checked: [TAG M2.1 Variable Demand Modelling](https://assets.publishing.service.gov.uk/media/664f48c8b7249a4c6e9d3a84/tag-m2-1-variable-demand-modelling.pdf), [TAG M2.2 Base Year Demand Matrix Development (May 2020)](https://assets.publishing.service.gov.uk/media/5fbfbd998fa8f559e32b4d25/tag-m2-2-base-year-matrix.pdf), [TAG M3.1 Highway Assignment Modelling](https://assets.publishing.service.gov.uk/media/6a033d074fb0713aa63ea802/tag-m3-1-highway-assignment-modelling.pdf), [TAG M3.2 Public Transport Assignment Modelling](https://assets.publishing.service.gov.uk/media/664f4a03f34f9b5a56adcd6d/tag-m3-2-public-transport-assignment.pdf). Last checked 2026-11-19. Version dates to be confirmed.

| Part | Decision | Value in notebook | TAG reference | Status | Note |
|------|----------|-------------------|---------------|--------|------|
| A | Links are two-way, same time in both directions | Assumed | M3.1 section 2.4 (network structure) | Not checked | Simplification. Real networks have directional links. |
| A | Free-flow times | 8 to 20 min | M3.1 section 2.4; Appendix E (speed/flow) | Placeholder | Replace from network data. |
| A | Link capacities | 100 to 250 veh/h | M3.1 section 2.4; Appendix E | Placeholder | Raised from 40 to 100 veh/h once the other-purpose trips were assigned, because the original capacities gave v/c above 2.5. Replace from network data. |
| Appendix | Shortest times by Floyd–Warshall | Algorithm | None (standard algorithm) | Not in TAG | Any correct shortest-path method gives the same result. Part A works the six pairs out by hand; the Appendix asserts the algorithm agrees. |
| A | Intrazonal cost = half the nearest zone's cost | nearest ÷ 2 | M2.2 section 5.2.28; M2.1 section 2.4.4 | Matches TAG | TAG also says to cap for large zones at mean trip distance. Not needed at four zones. |
| B | HBW productions and attractions | 400/300/200/100 trips/h; attractions scaled to match | Not checked | Placeholder | Trip generation is outside the toy model. Source from the plan's data. |
| C | Deterrence form, exponential | exp(−βc) | M2.1 section 4.9.14 (logit or exponential form) | Matches TAG | |
| C | HBW deterrence β | 0.05 per min | M2.2 section 5.2.31 (calibrate deterrence against observed trip-length data) | Placeholder | Calibrate in Phase 3. |
| E | HBW distribution is doubly constrained (Furness) | Furness, tolerance 0.1% (relative change in totals) | M2.1 section 4.9.12 (doubly constrained for commuting) | Matches TAG (model type) | The 0.1% tolerance is our choice. TAG's 0.1% in M3.1 Table 4 is for assignment convergence. |
| F | HBO distribution is singly constrained | Attraction weights, one pass | M2.1 section 4.9.12 (singly constrained for other purposes) | Matches TAG | |
| F | HBO deterrence β | 0.10 per min | M2.2 section 5.2.31 | Placeholder | Calibrate in Phase 3. |
| G | Value of time | £12 per hour | M3.1 section 2.8.7, PDF p. 20. Method: TAG unit A1-3. Values: data book Table A1.3.2 | Placeholder | Choose a basis and year from Table A1.3.2, then replace. |
| G | Money cost: car £1.50 per trip | £1.50 | M3.2 section 3.3.3 (fares converted to time by value of time) | Placeholder | Replace with sourced parking and fuel cost. |
| G | Money cost: bus fare £1.80 | £1.80 | M3.2 section 3.3.3 | Placeholder | Replace with sourced fare. |
| G | Walk access weight | 2.0 | M3.2 Table 1 (walk access 1.5 to 2.0) | Within TAG range | At the top of the range. |
| G | Wait weight (bus) | 1.0 | M3.2 Table 1 (waiting time: bus 1) | Matches TAG | Changed from 2.0, which was outside the range. Checked 2026-11-23: TAG lists 1 for interurban bus. |
| G | Bus in-vehicle time factor vs car | 1.1 | M3.2 Table 1 (in-vehicle time factor 0.7 to 1.1) | Within TAG range | Changed from 1.2, which was outside the range. Checked 2026-11-23 against the local M3.2 Table 1 (range 0.7 to 1.1). |
| G | Walk and wait times (3 min, 4 min) | Made up | M3.2 section 3.2 (access and waiting time) | Placeholder | Source from network or survey data. |
| H | Zero-car share of HBW trips | 30% | Not checked (plan cites Census TS045) | Placeholder | Source from Census. |
| H | Zero-car share of HBO trips | 30% (same as HBW until sourced) | Not checked | Placeholder | Source from Census, by trip purpose. |
| I | Logit sensitivity λ | 0.1 per min | M2.1 section 4.9.14 (logit form); M2.1 section 4.5.10 (λ estimation); M2.1 Table 3 (section 5.6.16, destination choice λ) | Placeholder | Table 3 is for destination choice, not mode choice. Check units against TAG. |
| I | Bus penalty (alternative-specific constant) | Fitted to 70% car share | Not checked | Not in TAG | Calibration method is ours. Target share is a placeholder. Work and other trips share one constant. |
| J | Car occupancy | 1.1 persons per car | M2.2 section 5.4.4 (car occupancy factors; M2.1 gives advice) | Placeholder | Data book Table A1.3.3 gives 1.11 for work trips (weekday average, 2010). |
| J | BPR congestion function, α = 0.15, n = 4 | BPR form | M3.1 Appendix E (TAG uses its own speed/flow relationships) | Not in TAG | The BPR form is not the one TAG specifies. Use Appendix E, or justify BPR. |
| K | Method of successive averages, stop at gap below 0.1% | Gap tolerance 0.1% | M3.1 section 3.4.17, Table 4 (base model convergence below 0.1%) | Matches TAG | |
| L | Link flow check: GEH below 5 on at least 85% of links | GEH < 5, 85% | M3.1 sections 3.3.10 to 3.3.14, Table 2 (GEH < 5, more than 85% of cases) | Matches TAG | TAG also accepts the absolute or percentage criteria. We use GEH only, which is stricter on that test. Current result: 80% of links pass, so the check fails. Kept as a finding, not tuned to pass (notebook Part L). |
| M | Screenline within ±5% | ±5% | M2.2 section 6.2.23 (highway ±5%; public transport ±15%) | Matches TAG | |
| M | Journey times within 15% (or 1 min if higher), on 85% of routes | 15% or 1 min; 85% | M3.1 section 3.3.15, Table 3 | Matches TAG | |
| All | Counts and observed journey times | Made up | Not applicable | Placeholder | Source from DfT counts and journey-time data. |

## TAG quotes

The notebook carries a one-line TAG reference per decision and points here for the wording. Each quote below is copied from the gov.uk PDF listed under "Sources checked". "PDF p." is the page of that PDF file, which may differ from the printed page number.

### Part A: network and intra-zonal cost

**M3.1 section 2.4, network structure.** Listed on contents page 5. The section text has not been checked yet, so the free-flow times and capacities are placeholders.

**M2.2 section 5.2.28, PDF p. 22.**
> "A measure of intra-zonal costs should be estimated. It is common to assume a value based on the cost to adjacent zones. Some models for example adopt half the lowest inter-zonal cost, often imposing a cap that maintains costs at or below mean trip distances for large zones."

This is the rule the notebook uses (half the nearest zone's cost). The cap matters for large zones, which four toy zones do not need.

**M2.1 section 2.4.4, PDF p. 17.**
> "for large zones it is important that the average intrazonal costs are as realistic as possible."

Zone size matters for trips inside a zone, which is why the notebook shows zone areas.

### Part C: deterrence

**M2.1 section 4.9.14, PDF p. 52.**
> "It is expected that the model form will generally be logit."

TAG expects a logit model form. The exponential the notebook uses is one of the deterrence functions TAG describes in Appendix C.

**M2.2 section 5.2.31, PDF p. 23.**
> "For the calibration of the deterrence function, it is usually necessary to use a representation of TCD produced from internal zones only to test the model fit."

The deterrence function should be calibrated against observed trip-length data. Both β values are placeholders until that data is in the model. The same quote covers the trip-length check in Part E.

### Parts E and F: constraints

**M2.1 section 4.9.12, PDF p. 51.**
> "doubly constrained models should be used for commuting and education."

Work trips are doubly constrained in the notebook, which matches TAG.

**M2.1 section 4.9.12, PDF p. 51.**
> "Other purposes such as shopping, social and leisure trips are typically modelled as singly production-end constrained."

Other trips are singly constrained, which matches TAG. TAG describes the attraction side as trip-end factors; the notebook's relative weights are a simpler version.

The 0.1% Furness tolerance is ours. The 0.1% in M3.1 Table 4 is for assignment convergence, not for balancing.

### Part G: generalised cost

**M3.2 section 2.7.5, PDF p. 18.**
> "In-VehicleTime * in-vehicle time factor + Fare / Value of Time +"

The notebook uses this form, with walk and wait weights and a bus in-vehicle factor.

**M3.2 Table 1, PDF p. 20**, "Recommended Generalised Cost Weights and Penalties". Walk access 1.5 to 2.0: ours is 2.0, in range. Bus waiting 1: ours is 1.0, in range. In-vehicle time factor 0.7 to 1.1: ours is 1.1, at the top of the range. The first version of the notebook used 2.0 for waiting and 1.2 for in-vehicle time, both outside the range. The table is hard to read in the extracted text, so check these against the PDF.

**M3.2 section 3.3.3, PDF p. 23.**
> "Fares are converted to time using a value of time parameter in the assignment process."

Fares are turned into minutes by dividing by value of time, as the notebook does.

**M3.1 section 2.8.7, PDF p. 20.**
> "Values of vehicle operating cost and value of time should be derived from TAG unit A1.3 for the base year and for forecasting assignments without amendment."

The method comes from TAG unit A1-3 and the values from the data book, Table A1.3.2. That table gives values by year, mode and purpose on different cost bases, so one needs choosing. The £12 per hour is a placeholder until then.

### Parts H and I: mode choice

**M2.1 section 4.2, PDF p. 34.**
> "Most variable demand models use some form of "hierarchical logit" formulation (introduced in section 4.2)"

The notebook's mode choice is a single logit between car and bus, a simplified version of the hierarchical logit TAG describes.

**M2.1 section 4.5.10, PDF p. 42.**
> "lambda values should be estimated (calibrated) from that data"

λ should be estimated from data, not guessed. The 0.1 per minute is a placeholder.

**M2.1 Table 3, PDF p. 60**, "Illustrative Destination Choice Lambda Parameters". These are destination-choice values, not mode-choice values, so they do not set the notebook's λ.

Splitting by car availability is our segmentation choice. TAG's segmentation advice is in M2.1, still to be located.

### Parts J and K: assignment

**M2.2 section 5.4.4, PDF p. 28.**
> "Car occupancy is generally expected to vary by factors such as trip purpose, travel time, trip distance, and area type."

The occupancy of 1.1 is a placeholder. The data book, Table A1.3.3, gives 1.11 for work trips (weekday average, 2010 values). TAG unit M2.1 gives the advice on occupancy factors.

**M3.1 section 2.9, PDF p. 23.**
> "The speed/flow relationships recommended for use in highway assignment models are specified in Appendix E:."

BPR is not the form TAG specifies. The α = 0.15 and n = 4 are our choice, so either use Appendix E or justify BPR.

**M3.1 Table 4, PDF p. 37.**
> "Less than 0.1% or at least stable with convergence fully documented and all other criteria met"

The notebook's stopping rule (gap below 0.1%) matches TAG's base-model convergence value.

**M3.1 section 3.4, PDF p. 34.**
> "some methods such as the Method of Successive Averages (MSA) force it to happen, without there necessarily being convergence to a solution."

Stable flows alone do not show convergence. The gap test is what shows it, which is why the notebook uses it.

### Parts L to N: validation

**M3.1 section 3.3.11, PDF p. 31.**
> "flows that meet either criterion should be regarded as satisfactory."

TAG accepts a link flow that meets either GEH or the absolute and percentage criteria. The notebook uses GEH only, which is stricter.

**M3.1 Table 2, PDF p. 32.**
> "GEH < 5 for individual flows"

The guideline is that more than 85% of cases meet it, which matches the rule in the notebook.

**M2.2 section 6.2.23, PDF p. 34.**
> "TAG units M3.1 and M3.2 set out flow criteria at screenline level for highway (i.e. ±5%) and public transport (i.e. ±15%) matrices, respectively."

The screenline test uses the highway ±5%, which matches TAG.

**M3.1 Table 3, PDF p. 33.**
> "Modelled times along routes should be within 15% of surveyed times (or 1 minute, if higher than 15%)"

The journey-time rule matches TAG Table 3: more than 85% of routes.
