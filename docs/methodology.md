# Methodology notes

Running record of assumptions, sources and parameters. Every change is logged here with its effect.

Written for: me, returning to the project later, and anyone checking the work.

## Scope

- Model: AM peak four-step model (trip generation, trip distribution, mode choice, assignment).
- Period: AM peak hour, 08:00–09:00, weekday.
- Coordinate system: EPSG:27700 (British National Grid) for all distances.

## Phase 0: toy model

_Notebook built: `notebooks/toy_model.ipynb`. Four zones, made-up numbers, checked by hand. Every decision in it is referenced to TAG below._

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
| A | Free-flow times and link capacities | 8 to 20 min; 40 to 100 veh/h | M3.1 section 2.4; Appendix E (speed/flow) | Placeholder | Capacities are far below real road capacities. Replace from network data. |
| A | Shortest times by Floyd–Warshall | Algorithm | None (standard algorithm) | Not in TAG | Any correct shortest-path method gives the same result. |
| B | HBW productions and attractions | 400/300/200/100 trips/h; attractions scaled to match | Not checked | Placeholder | Trip generation is outside the toy model. Source from the plan's data. |
| C | Deterrence form, exponential | exp(−βc) | M2.1 section 4.9.14 (logit or exponential form) | Matches TAG | |
| C | HBW deterrence β | 0.05 per min | M2.2 section 5.2.31 (calibrate deterrence against observed trip-length data) | Placeholder | Calibrate in Phase 3. |
| C | Intrazonal cost = half the nearest zone's cost | nearest ÷ 2 | M2.2 section 5.2.28; M2.1 section 2.4.4 | Matches TAG | TAG also says to cap for large zones at mean trip distance. Not needed at four zones. |
| D | HBW distribution is doubly constrained (Furness) | Furness, tolerance 0.1% (relative change in totals) | M2.1 section 4.9.12 (doubly constrained for commuting) | Matches TAG (model type) | The 0.1% tolerance is our choice. TAG's 0.1% in M3.1 Table 4 is for assignment convergence. |
| F | HBO distribution is singly constrained | Attraction weights, one pass | M2.1 section 4.9.12 (singly constrained for other purposes) | Matches TAG | |
| G | HBO deterrence β | 0.10 per min | M2.2 section 5.2.31 | Placeholder | Calibrate in Phase 3. |
| H | Zero-car share of HBW trips | 30% | Not checked (plan cites Census TS045) | Placeholder | Source from Census. |
| I | Value of time | £12 per hour | M3.1 section 2.8.7 (values from TAG Data Book) | Placeholder | Replace with TAG Data Book value. |
| I | Money cost: car £1.50 per trip | £1.50 | M3.2 section 3.3.3 (fares converted to time by value of time) | Placeholder | Replace with sourced parking and fuel cost. |
| I | Money cost: bus fare £1.80 | £1.80 | M3.2 section 3.3.3 | Placeholder | Replace with sourced fare. |
| I | Walk access weight | 2.0 | M3.2 Table 1 (walk access 1.5 to 2.0) | Within TAG range | At the top of the range. |
| I | Wait weight (bus) | 2.0 | M3.2 Table 1 (waiting time: bus 1; tram and light rail 1 to 1.4) | Outside TAG range | Change to a value in range, or justify. |
| I | Bus in-vehicle time factor vs car | 1.2 | M3.2 Table 1 (in-vehicle time factor 0.7 to 1.1, as read from the extracted table) | Outside TAG range | Check the table layout, then change or justify. |
| I | Walk and wait times (3 min, 4 min) | Made up | M3.2 section 3.2 (access and waiting time) | Placeholder | Source from network or survey data. |
| J | Logit sensitivity λ | 0.1 per min | M2.1 section 4.9.14 (logit form); M2.1 section 4.5.10 (λ estimation); M2.1 Table 3 (section 5.6.16, destination choice λ) | Placeholder | Table 3 is for destination choice, not mode choice. Check units against TAG. |
| J | Bus alternative-specific constant | Calibrated to 70% car share | Not checked | Not in TAG | Calibration method is ours. Target share is a placeholder. |
| K | Car occupancy | 1.1 persons per car | M2.2 section 5.4.4 (car occupancy factors; M2.1 gives advice) | Placeholder | Take the value from the TAG Data Book. |
| K | BPR congestion function, α = 0.15, β = 4 | BPR form | M3.1 Appendix E (TAG uses its own speed/flow relationships) | Not in TAG | The BPR form is not the one TAG specifies. Use Appendix E, or justify BPR. |
| L | Method of successive averages, stop at relative gap below 0.1% | Gap tolerance 0.1% | M3.1 section 3.4.17, Table 4 (base model convergence below 0.1%) | Matches TAG | |
| M | Link flow check: GEH below 5 on at least 85% of links | GEH < 5, 85% | M3.1 sections 3.3.10 to 3.3.14, Table 2 (GEH < 5, more than 85% of cases) | Matches TAG | TAG also accepts the absolute or percentage criteria. We use GEH only, which is stricter on that test. |
| N | Screenline within ±5% | ±5% | M2.2 section 6.2.23 (highway ±5%; public transport ±15%) | Matches TAG | |
| N | Journey times within 15% (or 1 min if higher), on 85% of routes | 15% or 1 min; 85% | M3.1 section 3.3.15, Table 3 | Matches TAG | |
| All | Counts and observed journey times | Made up | Not applicable | Placeholder | Source from DfT counts and journey-time data. |
