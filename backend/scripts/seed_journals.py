"""
期刊库种子数据导入（起始代表集，可后续扩充至 200-500 本）。

用法：
  cd backend
  python -m scripts.seed_journals

幂等：按 name_zh / name_en 去重，已存在则跳过。
说明：这是一个跨学科的代表性起始集（约 24 本），用于功能跑通；
正式上线前应通过爬取/采购扩充至 200-500 本（含投稿链接、格式要求等）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from app.models.user import SessionLocal, engine, Base
import app.models.phase1  # noqa: F401
from app.models.phase1 import Journal

Base.metadata.create_all(bind=engine)


# (name_zh, name_en, issn, impact_factor, jcr_rank, category, submission_url, review_days_avg, acceptance_rate, is_open_access)
_SEED = [
    # 理工农医
    ("计算机学报", None, "0254-4164", 2.1, "中文核心", "计算机", "http://cjc.ict.ac.cn", 120, 0.15, False),
    ("软件学报", None, "1000-9825", 2.0, "中文核心", "计算机/软件", "http://www.jos.org.cn", 120, 0.18, False),
    ("自动化学报", None, "0254-4156", 1.8, "中文核心", "信息/控制", None, 110, 0.20, False),
    (None, "IEEE Transactions on Pattern Analysis and Machine Intelligence", "0162-8828", 23.6, "JCR Q1", "计算机/CV", "https://mc.manuscriptcentral.com/tpami", 180, 0.05, False),
    (None, "Nature", "0028-0836", 64.8, "JCR Q1", "综合/science", "https://www.nature.com", 90, 0.08, False),
    (None, "The Lancet", "0140-6736", 168.9, "JCR Q1", "医学/medical", "https://www.thelancet.com", 60, 0.05, False),
    ("中华医学杂志", None, "0376-2491", 1.5, "中文核心", "医学", None, 90, 0.20, False),
    ("机械工程学报", None, "0577-6686", 1.6, "中文核心", "工/机械", None, 120, 0.22, False),
    ("材料研究学报", None, "1005-3093", 1.2, "中文核心", "材料", None, 100, 0.25, False),
    (None, "Cell", "0092-8674", 64.5, "JCR Q1", "生物/science", "https://www.cell.com", 75, 0.07, False),
    (None, "PLOS ONE", "1932-6203", 3.7, "JCR Q2", "综合/science", "https://journals.plos.org/plosone", 110, 0.45, True),
    ("农业工程学报", None, "1002-6819", 2.0, "中文核心", "农", None, 120, 0.20, False),
    # 人文社科
    ("中国社会科学", None, "1002-4921", 3.5, "中文权威", "社科/综合", None, 150, 0.05, False),
    ("经济研究", None, "0577-9154", 4.0, "中文权威", "经济", None, 150, 0.06, False),
    ("管理世界", None, "1002-5502", 4.2, "中文权威", "管理", None, 150, 0.06, False),
    ("教育研究", None, "1002-5731", 2.8, "中文权威", "教育", None, 140, 0.08, False),
    ("中国法学", None, "1003-1707", 3.0, "中文权威", "法学", None, 150, 0.07, False),
    ("文学评论", None, "0511-4683", 1.5, "中文核心", "文学", None, 150, 0.10, False),
    ("历史研究", None, "0459-1909", 1.4, "中文核心", "历史", None, 150, 0.10, False),
    (None, "American Economic Review", "0002-8282", 11.0, "JCR Q1", "经济/economics", "https://www.aeaweb.org/journals/aer", 180, 0.07, False),
    # 艺术
    ("美术研究", None, "0461-6855", 0.8, "中文核心", "艺术/美术", None, 120, 0.15, False),
    ("音乐研究", None, "0512-7939", 0.7, "中文核心", "艺术/音乐", None, 120, 0.15, False),
    ("装饰", None, "0412-3662", 1.0, "中文核心", "艺术/设计", None, 110, 0.18, False),
    ("文艺研究", None, "0257-5876", 1.3, "中文核心", "艺术/综合", None, 130, 0.12, False),
]


def run() -> None:
    db = SessionLocal()
    inserted = skipped = 0
    try:
        for row in _SEED:
            name_zh, name_en, issn, jif, rank, cat, url, days, acc, oa = row
            q = db.query(Journal)
            if name_zh:
                exists = q.filter(Journal.name_zh == name_zh).first()
            else:
                exists = q.filter(Journal.name_en == name_en).first()
            if exists:
                skipped += 1
                continue
            db.add(Journal(
                name_zh=name_zh, name_en=name_en, issn=issn,
                impact_factor=jif, jcr_rank=rank, category=cat,
                submission_url=url, review_days_avg=days,
                acceptance_rate=acc, is_open_access=oa,
            ))
            inserted += 1
        db.commit()
        logger.info(f"[seed_journals] 完成：新增 {inserted}，跳过 {skipped}（共 {len(_SEED)} 条）")
    except Exception as e:
        db.rollback()
        logger.error(f"[seed_journals] 失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
