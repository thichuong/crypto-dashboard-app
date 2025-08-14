#!/bin/bash
# Railway deployment script with migration

echo "🚀 Starting Railway deployment..."

# Run migration first
echo "📦 Running database migration..."
python migrate_railway.py

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

# Start the application
echo "🌟 Starting application..."
exec gunicorn --bind 0.0.0.0:$PORT run:app
