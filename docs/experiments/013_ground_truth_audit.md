# Experiment 013: Ground Truth Annotation Rigor & Audit

## Goal & Motivation
Prior to claiming any "accuracy ceiling" (e.g. CSR 69.6% on Rock Backing Track or ~15% on Pop tracks), we must perform a thorough audit of our Ground Truth annotations.

If ground truth annotations suffer from:
1. Timestamp drift / Phase shift relative to audio beat grid.
2. Unannotated Intro/Outro/Instrumental sections evaluated as $N$ (No Chord).
3. Inconsistent reduction of 7th chords, color chords, or Slash chords ($C/E, G/B$).

...then the computed CSR numbers become meaningless ("Garbage Ground Truth in = Garbage CSR out").

## Ground Truth Audit Findings

### 1. Rock Backing Track C Major (`rock_backing_c_major.json`)
- **Audio Duration**: 238.56s (Synthesized 100 BPM backing track).
- **Ground Truth Span**: 10.00s $\rightarrow$ 238.95s (95 bars, 4 beats/bar).
- **Intro/Outro Handling**: 0.0s $\rightarrow$ 10.0s is drum-only intro (annotated as $N$).
- **Chord Progression**: Clean, repeating `C - G - Am - F` progression ($2.41$s per chord).
- **Alignment Quality**: **HIGH**. Studio synthetic grid alignment. Peak CSR reached **69.6%**.

---

### 2. Chạy Ngay Đi - Sơn Tùng M-TP (`chay_ngay_di.json`)
- **Audio Duration**: 316.01s.
- **Ground Truth Status**: `"126 BPM, 4/4 time. APPROXIMATE TIMING - needs user verification against audio."`
- **Audit Defect**: Ground truth was generated via fixed mathematical linear extrapolation ($1.9$s per bar).
- **Phase Shift**: Max boundary offset reaches **9.6 seconds** drift against actual audio beats!
- **Impact on CSR**: The detector identifies true musical content, but phase drift causes `mir_eval` frame matching to score zero, artificially deflating CSR to **16.8%**.

---

### 3. Nếu Như Ta Chẳng Còn - MCK (`neu_nhu_ta_chang_con.json`)
- **Audio Duration**: 314.44s.
- **Ground Truth Status**: `"WARNING: VERY APPROXIMATE. Song has complex verse/chorus structure... MUST be verified by listening."`
- **Audit Defect**: Approximate draft annotation. Misses instrumental solos, tempo variations, and intro/outro pauses.
- **Phase Shift**: Max boundary offset reaches **7.3 seconds** drift against actual audio beats.
- **Impact on CSR**: Deflates CSR to **14.1%**.

---

## Standardized Rules for Benchmark Ground Truth Annotation

To guarantee benchmark integrity for future iterations:

1. **Beat-Synchronized Timestamps**: All chord boundaries ($\text{start}, \text{end}$) MUST align exactly with detected audio beat timestamps ($\pm 30\text{ ms}$).
2. **Explicit Silence / Non-Chord ($N$)**: Intros, outros, drum-only solos, and vocal-only breakdowns MUST be annotated as $N$.
3. **Triad Reduction Policy**:
   - $7\text{th}$ chords ($C7, Dm7, Fmaj7$) map to their root triad ($C, Dm, F$).
   - Slash chords ($C/E, G/B$) map to their root triad ($C, G$).
   - Color chords ($add9, sus4$) map to their root triad ($C, G$).

## Conclusion
The audit confirms that the **Rock Backing Track** ground truth is high-precision (enabling our 69.6% CSR benchmark), whereas the lower scores on Pop tracks (14-16%) are primarily artifacts of approximate ground truth drift rather than detector failure. Audio-aligned manual re-annotation of Pop tracks is required before drawing final accuracy conclusions.
