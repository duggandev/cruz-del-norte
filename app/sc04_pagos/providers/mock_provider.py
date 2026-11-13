from app.sc04_pagos.providers.base import (
    PaymentProvider,
    PaymentProviderRequest,
    PaymentProviderResult,
    ProviderConfigurationError,
    ProviderProcessingError,
    ProviderTimeoutError,
    ProviderValidationError,
)


class MockPaymentProvider(PaymentProvider):
    PROVIDER_NAME = "MOCK_GATEWAY"
    SAFE_ENVIRONMENTS = {"academic_demo", "development", "dev", "test", "testing"}
    TOKEN_RESULTS = {
        "mock_aprobado": "APROBADO",
        "mock_rechazado": "RECHAZADO",
        "mock_pendiente": "PENDIENTE",
    }

    def __init__(self, enabled: bool, app_env: str):
        self.enabled = enabled
        self.app_env = app_env.strip().lower()

    def process(self, request: PaymentProviderRequest) -> PaymentProviderResult:
        if not self.enabled:
            raise ProviderConfigurationError("El simulador de pagos está deshabilitado.")
        if self.app_env not in self.SAFE_ENVIRONMENTS:
            raise ProviderConfigurationError("El simulador no puede utilizarse en este entorno.")

        token = request.token.strip().lower()
        if token == "mock_error":
            raise ProviderProcessingError("El simulador produjo un error de procesamiento.")
        if token == "mock_timeout":
            raise ProviderTimeoutError("El simulador agotó el tiempo de espera.")
        estado = self.TOKEN_RESULTS.get(token)
        if estado is None:
            raise ProviderValidationError("El token de simulación no es válido.")
        if request.transaction_sequence is None or request.transaction_sequence < 1:
            raise ProviderProcessingError("No fue posible asignar la secuencia de la transacción simulada.")
        sequence = request.transaction_sequence
        return PaymentProviderResult(
            estado=estado,
            id_transaccion=f"MOCK-{sequence:06d}",
            proveedor=self.PROVIDER_NAME,
            referencia_proveedor=f"MOCK_REF-{sequence:06d}",
        )
