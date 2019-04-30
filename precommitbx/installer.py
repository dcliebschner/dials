from __future__ import absolute_import, division, print_function

import contextlib
import os
import stat
import sys
import time
import urllib2

import dials.precommitbx._precommitbx
import libtbx.introspection
import libtbx.load_env
import procrunner
import py
from tqdm import tqdm, trange

BOLD = "\033[1m"
GREEN = "\033[32m"
MAGENTA = "\033[1;35m"
NC = "\033[0m"
RED = "\033[1;31m"
YELLOW = "\033[1;33m"

precommit_home = py.path.local(abs(libtbx.env.build_path)).join("precommitbx")

python_source_version = "3.7.3"
python_source_size = 22973527
openssl_source_version = "1.0.2r"
openssl_source_size = 5348369
openssl_API_version = "(1, 0, 2, 18, 15)"  # import ssl; print(ssl._OPENSSL_API_VERSION)
precommitbx_version = dials.precommitbx._precommitbx.__version__

environment_override = {
    "LD_LIBRARY_PATH": "",
    "PRE_COMMIT_HOME": precommit_home.join("cache"),
    "PYTHONPATH": "",
}

repo_prefix = "  {:.<15}:"
repo_no_precommit = "(no pre-commit hooks)"
repo_precommit_installed = GREEN + "pre-commit installed" + NC
repo_precommit_conflict = (
    RED + "pre-commit available but a different pre-commit hook is installed" + NC
)
repo_precommit_legacy = YELLOW + "pre-commit out of date" + NC
repo_precommit_available = MAGENTA + "pre-commit available but not installed" + NC


def clean_run(*args, **kwargs):
    stop_on_error = kwargs.pop("stop_on_error", False)
    env_override = environment_override.copy()
    env_override.update(kwargs.pop("environment_override", {}))
    result = procrunner.run(
        *args,
        environment_override=env_override,
        print_stderr=False,
        print_stdout=False,
        **kwargs
    )
    if stop_on_error and result.returncode:
        if result.stdout:
            print("\n".join(result.stdout.split("\n")[-10:]))
            print("---")
        if result.stderr:
            print("\n".join(result.stderr.split("\n")[-10:]))
            print("---")
        sys.exit(stop_on_error)
    return result


class Progress(object):
    def __init__(self, description, length):
        self.pbar = tqdm(
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{remaining}]",
            desc="{:<18}".format(description),
            leave=False,
            smoothing=0.1,
            total=length,
            unit="",
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.pbar.n != self.pbar.total:
            precommit_home.join(".tqdm-record").write(
                "{pbar.desc}: {pbar.n} out of {pbar.total}\n".format(pbar=self.pbar),
                "a",
            )
        self.pbar.close()

    def increment(self, *args, **kwargs):
        self.pbar.update(1)


def stop_with_error(message, result):
    if result.stdout:
        print("\n".join(result.stdout.split("\n")[-10:]))
    if result.stderr:
        print("\n".join(result.stderr.split("\n")[-10:]))
    sys.exit(message)


def precommitbx_template(python):
    return "\n".join(
        [
            "#!/bin/bash",
            "# File generated by precommitbx",
            "export LD_LIBRARY_PATH=",
            "export PYTHONPATH=",
            "export PRE_COMMIT_HOME=" + precommit_home.join("cache").strpath,
            "export PATH=" + python.dirname + os.pathsep + "$PATH",
            "if [ ! -f .pre-commit-config.yaml ]; then",
            "  echo No pre-commit configuration. Skipping pre-commit checks.",
            "  exit 0",
            "fi",
            'if grep -q "language_version.\+libtbx.python" .pre-commit-config.yaml; then',
            "  echo Repository contains legacy pre-commit configuration. Skipping pre-commit checks.",
            "  exit 0",
            "fi",
            "if [ ! -e " + python.dirname + os.path.sep + python.basename + " ]; then",
            "  echo Precommitbx installation not found. Run libtbx.precommit to fix.",
            "  exit 0",
            "fi",
            python.basename + " -m _precommitbx.main",
        ]
    )


def install_precommitbx_hook(path, python):
    with path.join(".git", "hooks", "pre-commit").open("w") as fh:
        fh.write(precommitbx_template(python))
        mode = os.fstat(fh.fileno()).st_mode
        mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        os.fchmod(fh.fileno(), stat.S_IMODE(mode))


