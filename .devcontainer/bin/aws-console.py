import argparse
import configparser
import getpass
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional, Union

import boto3
import dateutil.parser
from botocore.exceptions import (
    NoAuthTokenError,
    SSOError,
    SSOTokenLoadError,
    TokenRetrievalError,
    UnauthorizedSSOTokenError,
)
from dateutil.tz import UTC, tzlocal

WORKSPACE_DIR = os.environ["DEVCONTAINER_WORKSPACE_FOLDER"]
NICKNAMES_FILE = f"{WORKSPACE_DIR}/.awsprofile"
AWS_CONFIG_FILE = os.path.expanduser("~/.aws/config")
AWS_SSO_CACHE_PATH = "{$HOME}/.aws/sso/cache"

AWS_CONFIG = configparser.ConfigParser()
AWS_CONFIG.read(AWS_CONFIG_FILE)


class File:
    @staticmethod
    def load_json(file_path: str) -> Any | None:
        with open(file_path) as context:
            return json.load(context)

    @staticmethod
    def exists(file_path: str) -> bool:
        if os.path.exists(file_path):
            return True
        else:
            return False


def get_sso_cached_login(profile: str):
    # https://github.com/NeilJed/aws-sso-credentials/blob/master/awssso#L110-L137
    print("\nChecking for SSO credentials...")

    profile_config = get_config_section(profile, section_type="profile")
    session_name = profile_config["sso_session"]
    session_config = get_config_section(session_name, section_type="sso-session")

    # print(f"CONFIG is {vars(profile_config)}")
    cache_token_id = hashlib.sha1(
        session_config["sso_start_url"].encode("utf-8")
    ).hexdigest()
    sso_cache_file = f"{AWS_SSO_CACHE_PATH}/{cache_token_id}.json"

    print(f"Looking for token: {cache_token_id}")

    if not Path(sso_cache_file).is_file():
        print("Cached SSO tokens not present or expired.")
        return None
    else:
        data = load_json(sso_cache_file)

        if not data:
            print(f"Failed to load token from {sso_cache_file}.")
            return None

        now = datetime.now().astimezone(UTC)
        expires_at = dateutil.parser.parse(data["expiresAt"]).astimezone(UTC)

        if data.get("region") != session_config["sso_region"]:
            raise Exception(
                "SSO authentication region in cache does not match region defined in profile"
            )

        if now > expires_at:
            print("SSO credentials have expired.")

        print(
            f"Found valid cached SSO credentials. Valid until {expires_at.astimezone(tzlocal())}"
        )
        return data


class AwsProfile:
    name: str
    nickname: str


def get_aws_profile_from_nickname(nickname: str) -> Union[str, None]:
    if file_exists(NICKNAMES_FILE):
        try:
            with open(NICKNAMES_FILE, "r", encoding="UTF-8") as f:
                # Read key-value pairs into a dictionary while skipping empty lines and comments
                nicknames_dict = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split(":")
                        nicknames_dict[key] = value
                return nicknames_dict.get(nickname)
        except Exception as e:
            print(f"Failed to parse ${NICKNAMES_FILE}: {e}")
    return None


def is_sso_profile(profile_name: str):
    config = get_config_section(profile_name, section_type="profile")
    has_sso_session = 1 if "sso_session" in config else 0
    has_sso_role = 1 if "sso_role_name" in config else 0
    has_sso_account = 1 if "sso_account_id" in config else 0
    sso_score = has_sso_session + has_sso_role + has_sso_account

    if sso_score == 3:
        return True
    elif sso_score == 0:
        return False
    else:
        raise Exception(
            "Error: profile ${profile_name} in ~/.aws/config appears to be misconfigured because it "
            "has an incomplete set of attributes needed for an SSO-backed profile. Ether all or none "
            "of the following should be specified: sso_session, sso_role_name, sso_account_id"
        )


class SsoLoginFailed(Exception):
    pass


def initiate_new_sso_login(profile: str):
    result = subprocess.run(
        ["aws", "sso", "login", "--profile", profile], capture_output=True, text=True
    )
    if result.returncode != 0:
        "Error: AWS SSO login failed."
        sys.exit()


def get_profile_identity(profile: str) -> dict:
    session = boto3.Session(profile_name=profile)
    sts = session.client("sts")
    return sts.get_caller_identity()


def validate_profile_and_get_identity(profile: str):
    identity = None
    if is_sso_profile(profile):
        try:
            identity = get_profile_identity(profile)
        except (
            SSOError,
            SSOTokenLoadError,
            UnauthorizedSSOTokenError,
            TokenRetrievalError,
            NoAuthTokenError,
        ) as e:
            print("No valid existing SSO token found. Let start a new session...")
            initiate_new_sso_login(profile)
    else:
        try:
            identity = get_profile_identity(profile)
        except Exception as e:
            print("Error: failed to validate credentials for profile ${profile}")
            print(e)
            sys.exit()
    return identity


def get_requested_name_from_args() -> str:
    parser = argparse.ArgumentParser(
        description="Open a bash subshell with AWS profile environment variables"
    )
    parser.add_argument("profile", type=str, help="AWS profile name or nickname")
    return parser.parse_args().profile


