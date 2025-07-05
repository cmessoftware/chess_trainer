apt-get update && \
    apt-get install -y stockfish && \
    apt-get clean


apt update && apt install -y curl git \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
       gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
       https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update && apt install -y gh

