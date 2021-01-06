class TurffError(Exception):
    """Generic Turff exception."""

    pass


class TurffConnectionError(TurffError):
    """Turff connection exception."""

    pass


class TurffCredentialsError(TurffError):
    """Turff invalid credentials exception."""

    pass
