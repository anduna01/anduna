class UsageLimitExceeded(Exception):
    """Se superó un límite de uso o presupuesto configurado."""


class ProviderDisabled(Exception):
    """El proveedor externo está desactivado o sin credenciales."""


class NotFound(Exception):
    pass


class InvalidTransition(Exception):
    """Transición de estado editorial no permitida."""
