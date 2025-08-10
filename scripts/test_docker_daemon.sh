#!/bin/bash
# Test script to diagnose Docker daemon connectivity issues

echo "=== Docker Daemon Connectivity Test ==="
echo "Date: $(date)"
echo "Host: $(hostname)"
echo

echo "1. Checking if Docker client is installed..."
if command -v docker &> /dev/null; then
    echo "✅ Docker client is installed: $(docker --version)"
else
    echo "❌ Docker client is not installed"
    exit 1
fi

echo
echo "2. Checking Docker daemon connectivity..."
echo "DOCKER_HOST: ${DOCKER_HOST:-not set}"
echo "DOCKER_TLS_CERTDIR: ${DOCKER_TLS_CERTDIR:-not set}"

echo
echo "3. Testing Docker daemon connection..."
if timeout 10 docker version &> /dev/null; then
    echo "✅ Docker daemon is accessible"
    docker version
else
    echo "❌ Docker daemon is not accessible"
    echo "Attempting to get more details..."
    docker version 2>&1 || true
fi

echo
echo "4. Testing Docker info command..."
if timeout 10 docker info &> /dev/null; then
    echo "✅ Docker info command works"
    docker info | head -20
else
    echo "❌ Docker info command failed"
    docker info 2>&1 || true
fi

echo
echo "5. Checking network connectivity to Docker daemon..."
if [ -n "$DOCKER_HOST" ]; then
    # Extract host and port from DOCKER_HOST (e.g., tcp://docker:2375)
    DOCKER_DAEMON_HOST=$(echo $DOCKER_HOST | sed 's|tcp://||' | cut -d':' -f1)
    DOCKER_DAEMON_PORT=$(echo $DOCKER_HOST | sed 's|tcp://||' | cut -d':' -f2)
    
    echo "Testing connection to $DOCKER_DAEMON_HOST:$DOCKER_DAEMON_PORT..."
    
    if command -v nc &> /dev/null; then
        if timeout 5 nc -z $DOCKER_DAEMON_HOST $DOCKER_DAEMON_PORT; then
            echo "✅ Network connection to Docker daemon is working"
        else
            echo "❌ Cannot connect to Docker daemon at $DOCKER_DAEMON_HOST:$DOCKER_DAEMON_PORT"
        fi
    else
        echo "netcat not available, trying telnet..."
        if timeout 5 telnet $DOCKER_DAEMON_HOST $DOCKER_DAEMON_PORT &> /dev/null; then
            echo "✅ Network connection to Docker daemon is working"
        else
            echo "❌ Cannot connect to Docker daemon at $DOCKER_DAEMON_HOST:$DOCKER_DAEMON_PORT"
        fi
    fi
else
    echo "DOCKER_HOST not set, assuming local socket"
    if [ -S /var/run/docker.sock ]; then
        echo "✅ Docker socket exists at /var/run/docker.sock"
        ls -la /var/run/docker.sock
    else
        echo "❌ Docker socket not found at /var/run/docker.sock"
    fi
fi

echo
echo "6. Checking Docker service status (if available)..."
if command -v systemctl &> /dev/null; then
    systemctl status docker 2>&1 || echo "systemctl not available or Docker service not found"
elif command -v service &> /dev/null; then
    service docker status 2>&1 || echo "service command not available or Docker service not found"
else
    echo "No service management tools available"
fi

echo
echo "7. Checking for Docker processes..."
ps aux | grep docker | grep -v grep || echo "No Docker processes found"

echo
echo "8. Environment variables..."
env | grep -i docker | sort

echo
echo "=== Test Complete ==="