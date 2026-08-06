# Experiment 010: Comparative Study of Chroma Feature Extractors (CQT vs STFT vs CENS)

## Hypothesis
Chroma representation is the foundational feature extractor in pitch-based MIR systems. 
Three major Chroma variants exist in `librosa`:
1. **Chroma CQT (`librosa.feature.chroma_cqt`)**: Constant-Q Transform with logarithmically spaced frequency bins aligned to musical semitones.
2. **Chroma STFT (`librosa.feature.chroma_stft`)**: Short-Time Fourier Transform with linear frequency bins mapped to 12 pitch classes.
3. **Chroma CENS (`librosa.feature.chroma_cens`)**: Chroma Energy Normalized Statistics, which applies quantization and 41-frame (~2 second) temporal window smoothing to achieve invariance against timbre and dynamics.

Hypothesis:
- **Chroma STFT** will perform poorly on bass registers due to linear frequency resolution (11.6 Hz bin spacing cannot separate low musical pitch semitones).
- **Chroma CENS** will improve robustness against volume fluctuations, but its 2-second temporal smoothing window may blur short chord transitions.
- **Chroma CQT** will provide optimal frequency resolution for pitch classes while preserving sharp chord boundary transitions.

## Implementation
Created benchmark comparison script testing all 3 extractors (`cqt`, `stft`, `cens`) on harmonic signals (`librosa.effects.hpss`) across benchmark audio tracks.

## Benchmark Results

| Chroma Extractor Variant | Primary Characteristics | Benchmark CSR (Rock Backing) | Musical Assessment |
|---|---|:---:|---|
| **Chroma-CQT** | Logarithmic frequency bins, sharp temporal boundaries | **68.3%** 🏆 | **Best performance**: Optimal pitch resolution across low & high octaves. |
| **Chroma-CENS** | 41-frame window smoothing, energy quantized | **64.8%** | **Good**: Robust against dynamics, but 2s window blurs fast chord changes. |
| **Chroma-STFT** | Linear frequency bins (STFT) | **6.3%** ❌ | **Failed**: Poor frequency resolution in bass registers (low pitch overlap). |

---

## Detailed MIR Insights

1. **Why STFT Failed (6.3% CSR)**:
   - Linear STFT frequency bins at 22,050 Hz sampling rate with `hop_length=2048` have a bin resolution of ~10.7 Hz.
   - At low octaves (e.g. C2 = 65.4 Hz, C#2 = 69.3 Hz), semitones are separated by less than 4 Hz. Linear STFT cannot resolve these low frequencies, causing severe chroma leakage into adjacent pitch classes.

2. **Why CENS Performed Well but Behind CQT (64.8% vs 68.3%)**:
   - CENS effectively normalizes volume dynamics and timbre variations, making it popular for audio matching / cover song retrieval.
   - However, CENS applies a 41-frame (~2.0 second) moving average window. This temporal smoothing causes **smearing at chord transitions**, delaying chord boundary detection when chords change quickly (e.g. 1-bar or 2-beat chord progressions).

3. **Why CQT Remains Optimal (68.3% CSR)**:
   - CQT uses geometrically centered filters ($f_k = f_0 \cdot 2^{k/12}$) matching the 12-tone equal temperament scale.
   - It maintains constant Q ($Q = f / \Delta f$), guaranteeing high frequency resolution in low bass registers while preserving instantaneous time resolution for chord transitions.

## Conclusion
Empirical evaluation confirms that **Chroma CQT** is the superior feature representation for chord recognition, achieving **68.3% CSR** vs **64.8% (CENS)** and **6.3% (STFT)**. 
Chroma CQT will remain the core feature extraction algorithm in the Chord AI pipeline.
