import os
import hashlib
from utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

'''
md5_obj = hashlib.md5()：初始化一个空的“锅”。

md5_obj.update(chunk)：每读取 4KB 数据，就把它丢进锅里搅拌。注意，丢进去后，md5_obj 的内部状态会改变，它记住了目前为止所有数据的特征，但它并没有产出 MD5。

md5_obj.hexdigest()：这才是最关键的一步。只有当你把文件全部“喂”完，按下这个按钮时，它才会根据锅里所有数据累积的状态，计算出一个最终的 32 位十六进制字符串。
'''
def get_file_md5_hex(filepath: str):     # 获取文件的md5的十六进制字符串

    if not os.path.exists(filepath):
        logger.error(f"[md5计算]文件{filepath}不存在")
        return

    if not os.path.isfile(filepath):
        logger.error(f"[md5计算]路径{filepath}不是文件")
        return

    md5_obj = hashlib.md5()

    chunk_size = 4096       # 4KB分片，避免文件过大爆内存
    try:
        with open(filepath, "rb") as f:     # 必须二进制读取
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)

            """
            chunk = f.read(chunk_size)
            while chunk:
                
                md5_obj.update(chunk)
                chunk = f.read(chunk_size)
            """
            md5_hex = md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"计算文件{filepath}md5失败，{str(e)}")
        return None


def listdir_with_allowed_type(path: str, allowed_types: tuple[str]):        # 返回文件夹内的文件列表（允许的文件后缀）
    files = []

    if not os.path.isdir(path):
        logger.error(f"[listdir_with_allowed_type]{path}不是文件夹")
        return allowed_types

    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path, f))

    return tuple(files)

#以页为单位，每一页是一个Document
def pdf_loader(filepath: str, passwd=None) -> list[Document]:
    return PyPDFLoader(filepath, passwd).load()

#整个文档为单位，只会返回一个Document
def txt_loader(filepath: str) -> list[Document]:
    return TextLoader(filepath, encoding="utf-8").load()
"""
list document
result = [
    Document(  # 第1页
        page_content="这是第1页的文字内容...",
        metadata={
            "source": "example.pdf",
            "page": 1,
            "page_label": "1"
        }
    ),
    Document(  # 第2页
        page_content="这是第2页的文字内容...",
        metadata={
            "source": "example.pdf", 
            "page": 2,
            "page_label": "2"
        }
    ),
    Document(  # 第3页
        page_content="这是第3页的文字内容...",
        metadata={
            "source": "example.pdf",
            "page": 3,
            "page_label": "3"
        }
    )
] 
长这个样子
"""