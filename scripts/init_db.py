import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import command
from alembic.config import Config

from app.shared.config import ROOT_DIR, settings


def main() -> None:
    settings.database_file.parent.mkdir(parents=True, exist_ok=True)
    command.upgrade(Config(str(ROOT_DIR / "alembic.ini")), "head")
    print(f"Base de datos inicializada: {settings.database_file}")


if __name__ == "__main__":
    main()
