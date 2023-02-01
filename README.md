# linode-update-firewall

This script runs its job every 5 minutes in the Docker conntainer. This will help isolate any issues and deploy in multiple environments.

## How to Run

1. Download repo
    - `git checkout develop`
    - `git pull`
    - `cd linode-update-firewall`
2. Export environment variables
3. run docker-compose
    - `docker-compose up --build -d`
