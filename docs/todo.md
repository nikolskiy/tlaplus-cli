# Plans for the project

Here is your "Go-Live" checklist to transform local repo into an automated release machine using `uv` and `poethepoet`.


## Phase 1: GitHub Repository Configuration

* [X] **Configure Trusted Publishing (PyPI):**
* Log in to **PyPI.org** -> **Publishing**.
* Add a "New Publisher" -> Select **GitHub**.
* Enter: Owner (`your-username`), Repo (`your-repo`), Workflow Name (`release.yml`).
* *Note:* Leave "Environment" blank on PyPI side for now to keep it simple, or match it to the GitHub environment below.


* [X] **Create "pypi" Environment (GitHub):**
* Go to GitHub Repo -> **Settings** -> **Environments**.
* Click **New environment** and name it `pypi`.
* Check **"Required reviewers"** and add your GitHub handle.
* *Why?* This creates the "Manual Approval" button for the PyPI upload step.



## Phase 2: The Workflow Implementation

* [X] **Create Workflow File:**
* Create `.github/workflows/release.yml`.


* [X] **Define Trigger:**
* Set `on: push: tags: ["v*"]`.


* [X] **Set Permissions:**
* Add `contents: write` (for GitHub Releases).
* Add `id-token: write` (for PyPI Trusted Publishing).


* [X] **Configure "Build & Release" Job:**


* [X] **Configure "PyPI Publish" Job:**
* Add `needs: [name-of-previous-job]`.
* Add `environment: pypi`.



