call .venv/Scripts/activate.bat

@rem 古いファイルを削除する
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q nlib3.egg-info

@rem ソースコード配布物を作成
python setup.py sdist

@rem ライブラリのパッケージ作成
python setup.py bdist_wheel

timeout 5
