from abc import ABC, abstractmethod
from dataclasses import dataclass


class PaymentProviderError(Exception):
    """Error controlado producido por un proveedor de pagos."""


class ProviderConfigurationError(PaymentProviderError):
    pass


class ProviderValidationError(PaymentProviderError):
    pass


class ProviderProcessingError(PaymentProviderError):
    pass


class ProviderTimeoutError(PaymentProviderError):
    pass


@dataclass(frozen=True)
class PaymentProviderRequest:
    id_reserva: int
    importe_centavos: int
    token: str
    idempotency_key: str
    transaction_sequence: int | None = None


@dataclass(frozen=True)
class PaymentProviderResult:
    estado: str
    id_transaccion: str
    proveedor: str
    referencia_proveedor: str


class PaymentProvider(ABC):
    @abstractmethod
    def process(self, request: PaymentProviderRequest) -> PaymentProviderResult:
        raise NotImplementedError
