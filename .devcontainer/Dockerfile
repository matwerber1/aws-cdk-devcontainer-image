FROM --platform=$BUILDPLATFORM mcr.microsoft.com/devcontainers/base:bullseye

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        # Python build dependencies
        build-essential \
        curl \
        libbz2-dev \
        libffi-dev \
        liblzma-dev \
        libncurses5-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        llvm \
        make \
        tk-dev \
        xz-utils \
        zlib1g-dev \
        # General requirements, tools, preferences
        #-------
        # Secure APT transport for HTTPS
        apt-transport-https \
        # Compression tool (BZ2 format)
        bzip2 \
        # Root CA certificates for SSL/TLS
        ca-certificates \
        # Tool for creating text user interfaces
        dialog \
        # Environment switcher for shell
        direnv \
        # Server for managing certificate revocation
        dirmngr \
        # Font configuration and customization library
        fontconfig \
        # Distributed version control system
        git \
        # GNU C Library sources
        glibc-source \
        # GNU Privacy Guard for encryption
        gnupg2 \
        # GNU Objective-C/C++ compiler
        gobjc++ \
        # Interactive process viewer
        htop \
        # Helpers for all init systems
        init-system-helpers \
        # Networking and traffic control tools
        iproute2 \
        # Command-line JSON processor
        jq \
        # File pager program, similar to more
        less \
        # Kerberos 5 GSS-API library
        libgssapi-krb5-2 \
        # International Components for Unicode
        libicu[0-9][0-9] \
        # Kerberos 5 authentication library
        libkrb5-3 \
        # LTTng Userspace Tracer library
        liblttng-ust[0-9] \
        # GNU Standard C++ Library v3
        libstdc++6 \
        # Common files for locale support
        locales \
        # Linux Standard Base version reporting
        lsb-release \
        # Utility to list open files
        lsof \
        # On-line manual pager
        man-db \
        # Manual pages for Linux
        manpages \
        # Development manual pages
        manpages-dev \
        # Small, easy-to-use text editor
        nano \
        # Disk usage analyzer with ncurses
        ncdu \
        # Networking tools
        net-tools \
        # Secure shell (SSH) client, for secure access
        openssh-client \
        # Python package installer
        pip \
        # Utilities for process monitoring
        procps \
        # Utilities for managing processes on the system
        psmisc \
        # Fast, versatile file copying tool
        rsync \
        # Manage software repositories
        software-properties-common \
        # System call tracer
        strace \
        # Execute commands as another user
        sudo \
        # Displays directory tree in terminal
        tree \
        # De-archiver for .zip files
        unzip \
        # Vi IMproved - enhanced vi editor - compact version
        vim-tiny \
        # Retrieves files from the web
        wget \
        # Package and compress (archive) files
        zip \
        # Compression library - runtime
        zlib1g \
    &&  update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Pyenv globally
ARG PYTHON_VERSION=3.11.6
ENV PYENV_ROOT=/usr/local/pyenv
ENV PATH=$PYENV_ROOT/bin:${PATH}

# Install pyenv
RUN git clone https://github.com/pyenv/pyenv.git ${PYENV_ROOT}
ENV PATH=${PYENV_ROOT}/shims:${PATH}

# Grant access to pyenv shims to default user
ARG USER=vscode
RUN groupadd pyenvgroup && \
    usermod -a -G pyenvgroup ${USER} && \
    chown -R :pyenvgroup ${PYENV_ROOT} && \
    chmod -R 775 ${PYENV_ROOT} & \
    pyenv rehash

# Initialize pyenv upon login
RUN echo 'eval "$(pyenv init -)"' >> /etc/profile.d/pyenv.sh

RUN pyenv install $PYTHON_VERSION

# Set global Python version
RUN pyenv global ${PYTHON_VERSION}

# Ensure bash is used for subsequent commands b/c pyenv relies heavily on bash, and install pipx globally
SHELL ["/bin/bash", "-c"]
RUN source /etc/profile.d/pyenv.sh && \
    pip install pipx && \
    pipx ensurepath

# Add GitHub CLI repository and install the CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && \
    apt-get install -y gh

# Install Poetry globally
RUN curl -sSL https://install.python-poetry.org | python -

# Install pipenv
RUN pip install pipenv

# Install pytest globally
RUN pipx install pytest

# Add Pyenv init to the bashrc for all users
RUN echo 'eval "$(pyenv init - --no-rehash)"' >> /etc/bash.bashrc

