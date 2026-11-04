# Sources and attribution

- **Starting portfolio:** Alex Chilton, v54 of
  https://www.kaggle.com/code/alexchilton/22-57-lb-verified-three-task-portfolio
  Independently rechecked here: 22.79549878 with our reference costs and declared
  salt. His notebook's historic slug is not its current score.
- **Inverse square root:** busyaprime/Akmal Xodarev's updated 63-qubit circuit,
  unchanged, from Alex's public output. Original:
  https://www.kaggle.com/code/busyaprime/lb-22-72431-22x-cheaper-than-google-s-circuits
  https://www.kaggle.com/datasets/busyaprime/33-qcc-v8-members
  His two rebuilt regions are on mrmeows' 63-qubit hybrid circuit; earlier
  lineage includes Phuc Thai/DePie, Dmitrii Gluzdov and marsyas. Apache-2.0.
- **Selected DQI, new in v12:** SomeJoint/Agniv Banerjee's 889-qubit decoder,
  unchanged, from the public output and source description:
  https://www.kaggle.com/code/somejoint/quantum-circuits-22-77-local-gm-889-qubit-dqi
  Their paired high-component charts, inverse19 reverse, streamed synthesis
  divide and retimed heads are their work. This replaces v11's Mudit
  Chaturvedi/muchat007 895-qubit decoder:
  https://www.kaggle.com/code/muchat007/895q-streamed-decoder-measured-node-choices
  On SomeJoint's streamed conversion/replay and their team's arithmetic.
  Their credited lineage includes GPT-6 Astra Pro, Ahmed Berat Ozer's v9
  narrowing, Alex Chilton's Schur design on jday96314's QuantumAI,
  mrmeows/Ozer/manwithacat mask projection, Dmitrii Gluzdov, ViberTeam and
  Phuc Thai. The original jday96314 repository has no explicit license; we do
  not redistribute its source or assert a blanket license over that history.
  Only the already-public compiled circuit is packaged here.
- **Chemistry factorization and words:** SomeJoint's public R8/B143/C60 model:
  https://www.kaggle.com/datasets/somejoint/qcc-our-chemistry-b143-c60-xor2
  Lineage: Michael Rustad, Ahmed Berat Ozer, busyaprime, lightningv08/Vladislav
  Lavrentev and mrmeows. The public starting coefficient file is Dmitrii
  Gluzdov's 29 October output, obtained through Alex's portfolio:
  https://www.kaggle.com/code/dmitriigluzdov/quantum-circuit-compilation-from-source
  Its angle_words, U, tree_edges, brot, H1_I and Hsym_lower are unchanged.
- **All 15 ANGLE circuits:** Heliosli's v31_mc14 dataset release, unchanged:
  https://www.kaggle.com/datasets/heliosli/qcc-circuits-live
  https://www.kaggle.com/code/heliosli/the-dataset-is-public-now-enjoy
  The compiler design is on SomeJoint's chemistry and kernel relations. We
  did not synthesize these production circuit binaries. Their exact emitter
  source was not included in that release; this notebook authenticates and
  verifies them, and does not claim a byte-for-byte source rebuild.
- **Our selected model update:** Ahmed Berat Ozer, float64 constrained joint
  coefficient fitting, implicit elimination of the gap scale, an augmented
  coefficient rotation and selected production W/H2_I delta. The augmented
  Gram gauge formulation is credited to Kirill Tymchishin and mrmeows:
  https://www.kaggle.com/code/kirilltym/quantum-circuits-exact-gauge-5-word-qrom
  Optional CUDA search sources and native numerical records are included.
- **Reachable-state phase certificate:** adapted from mrmeows' Apache-2.0
  bit-packed audit_affine_hmr.py in the public cost-first source package:
  https://www.kaggle.com/datasets/mrmeows/qcc-1375-open-circuits
  Our adaptation initializes the two official traversal domains and binds the
  certificates to the selected binaries. It checks every valid address and
  every independent HMR outcome. It is not an arbitrary-target XOR proof.
- **Official ANGLE ruling:** Tanuj Khattar, Competition Host:
  https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/discussion/753092
  The circuits need only work on the reachable forward/reverse word states.
- **Organizers:** Google Quantum AI / Qualtran, task definitions, Kickmix,
  reference Hamiltonian and unchanged official verifiers.

Our scripts are Apache-2.0. Each upstream component retains its own terms.
No ownership of upstream algorithms, binaries or competition data is claimed.
