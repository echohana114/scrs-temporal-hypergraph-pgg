# Cooperative role screening stabilizes cooperation in temporal hypergraph public goods games

Hui Zhao

School of Mechanical Engineering, Tongji University, Shanghai, China.

Correspondence: huizhao@tongji.edu.cn

## Abstract

Temporal public goods games create a role-attribution problem because successful groups can contain both contributors and free riders. We introduce cooperative role screening (SCRS), a rule that separates where imitation is sampled from who is eligible to transmit: temporal group exposure supplies the local context, whereas a cooperation-conditioned role mask restricts imitation to eligible cooperators. Across empirical, synthetic, null-model and construction-sensitive temporal hypergraphs, SCRS preserved cooperation against role-disrupted controls, while score-shuffled and generic local cooperator-search controls showed that fine score ordering is not the independent driver. These results identify local cooperative role screening, rather than score ordering or payoff ranking among eligible cooperators, as the supported stabilizing component under temporal-hypergraph exposure.

## Introduction

Cooperation remains difficult to explain when individual incentives favor free riding. In public goods games, cooperators pay a cost that increases the return available to a group, whereas defectors can share in the resulting benefit without paying that cost. This tension has made public goods games a central model for studying collective action, social punishment, structured reciprocity and the emergence of cooperation across biological and social systems [@hardin1968tragedy; @axelrod1981evolution; @fehr2002altruistic; @hauert2002volunteering; @nowak2006five; @santos2008social; @levin2014public]. A persistent theme is that cooperation can survive when the social environment changes which strategies are encountered, who can influence whom and how payoff differences are translated into imitation [@nowak1992spatial; @ohtsuki2006simple; @santos2005scale; @szabo2007evolutionary; @traulsen2007pairwise; @perc2017statistical].

Network reciprocity, temporal network theory and higher-order network models have each expanded this picture, but their combination still leaves a mechanistic gap. Static networks show how local structure can let cooperators support one another, while temporal networks show that ordering, burstiness and non-Markovian contact patterns can change the routes through which information and strategies spread [@holme2012temporal; @perra2012activity; @karsai2012universal; @masuda2013temporal; @scholtes2014causality; @li2017fundamental; @li2020evolution]. Higher-order and hypergraph models add the fact that many social interactions are group events rather than reducible pairs, with consequences for contagion, prediction and evolutionary games [@benson2016higher; @battiston2020networks; @battiston2021physics; @iacopini2019simplicial; @torres2021representations; @bick2023what; @alvarezrodriguez2021evolutionary; @civilini2021evolutionary]. Recent work on temporal hypergraph memory and hyperedge overlap shows that higher-order organization is not just a representational choice: temporal memory, overlap among group events and activity heterogeneity can change collective dynamics [@gallo2024higherorder; @malizia2025hyperedge]. Strategy-evolution work on temporal hypergraphs has also shown that time-resolved group structure can promote cooperation under payoff-based imitation [@wang2026strategy], yet the specific local rule by which a learner identifies a useful cooperative example remains underdeveloped.

Most update rules in structured evolutionary games emphasize the interaction structure being sampled, the payoff of available neighbors or direct imitation among contacts, and recent work continues to show that update heterogeneity, concurrent games and multiplayer structure can change cooperation outcomes [@meng2024personalised; @rossetti2025concurrent; @wang2024multiplayer]. These ingredients remain important, but group interactions separate two questions that pairwise imitation often merges: which local group context should be treated as informative, and which individual role inside that group should be imitated. Standard imitate-the-best or Fermi-style rules can therefore copy a free rider from a profitable group, allowing successful defection to spread when group payoff and individual contribution are misattributed. A temporal hyperedge supplies a transient group-success context that static or pairwise representations do not directly encode. Yet a profitable group can contain both contributors and free riders, so selecting a successful group is not equivalent to selecting a cooperative example. The resulting structural-mechanism proposition is that SCRS should be strongest when temporal organization repeatedly exposes learners to successful groups that still contain cooperative roles, and weaker when temporal memory, hyperedge overlap, activity heterogeneity or mixed-role exposure removes those cooperative examples. The missing mechanism is therefore not fine ordering among high-score edges, payoff ranking alone or neighbor imitation alone. It is the ability to screen for cooperative role models within locally successful temporal groups.

Here we propose cooperative role screening (SCRS) for public goods games on temporal hypergraphs (Fig. 1). SCRS treats social learning as layered information filtering: temporal exposure supplies local group contexts over the focal player's incident hyperedges, while the role mask restricts imitation to cooperative candidates within the sampled group whenever such candidates exist. In this formulation, temporal exposure supplies where the local signal is sampled; cooperative role screening controls who can transmit a strategy. This distinction also bounds the claim: fine score ordering among successful groups may help organize exposure, but it is not treated as the independent causal engine of cooperation. We test SCRS on empirical contact hypergraphs, synthetic temporal hypergraphs, temporal and topological null models, external empirical datasets, parameter sweeps and implementation sensitivity analyses, and then use targeted ablations to separate group context, cooperation conditioning and payoff ranking.

