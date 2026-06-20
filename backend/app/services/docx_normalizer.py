"""
.docx 归一化工具

WPS Office 生成的 .docx 虽然后缀标准,但内部 XML 含非标准标签,
python-docx 打开时可能抛 `no item named` / `BadZip` 等异常。
本模块通过 LibreOffice `soffice --headless --convert-to docx` 把文件
"洗"一遍,输出标准 OOXML,让 python-docx 能正常读。

设计原则:
- 透明:MS Word 标准文件走快速路径,不调 soffice
- 兜底:soffice 不可用(如 Windows 开发机)或转换失败 → 返回原路径,
         不抛异常,让调用方现有的 fallback 逻辑继续生效
- 并发安全:每次转换使用独立 UserInstallation 目录避免 soffice profile 冲突
"""
from __future__ import annotations

import re
import shutil
import subprocess
import uuid
import zipfile
from pathlib import Path

from loguru import logger


_SOFFICE_TIMEOUT_SEC = 90
_WPS_MARKERS = ("wps", "kingsoft")
_CTRL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_control_chars(text: str) -> str:
    """去除会污染 AI prompt 的控制字符,保留 \\n \\r \\t。"""
    if not text:
        return text
    return _CTRL_CHARS_RE.sub("", text)


def _find_soffice() -> str | None:
    """查找 soffice 可执行文件;找不到返回 None(Windows 开发机常见)。"""
    return shutil.which("soffice") or shutil.which("soffice.exe")


def _is_wps_docx(file_path: Path) -> bool:
    """通过 docProps/app.xml 的 <Application> 字段判断是否 WPS 生成。"""
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            if "docProps/app.xml" not in zf.namelist():
                return False
            app_xml = zf.read("docProps/app.xml").decode("utf-8", errors="ignore").lower()
            return any(marker in app_xml for marker in _WPS_MARKERS)
    except Exception:
        return False


def _try_open_with_docx(file_path: Path) -> bool:
    """试着用 python-docx 打开一次,成功为 True。"""
    try:
        from docx import Document
        Document(str(file_path))
        return True
    except Exception as exc:
        logger.debug(f"[docx_normalizer] python-docx 试开失败: {exc}")
        return False


def _run_soffice_convert(soffice: str, src: Path, staging_root: Path) -> Path | None:
    """
    调 soffice 把 src 转成标准 .docx 写到独立临时子目录,返回产物路径;失败返回 None。

    不把 --outdir 指向 src.parent:同 stem 会与源文件冲突,soffice 崩溃/超时可能
    把原文件截断。改为每次在 staging_root 下新建独立子目录,调用方 move 走产物后
    负责清理 `产物.parent`(即这个子目录)。
    每次调用用独立 UserInstallation 目录,避免并发冲突。
    """
    convert_dir = staging_root / f"lo_out_{uuid.uuid4().hex}"
    convert_dir.mkdir(parents=True, exist_ok=True)

    profile_dir = convert_dir / "profile"
    profile_uri = profile_dir.as_uri()

    cmd = [
        soffice,
        "--headless",
        "--norestore",
        "--nologo",
        "--nolockcheck",
        f"-env:UserInstallation={profile_uri}",
        "--convert-to",
        "docx",
        "--outdir",
        str(convert_dir),
        str(src),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_SOFFICE_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"[docx_normalizer] soffice 超时 (>{_SOFFICE_TIMEOUT_SEC}s): {src.name}")
        shutil.rmtree(convert_dir, ignore_errors=True)
        return None
    except Exception as exc:
        logger.warning(f"[docx_normalizer] soffice 执行异常: {exc}")
        shutil.rmtree(convert_dir, ignore_errors=True)
        return None

    # soffice 运行完,先把 profile 清掉;产物留在 convert_dir 里等调用方搬走
    shutil.rmtree(profile_dir, ignore_errors=True)

    if result.returncode != 0:
        logger.warning(
            f"[docx_normalizer] soffice 转换失败 rc={result.returncode}: "
            f"{(result.stderr or result.stdout or '').strip()[:200]}"
        )
        shutil.rmtree(convert_dir, ignore_errors=True)
        return None

    expected = convert_dir / (src.stem + ".docx")
    if not expected.exists():
        logger.warning(f"[docx_normalizer] soffice 未产出预期文件: {expected}")
        shutil.rmtree(convert_dir, ignore_errors=True)
        return None

    return expected


def normalize_docx(file_path: Path | str) -> Path:
    """
    检测并归一化 .docx 文件。

    :param file_path: 原始上传文件路径
    :return: 归一化后的文件路径(可能指向原文件,也可能是替换后的文件)

    策略:
    1. soffice 不可用 → 返回原路径(Windows 开发场景)
    2. 非 WPS 且 python-docx 能正常打开 → 返回原路径(性能优化)
    3. 是 WPS 或 python-docx 打不开 → 调 soffice 转换
       - 转换成功 → 用新文件覆盖原路径,返回原路径
       - 转换失败 → 返回原路径,让调用方现有 fallback 兜底
    """
    path = Path(file_path)
    if not path.exists():
        return path

    soffice = _find_soffice()
    if not soffice:
        logger.debug(f"[docx_normalizer] soffice 不可用,跳过归一化: {path.name}")
        return path

    wps = _is_wps_docx(path)
    if not wps and _try_open_with_docx(path):
        return path

    logger.info(
        f"[docx_normalizer] 触发归一化: {path.name} "
        f"(wps={wps})"
    )

    # soffice 产物写到 path.parent 下的独立临时子目录,不会与源文件冲突
    converted = _run_soffice_convert(soffice, path, path.parent)
    if converted is None:
        logger.warning(f"[docx_normalizer] 归一化失败,保留原文件: {path.name}")
        return path

    convert_dir = converted.parent
    try:
        shutil.move(str(converted), str(path))
    except Exception as exc:
        logger.warning(f"[docx_normalizer] 覆盖原文件失败,返回转换后路径: {exc}")
        return converted

    logger.info(f"[docx_normalizer] 归一化成功: {path.name}")

    # move 成功后 convert_dir 已空,清理掉
    try:
        convert_dir.rmdir()
    except OSError:
        pass

    return path
