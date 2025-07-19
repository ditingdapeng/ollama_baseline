#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步训练监控脚本 - 单类架构优化版

独立运行的监控脚本，用于实时监控训练过程中的系统资源使用情况。
负责每5秒的监控输出和监控文件的保存。

架构优化：
- 将原有的三个类（SystemMonitor、MonitorLogger、SyncTrainingMonitor）合并为一个统一的类
- 保持原有的数据获取方式不变
- 简化流程，提高代码可读性和维护性

使用方法:
    python training/sync_monitor_unified.py
"""

import os
import sys
import time
import signal
import json
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


class UnifiedTrainingMonitor:
    """
    统一训练监控器
    
    将系统监控、日志记录和监控管理功能整合到一个类中，
    简化架构，提高代码的可读性和维护性。
    """
    
    def __init__(self, interval: int = 5):
        """
        初始化统一监控器
        
        Args:
            interval: 监控间隔（秒）
        """
        # 监控配置
        self.interval = interval
        self.is_monitoring = False
        
        # 数据收集
        self.data_points = []
        self.start_time = None
        self.end_time = None
        
        # GPU可用性检查
        self.gpu_available = self._check_gpu_availability()
        
        # 设置日志目录和文件
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.monitor_log_file = str(self.log_dir / "training_monitor_data.jsonl")
        
        # 配置loguru日志
        self._setup_logging()
        
        logger.info(f"统一训练监控器初始化完成，监控间隔: {interval}秒")
    
    def _setup_logging(self):
        """
        设置日志配置
        """
        logger.remove()  # 移除默认处理器
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )
        logger.add(
            self.log_dir / "sync_monitor.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB"
        )
    
    def _check_gpu_availability(self) -> bool:
        """
        检查GPU是否可用
        """
        # 检查NVIDIA GPU
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            pass
        
        # 检查Apple Silicon GPU (Metal)
        try:
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], capture_output=True, text=True)
            if result.returncode == 0 and ('Apple' in result.stdout or 'Metal' in result.stdout):
                return True
        except FileNotFoundError:
            pass
        
        return False
    
    def _get_apple_silicon_gpu_utilization(self) -> Optional[float]:
        """
        通过powermetrics获取Apple Silicon GPU利用率
        需要管理员权限
        """
        try:
            # 使用powermetrics获取GPU利用率，采样1秒
            result = subprocess.run([
                'sudo', 'powermetrics', 
                '--samplers', 'gpu_power', 
                '--sample-rate', '1000',  # 1秒采样
                '--sample-count', '1'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    # 查找GPU利用率信息
                    if 'GPU HW active residency:' in line:
                        # 提取百分比数值，格式如: "GPU HW active residency:  34.74% (389 MHz:  35% ...)"
                        parts = line.split(':')
                        if len(parts) > 1:
                            # 获取冒号后的部分，然后提取第一个百分比
                            percent_part = parts[1].strip()
                            if '%' in percent_part:
                                # 找到第一个%符号前的数字
                                percent_str = percent_part.split('%')[0].strip()
                                try:
                                    return float(percent_str)
                                except ValueError:
                                    pass
                    elif 'GPU active residency:' in line:
                        # 备用匹配模式
                        parts = line.split(':')
                        if len(parts) > 1:
                            percent_part = parts[1].strip()
                            if '%' in percent_part:
                                percent_str = percent_part.split('%')[0].strip()
                                try:
                                    return float(percent_str)
                                except ValueError:
                                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # 如果powermetrics不可用或需要密码，返回None
            pass
        
        return None
    
    def _get_cpu_info(self) -> Dict:
        """
        获取CPU信息
        """
        return {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    
    def _get_memory_info(self) -> Dict:
        """
        获取内存信息
        """
        memory = psutil.virtual_memory()
        return {
            'total_gb': round(memory.total / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'percent': memory.percent
        }
    
    def _get_disk_info(self) -> Dict:
        """
        获取磁盘信息
        """
        disk = psutil.disk_usage('/')
        return {
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'percent': round((disk.used / disk.total) * 100, 2)
        }
    
    def _get_gpu_info(self) -> Dict:
        """
        获取GPU信息
        """
        if not self.gpu_available:
            return {
                'available': False,
                'type': 'N/A',
                'utilization_percent': None,
                'memory_used_mb': None,
                'memory_total_mb': None
            }
        
        # 尝试获取NVIDIA GPU信息
        try:
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(', ')
                    if len(parts) >= 4:
                        return {
                            'available': True,
                            'type': parts[0],
                            'utilization_percent': float(parts[1]),
                            'memory_used_mb': float(parts[2]),
                            'memory_total_mb': float(parts[3])
                        }
        except Exception:
            pass
        
        # 尝试获取Apple Silicon GPU信息
        try:
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                gpu_name = 'Apple Silicon GPU'
                for line in lines:
                    if 'Chipset Model:' in line:
                        gpu_name = line.split(':')[1].strip()
                        break
                
                # 尝试通过powermetrics获取GPU利用率
                gpu_utilization = self._get_apple_silicon_gpu_utilization()
                
                return {
                    'available': True,
                    'type': gpu_name,
                    'utilization_percent': gpu_utilization,
                    'memory_used_mb': None,       # 统一内存架构，难以单独统计GPU内存
                    'memory_total_mb': None
                }
        except Exception as e:
            logger.warning(f"获取Apple Silicon GPU信息失败: {e}")
        
        return {
            'available': True,
            'type': 'Unknown GPU',
            'utilization_percent': None,
            'memory_used_mb': None,
            'memory_total_mb': None
        }
    
    def _get_training_processes(self) -> List[Dict]:
        """
        获取训练相关的进程信息
        """
        training_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
            try:
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    # 检查是否是训练相关进程
                    if any(keyword in cmdline.lower() for keyword in ['train', 'training', 'model', 'torch', 'tensorflow']):
                        training_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline,
                            'cpu_percent': proc.info['cpu_percent'] or 0,
                            'memory_mb': round(proc.info['memory_info'].rss / (1024*1024), 2) if proc.info['memory_info'] else 0
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return training_processes
    
    def _collect_all_metrics(self) -> Dict:
        """
        收集所有系统指标
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': self._get_cpu_info(),
            'memory': self._get_memory_info(),
            'disk': self._get_disk_info(),
            'gpu': self._get_gpu_info(),
            'training_processes': self._get_training_processes()
        }
    
    def _log_metrics_to_file(self, metrics: Dict):
        """
        记录监控指标到文件
        """
        try:
            with open(self.monitor_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(metrics, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"记录监控数据失败: {e}")
    
    def _signal_handler(self, signum, frame):
        """
        信号处理器，用于优雅地停止监控
        """
        logger.info(f"\n🛑 接收到停止信号 ({signum})，正在停止监控...")
        self.stop_monitoring()
        sys.exit(0)
    
    def start_monitoring(self):
        """
        开始同步监控
        """
        if self.is_monitoring:
            logger.warning("监控已在运行中")
            return
        
        logger.info("🚀 开始同步训练监控...")
        logger.info("💡 提示: 按 Ctrl+C 停止监控")
        
        # 查找训练进程
        training_processes = self._get_training_processes()
        if training_processes:
            logger.info(f"✅ 找到 {len(training_processes)} 个训练进程")
        else:
            logger.warning("⚠️  未找到正在运行的训练进程，将监控整体系统资源")
        
        self.is_monitoring = True
        self.start_time = datetime.now()
        
        try:
            # 实时显示监控信息
            self._run_monitoring_loop()
        except KeyboardInterrupt:
            logger.info("\n🛑 用户中断监控")
        finally:
            self.stop_monitoring()
    
    def _run_monitoring_loop(self):
        """
        运行监控循环，显示实时信息并收集数据
        """
        while self.is_monitoring:
            try:
                # 收集系统指标
                metrics = self._collect_all_metrics()
                
                # 存储数据点
                self.data_points.append(metrics)
                
                # 记录到文件
                self._log_metrics_to_file(metrics)
                
                # 显示实时信息
                self._display_realtime_info(metrics)
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"监控过程中出错: {e}")
                time.sleep(self.interval)
    
    def _display_realtime_info(self, metrics: Dict):
        """
        显示实时监控信息
        """
        cpu_info = metrics['cpu']
        memory_info = metrics['memory']
        disk_info = metrics['disk']
        gpu_info = metrics['gpu']
        processes = metrics['training_processes']
        
        # 构建GPU显示信息
        if gpu_info['available']:
            if gpu_info['utilization_percent'] is not None:
                gpu_display = f"GPU: {gpu_info['utilization_percent']:.1f}% ({gpu_info['type']})"
            else:
                gpu_display = f"GPU: 可用 ({gpu_info['type']})"
        else:
            gpu_display = "GPU: 不可用"
        
        print(f"\r🔍 监控中... | CPU: {cpu_info['percent']:.1f}% | "
              f"内存: {memory_info['percent']:.1f}% ({memory_info['used_gb']:.1f}GB/{memory_info['total_gb']:.1f}GB) | "
              f"磁盘: {disk_info['percent']:.1f}% | "
              f"{gpu_display} | "
              f"训练进程: {len(processes)} | "
              f"数据点: {len(self.data_points)}", end="", flush=True)
    
    def stop_monitoring(self):
        """
        停止监控并生成报告
        """
        if not self.is_monitoring:
            return
        
        logger.info("🛑 正在停止监控...")
        self.is_monitoring = False
        self.end_time = datetime.now()
        
        # 生成监控报告
        if self.data_points:
            logger.info("📊 生成监控报告...")
            report = self.generate_report()
            if report:
                logger.info("✅ 监控报告生成完成")
                self._display_summary(report)
        
        logger.info("✅ 监控已停止")
    
    def generate_report(self, output_file: str = None) -> Dict:
        """
        生成监控报告
        """
        if not self.data_points:
            logger.warning("没有监控数据可生成报告")
            return {}
        
        if output_file is None:
            output_file = str(self.log_dir / "training_resource_report.json")
        
        # 计算统计信息
        cpu_usage = [dp['cpu']['percent'] for dp in self.data_points]
        memory_usage = [dp['memory']['percent'] for dp in self.data_points]
        
        # GPU统计（如果有数据）
        gpu_utilization = [dp['gpu']['utilization_percent'] for dp in self.data_points if dp['gpu']['utilization_percent'] is not None]
        
        duration_minutes = len(self.data_points) * self.interval / 60
        
        report = {
            "monitoring_summary": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_minutes": round(duration_minutes, 2),
                "total_data_points": len(self.data_points),
                "monitoring_interval_seconds": self.interval
            },
            "cpu_statistics": {
                "avg_usage_percent": round(sum(cpu_usage) / len(cpu_usage), 2),
                "max_usage_percent": round(max(cpu_usage), 2),
                "min_usage_percent": round(min(cpu_usage), 2)
            },
            "memory_statistics": {
                "avg_usage_percent": round(sum(memory_usage) / len(memory_usage), 2),
                "max_usage_percent": round(max(memory_usage), 2),
                "min_usage_percent": round(min(memory_usage), 2)
            },
            "gpu_statistics": {
                "available": any(dp['gpu']['available'] for dp in self.data_points),
                "avg_utilization_percent": round(sum(gpu_utilization) / len(gpu_utilization), 2) if gpu_utilization else None,
                "max_utilization_percent": round(max(gpu_utilization), 2) if gpu_utilization else None,
                "min_utilization_percent": round(min(gpu_utilization), 2) if gpu_utilization else None
            },
            "peak_resources": {
                "peak_cpu_time": self.data_points[cpu_usage.index(max(cpu_usage))]['timestamp'],
                "peak_memory_time": self.data_points[memory_usage.index(max(memory_usage))]['timestamp'],
                "peak_gpu_time": self.data_points[gpu_utilization.index(max(gpu_utilization))]['timestamp'] if gpu_utilization else None
            }
        }
        
        # 保存报告
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"监控报告已保存到: {output_file}")
        return report
    
    def _display_summary(self, report: Dict):
        """
        显示监控摘要
        """
        logger.info(f"📈 监控摘要:")
        logger.info(f"   - 监控时长: {report['monitoring_summary']['duration_minutes']:.1f} 分钟")
        logger.info(f"   - 平均CPU使用率: {report['cpu_statistics']['avg_usage_percent']:.1f}%")
        logger.info(f"   - 峰值CPU使用率: {report['cpu_statistics']['max_usage_percent']:.1f}%")
        logger.info(f"   - 平均内存使用率: {report['memory_statistics']['avg_usage_percent']:.1f}%")
        logger.info(f"   - 峰值内存使用率: {report['memory_statistics']['max_usage_percent']:.1f}%")
        if report['gpu_statistics']['available']:
            logger.info(f"   - GPU可用: 是")
            if report['gpu_statistics']['avg_utilization_percent'] is not None:
                logger.info(f"   - 平均GPU利用率: {report['gpu_statistics']['avg_utilization_percent']:.1f}%")
                logger.info(f"   - 峰值GPU利用率: {report['gpu_statistics']['max_utilization_percent']:.1f}%")
            else:
                logger.info("   - GPU可用但无法获取利用率数据")
        else:
            logger.info("   - GPU不可用")


def main():
    """
    主函数
    """
    try:
        # 创建统一监控器，固定5秒监控间隔
        monitor = UnifiedTrainingMonitor(interval=5)
        
        # 注册信号处理器，确保强制停止时能正确保存文件
        signal.signal(signal.SIGINT, monitor._signal_handler)
        signal.signal(signal.SIGTERM, monitor._signal_handler)
        
        # 开始监控
        monitor.start_monitoring()
        
    except Exception as e:
        logger.error(f"监控失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()