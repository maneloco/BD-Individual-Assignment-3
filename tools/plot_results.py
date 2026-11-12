import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'lines.linewidth': 2,
    'lines.markersize': 6,
    'grid.alpha': 0.4,
    'grid.linestyle': '--'
})

def load_data(filepath):
    if not os.path.exists(filepath):
        print(f"Error: file not found: {filepath}")
        return None
    df = pd.read_csv(filepath)
    df_measured = df[df['repetition'] >= 0].copy()
    return df_measured

def compute_summary_stats(df):
    grouped = df.groupby(['method', 'n', 'threads'])['time_sec']
    stats = grouped.agg(
        median='median',
        q25=lambda x: np.percentile(x, 25),
        q75=lambda x: np.percentile(x, 75),
        min='min',
        max='max'
    ).reset_index()
    stats['err_low'] = stats['median'] - stats['q25']
    stats['err_high'] = stats['q75'] - stats['median']
    return stats

def plot_speedup(stats, output_dir):
    seq_stats = stats[stats['method'] == 'seq_ikj'].set_index('n')['median'].to_dict()
    par_stats = stats[stats['method'] == 'par_ikj'].copy()

    if par_stats.empty or not seq_stats:
        return

    par_stats['t_seq'] = par_stats['n'].map(seq_stats)
    par_stats['speedup'] = par_stats['t_seq'] / par_stats['median']

    available_sizes = sorted(par_stats['n'].unique())
    target_sizes = [64, 128, 256, 512, 1024, 2048, 4096]
    selected_sizes = [s for s in target_sizes if s in available_sizes]
    if not selected_sizes:
        selected_sizes = available_sizes[-5:]

    fig, ax = plt.subplots(figsize=(8.5, 6))
    all_threads = sorted(par_stats['threads'].unique())

    ax.plot(all_threads, all_threads, 'k--', label='Ideal Linear Speedup (S=p)', alpha=0.7)

    colormap = plt.cm.viridis(np.linspace(0.1, 0.9, len(selected_sizes)))

    for idx, n in enumerate(selected_sizes):
        sub = par_stats[par_stats['n'] == n].sort_values('threads')
        ax.plot(sub['threads'], sub['speedup'], '-o', label=f'n = {n}', color=colormap[idx])

    ax.axvline(x=12, color='gray', linestyle=':', label='Physical Cores (12)')
    ax.axvline(x=16, color='red', linestyle=':', label='Logical Threads (16)')

    ax.set_xlabel('Thread Count (p)')
    ax.set_ylabel('Speedup S(p) = T_seq / T_p')
    ax.set_title('Speedup vs Thread Count Across Matrix Sizes')
    ax.set_xticks(all_threads)
    ax.grid(True)
    ax.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'speedup_vs_threads.png'), dpi=300)
    plt.close()
    print("  [SAVED] speedup_vs_threads.png")

def plot_efficiency(stats, output_dir):
    seq_stats = stats[stats['method'] == 'seq_ikj'].set_index('n')['median'].to_dict()
    par_stats = stats[stats['method'] == 'par_ikj'].copy()

    if par_stats.empty or not seq_stats:
        return

    par_stats['t_seq'] = par_stats['n'].map(seq_stats)
    par_stats['speedup'] = par_stats['t_seq'] / par_stats['median']
    par_stats['efficiency'] = par_stats['speedup'] / par_stats['threads']

    available_sizes = sorted(par_stats['n'].unique())
    target_sizes = [64, 128, 256, 512, 1024, 2048, 4096]
    selected_sizes = [s for s in target_sizes if s in available_sizes]
    if not selected_sizes:
        selected_sizes = available_sizes[-5:]

    fig, ax = plt.subplots(figsize=(8.5, 6))
    all_threads = sorted(par_stats['threads'].unique())

    ax.axhline(y=1.0, color='k', linestyle='--', label='Ideal Efficiency (100%)', alpha=0.7)

    colormap = plt.cm.viridis(np.linspace(0.1, 0.9, len(selected_sizes)))

    for idx, n in enumerate(selected_sizes):
        sub = par_stats[par_stats['n'] == n].sort_values('threads')
        ax.plot(sub['threads'], sub['efficiency'], '-s', label=f'n = {n}', color=colormap[idx])

    ax.axvline(x=12, color='gray', linestyle=':', label='Physical Cores (12)')
    ax.axvline(x=16, color='red', linestyle=':', label='Logical Threads (16)')

    ax.set_xlabel('Thread Count (p)')
    ax.set_ylabel('Efficiency E(p) = S(p) / p')
    ax.set_title('Parallel Efficiency vs Thread Count')
    ax.set_xticks(all_threads)
    ax.grid(True)
    ax.legend(loc='lower left', frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'efficiency_vs_threads.png'), dpi=300)
    plt.close()
    print("  [SAVED] efficiency_vs_threads.png")

