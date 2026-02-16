# Plans for the project

Here is your "Go-Live" checklist to transform local repo into an automated release machine using `uv` and `poethepoet`.

## Phase 1: Local Project Configuration (`pyproject.toml`)

* [ ] **Audit Project Metadata:**
  * [x] Ensure `[project]` table has `name`, `version`, `description`, `readme`, `requires-python`.
  * [ ] **Missing:** `license`, `authors`, and `classifiers`.
  * [x] *Critical:* Verify the `readme` file path matches your actual file (e.g., `README.md`).


* [x] **Verify Build System:**
  * [x] Confirm the `[build-system]` block exists (using fast, standard `setuptools` backend).


* [ ] **Define Poe Tasks:**
  * [ ] **Missing:** Add a `clean` task: `rm -rf dist` (or platform-equivalent).
  * [ ] **Missing:** Add a `build` task: `uv build`.
  * [x] Add a `test` task: `uv run pytest` (or your specific test command).
  * [ ] **Missing:** Add a `check-release` task: `sequence = ["clean", "test", "build", "cmd:twine check dist/*"]`.


## Phase 2: GitHub Repository Configuration

* [ ] **Configure Trusted Publishing (PyPI):**
* Log in to **PyPI.org** -> **Publishing**.
* Add a "New Publisher" -> Select **GitHub**.
* Enter: Owner (`your-username`), Repo (`your-repo`), Workflow Name (`release.yml`).
* *Note:* Leave "Environment" blank on PyPI side for now to keep it simple, or match it to the GitHub environment below.


* [ ] **Create "pypi" Environment (GitHub):**
* Go to GitHub Repo -> **Settings** -> **Environments**.
* Click **New environment** and name it `pypi`.
* Check **"Required reviewers"** and add your GitHub handle.
* *Why?* This creates the "Manual Approval" button for the PyPI upload step.



## Phase 3: The Workflow Implementation

* [ ] **Create Workflow File:**
* Create `.github/workflows/release.yml`.


* [ ] **Define Trigger:**
* Set `on: push: tags: ["v*"]`.


* [ ] **Set Permissions:**
* Add `contents: write` (for GitHub Releases).
* Add `id-token: write` (for PyPI Trusted Publishing).


* [ ] **Configure "Build & Release" Job:**
* Checkout code.
* Install `uv` & Python.
* Run `uv run poe test`.
* Run `uv build`.
* **Action:** `actions/upload-artifact@v4` (path: `dist/`).
* **Action:** `softprops/action-gh-release@v1` (files: `dist/*`).


* [ ] **Configure "PyPI Publish" Job:**
* Add `needs: [name-of-previous-job]`.
* Add `environment: pypi`.
* **Action:** `actions/download-artifact@v4` (path: `dist/`).
* **Action:** `pypa/gh-action-pypi-publish@release/v1`.


## Phase 4: Verification (The "Dry Run")

* [ ] **Bump Version:**
* Manually update `version = "0.1.0"` (or your starting version) in `pyproject.toml`.
* Commit and push to `main`.


* [ ] **Tag & Push:**
* Run `git tag v0.1.0`.
* Run `git push origin v0.1.0`.


* [ ] **Monitor Action:**
* Go to the **Actions** tab in GitHub.
* Watch the "Build & Release" job turn green.
* Verify a new Release exists on your repo main page with the `.whl` and `.tar.gz` files.


* [ ] **Approve PyPI Deployment:**
* The "PyPI Publish" job should be yellow (waiting).
* Click "Review deployments" -> "Approve and deploy".
* Watch it turn green.


* [ ] **Final Verify:**
* Check PyPI.org to see your package live!

