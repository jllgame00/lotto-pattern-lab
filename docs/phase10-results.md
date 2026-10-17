# Phase10 - Number-space neighborhood and range-density results



**H9: TESTED / INCONCLUSIVE.** Complete-search IID and constrained-null comparisons found no corrected spatial structure. Development-frozen later evaluation did not establish superiority. Numerical adjacency is not physical adjacency in the lottery machine. No predictive/profitability claim is made.



Actual data: canonical draws1..1245, ending2026-10-10. No draw1246 result was retrieved, searched for, inspected, imported or evaluated. All25 Phase5-9 prospective files were inventoried before work and remain protected. No commit or push.



## Protocol and exact search space



The [predeclared protocol](superpowers/plans/2026-10-17-phase10.md) fixes windows10/26/52, widths3/5/7/9, four primary kernels and descriptive box radii1..4. Own, neighbor-only and smoothed signals are separated. Every score uses completed draws strictly before its target, finite1..45 boundaries and no wrapping.



| range_density_cells | kernel_cells | zone_endpoint_cells | zone_movement_metrics | spacing_cells | motif_universe | range_configurations | primary_kernel_configurations | kernel_signal_configurations | families |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 584000 | 2463750 | 14600 | 144 | 83215 | 1086008 | 12 | 12 | 45 | 6 |


These are computational cells/records, not independent hypotheses. Range and kernel configuration counts index the same cells; zone endpoints derive from the range search. The six calibrated families are range density, neighborhood, persistence, movement, spacing/clustering and spacing motifs. The motif universe contains all C(44,5) ordered positive spacings summing at most44, including unobserved patterns.



## Baseline spacing and broad-region behavior



Per-draw sorted numbers, ordered gaps, clustering metrics and broad-region counts are in spacing.csv. Broad regions are descriptive. Reference means/SDs use50,000 independent IID draws, not real-history estimates. The exact fair expected draw range is230/7=32.8571; exact expected mean adjacent gap46/7=6.5714. Reference Monte Carlo error explains small departures from these exact values.



| metric | reference_mean | reference_std | historical_mean |
| --- | --- | --- | --- |
| minimum_spacing | 1.7709 | 1.0247 | 1.8056 |
| maximum_spacing | 14.3886 | 4.8093 | 14.1092 |
| mean_spacing | 6.5823 | 1.3488 | 6.5418 |
| median_spacing | 5.2402 | 2.0255 | 5.2988 |
| spacing_variance | 25.8073 | 21.0825 | 24.6589 |
| consecutive_pairs | 0.6699 | 0.7276 | 0.6602 |
| draw_range | 32.9114 | 6.7442 | 32.7092 |
| nearest_mean | 4.5645 | 1.4039 | 4.5290 |
| gaps_le2 | 1.2578 | 0.8832 | 1.2394 |
| gaps_ge10 | 1.1979 | 0.6989 | 1.1719 |
| clusters_2 | 4.7422 | 0.8832 | 4.7606 |
| clusters_4 | 3.7604 | 0.9252 | 3.7655 |
| region_0 | 1.2022 | 0.9210 | 1.1647 |
| region_1 | 1.1977 | 0.9204 | 1.2514 |
| region_2 | 1.1980 | 0.9229 | 1.1839 |
| region_3 | 1.1948 | 0.9181 | 1.1888 |
| region_4 | 1.2073 | 0.9243 | 1.2112 |


## Strongest raw hot zones



| end_draw | target_draw | window | width | start_number | end_number | occurrences | density | expected_density | lift | raw_z | support_draws |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | 14 | 10 | 7 | 36 | 42 | 21 | 0.3000 | 0.1333 | 2.2500 | 4.4140 | 10 |
| 11 | 12 | 10 | 3 | 40 | 42 | 12 | 0.4000 | 0.1333 | 3.0000 | 4.3978 | 10 |
| 697 | 698 | 10 | 3 | 33 | 35 | 12 | 0.4000 | 0.1333 | 3.0000 | 4.3978 | 10 |
| 427 | 428 | 10 | 3 | 26 | 28 | 12 | 0.4000 | 0.1333 | 3.0000 | 4.3978 | 10 |
| 820 | 821 | 52 | 3 | 10 | 12 | 38 | 0.2436 | 0.1333 | 1.8269 | 4.1464 | 52 |
| 13 | 14 | 10 | 5 | 38 | 42 | 16 | 0.3200 | 0.1333 | 2.4000 | 4.0724 | 10 |
| 427 | 428 | 10 | 5 | 26 | 30 | 16 | 0.3200 | 0.1333 | 2.4000 | 4.0724 | 10 |
| 168 | 169 | 10 | 5 | 39 | 43 | 16 | 0.3200 | 0.1333 | 2.4000 | 4.0724 | 10 |
| 697 | 698 | 10 | 7 | 33 | 39 | 20 | 0.2857 | 0.1333 | 2.1429 | 4.0357 | 10 |
| 657 | 658 | 10 | 7 | 38 | 44 | 20 | 0.2857 | 0.1333 | 2.1429 | 4.0357 | 10 |


