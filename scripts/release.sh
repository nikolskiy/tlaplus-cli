#!/usr/bin/env bash
# Bump the patch version in pyproject.toml, commit, tag, and push.
#
# Usage:
#   ./scripts/release.sh          # bump patch  (0.1.5 → 0.1.6)
#   ./scripts/release.sh minor    # bump minor  (0.1.5 → 0.2.0)
#   ./scripts/release.sh major    # bump major  (0.1.5 → 1.0.0)

set -euo pipefail

PART="${1:-patch}"
TOML="pyproject.toml"

# ── Read current version ────────────────────────────────────────────
CURRENT=$(grep -m1 '^version' "$TOML" | sed 's/version = "\(.*\)"/\1/')
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

# ── Compute new version ─────────────────────────────────────────────
case "$PART" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
  *)     echo "Usage: $0 [major|minor|patch]"; exit 1 ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
TAG="v${NEW_VERSION}"

echo "Bumping version: ${CURRENT} → ${NEW_VERSION}"

# ── Update pyproject.toml ───────────────────────────────────────────
sed -i "s/^version = \"${CURRENT}\"/version = \"${NEW_VERSION}\"/" "$TOML"

# ── Verify the change ──────────────────────────────────────────────
echo "Updated ${TOML}:"
grep '^version' "$TOML"

# ── Git commit, tag, push ──────────────────────────────────────────
git add -A
git commit -m "Release ${TAG}"
git tag "$TAG"
git push origin main "$TAG"

echo ""
echo "✓ Released ${TAG} — GitHub Actions will handle the rest."
