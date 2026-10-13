# Fig. 1 Vector Blueprint: Success-Context Cooperative Role Screening

Role: senior scientific illustrator for Nature Communications.

Purpose: redraw Fig. 1 as a vector schematic showing that the score layer samples a successful group context, whereas cooperative role screening determines the copied role. The figure should read as a mechanism diagram, not a generic workflow.

## Canvas

- Physical size: 180 mm wide x 120 mm high.
- SVG viewBox: `0 0 1800 1200`.
- Background: white, `#FFFFFF`.
- Export targets: editable SVG, vector PDF, and 600 dpi PNG preview.
- Font family: Helvetica or Arial.
- Stroke joins and caps: round.
- Main stroke width: 5 px in SVG coordinates, equivalent to about 0.5 pt at final print size.
- Highlight stroke width: 8 px, equivalent to about 0.75 pt.

## Palette

| Element | Hex | Use |
|---|---:|---|
| Cooperator | `#2E8B57` | Filled C nodes, passed role model, SCRS outcome |
| Defector/free rider | `#DC143C` | D nodes in explicit blocked/free-rider comparison |
| Defector alternate | `#5F6368` | Low-emphasis D nodes in panel a |
| Focal learner | `#00A6D6` | Border/halo around node `i` |
| Context blue | `#0072B2` | Selected successful hyperedge, context arrow |
| Auxiliary grey | `#B8B8B8` | Non-selected hyperedges, context layer scaffolding |
| Pale grey fill | `#F5F6F7` | Formula bar and soft panel guides |
| Claim boundary shade | `#EFEFEF` | Standard imitation/free-rider contrast |
| Text | `#1A1A1A` | Labels and equations |

## Typography

- Panel labels: 11 pt bold, lowercase `a`, `b`, `c`, `d`.
- Panel subtitles: 9 pt bold.
- Node letters: 8 pt bold white.
- Local labels: 7 pt regular.
- Step labels: 7 pt bold.
- Formula labels: 7 pt bold.
- Formula body: 8 pt, LaTeX-rendered vector text.
- Keep all visible text editable where possible. If equations are converted to paths for Illustrator, keep a hidden editable text layer with the source equation.

## Layout

- Outer margin: 60 px.
- Top panels share the same baseline and height:
  - Panel a: x 70-545, y 95-710.
  - Panel b: x 615-1185, y 95-710.
  - Panel c: x 1255-1730, y 95-710.
- Bottom formula bar:
  - Panel d: x 70-1730, y 785-1125.
- Inter-panel arrows:
  - Arrow a -> b: from `(555, 390)` to `(600, 390)`.
  - Arrow b -> c: from `(1195, 390)` to `(1240, 390)`.
  - Stroke `#5F6368`, opacity 0.55, width 5 px, arrowhead 16 px.
  - Labels above arrows:
    - a -> b: `sample context`
    - b -> c: `screen role`

## Panel a: Temporal Hypergraph Context

Panel label at `(80, 105)`: `a`

Subtitle at `(115, 105)`: `Temporal hypergraph context`

Draw a time badge at `(455, 142)`, rounded rectangle width 70 height 28, fill `#F5F6F7`, stroke `#D0D0D0`, text `t`.

Hyperedges:

| Edge | Center | Size | Rotation | Stroke/fill |
|---|---:|---:|---:|---|
| `e_1(t)` | `(285, 318)` | `300 x 185` | `-18 deg` | stroke `#B8B8B8`, fill `#EAF2F8`, opacity 0.30 |
| `e_2(t)` | `(342, 418)` | `330 x 205` | `14 deg` | stroke `#B8B8B8`, fill `#F4ECF7`, opacity 0.30 |
| `e_3(t)` | `(250, 505)` | `285 x 170` | `24 deg` | stroke `#B8B8B8`, fill `#E8F5E9`, opacity 0.25 |
| selected incident edge preview | `(333, 418)` | `338 x 210` | `14 deg` | stroke `#0072B2`, no fill, opacity 0.95 |

Node positions:

| Node | Position | Strategy | Style |
|---|---:|---|---|
| focal `i` | `(330, 420)` | D before update | white fill, border `#00A6D6`, border 8 px, label `i` in `#00A6D6` |
| `v_1` | `(245, 330)` | C | fill `#2E8B57`, white `C` |
| `v_2` | `(383, 335)` | D | fill `#5F6368`, white `D` |
| `v_3` | `(455, 435)` | C | fill `#2E8B57`, white `C` |
| `v_4` | `(252, 455)` | D | fill `#5F6368`, white `D` |
| `v_5` | `(172, 515)` | C | fill `#2E8B57`, white `C` |
| `v_6` | `(367, 555)` | D | fill `#5F6368`, white `D` |
| `v_7` | `(187, 300)` | D | fill `#5F6368`, white `D` |

Node radius:

- Ordinary nodes: 25 px.
- Focal learner: 31 px.
- Focal learner halo: radius 41 px, no fill, stroke `#00A6D6`, opacity 0.18, width 12 px.

Local annotation:

- At `(110, 650)`: `Focal learner observes only incident temporal groups`.
- Use 7 pt text, color `#5F6368`.

## Panel b: Two-Step Selection Mechanism

Panel label at `(625, 105)`: `b`

Subtitle at `(660, 105)`: `Two-step selection mechanism`

### Step 1: Context Selection

Place label at `(650, 170)`: `Step 1: context sampling`

Draw a compact score list from x `650` to `980`, y `210` to `410`.

Rows:

| Row | y | Label | Bar value | Bar color |
|---|---:|---|---:|---|
| 1 | 225 | `e_1` | 0.42 | `#B8B8B8` |
| 2 | 285 | `e*` | 0.87 | `#0072B2` |
| 3 | 345 | `e_3` | 0.18 | `#B8B8B8` |

Bar geometry:

- Label x: `662`.
- Bar x start: `720`.
- Bar max width: `235`.
- Bar height: `20`.
- Bar corner radius: 6.
- Selected row background: rounded rectangle `(638, 262, 350, 48)`, fill `#EAF2F8`, stroke `#0072B2`, width 5 px.
- Formula text above bars at `(650, 200)`: `$G_e(t)$ ranks local group contexts`.
- Small note below bars at `(650, 390)`: `Score layer = contextual sampler`.

### Step 2: Cooperative Screening

Place label at `(650, 470)`: `Step 2: cooperative role screen`

Selected edge mini-view:

- Draw ellipse centered `(845, 575)`, size `310 x 165`, rotation `0`, fill `#F5F6F7`, stroke `#0072B2`, width 7 px.
- Label above ellipse at `(735, 480)`: `selected successful edge e*`.

Nodes inside selected edge:

| Node | Position | Strategy | Extra mark |
|---|---:|---|---|
| candidate C `j` | `(750, 575)` | C | green eligibility halo radius 37 px, stroke `#2E8B57`, width 8 px |
| free rider D | `(845, 575)` | D | red dashed blocked halo radius 35 px, stroke `#DC143C`, width 6 px |
| candidate C | `(940, 575)` | C | normal |

Filter:

- Place a green funnel/shield icon centered at `(1055, 575)`.
- Funnel outline path: `(1015, 520) -> (1095, 520) -> (1068, 570) -> (1068, 625) -> (1042, 625) -> (1042, 570) -> close`.
- Stroke and fill: stroke `#2E8B57`, fill `#EAF6EF`, stroke width 6 px.
- Add text inside funnel at `(1055, 568)`: `C only`, 7 pt bold, color `#2E8B57`.
- Draw red blocking line from `(816, 545)` to `(874, 605)` and `(874, 545)` to `(816, 605)`, stroke `#DC143C`, width 7 px.
- Label below D at `(805, 645)`: `successful but not copied`.
- Label below C at `(690, 645)`: `eligible cooperative role model`.

Flow:

- Thin blue arrow from selected score row `(965, 285)` to selected edge `(735, 520)`.
- Thin green arrow from candidate C `j` `(770, 575)` through filter `(1015, 575)` to panel c start `(1240, 360)`.
- Red blocked arrow from D `(845, 575)` toward filter `(1015, 575)`, ending at filter boundary with stop cap.