For example, W10 ending draw13 has21 of60 winning occurrences inside36..42: count density0.3000, lift2.25, raw z4.4140. This selected maximum is weaker than typical complete-search null maxima. Heavily overlapping ranges/endpoints are not independent discoveries; latest top3 positive ranges are grouped transitively.



## Neighborhood peaks



| window | kernel | signal | end_draw | number | score | raw_z |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | none | smoothed | 780 | 21 | 0.7000 | 5.2715 |
| 26 | none | smoothed | 715 | 33 | 0.4615 | 4.9231 |
| 10 | triangular1 | neighbor_only | 780 | 20 | 0.5000 | 4.8796 |
| 10 | box1 | neighbor_only | 780 | 20 | 0.5000 | 4.8796 |
| 10 | gaussian2 | neighbor_only | 780 | 20 | 0.4362 | 4.8591 |
| 52 | triangular1 | neighbor_only | 821 | 11 | 0.2885 | 4.7076 |
| 52 | box1 | neighbor_only | 821 | 11 | 0.2885 | 4.7076 |
| 26 | triangular1 | neighbor_only | 796 | 20 | 0.3462 | 4.5668 |
| 26 | box1 | neighbor_only | 796 | 20 | 0.3462 | 4.5668 |
| 10 | gaussian2 | smoothed | 697 | 34 | 0.3886 | 4.5606 |


The largest neighborhood-family peak is actually the **own-number** control: number21, seven appearances in10 completed draws ending780. Neighbor-only peaks around20 partially inherit activity at21. Full-search calibration includes own and neighbor variants equally; these local peaks are not evidence of a spatial mechanism.



## Hot-zone persistence and movement



| window | width | range_start | range_end | start_endpoint | end_endpoint | length |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 3 | 41 | 43 | 761 | 771 | 11 |
| 10 | 5 | 10 | 14 | 802 | 814 | 13 |
| 10 | 7 | 36 | 42 | 10 | 20 | 11 |
| 10 | 9 | 36 | 44 | 652 | 664 | 13 |
| 26 | 3 | 20 | 22 | 400 | 423 | 24 |
| 26 | 5 | 26 | 30 | 430 | 450 | 21 |
| 26 | 7 | 18 | 24 | 1072 | 1100 | 29 |
| 26 | 9 | 13 | 21 | 337 | 367 | 31 |
| 52 | 3 | 20 | 22 | 400 | 455 | 56 |
| 52 | 5 | 11 | 15 | 1030 | 1058 | 29 |
| 52 | 7 | 2 | 8 | 606 | 641 | 36 |
| 52 | 9 | 34 | 42 | 162 | 210 | 49 |


| window | width | latest_grouped_zones | identical_run | direction_run | mean_abs_movement | overlap_mean | positive_1_run | positive_2_run | positive_3_run | positive_4_run | negative_1_run | negative_2_run | negative_3_run | negative_4_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 3 | [(11, 13), (18, 20), (32, 34)] | 11 | 3 | 5.8761 | 0.5690 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 10 | 5 | [(9, 14), (16, 20)] | 13 | 3 | 5.3951 | 0.6262 | 2 | 1 | 1 | 1 | 1 | 2 | 1 | 1 |
| 10 | 7 | [(7, 13), (18, 24), (32, 38)] | 11 | 3 | 5.4235 | 0.6293 | 3 | 2 | 2 | 2 | 3 | 2 | 1 | 1 |
| 10 | 9 | [(10, 20)] | 13 | 3 | 4.3377 | 0.6955 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 1 |
| 26 | 3 | [(11, 13), (18, 20), (42, 44)] | 24 | 2 | 4.3601 | 0.6884 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 26 | 5 | [(9, 13), (16, 22)] | 21 | 2 | 3.6637 | 0.7527 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 26 | 7 | [(12, 22)] | 29 | 2 | 3.4774 | 0.7576 | 2 | 2 | 2 | 1 | 2 | 1 | 1 | 1 |
| 26 | 9 | [(11, 21)] | 31 | 2 | 3.4479 | 0.7720 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 1 |
| 52 | 3 | [(13, 15), (30, 33)] | 56 | 2 | 2.8575 | 0.8102 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 52 | 5 | [(24, 32)] | 29 | 2 | 2.4820 | 0.8260 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 52 | 7 | [(25, 33)] | 36 | 2 | 2.8047 | 0.8310 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 |
| 52 | 9 | [(24, 34)] | 49 | 2 | 1.9204 | 0.8775 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |


