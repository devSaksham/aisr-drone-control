# Verified references (IEEE style)

Owner: M1 (report Section 13). Every entry was checked against the publisher's record
or an index (Crossref, dblp, IEEE Xplore, PubMed, a library catalogue) on 2026-11-17.
Entries are numbered in the order they are planned to be cited; renumber if the report
cites them in a different order. Mark anything not yet checked `[VERIFY]`.

| # | Reference | Checked via | Use in report |
|---|---|---|---|
| 1 | O. Michel, "Webots: Professional mobile robot simulation," *Int. J. Adv. Robot. Syst.*, vol. 1, no. 1, pp. 39-42, 2004, doi: 10.5772/5618. | DOAJ, arXiv cs/0412052 | Sec. 3, 8: simulation platform |
| 2 | S. Bouabdallah, A. Noth, and R. Siegwart, "PID vs LQ control techniques applied to an indoor micro quadrotor," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS)*, Sendai, Japan, 2004, vol. 3, pp. 2451-2456, doi: 10.1109/IROS.2004.1389776. | Crossref, dblp, ETH record | Sec. 3: PID on quadrotors |
| 3 | R. Mahony, V. Kumar, and P. Corke, "Multirotor aerial vehicles: Modeling, estimation, and control of quadrotor," *IEEE Robot. Autom. Mag.*, vol. 19, no. 3, pp. 20-32, 2012, doi: 10.1109/MRA.2012.2206474. | ANU portal, IEEE record | Sec. 5: dynamics, cascaded control |
| 4 | T. Lee, M. Leok, and N. H. McClamroch, "Geometric tracking control of a quadrotor UAV on SE(3)," in *Proc. 49th IEEE Conf. Decis. Control (CDC)*, Atlanta, GA, USA, 2010, pp. 5420-5425, doi: 10.1109/CDC.2010.5717652. | dblp, library record | Sec. 3: nonlinear alternatives |
| 5 | D. Mellinger and V. Kumar, "Minimum snap trajectory generation and control for quadrotors," in *Proc. IEEE Int. Conf. Robot. Autom. (ICRA)*, Shanghai, China, 2011, pp. 2520-2525, doi: 10.1109/ICRA.2011.5980409. | researchr, IEEE Xplore | Sec. 3, 5: polynomial trajectories |
| 6 | T. Flash and N. Hogan, "The coordination of arm movements: An experimentally confirmed mathematical model," *J. Neurosci.*, vol. 5, no. 7, pp. 1688-1703, 1985, doi: 10.1523/JNEUROSCI.05-07-01688.1985. | PubMed (PMID 4020415), PMC | Sec. 5: origin of the minimum-jerk profile |
| 7 | M. W. Mueller, M. Hehn, and R. D'Andrea, "A computationally efficient motion primitive for quadrocopter trajectory generation," *IEEE Trans. Robot.*, vol. 31, no. 6, pp. 1294-1310, 2015, doi: 10.1109/TRO.2015.2479878. | dblp, author PDF | Sec. 3: fast trajectory primitives |
| 8 | K. J. Åström and T. Hägglund, *PID Controllers: Theory, Design, and Tuning*, 2nd ed. Research Triangle Park, NC, USA: Instrument Society of America, 1995, ISBN 1-55617-516-7. | Library of Congress record | Sec. 5, 7: PID, anti-windup, derivative filter |
| 9 | R. E. Kalman, "A new approach to linear filtering and prediction problems," *J. Basic Eng.*, vol. 82, no. 1, pp. 35-45, 1960, doi: 10.1115/1.3662552. | Crossref (ASME) | Sec. 5, 6: velocity estimator |
| 10 | G. M. Hoffmann, H. Huang, S. L. Waslander, and C. J. Tomlin, "Quadrotor helicopter flight dynamics and control: Theory and experiment," in *Proc. AIAA Guid., Navig., Control Conf.*, Hilton Head, SC, USA, 2007. (DOI not confirmed; cite without it.) | scilit, author PDF | Sec. 3: wind and aerodynamic effects |
| 11 | PX4 Autopilot, "Controller diagrams," PX4 User Guide (v1.17). [Online]. Available: https://docs.px4.io/v1.17/en/flight_stack/controller_diagrams.html | docs.px4.io (page text) | Sec. 3, 4: industry cascaded P/PID architecture with clamping anti-windup |
| 12 | Cyberbotics, "DJI Mavic 2 Pro model (Mavic2Pro.proto) and sample controllers (mavic2pro_patrol.py)," Webots R2025a source repository. [Online]. Available: https://github.com/cyberbotics/webots/tree/R2025a/projects/robots/dji/mavic | Files read directly from the local R2025a install; our worlds load the PROTO from this path. (The user-guide page renders client-side and could not be checked, so it is not cited.) | Sec. 6, 8: robot model |

## Notes for the literature review (Section 3)
- PX4 [11] uses the same structure as our Method B: a position P loop → velocity PID with
  clamping anti-windup → acceleration → attitude. Our contribution is not the structure.
  It is the measured comparison against the sample-style baseline inside Webots, and the
  verification and tuning findings (see docs/tuning_log.md).
- Minimum-snap [5] and motion primitives [7] are the research state of the art. We use the
  simpler minimum-jerk quintic [6] because a waypoint-to-waypoint segment needs only
  position, velocity and acceleration continuity.
