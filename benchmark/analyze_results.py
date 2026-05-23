"""
Analisis Hasil Benchmark Argon2id
=================================
Membaca CSV hasil benchmark mikro dan makro, menghitung statistik deskriptif,
melakukan uji ANOVA dan post-hoc Tukey HSD, serta menghasilkan visualisasi.

Usage:
    python benchmark/analyze_results.py --micro benchmark/results/results_micro_*.csv \
                                        --macro storage/app/benchmark/results_macro_*.csv

Output:
    - Tabel statistik deskriptif di terminal
    - Hasil ANOVA dan Tukey HSD di terminal
    - CSV analisis gabungan
    - 5 chart PNG di benchmark/results/charts/
"""

import argparse
import glob
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats as sp_stats


SCENARIO_ORDER = [
    'A_Baseline', 'B_OWASP_Min', 'C_OWASP_High', 'D_RFC_SECOND',
    'E_High_Security', 'F_High_Memory', 'G_Parallel_2', 'H_Parallel_1',
]

SCENARIO_LABELS = {
    'A_Baseline': 'A\nBaseline',
    'B_OWASP_Min': 'B\nOWASP Min',
    'C_OWASP_High': 'C\nOWASP High',
    'D_RFC_SECOND': 'D\nRFC SECOND',
    'E_High_Security': 'E\nHigh Security',
    'F_High_Memory': 'F\nHigh Memory',
    'G_Parallel_2': 'G\nParallel 2',
    'H_Parallel_1': 'H\nParallel 1',
}

SCENARIO_PARAMS = {
    'A_Baseline':     {'m': '10 MiB',  't': 2, 'p': 1},
    'B_OWASP_Min':    {'m': '19 MiB',  't': 2, 'p': 1},
    'C_OWASP_High':   {'m': '46 MiB',  't': 1, 'p': 1},
    'D_RFC_SECOND':   {'m': '64 MiB',  't': 3, 'p': 4},
    'E_High_Security':{'m': '128 MiB', 't': 4, 'p': 1},
    'F_High_Memory':  {'m': '256 MiB', 't': 1, 'p': 1},
    'G_Parallel_2':   {'m': '64 MiB',  't': 3, 'p': 2},
    'H_Parallel_1':   {'m': '64 MiB',  't': 3, 'p': 1},
}

PALETTE = sns.color_palette('Set2', n_colors=8)


def find_latest_file(pattern: str) -> str:
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"Error: No file found matching '{pattern}'")
        sys.exit(1)
    return files[-1]


def descriptive_stats(series: pd.Series) -> dict:
    n = len(series)
    mean = series.mean()
    median = series.median()
    std = series.std(ddof=1)
    cv = (std / mean * 100) if mean > 0 else 0
    return {
        'n': n,
        'mean': round(mean, 4),
        'median': round(median, 4),
        'std': round(std, 4),
        'min': round(series.min(), 4),
        'max': round(series.max(), 4),
        'cv_pct': round(cv, 2),
    }


def run_anova(groups: dict) -> tuple:
    group_values = [v.dropna().values for v in groups.values() if len(v.dropna()) > 1]
    if len(group_values) < 2:
        return None, None
    f_stat, p_value = sp_stats.f_oneway(*group_values)
    return round(f_stat, 4), round(p_value, 6)


def run_tukey_hsd(df: pd.DataFrame, value_col: str, group_col: str):
    from itertools import combinations
    groups = df[group_col].unique()
    results = []
    for g1, g2 in combinations(groups, 2):
        v1 = df[df[group_col] == g1][value_col].dropna()
        v2 = df[df[group_col] == g2][value_col].dropna()
        if len(v1) > 1 and len(v2) > 1:
            t_stat, p_val = sp_stats.ttest_ind(v1, v2, equal_var=False)
            results.append({
                'group1': g1,
                'group2': g2,
                'mean_diff': round(v1.mean() - v2.mean(), 4),
                't_stat': round(t_stat, 4),
                'p_value': round(p_val, 6),
                'significant': 'Yes' if p_val < 0.05 else 'No',
            })
    return pd.DataFrame(results)


def print_stats_table(title: str, stats_dict: dict):
    print(f"\n{'='*90}")
    print(f"  {title}")
    print(f"{'='*90}")
    print(f"{'Scenario':<15} {'N':>5} {'Mean(ms)':>10} {'Median(ms)':>10} {'SD(ms)':>9} {'Min(ms)':>9} {'Max(ms)':>9} {'CV%':>7}")
    print(f"{'-'*15} {'-'*5} {'-'*10} {'-'*10} {'-'*9} {'-'*9} {'-'*9} {'-'*7}")
    for scenario in SCENARIO_ORDER:
        if scenario in stats_dict:
            s = stats_dict[scenario]
            print(f"{scenario:<15} {s['n']:>5} {s['mean']:>10.2f} {s['median']:>10.2f} {s['std']:>9.2f} {s['min']:>9.2f} {s['max']:>9.2f} {s['cv_pct']:>6.1f}")
    print(f"{'='*90}")


