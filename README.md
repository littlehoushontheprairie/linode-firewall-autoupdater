# linode-update-firewall

The Linode firewall uses an allowlist to prevent unwanted traffic on my server. This script is to update the allowlist in the Linode firewall automatically and runs its job every 5 minutes in the Docker conntainer.

## How to Run

1. Download repo
    - `git checkout develop`
    - `git pull`
    - `cd linode-update-firewall`
2. Export environment variables
3. run docker-compose
    - `docker-compose up --build -d`