## Panel c: Evolutionary Outcome

Panel label at `(1265, 105)`: `c`

Subtitle at `(1300, 105)`: `Evolutionary outcome`

Split panel c into two stacked outcomes:

### Upper outcome: SCRS

- Header at `(1300, 175)`: `SCRS update`.
- Draw pre-update focal node at `(1335, 285)`: white fill, border `#00A6D6`, label `i:D`.
- Draw arrow `(1390, 285)` to `(1510, 285)`, stroke `#2E8B57`, arrowhead.
- Draw post-update node at `(1585, 285)`: fill `#2E8B57`, label `i:C`.
- Add green halo around post-update node: radius 44 px, stroke `#2E8B57`, opacity 0.18, width 14 px.
- Text at `(1300, 360)`: `cooperative role copied`.

### Lower contrast: standard imitation

- Draw pale grey rounded rectangle `(1285, 425, 405, 205)`, fill `#EFEFEF`, stroke none.
- Header at `(1300, 465)`: `Unscreened imitation contrast`.
- Draw D node at `(1410, 540)`, fill `#DC143C`, label `D`.
- Draw arrow `(1455, 540)` to `(1550, 540)`, stroke `#DC143C`, arrowhead, opacity 0.75.
- Draw focal node at `(1610, 540)`: white fill, border `#DC143C`, label `i:D`.
- Text at `(1300, 610)`: `free rider may be copied`.
- Add a small warning callout at `(1575, 465)`: `wrong role`, text `#DC143C`, 7 pt bold.

Outcome message:

- At `(1300, 680)`: `Group success defines WHERE; role screening defines WHO.`
- Use 8 pt bold, color `#1A1A1A`.

## Panel d: Core Equations

Panel label at `(80, 810)`: `d`

Subtitle at `(115, 810)`: `Operational rules`

Background:

- Rounded rectangle `(70, 785, 1660, 340)`, radius 16 px, fill `#F5F6F7`, stroke `#DADADA`, width 4 px.
- Inner vertical divider from `(900, 850)` to `(900, 1090)`, stroke `#DADADA`, width 3 px.

Left column:

- Label at `(120, 875)`: `Payoff`
- Formula at `(245, 875)`:
  `$P_i(t)=\sum_{e\in\mathcal{E}_t:i\in e}\left[r\,n_C(e,t)-s_i(t)\right]$`
- Label at `(120, 965)`: `Context score`
- Formula at `(245, 965)`:
  `$G_e(t)=q_e(t)\max\{0,r\,n_C(e,t)-1\},\quad q_e(t)=n_C(e,t)/|e|$`

Right column:

- Label at `(940, 875)`: `Eligible roles`
- Formula at `(1070, 875)`:
  `$\mathcal{C}_i(e^\star,t)=\{j\in e^\star\setminus\{i\}:s_j(t)=1\}$`
- Label at `(940, 965)`: `Adoption`
- Formula at `(1070, 965)`:
  `$\Pr(i\leftarrow j)=\left[1+\exp\{-\beta(P_j-P_i)\}\right]^{-1}$`

Footer note:

- At `(120, 1065)`: `Successful-group context is an exposure layer; cooperative role screening is the stabilizing mechanism.`
- Use 7 pt italic, color `#5F6368`.

## Layer Order

1. White background.
2. Pale panel guide shapes and selected-row backgrounds.
3. Hyperedge fills and score-list backgrounds.
4. Hyperedge strokes.
5. Nodes and halos.
6. Arrows.
7. Text labels.
8. Equations.

## Illustrator/Inkscape Implementation Notes

- Build all hyperedges as editable ellipses with separate fill opacity and stroke opacity.
- Do not use drop shadows except the very light focal halos specified above.
- Keep arrows below text and above hyperedge fills.
- Avoid large rounded boxes around the top panels; the visual modules should be defined by whitespace and panel labels.
- Equations should be inserted from LaTeX as vector PDF/SVG snippets or generated by TikZ. Do not paste raster screenshots.
- The selected edge in panel b and the cooperative role model should be the visual center of the figure.

