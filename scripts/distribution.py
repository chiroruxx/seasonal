#!/usr/bin/env python3
"""Prepare and identify a manually reviewed, consistently signed Debug APK."""

import argparse
import base64
import binascii
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
APPLICATION_ID = "com.chihiro.seasonal"
EPOCH = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)


def command(*args, binary=False):
    result = subprocess.run(args, cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout if binary else result.stdout.decode().strip()


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Required environment variable is missing: {name}")
    return value


def validate_story(story):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", story):
        raise ValueError("story must contain only lowercase letters, digits and hyphens")
    if not (ROOT / "docs/stories" / story / "README.md").is_file():
        raise ValueError("The selected story does not exist")
    return story


def validate_commit(commit):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("commit must be a complete lowercase 40-character commit SHA")
    return commit


def version_code(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    value = int((now - EPOCH).total_seconds())
    if not 2 <= value <= 2_100_000_000:
        raise ValueError("The version code is outside the Android versionCode range")
    return value


def create_key(path):
    path = path.expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("Create the signing key outside the Git repository")
    if path.exists():
        raise ValueError("Refusing to replace an existing signing key")
    for name in ("SEASONAL_DEBUG_STORE_PASSWORD", "SEASONAL_DEBUG_KEY_ALIAS", "SEASONAL_DEBUG_KEY_PASSWORD"):
        required_env(name)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    old_umask = os.umask(0o077)
    try:
        command("keytool", "-genkeypair", "-noprompt", "-storetype", "JKS", "-keystore", str(path),
                "-alias", required_env("SEASONAL_DEBUG_KEY_ALIAS"), "-keyalg", "RSA", "-keysize", "3072",
                "-validity", "10000", "-dname", "CN=Seasonal Debug,O=Seasonal,C=JP",
                "-storepass:env", "SEASONAL_DEBUG_STORE_PASSWORD", "-keypass:env", "SEASONAL_DEBUG_KEY_PASSWORD")
    finally:
        os.umask(old_umask)
    path.chmod(0o600)
    print(f"Created signing key: {path}")


def restore_key(path):
    if path.exists():
        raise ValueError("Refusing to replace an existing signing key")
    try:
        data = base64.b64decode("".join(required_env("SEASONAL_DEBUG_KEYSTORE_BASE64").split()), validate=True)
    except binascii.Error:
        raise ValueError("SEASONAL_DEBUG_KEYSTORE_BASE64 is not valid base64") from None
    if not data:
        raise ValueError("The signing key is empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(data)


def prepare(story, commit, branch, output):
    validate_story(story)
    validate_commit(commit)
    command("git", "check-ref-format", "--branch", branch)
    # Only merged commits on the trusted default branch may execute with signing secrets later.
    command("git", "merge-base", "--is-ancestor", commit, f"refs/remotes/origin/{branch}")
    if command("git", "rev-parse", f"{commit}^{{commit}}") != commit:
        raise ValueError("The target is not the requested commit")
    command("git", "cat-file", "-e", f"{commit}:docs/stories/{story}/README.md")
    with output.open("a") as stream:
        stream.write(f"commit={commit}\nstory={story}\n")


def check_pending():
    # Annotation declarations and comments are not applications of the annotation.
    found = []
    for path in (ROOT / "app/src").rglob("*.kt"):
        text = re.sub(r"/\*.*?\*/|//[^\n]*", "", path.read_text(), flags=re.S)
        if re.search(r"@(?:[\w]+\.)*PendingAcceptance\b", text):
            found.append(str(path.relative_to(ROOT)))
    if found:
        raise ValueError("Pending acceptance tests remain: " + ", ".join(found))
    print("No @PendingAcceptance annotations remain")


def package(args):
    story = validate_story(args.story)
    commit = validate_commit(args.commit)
    if command("git", "rev-parse", "HEAD") != commit:
        raise ValueError("The APK source checkout does not match the selected commit")
    if not 2 <= args.version_code <= 2_100_000_000:
        raise ValueError("Invalid version code")
    info = command(str(args.aapt), "dump", "badging", str(args.apk))
    package_info = re.search(r"^package: name='([^']+)' versionCode='([^']+)'", info)
    if not package_info or package_info.groups() != (APPLICATION_ID, str(args.version_code)):
        raise ValueError("The APK applicationId or versionCode does not match the distribution request")
    signature = command(str(args.apksigner), "verify", "--print-certs", str(args.apk))
    fingerprints = re.findall(r"Signer #\d+ certificate SHA-256 digest: ([0-9a-f]+)", signature)
    expected = hashlib.sha256(command("keytool", "-exportcert", "-keystore", str(args.keystore),
                                       "-alias", required_env("SEASONAL_DEBUG_KEY_ALIAS"),
                                       "-storepass:env", "SEASONAL_DEBUG_STORE_PASSWORD", binary=True)).hexdigest()
    if fingerprints != [expected]:
        raise ValueError("The APK is not signed with the configured persistent signing certificate")
    filename = f"seasonal-{story}-{commit}-v{args.version_code}.apk"
    args.output_dir.mkdir(parents=True, exist_ok=False)
    target = args.output_dir / filename
    target.write_bytes(args.apk.read_bytes())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = {"schema_version": 1, "story": story, "commit": commit, "application_id": APPLICATION_ID,
                "version_code": args.version_code, "apk": filename, "sha256": digest,
                "signing_certificate_sha256": expected, "workflow_run_url": args.run_url}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (args.output_dir / "SHA256SUMS").write_text(f"{digest}  {filename}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a") as stream:
            stream.write(f"## 確認用 Debug APK\n\n- Story: `{story}`\n- Commit: `{commit}`\n"
                         f"- Version code: `{args.version_code}`\n- APK: `{filename}`\n"
                         f"- SHA-256: `{digest}`\n- Certificate SHA-256: `{expected}`\n\n"
                         "実機で確認し、受け入れた APK と同じファイルを配布してください。受け入れ後に再ビルドしません。\n")
    print(filename)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    for operation in ("create-key", "restore-key"):
        p = sub.add_parser(operation)
        p.add_argument("path", type=Path)
    sub.add_parser("version-code")
    sub.add_parser("check-pending")
    p = sub.add_parser("prepare")
    for name in ("story", "commit", "branch"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("package")
    for name in ("story", "commit", "run-url"):
        p.add_argument("--" + name, required=True)
    for name in ("apk", "keystore", "apksigner", "aapt", "output-dir"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--version-code", type=int, required=True)
    args = parser.parse_args()
    try:
        if args.operation == "create-key": create_key(args.path)
        elif args.operation == "restore-key": restore_key(args.path)
        elif args.operation == "version-code": print(version_code())
        elif args.operation == "check-pending": check_pending()
        elif args.operation == "prepare": prepare(args.story, args.commit, args.branch, args.output)
        elif args.operation == "package": package(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        # Do not include subprocess stderr or environment values: signing diagnostics may contain secrets.
        message = str(exc) if isinstance(exc, ValueError) else f"Distribution operation failed ({type(exc).__name__})"
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