The longest identical strongest-range run is56 rolling endpoints for20..22, W52, ending draws400..455. Overlapping windows naturally induce long persistence. The strongest bounded directional movement run is3 steps. No persistence or movement family survives null comparison. Fixed-width zone traces do not estimate an adaptive expansion/contraction law; grouped latest extents are exported descriptively, and no movement predictor is fitted.



## Complete-search null results



| null_model | statistic | real_max | null_mean | null_q95 | exceedances | replicates | global_p | adjusted_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed_margins | range_density | 4.4140 | 4.9837 | 5.4973 | 191 | 199 | 0.9600 | 1.0000 |
| fixed_margins | neighborhood | 5.2715 | 5.5141 | 6.2017 | 175 | 199 | 0.8800 | 1.0000 |
| fixed_margins | persistence | 56.0000 | 56.3869 | 75.3000 | 87 | 199 | 0.4400 | 1.0000 |
| fixed_margins | movement | 3.0000 | 3.2513 | 4.0000 | 197 | 199 | 0.9900 | 1.0000 |
| fixed_margins | spacing_clustering | 5.8035 | 6.3661 | 7.8204 | 136 | 199 | 0.6850 | 1.0000 |
| fixed_margins | spacing_motif | 1.0000 | 1.7136 | 2.0000 | 199 | 199 | 1.0000 | 1.0000 |
| iid | range_density | 4.4140 | 4.9451 | 5.5024 | 188 | 199 | 0.9450 | 1.0000 |
| iid | neighborhood | 5.2715 | 5.5726 | 6.2104 | 176 | 199 | 0.8850 | 1.0000 |
| iid | persistence | 56.0000 | 57.4271 | 75.0000 | 102 | 199 | 0.5150 | 1.0000 |
| iid | movement | 3.0000 | 3.2663 | 4.0000 | 197 | 199 | 0.9900 | 1.0000 |
| iid | spacing_clustering | 5.8035 | 6.4611 | 7.8374 | 157 | 199 | 0.7900 | 1.0000 |
| iid | spacing_motif | 1.0000 | 1.7085 | 2.0000 | 199 | 199 | 1.0000 | 1.0000 |


Every one of199 IID and199 exact-margin histories reruns the full declared search and recomputes all recent activity, neighborhoods, hot zones, motion and spacing. Exact margins preserve six per draw and per-number counts; finite curveball mixing remains approximate. Empirical global p=(1+exceedances)/(199+1); adjusted p is Bonferroni across6 families within each null. No family survives correction under either null. Local raw z values are not local tests. Resolution is0.005 raw/0.030 adjusted.



## Development-only choices



Development targets401..900 alone selected12 range configurations,12 primary kernel configurations, then gap weights.25/.5/.75 for the selected neighborhood. Ties retain the declared order. No later outcome changed any choice.



Selected range: **W26, width3**. Selected neighborhood: **W52, kernel=none**. Gap combination weight **0.75**, with the remainder assigned to neighborhood percentile ranks.



**No smoothing won development selection.** The frozen NeighborhoodModel is therefore an own-number W52 frequency control, and the combination is75% Gap Logistic rank +25% own W52 frequency rank. It must not be described as evidence that neighbors help. All true smoothing/neighbor-only variants remain reported as ablations.



Frozen configuration SHA256: `2ce1f1b9d9005e50089cc4be587bad9fec19550fd84d16a5b0aa13d507af3301`.



Selection was saved before later scoring; cadence13 reuses it without selection. The development prefix hash, canonical descriptive hash and normalized full-input hash in BOTH cadence protocols are checked before prospective publication. Independent review caught the missing source-binding gate; it was fixed with a failing/passing regression before publication.



## Primary later historical results (901..1245)



The later segment is excluded from Phase10 model selection, but is NOT pristine after previous phases. Full401..1245 results include selection optimism and are exploratory. Existing Random and Gap Logistic reproduce their Phase9 score/rank/cutoff/hit outputs exactly:1,690 rows at each cadence.



