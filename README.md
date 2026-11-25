# ant-skills

My Claude Code skills, grouped by what they're for.

| folder | skills |
|---|---|
| [`development/`](development) | [`component-scout`](development/component-scout): searches my bookmarked UI component libraries for ready-made components before building UI by hand<br>[`ship-pr`](development/ship-pr): `/ship-pr` commits, pushes, opens or updates the PR, self-reviews the diff, then checks CI and review comments |
| [`content-creation/`](content-creation) | _(none yet)_ |

## Install

```bash
git clone https://github.com/aaf1007/ant-skills.git ~/ant-skills
~/ant-skills/install.sh
```

`install.sh` symlinks each skill into `~/.claude/skills/<name>`. Claude Code only finds skills one folder deep, so the category folders exist only in this repo. Because they're symlinks, edits here take effect right away.

## Adding a skill

1. Create `<category>/<skill-name>/SKILL.md` (make a new category folder if none fits).
2. Run `./install.sh`.
3. Add it to the table above, then commit and push.
