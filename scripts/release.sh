#!/usr/bin/env bash
# Verifies version in pyproject.toml, tags the release, and pushes.
#
# Usage:
#   ./scripts/release.sh

set -euo pipefail

TOML="pyproject.toml"
CHANGELOG="CHANGELOG.md"

# ── Read current version ────────────────────────────────────────────
VERSION=$(grep -m1 '^version' "$TOML" | sed 's/version = "\(.*\)"/\1/')
TAG="v${VERSION}"

# ── Check if tag already exists ─────────────────────────────────────
if git rev-parse "refs/tags/$TAG" >/dev/null 2>&1; then
  echo "Tag with ${VERSION} already exists. Please change the version to proceed."
  exit 1
fi

# ── Check if version is in CHANGELOG.md ─────────────────────────────
if ! grep -q "\[${VERSION}\]" "$CHANGELOG"; then
  echo "Entry for version ${VERSION} is missing in ${CHANGELOG}. Please add the entry into the change log to proceed."
  exit 1
fi

# ── Git tag and push ───────────────────────────────────────────────
git tag "$TAG"
git push origin main "$TAG"

echo ""
echo "✓ Released ${TAG} — GitHub Actions will handle the rest."
