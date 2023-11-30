# AWS CDK Devcontainer Image

The source code used to build a VSCode Dev Container for those working with AWS CDK in Python.

This devcontainer is a swiss army knife for AWS with many official and 3rd-party AWS tools. It's not limited to AWS, either - it comes pre-packaged with a number of VSCode extensions, a robust Python toolchain (e.g. poetry, pip, pyenv, pipx, pylint, pylance), NodeJS (via NVM), kubectl, Helm, k9s, git, github CLI, and more.

## Under construction

:construction: under construction.

My latest build is available on from DockerHub at [berbs/aws-cdk-devcontainer](https://hub.docker.com/repository/docker/berbs/aws-cdk-devcontainer/general). Still work in progress and breaking changes possible until I get it dialed in.

## What's included

### Multi-architecture build

Multi-architecture build supports both x86-64 and ARM hosts.

If you want to run your container with a different architecture from your host machine, you can use the `--platform` argument in your `Dockerfile` or `devcontainer.json`.

For example, if you're on M1 / ARM but want to run x86-64, modify your Dockerfile as shown below:

```dockerfile
FROM --platform=linux/amd64 mcr.microsoft.com/devcontainers/base:bullseye
```

Or, you can specify the platform as a `RunArg` in `devcontainer.json`:

```json
{
  "build": {
    "runArgs": ["--platform=linux/amd64"]
  }
}
```

### NodeJS via NVM

- NodeJS via nvm (latest at time of last image build -> v21.2.0)

### Python via pyenv

- Python 3.11.6 (via pyenv)
- Poetry
- pyenv
- pip
- pipx
- pytest

### Easily change your shell's AWS profile with aws-profile CLI

This devcontainer provides a custom CLI tool, [aws-profile](./devcontainer/bin/aws-profile), that was originally inspired from one of my all-time AWS tools of the same name from [juhofriman/aws-profile-bash-prompt](https://github.com/juhofriman/aws-profile-bash-prompt/blob/master/aws-profile) and builds on it significantly.

This container image also includes the popular [aws-sso-util] CLI from [benkehoe/aws-sso-util](https://github.com/benkehoe/aws-sso-util) which also provided some of the inspiration for my `aws-profile` and [aws-console](#aws_console) CLI tool. Personally, I prefer my `aws-profile` and `aws-console` CLIs described in detail below, but both options are available to you.

#### Switching AWS profiles by name

If you mount your local `~/.aws/config` file `devcontainer.json` (or otherwise configure this file however you like), you can run `aws-profile <PROFILE>` from the command line to switch profiles:

```sh
aws-profile [name]
```

#### Switching AWS profiles by nickname

You can optionally add an `.awsprofile` file to your project root to provide profile nicknames:

```ini
dev=team1-account123-poweruser
prod=team1-account123-readonly
```

If you create an `.awsprofile`) `aws-profile` will first try to match the `[name]` argument in your nicknames and use the corresponding real profile name when switching profiles. If no matching nickname is found, `aws-profile` will then try to find a profile with that name in `~/.aws/config`.

#### Automatic AWS SSO login when switching profiles

`aws-profile` will check whether the profile you've selected is an AWS SSO profile and, if so, automatically run `aws sso login` if a previous AWS SSO login token has expired or is not found.

#### Support for Multiple AWS SSO Organizations

For those that work with multiple AWS Organizations, `aws-profile` supports multiple AWS SSO sessions in your ~/.aws/config. For example, if you have a configuration like below, `aws-profile company_a_dev` and `aws-profile company_b_prod` will automatically ask you to to log in to the appropriate AWS SSO portal:

#### Dynamic bash prompt with starship

This image includes [starship.rs](https://starship.rs/) which will automatically update your bash prompt to show you the current AWS profile and region, if any, that your AWS CLI is using.

Starship will also tell you:

- Current branch and git status
- Current working directory and user

```ini
[sso-session company_a]
sso_start_url = https://company_a.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access

[sso-session company_b]
sso_start_url = https://company_b.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access

[profile company_a_dev]
sso_session = company_a
sso_account_id = 999999999999
sso_role_name = PowerUserAccess
region = us-east-1
output = json

[profile company_b_prod]
sso_session = company_b
sso_account_id = 888888888888
sso_role_name = ReadOnlyAccess
region = us-west-2
output = json

```

#### Support for Chained Profiles

The `~/.aws/config` file allows you to specify a profile with a role ARN and chain it to another profile by specifying `source_profile`. If you have an assumed role profile that is ultimately derived from an AWS SSO profile, the `aws-profile` CLI will trace back to this source profile and - if your SSO token is expired - prompt you to log in as described earlier. All other assumed roles that do not use federated identity are also supported (as long as you've properly configured your ~/.aws/config file with valid access keys)

### Easy AWS Web Console access from shell command (aws-console)

TLDR; this works much like `aws-profile`) though isn't as fully-baked.

Under the hood, it's wrapping the `aws-sso-util` CLI from [benkehoe/aws-sso-util](https://github.com/benkehoe/aws-sso-util) to incorporate some of the convenience of the `aws-profile` CLI described above. I haven't baked this out quite as much... if you try it out, let me know how it goes!

## Auto-load environment variables with direnv

[direnv](https://direnv.net/) is an awesome tool that will automatically load environment variables into your shell when your current directory (or a parent directory) has a `.envrc` file and unload them if you move to a location that doesn't have `.envrc` in it or a parent directory. Envrc also supports many shell commands (certain things, like aliases and functions, are not supported).

**Example use case**: imagine you have a microservices repo with source code for several Lambda functions and and ECS or EKS containers that each have different sets of Python dependencies in their own requirements.txt, Pipfile, or pyproject.toml. You could add a `.envrc` in each of their directories with contents like below:

```sh

```

### AWS

- AWS CLI v2
- AWS SAM CLI
- AWS CDK
- AWS Session Manager CLI plugin
- AWS `git-remote-codecommit` credentials helper
- AWS eksctl
- AWS eksctl-anywhere
- AWS copilot
- aws-sso-util (3rd-party)

### Containers

- Docker CLI
- kubectl
- Helm
- k9s

This devcontainer uses the `docker-outside-of-docker` VSCode Dev Container feature that allows the Docker CLI within the devcontainer to use your hosts Docker installation (assuming your host has Docker installed!).

## General

- starship
- direnv
- jq

### VS Code extensions

This image comes with the VS Code extensions below. I've added comments to those that I find particularly useful.

- AWS Extensions

  - **AWS Toolkit** (`amazonwebservices.aws-toolkit-vscode`) - convenient resource browser (for some services), testing, building, uploading Lambda functions, access to Code Whisperer (free AI coding assistant), and a resource browser to view your CDK resources if a CDK project is detected.

  - **Type annotations for Boto3** (`Boto3typed.boto3-ide`) - provides _type annotations_ (woo!) for `boto3`

- NodeJS

  - ESLint (`dbaeumer.vscode-eslint`)

- Python

  - Python (`ms-python.python`)
  - Python environment manager (`donjayamanne.python-environment-manager`)
  - Python auto-indent (`KevinRose.vsc-python-indent`)
  - MyPy (`matangover.mypy`)
  - Pylance (`ms-python.vscode-pylance`)
  - isort (`ms-python.isort`)
  - Black (`ms-python.black-formatter`)
  - Jupyter (`ms-toolsai.jupyter`, `ms-toolsai.jupyter-keymap`)

- General

  - **Direnv** (`mkhl.direnv`) - auto-load environment variables based on the directory your shell is in, auto-remove them if you leave the directory.
  - **Paste Image** (`mushan.vscode-paste-image`) - Past images from clipboard directly into your Markdown files.
  - GitLens (`eamodio.gitlens`)
  - Dotenv (`mikestead.dotenv`)
  - Github PRs (`GitHub.vscode-pull-request-github`)
  - Postman (`Postman.postman-for-vscode`)
  - YAML support (`redhat.vscode-yaml`)
  - Better comments (`aaron-bond.better-comments`)
  - CodeSnap (`adpyke.codesnap`)

- Containers
  - Docker (`ms-azuretools.vscode-docker`)
  - Kubernetes tools (`ms-kubernetes-tools.vscode-kubernetes-tools`)
  - Remote containers (`ms-vscode-remote.remote-containers`)

## Creating and attaching to the devcontainer

1. In your project, create a `.devcontainer` directory and add a `devcontainer.json`:

```json
{
  "name": "VSCodeAWSDevContainer",
  "dockerFile": "Dockerfile",
  "mounts": [
    // Optional - allow use of Docker CLI within container
    "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind,consistency=cached",
    // Optional - leverage existing git configuration
    "source=${localEnv:HOME}${localEnv:USERPROFILE}/.gitconfig,target=/home/vscode/.gitconfig,type=bind,consistency=cached",
    // Optional - leverage existing AWS profiles
    "source=${localEnv:HOME}${localEnv:USERPROFILE}/.aws,target=/home/vscode/.aws,type=bind,consistency=cached"
  ],
  "workspaceFolder": "/workspace/${localWorkspaceFolderBasename}",
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace/${localWorkspaceFolderBasename},type=bind,consistency=cached"
}
```

2. Add a `Dockerfile` to the `.devcontainer` directory. You only need to start with the line below, though you can add whatever you want to it:

```dockerfile
FROM berbs/aws-cdk-devcontainer:latest
```

3. In VSCode, open the command panel (`CMD+Shift+P`) and use the `> Dev Containers: Rebuild Container`

4. VSCode will download the image and re-open your project workspace in the devcontainer. Over the next ~30 seconds or so, you'll notice that the extensions bar on the left begins to populate with the pre-installed extensions included in this project.

## Using the devcontainer

## Building image

> This is for my own reference. You can use the built container directly, if you prefer.

Switch to using buildkit to support multi-architecture build for both ARM and x86-64:

```sh
docker buildx create --use
```

Run this command from the host machine, one directory above the git project root directory:

```sh
devcontainer build --workspace-folder ./aws-cdk-devcontainer-image . --push true --image-name berbs/aws-cdk-devcontainer:latest --buildkit --platform linux/amd64,linux/arm64
```
