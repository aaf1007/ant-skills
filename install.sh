#!/usr/bin/env bash
# Link every skill in this repo into ~/.claude/skills so Claude Code loads it.
# Skills live in category folders (development/, content-creation/, ...), but Claude Code
# only discovers skills one level deep, so each skill gets its own flat symlink.
# Re-run after adding a skill. Edits to the repo take effect immediately (they're symlinks).
set -euo pipefail

repo="$(cd "$(dirname "$0")" && pwd)"
dest="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$dest"

for skill_md in "$repo"/*/*/SKILL.md; do
  [ -e "$skill_md" ] || continue
  dir="$(dirname "$skill_md")"
  name="$(basename "$dir")"
  target="$dest/$name"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "skip  $name: $target is a real folder, not a link (move it aside first)"
    continue
  fi
  ln -sfn "$dir" "$target"
  echo "link  $name  ->  ${dir#"$repo"/}"
done
