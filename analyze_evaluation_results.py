"""
Analyze evaluation results and generate comprehensive comparison reports.

This script processes evaluation_results.json and generates:
- Comparison tables (multimodal vs. baseline, ablation studies)
- Statistical analysis
- Performance by map and weather
- Research contribution analysis
"""

import json
import os
from typing import Dict, List, Any
from collections import defaultdict

def load_results(filepath: str = "evaluation_results.json") -> Dict:
    """Load evaluation results from JSON file."""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found. Run evaluation_runner.py first.")
        return None
    
    with open(filepath, "r") as f:
        return json.load(f)


def analyze_by_mode(results: Dict) -> Dict[str, Any]:
    """Analyze results grouped by evaluation mode."""
    by_mode = defaultdict(list)
    
    for result in results.get("results", []):
        if result.get("success"):
            mode = result.get("mode", "unknown")
            by_mode[mode].append(result)
    
    analysis = {}
    for mode, mode_results in by_mode.items():
        if not mode_results:
            continue
        
        safety_rates = [r.get("metrics", {}).get("safety_rate", 0) for r in mode_results]
        collision_counts = [r.get("metrics", {}).get("collisions", 0) for r in mode_results]
        avg_fps = [r.get("metrics", {}).get("avg_fps", 0) for r in mode_results]
        
        analysis[mode] = {
            "count": len(mode_results),
            "avg_safety_rate": sum(safety_rates) / len(safety_rates) if safety_rates else 0,
            "avg_collisions": sum(collision_counts) / len(collision_counts) if collision_counts else 0,
            "avg_fps": sum(avg_fps) / len(avg_fps) if avg_fps else 0,
            "min_safety_rate": min(safety_rates) if safety_rates else 0,
            "max_safety_rate": max(safety_rates) if safety_rates else 0,
        }
    
    return analysis


