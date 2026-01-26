#!/usr/bin/env python3
"""
Satellite GIS Extractor - Minimal Server
Flask統合サーバー（API + 静的ファイル配信）
"""

import os
import sys
import json
import logging
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_file, make_response, send_from_directory
from flask_cors import CORS
import ee

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ディレクトリ設定
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / 'frontend'
TEMP_DIR = Path(tempfile.gettempdir())

app = Flask(__name__, static_folder=str(FRONTEND_DIR))
CORS(app)

# Earth Engine初期化フラグ
ee_initialized = False


def initialize_earth_engine():
    """Initialize Earth Engine with service account authentication"""
    global ee_initialized
    if ee_initialized:
        return True

    # Get credentials from environment variables (required)
    service_account = os.environ.get('EARTH_ENGINE_SERVICE_ACCOUNT')
    key_file_path = os.environ.get('EARTH_ENGINE_KEY_FILE')
    project_id = os.environ.get('EARTH_ENGINE_PROJECT_ID')

    # Check if all required environment variables are set
    if not all([service_account, key_file_path, project_id]):
        logger.warning("Earth Engine credentials not configured.")
        logger.info("Please set the following environment variables:")
        logger.info("  - EARTH_ENGINE_SERVICE_ACCOUNT")
        logger.info("  - EARTH_ENGINE_KEY_FILE")
        logger.info("  - EARTH_ENGINE_PROJECT_ID")
        return False

    key_file = Path(key_file_path)

    try:
        if key_file.exists():
            logger.info(f"Initializing Earth Engine...")
            logger.info(f"  Project: {project_id}")

            credentials = ee.ServiceAccountCredentials(service_account, str(key_file))
            ee.Initialize(credentials, project=project_id)

            # Verify initialization
            ee.Number(1).getInfo()
            logger.info("Earth Engine initialized successfully")
            ee_initialized = True
            return True
        else:
            logger.error(f"Key file not found: {key_file}")
            return False

    except Exception as e:
        logger.error(f"Earth Engine initialization failed: {e}")
        return False


# ============================================
# 静的ファイル配信
# ============================================

@app.route('/')
def serve_index():
    """メインページ"""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """静的ファイル"""
    return send_from_directory(FRONTEND_DIR, filename)


# ============================================
# API エンドポイント
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    ee_status = False
    ee_error = None
    try:
        ee.Number(1).getInfo()
        ee_status = True
    except Exception as ex:
        ee_error = str(ex)
        logger.error(f"EE health check failed: {ex}")
    return jsonify({
        'status': 'healthy',
        'earth_engine': ee_status,
        'earth_engine_error': ee_error,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/gis_extraction_worldcover', methods=['POST', 'OPTIONS'])
def extract_gis_worldcover():
    """ESA WorldCoverを使用したGISデータ抽出"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        # EEが初期化されていなければ初期化する
        try:
            ee.Number(1).getInfo()
        except:
            if not initialize_earth_engine():
                return jsonify({'error': 'Earth Engine not initialized. Please check your credentials.'}), 500

        from worldcover_classifier import WorldCoverClassifier

        data = request.get_json()
        coordinates = data.get('coordinates', [])
        user_classes = data.get('classes', ['forest', 'agriculture', 'water', 'urban'])
        output_format = data.get('output_format', 'geojson')

        logger.info(f"Extraction request: classes={user_classes}, format={output_format}")

        if not coordinates or len(coordinates) < 3:
            return jsonify({'error': 'Invalid coordinates. At least 3 points required.'}), 400

        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])

        polygon = ee.Geometry.Polygon([coordinates])

        classifier = WorldCoverClassifier()
        classifier.load_worldcover()

        statistics = classifier.get_statistics(polygon)
        vectors = classifier.classify_area(polygon, user_classes)
        geojson_data = vectors.getInfo()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if output_format == 'shapefile':
            import geopandas as gpd

            features = geojson_data.get('features', [])
            if features:
                gdf = gpd.GeoDataFrame.from_features(features, crs='EPSG:4326')

                zip_filename = f'worldcover_{timestamp}.zip'
                zip_filepath = TEMP_DIR / zip_filename
                shp_basename = f'worldcover_{timestamp}'

                with tempfile.TemporaryDirectory() as tmpdir:
                    shp_path = os.path.join(tmpdir, f'{shp_basename}.shp')
                    gdf.to_file(shp_path, encoding='utf-8')

                    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                            file_path = os.path.join(tmpdir, f'{shp_basename}{ext}')
                            if os.path.exists(file_path):
                                zipf.write(file_path, f'{shp_basename}{ext}')

                download_filename = zip_filename
            else:
                download_filename = None
        else:
            geojson_filename = f'worldcover_{timestamp}.geojson'
            geojson_filepath = TEMP_DIR / geojson_filename

            with open(geojson_filepath, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, ensure_ascii=False, indent=2)

            download_filename = geojson_filename

        response_data = {
            'success': True,
            'statistics': statistics,
            'feature_count': len(geojson_data.get('features', [])),
            'output_format': output_format
        }

        if download_filename:
            response_data['download_url'] = f'/api/download/{download_filename}'

        return jsonify(response_data)

    except Exception as e:
        logger.exception(f"Extraction error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """ファイルダウンロード"""
    try:
        filepath = TEMP_DIR / filename

        if filepath.exists():
            mime_type = 'application/octet-stream'
            if filename.endswith('.zip'):
                mime_type = 'application/zip'
            elif filename.endswith('.geojson'):
                mime_type = 'application/json'

            return send_file(
                filepath,
                as_attachment=True,
                mimetype=mime_type,
                download_name=filename
            )
        else:
            return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        logger.exception(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    print(f"""
========================================================
     Satellite GIS Extractor
     http://localhost:{port}
========================================================
    """, flush=True)

    # 起動時にEarth Engineを初期化
    print("Initializing Earth Engine...", flush=True)
    if initialize_earth_engine():
        print("Earth Engine: OK", flush=True)
    else:
        print("Earth Engine: FAILED - Check credentials", flush=True)

    app.run(host='0.0.0.0', port=port, debug=debug, threaded=False)
