import os
from typing import List, Tuple
import math

from sklearn.manifold import TSNE
import networkx as nx
import torch
import numpy as np
import pandas as pd
try:
    import seaborn as sns
    import matplotlib.pyplot as plt
except ImportError:
    pass


def _get_key(args, no_args_key=None, args_prefix=None):
    _k = "{}-{}-{}".format(args.model_name, args.dataset_name, args.custom_key) if args is not None \
        else (no_args_key or "raw")
    if args_prefix:
        _k = "{}-{}".format(args_prefix, _k)
    return _k


def _get_key_and_makedirs(args=None, no_args_key=None, base_path="./", args_prefix=None,
                          exist_ok=True, **kwargs) -> Tuple[str, str]:
    _key = _get_key(args, no_args_key, args_prefix)
    _path = os.path.join(base_path, _key)
    os.makedirs(_path, exist_ok=exist_ok, **kwargs)
    return _key, _path


def plot_line_with_std(tuple_to_mean_list, tuple_to_std_list, x_label, y_label, name_label_list, x_list,
                       hue=None, size=None, style=None, col=None, order=None,
                       markers=True, dashes=False, n=150,
                       x_lim=None, y_lim=None, err_style="band",
                       args=None, custom_key="", extension="png"):
    pd_data = {x_label: [], y_label: [], **{name_label: [] for name_label in name_label_list}}
    for name_tuple, mean_list in tuple_to_mean_list.items():
        std_list = tuple_to_std_list[name_tuple]
        for x, mean, std in zip(x_list, mean_list, std_list):
            for name_label, value_of_name in zip(name_label_list, name_tuple):
                pd_data[name_label] += [value_of_name for _ in range(n)]
            pd_data[y_label] += list(np.random.normal(mean, std, n))
            pd_data[x_label] += [x for _ in range(n)]
    df = pd.DataFrame(pd_data)

    key, path = _get_key_and_makedirs(args, custom_key, base_path="../figs")
    plot_info = "_".join([k for k in [hue, size, style, col] if k])
    path_and_name = "{}/fig_line_{}_{}.{}".format(path, key, plot_info, extension).replace(". ", "_")

    plot = sns.relplot(x=x_label, y=y_label, kind="line",
                       col=col, hue=hue, style=style, markers=markers, dashes=dashes,
                       legend="full", hue_order=order, ci="sd", err_style=err_style,
                       data=df)
    plot.set(xlim=x_lim)
    plot.set(ylim=y_lim)
    plot.savefig(path_and_name, bbox_inches='tight')
    plt.clf()


def plot_multiple_dist(data_list: List[torch.Tensor], name_list: List[str], x, y,
                       args=None, extension="png", custom_key="",
                       ylim=None, plot_func=None, unit_width_per_name=3,
                       **kwargs):
    plt.figure(figsize=(unit_width_per_name * len(name_list), 7))

    # data_list, name_list -> pd.Dataframe {x: [name...], y: [datum...]}
    pd_data = {x: [], y: []}
    for data, name in zip(data_list, name_list):
        data = data.cpu().numpy()
        pd_data[x] = pd_data[x] + [name for _ in range(len(data))]
        pd_data[y] = pd_data[y] + list(data)
    df = pd.DataFrame(pd_data)

    plot_func = plot_func or sns.boxplot
    plot = plot_func(x=x, y=y, data=df, **kwargs)

    if ylim:
        plot.set_ylim(*ylim)

    key, path = _get_key_and_makedirs(args, base_path="../figs")
    plot.get_figure().savefig("{}/fig_dist_{}_{}.{}".format(path, key, custom_key, extension),
                              bbox_inches='tight')
    plt.clf()


def plot_nodes_by_tsne(xs, ys, args=None, extension="png"):
    x_embed = TSNE(n_components=2).fit_transform(xs)

    df = pd.DataFrame({
        "x_coord": x_embed[:, 0],
        "y_coord": x_embed[:, 1],
        "class": ys,
    })
    plot = sns.scatterplot(x="x_coord", y="y_coord", hue="class", data=df,
                           legend=False, palette="Set1")
    plot.set_xlabel("")
    plot.set_ylabel("")
    plot.get_xaxis().set_visible(False)
    plot.get_yaxis().set_visible(False)
    sns.despine(left=False, right=False, bottom=False, top=False)

    key, path = _get_key_and_makedirs(args, base_path="../figs")
    plot.get_figure().savefig("{}/fig_tsne_{}.{}".format(path, key, extension), bbox_inches='tight')
    plt.clf()


def plot_scatter(xs, ys, hues, xlabel, ylabel, hue_name, custom_key, extension="pdf"):
    df = pd.DataFrame({
        xlabel: xs,
        ylabel: ys,
        hue_name: hues,
    })
    plot = sns.scatterplot(x=xlabel, y=ylabel, hue=hue_name, data=df,
                           palette="Set1")
    plot.set_xlabel(xlabel)
    plot.set_ylabel(ylabel)

    key, path = _get_key_and_makedirs(no_args_key=custom_key, base_path="../figs")
    plot_info = "_".join([k for k in [xlabel, ylabel, hue_name] if k])
    path_and_name = "{}/fig_scatter_{}_{}.{}".format(path, key, plot_info, extension)

    plot.get_figure().savefig(path_and_name, bbox_inches='tight')
    plt.clf()


def plot_graph_layout(xs, ys, edge_index, edge_to_attention, args=None, key=None, extension="png", layout="tsne"):
    _key, path = _get_key_and_makedirs(args, base_path="../figs")
    key = _key if key is None else "{}_{}".format(_key, key)

    G = nx.Graph()
    G.add_nodes_from(list(range(len(xs))))
    G.add_edges_from([(i, j) for i, j in np.transpose(edge_index)])

    if layout == "tsne":
        x_embed = TSNE(n_components=2).fit_transform(xs)
        pos = {xid: x_embed[xid] for xid in range(len(xs))}
    else:
        if layout == "random":
            pos = nx.layout.random_layout(G)
        elif layout == "spectral":
            pos = nx.layout.spectral_layout(G)
        elif layout == "spring":
            _k = 2.6
            layout = "{}-{}".format(layout, _k)
            pos = nx.layout.spring_layout(G, k=_k / math.sqrt(len(xs)))
        elif layout == "kamada_kawai":
            pos = nx.layout.kamada_kawai_layout(G)
        elif layout == "shell":
            pos = nx.layout.shell_layout(G)
        else:
            raise ValueError("{} is wrong layout".format(layout))

    n_classes = len(np.unique(ys))

    node_sizes = 4
    node_cmap = plt.cm.get_cmap("Set1")
    class_to_node_color = {c: node_cmap(c / n_classes) for c in range(n_classes)}
    node_color_list = [class_to_node_color[int(y)] for y in ys]

    nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_color_list, alpha=0.5)

    if edge_to_attention is not None:
        edge_color = [float(np.mean(edge_to_attention[tuple(sorted(e))])) for e in G.edges]
        edge_kwargs = dict(edge_color=edge_color, edge_cmap=plt.cm.Greys, width=1.25, alpha=0.8,
                           edge_vmin=0., edge_vmax=1.)
    else:
        edge_kwargs = dict(edge_color="grey", width=0.5, alpha=0.2)

    edges = nx.draw_networkx_edges(G, pos, node_size=node_sizes, **edge_kwargs)

    ax = plt.gca()
    ax.set_axis_off()
    plt.savefig("{}/fig_glayout_{}_{}.{}".format(path, key, layout, extension), bbox_inches='tight')
    plt.clf()
