# Satellite GIS Extractor

A simple tool to extract land cover from satellite data and export to GIS formats.

Uses ESA WorldCover 2021 (10m resolution).

[日本語](README.md)

## Features

- Draw areas on Google Maps (polygon/rectangle)
- Automatic land cover classification from ESA WorldCover
- Export to GeoJSON/Shapefile
- Land cover statistics (area & percentage)

## Architecture

```
┌─────────────────────────────────────┐
│  Browser (localhost:5001)           │
│  ┌─────────────────────────────┐   │
│  │  Google Maps Drawing        │   │
│  │  + Land Cover Selection     │   │
│  └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │ /api/gis_extraction_worldcover
               ▼
┌─────────────────────────────────────┐
│  Flask Server (server.py)           │
│  - Static file serving              │
│  - Earth Engine API                 │
│  - WorldCover classification        │
└─────────────────────────────────────┘
```

**Single server** - Frontend and backend integrated

## Setup

### 1. Get API Keys

#### Google Maps API
1. Go to [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)
2. Enable Maps JavaScript API
3. Create API key

#### Google Earth Engine
```bash
pip install earthengine-api
earthengine authenticate
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Start

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

Open http://localhost:5001 in your browser.

You'll be prompted to enter your Google Maps API key on first launch.

## Usage

1. Draw an area on the map
2. Select land cover classes to extract
3. Choose output format
4. Click "Extract Land Cover"
5. Download results

## Supported Classes

| Class | Description |
|-------|-------------|
| Forest | Tree cover & mangroves |
| Agriculture | Cropland |
| Water | Water bodies |
| Urban | Built-up areas |
| Grassland | Grassland & shrubland |
| Bare | Bare or sparse vegetation |

## File Structure

```
satellite-gis-extractor/
├── backend/
│   ├── server.py              # Integrated server
│   ├── worldcover_classifier.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   └── js/
│       ├── config.js          # API configuration
│       └── app.js             # Main logic
├── start.bat / start.sh
└── README.md
```

## License

MIT License

## Data Source

- [ESA WorldCover](https://worldcover2021.esa.int/) - CC BY 4.0
