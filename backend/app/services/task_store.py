"""
任务结果双写服务

写入：任务完成时同时写 Redis（快速查询）+ MySQL（永久存储）
读取：先查 Redis，缓存缺失则查 MySQL 并回填 Redis
"""

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.billing import TaskRecord
from app.models.user import SessionLocal

logger = logging.getLogger(__name__)


def save_task_result(
    task_id: str,
    task_type: str,
    result: dict,
    output_file: str = None,
    user_id: int = None,
):
    """
    任务成功时调用：将结果写入 MySQL。
    Redis 由 Celery 自动写入（result_expires=7天），这里只负责 MySQL 持久化。
    """
    db: Session = SessionLocal()
    try:
        record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).first()
        if record:
            record.status = "success"
            record.result_json = json.dumps(result, ensure_ascii=False)
            record.output_file = output_file
            record.completed_at = datetime.utcnow()
        else:
            db.add(TaskRecord(
                task_id=task_id,
                task_type=task_type,
                user_id=user_id,
                status="success",
                result_json=json.dumps(result, ensure_ascii=False),
                output_file=output_file,
                completed_at=datetime.utcnow(),
            ))
        db.commit()
    except Exception as e:
        logger.error(f"[task_store] 写入 MySQL 失败 task_id={task_id}: {e}")
    finally:
        db.close()


def save_task_failure(task_id: str, task_type: str, error_msg: str, user_id: int = None):
    """任务失败时记录错误到 MySQL"""
    db: Session = SessionLocal()
    try:
        record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).first()
        if record:
            record.status = "failure"
            record.error_msg = error_msg
            record.completed_at = datetime.utcnow()
        else:
            db.add(TaskRecord(
                task_id=task_id,
                task_type=task_type,
                user_id=user_id,
                status="failure",
                error_msg=error_msg,
                completed_at=datetime.utcnow(),
            ))
        db.commit()
    except Exception as e:
        logger.error(f"[task_store] 写入失败记录 MySQL 失败 task_id={task_id}: {e}")
    finally:
        db.close()


def get_task_result_from_db(task_id: str) -> Optional[dict]:
    """
    从 MySQL 查询任务结果（Redis 缺失时的兜底）。
    返回格式与 Celery AsyncResult.result 一致。
    """
    db: Session = SessionLocal()
    try:
        record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).first()
        if not record:
            return None
        return {
            "status": record.status,
            "result": json.loads(record.result_json) if record.result_json else None,
            "error": record.error_msg,
            "output_file": record.output_file,
        }
    except Exception as e:
        logger.error(f"[task_store] 从 MySQL 查询失败 task_id={task_id}: {e}")
        return None
    finally:
        db.close()