# Install NVM as root
ENV NVM_DIR /usr/local/nvm
ARG NODE_VERSION=stable
ENV NODE_VERSION=${NODE_VERSION}
RUN mkdir -p $NVM_DIR
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

# # Add NVM binaries to PATH for all users
#ENV NODE_PATH $NVM_DIR/versions/node/v`cat $NVM_DIR/alias/default`/lib/node_modules
#ENV PATH      $NVM_DIR/versions/node/v`cat $NVM_DIR/alias/default`/bin:$PATH
# Add NVM setup to a global profile script to be sourced for all users
RUN echo 'export NVM_DIR="$NVM_DIR"' >> /etc/profile.d/nvm.sh \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> /etc/profile.d/nvm.sh \
    && echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> /etc/profile.d/nvm.sh \
    && chmod +x /etc/profile.d/nvm.sh

# Set PATH for all users to find node
RUN echo 'export PATH=$NVM_DIR/versions/node/`ls $NVM_DIR/versions/node/ | sort -V | tail -n1`/bin:$PATH' >> /etc/profile.d/nvm.sh

# Install AWS Systems Manager  CLI Plugin
# Define a build argument for the target architecture
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "amd64" ]; then \
      curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o session-manager-plugin.deb; \
      dpkg -i session-manager-plugin.deb; \
      rm session-manager-plugin.deb; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
      curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_arm64/session-manager-plugin.deb" -o session-manager-plugin.deb; \
      dpkg -i session-manager-plugin.deb; \
      rm session-manager-plugin.deb; \
    fi

# # Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod o+rx ./kubectl && \
    mv ./kubectl /usr/local/bin/kubectl

# # Install eksctl
RUN curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz"
RUN curl -sL "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_checksums.txt" | grep Linux_amd64 | sha256sum --check
RUN tar -xzf eksctl_Linux_amd64.tar.gz -C /tmp && rm eksctl_Linux_amd64.tar.gz
RUN  mv /tmp/eksctl /usr/local/bin

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws

# Install EKS Anywhere
ARG EKS_ANYWHERE_RELEASE_VERSION=v0.18.2
ENV EKS_ANYWHERE_TARBALL_URL=https://anywhere-assets.eks.amazonaws.com/releases/eks-a/53/artifacts/eks-a/${EKS_ANYWHERE_RELEASE_VERSION}/darwin/amd64/eksctl-anywhere-${EKS_ANYWHERE_RELEASE_VERSION}-darwin-amd64.tar.gz
RUN curl $EKS_ANYWHERE_TARBALL_URL \
    --silent --location \
    | tar xz ./eksctl-anywhere && \
    mv ./eksctl-anywhere /usr/local/bin/

# Install k9s
RUN curl -sS https://webinstall.dev/k9s | bash

# Install Helm
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install aws-sso-util
RUN pip install aws-sso-util

# Install type annotations for AWS SDK in Python
RUN pip install \
    boto3-stubs[all]

# Install AWS Copilot for ECS
RUN curl -Lo copilot https://github.com/aws/copilot-cli/releases/download/v1.32.0/copilot-linux && \
    chmod +x copilot && \
    mv copilot /usr/local/bin/copilot

# Font and setup for starship
ARG NERD_FONT_NAME="FiraCode"
ENV FONT_DIR="/usr/local/share/fonts/"
RUN mkdir -p $FONT_DIR && \
    cd $FONT_DIR && curl -fLO "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.1.1/$NERD_FONT_NAME.zip" && \
    unzip $FONT_NAME && \
    rm $NERD_FONT_NAME.zip && \
    fc-cache -fv

ENV DEVCONTAINER_ASSETS_DIR=/devcontainer

RUN mkdir -p $DEVCONTAINER_ASSETS_DIR/templates &&\
    mkdir -p $DEVCONTAINER_ASSETS_DIR/config

COPY --chmod=755 ./bin/* /usr/local/bin/
COPY --chmod=666 ./templates/* $DEVCONTAINER_ASSETS_DIR/templates/
COPY --chmod=666 ./config/starship.toml $DEVCONTAINER_ASSETS_DIR/config/starship.toml

ENV STARSHIP_CONFIG="$DEVCONTAINER_ASSETS_DIR/config/starship.toml"
RUN curl -O https://starship.rs/install.sh && \
    chmod +x install.sh && \
    ./install.sh -y && \
    echo $'\neval "$(starship init bash)"\n' >> /etc/bash.bashrc

RUN echo $'\neval "$(direnv hook bash)"\n' >> /etc/bash.bashrc

ENV DOCKER_BUILDKIT=1