def check_precommitbx_hook(path, python):
    hookfile = path.join(".git", "hooks", "pre-commit")
    if not hookfile.check():
        return False
    if not os.access(hookfile.strpath, os.X_OK):
        return False
    hook = hookfile.read()
    if python and hook == precommitbx_template(python):
        return repo_precommit_installed
    if "generated by precommitbx" in hook:
        return repo_precommit_legacy
    if hook:
        return repo_precommit_conflict
    return False


def clean_precommit_home():
    if precommit_home.check():
        print("Cleaning out existing pre-commit installation")
        precommit_home.remove(rec=1)


def python_version(python):
    result = clean_run([python, "--version"])
    if result.returncode:
        return False
    return result.stdout.strip().split(" ")[1]


def precommit_version(python):
    result = clean_run(
        [python, "-c", "import _precommitbx;print(_precommitbx.__version__)"],
        working_directory=precommit_home.join("..").join(".."),
    )
    if result.returncode:
        return False
    return result.stdout.strip()


def download(name, url, size, target):
    with tqdm(
        bar_format="{l_bar}{bar}| [{remaining}, {rate_fmt}]",
        desc="{:<18}".format(name),
        leave=False,
        total=size,
        unit="B",
        unit_scale=True,
    ) as bar:
        with target.open("wb", ensure=True) as fh:
            url_request = urllib2.Request(url)
            with contextlib.closing(urllib2.urlopen(url_request)) as socket:
                while True:
                    block = socket.read(4096)
                    if not block:
                        break
                    bar.update(len(block))
                    fh.write(block)
        if bar.n != size:
            raise RuntimeError(
                "Error downloading %s: received %d bytes, expected %d"
                % (url, bar.n, size)
            )


def download_openssl():
    archive = precommit_home / "openssl-{}.tar.gz".format(openssl_source_version)
    if archive.check() and archive.size() == openssl_source_size:
        return archive
    url = "https://www.openssl.org/source/openssl-{}.tar.gz".format(
        openssl_source_version
    )
    download("Downloading OpenSSL", url, openssl_source_size, archive)
    return archive


def install_openssl():
    markerfile = precommit_home.join(".valid.openssl")
    if markerfile.check():
        return
    sourcedir = precommit_home / "openssl-{}".format(openssl_source_version)
    targz = download_openssl()
    if sys.platform == "darwin":
        build_environment = {"KERNEL_BITS": "64"}
    else:
        build_environment = {}

    with Progress("Unpacking OpenSSL", 2416) as bar:
        clean_run(
            ["tar", "xvfz", targz],
            working_directory=precommit_home,
            callback_stdout=bar.increment,
            stop_on_error="Error unpacking OpenSSL sources",
        )
    with Progress("Configuring OpenSSL", 351) as bar:
        clean_run(
            [
                sourcedir.join("config"),
                "--prefix=%s" % precommit_home,
                "-fPIC",
                "no-hw",
            ],
            callback_stdout=bar.increment,
            environment_override=build_environment,
            stop_on_error="Error configuring OpenSSL sources",
            working_directory=sourcedir,
        )
    with Progress("Building OpenSSL", 1265) as bar:
        clean_run(
            ["make"],
            callback_stdout=bar.increment,
            environment_override=build_environment,
            stop_on_error="Error building OpenSSL",
            working_directory=sourcedir,
        )
    with Progress("Installing OpenSSL", 2152) as bar:
        clean_run(
            ["make", "install"],
            callback_stdout=bar.increment,
            environment_override=build_environment,
            stop_on_error="Error installing OpenSSL",
            working_directory=sourcedir,
        )
    markerfile.ensure()


def download_python():
    archive = precommit_home / "Python-{}.tgz".format(python_source_version)
    if archive.check() and archive.size() == python_source_size:
        return archive
    url = "https://www.python.org/ftp/python/{0}/Python-{0}.tgz".format(
        python_source_version
    )
    download("Downloading Python", url, python_source_size, archive)
    return archive


