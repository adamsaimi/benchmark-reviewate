"""
Reporter module for generating benchmark evaluation reports.
"""
from typing import Dict, Any
from collections import defaultdict


class Reporter:
    """Handles report generation and formatting for benchmark results."""
    
    def __init__(self):
        pass
    
    @staticmethod
    def calculate_metrics(tp: float, fp: float, fn: float, 
                         total_comments: int = None, 
                         total_noise_score: float = None) -> Dict[str, float]:
        """
        Calculate precision, recall, and F1 score.
        
        Args:
            tp: True positives (weighted)
            fp: False positives (noise penalty)
            fn: False negatives (missed requirements)
            total_comments: Total number of agent comments
            total_noise_score: Sum of all noise scores
            
        Returns:
            Dictionary with precision, recall, and f1 metrics
        """
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        # Precision: 1.0 - average noise score
        # If avg noise = 0.30 → precision = 70%
        # If avg noise = 0.80 → precision = 20%
        if total_comments is not None and total_noise_score is not None and total_comments > 0:
            avg_noise = total_noise_score / total_comments
            precision = 1.0 - avg_noise
        else:
            # Fallback to old calculation if comment data not provided
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        return {"precision": precision, "recall": recall, "f1": f1}
    
    def print_report(self, scores: Dict[str, Any], 
                    token_usage: Dict[str, int] = None, 
                    noise_breakdown: Dict[str, int] = None) -> None:
        """
        Print comprehensive benchmark report.
        
        Args:
            scores: Dictionary containing overall, category, and difficulty scores
            token_usage: Optional token usage statistics
            noise_breakdown: Optional noise type breakdown
        """
        print("\n\n" + "=" * 60)
        print("          AI Code Review Benchmark Results          ")
        print("=" * 60)
        print("\n🎯 SIMPLE SCORING SYSTEM:")
        print("   • RECALL: % of ground truth requirements matched (weighted by severity)")
        print("   • PRECISION: Average comment quality (1.0 - average noise score)")
        
        # Overall Performance
        self._print_overall_performance(scores)
        
        # Noise Breakdown
        if noise_breakdown:
            self._print_noise_breakdown(noise_breakdown)
        
        # Performance by Category
        self._print_performance_by_category(scores)
        
        # Performance by Difficulty
        self._print_performance_by_difficulty(scores)
        
        # Token Usage Summary
        if token_usage:
            self._print_token_usage(token_usage)
        
        print("\n" + "=" * 60)
    
    def _print_overall_performance(self, scores: Dict[str, Any]) -> None:
        """Print overall performance metrics."""
        overall = self.calculate_metrics(
            scores['overall']['tp'], 
            scores['overall']['fp'], 
            scores['overall']['fn'],
            scores['overall'].get('total_comments'),
            scores['overall'].get('total_noise_score')
        )
        total_comments = scores['overall'].get('total_comments', 0)
        total_noise = scores['overall'].get('total_noise_score', 0)
        avg_noise = (total_noise / total_comments * 100) if total_comments > 0 else 0
        
        print("\n--- Overall Performance ---")
        print(f"  True Positives (Weighted):     {scores['overall']['tp']:.2f}")
        print(f"  False Negatives (Missed):      {scores['overall']['fn']:.2f}")
        print(f"  Total Agent Comments:          {total_comments}")
        print(f"  Average Noise per Comment:     {avg_noise:.1f}%")
        print(f"  ---------------------------")
        print(f"  Recall:     {overall['recall']:.2%}  ← Coverage of ground truth")
        print(f"  Precision:  {overall['precision']:.2%}  ← Comment quality (1 - avg noise)")
        print(f"  F1-Score:   {overall['f1']:.4f}")
    
    def _print_noise_breakdown(self, noise_breakdown: Dict[str, int]) -> None:
        """Print noise breakdown by type."""
        print("\n--- Noise Breakdown by Type ---")
        total_noise = sum(noise_breakdown.values())
        if total_noise > 0:
            sorted_noise = sorted(noise_breakdown.items(), key=lambda x: x[1], reverse=True)
            for noise_type, count in sorted_noise:
                percentage = (count / total_noise) * 100
                print(f"  {noise_type:<30} {count:>4} ({percentage:>5.1f}%)")
        else:
            print("  🎉 No significant noise detected!")
    
    def _print_performance_by_category(self, scores: Dict[str, Any]) -> None:
        """Print performance metrics by category."""
        print("\n--- Performance by Category ---")
        print(f"{'Category':<20} | {'Precision':>10} | {'Recall':>10} | {'F1-Score':>10} | "
              f"{'TP':>6} | {'Comments':>8} | {'Avg Noise':>9} | {'FN':>6}")
        print(f"{'-'*20} | {'-'*10} | {'-'*10} | {'-'*10} | "
              f"{'-'*6} | {'-'*8} | {'-'*9} | {'-'*6}")
        
        for category, counts in sorted(scores['category'].items()):
            metrics = self.calculate_metrics(
                counts['tp'], counts['fp'], counts['fn'],
                counts.get('total_comments'), counts.get('total_noise_score')
            )
            total_cmts = counts.get('total_comments', 0)
            avg_noise_pct = (counts.get('total_noise_score', 0) / total_cmts * 100) if total_cmts > 0 else 0
            print(f"{category:<20} | {metrics['precision']:>9.1%} | {metrics['recall']:>9.1%} | "
                  f"{metrics['f1']:>9.4f} | {counts['tp']:>6.2f} | {total_cmts:>8} | "
                  f"{avg_noise_pct:>8.1f}% | {counts['fn']:>6.2f}")
    
    def _print_performance_by_difficulty(self, scores: Dict[str, Any]) -> None:
        """Print performance metrics by difficulty."""
        print("\n--- Performance by Difficulty ---")
        print(f"{'Difficulty':<20} | {'Precision':>10} | {'Recall':>10} | {'F1-Score':>10} | "
              f"{'TP':>6} | {'Comments':>8} | {'Avg Noise':>9} | {'FN':>6}")
        print(f"{'-'*20} | {'-'*10} | {'-'*10} | {'-'*10} | "
              f"{'-'*6} | {'-'*8} | {'-'*9} | {'-'*6}")
        
        for difficulty, counts in sorted(scores['difficulty'].items()):
            metrics = self.calculate_metrics(
                counts['tp'], counts['fp'], counts['fn'],
                counts.get('total_comments'), counts.get('total_noise_score')
            )
            total_cmts = counts.get('total_comments', 0)
            avg_noise_pct = (counts.get('total_noise_score', 0) / total_cmts * 100) if total_cmts > 0 else 0
            print(f"{difficulty:<20} | {metrics['precision']:>9.1%} | {metrics['recall']:>9.1%} | "
                  f"{metrics['f1']:>9.4f} | {counts['tp']:>6.2f} | {total_cmts:>8} | "
                  f"{avg_noise_pct:>8.1f}% | {counts['fn']:>6.2f}")
    
    def _print_token_usage(self, token_usage: Dict[str, int]) -> None:
        """Print token usage summary."""
        print("\n--- Token Usage Summary ---")
        print(f" Prompt Tokens = {token_usage['input_tokens']:,}, "
              f"Completion Tokens = {token_usage['output_tokens']:,}")
