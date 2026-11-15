"""The neural network that classifies incident types from their comments."""

from sklearn.neural_network import MLPClassifier

# Three hidden layers, so the network is four layers deep with its output layer.
NEURAL_NETWORK_HIDDEN_LAYERS = (512, 256, 128)


def build_neural_network(random_state: int | None = None) -> MLPClassifier:
    """Build a multi-layer perceptron with sigmoid outputs per incident type."""
    return MLPClassifier(
        hidden_layer_sizes=NEURAL_NETWORK_HIDDEN_LAYERS,
        activation="relu",
        alpha=1e-4,
        early_stopping=True,
        n_iter_no_change=5,
        max_iter=100,
        random_state=random_state,
    )
