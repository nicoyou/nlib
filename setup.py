import os
import re
from codecs import open

import setuptools

here = os.path.abspath(os.path.dirname(__file__))
package_name = "nlib3"

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(os.path.join(here, package_name.replace("-", "_"), "__init__.py")) as f:
    init_text = f.read()
    version = re.search(r'__version__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
    license = re.search(r'__license__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
    author = re.search(r'__author__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
    author_email = re.search(r'__author_email__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
    url = re.search(r'__url__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)

assert version
assert license
assert author
assert author_email
assert url

setuptools.setup(
    name=package_name,                                                      # パッケージ名 ( プロジェクト名 )
    packages=[package_name.replace("-", "_")],                              # パッケージ内 ( プロジェクト内 ) のパッケージ名をリスト形式で指定 ( ここを指定しないとパッケージが含まれずに、テキストのみのパッケージになってしまう )
    version=version,                                                        # バージョン
    license=license,                                                        # ライセンス
    install_requires=[],                                                    # pip install する際に同時にインストールされるパッケージ名をリスト形式で指定
    author=author,                                                          # パッケージ作者の名前
    author_email=author_email,                                              # パッケージ作者の連絡先メールアドレス
    url=url,                                                                # パッケージに関連するサイトの URL ( GitHub など )
    description="You can use a slightly useful function.",                  # パッケージの簡単な説明
    long_description=long_description,                                      # PyPI に "Project description" として表示されるパッケージの説明文
    long_description_content_type="text/markdown",                          # long_description の形式を "text/plain", "text/x-rst", "text/markdown" のいずれかから指定
    keywords=f"{package_name} nlib library utility nicoyou_lib nicoyou",    # PyPI での検索用キーワードをスペース区切りで指定
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],                                                                      # パッケージ ( プロジェクト ) の分類 ( https://pypi.org/classifiers/ )
)
