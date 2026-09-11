#question1
files created are:
-pyproject.toml
-readme.md
-python-version
-src folder / init.py file

This is the standard uv init scaffold for a new Python 3.12 package, and its the bare project skeleton.



#question2
files created are:
.dvc/config
.dvc/.gitignore
.dvc/tmp/
.dvcignore

 they're just DVC's bootstrap metadata — no actual data or models yet, just the config/plumbing needed before you start tracking datasets with dvc add.

files should be pushed are .gitignore and config and dvc.ignore but the tmp in a local machine file that is not meant to be shared



#question3:
In .dvc/config.local. This file lives inside your project's .dvc folder, but it's automatically ignored by git, so it never gets committed.

and for other options then --global we have:
(no flag) → saved in .dvc/config — shared, goes into git



#question4:
.gitignore containing just /data. DVC did this automatically: since it's now tracking data itself (via DVC, not git), it adds an entry so git ignores the actual data folder — preventing you from accidentally committing 1GB+ of raw files to your git repo



#question5:
Yes — data.dvc. It's a small text/YAML metadata file DVC generates as a stand-in for the real data


Question 6:

GitHub: yes, the code is there (.py files, pyproject.toml, etc.).
GitHub: the actual data is not there — /data is gitignored, so it was never pushed to git.
Pointer file: yes — data.dvc is pushed to GitHub, and it points to the data via its md5 hash.
DagsHub: yes, the data is visible there (DagsHub hosts the actual data content since it's your DVC remote), and DagsHub also nicely renders the git repo + DVC-tracked files together in one UI.



Question 7:

After cloning, you see the code and data.dvc, but no data folder (it wasn't in git).
To get the actual data: dvc pull (after dvc remote is configured — it pulls from the DagsHub remote using the hash in data.dvc).



question8:
Yes, both food11_processed and food11_processed_mini are still there.
That's expected: .gitignore has /data — the entire data folder is ignored by git, not just the raw dataset.