#!/usr/bin/env python3
"""
ESA WorldCover を使用した高精度土地被覆分類
訓練済みの10m解像度グローバルデータセットを使用
"""

import ee

class WorldCoverClassifier:
    """ESA WorldCover v200を使用した土地被覆分類"""
    
    # WorldCoverのクラス定義
    WORLDCOVER_CLASSES = {
        10: {'name': 'Tree cover', 'color': '#006400', 'ja': '森林'},
        20: {'name': 'Shrubland', 'color': '#ffbb22', 'ja': '低木地'},
        30: {'name': 'Grassland', 'color': '#ffff4c', 'ja': '草地'},
        40: {'name': 'Cropland', 'color': '#f096ff', 'ja': '農地'},
        50: {'name': 'Built-up', 'color': '#fa0000', 'ja': '市街地'},
        60: {'name': 'Bare / sparse vegetation', 'color': '#b4b4b4', 'ja': '裸地'},
        70: {'name': 'Snow and ice', 'color': '#f0f0f0', 'ja': '雪氷'},
        80: {'name': 'Permanent water bodies', 'color': '#0064c8', 'ja': '水域'},
        90: {'name': 'Herbaceous wetland', 'color': '#0096a0', 'ja': '湿地'},
        95: {'name': 'Mangroves', 'color': '#00cf75', 'ja': 'マングローブ'},
        100: {'name': 'Moss and lichen', 'color': '#fae6a0', 'ja': '苔地'}
    }
    
    # ユーザークラスとWorldCoverクラスのマッピング
    CLASS_MAPPING = {
        'forest': [10, 95],  # Tree cover, Mangroves
        'tree_cover': [10, 95],  # Tree cover, Mangroves
        'agriculture': [40],  # Cropland
        'cropland': [40],  # Cropland
        'water': [80, 90],   # Water bodies, Wetland
        'urban': [50],       # Built-up
        'built_up': [50],    # Built-up
        'built-up': [50],    # Built-up (alternate spelling)
        'grassland': [20, 30],  # Shrubland, Grassland
        'bare': [60],        # Bare/sparse vegetation
        'shrubland': [20],   # Shrubland
        'snow_ice': [70],    # Snow and ice
        'wetland': [90],     # Herbaceous wetland
        'mangroves': [95],   # Mangroves
        'moss_lichen': [100] # Moss and lichen
    }
    
    def __init__(self):
        self.worldcover = None
        
    def load_worldcover(self, year=2021):
        """WorldCoverデータをロード"""
        # ESA WorldCover v200 (2021年版)
        self.worldcover = ee.ImageCollection("ESA/WorldCover/v200").first()
        return self.worldcover
        
    def classify_area(self, polygon, user_classes=['forest', 'agriculture', 'water', 'urban']):
        """
        指定エリアの土地被覆を分類
        
        Args:
            polygon: ee.Geometry.Polygon - 対象エリア
            user_classes: list - 抽出したいクラス
            
        Returns:
            ee.FeatureCollection - 分類結果のベクターデータ
        """
        if self.worldcover is None:
            self.load_worldcover()
            
        # 対象エリアにクリップ
        clipped = self.worldcover.clip(polygon)
        
        # 結果を格納するリスト
        all_features = []
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Processing user classes: {user_classes}")
        
        for user_class in user_classes:
            if user_class not in self.CLASS_MAPPING:
                logger.warning(f"Unknown class: {user_class}")
                continue
                
            # WorldCoverクラスを取得
            wc_classes = self.CLASS_MAPPING[user_class]
            logger.info(f"Processing class {user_class} with WorldCover classes: {wc_classes}")
            
            # 該当クラスのマスクを作成
            mask = None
            for wc_class in wc_classes:
                class_mask = clipped.eq(wc_class)
                mask = class_mask if mask is None else mask.Or(class_mask)
            
            # ベクター化
            vectors = mask.updateMask(mask).reduceToVectors(
                geometryType='polygon',
                reducer=ee.Reducer.countEvery(),
                scale=10,  # WorldCoverの解像度
                maxPixels=1e8,
                geometry=polygon
            )
            
            # 最小面積フィルター（小エリア対応のため緩和）
            min_area = {
                'forest': 500,        # 0.05ha
                'tree_cover': 500,    # 0.05ha
                'agriculture': 300,   # 0.03ha
                'cropland': 300,      # 0.03ha
                'water': 200,         # 0.02ha
                'urban': 200,         # 0.02ha
                'built_up': 200,      # 0.02ha
                'built-up': 200,      # 0.02ha
                'grassland': 300,     # 0.03ha
                'shrubland': 300,     # 0.03ha
                'bare': 200,          # 0.02ha
                'wetland': 200,       # 0.02ha
                'mangroves': 200,     # 0.02ha
                'snow_ice': 200,      # 0.02ha
                'moss_lichen': 200,   # 0.02ha
            }.get(user_class, 200)
            
            vectors = vectors.filter(ee.Filter.gt('count', min_area / 100))  # 10m×10m = 100m²/pixel
            
            # プロパティを追加
            vectors = vectors.map(lambda f: f.set({
                'class': user_class,
                'class_ja': {
                    'forest': '森林',
                    'tree_cover': '森林',
                    'agriculture': '農地',
                    'cropland': '農地',
                    'water': '水域',
                    'urban': '市街地',
                    'built_up': '市街地',
                    'built-up': '市街地',
                    'grassland': '草地',
                    'bare': '裸地',
                    'shrubland': '低木地',
                    'snow_ice': '雪氷',
                    'wetland': '湿地',
                    'mangroves': 'マングローブ',
                    'moss_lichen': '苔地'
                }.get(user_class, user_class),
                'source': 'ESA WorldCover 2021',
                'resolution': '10m'
            }))
            
            all_features.append(vectors)
        
        # すべてのフィーチャーを結合
        if all_features:
            return ee.FeatureCollection(all_features).flatten()
        else:
            return ee.FeatureCollection([])
    
    def get_statistics(self, polygon):
        """エリア内の土地被覆統計を取得"""
        if self.worldcover is None:
            self.load_worldcover()
            
        # ピクセルカウントを取得
        pixel_counts = self.worldcover.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=polygon,
            scale=10,
            maxPixels=1e9
        ).getInfo()
        
        # 統計を整理
        stats = {}
        histogram = pixel_counts.get('Map', {})
        
        total_pixels = sum(int(v) for v in histogram.values())
        
        for class_val, count in histogram.items():
            class_info = self.WORLDCOVER_CLASSES.get(int(class_val), {})
            if class_info:
                area_m2 = int(count) * 100  # 10m × 10m
                percentage = (int(count) / total_pixels * 100) if total_pixels > 0 else 0
                
                stats[class_info['name']] = {
                    'area_m2': area_m2,
                    'area_ha': area_m2 / 10000,
                    'percentage': round(percentage, 2),
                    'name_ja': class_info['ja'],
                    'color': class_info['color']
                }
        
        return stats