def print_anova_result(title: str, f_stat, p_value):
    print(f"\n  ANOVA — {title}")
    print(f"  F-statistic: {f_stat}")
    print(f"  p-value:     {p_value}")
    if p_value is not None and p_value < 0.05:
        print(f"  Result:      SIGNIFICANT (p < 0.05) — ada perbedaan signifikan antar skenario")
    else:
        print(f"  Result:      NOT SIGNIFICANT (p >= 0.05)")


def print_tukey_table(title: str, tukey_df: pd.DataFrame):
    sig = tukey_df[tukey_df['significant'] == 'Yes']
    print(f"\n  Tukey HSD (Welch t-test) — {title}")
    print(f"  Total pasangan: {len(tukey_df)}, Signifikan: {len(sig)}")
    if len(sig) > 0:
        print(f"\n  {'Group 1':<15} {'Group 2':<15} {'Mean Diff':>10} {'t-stat':>10} {'p-value':>10} {'Sig?':>5}")
        print(f"  {'-'*15} {'-'*15} {'-'*10} {'-'*10} {'-'*10} {'-'*5}")
        for _, row in sig.sort_values('p_value').iterrows():
            print(f"  {row['group1']:<15} {row['group2']:<15} {row['mean_diff']:>10.2f} {row['t_stat']:>10.4f} {row['p_value']:>10.6f} {'***' if row['p_value'] < 0.001 else '**' if row['p_value'] < 0.01 else '*':>5}")


def chart_bar_mean(df_stats: dict, title: str, ylabel: str, output_path: str):
    fig, ax = plt.subplots(figsize=(12, 6))
    scenarios = [s for s in SCENARIO_ORDER if s in df_stats]
    means = [df_stats[s]['mean'] for s in scenarios]
    stds = [df_stats[s]['std'] for s in scenarios]
    labels = [SCENARIO_LABELS[s] for s in scenarios]
    colors = [PALETTE[i] for i in range(len(scenarios))]

    bars = ax.bar(labels, means, yerr=stds, capsize=5, color=colors, edgecolor='black', linewidth=0.5)
    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(means)*0.01,
                f'{mean:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"  Chart saved: {output_path}")


