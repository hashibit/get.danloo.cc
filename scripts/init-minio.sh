#!/bin/bash

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
until curl -f http://localhost:9000/minio/health/live 2>/dev/null; do
  echo "MinIO is not ready yet..."
  sleep 2
done

echo "MinIO is ready! Creating bucket..."

# Install mc (MinIO client) if not present
if ! command -v mc &> /dev/null; then
    echo "Installing MinIO client..."
    curl https://dl.min.io/client/mc/release/linux-amd64/mc \
      --create-dirs \
      -o /usr/local/bin/mc
    chmod +x /usr/local/bin/mc
fi

# Configure MinIO client
mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Create bucket if it doesn't exist
if ! mc ls myminio/uploads 2>/dev/null; then
    echo "Creating uploads bucket..."
    mc mb myminio/uploads
    echo "Bucket created successfully!"
else
    echo "Bucket already exists."
fi

# Set bucket policy to allow public read access (optional, for development)
# mc policy set public myminio/uploads

echo "MinIO initialization complete!"