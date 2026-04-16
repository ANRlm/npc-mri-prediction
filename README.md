# NPC MRI Prognosis Prediction Platform

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9-blue.svg)
![React](https://img.shields.io/badge/react-18.3-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)

A comprehensive web-based platform for Nasopharyngeal Carcinoma (NPC) prognosis prediction using MRI imaging analysis and machine learning. The system provides survival prediction, risk stratification, and clinical decision support through an intuitive interface.

## Features

- **User Authentication**: Secure registration and login system with JWT-based authentication
- **MRI Image Analysis**: Upload and process NIfTI format MRI images (T1, T2, T1C) with automatic feature extraction
- **Survival Prediction**: Cox proportional hazards model for personalized survival rate prediction (1-year, 3-year, 5-year)
- **Risk Stratification**: Automatic classification into high-risk and low-risk groups based on optimal thresholds
- **Interactive Visualizations**: Dynamic survival curves, risk score distributions, and comparative analysis charts
- **Clinical Decision Support**: Automated generation of follow-up recommendations based on risk assessment
- **Prediction History**: Complete audit trail of all predictions with filtering and search capabilities
- **Model Performance Metrics**: Real-time display of C-index, AUC, sensitivity, and specificity
- **File Management**: Upload, download, and manage clinical data files
- **Responsive Design**: Modern, mobile-friendly interface built with React and Tailwind CSS

## Technology Stack

### Backend
- **Framework**: Flask 2.3.3
- **Database**: MongoDB 
- **Authentication**: Flask-JWT-Extended with bcrypt password hashing
- **Machine Learning**: scikit-survival (Cox model), scikit-learn, lifelines
- **Image Processing**: nibabel, OpenCV, mahotas, scikit-image
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib
- **API Security**: Flask-Limiter for rate limiting, Flask-CORS for cross-origin requests

### Frontend
- **Framework**: React 18.3 with TypeScript
- **Build Tool**: Vite 5.4
- **Styling**: Tailwind CSS 3.4
- **Routing**: React Router DOM 6.27
- **State Management**: Zustand 5.0
- **Charts**: Recharts 2.13
- **Animations**: Framer Motion 11.11
- **Icons**: Lucide React
- **HTTP Client**: Axios 1.7

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (frontend reverse proxy)
- **Python Version**: 3.9
- **Node Version**: Compatible with Vite 5.x

## Architecture Overview

The platform follows a modern 3-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│  React SPA (Port 80) - User Interface & Visualization       │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST API
┌─────────────────────────▼───────────────────────────────────┐
│                      Application Layer                       │
│  Flask API (Port 5001) - Business Logic & ML Inference      │
│  - Authentication & Authorization                            │
│  - Feature Extraction from MRI Images                        │
│  - Cox Model Prediction                                      │
│  - Survival Curve Generation                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │ MongoDB Protocol
┌─────────────────────────▼───────────────────────────────────┐
│                        Data Layer                            │
│  MongoDB (Port 27017) - Persistent Storage                   │
│  - User Accounts                                             │
│  - Prediction History                                        │
│  - Clinical Data                                             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **System Requirements**:
  - 4GB RAM minimum (8GB recommended)
  - 10GB free disk space
  - Linux, macOS, or Windows with WSL2

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd MRI
```

### 2. Prepare Model Files

Place your trained model files in the `MRI_backend/models/` directory:

```
MRI_backend/models/
├── adasyn_cox_model.pkl      # Trained Cox model
├── scaler.pkl                 # Feature scaler
└── adasyn_model_info.pkl      # Model metadata
```

### 3. Prepare Data Files

Place your feature data in the `MRI_backend/data/` directory:

```
MRI_backend/data/
└── flat_statistics.csv        # Pre-extracted features (for /api/predict)
```

### 4. Configure Environment Variables

Create a `.env` file in the project root (optional, defaults are provided):

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secure-secret-key-here
JWT_EXPIRES_DAYS=7

# Registration Code (for demo mode)
REGISTER_CODE=123456

# Model Paths (relative to /app in container)
MODEL_PATH=models/adasyn_cox_model.pkl
SCALER_PATH=models/scaler.pkl
INFO_PATH=models/adasyn_model_info.pkl
FEATURES_PATH=data/flat_statistics.csv

# MongoDB Configuration
MONGO_URI=mongodb://mongodb:27017/
MONGO_DB=MRI
MONGO_COLLECTION=predictions

# File Storage
FILES_DIRECTORY=/app/data/16after/00C1068568
```

### 5. Build and Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 6. Verify Installation

- **Frontend**: http://localhost
- **Backend API**: http://localhost:5001
- **MongoDB**: localhost:27017

## Usage Guide

### Starting the Application

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart backend

# View real-time logs
docker-compose logs -f backend
```

### Accessing the Application

1. Open your browser and navigate to `http://localhost`
2. Register a new account or login with existing credentials
3. Upload MRI images or use pre-extracted features for prediction
4. View survival curves, risk scores, and clinical recommendations
5. Access prediction history from the dashboard

### Making Predictions

#### Method 1: Upload MRI Images (Recommended)

```bash
# Using curl
curl -X POST http://localhost:5001/api/upload-predict \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image_file=@/path/to/image.nii.gz" \
  -F "mask_file=@/path/to/mask.nii.gz" \
  -F "clinical_file=@/path/to/clinical.xlsx" \
  -F "image_type=T1"
```

#### Method 2: Use Pre-extracted Features

```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "Patient_ID": "P001",
    "性别": 1,
    "年龄": 45,
    "T分期": 3,
    "N分期": 2,
    "总分期": 3,
    "治疗前DNA": 150.5,
    "治疗后DNA": 80.2
  }'
```

## API Endpoints Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/register
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepass",
  "code": "123456"
}
```

#### Login
```http
POST /api/login
Content-Type: application/json