## Results

### Mathematical formulation of cooperative role screening

SCRS formalizes imitation as a two-stage event on a temporal hypergraph (Fig. 1). For focal node \(i\), the first stage samples a local group context from the incident temporal hyperedges, using the cooperative-success score only as an exposure layer,

\[
\pi_i(e,t)\propto w(G_e(t)),\qquad e\in E_t(i).
\]

After normalization over incident hyperedges,

\[
\pi_i(e,t)=\frac{w(G_e(t))}{\sum_{e'\in E_t(i)}w(G_{e'}(t))},\qquad e\in E_t(i).
\]

The second stage applies a cooperation-conditioned role mask,

\[
M_{ij}(e,t)=\mathbf{1}\{j\in e\setminus\{i\},\,s_j(t)=1\},\qquad
\mathcal{C}_i(e,t)=\{j:M_{ij}(e,t)=1\},
\]

so that cooperative candidates, rather than all successful group members, become eligible role models. Once a role model \(j\) is selected, adoption follows the Fermi comparison

\[
\Pr(i\leftarrow j)=\left[1+\exp\{-\beta(P_j(t)-P_i(t))\}\right]^{-1}.
\]

This separation is the core claim tested below: temporal exposure supplies local group contexts, whereas cooperative role screening controls who can transmit.

### SCRS promotes cooperation across empirical and synthetic temporal hypergraphs

The main validation experiment (Table S1) used 14,400 Monte Carlo trials, 5000 update steps per trial, 50 repetitions per cell and a tail average over the final 1000 steps. We tested four empirical SocioPatterns contact datasets and two synthetic temporal hypergraphs at per-member marginal return coefficients \(r=0.70\), \(0.90\) and \(1.00\), using fixed edge size \(h=6\), initial cooperator density \(\rho_0=0.5\) and selection intensity \(\beta=2.0\). SCRS maintained high empirical cooperation, with mean tail cooperation 0.8450 and a weakest empirical cell of 0.6289 (Fig. 2a-d); in the two synthetic cases it reached 1.0000 in every main-validation cell.

The paired performance gaps were large against the principal baselines (Fig. 2f). In empirical temporal hypergraphs, SCRS exceeded the temporal-hypergraph imitation baseline based on Wang et al. by +0.6543, cooperative-success group-context selection (CSGC) by +0.6491 and strategy-shuffled SCRS by +0.6157 on average. Cell-level paired inference treated the 12 empirical case-parameter cells as the units for this comparison: the empirical gap against the Wang et al. baseline had a bootstrap 95% CI of +0.4889 to +0.8152 (paired sign-permutation two-sided \(P=0.00049\)), the gap against CSGC had a CI of +0.4849 to +0.8116 (\(P=0.00049\)) and the gap against strategy-shuffled SCRS had a CI of +0.4698 to +0.7652 (\(P=0.00049\)). In synthetic temporal hypergraphs, the corresponding mean gaps were +0.4100, +0.2967 and +0.1433. By contrast, score-shuffled SCRS was essentially tied with SCRS, with a mean empirical gap of +0.0011, bootstrap CI -0.0017 to +0.0050 and \(P=0.7905\). The main performance result is therefore strong stability relative to standard and role-disrupted controls, with a specific boundary on claims about the independent value of the score layer.

### Mechanism decomposition separates exposure from role filtering

The mechanism decomposition experiment (Table S1) directly separated role and score components using 7,350 trials (Fig. 3). The empirical SCRS mean was 0.8456, close to the main validation, and synthetic SCRS again reached 1.0000. Replacing the cooperation-conditioned role screen with shuffled strategy labels produced a large empirical mean gap of +0.6074 in favor of SCRS (bootstrap 95% CI +0.4612 to +0.7508; paired sign-permutation two-sided \(P=0.00049\)). Removing cooperation conditioning while retaining payoff-based role selection also failed, with a +0.5715 mean gap against payoff-only role selection (+0.4372 to +0.7041; \(P=0.00049\)). Selecting a successful edge without filtering for cooperators gave a +0.5925 mean gap (+0.4507 to +0.7403; \(P=0.00049\)), and choosing a random role on the same selected edge gave a +0.6515 mean gap (+0.4815 to +0.8139; \(P=0.00049\)).

