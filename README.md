# meeseeks-backport-label
This is a workflow to assist in ensuring that all pull requests to a project employing [MeeseeksBox](https://meeseeksbox.github.io/) to handle automatically backporting changes have a decision made about if the pull request should be backported and/or where that pull request should be backported to. Since this process is equivalent to deciding a milestone for the pull request, it can further assist the process by consistently setting the milestone instead of requiring a maintainer perform another action.

Thus this workflow performs 3 checks:

1. The "description" of all the backport labels is correct to get MeeseeksBox attempt to backport a PR.
2. (Optional) Check that the backport labels are self-consitent:
    * At least one backport label is present, including a `no-backport` label.
    * If a `no-backport` label is present, then no other backport labels are present.
3. (Optional) Add a milestone consistent with the backport label.

See [below](#assumptions) for details on the assumptions made by this action.

## Example Workflow
```yaml
name: Label Checker
on:
  pull_request_target:
    types:
      - opened
      - synchronize
      - reopened
      - labeled
      - unlabeled

jobs:
  check_labels:
    name: Check labels
    runs-on: ubuntu-latest
    steps:
    - uses: WilliamJamieson/meeseeks-backport-label@main
      env:
        CHECK_BACKPORT_LABELS: true
        SET_MILESTONE: overwrite
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Will perform all 3 checks (overwriting any existing milestones). Note that the `GITHUB_TOKEN` is required. Moreover, if you wish for the workflow to modifly milestones then the workflow must be triggerd by `pull_request_target`, if you don't want to modify milestones then `pull_request` is a sufficient trigger.

## Assumptions

This workflow assumes that your backport-label, backport-branch, and milestone naming conventions are both self consistent and follow a semantic versioning scheme. In particular:

1. This workflow assumines that backport branches have names of the form `<prefix>a.b.x`, where each major or minor version is tracked on a separate bugfix branch, which has backports applied to it by MeeseeksBox.
    * For example, `astropy` uses `v5.0.x` and `v5.2.x` as two of its active backport branches.
        
2. This workflow assumes that backport labels have names of the form `<label prefix>-<backport branch>`.
    * For example, `astropy` uses `backport-v5.0.x` and `backport-v5.2.x` as two of its backport labels.
    
3. Milestones full symantic versions, `<prefix>a.b.c` where the `<prefix>` is the same as what the backport branch has.
    * Corresponding milestone titles for `astropy` could be `v5.0.5` and `v5.2.3`.


When computing milestones it follows the following rules:

* If backport labels is present, milestones are computed to be the latest bugfix version of the earliest label version. Meaning if the labels: `backport-1.1.x` and `backport-2.0.x` are present it will pick the latest open milestone corrisponding to version `1.1` i.e., if `1.1.1` and `1.1.2` are both open milestones, then it wil pick `1.1.2` (An error will be raised if no `1.1` open milestones are found).
* If a `no-backport` label is present then it will find the latest semantic version milestone and apply that.

This means we have two configuration options for these:

1. `TAG_PREFIX`, the prefix for the branch name. By default it is assumed to be an empty string `""`.
2. `LABEL_PREFIX`, the prefix for the label name. By default it is assumed to be `"backport-"`.



Which can be set as environment variables for the workflow.

## Additional Options

* `NO_BACKPORT`, sets the name of the `no-backport` label, which by default is `no-backport`.
* `CHECK_BACKPORT_LABELS`, turns on checking that the backport labels are self-consistent. It can be `true` or `false`, by default it is `false`.
* `SET_MILESTONE`, turns on milestone checking and setting. It has three possible values:

    * `false`, turns of all milestone checking. This is the default.
    * `true`, turns on milestone checking. It will compute a milestone and set it if no milestone exists, but it will not overwrite any existing milestone. It will fail if the computed milestone does not match a currently set milestone.
    * `overwrite`, turns on milestone checking and setting. In this case it will compute a milestone and then overwrite any existing milestones set on the PR.
    
## Final Suggestion
If you want the automated backports generated by MeeseeksBox to get automatically merged you can add:
```yaml
    if: github.event.pull_request.user.login == 'meeseeksmachine'
    steps:
      - run: gh pr merge $PR_URL --auto --rebase
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_URL: ${{ github.event.pull_request.html_url }}
```
to the end of the example workflow.

Assuming you are comfortable with the branch protections on your backport branches and have `automerge` turned on in your repository. That job will automatically merge the MeeseeksBox backport if/when all of its branch protections pass (this will require `pull_request_target` to function).