#!/bin/bash
# Improved Railway deployment script with better error handling

set -e  # Exit on any error

echo "🚀 Starting Railway deployment v2.0..."
echo "=================================="

# Environment check
echo "🔍 Environment Information:"
echo "   PORT: ${PORT:-Not set}"
echo "   RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-Not set}"
echo "   DATABASE_URL: $(if [ -n "$DATABASE_URL" ]; then echo "✅ Set"; else echo "❌ Not set"; fi)"

# Run migration with improved script
echo ""
echo "📦 Running database migration..."
python migrate_railway_v2.py

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed"
    echo "⚠️  Continuing with application start (migration might not be critical)"
fi

echo ""
echo "🌟 Starting application..."
echo "   Binding to: 0.0.0.0:${PORT:-8000}"
echo "   Workers: 2"
echo "   Environment: ${RAILWAY_ENVIRONMENT:-development}"

# Start the application with optimized settings for Railway
exec gunicorn \
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
