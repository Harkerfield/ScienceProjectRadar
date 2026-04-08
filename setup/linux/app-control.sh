#!/bin/bash
# Radar Application - Linux/Pi Control Script
# Manage application services and checking status

set -e

APPNAME="radar-app"
COMMAND=${1:-status}

case "$COMMAND" in
    status)
        echo ""
        echo "📊 Radar Application Status"
        echo ""
        
        echo "🖥️  Server:"
        if pgrep -f "npm.*start" > /dev/null; then
            PID=$(pgrep -f "npm.*start" | head -1)
            echo "   ✅ Running (PID: $PID)"
        else
            echo "   ❌ Not running"
        fi
        
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo "   ✅ Port 3000 responding"
        else
            echo "   ❌ Port 3000 not responding"
        fi
        
        echo ""
        echo "🎨 Client (Dev):"
        if pgrep -f "npm.*dev" > /dev/null; then
            PID=$(pgrep -f "npm.*dev" | head -1)
            echo "   ✅ Running (PID: $PID)"
        else
            echo "   ❌ Not running"
        fi
        
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            echo "   ✅ Port 5173 responding"
        else
            echo "   ⚠️  Port 5173 not responding (expected in production)"
        fi
        
        echo ""
        echo "🔌 Services (if using systemd):"
        systemctl is-active --quiet $APPNAME && echo "   ✅ $APPNAME service running" || echo "   ❌ $APPNAME service not running"
        
        echo ""
        ;;
    
    start)
        echo "🚀 Starting Radar Application..."
        
        # Start server
        echo "  Starting server..."
        cd "${SERVER_DIR:-RaspberryPiRadarFullStackApplicationAndStepperController/server}"
        npm start &
        SERVER_PID=$!
        cd - > /dev/null
        
        # Wait for server
        sleep 3
        
        # Start client
        echo "  Starting client..."
        cd "${CLIENT_DIR:-RaspberryPiRadarFullStackApplicationAndStepperController/client}"
        npm run dev &
        CLIENT_PID=$!
        cd - > /dev/null
        
        echo "✅ Started"
        echo "   Server PID: $SERVER_PID"
        echo "   Client PID: $CLIENT_PID"
        ;;
    
    stop)
        echo "🛑 Stopping Radar Application..."
        pkill -f "npm.*start" || true
        pkill -f "npm.*dev" || true
        echo "✅ Stopped"
        ;;
    
    restart)
        echo "🔄 Restarting Radar Application..."
        $0 stop
        sleep 2
        $0 start
        ;;
    
    logs)
        echo "📋 Recent logs:"
        if systemctl is-active --quiet $APPNAME 2>/dev/null; then
            journalctl -u $APPNAME -n 50 --no-pager
        else
            echo "ℹ️  Service not active. Check running processes:"
            ps aux | grep -E "npm|node" | grep -v grep
        fi
        ;;
    
    test)
        echo "🧪 Testing connectivity..."
        echo ""
        
        echo "  Testing server on port 3000..."
        if curl -s -m 5 http://localhost:3000 > /dev/null; then
            echo "  ✅ Server responding"
        else
            echo "  ❌ Server not responding"
        fi
        
        echo ""
        echo "  Testing client dev server on port 5173..."
        if curl -s -m 5 http://localhost:5173 > /dev/null; then
            echo "  ✅ Client responding"
        else
            echo "  ℹ️  Client not responding (may not be running in production)"
        fi
        
        echo ""
        ;;
    
    *)
        echo "Usage: $0 {status|start|stop|restart|logs|test}"
        echo ""
        echo "Commands:"
        echo "  status   - Show application status"
        echo "  start    - Start servers"
        echo "  stop     - Stop servers"
        echo "  restart  - Restart servers"
        echo "  logs     - Show recent logs"
        echo "  test     - Test connectivity"
        echo ""
        exit 1
        ;;
esac
