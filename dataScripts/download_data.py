#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
甄嬛传数据集下载脚本

从GitHub下载训练数据

使用方法:
    python scripts/download_data.py
"""

import requests
from pathlib import Path
from tqdm import tqdm
from loguru import logger

class HuanHuanDataDownloader:
    """
    甄嬛传数据下载器
    """
    
    def __init__(self, data_dir: str = "../data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        
        # 创建目录
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据源URL
        self.base_url = "https://raw.githubusercontent.com/datawhalechina/self-llm/master/dataset"
        
        # 数据文件
        self.data_file = "huanhuan.json"
    
    def download_file(self, url: str, save_path: Path, description: str = "") -> bool:
        """
        下载文件
        """
        try:
            logger.info(f"开始下载: {description or url}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(save_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=description) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            logger.info(f"下载完成: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"下载失败 {url}: {e}")
            return False
    
    def download_data(self) -> bool:
        """
        下载训练数据
        """
        logger.info("开始下载甄嬛传数据集...")
        
        url = f"{self.base_url}/{self.data_file}"
        save_path = self.raw_dir / self.data_file
        
        return self.download_file(url, save_path, "甄嬛传训练数据")

    def run(self) -> bool:
        """
        执行数据下载
        """
        if self.download_data():
            logger.info("🎉 数据下载完成！")
            logger.info(f"📁 数据保存在: {self.data_dir}")
            logger.info("📝 接下来可以运行: python training/huanhuan_data_prepare.py")
            return True
        else:
            logger.error("❌ 数据下载失败")
            return False
    
def main():
    """主函数"""
    downloader = HuanHuanDataDownloader()
    
    if not downloader.run():
        exit(1)

if __name__ == "__main__":
    main()