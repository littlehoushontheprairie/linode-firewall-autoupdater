# Update Linode Firewall

The Linode firewall uses an allowlist to prevent unwanted traffic on my server. This script is to update the allowlist in the Linode firewall automatically and runs its job every 5 minutes in the Docker conntainer.

## How to Run

1. Download repo
    - `git checkout develop`
    - `git pull`
    - `cd update-firewall`
2. Export environment variables
3. run docker-compose
    - `docker-compose up --build -d`

## Email Templates

The script reads in email templates everytime it is ran. You can customize the templates located in the _templates_ folder. They are read in as HTML files and are injected at runtime with the information.

### Structure

-   error.html - Error Template
-   index.html - Main Template

## Environment Variables

| Variable       | Required | Default | Example                        | Needed by                     |
| -------------- | -------- | ------- | ------------------------------ | ----------------------------- |
| FROM_EMAIL     | true     | ---     | from@example.com               | SMTP Server (send email from) |
| TO_EMAIL       | true     | ---     | to@example.com                 | SMTP Server (send email to)   |
| EMAIL_GREETING | true     | ---     | Laura                          | Template                      |
| PROXY_URL      | true     | ---     | nginx.example.com              | Template                      |
| SMTP_URL       | true     | ---     | smtp.example.com               | SMTP Server                   |
| SMTP_PORT      | true     | ---     | 465                            | SMTP Server                   |
| SMTP_EMAIL     | true     | ---     | laura@example.com              | SMTP Server                   |
| SMTP_PASSWORD  | true     | ---     | 8f5cd6729h0v5d247vc190ddcs4l2a | SMTP Server                   |

**NOTE:** For security purposes, it is strong recommended that you use a generated API passwords.