These ablations isolate the supported component. SCRS works because the learner receives a cooperative role sample from a local group context, not because it merely selects a high-scoring edge or copies the highest-payoff individual. Two comparisons mark the boundary. Score-shuffled SCRS was tied with SCRS in practice, with an empirical mean gap of -0.0003, bootstrap CI -0.0015 to +0.0008 and \(P=0.6011\); only 1 of 12 confidence intervals was positive. Cooperator-only random role selection was also tied with SCRS, with a mean empirical gap of -0.0009, bootstrap CI -0.0023 to +0.0003 and \(P=0.2344\); again only 1 of 12 confidence intervals was positive. Thus, the evidence supports cooperation-conditioned role screening under temporal-hypergraph exposure; fine edge-score ordering and payoff ranking among eligible cooperators are not independently necessary under the tested conditions.

The clean mechanism-context experiment (Table S1; Supplementary Fig. S29) added three controls that asked whether any local search for cooperators is enough: cooperator-only sampling from a uniformly sampled incident edge, cooperator-only sampling from a random local neighborhood and successful-edge sampling without score ranking. Across 6300 matched trials, SCRS remained far above strategy-shuffled SCRS, with a mean empirical gap of +0.6166 (bootstrap 95% CI +0.4661 to +0.7658; paired sign-permutation two-sided \(P=0.00049\)). It did not separate meaningfully from the generic local cooperator-search controls: the empirical mean gaps were +0.0019 against uniformly sampled incident-edge cooperator search (-0.0011 to +0.0063; \(P=0.4771\)), -0.0016 against random local-neighborhood cooperator search (-0.0028 to -0.0006; \(P=0.0117\), in the opposite direction) and -0.0017 against successful-edge sampling without score ranking (-0.0032 to -0.0005; \(P=0.0171\), in the opposite direction). This result narrows the mechanism claim. The supported stabilizing component is local cooperative role screening under temporal-hypergraph exposure; successful-group context is an effective exposure layer, not an independently necessary driver in all tested regimes.

### Phase boundaries under return, initial condition and mutation noise

The parameter robustness experiment (Table S1) expanded the range to 84,000 trials across \(r\), selection intensity \(\beta\) and \(\rho_0\) sweeps. In the \(r\) sweep, empirical SCRS averaged 0.8263 and synthetic SCRS averaged 1.0000, with mean empirical gaps of +0.6412 against the Wang et al. baseline, +0.6284 against CSGC and +0.5926 against strategy-shuffled SCRS. In the \(\beta\) sweep, empirical SCRS averaged 0.8475 and retained a +0.6138 mean gap against strategy-shuffled SCRS. These sweeps show that the main validation result is not confined to one return coefficient or one imitation temperature.

The widest fragility appeared in the \(\rho_0\) sweep and is now shown as an empirical \(r\times\rho_0\) phase diagram (Fig. 2e). Empirical SCRS still averaged 0.7577, but the weakest cell dropped to 0.1015; synthetic SCRS averaged 0.9780, with a minimum of 0.6800. This identifies an initial-condition boundary rather than a general failure of the mechanism. When too few cooperators are initially available, the rule has limited cooperative role models to screen, so the exposure step cannot reliably seed cooperative imitation. A complementary long-horizon mutation phase diagram (Table S1; Fig. 4d) shows a similar boundary under mutation rate \(\mu\): empirical SCRS declined as mutation increased, from 0.6985 at \(\mu=0\) to 0.5487 at \(\mu=0.01\).

### Temporal and topological perturbations preserve the SCRS advantage

The empirical null-model experiment (Table S1) tested whether the advantage depended on the exact ordering or topology of the original contact sequences. We compared the original empirical temporal hypergraphs with block-order shuffled, degree-preserving rewired and activity-preserving resampled null models, for 12,000 formal trials (Fig. 4a-c). Across the real-null cells, SCRS had mean tail cooperation 0.8498 and a weakest cell of 0.6274.

The SCRS advantage persisted across these null models. Mean gaps were +0.6600 against the Wang et al. baseline, +0.6437 against CSGC and +0.6162 against strategy-shuffled SCRS, with all 48 tested cells giving confidence intervals above zero for those three comparisons. The score-shuffled comparison again remained small: the mean gap was +0.0038 and only 4 of 48 cell-level confidence intervals were positive. Thus, null models preserve the central SCRS advantage but also preserve the claim boundary that edge-score ordering alone is not the main source of the effect.

### Synthetic topology and size stress tests support generality

The synthetic stress test (Table S1) asked whether the mechanism survives changes in topology and population size. We ran 11,250 trials across structured-ring, community-resampled, uniform-random, heterogeneous-activity and temporal-modular-switching temporal hypergraphs, with \(n=100\), \(200\) and \(400\) and with the number of hyperedges scaled as \(m=0.2n\) (Fig. 4e,f). SCRS remained near fixation: mean tail cooperation was 0.9993 and the weakest topology-size case averaged 0.9941.

