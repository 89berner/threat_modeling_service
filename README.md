** IMPORTANT ** This is just a show case version, this is not expected to be run in production.

# Threat Modeling Service

An interactive threat modeling assistant that uses OpenAI to help guide users through the threat modeling process.

## Setup Options

### Option 1: Local Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export OPENAI_API_KEY=your_openai_api_key
export FLASK_SECRET_KEY=your_secure_random_string
export OPENAI_MODEL=gpt-4  # Optional, defaults to gpt-4
```

3. Run the application:
```bash
python app.py
```

### Option 2: Docker Compose

1. Create a `.env` file in the project root with the following variables:
```bash
OPENAI_API_KEY=your_openai_api_key
FLASK_SECRET_KEY=your_secure_random_string
```

2. Build and start the container:
```bash
docker-compose up -d
```

3. Access the application at http://localhost:5000

4. To stop the service:
```bash
docker-compose down
```

## Security Note

This application requires a secure `FLASK_SECRET_KEY` to protect session data. Make sure to use a strong random string for production deployments.