{
  "username": "user123",
  "password": "securepass"
}

Response:
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "username": "user123",
  "email": "user@example.com"
}
```

#### Get Current User
```http
GET /api/user
Authorization: Bearer <token>
```

#### Logout
```http
POST /api/logout
Authorization: Bearer <token>
```

### Prediction Endpoints

#### Predict with Pre-extracted Features
```http
POST /api/predict
Content-Type: application/json
Authorization: Bearer <token>

{
  "Patient_ID": "P001",
  "性别": 1,
  "年龄": 45,
  "T分期": 3,
  "N分期": 2,
  "总分期": 3,
  "治疗前DNA": 150.5,
  "治疗后DNA": 80.2
}
```

#### Upload and Predict
```http
POST /api/upload-predict
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
- image_file: NIfTI image file (.nii or .nii.gz)
- mask_file: NIfTI mask file
- clinical_file: Clinical data (.xlsx, .xls, or .csv)
- image_type: "T1" | "T2" | "T1C"
```

#### Get Survival Curve Data
```http
POST /api/survival-curve-data
Content-Type: application/json
Authorization: Bearer <token>

{
  "Patient_ID": "P001",
  "性别": 1,
  "年龄": 45,
  "T分期": 3,
  "N分期": 2,
  "总分期": 3,
  "治疗前DNA": 150.5,
  "治疗后DNA": 80.2
}
```

### History and Management Endpoints

#### Get Prediction History
```http
GET /api/prediction-history?patient_id=P001&limit=20&skip=0&time_range=month
Authorization: Bearer <token>
```

#### Delete Prediction
```http
DELETE /api/prediction/<prediction_id>
Authorization: Bearer <token>
```

#### Get MRI Images
```http
GET /api/images
Authorization: Bearer <token>
```

#### Get File List
```http
GET /api/get-file-list
```

#### Download File
```http
GET /files/<filename>
```

## Project Structure

```
MRI/
├── MRI_backend/                    # Backend application
│   ├── Dockerfile                  # Backend container configuration
│   ├── requirements.txt            # Python dependencies
│   ├── predict_backend.py          # Main Flask application
│   ├── OS_T1_predictor.py          # Cox model predictor class
│   ├── feature_extractor.py        # MRI feature extraction
│   ├── auth_models.py              # User authentication models
│   ├── models/                     # Trained ML models
│   │   ├── adasyn_cox_model.pkl
│   │   ├── scaler.pkl
│   │   └── adasyn_model_info.pkl
│   └── data/                       # Data files
│       ├── flat_statistics.csv
│       └── 16after/                # Sample MRI data
│
├── frontend/                       # Frontend application
│   ├── Dockerfile                  # Frontend container configuration
│   ├── package.json                # Node.js dependencies
│   ├── tsconfig.json               # TypeScript configuration
│   ├── vite.config.ts              # Vite build configuration
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   ├── src/                        # Source code
│   │   ├── App.tsx                 # Main application component
│   │   ├── main.tsx                # Application entry point
│   │   ├── components/             # React components
│   │   ├── pages/                  # Page components
│   │   ├── store/                  # Zustand state management
│   │   └── utils/                  # Utility functions
│   └── public/                     # Static assets
│
├── docker-compose.yml              # Multi-container orchestration
├── nginx.conf                      # Nginx configuration
└── README.md                       # This file
```

## Development Guide

### Backend Development

#### Running Backend Locally

```bash
cd MRI_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGO_URI=mongodb://localhost:27017/
export JWT_SECRET_KEY=dev-secret-key