The stress-test gaps were also positive against role-disrupted and non-SCRS baselines. Averaged over the synthetic stress-test cells, SCRS exceeded the Wang et al. baseline by +0.3426, CSGC by +0.2432 and strategy-shuffled SCRS by +0.1722. The gap against score-shuffled SCRS was effectively zero, matching the main-validation and null-model pattern. Synthetic stress therefore supports the generality of cooperative role screening over population size and temporal topology, while again limiting the interpretation of the edge-score layer to contextual sampling.

### Construction sensitivity and structural moderators refine the claim

The hypergraph-construction sensitivity audit (Table S1; Supplementary Fig. S28) tested whether the main empirical result depended on converting pairwise contacts into a single fixed \(h=6\) hypergraph representation. We ran 45,000 matched trials across the four core contact datasets plus Copenhagen Bluetooth and Email-Enron, varying \(h\in\{4,6,8\}\), \(m\in\{20,33\}\), temporal block duration \(\in\{50,100,200\}\) and construction mode. SCRS retained high cooperation across construction slices, with mean tail cooperation 0.8919 and a weakest construction cell of 0.5874. The mean gaps remained positive against the Wang et al. baseline (+0.6400), CSGC (+0.6142) and strategy-shuffled SCRS (+0.5929), while the score-shuffled gap stayed near zero (+0.0023). Thus, the fixed-size construction is a modeling assumption that affects absolute values in some cells, especially smaller-edge SFHH settings, but it does not create the role-screening advantage.

The structure-stratified moderator audit (Table S1; Supplementary Fig. S30) then related SCRS paired gaps to temporal-hypergraph organization across the completed main, null-model, stress-test, external, construction-sensitivity and clean-control summaries. Temporal memory and within-block hyperedge overlap moderated the role-screening advantage most clearly. The gap against strategy-shuffled SCRS rose from +0.3470 in low temporal-memory strata to +0.5921 in high temporal-memory strata, and from +0.3487 in low within-block-overlap strata to +0.6300 in high-overlap strata. Temporal memory and hyperedge overlap increase repeated exposure to local group contexts containing eligible cooperative roles, making role screening more consequential. Score-shuffled gaps remained near zero across the same strata. Activity heterogeneity was not monotone, and the mixed-role exposure potential was nearly saturated in these completed cells, so these moderators refine rather than overextend the mechanism: temporal organization and overlap make role screening more consequential, but the present data do not support a broad claim that every structural heterogeneity measure strengthens SCRS.

### External empirical datasets and implementation sensitivity define boundary regimes

The external empirical test (Table S1) extended the analysis beyond the original contact datasets to Copenhagen Bluetooth proximity, Email-EU, Congress bills, Ask Ubuntu threads and Email-Enron temporal group data (Fig. 5a-c). These datasets were converted into fixed-size temporal hypergraphs by sorting events in time, retaining active nodes, constructing \(h=6\) group interactions and sampling \(m=33\) hyperedges per temporal block. They differ in event semantics, node activity, sparsity and retained event counts, so the high absolute cooperation should not be read as evidence that the setting is uniformly easy. Across 3,750 external empirical trials, SCRS achieved mean tail cooperation 0.9911, with a weakest cell of 0.9749. Mean gaps were +0.6112 against the Wang et al. baseline, +0.5509 against CSGC and +0.4313 against strategy-shuffled SCRS, while the score-shuffled gap remained near zero at +0.0002. The lower cooperation observed under per-capita payoff, low initial cooperation and mutation noise provides the corresponding boundary cases.

The implementation sensitivity experiment (Table S1) tested payoff and update modes (Fig. 5d). Under the accumulated-payoff synchronous baseline, empirical SCRS averaged 0.6967 and exceeded strategy-shuffled SCRS by +0.3678. Degree-normalized payoff increased empirical SCRS to 0.7148 and gave a +0.4285 strategy-shuffled gap; asynchronous in-place updating gave mean empirical SCRS 0.6978 and a +0.3717 strategy-shuffled gap. Per-capita payoff lowered absolute empirical cooperation to 0.4394, but the relative mechanism remained visible, with a +0.1558 gap against strategy-shuffled SCRS. Finally, the long-horizon mutation audit (Table S1) supplies the trajectory and endpoint views of the noise boundary over 10,000 steps (Fig. 5e,f). Empirical strategy-shuffled gaps declined from +0.3739 at \(\mu=0\) to +0.0970 at \(\mu=0.01\); synthetic SCRS remained high, averaging 0.8826 even at \(\mu=0.01\). Together, the long-horizon, external and implementation-sensitivity experiments show external validity, implementation stability and a clear noise/payoff boundary.

## Discussion

SCRS is not best understood as a generic performance improvement to temporal-hypergraph imitation or as a score-ranking trick. It changes what a learner can copy during updating. Temporal exposure supplies local group contexts, whereas cooperative role screening explains the stabilizing effect. This distinction matters because public goods groups can be profitable even when they contain defectors. An update rule that only identifies a successful edge can still point the learner toward a free rider, whereas SCRS conditions the imitable role on cooperation within the sampled context.

