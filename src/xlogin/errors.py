class XLoginError(Exception):
    """Base error. Messages must never contain secrets (tokens, codes, verifiers)."""


class ConfigError(XLoginError):
    pass


class AuthorizationError(XLoginError):
    """The authorization step failed (denied, state mismatch, timeout...)."""


class TokenError(XLoginError):
    """The token endpoint rejected a request."""


class StorageError(XLoginError):
    pass
