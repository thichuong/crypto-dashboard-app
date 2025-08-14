#!/bin/bash
# Railway deployment script with migration

echo "🚀 Starting Railway deployment..."

# Detect Python environment
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    GUNICORN_CMD=".venv/bin/gunicorn"
    echo "📍 Using virtual environment: .venv"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    GUNICORN_CMD="gunicorn"
    echo "📍 Using system Python3"
else
    PYTHON_CMD="python"
    GUNICORN_CMD="gunicorn"
    echo "📍 Using system Python"
fi

# Run migration first
echo "📦 Running database migration..."
$PYTHON_CMD migrate_railway_v2.py

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed"
    echo "⚠️  Continuing with application start (migration might not be critical)"
fi

# Start the application
echo "🌟 Starting application..."
echo "   Binding to: 0.0.0.0:${PORT:-8000}"
echo "   Environment: ${RAILWAY_ENVIRONMENT:-development}"

# Start the application with optimized settings for Railway
exec $GUNICORN_CMD \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 2 \
    --timeout 300 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    run:app
