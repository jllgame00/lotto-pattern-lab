"""Offline visual inspection of saved Phase 17 tensors and search results.

All factors, reconstructions, and null statistics are read from artifacts;
plotting never fits a decomposition or a predictive model.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .recurrence import research_matrix


TENSORS = ('A', 'B', 'C')
MODES = ('Time', 'Number', 'Feature')
FAMILIES = ('concentration', 'reconstruction', 'effective_rank', 'stability', 'temporal')


def plots(x, directory):
    """Write the nine diagnostic PNGs to ``directory/plots``; return paths.

    ``x`` is the valid research prefix matching the saved draw endpoints.
    Required inputs are ``decompositions.npz``, ``full_metrics.csv``,
    ``null_maxima.csv``, and ``real_summary.json``. If available, the frozen
    selection picks the tensor for the feature-0 reconstruction comparison;
    otherwise tensor A is used. The saved diagnostic ranks are (8, 6, 3),
    independent of the selected search cell. No inference is made here.
    """
    x = research_matrix(x)
    directory = Path(directory)
    with np.load(directory / 'decompositions.npz', allow_pickle=False) as stored:
        arrays = {key: stored[key] for key in stored.files}
    for name in TENSORS:
        draws = arrays[f'{name}_draws']
        values = arrays[f'{name}_tensor']
        reconstruction = arrays[f'{name}_reconstruction']
        if (draws.ndim != 1 or not len(draws) or draws[-1] != len(x)
                or not np.array_equal(draws, np.arange(draws[0], len(x) + 1))
                or values.ndim != 3 or values.shape[:2] != (len(draws), 45)
                or values.shape != reconstruction.shape):
            raise ValueError(f'Tensor {name} artifacts must match the supplied research prefix')
        if not np.isfinite(values).all() or not np.isfinite(reconstruction).all():
            raise ValueError(f'Tensor {name} artifacts must be finite')
    metrics = pd.read_csv(directory / 'full_metrics.csv')
    nulls = pd.read_csv(directory / 'null_maxima.csv')
    summary = json.loads((directory / 'real_summary.json').read_text(encoding='utf-8'))['full']
    output = directory / 'plots'
    output.mkdir(parents=True, exist_ok=True)
    written = []

    def save(fig, filename, title):
        fig.suptitle(title, fontsize=14)
        fig.tight_layout(rect=(0, 0, 1, .96))
        path = output / filename
        fig.savefig(path, dpi=160, bbox_inches='tight')
        plt.close(fig)
        written.append(path)

    with plt.rc_context({'font.family': 'DejaVu Sans', 'font.size': 10}):
        fig, axes = plt.subplots(3, 3, figsize=(13, 10), squeeze=False)
        for row, name in enumerate(TENSORS):
            for mode, label in enumerate(MODES):
                axis = axes[row, mode]
                singular = arrays[f'{name}_singular_{mode}']
                positive = singular > 0
                axis.semilogy(np.arange(1, len(singular) + 1)[positive],
                              singular[positive] / singular[0], color=f'C{row}')
                axis.set(title=f'Tensor {name}: {label}', xlabel='Component',
                         ylabel='Singular value / leading value')
                axis.grid(alpha=.25)
        save(fig, 'singular_spectra.png', 'HOSVD mode singular spectra')

        for model, filename, label in [
            ('iid', 'real_vs_iid.png', 'IID'),
            ('fixed_margins', 'real_vs_fixed_margin.png', 'Fixed margins'),
        ]:
            group = nulls[(nulls['scope'] == 'full') & (nulls['null_model'] == model)]
            if group.empty:
                raise ValueError(f'Missing full-scope {model} null maxima')
            fig, axes = plt.subplots(2, 3, figsize=(14, 8))
            for axis, family in zip(axes.flat, FAMILIES):
                samples = group[family].to_numpy(dtype=float)
                samples = samples[np.isfinite(samples)]
                observed = float(summary['maxima'][family])
                if not len(samples) or not np.isfinite(observed):
                    raise ValueError(f'Missing finite {model}/{family} maxima')
                axis.hist(samples, bins=min(25, max(5, int(np.sqrt(len(samples))))),
                          color='steelblue', alpha=.8, label=f'Null ({len(samples)})')
                axis.axvline(observed, color='crimson', linewidth=2,
                             label=f'Real: {observed:.2f}')
                axis.set(title=family.replace('_', ' ').title(),
                         xlabel='Complete-search maximum z', ylabel='Replicates')
                axis.legend(fontsize=8)
            axes.flat[-1].axis('off')
            axes.flat[-1].text(.05, .8,
                'Full research scope\nEach null repeats the complete search.\n'
                'Histograms show each family\'s own maximum.\n'
                'Significance and correction are reported\nin global_null_comparison.csv.',
                transform=axes.flat[-1].transAxes, va='top', linespacing=1.7)
            save(fig, filename, f'Real vs {label} null: global family maxima')

        fig, axes = plt.subplots(1, 3, figsize=(13, 12), sharey=True)
        bound = max(float(np.abs(arrays[f'{name}_factors_1'][:, :6]).max())
                    for name in TENSORS)
        for axis, name in zip(axes, TENSORS):
            loading = arrays[f'{name}_factors_1'][:, :6]
            image = axis.imshow(loading, aspect='auto', cmap='RdBu_r',
                                vmin=-bound, vmax=bound)
            axis.set(title=f'Tensor {name}', xlabel='Number factor', ylabel='Number')
            axis.set_xticks(np.arange(loading.shape[1]), np.arange(1, loading.shape[1] + 1))
            axis.set_yticks(np.arange(0, 45, 2), np.arange(1, 46, 2))
            fig.colorbar(image, ax=axis, fraction=.045, pad=.03, label='Loading')
        save(fig, 'number_factor_loadings.png', 'Number factor loadings (rank 6; sign-fixed)')

        fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)
        for axis, name in zip(axes, TENSORS):
            factors = arrays[f'{name}_factors_0']
            for component in range(min(4, factors.shape[1])):
                axis.plot(arrays[f'{name}_draws'], factors[:, component],
                          linewidth=.8, label=f'Factor {component + 1}')
            axis.set(title=f'Tensor {name}', ylabel='Temporal loading')
            axis.grid(alpha=.2)
            axis.legend(ncol=4, fontsize=8)
        axes[-1].set_xlabel('Completed draw anchor')
        save(fig, 'temporal_factors.png', 'Leading four temporal factors: inspection only')

        fig, axes = plt.subplots(1, 3, figsize=(17, 5))
        energies = {name: np.square(arrays[f'{name}_core']) for name in TENSORS}
        fractions = {name: energy / energy.sum() for name, energy in energies.items()}
        maximum = max(float(energy.max()) for energy in fractions.values())
        for axis, name in zip(axes, TENSORS):
            core = fractions[name]
            image = axis.imshow(core.reshape(core.shape[0], -1), aspect='auto',
                                cmap='magma', vmin=0, vmax=maximum)
            labels = [f'{number + 1},{feature + 1}'
                      for number in range(core.shape[1]) for feature in range(core.shape[2])]
            axis.set_xticks(np.arange(len(labels)), labels, rotation=90, fontsize=7)
            axis.set_yticks(np.arange(core.shape[0]), np.arange(1, core.shape[0] + 1))
            axis.set(title=f'Tensor {name}', xlabel='Number factor, feature factor',
                     ylabel='Temporal factor')
            fig.colorbar(image, ax=axis, fraction=.045, label='Fraction of core energy')
        save(fig, 'tucker_core_energy.png', 'Tucker core energy (8, 6, 3): descriptive only')

        fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
        reconstruction_rows = metrics[metrics['kind'] == 'negative_relative_error']
        for axis, name in zip(axes, TENSORS):
            rows = reconstruction_rows[reconstruction_rows['tensor'] == name]
            for feature_rank, group in rows.groupby('feature_rank', sort=True):
                group = group.sort_values('number_rank')
                axis.plot(group['number_rank'], -group['oriented_value'], marker='o',
                          label=f'Feature rank {int(feature_rank)}')
            axis.set(title=f'Tensor {name}', xlabel='Number rank',
                     ylabel='Relative Frobenius error', xticks=[2, 3, 4, 6])
            axis.grid(alpha=.25)
            axis.legend(fontsize=8)
        save(fig, 'reconstruction_by_rank.png', 'Reconstruction error by rank (temporal rank 8)')

        fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
        stability_rows = metrics[metrics['kind'] == 'number_subspace']
        for axis, name in zip(axes, TENSORS):
            rows = stability_rows[stability_rows['tensor'] == name]
            for (block_a, block_b), group in rows.groupby(['block_a', 'block_b'], sort=True):
                group = group.sort_values('number_rank')
                axis.plot(group['number_rank'], group['oriented_value'], marker='o',
                          label=f'Blocks {int(block_a) + 1} vs {int(block_b) + 1}')
            axis.set(title=f'Tensor {name}', xlabel='Number subspace rank',
                     ylabel='Mean squared principal-angle cosine',
                     xticks=[2, 3, 4, 6], ylim=(0, 1.03))
            axis.grid(alpha=.25)
            axis.legend(fontsize=8)
        save(fig, 'factor_stability.png', 'Number subspace stability across non-overlapping blocks')

        selection_path = directory / 'selected_configuration.json'
        selected = 'A'
        if selection_path.exists():
            selection = json.loads(selection_path.read_text(encoding='utf-8'))
            selected = selection['selection']['choice']['spec']['tensor']
            if selected not in TENSORS:
                raise ValueError('Selected tensor must be A, B, or C')
        observed = arrays[f'{selected}_tensor'][-104:, :, 0].T
        reconstructed = arrays[f'{selected}_reconstruction'][-104:, :, 0].T
        draws = arrays[f'{selected}_draws'][-104:]
        bound = max(float(np.abs(observed).max()), float(np.abs(reconstructed).max()))
        fig, axes = plt.subplots(2, 1, figsize=(15, 10), sharex=True, sharey=True)
        for axis, values, label in zip(axes, [observed, reconstructed],
                                       ['Observed standardized tensor', 'Saved rank-(8, 6, 3) reconstruction']):
            image = axis.imshow(values, origin='lower', aspect='auto', cmap='RdBu_r',
                                vmin=-bound, vmax=bound,
                                extent=(draws[0] - .5, draws[-1] + .5, .5, 45.5))
            axis.set(title=label, ylabel='Number', yticks=[1, 10, 20, 30, 40, 45])
            fig.colorbar(image, ax=axis, fraction=.025, pad=.02, label='Standardized value')
        axes[-1].set_xlabel('Completed draw anchor')
        save(fig, 'tensor_slice_reconstruction.png',
             f'Tensor {selected}, feature 0: last {len(draws)} anchors (inspection only)')

    return written
