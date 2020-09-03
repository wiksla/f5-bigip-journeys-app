class JourneysError(Exception):
    """Base for journeys errors."""

    pass


class ConfigurationError(JourneysError):
    """Signifies an issue with user-specified configuration."""

    def __init__(self, msg: str):
        msg = f"Configuration error: {msg}"
        super().__init__(msg)


class TestConfigurationError(ConfigurationError):
    """Signifies an issue with user-specified configuration."""

    def __init__(self, msg: str):
        msg = f"Test configuration error: {msg}"
        super().__init__(msg)


class InputError(JourneysError):
    """Signifies an issue with user-specified configuration."""

    def __init__(self, msg: str):
        msg = f"Invalid input: {msg}"
        super().__init__(msg)


class JourneysConnectionError(JourneysError):
    """Signifies a general connection issue."""

    def __init__(self, msg: str):
        msg = f"Permanent connection error: {msg}"
        super().__init__(msg)
