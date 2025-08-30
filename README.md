# mm-accounts-monitor

Multi-blockchain cryptocurrency account balance and domain name monitoring system.

## Overview

mm-accounts-monitor is a web application for automated tracking of cryptocurrency balances and domain names across multiple accounts on various blockchain networks:
- EVM-compatible chains (Ethereum, BSC, Arbitrum, Optimism, etc.)
- Solana
- Aptos
- StarkNet

## Key Features

- **Balance Monitoring**: Automated cryptocurrency balance checking across specified accounts
- **Domain Name Tracking**: Support for ENS (Ethereum Name Service), ANS (Aptos), StarkNet ID
- **Account Grouping**: Organize accounts into groups for convenient management
- **Change History**: Create snapshots and compare balance changes over time
- **Proxy Support**: Use proxy servers for RPC requests
- **Web Interface**: User-friendly interface for viewing monitoring results
- **Telegram Bot**: Integration for management via Telegram
- **Import/Export**: Support for TOML and ZIP formats for account groups

## Tech Stack

- **Python 3.13+**
- **FastAPI** — Web framework
- **SQLAlchemy** — Database operations
- **mm-base6** — Core application infrastructure
- **mm-eth, mm-sol, mm-apt, mm-strk** — Blockchain interaction libraries
- **Jinja2** — Web interface templating
- **Docker** — Application containerization
- **Ansible** — Deployment automation

## Installation & Setup

### Requirements

- Python 3.13 or higher
- uv (Python package installer)
- Docker and Docker Compose (optional)

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/mm-accounts-monitor.git
cd mm-accounts-monitor
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Run the application:
```bash
uv run python src/app/main.py
```

The application will be available at `http://localhost:3000`

### Docker Setup

1. Build the Docker image:
```bash
docker-compose -f docker/docker-compose.yml build
```

2. Run the container:
```bash
docker-compose -f docker/docker-compose.yml up
```

## Configuration

### Main Settings

Application settings are located in `src/app/config.py`:

- `mm_node_checker` — URL for RPC node service
- `proxies_url` — URL for loading proxy server list
- `check_balance_interval` — Balance check interval (minutes)
- `check_name_interval` — Domain name check interval (minutes)
- `limit_network_workers` — Number of parallel requests per network
- `limit_naming_workers` — Number of parallel requests to naming services

### Data Structure

#### Account Groups

Groups are stored in TOML format:
```toml
[group_name]
networks = ["ethereum", "arbitrum", "optimism"]
coins = ["ETH", "USDT", "USDC"]
namings = ["ens"]
accounts = [
    "0x1234567890123456789012345678901234567890",
    "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
]
```

#### Coins (Cryptocurrencies)

Coin configuration in TOML:
```toml
[ETH]
symbol = "ETH"
networks = ["ethereum", "arbitrum", "optimism"]
decimals = 18
```

## API & Interfaces

### Web Interface

- `/` — Main page with statistics
- `/groups` — Account group management
- `/balances` — View balances
- `/history` — Change history
- `/bot` — Bot management
- `/networks` — RPC node configuration
- `/coins` — Coin list management

### REST API

The application provides a REST API for programmatic access. Documentation is available at `/docs` (Swagger UI).

## Development

### Project Structure

```
mm-accounts-monitor/
├── src/app/
│   ├── core/           # Core business logic
│   │   ├── blockchains/  # Blockchain interaction modules
│   │   ├── services/     # Application services
│   │   └── db.py         # Database models
│   ├── server/         # Web server and routers
│   │   ├── routers/      # API endpoints
│   │   └── templates/    # HTML templates
│   ├── config.py       # Configuration
│   └── main.py         # Entry point
├── docker/             # Docker configuration
├── ansible/            # Ansible playbooks
└── tests/              # Tests
```

### Running Tests

```bash
uv run pytest
```

### Linting & Formatting

```bash
# Code checking
uv run ruff check .

# Formatting
uv run ruff format .

# Type checking
uv run mypy src
```

## Deployment

For server deployment using Ansible:

1. Configure `ansible/hosts.yml` with your servers
2. Run the playbook:
```bash
cd ansible
ansible-playbook -i hosts.yml playbook.yml
```

## License

This project is distributed under the MIT License. See LICENSE file for details.