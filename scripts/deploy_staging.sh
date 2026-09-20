#!/bin/bash
# Placeholder deploy script for staging
python -c "from dev.db import init_db; init_db()"
echo 'deployed (placeholder)'
