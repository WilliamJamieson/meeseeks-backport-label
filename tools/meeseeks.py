"""Tools for Meeseeks."""

from dataclasses import dataclass
from typing import Self, TypeVar

from options import Options
from pull import PullRequest

_M = TypeVar("_M", bound="Meeseeks")


@dataclass
class Meeseeks:
    """Hold all the information about Meeseeks labels for a pull request."""

    options: Options
    pull_request: PullRequest

    @classmethod
    def from_event(cls: type[_M]) -> _M:
        """Construct a Meeseeks from a GitHub event."""
        options = Options.from_environ()

        return cls(options, PullRequest.from_environ(options))

    def check(self: Self) -> None:
        """Check that the labels are valid."""
        self.pull_request.check(self.options)

    def set_milestone(self: Self) -> None:
        """Set the milestone on the pull request."""
        self.pull_request.set_milestone(self.options)