| model | targets | avg_hits | mean_winning_rank | recall_6 | recall_10 | recall_15 | hits_0 | hits_1 | hits_2 | hits_3 | hits_4 | hits_5 | hits_6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | 345 | 0.7739 | 23.3362 | 0.1290 | 0.2072 | 0.3145 | 142 | 144 | 54 | 5 | 0 | 0 | 0 |
| GapLogistic | 345 | 0.8232 | 23.0478 | 0.1372 | 0.2184 | 0.3309 | 147 | 129 | 53 | 15 | 1 | 0 | 0 |
| RandomModel | 345 | 0.7681 | 22.9585 | 0.1280 | 0.2198 | 0.3367 | 149 | 135 | 53 | 8 | 0 | 0 | 0 |
| RangeDensityModel | 345 | 0.7652 | 23.0391 | 0.1275 | 0.2140 | 0.3391 | 140 | 155 | 42 | 7 | 1 | 0 | 0 |
| NeighborhoodModel | 345 | 0.7304 | 23.5005 | 0.1217 | 0.2068 | 0.3242 | 146 | 150 | 45 | 4 | 0 | 0 | 0 |
| GapNeighborhoodModel | 345 | 0.7507 | 23.1720 | 0.1251 | 0.2155 | 0.3198 | 161 | 122 | 51 | 9 | 2 | 0 | 0 |


### Paired uncertainty



Circular26-draw block bootstrap2,000, seed42. Intervals are exploratory and unadjusted for model search; positive hit differences favor the first model. Pool mean and3+/4+/5+/all6 comparisons against Random/Frequency26/Gap Logistic are also exported.



| model | reference | difference | ci_low | ci_high |
| --- | --- | --- | --- | --- |
| RangeDensityModel | RandomModel | -0.0029 | -0.0928 | 0.0812 |
| RangeDensityModel | Frequency26 | -0.0087 | -0.0899 | 0.0609 |
| RangeDensityModel | GapLogistic | -0.0580 | -0.1392 | 0.0319 |
| NeighborhoodModel | RandomModel | -0.0377 | -0.1536 | 0.0696 |
| NeighborhoodModel | Frequency26 | -0.0435 | -0.1420 | 0.0580 |
| NeighborhoodModel | GapLogistic | -0.0928 | -0.1855 | -0.0058 |
| GapNeighborhoodModel | RandomModel | -0.0174 | -0.1188 | 0.0986 |
| GapNeighborhoodModel | Frequency26 | -0.0232 | -0.1304 | 0.0841 |
| GapNeighborhoodModel | GapLogistic | -0.0725 | -0.1420 | -0.0058 |


The combination underperforms Gap Logistic by point estimate. There is no robust neighborhood/range improvement beyond the simple baselines.



### Candidate pools



Complete0..6 distributions, mean pool winners,3+/4+/5+/all6 rates, exact hypergeometric references, marginal intervals and paired comparisons are in pools.csv. Rare events are not evidence by themselves.



| model | pool_size | count_3plus | count_4plus | count_5plus | count_6plus | exact_random_5plus | exact_random_6plus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | 8 | 18 | 1 | 0 | 0 | 0.000258 | 3.44e-06 |
| Frequency26 | 10 | 33 | 4 | 0 | 0 | 0.0011 | 2.58e-05 |
| Frequency26 | 12 | 55 | 7 | 0 | 0 | 0.0033 | 0.000113 |
| Frequency26 | 15 | 100 | 21 | 4 | 0 | 0.0117 | 0.000614 |
| GapLogistic | 8 | 27 | 2 | 0 | 0 | 0.000258 | 3.44e-06 |
| GapLogistic | 10 | 43 | 6 | 1 | 0 | 0.0011 | 2.58e-05 |
| GapLogistic | 12 | 68 | 11 | 1 | 0 | 0.0033 | 0.000113 |
| GapLogistic | 15 | 116 | 31 | 3 | 0 | 0.0117 | 0.000614 |
| RandomModel | 8 | 20 | 1 | 0 | 0 | 0.000258 | 3.44e-06 |
| RandomModel | 10 | 35 | 6 | 0 | 0 | 0.0011 | 2.58e-05 |
| RandomModel | 12 | 71 | 14 | 0 | 0 | 0.0033 | 0.000113 |
| RandomModel | 15 | 111 | 34 | 0 | 0 | 0.0117 | 0.000614 |
| RangeDensityModel | 8 | 18 | 2 | 1 | 0 | 0.000258 | 3.44e-06 |
| RangeDensityModel | 10 | 44 | 3 | 1 | 0 | 0.0011 | 2.58e-05 |
| RangeDensityModel | 12 | 65 | 14 | 1 | 0 | 0.0033 | 0.000113 |
| RangeDensityModel | 15 | 113 | 35 | 6 | 0 | 0.0117 | 0.000614 |
| NeighborhoodModel | 8 | 16 | 1 | 0 | 0 | 0.000258 | 3.44e-06 |
| NeighborhoodModel | 10 | 32 | 3 | 0 | 0 | 0.0011 | 2.58e-05 |
| NeighborhoodModel | 12 | 55 | 15 | 1 | 0 | 0.0033 | 0.000113 |
| NeighborhoodModel | 15 | 100 | 37 | 4 | 0 | 0.0117 | 0.000614 |
| GapNeighborhoodModel | 8 | 26 | 2 | 0 | 0 | 0.000258 | 3.44e-06 |
| GapNeighborhoodModel | 10 | 43 | 5 | 0 | 0 | 0.0011 | 2.58e-05 |
| GapNeighborhoodModel | 12 | 66 | 8 | 0 | 0 | 0.0033 | 0.000113 |
| GapNeighborhoodModel | 15 | 105 | 23 | 0 | 0 | 0.0117 | 0.000614 |


