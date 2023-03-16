"""Script run by the GitHub Action."""

from meeseeks import Meeseeks

# Check PR labels
if __name__ == "__main__":
    meeseeks = Meeseeks.from_event()

    # Run Label Checks
    meeseeks.check()

    # Run Milestone Checks
    meeseeks.set_milestone()
