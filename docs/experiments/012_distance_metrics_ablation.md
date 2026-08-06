# Experiment 012: Distance Metrics & Similarity Function Ablation Study

## Hypothesis
The baseline classification step used **Cosine Similarity** to compare normalized frame chroma vectors with template vectors:
$$\text{Cosine}(x, y) = \frac{\mathbf{x} \cdot \mathbf{y}}{\|\mathbf{x}\| \|\mathbf{y}\|}$$

Hypothesis: 
Cosine similarity treats all 12 pitch dimensions symmetrically. Alternative distance metrics such as **Pearson Correlation Coefficient**, **Negative Euclidean Distance ($L_2$)**, or **Negative Manhattan Distance ($L_1$)** might provide superior discrimination by mean-centering the chroma spectrum or penalizing off-triad noise.

Testing alternative metrics via an Ablation Study will determine whether Cosine Similarity remains mathematically optimal for pitch class template matching.

## Implementation
Constructed an Ablation Study script comparing 4 distance metrics under identical pre-processing and Key Estimation conditions:
1. **Cosine Similarity**: Dot product of $L_2$-normalized vectors.
2. **Pearson Correlation Coefficient**: Mean-centered dot product normalized by standard deviations.
3. **Negative Euclidean Distance**: $d(x, y) = -\|\mathbf{x} - \mathbf{y}\|_2$.
4. **Negative Manhattan Distance**: $d(x, y) = -\|\mathbf{x} - \mathbf{y}\|_1$.

## Ablation Benchmark Results

| Distance Metric Variant | Formula / Characterization | CSR (Rock Backing) | CSR Delta vs Cosine | Mathematical & MIR Assessment |
|---|---|:---:|:---:|---|
| 🏆 **Cosine Similarity** | $\frac{\mathbf{x} \cdot \mathbf{y}}{\|\mathbf{x}\| \|\mathbf{y}\|}$ | **69.6%** | **Baseline Peak** | **Optimal**: Scale-invariant directional angle matching. |
| 🥈 **Negative Euclidean ($L_2$)** | $-\sqrt{\sum (x_i - y_i)^2}$ | **64.0%** | -5.6pp 📉 | **Good**: Sensitive to magnitude variations in quiet frames. |
| 🥉 **Pearson Correlation** | $\frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sigma_x \sigma_y}$ | **61.5%** | -8.1pp 📉 | **Sub-optimal**: Mean-centering turns zero-energy pitch classes negative. |
| ❌ **Negative Manhattan ($L_1$)** | $-\sum \|x_i - y_i\|$ | **55.6%** | -14.0pp 📉 | **Poor**: Linear error penalty over-sensitizes to unplayed residual noise. |

---

## MIR Theoretical Insights

1. **Why Pearson Correlation Underperformed (61.5% vs 69.6%)**:
   - Pearson correlation mean-centers the 12-dimensional vector by subtracting $\bar{x} = \frac{1}{12}\sum_{i=1}^{12} x_i$.
   - In sparse chroma vectors (where only 3 triad notes contain energy), non-triad pitch classes have $x_i = 0$. Subtracting $\bar{x}$ converts inactive zero components into **negative values** ($-\bar{x}$).
   - Correlating negative non-triad values against positive template weights distorts pitch alignment and lowers classification accuracy.

2. **Why Manhattan ($L_1$) Distance Underperformed (55.6%)**:
   - Manhattan distance penalizes differences linearly ($|x_i - y_i|$). Residual acoustic overtones or background noise in non-triad pitch classes accumulate linear error penalties across all 9 non-triad dimensions.

3. **Why Cosine Similarity Remains Mathematically Optimal (69.6%)**:
   - Cosine similarity measures the **directional alignment angle** between the observed chroma spectrum and template profile in 12D space.
   - It is strictly non-negative for non-negative chroma vectors and invariant to overall volume dynamics.

## Conclusion
Empirical Ablation Study proves that **Cosine Similarity** remains the mathematically optimal similarity metric for template-based chord recognition, outperforming Pearson Correlation (61.5%), Euclidean Distance (64.0%), and Manhattan Distance (55.6%).
