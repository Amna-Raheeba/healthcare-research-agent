# Root conftest: its presence makes pytest insert the project root into
# sys.path (rootdir-based "prepend" import mode), so `import health_agent`
# works when tests are run with the bare `pytest` binary from a fresh
# checkout where the package has not been pip-installed. This backs up the
# `pythonpath = ["."]` setting in pyproject.toml — either alone would do,
# both together keep CI green regardless of how pytest is invoked.
