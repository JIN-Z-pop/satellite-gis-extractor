# Satellite GIS Extractor

衛星データから土地被覆情報を抽出してGIS形式で出力するシンプルなツール。

ESA WorldCover 2021（10m解像度）を使用。

[![Windows 11](https://img.shields.io/badge/Tested%20on-Windows%2011-blue.svg)](https://www.microsoft.com/windows/windows-11)

[English](README.en.md)

## 機能

- Google Maps上で領域を描画（ポリゴン/矩形）
- ESA WorldCoverから土地被覆を自動分類
- GeoJSON/Shapefile形式で出力
- 土地被覆統計（面積・割合）を表示

## アーキテクチャ

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

**1サーバーで完結** - フロントエンドとバックエンドを統合

## セットアップ

### 1. API キーの取得

#### Google Maps API
1. [Google Cloud Console](https://console.cloud.google.com/google/maps-apis) にアクセス
2. Maps JavaScript API を有効化
3. API キーを作成

#### Google Earth Engine
```bash
pip install earthengine-api
earthengine authenticate
```

### 2. 依存パッケージのインストール

```bash
pip install -r backend/requirements.txt
```

### 3. 起動

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

ブラウザで http://localhost:5001 を開きます。

初回起動時にGoogle Maps APIキーの入力を求められます。

## 使い方

1. 地図上で領域を描画
2. 抽出したい土地被覆クラスを選択
3. 出力形式を選択
4. 「Extract Land Cover」をクリック
5. 結果をダウンロード

## 対応クラス

| クラス | 説明 |
|--------|------|
| Forest | 森林・マングローブ |
| Agriculture | 農地 |
| Water | 水域 |
| Urban | 市街地 |
| Grassland | 草地 |
| Bare | 裸地 |

## ファイル構成

```
satellite-gis-extractor/
├── backend/
│   ├── server.py              # 統合サーバー
│   ├── worldcover_classifier.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   └── js/
│       ├── config.js          # API設定
│       └── app.js             # メインロジック
├── start.bat / start.sh
└── README.md
```

## 作者

**JIN-Z-pop and his merry AI brothers**

## ライセンス

MIT License

## データソース

- [ESA WorldCover](https://worldcover2021.esa.int/) - CC BY 4.0
