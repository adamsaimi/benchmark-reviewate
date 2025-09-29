# Scoring Methodology

This document outlines the formal methodology used to score the performance of an AI code review agent against this benchmark. The process is designed to be objective, reproducible, and based on standard industry metrics for classification tasks.

## 1. Foundational Definitions

To formalize the scoring process, we begin with a few key definitions.

* **Benchmark Case ($k$)**: A single pull request in the benchmark, identified by a unique `issue_id`. The set of all cases is denoted by $K$.
* **Ground Truth Set ($G_k$)**: For each case $k$, this is the definitive set of pre-defined, correct reviews.
    $$G_k = \{g_1, g_2, \dots, g_m\}$$
    Each review $g_i$ contains the location (`file`, `line`) and text (`comment`) of an intended flaw.
* **Agent-Generated Set ($A_k$)**: For each case $k$, this is the set of all reviews produced by the agent being tested.
    $$A_k = \{a_1, a_2, \dots, a_n\}$$
    Each review $a_j$ contains the location and text of a comment made by the agent.

## 2. The Matching Algorithm

To evaluate the agent's performance, we must determine which of its generated reviews correspond to the ground truth. A generated review $a_j$ is considered a **match** for a ground truth review $g_i$ if and only if they align in both location and meaning.

### a) Location Match
A review must be in the correct location to be considered correct. We define a location match function, $Match_{loc}$, with a line tolerance $\tau$ (e.g., $\tau=2$) to account for minor variations in diffs.

$$Match_{loc}(g_i, a_j) \iff (g_i.\text{file} = a_j.\text{file}) \land (|g_i.\text{line} - a_j.\text{line}| \le \tau)$$

### b) Semantic Match
If the locations match, we then use a large language model (LLM) as a neutral evaluator to determine if the agent's comment identifies the same underlying flaw as the ground truth comment. This is our semantic match function, $Match_{sem}$.

$$Match_{sem}(g_i, a_j) \iff \text{LLM_Validate}(g_i.\text{comment}, a_j.\text{comment}) = \text{true}$$

### c) Overall Match
A definitive match, $Match(g_i, a_j)$, requires both conditions to be met:

$$Match(g_i, a_j) = Match_{loc}(g_i, a_j) \land Match_{sem}(g_i, a_j)$$

## 3. Classification of Reviews

For each benchmark case $k$, we classify the reviews by finding the maximum number of unique pairs between the ground truth set $G_k$ and the agent's set $A_k$. Based on this matching, we count three outcomes:

* **True Positive (TP)**: A ground truth review that is successfully matched with an agent's review. This is a **correct finding** by the agent.
* **False Negative (FN)**: A ground truth review that was **not matched** by any agent review. This is a **missed flaw**.
* **False Positive (FP)**: An agent's review that was **not matched** to any ground truth review. This is an **incorrect or irrelevant finding**.

## 4. Aggregation and Performance Metrics

The counts from each individual case are summed to produce benchmark-wide totals for $TP$, $FP$, and $FN$. From these totals, we calculate the three standard performance metrics.

### Precision
Precision measures the reliability of the agent's reviews. A high precision means the agent generates very few incorrect suggestions (low noise).

$$\text{Precision} = \frac{TP}{TP + FP}$$

### Recall
Recall measures the thoroughness of the agent's review. A high recall means the agent finds most of the existing flaws (high coverage).

$$\text{Recall} = \frac{TP}{TP + FN}$$

### F1-Score
The F1-Score is the harmonic mean of Precision and Recall. It provides a single, balanced metric of the agent's overall effectiveness, punishing models that are extremely biased towards either high precision or high recall.

$$F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}} = \frac{2 \cdot TP}{2 \cdot TP + FP + FN}$$

## 5. Stratified Analysis

Beyond the overall score, we provide a more granular analysis by applying the same scoring methodology to subsets of the benchmark. This allows for performance evaluation across different dimensions:

* **By Category**: Performance on `Security`, `Performance`, `Business Logic`, etc.
* **By Difficulty**: Performance on `Easy`, `Medium`, and `Hard` flaws.
* **By Context Size**: Performance on small, isolated changes versus large, complex pull requests.

This stratified analysis provides deep insights into the specific strengths and weaknesses of the code review agent being tested.