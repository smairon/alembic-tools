import typing
import types
from functools import cached_property

import sqlalchemy
import os
from alembic.config import Config
from alembic.command import revision as alembic_revision
from alembic.command import upgrade as alembic_upgrade
from alembic.command import downgrade as alembic_downgrade

from . import utils

ModuleType = typing.Union[
    types.ModuleType,
    typing.Any,
]

MigrationSourceType = typing.Union[
    str,
    ModuleType,
]

CONFIG_FAILED_MSG = (
    'Please provide one of "database_module" or ' '"metadata" and "migrations_source"'
)
VERSIONS_TABLE = "alembic_version"
SCRIPT_LOCATION = utils.abspath_for_script_directory()
DEFAULT_MIGRATIONS_FOLDER = "versions"
TRIGGER_MIGRATIONS_FOLDER = "triggers"
DATA_MIGRATIONS_FOLDER = "data_migrations"
FILE_TEMPLATE = "%%(year)d_%%(month).2d_%%(day).2d_%%(rev)s_%%(slug)s"


class Migrator:
    def __init__(
        self,
        db_dsn: str,
        metadata: typing.Optional[sqlalchemy.MetaData] = None,
        migrations_source: typing.Optional[MigrationSourceType] = None,
        version_table: str = VERSIONS_TABLE
    ):
        self._db_dsn = db_dsn
        self._metadata = metadata
        self._migrations_source = migrations_source
        self._version_table = version_table

    def create_auto_migration(
        self,
        message: str,
        migrations_folder: str = None
    ):
        """Создание автоматической миграции на основе метаданных"""
        self._do_create_revision(
            message=message,
            migrations_folder=migrations_folder,
            autogenerate=True,
        )

    def upgrade(
        self,
        version: str = "head",
    ):
        alembic_upgrade(
            self._config,
            revision=version,
        )

    def downgrade(
        self,
        version: str = "-1",
    ):
        alembic_downgrade(
            self._config,
            revision=version,
        )

    @property
    def _migrations_dir(
        self
    ) -> str:
        if not isinstance(self._migrations_source, str):
            return utils.abspath_for_module(
                module=self._migrations_source,
            )
        return self._migrations_source

    @cached_property
    def _config(self) -> Config:
        config = Config(
            attributes=dict(
                metadata=self._metadata,
                migrations_dir=self._migrations_dir,
                version_table=self._version_table,
            ),
        )

        config.set_main_option(
            name="script_location",
            value=SCRIPT_LOCATION,
        )
        config.set_main_option(
            name="file_template",
            value=FILE_TEMPLATE,
        )
        config.set_main_option(
            name="version_locations",
            value=self._default_migrations_dir,
        )
        config.set_main_option(
            name="sqlalchemy.url",
            value=self._db_dsn,
        )

        return config

    @cached_property
    def _default_migrations_dir(
        self
    ) -> str:
        return str(os.path.join(self._migrations_dir, DEFAULT_MIGRATIONS_FOLDER))

    def _do_create_revision(
        self,
        message: str,
        migrations_folder: str = None,
        autogenerate: bool = False,
    ):
        if migrations_folder is None:
            path = self._default_migrations_dir
        else:
            path = os.path.join(
                self._config.attributes["migrations_dir"],
                migrations_folder,
            )

        utils.mkdirs(path)

        alembic_revision(
            config,
            version_path=path,
            message=message,
            autogenerate=autogenerate,
        )
