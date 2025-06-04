#!/usr/bin/env python3
# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
apply_patches.py -- utility for applying QNX-specific patches
"""

import json
import logging
from pathlib import Path
import os
import subprocess
import sys


_THIS_DIR = os.path.abspath(os.path.dirname(__file__))
_ROOT_DIR = Path(__file__).parents[4]

sys.path.insert(0, os.path.join(_ROOT_DIR, "third_party/depot_tools"))


class GitError(Exception):
    pass


def _RunGitCommand(directory, command):
    """Launches git subcommand.

    Returns:
      The stripped stdout of the git command.
    Raises:
      GitError on failure, including a nonzero return code.
    """
    command = ["git"] + command
    # Force shell usage under cygwin. This is a workaround for
    # mysterious loss of cwd while invoking cygwin's git.
    # We can't just pass shell=True to Popen, as under win32 this will
    # cause CMD to be used, while we explicitly want a cygwin shell.
    if sys.platform == "cygwin":
        command = ["sh", "-c", " ".join(command)]
    try:
        logging.info("Executing '%s' in %s", " ".join(command), directory)
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=directory,
            shell=(sys.platform == "win32"),
        )
        stdout, stderr = tuple(x.decode(encoding="utf_8") for x in proc.communicate())
        stdout = stdout.strip()
        stderr = stderr.strip()
        logging.debug("returncode: %d", proc.returncode)
        logging.debug("stdout: %s", stdout)
        logging.debug("stderr: %s", stderr)
        if proc.returncode != 0:
            raise GitError(
                (
                    "Git command '{}' in {} failed: " "rc={}, stdout='{}' stderr='{}'"
                ).format(" ".join(command), directory, proc.returncode, stdout, stderr)
            )
        return stdout
    except OSError as e:
        raise GitError(
            "Git command 'git {}' in {} failed: {}".format(
                " ".join(command), directory, e
            )
        )


def AppplyPaches(patch_dir):
    files = [
        f for f in os.listdir(patch_dir) if os.path.isfile(os.path.join(patch_dir, f))
    ]

    patch_files = [f for f in files if f.endswith(".patch")]
    patch_files.sort()
    meta_files = [f for f in files if f.endswith(".meta")]
    with open(os.path.join(patch_dir, meta_files[0]), "r") as j:
        data = json.load(j)
    repo_path = data["path"]
    head = ''
    if repo_path != '.': # not project root
        dep_path = os.path.join(_ROOT_DIR, "DEPS")
        command = ["gclient", "getdep", "-r", f"src/{repo_path}", "--deps-file", dep_path]
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        head = result.stdout.strip()

    result = _RunGitCommand(repo_path, ["status"])
    if "working tree clean" not in result:
        if os.path.basename(patch_dir) == "third_party":
            result = _RunGitCommand(repo_path, ["status", "-uno"])
            if "nothing to commit" not in result:
                logging.warning("%s: the local repo has uncommitted change(s).", repo_path)
                return -1
        else:
            logging.warning("%s: the local repo is not clean.", repo_path)
            return -1

    if repo_path != '.': # not project root
        result = _RunGitCommand(repo_path, ["rev-parse", "HEAD"]).strip()
        if result != head:
            logging.warning(
                "%s: unexpected haad sha, have patches been applied already?", repo_path
            )
            return -1
    else:
        result = _RunGitCommand(repo_path, ["log", "--grep", "\[QNX LOCAL PATCH]", "--pretty=format:%H"]).strip()
        if result:
            logging.warning(
                "%s: found comit(s) labled with [QNX LOCAL PATCH], have patches been applied already?", repo_path
            )
            return -1

    for f in patch_files:
        if repo_path == '.':
            _RunGitCommand(repo_path, ["am", "-k", os.path.join(patch_dir, f)])
        else:
            _RunGitCommand(repo_path, ["am", os.path.join(patch_dir, f)])

def main(argv=None):
    logging.basicConfig(level=logging.WARNING)

    os.chdir(_ROOT_DIR)
    patches_dir = os.path.dirname(_THIS_DIR)
    patches_dir = os.path.join(patches_dir, "patches")
    subdirs = [f.path for f in os.scandir(patches_dir) if f.is_dir()]

    for dir in subdirs:
        AppplyPaches(dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
