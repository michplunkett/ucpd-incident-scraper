"""Test the incident type neural network."""

import numpy as np
import pytest

from incident_scraper.models.neural_network import (
    NEURAL_NETWORK_HIDDEN_LAYERS,
    build_neural_network,
)


def synthetic_split(seed):
    """Features whose first three columns decide the three labels."""
    X = np.random.default_rng(seed).normal(size=(400, 10))
    y = (X[:, :3] > 0).astype(int)
    return X[:300], X[300:], y[:300], y[300:]


@pytest.mark.parametrize("seed", [None, 0, 7])
def test_neural_network_has_at_least_three_layers(seed):
    model = build_neural_network(seed)
    assert len(NEURAL_NETWORK_HIDDEN_LAYERS) >= 3
    assert tuple(model.hidden_layer_sizes) == NEURAL_NETWORK_HIDDEN_LAYERS
    assert model.random_state == seed

    X_train, _, y_train, _ = synthetic_split(0)
    model.fit(X_train, y_train)
    # One weight matrix per gap between layers: input -> hidden x3 -> output.
    assert len(model.coefs_) == len(NEURAL_NETWORK_HIDDEN_LAYERS) + 1


@pytest.mark.parametrize("seed", [0, 1])
def test_neural_network_learns_multilabel_signal(seed):
    X_train, X_test, y_train, y_test = synthetic_split(seed)
    prediction = (
        build_neural_network(seed).fit(X_train, y_train).predict(X_test)
    )

    assert prediction.shape == y_test.shape
    # Most labels are right, and most whole rows are right.
    assert (prediction == y_test).mean() > 0.9
    assert (prediction == y_test).all(axis=1).mean() > 0.7