## Window, width and kernel ablations



All configurations were declared before results. Later ablation outcomes are reported rather than used to select a replacement. Tables pair development/later average Top6 hits.



### Raw frequency



| model | development | later |
| --- | --- | --- |
| Frequency10 | 0.8100 | 0.7826 |
| Frequency26 | 0.7920 | 0.7739 |
| Frequency52 | 0.8620 | 0.7304 |


### Range widths and windows



| model | development | later |
| --- | --- | --- |
| Range_W10_D3 | 0.7960 | 0.7159 |
| Range_W10_D5 | 0.8000 | 0.7971 |
| Range_W10_D7 | 0.7900 | 0.7739 |
| Range_W10_D9 | 0.8080 | 0.7855 |
| Range_W26_D3 | 0.8100 | 0.7652 |
| Range_W26_D5 | 0.7660 | 0.7826 |
| Range_W26_D7 | 0.7740 | 0.8000 |
| Range_W26_D9 | 0.7600 | 0.7855 |
| Range_W52_D3 | 0.7900 | 0.8029 |
| Range_W52_D5 | 0.8080 | 0.7826 |
| Range_W52_D7 | 0.8080 | 0.7739 |
| Range_W52_D9 | 0.7720 | 0.7710 |


### Primary smoothing kernels



| model | development | later |
| --- | --- | --- |
| Neighborhood_W10_gaussian2 | 0.7940 | 0.7275 |
| Neighborhood_W10_none | 0.8100 | 0.7826 |
| Neighborhood_W10_triangular1 | 0.7960 | 0.6928 |
| Neighborhood_W10_triangular2 | 0.7980 | 0.7246 |
| Neighborhood_W26_gaussian2 | 0.7920 | 0.7507 |
| Neighborhood_W26_none | 0.7920 | 0.7739 |
| Neighborhood_W26_triangular1 | 0.8040 | 0.7623 |
| Neighborhood_W26_triangular2 | 0.7620 | 0.7420 |
| Neighborhood_W52_gaussian2 | 0.8080 | 0.7739 |
| Neighborhood_W52_none | 0.8620 | 0.7304 |
| Neighborhood_W52_triangular1 | 0.8100 | 0.7623 |
| Neighborhood_W52_triangular2 | 0.8000 | 0.7855 |


### Neighbor-only controls



| model | development | later |
| --- | --- | --- |
| NeighborOnly_W10_gaussian2 | 0.8040 | 0.7420 |
| NeighborOnly_W10_triangular1 | 0.7960 | 0.7768 |
| NeighborOnly_W10_triangular2 | 0.7920 | 0.7159 |
| NeighborOnly_W26_gaussian2 | 0.7340 | 0.7188 |
| NeighborOnly_W26_triangular1 | 0.7680 | 0.7565 |
| NeighborOnly_W26_triangular2 | 0.7560 | 0.7797 |
| NeighborOnly_W52_gaussian2 | 0.7680 | 0.8000 |
| NeighborOnly_W52_triangular1 | 0.7800 | 0.8522 |
| NeighborOnly_W52_triangular2 | 0.7600 | 0.7855 |


### Neighbor contribution versus own at the same W



