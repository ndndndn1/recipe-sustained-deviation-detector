# Literature-grounded learning / 문헌 기반 학습

## Evidence register

### S1. Copper Electroplating Technology for Microvia Filling

Lefebvre et al., IPC conference paper (2004).
https://www.electronics.org/system/files/technical_resource/E18%26S23-2.pdf

Access: full text read during planning; a later retrieval timed out. Public primary technical source, not an ABF-specific modern process qualification.

The paper studies current density, agitation, geometry and chemistry alongside via filling. This motivates recording these conditions and comparing matched shapes, rather than combining unrelated lots. Its filling-ratio definition is height-based; the tool keeps area measurements separate. Reported experimental bath recipes are not adopted as production recommendations.

Hypothesis: observed low fill at higher current deserves a matched comparison controlling bath and geometry. Falsifier: the contrast disappears when order, agitation and bath state are controlled. Implementation: stratified associations and replicated current contrasts. Validation: synthetic software examples only; no reproduction of the paper's process experiments.

### S2. Superconformal Film Growth

Moffat, Wheeler and Josell, ECS meeting (2002), NIST record.
https://www.nist.gov/publications/superconformal-film-growth

Access: official abstract read on 2026-09-16; full paper not accessed. The abstract describes coupling between accelerator surface coverage and geometry during deposition. It supports a qualitative warning that planar charge balance alone cannot determine via filling shape. No CEAC kinetics or calibrated coefficients have been implemented. A future reproduction must obtain full equations, parameters and experimental conditions first.

### S3. Fast Filling of Microvia by Pre-Settling Particles and Following Cu Electroplating

Nanomaterials 12(10), 1699 (2022).
https://doi.org/10.3390/nano12101699

Access: bibliographic/abstract discovery only; publisher retrieval returned 429. Not used for numerical assumptions or performance claims. The additional particle step is outside this project's experimental scope. No automated retry or alternative institutional account was used to bypass the response.

## Directly learned by implementation

- Units matter: A/dm2 must convert to A/m2, minutes to seconds, metres to micrometres. Independent charge balance checks detect scaling mistakes.
- A section's copper area fraction and a via's height filling ratio are different quantities. A small pixel error also changes measured area through the squared calibration scale.
- More observations do not remove confounding. Separate lot and exact geometry before comparing conditions; acquire bath composition/age and agitation before causal interpretation.
- Equal experiment budgets and information separation are necessary to compare optimization methods. A smooth synthetic surface can make an optimizer appear unusually strong.

These are documented implementation observations, not statements of factory experience. Public inputs cannot establish company-specific cost savings, throughput gains or manufacturing qualification.