Role screening is effective because it links two signals that are separated in group games. Group-level success indicates that the local interaction context can sustain high payoff, while the cooperator filter identifies which strategy actually contributed to the public good. When both signals are present, a focal player is more likely to encounter a strategy that is both socially productive and locally successful. The mechanism decompositions support this interpretation: disrupting strategy labels, dropping the cooperator filter or selecting a random role from the same edge removes most of the advantage, whereas random selection among eligible cooperators remains close to SCRS.

This interpretation also turns SCRS into a structural hypothesis rather than only a performance comparison. Temporal memory, hyperedge overlap, activity heterogeneity and mixed-role exposure can moderate the mechanism because they determine how often a learner encounters repeated group contexts with eligible cooperators inside them. The completed structure-stratified audit supports the strongest version of this claim for temporal memory and hyperedge overlap: role-disrupted gaps increased in higher-memory and higher-overlap strata, while score-shuffled gaps remained close to zero. The evidence is weaker for activity heterogeneity and mixed-role exposure potential, the latter being nearly saturated in the completed cells. SCRS should therefore be read as a role-screening mechanism whose strength depends on temporal-hypergraph organization, not as a universal guarantee that every form of higher-order structure increases cooperation.

The score-shuffled result is a claim boundary, not a contradiction. Score-shuffled SCRS preserves the downstream cooperative role screen while disrupting the fine ordering of edge scores, and it remains close to SCRS in the tested regimes. This pattern indicates that the cooperative-success score should be interpreted as a contextual sampling layer rather than as a direct causal driver. Temporal hypergraphs already expose a learner to changing local group contexts, and even a shuffled score layer can supply enough local exposure when cooperative role models are abundant. What fails sharply is not score reordering but disruption of the role signal itself: strategy shuffling, removal of the cooperator filter and random role choice from the same selected edge all destroy most of the SCRS advantage.

This boundary makes the mechanism more specific. SCRS does not claim that exact edge-score rank is necessary for cooperation, nor that every local cooperator-search rule has been excluded. The supported claim is that, within the tested temporal-hypergraph public goods settings, cooperative role screening is the stabilizing component once temporal group exposure supplies locally successful contexts. The completed local-search controls, including cooperator-only sampling from uniformly chosen incident edges, random local neighborhoods and successful edges without score ranking, caution against broader sufficiency claims when cooperative role models are already abundant. Payoff scaling also matters. Under per-capita payoff, empirical absolute cooperation is lower, but the advantage over strategy-shuffled SCRS remains positive. Low per-member return, high mutation rates and extreme initial conditions act as phase boundaries because they reduce the availability, stability or payoff advantage of cooperative role models.

Beyond evolutionary-game models, the same abstraction points to a broader problem of role attribution in group success: when a successful group contains both constructive and exploitative roles, transmission rules may need to filter who is eligible to be copied rather than only which group appears successful.

These findings provide a testable mechanism for cooperation in time-resolved higher-order interaction systems. Rather than treating temporal hypergraphs only as changing opportunity structures, SCRS identifies a role-selection process that can be experimentally decomposed and falsified. The construction-sensitivity audit shows that the result is not an artifact of a single fixed-size hypergraph construction, the clean mechanism-context controls show that generic local cooperator search can match SCRS when cooperative role models are already abundant, and the structural moderator audit shows that temporal memory and overlap sharpen the role-screening advantage. A direct falsifiable prediction is that the SCRS advantage should shrink when local successful groups rarely contain cooperators, mutation noise is high or payoff is diluted by per-capita scaling.

## Methods

### Temporal hypergraph construction

We represent the interaction data as a temporal hypergraph sequence \(H_t=(V,E_t)\), where \(V\) is the node set and \(E_t\) is the set of group interactions active in temporal block \(t\). The edge size \(h\) is the number of nodes in each hyperedge. In the formal experiments, \(h=6\) unless a sensitivity case states otherwise. The parameter \(m\) is the number of hyperedges sampled in each temporal block; the main empirical and external tests used \(m=33\), while the main synthetic validation used \(m=20\) and the size stress test scaled \(m\) as \(0.2n\). The block-duration parameter gives the duration of one temporal block, with the main experiments using 100 time units.

