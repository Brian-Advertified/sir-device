class ApplicationError(Exception):
    """Base application exception safe to present to the user."""


class AuthenticationError(ApplicationError):
    pass


class AuthorizationError(ApplicationError):
    pass


class ValidationError(ApplicationError):
    pass


class NotFoundError(ApplicationError):
    pass


class ConfigurationError(ApplicationError):
    pass
