#!/bin/bash
# Main run script for BlueAbel AIOS
# This script starts the API server and Flask UI

# Configuration
CONFIG_FILE="server_config.json"
API_PORT=$(jq -r '.api.port' $CONFIG_FILE)
FLASK_PORT=$(jq -r '.ui.flask.port' $CONFIG_FILE)

# Function to check if a port is in use
is_port_in_use() {
  lsof -i :$1 > /dev/null 2>&1
  return $?
}

# Kill existing processes if needed
if is_port_in_use $API_PORT; then
  echo "Port $API_PORT is in use. Attempting to kill the process..."
  lsof -ti :$API_PORT | xargs kill -9
  sleep 1
fi

if is_port_in_use $FLASK_PORT; then
  echo "Port $FLASK_PORT is in use. Attempting to kill the process..."
  lsof -ti :$FLASK_PORT | xargs kill -9
  sleep 1
fi

# Start API server in the background
echo "Starting API server on port $API_PORT..."
python -m app.main &
API_PID=$!
echo $API_PID > server.pid
echo "API server started with PID $API_PID"

# Wait for API to start
echo "Waiting for API server to start..."
while ! curl -s http://localhost:$API_PORT/status > /dev/null; do
  sleep 1
  echo "Waiting for API server..."
done
echo "API server is running!"

# Start Flask UI
echo "Starting Flask UI on port $FLASK_PORT..."
python run_flask_ui.py &
UI_PID=$!
echo $UI_PID >> server.pid
echo "Flask UI started with PID $UI_PID"

echo "BlueAbel AIOS is now running!"
echo "API: http://localhost:$API_PORT"
echo "UI:  http://localhost:$FLASK_PORT"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for termination signal
wait $API_PID