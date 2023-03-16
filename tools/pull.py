"""Tools for working with pull requests."""

from dataclasses import dataclass
from json import load
from os import environ
from pathlib import Path
from sys import stdout
from typing import Self, TypeVar

from github import Github
from github.Issue import Issue
from github.Milestone import Milestone
from github.Repository import Repository
from labels import MilestoneLabel
from options import Options

_PR = TypeVar("_PR", bound="PullRequest")


@dataclass
class PullRequest:
    """Hold all the information about a pull request."""

    backport: dict[str, MilestoneLabel]
    labels: list[str]
    issue: Issue

    @staticmethod
    def _get_event() -> dict:
        if (name := environ["GITHUB_EVENT_NAME"]) not in (
            "pull_request",
            "pull_request_target",
        ):
            msg = f"Event name: {name} is not a pull request event"

            raise ValueError(msg)

        with Path(environ["GITHUB_EVENT_PATH"]).open(encoding="utf-8") as event_file:
            return load(event_file)

    @staticmethod
    def _get_repo(event: dict) -> Repository:
        g = Github(environ["GITHUB_TOKEN"])

        return g.get_repo(event["pull_request"]["head"]["repo"]["full_name"])

    @staticmethod
    def _get_backport_labels(
        repo: Repository,
        options: Options,
    ) -> dict[str, MilestoneLabel]:
        labels = [
            MilestoneLabel.backport(repo, label, options)
            for label in repo.get_labels()
            if label.name.startswith(options.label_prefix)
        ]
        labels.append(MilestoneLabel.no_backport(repo, options))

        return {label.label.name: label for label in labels}

    @staticmethod
    def _get_pr_labels(event: dict, backport: list[str]) -> list[str]:
        return [
            label["name"]
            for label in event["pull_request"]["labels"]
            if label["name"] in backport
        ]

    @classmethod
    def from_environ(cls: type[_PR], options: Options) -> _PR:
        """Construct a PullRequest from the environment."""
        event = cls._get_event()
        repo = cls._get_repo(event)

        backport = cls._get_backport_labels(repo, options)

        return cls(
            backport,
            cls._get_pr_labels(event, list(backport.keys())),
            repo.get_issue(event["number"]),
        )

    def _check_has_backport(self: Self) -> None:
        """Check that the PR has a backport label."""
        if len(self.labels) == 0:
            msg = "PR requires backport labeling"

            raise ValueError(msg)

    def _check_no_backport(self: Self, options: Options) -> None:
        """Check that PR does not have a backport and no-backport labels."""
        if options.no_backport in self.labels and len(self.labels) > 1:
            msg = f"PR has both a {options.no_backport} and backport labels"

            raise ValueError(msg)

    def check(self: Self, options: Options) -> None:
        """Check that the labels are valid."""
        if options.run_check:
            stdout.write("Checking backport labels...\n")
            stdout.write(f"    Available backport labels: {list(self.backport)}\n")
            stdout.write(f"    Found backport labels: {self.labels}\n")
            stdout.flush()

            self._check_has_backport()
            self._check_no_backport(options)

    def _calculate_milestone(self: Self, options: Options) -> Milestone:
        """
        Calculate the milestone from the labels.

            Returns the lowest possible milestone.
        """
        if options.no_backport in self.labels:
            return self.backport[options.no_backport].milestone

        labels = {(bp := self.backport[label]).version: bp for label in self.labels}
        return labels[sorted(labels.keys())[0]].milestone

    def set_milestone(self: Self, options: Options) -> None:
        """Set the milestone on the pull request."""
        if options.run_milestone:
            stdout.write("Checking milestone...\n")

            current = self.issue.milestone
            new = self._calculate_milestone(options)

            stdout.write(
                "    Current milestone: "
                f"{None if current is None else current.title}\n",
            )
            stdout.write(f"    Calculated milestone: {new.title}\n")
            stdout.flush()

            if current is not None and current != new and not options.overwrite:
                msg = f"PR already has milestone: {current.title}"
                raise ValueError(msg)

            stdout.write(f"    Setting milestone to: {new.title}\n")
            stdout.flush()

            self.issue.edit(milestone=new)