class ProfileNotInAwsConfig(Exception):
    pass


SectionType = Literal["profile", "sso-session"]


def is_chained_profile(profile: str):
    profile_config = get_config_section(profile, section_type="profile")

    if "role_arn" in profile_config and "source_profile" in profile_config:
        return True
    else:
        return False


def get_config_section(section_name: str, *, section_type: SectionType):
    section_heading = f"{section_type} {section_name}"
    if section_heading in AWS_CONFIG.sections():
        return AWS_CONFIG[section_heading]
    else:
        print(f"Section '{section_heading}' not found in {AWS_CONFIG_FILE}")
        print("Available profiles:")
        for option in AWS_CONFIG.sections():
            print(option[8:]) if option[:7] == "profile" else None
        sys.exit()


def get_root_profile_of_chained_profile(profile: str):
    profile_config = get_config_section(profile, section_type="profile")
    if "source_profile" in profile_config:
        parent_profile = profile_config["source_profile"]
        return get_root_profile_of_chained_profile(parent_profile)
    else:
        return profile


@dataclass
class AwsSubshell:
    requested_profile: str
    chained_root_profile: Optional[str] = None
    check_for_valid_sso_token: Optional[bool] = False


def run_git_command(command):
    try:
        return (
            subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        return None


BLACK: str = r"\[\e[0;30m\]"
BLUE: str = r"\[\e[0;34m\]"
GREEN: str = r"\[\e[0;32m\]"
CYAN: str = r"\[\e[0;36m\]"
RED: str = r"\[\e[0;31m\]"
PURPLE: str = r"\[\e[0;35m\]"
BROWN: str = r"\[\e[0;33m\]"
LIGHT_GRAY: str = r"\[\e[0;37m\]"
DARK_GRAY: str = r"\[\e[1;30m\]"
LIGHT_BLUE: str = r"\[\e[1;34m\]"
LIGHT_GREEN: str = r"\[\e[1;32m\]"
LIGHT_CYAN: str = r"\[\e[1;36m\]"
LIGHT_RED: str = r"\[\e[1;31m\]"
LIGHT_PURPLE: str = r"\[\e[1;35m\]"
YELLOW: str = r"\[\e[1;33m\]"
WHITE: str = r"\[\e[1;37m\]"
RESET: str = r"\[\e[0m\]"


def get_bash_prompt_for_profile(requested_profile: str):
    # Check git status
    hide_status = (
        run_git_command("git config --get devcontainers-theme.hide-status") != "1"
        and run_git_command("git config --get codespaces-theme.hide-status") != "1"
    )

    branch = run_git_command(
        "git --no-optional-locks symbolic-ref --short HEAD"
    ) or run_git_command("git --no-optional-locks rev-parse --short HEAD")

    show_dirty = (
        run_git_command("git config --get devcontainers-theme.show-dirty") == "1"
    )

    is_dirty = run_git_command(
        'git --no-optional-locks ls-files --error-unmatch -m --directory --no-empty-directory -o --exclude-standard ":/*"'
    )

    username = os.getenv("GITHUB_USER") or getpass.getuser()

    # Check for AWS_PROFILE_PS1 and GITHUB_USER
    ps1_profile = f"{YELLOW}(⚙{requested_profile}){RESET}"

    ps1_user = f"{GREEN}{username}"

    ps1_dirty = f" {YELLOW}✗" if show_dirty and is_dirty else ""

    ps1_branch = f"{CYAN}({LIGHT_RED}{branch}{ps1_dirty}{CYAN})"

    ps1_workdir = f"{LIGHT_BLUE}\\w{RESET}"

    # Construct the prompt
    prompt = f"{ps1_user} ➜ {ps1_workdir} {ps1_branch} {ps1_profile} $ "

    return prompt


def main():
    # This might be a nickname or it might be a real profile name
    requested_name = get_requested_name_from_args()

    # Check if requested value in nickname file and if not, assume an explicit profile was requested
    requested_profile = get_aws_profile_from_nickname(requested_name) or requested_name

    profile_config = get_config_section(requested_profile, section_type="profile")

    if is_sso_profile(requested_profile):
        print("SSO profile")
        session_name = profile_config["sso_session"]
        profile_account = profile_config["sso_account_id"]
        profile_role = profile_config["sso_role_name"]
        profile_region = profile_config.get("region")

        session_config = get_config_section(session_name, section_type="sso-session")
        sso_start_url = session_config.get("sso_start_url")
        sso_region = session_config.get("sso_region")
        if sso_start_url and sso_region:
            console_command = f"""aws-sso-util console launch --sso-start-url {sso_start_url} --sso-region {sso_region} --account-id {profile_account} --role-name {profile_role} """
            console_command += f"--region {profile_region}" if profile_region else ""

            print(console_command)
            subprocess.Popen(console_command.split())

        else:
            raise Exception(
                f"Section for [sso-session $session_name] in ~/.aws/config appears misconfigured"
                "because it's missing one or both of the following required settings: sso_start_url, "
                "sso_region"
            )


if __name__ == "__main__":
    main()
