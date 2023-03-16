"""Tools for working with labels and their milestones and branches for Meeseeks."""

from dataclasses import dataclass
from re import match
from typing import Self, TypeVar

from github.Branch import Branch
from github.Label import Label
from github.Milestone import Milestone
from github.Repository import Repository
from options import Options
from packaging.version import Version, parse

MAJOR_MINOR_REGEX = r"([0-9]+)\.([0-9]+)"
BRANCH_NAME_REGEX = rf"{MAJOR_MINOR_REGEX}\.x$"
MILESTONE_REGEX = rf"{MAJOR_MINOR_REGEX}(\.([0-9]+))?"


def _get_branch_name(label: Label, options: Options) -> str:
    """Return the branch name for a backport label."""
    name = label.name.split("-")[1]

    if not match(
        f"^{options.tag_prefix}{BRANCH_NAME_REGEX}",
        name,
    ):
        msg = f"Label name: {label.name} does not match expected format"

        raise ValueError(msg)

    return name


def _get_branch_milestone(
    repo: Repository,
    title_prefix: str,
    options: Options,
) -> Milestone | None:
    if options.run_milestone:
        name_regex = f"^{options.tag_prefix}{MILESTONE_REGEX}"

        milestones = {
            parse(milestone.title): milestone
            for milestone in repo.get_milestones(state="open")
            if match(name_regex, milestone.title) and title_prefix in milestone.title
        }
        try:
            return milestones[sorted(milestones.keys())[-1]]
        except IndexError as err:
            msg = f"No milestones found matching: {title_prefix}"
            raise ValueError(msg) from err

    return None


_ML = TypeVar("_ML", bound="MilestoneLabel")


@dataclass
class MilestoneLabel:
    """Track a Meeseeks label together with its milestone and branch."""

    label: Label
    branch: Branch
    milestone: Milestone | None

    @property
    def version(self: Self) -> Version | None:
        """Get the version corresponding to the milestone."""
        if self.milestone is not None:
            return parse(self.milestone.title)

        return None

    @staticmethod
    def _check_label(label: Label, options: Options) -> Label:
        """Return a label from a repository."""
        if (
            label.description
            != f"on-merge: backport to {_get_branch_name(label, options)}"
        ):
            msg = f"Label {label.name} has incorrect description"
            raise ValueError(msg)

        return label

    @staticmethod
    def _get_backport_branch(
        repo: Repository,
        label: Label,
        options: Options,
    ) -> Branch:
        return repo.get_branch(_get_branch_name(label, options))

    @staticmethod
    def _get_backport_milestone(
        repo: Repository,
        branch: Branch,
        options: Options,
    ) -> Milestone:
        return _get_branch_milestone(repo, branch.name.split(".x")[0], options)

    @classmethod
    def backport(
        cls: type[_ML],
        repo: Repository,
        label: Label,
        options: Options,
    ) -> _ML:
        """Return a backport label from a repository."""
        label = cls._check_label(label, options)
        branch = cls._get_backport_branch(repo, label, options)
        milestone = cls._get_backport_milestone(repo, branch, options)

        return cls(label, branch, milestone)

    @classmethod
    def no_backport(
        cls: type[_ML],
        repo: Repository,
        options: Options,
    ) -> _ML:
        """Return a no-backport label from a repository."""
        return cls(
            repo.get_label(options.no_backport),
            repo.get_branch(repo.default_branch),
            _get_branch_milestone(repo, "", options),
        )
