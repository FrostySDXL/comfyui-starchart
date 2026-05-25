import shutil
import subprocess
import tempfile
from pathlib import Path


def _run_cmd(
    cmd: list[str], description: str, cwd: str | None = None
) -> subprocess.CompletedProcess:
    """Run a command and raise on failure."""
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        message_lines = [f"FAILED: {description}"]
        if result.stdout:
            message_lines.append(f"stdout: {result.stdout[:500]}")
        if result.stderr:
            message_lines.append(f"stderr: {result.stderr[:500]}")
        raise RuntimeError("\n".join(message_lines))
    return result


def _resolve_commit(clone_dir: str) -> str:
    """Get the full commit hash from a cloned repo."""
    result = _run_cmd(["git", "rev-parse", "HEAD"], "resolving commit hash", cwd=clone_dir)
    return result.stdout.strip()


def _copy_source_files(
    clone_dir: str, dest_dir: Path, files: list[str], repo_label: str
) -> list[str]:
    """Copy source files from clone into snapshot directory."""
    copied = []
    for rel_path in files:
        src = Path(clone_dir) / rel_path
        dst = dest_dir / rel_path
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
            copied.append(rel_path)
            print(f"  Copied {repo_label}/{rel_path}")
        else:
            print(f"  WARNING: {rel_path} not found in {repo_label} clone at {clone_dir}")
    return copied


def _refresh_repo_snapshot(
    *,
    version: str,
    snapshot_date: str,
    repo_url: str,
    snapshots_dir: Path,
    dest_prefix: str,
    heading_label: str,
    clone_label: str,
    copy_label: str,
    temp_prefix: str,
    files: list[str],
) -> tuple[str, str]:
    """Clone a repo at a tag and copy the selected source files into snapshots."""
    tag = version
    dest_name = f"{dest_prefix}-{version}"
    dest_dir = snapshots_dir / snapshot_date / dest_name

    print(f"\n=== Refreshing {heading_label} {version} ===")

    with tempfile.TemporaryDirectory(prefix=temp_prefix) as tmpdir:
        _run_cmd(
            ["git", "clone", "--depth", "1", "--branch", tag, repo_url, tmpdir],
            f"cloning {clone_label} at {tag}",
        )

        commit = _resolve_commit(tmpdir)
        print(f"  Resolved commit: {commit}")

        dest_dir.mkdir(parents=True, exist_ok=True)
        _copy_source_files(tmpdir, dest_dir, files, copy_label)

    return commit, dest_name


def verify_git_available() -> str:
    """Verify git is available on PATH before refresh work starts."""
    result = _run_cmd(["git", "--version"], "checking git availability")
    return result.stdout.strip()