def plot_execution_time(stats, output_dir):
    fig, ax = plt.subplots(figsize=(9, 6))

    seq = stats[stats['method'] == 'seq_ikj'].sort_values('n')
    ax.plot(seq['n'], seq['median'], 'k-o', label='Sequential Baseline (1 core)', linewidth=2.5)

    par = stats[stats['method'] == 'par_ikj']
    thread_picks = [1, 4, 8, 12, 16, 32]
    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#a65628']

    for idx, p in enumerate(thread_picks):
        sub = par[par['threads'] == p].sort_values('n')
        if not sub.empty:
            ax.plot(sub['n'], sub['median'], '--^', label=f'Parallel ({p} threads)', color=colors[idx % len(colors)])

    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xlabel('Matrix Dimension n (log2 scale)')
    ax.set_ylabel('Execution Time [s] (log scale)')
    ax.set_title('Execution Time vs Matrix Dimension (Sequential vs Parallel)')
    ax.grid(True, which='both')
    ax.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'execution_time_vs_n.png'), dpi=300)
    plt.close()
    print("  [SAVED] execution_time_vs_n.png")

def plot_framework_overhead(stats, output_dir):
    seq_stats = stats[stats['method'] == 'seq_ikj'].set_index('n')['median'].to_dict()
    par_1 = stats[(stats['method'] == 'par_ikj') & (stats['threads'] == 1)].sort_values('n').copy()

    if par_1.empty or not seq_stats:
        return

    par_1['t_seq'] = par_1['n'].map(seq_stats)
    par_1['overhead_ratio'] = par_1['median'] / par_1['t_seq']

    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.plot(par_1['n'], par_1['overhead_ratio'], '-d', color='#e7298a', label='T_par(p=1) / T_seq')
    ax.axhline(y=1.0, color='k', linestyle='--', label='Equal Runtime (1.0)', alpha=0.7)

    ax.set_xscale('log', base=2)
    ax.set_xlabel('Matrix Dimension n (log2 scale)')
    ax.set_ylabel('Ratio (T_parallel_1thread / T_seq)')
    ax.set_title('Single-Thread Parallel Overhead vs Sequential Baseline')
    ax.grid(True, which='both')
    ax.legend(loc='upper right', frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'framework_overhead.png'), dpi=300)
    plt.close()
    print("  [SAVED] framework_overhead.png")

def plot_memory_scaling(df, output_dir):
    med_mem = df.groupby('n')['peak_rss_kb'].median().reset_index()
    med_mem['rss_mb'] = med_mem['peak_rss_kb'] / 1024.0
    med_mem['theoretical_mb'] = (3.0 * 8.0 * (med_mem['n'] ** 2)) / (1024.0 * 1024.0)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(med_mem['n'], med_mem['rss_mb'], '-o', color='#2ca02c', label='Observed Peak RSS')
    ax.plot(med_mem['n'], med_mem['theoretical_mb'], '--', color='darkgreen', alpha=0.6, label='Theoretical Footprint (3x n^2 double)')

    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xlabel('Matrix Dimension n (log2 scale)')
    ax.set_ylabel('Peak Memory [MB] (log scale)')
    ax.set_title('Memory Footprint (Peak RSS) vs Matrix Dimension n')
    ax.grid(True, which='both')
    ax.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'memory_scaling.png'), dpi=300)
    plt.close()
    print("  [SAVED] memory_scaling.png")

def main():
    results_dir = 'results'
    output_dir = os.path.join(results_dir, 'figures')
    os.makedirs(output_dir, exist_ok=True)

    csv_name = sys.argv[1] if len(sys.argv) > 1 else 'parallel_benchmark.csv'
    csv_path = os.path.join(results_dir, csv_name)

    if not os.path.exists(csv_path):
        fallback = os.path.join(results_dir, 'test_quick.csv')
        if os.path.exists(fallback):
            csv_path = fallback
        else:
            print(f"Error: CSV file not found: {csv_path}")
            return

    print(f"Loading benchmark results from: {csv_path}")
    df = load_data(csv_path)
    if df is None or df.empty:
        print("Error: No data to plot.")
        return

    stats = compute_summary_stats(df)

    print("Generating Assignment 3 publication figures...")
    plot_speedup(stats, output_dir)
    plot_efficiency(stats, output_dir)
    plot_execution_time(stats, output_dir)
    plot_framework_overhead(stats, output_dir)
    plot_memory_scaling(df, output_dir)
    print(f"All figures generated successfully in: {output_dir}")

if __name__ == '__main__':
    main()