The original empirical tests used SocioPatterns-style contact datasets: High school 2013, Workplace 2013, Hospital ward 2010 and SFHH 2009 [@cattuto2010dynamics; @fournet2014contact; @mastrandrea2015contact; @vanhems2013estimating; @genois2015office; @sociopatternsData]. Pairwise contact rows were grouped into temporal snapshots; \(h=6\) cliques were extracted where possible, and contact-centered \(h\)-groups supplied a deterministic fallback when a temporal block had too few cliques. Table S2 reports the input contact rows, retained contact rows and sampled hyperedges for each core empirical dataset. The external empirical datasets used Copenhagen Bluetooth proximity [@sapiezynski2019interaction], Email-EU, Email-Enron, Congress bills and Ask Ubuntu thread data from the Cornell higher-order network collection [@cornellHigherOrderData; @emailEuData; @emailEnronData; @congressBillsData; @askUbuntuThreadsData]. Each external dataset was sorted by timestamp, capped to the most active nodes when needed, converted to \(h=6\) group interactions and sampled to \(m=33\) hyperedges per block. The external dataset manifest gives the retained event counts and preprocessing decisions. The construction-sensitivity audit varied \(h\in\{4,6,8\}\), \(m\in\{20,33\}\), temporal block duration \(\in\{50,100,200\}\), clique-only extraction, contact-centered fallback construction, a fixed-\(h=6\) alternative and native variable-size group-event construction where available.

### Public goods payoff

Each node has a binary strategy \(s_i(t)\), where \(s_i(t)=1\) denotes cooperation and \(s_i(t)=0\) denotes defection. The number of cooperators in hyperedge \(e\) at time \(t\) is

\[
n_C(e,t)=\sum_{j\in e}s_j(t).
\]

The coefficient \(r\) is a per-member marginal return coefficient: one additional cooperator in an edge increases every member's edge payoff by \(r\) before the cooperator pays unit cost. In the accumulated-payoff mode used for the main experiments, node \(i\) receives

\[
P_i(t)=\sum_{e\in E_t:\,i\in e}\left[r\,n_C(e,t)-s_i(t)\right].
\]

Thus every member of an edge receives the benefit \(r n_C(e,t)\), and a cooperator pays cost 1 in each incident edge. This \(r\) is not the conventional total public-goods multiplier. For fixed group size \(h\), the equivalent conventional multiplier is \(R=hr\); with the main value \(h=6\), \(r=0.70\), \(0.90\) and \(1.00\) correspond to \(R=4.2\), \(5.4\) and \(6.0\). The implementation-sensitivity analysis also tested degree-normalized payoff, where accumulated payoff is divided by the number of incident edges, and a stricter per-capita payoff mode, where the edge benefit is \(r n_C(e,t)/h\) before the cooperation cost is subtracted. In that per-capita mode, \(r\) is interpreted as the conventional group multiplier. All main Results use accumulated payoff and synchronous updating unless a payoff/update sensitivity condition states otherwise.

### Cooperative-success edge score

SCRS uses an edge-level context score before choosing an individual role model. For edge \(e\), define the cooperative fraction \(q_e(t)=n_C(e,t)/h\). The cooperative-success score is

\[
G_e(t)=q_e(t)\max\{0,r\,n_C(e,t)-1\}.
\]

The score is zero when no cooperator is present and increases when an edge contains more cooperators and gives positive cooperative net return. For a focal node, incident edges are sampled using standardized edge scores. If all incident scores are identical, the edge is sampled uniformly. Otherwise, each incident edge receives weight

\[
w(G_e(t))=1+\max\{0,z_e\},
\]

where \(z_e\) is its within-neighborhood standardized score.

### SCRS update rule

The initial cooperator density \(\rho_0\) is the fraction of nodes initialized as cooperators at the start of a trial. At each update, SCRS applies three local kernels: a context kernel, a role mask and an adoption kernel. Let \(E_t(i)=\{e\in E_t:i\in e\}\) denote the incident hyperedges of focal node \(i\). Context sampling weights incident hyperedges as

\[
\pi_i(e,t)\propto w(G_e(t)),\qquad e\in E_t(i),
\]

with normalized probability

\[
\pi_i(e,t)=\frac{w(G_e(t))}{\sum_{e'\in E_t(i)}w(G_{e'}(t))},\qquad e\in E_t(i).
\]

Here \(w(G_e(t))\) is the nonnegative sampling weight derived from the standardized cooperative-success score. In the implementation, it equals \(1+\max\{0,z_e\}\) when incident scores vary, where \(z_e\) is the within-neighborhood standardized score, and the rule becomes uniform sampling when all incident scores are identical. If \(E_t(i)\) is empty, the focal node keeps its current strategy for that update.

The role mask then defines which individuals in the sampled context can transmit cooperation:

\[
M_{ij}(e,t)=\mathbf{1}\{j\in e\setminus\{i\},\,s_j(t)=1\}.
\]

The focal node is never included in the mask, so it cannot copy itself. The candidate set is

\[
\mathcal{C}_i(e,t)=\{j:M_{ij}(e,t)=1\}.
\]

If the sampled edge has positive score and \(\mathcal{C}_i(e,t)\) is nonempty, the role model is the candidate with highest payoff, with random tie-breaking. Same-strategy cooperators may be selected; in that case the subsequent adoption step can leave the focal strategy unchanged. If the sampled edge has no eligible cooperator, the fallback role model is sampled uniformly from \(e\setminus\{i\}\). If \(e\setminus\{i\}\) is empty, the focal node retains its strategy.

