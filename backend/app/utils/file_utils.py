"""文件工具函数"""
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

def clean_old_files(directory: Path, retention_hours: int = 24) -> int:
    """清理超过保留期的文件，返回删除数量"""
    if not directory.exists():
        return 0
    cutoff = datetime.now() - timedelta(hours=retention_hours)
    deleted = 0
    for f in directory.iterdir():
        if f.is_file() and datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            try:
                f.unlink()
                deleted += 1
                logger.info(f"已删除旧文件: {f}")
            except Exception as e:
                logger.error(f"删除文件失败: {f}, {e}")
    return deleted
