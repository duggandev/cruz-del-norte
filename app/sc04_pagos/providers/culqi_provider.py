from app.sc04_pagos.providers.base import (
    PaymentProvider,
    PaymentProviderRequest,
    PaymentProviderResult,
    ProviderConfigurationError,
)


class CulqiPaymentProvider(PaymentProvider):
    """Punto de extensión para una futura integración real autorizada con Culqi."""

    def process(self, request: PaymentProviderRequest) -> PaymentProviderResult:
        raise ProviderConfigurationError(
            "El proveedor Culqi real no está implementado en esta versión académica."
        )