def install_python(check_only=False):
    python3 = precommit_home.join("bin").join("python3")
    if python3.check():
        return python3
    if check_only:
        return False
    install_openssl()
    sourcedir = precommit_home / "Python-{}".format(python_source_version)
    targz = download_python()
    with Progress("Unpacking Python", 4174) as bar:
        clean_run(
            ["tar", "xvfz", targz],
            working_directory=precommit_home,
            callback_stdout=bar.increment,
            stop_on_error="Error unpacking Python sources",
        )
    with Progress("Configuring Python", 716) as bar:
        clean_run(
            [
                sourcedir.join("configure"),
                "--prefix=%s" % precommit_home,
                "--with-openssl=%s" % precommit_home,
            ],
            working_directory=sourcedir,
            callback_stdout=bar.increment,
            stop_on_error="Error configuring Python",
        )
    parallel = libtbx.introspection.number_of_processors()
    if parallel:
        parallel = str(parallel)
    else:
        parallel = "2"
    with Progress("Building Python", 461) as bar:
        clean_run(
            ["make", "-j", parallel],
            working_directory=sourcedir,
            callback_stdout=bar.increment,
            stop_on_error="Error building Python",
        )
    compiled_python = sourcedir.join("python")
    if sys.platform == "darwin":
        compiled_python = sourcedir.join("python.exe")
    if not compiled_python.check():
        # in a parallel build 'make' might terminate before the build is complete
        for _ in trange(
            100,
            desc="Waiting for build results to appear...",
            bar_format="{l_bar}{bar}| [{remaining}]",
        ):
            if compiled_python.check():
                break
            time.sleep(0.1)
        else:
            sys.exit("Did not find build results")
    result = clean_run(
        [compiled_python, "-c", "import ssl; print(ssl._OPENSSL_API_VERSION)"],
        working_directory=sourcedir,
        stop_on_error="Python is missing SSL support",
    )
    if result.stdout.strip() != openssl_API_version:
        sys.exit("Python has not picked up correct OpenSSL headers")
    with Progress("Installing Python", 7763) as bar:
        clean_run(
            ["make", "install"],
            working_directory=sourcedir,
            callback_stdout=bar.increment,
            stop_on_error="Error installing Python",
        )
    return python3


def install_precommit(python):
    with Progress("Installing Precommitbx", 28) as bar:
        clean_run(
            [python, "-m", "pip", "install", py.path.local(__file__).dirname],
            callback_stdout=bar.increment,
            stop_on_error="Error installing precommitbx",
            working_directory=precommit_home,
        )


def main():
    changes_required = False
    python = install_python(check_only=True)
    fix_things = "install" in sys.argv
    if python:
        py_ver = python_version(python)
    else:
        py_ver = False
    if py_ver != python_source_version and fix_things:
        python = install_python()
        py_ver = python_version(python)
    if py_ver == python_source_version:
        py_ver = GREEN + py_ver + NC
    elif py_ver:
        py_ver = YELLOW + py_ver + NC + " (expected: " + python_source_version + ")"
        changes_required = True
    else:
        py_ver = RED + "not installed" + NC
        changes_required = True
    print("Precommit Python:", py_ver)
    if python:
        pc_ver = precommit_version(python)
        if pc_ver != precommitbx_version and fix_things:
            install_precommit(python)
            pc_ver = precommit_version(python)
        if pc_ver == precommitbx_version:
            pc_ver = GREEN + pc_ver + NC
        elif pc_ver:
            pc_ver = YELLOW + pc_ver + NC + " (expected: " + precommitbx_version + ")"
            changes_required = True
        else:
            pc_ver = RED + "not installed" + NC
            changes_required = True
        print("Precommitbx:", pc_ver)

    print()
    print("Repositories:")
    for module in sorted(libtbx.env.module_dict):
        module_paths = [
            py.path.local(abs(path))
            for path in libtbx.env.module_dict[module].dist_paths
            if path and (path / ".git").exists()
        ]
        if not module_paths:
            continue
        module_paths = [
            path
            for path in module_paths
            if path.join(".pre-commit-config.yaml").check()
        ]
        if not module_paths:
            print(repo_prefix.format(module), repo_no_precommit)
            continue
        if len(module_paths) == 1:
            module_names = [module]
        else:
            module_names = [module + ":" + str(path) for path in module_paths]
        for moddirname, moddirpath in zip(module_names, module_paths):
            message = (
                check_precommitbx_hook(moddirpath, python) or repo_precommit_available
            )
            if message != repo_precommit_installed and fix_things:
                install_precommitbx_hook(moddirpath, python)
                message = (
                    check_precommitbx_hook(moddirpath, python)
                    or repo_precommit_available
                )
            print(repo_prefix.format(moddirname), message)
            if message != repo_precommit_installed:
                changes_required = True

    if changes_required:
        print()
        sys.exit(
            "To install pre-commit hooks run " + BOLD + "libtbx.precommit install" + NC
        )
