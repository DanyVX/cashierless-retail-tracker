# Consented mock-shelf recording protocol

## Before filming
Every visible participant must agree, with consent evidence stored privately **outside git**. Use a closed private space with no public/customer footage. Consent to record is separate from consent to publish a blurred clip.

## M0 capture checklist (not yet confirmed)
| Field | Current value |
| --- | --- |
| Camera make/model, lens | TBD |
| Actual resolution and FPS | TBD (not measured) |
| Fixed mounting angle, distance | TBD |
| Auto-exposure / autofocus / lighting | TBD |
| Shelf geometry, zones and calibration reference | TBD |
| Exact five-to-ten SKU inventory and zones | TBD |
| Participants' private signed/recorded consent | Pending |

## Scripted protocol
1. Mount one stable high-front or top-down camera to reduce occlusions, with adequate constant lighting.
2. Photograph/diagram *only the empty shelf* to define numbered zones. Track calibration/camera parameters; never put personal or identifying information in git.
3. Record an empty-scene setup clip and a static shelf view, with known timebase and no bystanders.
4. Record at least three separately labeled tracker clips and scripted trials: one shopper, two shoppers at same shelf, pick-and-return, multi-item grab, hover, staff restocking, heavy occlusion, low light and fast shopper.
5. Annotate timestamped track boxes and pick/return changes in private files. Split train/validation/test at **session** level, not adjacent frames.
6. Note each deliberate exposure/camera change and any recording interruptions; gaps must not be bridged as inferred events.
7. **Never publish clips** until validated face blurring, independent consent for publication, and M7 controls are present.

Recommended recording parameters are not claimed as actual measurements. The capture setup and SKU decisions remain acceptance blockers.