# Run development server
python predict_backend.py
```

#### Adding New API Endpoints

1. Define route in `predict_backend.py`
2. Implement validation logic
3. Add MongoDB operations if needed
4. Update API documentation
5. Test with curl or Postman

### Frontend Development

#### Running Frontend Locally

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

#### Project Structure

- `src/components/`: Reusable UI components
- `src/pages/`: Page-level components
- `src/store/`: Zustand state management
- `src/utils/`: Helper functions and API clients

### Code Style

- **Backend**: Follow PEP 8 guidelines
- **Frontend**: Use ESLint and Prettier configurations
- **TypeScript**: Enable strict mode
- **Commits**: Use conventional commit messages

## Testing Instructions

### Backend Testing

```bash
cd MRI_backend

# Run unit tests
python -m pytest tests/

# Test API endpoints
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Check model loading
python -c "from OS_T1_predictor import OST1Predictor; print('Model OK')"
```

### Frontend Testing

```bash
cd frontend

# Run type checking
npm run build

# Test production build
npm run preview
```

### Integration Testing

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Test health endpoints
curl http://localhost:5001/api/prediction-history
curl http://localhost/

# Check logs for errors
docker-compose logs backend | grep ERROR
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test prediction endpoint
ab -n 100 -c 10 -T application/json \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5001/api/prediction-history
```

## Deployment Notes

### Production Checklist

- [ ] Change `JWT_SECRET_KEY` to a strong random value
- [ ] Update `REGISTER_CODE` or implement proper invitation system
- [ ] Configure MongoDB authentication
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up backup strategy for MongoDB
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting
- [ ] Review and adjust rate limiting rules
- [ ] Implement proper error tracking (e.g., Sentry)
- [ ] Configure CORS for production domains only

### Environment-Specific Configuration

#### Development
```bash
docker-compose up
```

#### Production
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Enable auto-restart
docker-compose -f docker-compose.prod.yml up -d --restart=always
```

### Scaling Considerations

- **Backend**: Use Gunicorn with multiple workers
- **Database**: Enable MongoDB replica set for high availability
- **Frontend**: Serve through CDN for static assets
- **Load Balancing**: Use Nginx or cloud load balancer for multiple backend instances

### Security Best Practices

1. **Never commit secrets**: Use environment variables or secret management
2. **Regular updates**: Keep dependencies up to date
3. **Input validation**: Validate all user inputs on backend
4. **Rate limiting**: Protect against brute force attacks
5. **HTTPS only**: Enforce SSL/TLS in production
6. **Database security**: Enable authentication and encryption
7. **Audit logging**: Log all authentication and prediction events

### Backup Strategy

```bash
# Backup MongoDB
docker exec mri-mongodb mongodump --out /backup

# Backup models
tar -czf models-backup.tar.gz MRI_backend/models/

# Automated daily backup
0 2 * * * /path/to/backup-script.sh
```

## Troubleshooting

### Common Issues

#### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Verify model files exist
ls -la MRI_backend/models/

# Check MongoDB connection
docker-compose exec backend python -c "from pymongo import MongoClient; print(MongoClient('mongodb://mongodb:27017/').server_info())"
```

#### Frontend build fails
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### MongoDB connection refused
```bash
# Ensure MongoDB is running
docker-compose ps mongodb

# Check network connectivity
docker-compose exec backend ping mongodb
```

#### Model prediction errors
```bash
# Verify model compatibility
docker-compose exec backend python -c "import pickle; pickle.load(open('models/adasyn_cox_model.pkl', 'rb'))"

# Check feature alignment
docker-compose logs backend | grep "特征对齐"
```

## Performance Optimization

- **Backend**: Enable response caching for static predictions
- **Frontend**: Implement code splitting and lazy loading
- **Database**: Create indexes on frequently queried fields
- **Images**: Compress and optimize MRI visualizations
- **API**: Use pagination for large result sets

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2024 NPC MRI Prognosis Prediction Platform

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Acknowledgments

- Cox proportional hazards model implementation based on scikit-survival
- MRI feature extraction using radiomics principles
- UI design inspired by modern medical software interfaces
- Chinese font support provided by WenQuanYi Zen Hei

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact the development team
- Check the documentation wiki

## Changelog

### Version 1.0.0 (Current)
- Initial release
- User authentication system
- MRI image upload and feature extraction
- Cox model survival prediction
- Interactive survival curve visualization
- Prediction history management
- Docker containerization
- RESTful API with comprehensive documentation