| window | kernel | signal | avg_hits | own_avg_hits | difference | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | triangular1 | neighbor_only | 0.7768 | 0.7826 | -0.0058 | -0.1044 | 0.0928 |
| 10 | triangular1 | own_plus_neighbors | 0.6928 | 0.7826 | -0.0899 | -0.1623 | -0.0174 |
| 10 | triangular2 | neighbor_only | 0.7159 | 0.7826 | -0.0667 | -0.1768 | 0.0291 |
| 10 | triangular2 | own_plus_neighbors | 0.7246 | 0.7826 | -0.0580 | -0.1450 | 0.0261 |
| 10 | gaussian2 | neighbor_only | 0.7420 | 0.7826 | -0.0406 | -0.1478 | 0.0638 |
| 10 | gaussian2 | own_plus_neighbors | 0.7275 | 0.7826 | -0.0551 | -0.1362 | 0.0290 |
| 26 | triangular1 | neighbor_only | 0.7565 | 0.7739 | -0.0174 | -0.1246 | 0.0986 |
| 26 | triangular1 | own_plus_neighbors | 0.7623 | 0.7739 | -0.0116 | -0.0812 | 0.0493 |
| 26 | triangular2 | neighbor_only | 0.7797 | 0.7739 | 0.0058 | -0.1073 | 0.1159 |
| 26 | triangular2 | own_plus_neighbors | 0.7420 | 0.7739 | -0.0319 | -0.0957 | 0.0290 |
| 26 | gaussian2 | neighbor_only | 0.7188 | 0.7739 | -0.0551 | -0.1594 | 0.0522 |
| 26 | gaussian2 | own_plus_neighbors | 0.7507 | 0.7739 | -0.0232 | -0.0957 | 0.0464 |
| 52 | triangular1 | neighbor_only | 0.8522 | 0.7304 | 0.1217 | 0.0290 | 0.2232 |
| 52 | triangular1 | own_plus_neighbors | 0.7623 | 0.7304 | 0.0319 | -0.0493 | 0.1102 |
| 52 | triangular2 | neighbor_only | 0.7855 | 0.7304 | 0.0551 | -0.0435 | 0.1682 |
| 52 | triangular2 | own_plus_neighbors | 0.7855 | 0.7304 | 0.0551 | -0.0319 | 0.1392 |
| 52 | gaussian2 | neighbor_only | 0.8000 | 0.7304 | 0.0696 | -0.0493 | 0.1942 |
| 52 | gaussian2 | own_plus_neighbors | 0.7739 | 0.7304 | 0.0435 | -0.0233 | 0.1130 |


These are postselection-excluded ablation reports, not additional winners selected after seeing later performance. Positive unadjusted estimates require global and robustness support; none establishes the neighborhood hypothesis.



## Start-point and cadence robustness



Nested start slices401/501/601/701/801/901 retain the refit calendar from401. Starts before901 overlap development; they are descriptive, not independent later validation.



### Cadence26 average hits by start



| model | 401 | 501 | 601 | 701 | 801 | 901 |
| --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | 0.7846 | 0.7732 | 0.7767 | 0.7743 | 0.7730 | 0.7739 |
| GapLogistic | 0.8426 | 0.8336 | 0.8388 | 0.8330 | 0.8472 | 0.8232 |
| GapNeighborhoodModel | 0.8142 | 0.7933 | 0.8109 | 0.8000 | 0.7978 | 0.7507 |
| NeighborhoodModel | 0.8083 | 0.7893 | 0.7829 | 0.7817 | 0.7685 | 0.7304 |
| RandomModel | 0.8024 | 0.8054 | 0.7984 | 0.7761 | 0.7685 | 0.7681 |
| RangeDensityModel | 0.7917 | 0.7839 | 0.7984 | 0.7963 | 0.8135 | 0.7652 |


### Cadence13 average hits by start



| model | 401 | 501 | 601 | 701 | 801 | 901 |
| --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | 0.7846 | 0.7732 | 0.7767 | 0.7743 | 0.7730 | 0.7739 |
| GapLogistic | 0.8391 | 0.8322 | 0.8403 | 0.8349 | 0.8472 | 0.8203 |
| GapNeighborhoodModel | 0.8059 | 0.7919 | 0.8062 | 0.7963 | 0.7933 | 0.7449 |
| NeighborhoodModel | 0.8083 | 0.7893 | 0.7829 | 0.7817 | 0.7685 | 0.7304 |
| RandomModel | 0.8024 | 0.8054 | 0.7984 | 0.7761 | 0.7685 | 0.7681 |
| RangeDensityModel | 0.7917 | 0.7839 | 0.7984 | 0.7963 | 0.8135 | 0.7652 |


### Later-period early/middle/recent blocks