def compare_modes(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Compare multimodal vs. baseline and ablation studies."""
    comparisons = {}
    
    multimodal = analysis.get("multimodal", {})
    baseline = analysis.get("baseline", {})
    vision_only = analysis.get("vision_only", {})
    audio_only = analysis.get("audio_only", {})
    
    # Multimodal vs. Baseline
    if multimodal and baseline:
        comparisons["multimodal_vs_baseline"] = {
            "safety_rate_improvement": multimodal["avg_safety_rate"] - baseline["avg_safety_rate"],
            "collision_reduction": baseline["avg_collisions"] - multimodal["avg_collisions"],
            "relative_improvement": ((multimodal["avg_safety_rate"] - baseline["avg_safety_rate"]) / baseline["avg_safety_rate"] * 100) if baseline["avg_safety_rate"] > 0 else 0,
        }
    
    # Ablation studies
    if multimodal and vision_only and audio_only:
        comparisons["ablation_studies"] = {
            "multimodal_safety_rate": multimodal["avg_safety_rate"],
            "vision_only_safety_rate": vision_only["avg_safety_rate"],
            "audio_only_safety_rate": audio_only["avg_safety_rate"],
            "vision_contribution": multimodal["avg_safety_rate"] - audio_only["avg_safety_rate"],
            "audio_contribution": multimodal["avg_safety_rate"] - vision_only["avg_safety_rate"],
            "synergy_effect": multimodal["avg_safety_rate"] - (vision_only["avg_safety_rate"] + audio_only["avg_safety_rate"]) / 2,
        }
    
    return comparisons


def analyze_by_map_and_weather(results: Dict) -> Dict[str, Any]:
    """Analyze results by map and weather conditions."""
    by_map = defaultdict(lambda: defaultdict(list))
    
    for result in results.get("results", []):
        if result.get("success"):
            map_name = result.get("map", "unknown")
            weather = result.get("weather", "unknown")
            by_map[map_name][weather].append(result)
    
    analysis = {}
    for map_name, weather_dict in by_map.items():
        analysis[map_name] = {}
        for weather, weather_results in weather_dict.items():
            if not weather_results:
                continue
            
            safety_rates = [r.get("metrics", {}).get("safety_rate", 0) for r in weather_results]
            analysis[map_name][weather] = {
                "count": len(weather_results),
                "avg_safety_rate": sum(safety_rates) / len(safety_rates) if safety_rates else 0,
                "min_safety_rate": min(safety_rates) if safety_rates else 0,
                "max_safety_rate": max(safety_rates) if safety_rates else 0,
            }
    
    return analysis


def generate_report(results: Dict) -> str:
    """Generate a comprehensive evaluation report."""
    report = []
    report.append("=" * 80)
    report.append("COMPREHENSIVE EVALUATION REPORT")
    report.append("=" * 80)
    report.append("")
    
    # By mode analysis
    mode_analysis = analyze_by_mode(results)
    report.append("PERFORMANCE BY MODE")
    report.append("-" * 80)
    for mode, stats in mode_analysis.items():
        report.append(f"\n{mode.upper()}:")
        report.append(f"  Average Safety Rate: {stats['avg_safety_rate']:.2f}%")
        report.append(f"  Average Collisions: {stats['avg_collisions']:.2f}")
        report.append(f"  Average FPS: {stats['avg_fps']:.2f}")
        report.append(f"  Safety Rate Range: {stats['min_safety_rate']:.2f}% - {stats['max_safety_rate']:.2f}%")
    
    # Comparisons
    comparisons = compare_modes(mode_analysis)
    report.append("\n" + "=" * 80)
    report.append("COMPARISONS")
    report.append("=" * 80)
    
    if "multimodal_vs_baseline" in comparisons:
        comp = comparisons["multimodal_vs_baseline"]
        report.append("\nMULTIMODAL vs. CARLA AUTOPILOT (Baseline):")
        report.append(f"  Safety Rate Improvement: {comp['safety_rate_improvement']:+.2f}%")
        report.append(f"  Collision Reduction: {comp['collision_reduction']:.2f}")
        report.append(f"  Relative Improvement: {comp['relative_improvement']:+.2f}%")
    
    if "ablation_studies" in comparisons:
        abl = comparisons["ablation_studies"]
        report.append("\nABLATION STUDIES:")
        report.append(f"  Multimodal Safety Rate: {abl['multimodal_safety_rate']:.2f}%")
        report.append(f"  Vision-Only Safety Rate: {abl['vision_only_safety_rate']:.2f}%")
        report.append(f"  Audio-Only Safety Rate: {abl['audio_only_safety_rate']:.2f}%")
        report.append(f"  Vision Contribution: {abl['vision_contribution']:+.2f}%")
        report.append(f"  Audio Contribution: {abl['audio_contribution']:+.2f}%")
        report.append(f"  Synergy Effect: {abl['synergy_effect']:+.2f}%")
    
    # By map and weather
    map_weather_analysis = analyze_by_map_and_weather(results)
    report.append("\n" + "=" * 80)
    report.append("PERFORMANCE BY MAP AND WEATHER")
    report.append("=" * 80)
    
    for map_name, weather_dict in map_weather_analysis.items():
        report.append(f"\n{map_name}:")
        for weather, stats in weather_dict.items():
            report.append(f"  {weather}: {stats['avg_safety_rate']:.2f}% safety rate")
    
    report.append("\n" + "=" * 80)
    report.append("RESEARCH CONTRIBUTION SUMMARY")
    report.append("=" * 80)
    report.append("\nKey Findings:")
    
    if "multimodal_vs_baseline" in comparisons:
        comp = comparisons["multimodal_vs_baseline"]
        if comp['safety_rate_improvement'] > 0:
            report.append(f"  ✓ Multimodal approach improves safety by {comp['safety_rate_improvement']:.2f}% over baseline")
        else:
            report.append(f"  ✗ Multimodal approach shows {abs(comp['safety_rate_improvement']):.2f}% lower safety than baseline")
    
    if "ablation_studies" in comparisons:
        abl = comparisons["ablation_studies"]
        report.append(f"  ✓ Vision contributes {abl['vision_contribution']:.2f}% to safety")
        report.append(f"  ✓ Audio contributes {abl['audio_contribution']:.2f}% to safety")
        if abl['synergy_effect'] > 0:
            report.append(f"  ✓ Positive synergy effect: {abl['synergy_effect']:.2f}%")
        else:
            report.append(f"  ✗ Negative synergy effect: {abl['synergy_effect']:.2f}%")
    
    return "\n".join(report)


def main():
    """Main analysis function."""
    results = load_results()
    if not results:
        return
    
    # Generate report
    report = generate_report(results)
    print(report)
    
    # Save report
    with open("evaluation_report.txt", "w") as f:
        f.write(report)
    
    print("\n" + "=" * 80)
    print("Report saved to: evaluation_report.txt")
    print("=" * 80)


if __name__ == "__main__":
    main()

