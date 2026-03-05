#!/usr/bin/env python3
"""下载本地 Embedding 模型"""
import os
from pathlib import Path

from loguru import logger

# 配置使用国内镜像源
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TRANSFORMERS_CACHE"] = str(Path(__file__).parent.parent / "models")
os.environ["HF_HOME"] = str(Path(__file__).parent.parent / "models")

logger.info("开始下载 BAAI/bge-m3 模型...")
logger.info(f"使用镜像源: {os.environ['HF_ENDPOINT']}")
logger.info(f"模型将保存到: {os.environ['HF_HOME']}")

try:
    from sentence_transformers import SentenceTransformer

    # 下载模型
    model = SentenceTransformer(
        "BAAI/bge-m3",
        device="cpu",
        cache_folder=str(Path(__file__).parent.parent / "models"),
    )

    # 测试模型
    test_text = "这是一个测试句子"
    embedding = model.encode(test_text, show_progress_bar=False)

    logger.success(f"✓ 模型下载成功!")
    logger.info(f"  - 模型维度: {len(embedding)}")
    logger.info(f"  - 存储位置: {model._first_module().model_path}")

except Exception as e:
    logger.error(f"✗ 模型下载失败: {e}")
    logger.info("\n由于网络原因,模型下载失败。系统将使用远程 API 作为备选方案。")
    logger.info("\n如需手动下载,可访问:")
    logger.info("  - https://hf-mirror.com/BAAI/bge-m3 (国内镜像)")
    logger.info("  - https://huggingface.co/BAAI/bge-m3 (官方源)")
    exit(1)