| model | block | start_draw | end_draw | targets | avg_hits | delta_vs_random |
| --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | early | 901 | 1015 | 115 | 0.6696 | -0.1043 |
| Frequency26 | middle | 1016 | 1130 | 115 | 0.9043 | 0.0783 |
| Frequency26 | recent | 1131 | 1245 | 115 | 0.7478 | 0.0435 |
| GapLogistic | early | 901 | 1015 | 115 | 0.7565 | -0.0174 |
| GapLogistic | middle | 1016 | 1130 | 115 | 0.8957 | 0.0696 |
| GapLogistic | recent | 1131 | 1245 | 115 | 0.8174 | 0.1130 |
| RandomModel | early | 901 | 1015 | 115 | 0.7739 | 0.0000 |
| RandomModel | middle | 1016 | 1130 | 115 | 0.8261 | 0.0000 |
| RandomModel | recent | 1131 | 1245 | 115 | 0.7043 | 0.0000 |
| RangeDensityModel | early | 901 | 1015 | 115 | 0.6783 | -0.0957 |
| RangeDensityModel | middle | 1016 | 1130 | 115 | 0.8261 | 0.0000 |
| RangeDensityModel | recent | 1131 | 1245 | 115 | 0.7913 | 0.0870 |
| NeighborhoodModel | early | 901 | 1015 | 115 | 0.6435 | -0.1304 |
| NeighborhoodModel | middle | 1016 | 1130 | 115 | 0.8435 | 0.0174 |
| NeighborhoodModel | recent | 1131 | 1245 | 115 | 0.7043 | 0.0000 |
| GapNeighborhoodModel | early | 901 | 1015 | 115 | 0.6435 | -0.1304 |
| GapNeighborhoodModel | middle | 1016 | 1130 | 115 | 0.8174 | -0.0087 |
| GapNeighborhoodModel | recent | 1131 | 1245 | 115 | 0.7913 | 0.0870 |


Rolling104-target performance is exported and plotted. No stable positive effect appears across eras or cadence. Range/neighborhood scores have no fitted temporal parameters, so their fixed-config results are cadence invariant; Gap Logistic and its combination may change.



## Equal-budget virtual ticket portfolios



All methods use identical target sets and budgets1/5/10/20, deterministic seed42+target, unique nested tickets. Model methods use Top15; uniform controls sample all45. This intentionally tests practical concentration versus broader coverage. All portfolios exist before actual and bonus evaluation; bonus never enters training. Range coverage rewards new five-subsets, then uncovered grouped zones/outside, then new pairs and seeded priority. No2+2 quota was introduced. Individual-number coverage is implicit through pairs, not an extra optimized reward.



| model | method | budget | mean_best_match | draws_ge4 | draws_ge5 | prize1_tickets | prize2_tickets | prize3_tickets | delta_best_vs_uniform | paired_ci_low | paired_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | weighted | 1 | 0.7304 | 0 | 0 | 0 | 0 | 0 | -0.0725 | -0.1681 | 0.0203 |
| Frequency26 | weighted | 5 | 1.4116 | 3 | 0 | 0 | 0 | 0 | -0.2870 | -0.3913 | -0.1768 |
| Frequency26 | weighted | 10 | 1.6116 | 4 | 0 | 0 | 0 | 0 | -0.4203 | -0.5362 | -0.2986 |
| Frequency26 | weighted | 20 | 1.7188 | 7 | 0 | 0 | 0 | 0 | -0.6406 | -0.7594 | -0.5101 |
| GapLogistic | weighted | 1 | 0.7884 | 0 | 0 | 0 | 0 | 0 | -0.0145 | -0.1333 | 0.1072 |
| GapLogistic | weighted | 5 | 1.5159 | 1 | 0 | 0 | 0 | 0 | -0.1826 | -0.2986 | -0.0754 |
| GapLogistic | weighted | 10 | 1.6580 | 3 | 0 | 0 | 0 | 0 | -0.3739 | -0.4725 | -0.2754 |
| GapLogistic | weighted | 20 | 1.7913 | 8 | 1 | 0 | 0 | 1 | -0.5681 | -0.6841 | -0.4493 |
| NeighborhoodModel | weighted | 1 | 0.7739 | 0 | 0 | 0 | 0 | 0 | -0.0290 | -0.1420 | 0.0899 |
| NeighborhoodModel | weighted | 5 | 1.4580 | 6 | 0 | 0 | 0 | 0 | -0.2406 | -0.3363 | -0.1391 |
| NeighborhoodModel | weighted | 10 | 1.6522 | 10 | 0 | 0 | 0 | 0 | -0.3797 | -0.4841 | -0.2725 |
| NeighborhoodModel | weighted | 20 | 1.7652 | 17 | 0 | 0 | 0 | 0 | -0.5942 | -0.7188 | -0.4580 |
| RangeDensityModel | weighted | 1 | 0.8609 | 2 | 0 | 0 | 0 | 0 | 0.0580 | -0.0522 | 0.1565 |
| RangeDensityModel | weighted | 5 | 1.4609 | 2 | 0 | 0 | 0 | 0 | -0.2377 | -0.3333 | -0.1275 |
| RangeDensityModel | weighted | 10 | 1.6899 | 3 | 0 | 0 | 0 | 0 | -0.3420 | -0.4638 | -0.2231 |
| RangeDensityModel | weighted | 20 | 1.8493 | 11 | 0 | 0 | 0 | 0 | -0.5101 | -0.6464 | -0.3797 |
| RangeDensityModel | range_coverage | 1 | 0.8406 | 2 | 0 | 0 | 0 | 0 | 0.0377 | -0.0696 | 0.1478 |
| RangeDensityModel | range_coverage | 5 | 1.5565 | 2 | 0 | 0 | 0 | 0 | -0.1420 | -0.2319 | -0.0464 |
| RangeDensityModel | range_coverage | 10 | 1.7623 | 3 | 0 | 0 | 0 | 0 | -0.2696 | -0.3855 | -0.1449 |
| RangeDensityModel | range_coverage | 20 | 1.8725 | 7 | 0 | 0 | 0 | 0 | -0.4870 | -0.6116 | -0.3681 |
| GapNeighborhoodModel | weighted | 1 | 0.8000 | 0 | 0 | 0 | 0 | 0 | -0.0029 | -0.1304 | 0.1130 |
| GapNeighborhoodModel | weighted | 5 | 1.4696 | 1 | 0 | 0 | 0 | 0 | -0.2290 | -0.3362 | -0.1275 |
| GapNeighborhoodModel | weighted | 10 | 1.6522 | 1 | 0 | 0 | 0 | 0 | -0.3797 | -0.5043 | -0.2580 |
| GapNeighborhoodModel | weighted | 20 | 1.7826 | 4 | 0 | 0 | 0 | 0 | -0.5768 | -0.7014 | -0.4522 |
| Uniform45 | uniform | 1 | 0.8029 | 1 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| Uniform45 | uniform | 5 | 1.6986 | 2 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| Uniform45 | uniform | 10 | 2.0319 | 4 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| Uniform45 | uniform | 20 | 2.3594 | 9 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |


Range-aware20-ticket mean best match1.8725 versus uniform2.3594. Restricting tickets to an uninformative small pool reduces broad coverage; range allocation does not establish superiority. No range-aware allocation will be frozen as a separately justified strategy. The three scoring models still freeze normal experimental weighted/coverage portfolios as required, without claiming superiority.



Prize-equivalent events are saved in portfolio_prize_events.csv for each cadence. Nested budgets are not independent events; the same successful ticket may appear at multiple budgets. An isolated five-main-number event does not establish skill.



| model | method | target_draw | budget | prize1 | prize2 | prize3 |
| --- | --- | --- | --- | --- | --- | --- |
| GapLogistic | weighted | 1225 | 20 | 0 | 0 | 1 |


## Outputs and verification



Code adds reusable finite-axis analysis, two scoring models plus the frozen gap combination, development selection, matched evaluation/portfolios, offline commands and an isolated immutable publisher. Existing formulas/defaults remain intact.



Commands: `analyze-number-space`, `compare-number-space --cadence 26`, `compare-number-space --cadence 13`, `freeze-number-space`. Reports live only under reports/number_space/;11 plots cover all requested views plus rolling ranking performance and global null maxima. Full45 score/rank/cutoff audit rows are preserved.



Initial baseline:265 passed,2 dependency-related skips. Final full suite: **289 passed, 2 existing dependency skips in45.05s**; evidence is recorded in verification.json. All new timing, boundary, selection, seeded null, ticket, publication, score-consistency and integrity tests use synthetic outcomes. No dependency installation or network access was required.



Analysis including398 complete surrogate searches: 237.3s. Verified frozen-selection reruns: cadence26 63.4s, cadence13 65.1s. Original development selection plus first evaluation took136.9s; no selection was repeated in the verified reruns. Timings depend on concurrent workload.



The [Phase10 prospective record](phase10-prospective.md) is written after the one-time independent freeze. All prior Phase5-9 evidence remains immutable. No real draw1246 result is accessed; no commit/push.


Publication completed once: **draw1246_phase10_numberspace_20261017T100839079270_ccb21ee9**, status **FROZEN_UNEVALUATED**. The [prospective record](phase10-prospective.md) lists rankings, ticket/artifact links and SHA256. All25 earlier files and the canonical hash were verified unchanged after publication. No model design or parameters were changed after viewing frozen predictions.
