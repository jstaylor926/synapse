# Neural Network Training

Backpropagation: an algorithm that computes the gradient of a loss function with
respect to each weight by applying the chain rule backward through the network's
layers, layer by layer, from output to input.

Gradient descent — an optimization method that iteratively updates parameters in
the direction of the negative gradient to minimize a loss function.

The chain rule is a rule of calculus for differentiating a composition of
functions; backpropagation is essentially the chain rule applied across layers.

Learning rate: a scalar hyperparameter that controls how large each gradient
descent step is. Too high diverges; too low trains slowly.

Activation function — a nonlinearity (such as ReLU or sigmoid) applied to a
neuron's weighted sum so the network can model nonlinear relationships.

A loss function measures how far the model's predictions are from the targets;
training minimizes it. Common choices are cross-entropy and mean squared error.
