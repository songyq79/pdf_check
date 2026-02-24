"""
论文评价检验系统 - 自动创建项目目录结构脚本
运行此脚本将在当前目录下创建完整的项目结构
"""

import os
from pathlib import Path

# 定义项目目录结构
STRUCTURE = {
    "backend": {
        "app": {
            "__init__.py": "",
            "main.py": "",
            "config.py": "",
            "api": {
                "__init__.py": "",
                "v1": {
                    "__init__.py": "",
                    "endpoints": {
                        "__init__.py": "",
                        "spell_check.py": "",
                        "evaluation.py": "",
                        "formatting.py": "",
                    },
                    "router.py": "",
                }
            },
            "core": {
                "__init__.py": "",
                "spell_checker": {
                    "__init__.py": "",
                    "detector.py": "",
                    "corrector.py": "",
                    "docx_handler.py": "",
                    "rules": {
                        "__init__.py": "",
                        "typo_dict.json": "{}",
                        "punctuation.py": "",
                        "spacing.py": "",
                    }
                },
                "evaluator": {
                    "__init__.py": "",
                    "bailian_client.py": "",
                    "prompts.py": "",
                    "report_generator.py": "",
                    "chart_generator.py": "",
                },
                "formatter": {
                    "__init__.py": "",
                    "template_parser.py": "",
                    "structure_recognizer.py": "",
                    "style_applier.py": "",
                    "template_library": {
                        "README.md": "# 预设模板库\n\n存放系统内置的论文模板文件。\n",
                    }
                }
            },
            "models": {
                "__init__.py": "",
                "user.py": "",
                "task.py": "",
            },
            "schemas": {
                "__init__.py": "",
                "spell_check.py": "",
                "evaluation.py": "",
                "formatting.py": "",
            },
            "services": {
                "__init__.py": "",
                "file_service.py": "",
                "task_service.py": "",
                "cache_service.py": "",
            },
            "utils": {
                "__init__.py": "",
                "file_utils.py": "",
                "logger.py": "",
                "exceptions.py": "",
            }
        },
        "tests": {
            "__init__.py": "",
            "test_spell_check.py": "",
            "test_evaluation.py": "",
            "test_formatting.py": "",
        },
        "storage": {
            "uploads": {
                ".gitkeep": "",
            },
            "outputs": {
                ".gitkeep": "",
            },
            "temp": {
                ".gitkeep": "",
            }
        },
        "requirements.txt": "",
        "Dockerfile": "",
        ".env.example": "",
    },
    "frontend": {
        "public": {
            "index.html": "",
            "favicon.ico": "",
        },
        "src": {
            "main.js": "",
            "App.vue": "",
            "assets": {
                "images": {
                    ".gitkeep": "",
                },
                "styles": {
                    "global.css": "",
                }
            },
            "components": {
                "FileUpload.vue": "",
                "ProgressBar.vue": "",
                "RadarChart.vue": "",
                "ResultCard.vue": "",
            },
            "views": {
                "Home.vue": "",
                "SpellCheck.vue": "",
                "Evaluation.vue": "",
                "Formatting.vue": "",
                "History.vue": "",
            },
            "router": {
                "index.js": "",
            },
            "store": {
                "index.js": "",
                "modules": {
                    "task.js": "",
                    "user.js": "",
                }
            },
            "api": {
                "index.js": "",
                "spellCheck.js": "",
                "evaluation.js": "",
                "formatting.js": "",
            },
            "utils": {
                "request.js": "",
                "fileUtils.js": "",
            }
        },
        "package.json": "",
        "vite.config.js": "",
        ".env.example": "",
    },
    "database": {
        "migrations": {
            ".gitkeep": "",
        },
        "init.sql": "",
    },
    "docker": {
        "docker-compose.yml": "",
        "nginx": {
            "nginx.conf": "",
        },
        "redis": {
            "redis.conf": "",
        }
    },
    "docs": {
        "API文档.md": "# API接口文档\n\n待补充...\n",
        "部署指南.md": "# 部署指南\n\n待补充...\n",
    },
    "scripts": {
        "clean_files.sh": "",
        "init_db.sh": "",
    },
    ".gitignore": "",
    "README.md": "",
    "LICENSE": "",
}


def create_structure(base_path: Path, structure: dict):
    """
    递归创建目录结构

    :param base_path: 基础路径
    :param structure: 目录结构字典
    """
    created_dirs = []
    created_files = []

    for name, content in structure.items():
        path = base_path / name

        if isinstance(content, dict):
            # 创建目录
            path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(path.relative_to(base_path.parent)))
            # 递归创建子目录
            sub_dirs, sub_files = create_structure(path, content)
            created_dirs.extend(sub_dirs)
            created_files.extend(sub_files)
        else:
            # 创建文件
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(content, encoding='utf-8')
                created_files.append(str(path.relative_to(base_path.parent)))

    return created_dirs, created_files


def main():
    """主函数"""
    # 获取当前脚本所在目录
    base_path = Path(__file__).parent

    print("=" * 60)
    print("论文评价检验系统 - 目录结构创建工具")
    print("=" * 60)
    print(f"\n当前工作目录: {base_path}")
    print(f"\n开始创建项目结构...\n")

    # 创建目录结构
    created_dirs, created_files = create_structure(base_path, STRUCTURE)

    # 输出统计信息
    print("=" * 60)
    print("创建完成！")
    print("=" * 60)
    print(f"\n[OK] 创建目录数: {len(created_dirs)}")
    print(f"[OK] 创建文件数: {len(created_files)}")

    print("\n主要目录结构：")
    main_dirs = [d for d in created_dirs if d.count(os.sep) == 0]
    for dir_name in sorted(main_dirs):
        print(f"  - {dir_name}/")

    print("\n接下来你可以：")
    print("  1. 运行 'python create_initial_files.py' 生成核心代码文件")
    print("  2. 进入 backend/ 目录，创建Python虚拟环境")
    print("  3. 进入 frontend/ 目录，安装Node.js依赖")
    print("  4. 查看 PROJECT_STRUCTURE.md 了解详细说明")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
