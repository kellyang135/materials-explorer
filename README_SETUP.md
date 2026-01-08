# Materials Explorer - Local Development Setup

## 🚀 Quick Start (One Command)

```bash
./start_demo.sh
```

This will:
1. Load sample materials from Materials Project API
2. Start the backend (FastAPI) on port 8000
3. Start the frontend (React) on port 3000
4. Open both services for testing

## 📋 Manual Setup (Step by Step)

### 1. Load Sample Data
```bash
python3 load_sample_data.py
```

### 2. Start Backend
```bash
./run_backend.sh
```

### 3. Start Frontend (in new terminal)
```bash
cd frontend
npm start
```

## 🌐 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🧪 Testing the 3D Viewer

1. Go to http://localhost:3000
2. Click on any material (e.g., "mp-149" for Silicon)
3. Scroll down to the "Crystal Structure" section
4. You should see an interactive 3D crystal structure viewer

## 📊 Available Test Materials

The sample data loader fetches these materials:
- **mp-149**: Silicon (Si)
- **mp-13**: Iron (Fe)
- **mp-22862**: Sodium Chloride (NaCl)
- **mp-2534**: Gallium Arsenide (GaAs)
- **mp-134**: Aluminum (Al)
- **mp-1265**: Quartz (SiO2)
- **mp-19017**: Iron Oxide (Fe2O3)
- **mp-1143**: Copper (Cu)

## 🔧 Technical Details

### Database
- **Type**: SQLite (local file: `materials_explorer.db`)
- **Location**: Root directory
- **Auto-created**: Tables are created automatically on first run

### Cache
- **Type**: In-memory dictionary (no Redis required)
- **TTL**: 1 hour (configurable)
- **Auto-cleanup**: Expired entries removed automatically

### API Key
- **Materials Project API**: Built-in (4qLIaDzBfyUgYLrnh6mu9tOsGbAshwYG)
- **Usage**: Only for loading sample data

## 🛠️ Development

### Backend Development
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend
npm start
```

### Reset Database
```bash
rm materials_explorer.db
python3 load_sample_data.py
```

## 🚨 Troubleshooting

### Backend won't start
1. Check if port 8000 is available: `lsof -i :8000`
2. Kill existing process: `pkill -f uvicorn`
3. Check dependencies: `pip install -r requirements.txt`

### Frontend won't start
1. Check if port 3000 is available: `lsof -i :3000`
2. Kill existing process: `pkill -f react-scripts`
3. Reinstall dependencies: `cd frontend && npm install`

### No 3D viewer
1. Check browser console for errors
2. Verify backend is running: `curl http://localhost:8000/health`
3. Check material has structure data: `curl http://localhost:8000/api/v1/materials/mp-149/structure`

### Sample data loading fails
1. Check internet connection
2. Verify API key is working
3. Try loading individual materials manually

## 📝 Notes

- No Docker required for local development
- SQLite database is portable and self-contained
- All dependencies are Python/Node.js based
- 3D viewer works in all modern browsers
- API key is included for convenience (rate-limited but sufficient for testing)