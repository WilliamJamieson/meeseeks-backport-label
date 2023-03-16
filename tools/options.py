"""Read options from environment variables."""

from dataclasses import dataclass
from enum import StrEnum
from os import environ
from re import sub
from typing import Self, TypeVar

_EO = TypeVar("_EO", bound="EnvOption")


class EnvOption(StrEnum):
    """Base class for environment options."""

    @classmethod
    def default(cls: type[_EO]) -> str:
        """
        Return the default value for the option.

            This always assumed to be the value of FALSE.
        """
        return getattr(cls, "DEFAULT").value  # noqa: B009

    @classmethod
    def env_name(cls: type[_EO]) -> str:
        """
        Get the environment variable name for the option.

            This is always the all caps snake case version of the class name.
        """
        return sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).upper()

    @classmethod
    def read_env(cls: type[_EO]) -> str:
        """
        Read the environment variable for the option.

            This will return the default value if the environment variable is
            not set.
        """
        return environ.get(cls.env_name(), cls.default()).lower()


class NoBackport(EnvOption):
    """NO_BACKPORT environment variable."""

    DEFAULT: str = "no-backport"


class TagPrefix(EnvOption):
    """TAG_PREFIX environment variable."""

    DEFAULT: str = ""


class LabelPrefix(EnvOption):
    """LABEL_PREFIX environment variable."""

    DEFAULT: str = "backport-"


_ES = TypeVar("_ES", bound="EnvSetting")


class EnvSetting(EnvOption):
    """Base class for environment settings."""

    @classmethod
    def read_env(cls: type[_ES]) -> str:
        """
        Read the environment variable for the option.

            This will return the default value if the environment variable is
            not set.

            This will raise an error if the environment variable is set to an
            option that is not defined.
        """
        value = super().read_env()

        if value not in list(cls):
            msg = f"Invalid value for {cls.env_name()}: {value}"
            raise ValueError(msg)

        return value


class CheckBackportLabels(EnvSetting):
    """CHECK_BACKPORT_LABELS environment variable."""

    DEFAULT: str = "false"
    TRUE: str = "true"


class SetMilestone(EnvSetting):
    """SET_MIILESTONE environment variable."""

    DEFAULT: str = "false"
    TRUE: str = "true"
    OVERWRITE: str = "overwrite"


_O = TypeVar("_O", bound="Options")


@dataclass
class Options:
    """Environment options read from environment variables."""

    check_backport_labels: str
    set_milestone: str
    no_backport: str
    tag_prefix: str
    label_prefix: str

    @classmethod
    def from_environ(cls: type[_O]) -> _O:
        """Read options from environment variables."""
        return cls(
            CheckBackportLabels.read_env(),
            SetMilestone.read_env(),
            NoBackport.read_env(),
            TagPrefix.read_env(),
            LabelPrefix.read_env(),
        )

    @property
    def run_check(self: Self) -> bool:
        """Return True if the check should be run."""
        return self.check_backport_labels == CheckBackportLabels.TRUE

    @property
    def run_milestone(self: Self) -> bool:
        """Return True if the milestone should be set."""
        return self.set_milestone in (SetMilestone.TRUE, SetMilestone.OVERWRITE)

    @property
    def overwrite(self: Self) -> bool:
        """Return True if the milestone should be overwritten."""
        return self.set_milestone == SetMilestone.OVERWRITE
