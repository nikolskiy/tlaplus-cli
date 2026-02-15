# Plans for the project

## Github actions

CI + Release to github


### Release Steps
1.  **Prepare**: Ensure all tests and linters pass locally.
2.  **Bump Version**: Edit `pyproject.toml` to increment version.
3.  **Commit**: `git commit -am "chore(release): bump version to 0.1.0"`
4.  **Tag**: `git tag v0.1.0`
5.  **Push**: `git push && git push --tags`
6.  **Build**: `uv build` to generate sdist and wheel.
7.  **Publish** (optional): `uv publish` (if distributing to PyPI).

### Release Workflow
Create `.github/workflows/release.yml` to publish when a tag is pushed.

## Release to pypi
It would be best to upload from githab actions.