After a role model \(j\) is selected for focal node \(i\), the adoption kernel follows the Fermi pairwise comparison rule [@traulsen2007pairwise]:

\[
\Pr(i\leftarrow j)
=\left[1+\exp\{-\beta(P_j(t)-P_i(t))\}\right]^{-1}.
\]

Here \(\beta\) is the selection intensity. Larger \(\beta\) makes payoff differences more decisive, while lower values increase stochasticity. Unless noted otherwise, we used \(\beta=2.0\). Trials ran for 5000 update steps in the main, robustness, null-model, stress, mechanism, external and implementation-sensitivity experiments, and for 10,000 steps in the long-horizon mutation audit. The reported tail cooperation is the mean cooperation over the final 1000 steps, and the number of Monte Carlo repetitions is usually 50 per cell.

### Transition-kernel interpretation

The SCRS update can be written as a finite-state transition kernel by separating context sampling, role eligibility and payoff comparison. Let the Fermi adoption function be

\[
F_{\beta}(\Delta P)=\left[1+\exp(-\beta\Delta P)\right]^{-1},
\]

and let \(\psi_{ij}(e,t)\) denote the role-selection probability of choosing node \(j\) after edge \(e\) has been sampled. Under full SCRS, \(\psi_{ij}(e,t)\) is zero for the focal node and for non-cooperators when eligible cooperators exist; among eligible cooperators it follows payoff ranking with random tie-breaking. When no eligible cooperator exists, \(\psi_{ij}(e,t)\) is uniform over \(e\setminus\{i\}\).

The probability that focal node \(i\) copies role model \(j\) at time \(t\) is therefore

\[
\mathcal{W}_{i\leftarrow j}(t)
=\sum_{e\in E_t(i)}\pi_i(e,t)\,\psi_{ij}(e,t)\,
F_{\beta}\!\left(P_j(t)-P_i(t)\right),
\]

and the one-step expected change in the focal strategy is

\[
\mathrm{E}[\Delta s_i(t)]
=\sum_{e\in E_t(i)}\pi_i(e,t)
\sum_{j\in e\setminus\{i\}}\psi_{ij}(e,t)
\left[s_j(t)-s_i(t)\right]
F_{\beta}\!\left(P_j(t)-P_i(t)\right).
\]

For small selection intensity, the Fermi term has the local expansion

\[
F_{\beta}(P_j-P_i)=\frac{1}{2}+\frac{\beta(P_j-P_i)}{4}+O(\beta^3).
\]

This expansion is used only to interpret the transition kernel. SCRS does not change the public-goods payoff; it changes which payoff comparisons enter the update by combining the context kernel \(\pi_i(e,t)\) with the role-selection probability \(\psi_{ij}(e,t)\). The Results therefore rely on simulation, matched ablations and cell-level paired inference rather than on a closed-form fixation threshold.

### Baselines and ablations

The Wang et al. baseline implements temporal-hypergraph payoff-based imitation following recent strategy-evolution work on temporal hypergraphs [@wang2026strategy]. CSGC keeps cooperative-success edge-context selection but does not enforce the SCRS role screen. LFDS controls use the strongest matched local diffusion-style variants available in the formal comparison set. Score-shuffled SCRS permutes edge scores before edge selection, preserving the downstream SCRS role rule while disrupting the score ordering. Strategy-shuffled SCRS permutes strategy labels used for the role-screening step, preserving other model components while breaking the link between cooperation and role eligibility.

The mechanism decomposition added four mechanism variants. The payoff-only role variant selects role models by payoff without a cooperation filter. The success-only-no-coop-filter variant uses the successful-edge condition without requiring a cooperative role. The random-role-same-edge variant samples a random role from the selected edge. The cooperator-only-random variant retains the cooperator filter but chooses randomly among eligible cooperators. The clean mechanism-context experiment added three further controls: cooperator-only sampling from a uniformly sampled incident edge, cooperator-only sampling from a random local neighborhood and successful-edge sampling without score ranking. Comparisons among these variants separate edge context, cooperation conditioning, payoff ranking and generic local cooperator search.

### Null models

The null-model audit evaluated temporal and topological null models for the empirical datasets. Block-order shuffling preserves block contents while changing temporal order. Degree-preserving rewiring preserves node-level participation tendencies while randomizing group membership structure. Activity-preserving resampling preserves temporal activity rates while resampling event composition. These nulls test whether the SCRS advantage requires the exact empirical sequence or whether it persists when temporal order or topology is partially randomized.

### Synthetic generators

