from app.sc04_pagos.providers.base import PaymentProvider
from app.sc04_pagos.providers.culqi_provider import CulqiPaymentProvider
from app.sc04_pagos.providers.mock_provider import MockPaymentProvider
from app.shared.config import settings


def get_payment_provider() -> PaymentProvider:
    provider = settings.payment_provider.strip().lower()
    if provider == "mock":
        return MockPaymentProvider(enabled=settings.payment_mock_enabled, app_env=settings.app_env)
    if provider == "culqi":
        return CulqiPaymentProvider()
    from app.sc04_pagos.providers.base import ProviderConfigurationError

    raise ProviderConfigurationError(f"Proveedor de pagos no soportado: {provider}")


__all__ = ["PaymentProvider", "get_payment_provider"]
