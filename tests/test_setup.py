"""Smoke tests to check the salisbury environment is set up correctly."""

import importlib
import sys

import pytest
import geopandas as gpd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import Point


@pytest.mark.parametrize(
    "module",
    [
        "geopandas",
        "osmnx",
        "networkx",
        "scipy",
        "pandas",
        "numpy",
        "matplotlib",
        "jupyterlab",
        "pytest",
    ],
)
def test_import(module):
    assert importlib.import_module(module) is not None


def test_python_version():
    assert sys.version_info >= (3, 9), f"Python 3.9+ required, got {sys.version}"


def test_crs_distance_near_salisbury():
    # Two points 0.01 degrees of longitude apart at the same latitude
    points = gpd.GeoSeries(
        [Point(-1.7983, 51.0688), Point(-1.7883, 51.0688)], crs="EPSG:4326"
    )
    projected = points.to_crs("EPSG:27700")
    distance = projected.iloc[0].distance(projected.iloc[1])
    assert 500 <= distance <= 800, f"Distance was {distance:.1f} m"


def test_scipy_dijkstra_shortest_path():
    # Directed graph: 0 -> 1 (2), 1 -> 2 (3), 0 -> 2 (10)
    # Shortest path 0 -> 2 is 2 + 3 = 5
    rows = [0, 1, 0]
    cols = [1, 2, 2]
    weights = [2, 3, 10]
    graph = csr_matrix((weights, (rows, cols)), shape=(3, 3))
    distances = dijkstra(graph, directed=True, indices=0)
    assert distances[2] == 5


@pytest.mark.network
def test_osm_drive_network_download():
    import osmnx as ox

    graph = ox.graph_from_point((51.0688, -1.7983), dist=500, network_type="drive")
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0
