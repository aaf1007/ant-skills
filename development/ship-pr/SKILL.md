---
name: ship-pr
description: Commit and push the current work, open a pull request if the branch has none, review the diff, fix real problems, then check CI and review comments. Only run when the user types /ship-pr; never invoke it yourself.
disable-model-invocation: true
---

# Ship PR

Take the current work from a dirty tree to a reviewed, pushed pull request. Run the steps in order; each ends on its stated condition.

## 1. Preflight

- Run `git status`, `git branch --show-current`, and `git remote get-url origin`. Use the forge CLI that matches the remote (usually `gh`).
- On the default branch, create a feature branch named for the change before committing.
- Leave out any file that looks like a secret (`.env*`, `credentials*`, `*.local.json`, keys, tokens). Tell the user which files you skipped.

Done when you are on a feature branch and know exactly which files will be committed.

## 2. Verify

- Read `AGENTS.md` / `CLAUDE.md`. If the repo documents a changed-files check (e.g. `vp run check:changed` in T3 Code), run it.
- Otherwise run the project's own lint, typecheck, and tests for the changed files.
- Fix failures and rerun.

Done when the check passes.

## 3. Commit

- Group changes into logical commits, each with a conventional-commit title in plain language (`fix: keep draft when switching threads`).
- The user is the sole author: commit messages carry no `Co-Authored-By` trailers, no "Generated with" lines, and no AI attribution of any kind.

## 4. Push

- `git push -u origin <branch>`.

## 5. Pull request

- Run `gh pr view`. If no PR exists, open one with `gh pr create`.
- Body: the problem in 1–2 sentences, then how it was fixed. Follow the repo's PR template or PR skill when one exists.
- The PR body carries no AI credit.

Done when the branch has an open PR and you have its URL.

## 6. Self-review

- Read the full diff against the base branch with `gh pr diff`.
- Hunt for real bugs, missed surfaces (other callers, types, docs, tests that should change too), and leftover debug code.
- Fix real problems, commit, and push. Skip style nitpicks.

Done when every changed file in the diff has been read.

## 7. CI and review comments

- Run `gh pr checks` and `gh pr view --comments`.
- Fix real failures and valid review comments, commit, and push.
- Reply to each comment you dismiss with a one-line reason.
- If checks are still running, report their state and stop. The user reruns `/ship-pr` to continue; leave waiting to them rather than sleep-polling.

## Guardrails

Leave merging to the user. Push only fast-forward commits: no force-push, no rebasing or amending published history, unless the user explicitly asks.

## Report

Finish with a short report:

- PR URL
- Commits pushed this run
- Check status (passing / failing / pending)
- Anything left for the user
