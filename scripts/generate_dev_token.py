import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.shared.config import settings
from app.shared.security import create_access_token


def main() -> None:
    if settings.app_env.lower() not in {"academic_demo", "development", "dev"}:
        raise SystemExit("Este generador solo está habilitado en desarrollo.")
    parser = argparse.ArgumentParser(description="Genera un JWT local para Cruz del Norte")
    parser.add_argument("--subject", default="usuario-dev")
    parser.add_argument("--roles", nargs="+", default=["ADMIN"])
    parser.add_argument("--minutes", type=int, default=120)
    args = parser.parse_args()
    if not settings.jwt_secret_key:
        raise SystemExit("Configure JWT_SECRET_KEY en .env")
    print(create_access_token(args.subject, args.roles, args.minutes))


if __name__ == "__main__":
    main()