Synthetic temporal hypergraphs were used both for controlled main validation and for topology-size stress tests. The main validation used structured-ring and community temporal hypergraphs with \(n=100\), \(m=20\) and \(h=6\). The stress test expanded to structured-ring, community-resampled, uniform-random, heterogeneous-activity and temporal-modular-switching generators, with \(n=100\), \(200\) and \(400\). These generators separate regular local overlap, modularity, random mixing, heterogeneous participation and switching temporal modules.

### External empirical preprocessing

External empirical data were converted to fixed-size temporal hypergraphs using a common preprocessing scheme. Timestamped group events were sorted by time, mapped to integer node identifiers and filtered to nodes with sufficient activity when datasets exceeded the target size. Events smaller than \(h\) were not used as \(h=6\) hyperedges; events larger than \(h\) were converted by sampling fixed-size groups. Each block was sampled to \(m=33\) hyperedges when enough events were available. The prepared external manifest records input events, retained events, node counts, edge counts and source URLs.

### Structural-moderator audit

The structure-stratified audit computed temporal memory, hyperedge overlap, activity heterogeneity and mixed-role exposure potential for completed empirical and synthetic temporal-hypergraph cells, then related those quantities to paired SCRS gaps, the SCRS role-model cooperator rate and the SCRS-versus-CSGC selection lift. Temporal memory measures adjacent-block recurrence using Jaccard similarity among group events. Hyperedge overlap measures mean Jaccard overlap among contemporaneous or adjacent hyperedges. Activity heterogeneity measures dispersion in node participation counts using coefficient of variation and Gini summaries. Mixed-role exposure potential estimates whether a construction can expose a learner to groups that contain both cooperators and defectors under the initial \(\rho_0\). These quantities are moderators rather than new model parameters: they test when temporal-hypergraph organization supplies eligible cooperative role models often enough for the role screen to matter.

### Statistical analysis

For each condition, we report mean tail cooperation, standard error and approximate 95% confidence intervals across Monte Carlo repetitions. Monte Carlo repetitions quantify within-cell simulation uncertainty, whereas matched case-parameter cells are the inferential units for cross-condition claims. Paired gap summaries compare SCRS with each control within matched case-parameter cells, and a positive gap means SCRS has higher tail cooperation. The deposited source data include a cell-level inference summary with paired bootstrap intervals for the mean paired gap and paired sign-permutation summaries across cells; repetition-level intervals are used only to describe within-cell simulation variability.

### Reproducibility and QA

All formal results used completed output directories documented in the deposited provenance records and release manifest. The manuscript source data were generated by the deposited source-data script or copied from completed formal output tables into the deposited Source Data directory. Each formal experiment group has supplementary source CSV or QA JSON files in the deposited supplementary source-data directory. Table S1 summarizes the experimental design, Table S2 reports dataset and hypergraph construction statistics, Table S3 defines the baseline and ablation variants and Table S4 records the completed supplementary robustness and mechanism audits. The deposited experiment-specification records provide the same S28-S30 completed audit records as machine-readable CSV and JSON. The reference list was generated by the deposited reference-verification script, which queried the Crossref Works API for DOI metadata and recorded non-DOI dataset resources as manual URL entries. Numerical computing used Python with NumPy, pandas and Matplotlib [@harris2020array; @hunter2007matplotlib].

## Acknowledgements

The author thanks the maintainers of the SocioPatterns, Copenhagen Networks Study and Cornell higher-order network datasets for making empirical interaction data available.

## Funding

No specific funding was received for this work.

## Author Contributions

H.Z. conceived the study, designed the SCRS model, implemented the simulations and analyses, curated the source data, prepared the figures and wrote the manuscript.

## Competing Interests

The author declares no competing interests.

## Data Availability

The source data required to reproduce all main and supplementary figures, processed result summaries, random seed manifest, environment files and QA records are prepared for deposition in a public repository: [data repository name and data DOI to be inserted]. The deposition includes the Source Data directory, figure-specific Source Data packages for Figs. 1-5, a supplementary Source Data package for Supplementary Figs. S20-S30, supplementary tables, figure manifest, reference verification records and the release manifest. Raw empirical datasets are available from the cited SocioPatterns, Copenhagen Networks Study and Cornell higher-order network repositories; the deposited source data include processed hypergraph summaries and manifests sufficient to verify and extend the reported figure-level conclusions.

## Code Availability

The simulation and analysis code are prepared for release in a public GitHub repository and archival DOI record: [GitHub URL to be inserted], [code DOI to be inserted]. The archived release will identify the exact tag or commit used for the manuscript: [release tag/commit to be inserted]. The release includes the scripts for source-data generation, figure regeneration, reference verification, formal experiment drivers, random-seed records and environment files needed to reproduce the reported analyses.

## Figure Legends

Figure legends are provided as a separate manuscript file.

## References

Reference metadata and DOI/URL verification records are provided with the deposited manuscript package.
