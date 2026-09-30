# Validator runtime requirements

Provider-side validators require Python 3.10 or newer and NumPy 2.0 or newer. The release was tested with Python 3.12.13 and NumPy 2.3.5.

No network access is required by the provider-side validation commands.

Run validators in a clean environment and record the environment lock in every raw-evidence archive. A different dependency version is not automatically invalid, but it must be declared and becomes part of the controlled coarse/fine configuration.
