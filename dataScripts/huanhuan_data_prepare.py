#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
甄嬛传训练数据预处理脚本

将原始JSON数据转换为模型训练所需的JSONL格式

使用方法:
    python training/huanhuan_data_prepare.py          # 处理全部数据
    python training/huanhuan_data_prepare.py 100     # 处理100条数据
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from loguru import logger
import random

class HuanHuanDataProcessor:
    """
    甄嬛传数据处理器
    """
    
    def __init__(self, max_samples: Optional[int] = None):
        # 获取项目根目录（dataScripts的上级目录）
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        
        # 设置输入和输出目录的相对路径
        self.input_dir = project_root / "data" / "raw"
        self.output_dir = project_root / "data"
        self.max_samples = max_samples
        
        # 检查输入目录是否存在
        if not self.input_dir.exists():
            logger.error(f"输入目录不存在: {self.input_dir}")
            logger.info("请先运行: python scripts/download_data.py")
            raise FileNotFoundError(f"输入目录不存在: {self.input_dir}")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_json_data(self) -> List[Dict]:
        """
        加载JSON训练数据
        """
        all_data = []
        
        # 查找huanhuan.json文件
        json_file = self.input_dir / "huanhuan.json"
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                        logger.info(f"加载训练数据: {len(data)} 条")
                    else:
                        logger.warning(f"数据格式不正确: {json_file.name}")
            except Exception as e:
                logger.error(f"加载数据失败: {e}")
        else:
            logger.error(f"未找到训练数据文件: {json_file}")
        
        return all_data
    
    def process_data(self) -> List[Dict]:
        """
        处理训练数据
        """
        logger.info("开始处理甄嬛传数据...")
        
        # 加载JSON数据
        data = self.load_json_data()
        
        if not data:
            logger.error("没有找到有效的训练数据")
            return []
        
        # 验证数据格式
        valid_data = []
        for item in data:
            if isinstance(item, dict) and all(key in item for key in ['instruction', 'input', 'output']):
                valid_data.append({
                    "instruction": item['instruction'],
                    "input": item['input'],
                    "output": item['output']
                })
        
        # 如果指定了最大样本数，则限制数据量
        if self.max_samples and self.max_samples < len(valid_data):
            # 随机采样指定数量的数据
            random.shuffle(valid_data)
            valid_data = valid_data[:self.max_samples]
            logger.info(f"限制数据量为: {self.max_samples} 条")
        
        logger.info(f"处理完成，有效数据: {len(valid_data)} 条")
        return valid_data
    
    def split_data(self, data: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        分割数据集为训练集、验证集和测试集
        """
        random.shuffle(data)
        
        total_size = len(data)
        train_size = int(total_size * 0.8)
        val_size = int(total_size * 0.1)
        
        train_data = data[:train_size]
        val_data = data[train_size:train_size + val_size]
        test_data = data[train_size + val_size:]
        
        logger.info(f"数据分割完成 - 训练集: {len(train_data)}, 验证集: {len(val_data)}, 测试集: {len(test_data)}")
        
        return train_data, val_data, test_data
    
    def save_data(self, train_data: List[Dict], val_data: List[Dict], test_data: List[Dict]):
        """
        保存处理后的数据为JSONL格式
        """
        # 创建processed子目录用于存放处理后的数据
        processed_dir = self.output_dir / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        datasets = {
            "train": train_data,
            "validation": val_data,
            "test": test_data
        }
        
        for split_name, split_data in datasets.items():
            jsonl_file = processed_dir / f"{split_name}.jsonl"
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                for item in split_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            logger.info(f"保存 {split_name}.jsonl: {len(split_data)} 条数据")
    
    def run(self) -> bool:
        """
        执行数据预处理
        """
        try:
            # 处理数据
            data = self.process_data()
            
            if not data:
                logger.error("没有有效的训练数据")
                return False
            
            # 分割数据
            train_data, val_data, test_data = self.split_data(data)
            
            # 保存数据
            self.save_data(train_data, val_data, test_data)
            
            logger.info("🎉 数据预处理完成！")
            logger.info(f"📁 数据保存在: {self.output_dir}")
            logger.info("📝 接下来可以运行: python training/huanhuan_train.py")
            
            return True
            
        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="甄嬛传训练数据预处理脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python training/huanhuan_data_prepare.py          # 处理全部数据
  python training/huanhuan_data_prepare.py 100     # 处理100条数据
        """
    )
    
    # 位置参数：数据量
    parser.add_argument(
        'data_count', 
        nargs='?', 
        type=int, 
        help='要处理的数据条数（可选，不指定则处理全部数据）'
    )
    
    args = parser.parse_args()
    
    # 获取最大样本数
    max_samples = args.data_count
    
    if max_samples is not None:
        if max_samples <= 0:
            logger.error("数据量必须大于0")
            exit(1)
        logger.info(f"将处理最多 {max_samples} 条数据")
    else:
        logger.info("将处理全部数据")
    
    # 创建处理器并执行
    try:
        processor = HuanHuanDataProcessor(max_samples=max_samples)
        if not processor.run():
            exit(1)
    except FileNotFoundError:
        exit(1)

if __name__ == "__main__":
    main()