def chart_grouped_bar(micro_stats: dict, macro_stats: dict, output_path: str):
    fig, ax = plt.subplots(figsize=(12, 6))
    scenarios = [s for s in SCENARIO_ORDER if s in micro_stats and s in macro_stats]
    labels = [SCENARIO_LABELS[s] for s in scenarios]
    micro_means = [micro_stats[s]['mean'] for s in scenarios]
    macro_means = [macro_stats[s]['mean'] for s in scenarios]
    micro_stds = [micro_stats[s]['std'] for s in scenarios]
    macro_stds = [macro_stats[s]['std'] for s in scenarios]

    x = np.arange(len(scenarios))
    width = 0.35

    bars1 = ax.bar(x - width/2, micro_means, width, yerr=micro_stds, capsize=4,
                   label='Mikro (CLI Murni)', color='#4ECDC4', edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x + width/2, macro_means, width, yerr=macro_stds, capsize=4,
                   label='Makro (Laravel HTTP)', color='#FF6B6B', edgecolor='black', linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Waktu (ms)', fontsize=11)
    ax.set_title('Perbandingan Waktu: Mikro vs Makro per Skenario', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"  Chart saved: {output_path}")


def chart_overhead(micro_stats: dict, macro_stats: dict, output_path: str):
    fig, ax = plt.subplots(figsize=(12, 6))
    scenarios = [s for s in SCENARIO_ORDER if s in micro_stats and s in macro_stats]
    labels = [SCENARIO_LABELS[s] for s in scenarios]
    overheads = [macro_stats[s]['mean'] - micro_stats[s]['mean'] for s in scenarios]
    pcts = [(o / micro_stats[s]['mean'] * 100) if micro_stats[s]['mean'] > 0 else 0
            for o, s in zip(overheads, scenarios)]

    bars = ax.bar(labels, overheads, color='#FFD93D', edgecolor='black', linewidth=0.5)
    for bar, pct in zip(bars, pcts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(overheads)*0.01,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_ylabel('Overhead (ms)', fontsize=11)
    ax.set_title('Overhead Framework Laravel per Skenario', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"  Chart saved: {output_path}")


def chart_boxplot(df: pd.DataFrame, value_col: str, title: str, ylabel: str, output_path: str):
    fig, ax = plt.subplots(figsize=(12, 6))
    order = [s for s in SCENARIO_ORDER if s in df['scenario'].unique()]
    palette_dict = {s: PALETTE[i] for i, s in enumerate(SCENARIO_ORDER)}

    sns.boxplot(data=df, x='scenario', y=value_col, order=order, hue='scenario',
                hue_order=order, palette=palette_dict, ax=ax, fliersize=3, linewidth=0.8,
                legend=False)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([SCENARIO_LABELS.get(s, s) for s in order])
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"  Chart saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Analisis Benchmark Argon2id')
    parser.add_argument('--micro', required=True, help='Path ke CSV mikro (atau glob pattern)')
    parser.add_argument('--macro', required=True, help='Path ke CSV makro (atau glob pattern)')
    parser.add_argument('--output-dir', default='benchmark/results', help='Direktori output')
    args = parser.parse_args()

    micro_file = args.micro if '*' not in args.micro else find_latest_file(args.micro)
    macro_file = args.macro if '*' not in args.macro else find_latest_file(args.macro)

    print(f"Micro file: {micro_file}")
    print(f"Macro file: {macro_file}")

    df_micro = pd.read_csv(micro_file)
    df_macro = pd.read_csv(macro_file)

    print(f"Micro rows: {len(df_micro)}")
    print(f"Macro rows: {len(df_macro)}")

    os.makedirs(args.output_dir, exist_ok=True)
    charts_dir = os.path.join(args.output_dir, 'charts')
    os.makedirs(charts_dir, exist_ok=True)

    # === STATISTIK DESKRIPTIF ===
    micro_stats = {}
    for scenario in SCENARIO_ORDER:
        subset = df_micro[df_micro['scenario'] == scenario]['hashing_time_ms']
        if len(subset) > 0:
            micro_stats[scenario] = descriptive_stats(subset)

    macro_stats = {}
    for scenario in SCENARIO_ORDER:
        subset = df_macro[df_macro['scenario'] == scenario]['login_time_ms']
        if len(subset) > 0:
            macro_stats[scenario] = descriptive_stats(subset)

    print_stats_table('LAYER 1: MIKRO (PHP CLI Murni) — Waktu Hashing', micro_stats)
    print_stats_table('LAYER 2: MAKRO (Laravel HTTP) — Waktu Login', macro_stats)

    # === OVERHEAD ===
    print(f"\n{'='*90}")
    print(f"  OVERHEAD FRAMEWORK (Makro - Mikro)")
    print(f"{'='*90}")
    print(f"{'Scenario':<15} {'Mikro(ms)':>10} {'Makro(ms)':>10} {'Overhead(ms)':>12} {'%Overhead':>10}")
    print(f"{'-'*15} {'-'*10} {'-'*10} {'-'*12} {'-'*10}")
    for scenario in SCENARIO_ORDER:
        if scenario in micro_stats and scenario in macro_stats:
            m = micro_stats[scenario]['mean']
            M = macro_stats[scenario]['mean']
            ov = M - m
            pct = (ov / m * 100) if m > 0 else 0
            print(f"{scenario:<15} {m:>10.2f} {M:>10.2f} {ov:>12.2f} {pct:>9.1f}%")

    # === ANOVA ===
    print(f"\n{'='*90}")
    print(f"  UJI STATISTIK: ONE-WAY ANOVA")
    print(f"{'='*90}")

    f_micro, p_micro = run_anova({s: df_micro[df_micro['scenario'] == s]['hashing_time_ms'] for s in SCENARIO_ORDER})
    print_anova_result('Mikro — hashing_time_ms', f_micro, p_micro)

    f_macro, p_macro = run_anova({s: df_macro[df_macro['scenario'] == s]['login_time_ms'] for s in SCENARIO_ORDER})
    print_anova_result('Makro — login_time_ms', f_macro, p_macro)

    # === TUKEY HSD ===
    tukey_micro = run_tukey_hsd(df_micro, 'hashing_time_ms', 'scenario')
    tukey_macro = run_tukey_hsd(df_macro, 'login_time_ms', 'scenario')

    print_tukey_table('Mikro — hashing_time_ms', tukey_micro)
    print_tukey_table('Makro — login_time_ms', tukey_macro)

    # === CHARTS ===
    print(f"\n{'='*90}")
    print(f"  VISUALISASI")
    print(f"{'='*90}")

    chart_bar_mean(micro_stats, 'Rata-rata Waktu Hashing Argon2id per Skenario (Mikro)',
                   'Waktu Hashing (ms)', os.path.join(charts_dir, '01_bar_mikro_mean.png'))

    chart_bar_mean(macro_stats, 'Rata-rata Waktu Login Argon2id per Skenario (Makro)',
                   'Waktu Login (ms)', os.path.join(charts_dir, '02_bar_makro_mean.png'))

    chart_grouped_bar(micro_stats, macro_stats, os.path.join(charts_dir, '03_grouped_mikro_vs_makro.png'))

    chart_overhead(micro_stats, macro_stats, os.path.join(charts_dir, '04_overhead_framework.png'))

    chart_boxplot(df_micro, 'hashing_time_ms',
                  'Distribusi Waktu Hashing per Skenario (Mikro)',
                  'Waktu Hashing (ms)', os.path.join(charts_dir, '05_boxplot_mikro.png'))

    chart_boxplot(df_macro, 'login_time_ms',
                  'Distribusi Waktu Login per Skenario (Makro)',
                  'Waktu Login (ms)', os.path.join(charts_dir, '06_boxplot_makro.png'))

    # === SIMPAN CSV ANALISIS ===
    analysis_rows = []
    for scenario in SCENARIO_ORDER:
        if scenario in micro_stats:
            s = micro_stats[scenario]
            overhead_ms = macro_stats[scenario]['mean'] - s['mean'] if scenario in macro_stats else None
            overhead_pct = (overhead_ms / s['mean'] * 100) if (overhead_ms is not None and s['mean'] > 0) else None
            analysis_rows.append({
                'scenario': scenario,
                'layer': 'micro',
                'memory_kib': SCENARIO_PARAMS[scenario]['m'],
                'time_cost': SCENARIO_PARAMS[scenario]['t'],
                'parallelism': SCENARIO_PARAMS[scenario]['p'],
                'n': s['n'], 'mean_ms': s['mean'], 'median_ms': s['median'],
                'std_ms': s['std'], 'min_ms': s['min'], 'max_ms': s['max'], 'cv_pct': s['cv_pct'],
                'overhead_ms': '', 'overhead_pct': '',
            })
        if scenario in macro_stats:
            s = macro_stats[scenario]
            overhead_ms = s['mean'] - micro_stats[scenario]['mean'] if scenario in micro_stats else None
            overhead_pct = (overhead_ms / micro_stats[scenario]['mean'] * 100) if (overhead_ms is not None and micro_stats[scenario]['mean'] > 0) else None
            analysis_rows.append({
                'scenario': scenario,
                'layer': 'macro',
                'memory_kib': SCENARIO_PARAMS[scenario]['m'],
                'time_cost': SCENARIO_PARAMS[scenario]['t'],
                'parallelism': SCENARIO_PARAMS[scenario]['p'],
                'n': s['n'], 'mean_ms': s['mean'], 'median_ms': s['median'],
                'std_ms': s['std'], 'min_ms': s['min'], 'max_ms': s['max'], 'cv_pct': s['cv_pct'],
                'overhead_ms': round(overhead_ms, 4) if overhead_ms is not None else '',
                'overhead_pct': round(overhead_pct, 2) if overhead_pct is not None else '',
            })

    df_analysis = pd.DataFrame(analysis_rows)
    analysis_csv = os.path.join(args.output_dir, 'analysis_combined.csv')
    df_analysis.to_csv(analysis_csv, index=False)
    print(f"\n  Analysis CSV: {analysis_csv}")

    # Simpan ANOVA results
    anova_rows = [
        {'test': 'ANOVA', 'layer': 'micro', 'f_stat': f_micro, 'p_value': p_micro,
         'significant': 'Yes' if p_micro and p_micro < 0.05 else 'No'},
        {'test': 'ANOVA', 'layer': 'macro', 'f_stat': f_macro, 'p_value': p_macro,
         'significant': 'Yes' if p_macro and p_macro < 0.05 else 'No'},
    ]
    df_anova = pd.DataFrame(anova_rows)
    anova_csv = os.path.join(args.output_dir, 'anova_results.csv')
    df_anova.to_csv(anova_csv, index=False)
    print(f"  ANOVA CSV:    {anova_csv}")

    tukey_micro.to_csv(os.path.join(args.output_dir, 'tukey_micro.csv'), index=False)
    tukey_macro.to_csv(os.path.join(args.output_dir, 'tukey_macro.csv'), index=False)
    print(f"  Tukey CSV:    {args.output_dir}/tukey_micro.csv, tukey_macro.csv")

    print(f"\n{'='*90}")
    print(f"  ANALISIS SELESAI")
    print(f"{'='*90}")


if __name__ == '__main__':
    main()
