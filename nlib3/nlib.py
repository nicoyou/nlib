import base64
import datetime
import enum
import inspect
import json
import logging
import math
import os
import platform
import re
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Final, TypeAlias, overload

OUTPUT_DIR: Final[Path] = Path("./data")                # 情報を出力する際のディレクトリ
LOG_PATH: Final[Path] = OUTPUT_DIR / "lib.log"          # ログのファイルパス
ERROR_LOG_PATH: Final[Path] = OUTPUT_DIR / "error.log"  # エラーログのファイルパス
DISPLAY_DEBUG_LOG_FLAG: Final[bool] = True              # デバッグログを出力するかどうか
DEFAULT_ENCODING: Final[str] = "utf-8"                  # ファイル IO の標準エンコード

# type alias
Number: TypeAlias = int | float
JsonValue: TypeAlias = int | float | bool | str | None

IntList: TypeAlias = list[int] | tuple[int, ...]
FloatList: TypeAlias = list[float] | tuple[float, ...]
BoolList: TypeAlias = list[bool] | tuple[bool, ...]
StrList: TypeAlias = list[str] | tuple[str, ...]


class LibErrorCode(enum.Enum):
    """ライブラリ内の一部関数で返されるエラーコード
    """
    success = enum.auto()           # 成功
    file_not_found = enum.auto()    # ファイルが見つからなかった
    http = enum.auto()              # http 通信のエラー
    argument = enum.auto()          # 引数が原因のエラー
    cancel = enum.auto()            # 前提条件不一致で処理がキャンセルされたときのエラー
    unknown = enum.auto()           # 不明なエラー


class Vector2():
    """2 次元ベクトルの値を格納するためのクラス
    Vector2.x と Vector2.y か Vector2[0] と Vector2[1] でそれぞれの値にアクセスできる
    """
    def __init__(self, x: Number | tuple[Number, Number] | list[Number] = 0, y: Number = 0) -> None:
        """それぞれの値を初期化する、値を指定しなかった場合は 0 で初期化される
        x に Vector2 クラスをそのまま渡せば、その Vector2 の値で初期化される
        x にリストやタプルを渡した場合は、一つ目の要素が x 二つ目の要素が y となる

        Args:
            x: 数値を指定する
            y: 数値を指定する
        """
        self.x: Number = 0
        self.y: Number = 0
        self.set(x, y)
        return

    def set(self, x: Number | tuple[Number, Number] | list[Number], y: Number = 0) -> Any:
        """それぞれの値を初期化する、値を指定しなかった場合は 0 で初期化される
        x に Vector2 クラスをそのまま渡せば、その Vector2 の値で初期化される
        x にリストやタプルを渡した場合は、一つ目の要素が x 二つ目の要素が y となる

        Args:
            x: 数値を指定する
            y: 数値を指定する
        """
        if isinstance(x, self.__class__) and y == 0:
            self.x = x.x
            self.y = x.y
        elif type(x) is tuple or type(x) is list:
            if len(x) == 2 and y == 0:
                self.x = x[0]
                self.y = x[1]
            else:
                raise ValueError("不正な引数が指定されました")
        else:
            self.x = x
            self.y = y
        return self

    def max(self) -> Number:
        """x と y のうち大きい方の値を取得する

        Returns:
            x か y の値
        """
        return self.x if self.x >= self.y else self.y

    def min(self) -> Number:
        """x と y のうち小さい方の値を取得する

        Returns:
            x か y の値
        """
        return self.x if self.x <= self.y else self.y

    def round(self) -> Any:     # __class__ 未対応のため Any
        """x と y それぞれの小数点以下を丸める

        Returns:
            x, y の小数点以下を丸めた Vector2
        """
        return self.__class__(round(self.x), round(self.y))

    def floor(self) -> Any:
        """x と y それぞれの小数点以下を切り捨てる

        Returns:
            x, y の小数点以下を切り捨てた Vector2
        """
        return self.__class__(math.floor(self.x), math.floor(self.y))

    def ceil(self) -> Any:
        """x と y それぞれの小数点以下を切り上げる

        Returns:
            x, y の小数点以下を切り上げた Vector2
        """
        return self.__class__(math.ceil(self.x), math.ceil(self.y))

    def invert(self) -> Any:
        """x と y の値を入れ替える

        Returns:
            x, y の値を入れ替えた Vector2
        """
        return self.__class__(self.y, self.x)

    def to_self_type(self, x: Any) -> Any:
        """自クラス型以外の値を自クラス型へ変換する

        Args:
            x: 自クラス型か数値

        Returns:
            自クラス型の値
        """
        if isinstance(x, self.__class__):
            return x
        else:
            return self.__class__(x, x)

    def __str__(self) -> str:
        return f"x={self.x}, y={self.y}"

    def __repr__(self) -> str:
        return self.__str__()

    def __bool__(self) -> bool:
        return (bool(self.x) or bool(self.y))

    # 比較演算子
    def __eq__(self, other):
        other = self.to_self_type(other)
        return (self.x == other.x and self.y == other.y)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        other = self.to_self_type(other)
        return (self.x < other.x and self.y < other.y)

    def __gt__(self, other):
        other = self.to_self_type(other)
        return (self.x > other.x and self.y > other.y)

    # 算術演算子
    def __add__(self, other):
        other = self.to_self_type(other)
        return self.__class__(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        other = self.to_self_type(other)
        return self.__class__(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        other = self.to_self_type(other)
        return self.__class__(self.x * other.x, self.y * other.y)

    def __truediv__(self, other):
        other = self.to_self_type(other)
        return self.__class__(self.x / other.x, self.y / other.y)

    def __floordiv__(self, other):
        other = self.to_self_type(other)
        return self.__class__(self.x // other.x, self.y // other.y)

    def __mod__(self, other):
        other = self.to_self_type(other)
        return self.__class__(self.x % other.x, self.y % other.y)

    def __pow__(self, other):
        other = self.to_self_type(other)
        return self.__class__(self.x**other.x, self.y**other.y)

    # 算術演算子 (右辺)
    def __radd__(self, other):
        other = self.to_self_type(other)
        return self.__class__(other.x + self.x, other.y + self.y)

    def __rsub__(self, other):
        other = self.to_self_type(other)
        return self.__class__(other.x - self.x, other.y - self.y)

    def __rmul__(self, other):
        other = self.to_self_type(other)
        return self.__class__(other.x * self.x, other.y * self.y)

    def __rtruediv__(self, other):
        other = self.to_self_type(other)
        return self.__class__(other.x / self.x, other.y / self.y)

    def __rfloordiv__(self, other):
        other = self.to_self_type(other)
        return self.__class__(other.x // self.x, other.y // self.y)

    def __rmod__(self, other):
        other = self.to_self_type(other)
        return self.__class__(other.x % self.x, other.y % self.y)

    def __rpow__(self, other):
        other = self.to_self_type(other)
        return self.__class__(other.x**self.x, other.y**self.y)

    # 単項演算子
    def __neg__(self):
        return self.__class__(-self.x, -self.y)

    def __pos__(self):
        return self.__class__(+self.x, +self.y)

    def __invert__(self):
        return self.__class__(~self.x, ~self.y)

    def __len__(self):
        return 2

    def __getitem__(self, index):
        if index == 0 or index == "x":
            return self.x
        elif index == 1 or index == "y":
            return self.y
        raise IndexError


class Url(str):
    """URL を格納するクラス
    """
    def __new__(cls, *content):
        return str.__new__(cls, content[0])     # 他の引数を認識させないために情報を削る

    def __init__(self, url: str, param: dict[str, Any] = {}) -> None:
        self.url = str(url)     # Url クラスを渡されてもそのまま文字列として処理する
        self.param = deepcopy(param)
        self.SCHEME_END: Final[str] = "://"

        if "?" in self.url:
            temp = self.url.split("?")
            if len(temp) != 2:
                raise ValueError("不正な URL です")
            self.url = temp[0]  # URL から ? を削除する
            if temp[1] != "":   # パラメーターが存在すれば
                for row in temp[1].split("&"):
                    k, v = row.split("=")
                    self.param |= {k: v}
        return

    @property
    def name(self) -> str:
        """URL の末尾を取得する

        Returns:
            URL の末尾
        """
        return self.url.split("/")[-1]

    @property
    def parent(self) -> Any:
        """現在の URL の上位 URL を取得する

        Returns:
            現在の URL の上位 URL
        """
        temp = self.url.split(self.SCHEME_END)
        if len(temp) != 2:
            return self.__class__(("/").join(self.url.split("/")[:-1]), self.param)
        return self.__class__(temp[0] + (self.SCHEME_END) + ("/").join(temp[1].split("/")[:-1]), self.param)

    def with_name(self, name: str) -> Any:
        """URL の name 属性を引数に与えた名前に変換した URL を取得

        Args:
            name: URL の末尾

        Returns:
            URL の末尾を変換した URL
        """
        return self.parent / name

    def add_param(self, key: str, value: Any) -> Any:
        """パラメータを追加する

        Args:
            key: パラメータのキー
            value: 値

        Returns:
            パラメータを追加した URL オブジェクト
        """
        return self.__class__(self.url, self.param | {key: value})

    def pop_param(self, key: str) -> Any:
        """URL パラメーターを削除する

        Args:
            key: 削除するパラメーターのキー

        Returns:
            パラメータを削除した URL オブジェクト
        """
        param = deepcopy(self.param)
        param.pop(key)
        return self.__class__(self.url, param)

    def format(self, *args: object, **kwargs: object):
        """URL に対して format 関数を使用する

        Returns:
            format 関数の返り値
        """
        return self.url.format(*args, **kwargs)

    def __truediv__(self, other: str) -> Any:
        if other[0] == "/":
            other = other[1:]
        return self.__class__(self.url + "/" + other, self.param)

    def __str__(self) -> str:
        if self.param:
            result = self.url
            for i, (k, v) in enumerate(self.param.items()):
                if i == 0:
                    result += "?"
                else:
                    result += "&"
                if type(v) is bool:     # bool 型はすべて小文字にする
                    v = str(v).lower()
                result += f"{k}={v}"
            return result

        return self.url

    def __repr__(self) -> str:
        return self.__str__()

    def __bool__(self) -> bool:
        return bool(self.url) or bool(self.param)

    def __getitem__(self, key: Any):
        return self.param[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        self.param[key] = value
        return

    def __contains__(self, value) -> bool:
        return value in self.param.keys()


class StrEnum(str, enum.Enum):
    """str のサブクラスでもある列挙型を作成する基底クラス
    """
    def __str__(self) -> str:
        return str(self.value)


class JsonData():
    """Jsonファイルから一つの値を読み込んで保持するクラス
    """
    def __init__(self, keys: str | StrList, default: JsonValue, path: str | Path) -> None:
        """Jsonファイルから読み込む値を指定する

        Args:
            keys: Jsonデータのキーを指定する ( 複数階層ある場合はリストで渡す )
            default: 値が存在しなかった場合のデフォルトの値を設定する
            path: Jsonファイルのパス
        """
        self.keys = keys
        self.default = default
        self.path = Path(path)
        self.data = None
        self.load_error_flag = False
        self.load()
        return

    def load(self) -> bool:
        """ファイルから値を読み込む

        Returns:
            正常に読み込めた場合か、デフォルト値で初期化した場合は True
            何らかのエラーが発生した場合は False
        """
        try:
            json_data = load_json(self.path)
            if type(self.keys) is not list and type(self.keys) is not tuple:
                self.keys = (self.keys, )       # タプルでもリストでもなければタプルに加工する
            try:
                for row in self.keys:
                    json_data = json_data[row]  # キーの名前をたどっていく
                self.data = json_data
                return True
            except KeyError as e:
                self.data = self.default        # キーが見つからなければデフォルト値を設定する
                return True
        except FileNotFoundError as e:          # ファイルが見つからなかった場合はデフォルト値を設定する
            self.data = self.default
            return True
        except Exception as e:
            self.data = self.default
            self.load_error_flag = True
            print_error_log(f"json ファイルの読み込みに失敗しました [keys={self.keys}]\n{e}")
        return False

    def save(self) -> bool:
        """ファイルに現在保持している値を保存する

        Returns:
            ファイルへの保存が成功した場合は True
        """
        if self.load_error_flag:
            print_error_log("データの読み込みに失敗しているため、上書き保存をスキップしました")
            return False
        json_data = {}
        try:
            json_data = load_json(self.path)
        except FileNotFoundError as e:              # ファイルが見つからなかった場合は
            print_log(f"json ファイルが見つからなかったため、新規生成します [keys={self.keys}]\n{e}")
        except json.decoder.JSONDecodeError as e:   # json の文法エラーがあった場合は新たに上書き保存する
            print_log(f"json ファイルが壊れている為、再生成します [keys={self.keys}]\n{e}")
        except Exception as e:                      # 不明なエラーが起きた場合は上書きせず終了する
            print_error_log(f"json ファイルへのデータの保存に失敗しました [keys={self.keys}]\n{e}")
            return False
        try:
            update_nest_dict(json_data, self.keys, self.data)
            save_json(self.path, json_data)
            return True
        except Exception as e:
            print_error_log(f"json への出力に失敗しました [keys={self.keys}]\n{e}")
        return False

    def increment(self, save_flag: bool = False, num: int = 1) -> bool:
        """値をインクリメントしてファイルに保存する ( 数値以外が保存されていた場合は 0 で初期化 )

        Args:
            save_flag: ファイルにデータを保存するかどうかを指定する
            num: 増加させる値を指定する

        Returns:
            データがファイルに保存されれば True
        """
        if not can_cast(self.get(), int):                   # int 型に変換できない場合は初期化する
            print_error_log(f"使用できない値を初期化します [keys={self.keys}, value={self.get()}]")
            self.set(0)
        return self.set(int(self.get()) + num, save_flag)   # 一つインクリメントして値を保存する

    def get(self) -> JsonValue:
        """現在保持している値を取得する

        Returns:
            保持している値
        """
        return self.data

    def set(self, data: JsonValue, save_flag: bool = False) -> bool:
        """新しい値を登録する

        Args:
            data: 新しく置き換える値
            save_flag: ファイルに新しい値を保存するかどうか

        Returns:
            データがファイルに保存されれば True
        """
        self.data = data
        if save_flag:
            return self.save()  # 保存フラグが立っていれば保存する
        return False            # 保存無し

    def get_keys(self) -> tuple:
        """Jsonファイルのこの値が保存されているキーを取得する

        Returns:
            値にたどり着くまでのキー
        """
        return tuple(self.keys)

    def get_default(self) -> JsonValue:
        """設定されているデフォルト値を取得する

        Returns:
            ファイルに値が存在しなかった時に使用するデフォルト値
        """
        return self.default

    def file_exists(self) -> bool:
        """json ファイルが存在するかどうかを取得する

        Returns:
            ファイルが存在すれば True
        """
        return self.path.is_file()

    def __str__(self) -> str:
        return str(self.data)

    def __repr__(self) -> str:
        return self.__str__()


def thread(func: Callable) -> Callable:
    """関数をマルチスレッドで実行するためのデコレーター
    """
    def inner(*args, **kwargs) -> threading.Thread:
        th = threading.Thread(target=lambda: func(*args, **kwargs))
        th.start()
        return th

    return inner


def make_lib_dir() -> None:
    """ライブラリ内で使用するディレクトリを作成する
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)  # データを出力するディレクトリを生成する
    return


def get_error_message(code: LibErrorCode) -> str:
    """ライブラリ内エラーコードからエラーメッセージを取得する

    Args:
        code: ライブラリのエラーコード

    Returns:
        コードに対応するエラーメッセージ
    """
    if code == LibErrorCode.success:
        return "処理が正常に終了しました"
    elif code == LibErrorCode.file_not_found:
        return "ファイルが見つかりませんでした"
    elif code == LibErrorCode.http:
        return "HTTP通信関係のエラーが発生しました"
    elif code == LibErrorCode.argument:
        return "引数が適切ではありません"
    elif code == LibErrorCode.cancel:
        return "処理がキャンセルされました"
    elif code == LibErrorCode.unknown:
        return "不明なエラーが発生しました"
    else:
        print_error_log("登録されていないエラーコードが呼ばれました", console_print=False)
    return "不明なエラーが発生しました"


def create_logger(name: str = "main", path: Path | None = None, error_path: Path | None = None, level=logging.DEBUG, encoding=DEFAULT_ENCODING):
    """ロガーを作成する

    Args:
        name: ロガー名
        path: ログファイルのパス
        error_path: ログレベルが ERROR 以上のログを出力するファイルのパス ( 指定しなかった場合は path と同じファイルに出力 )
        level: 実際に表示する最低ログレベル

    Returns:
        出力情報が設定されたロガー
    """
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    detailed_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(filename)s(%(lineno)d) %(message)s", "%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger(name)
    logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if path is not None:
        file_handler = logging.FileHandler(path, encoding=encoding)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        class LevelFilter(logging.Filter):
            def filter(self, record):
                return record.levelno in [logging.DEBUG, logging.INFO, logging.WARNING]

        file_handler.addFilter(LevelFilter())   # ERROR 以上のログレベルは error_path に出力するため、file_handler からは除外する
        logger.addHandler(file_handler)

        error_file_handler = logging.FileHandler(error_path if error_path is not None else path, encoding=encoding)
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_file_handler)
    return logger


def print_log(message: object, console_print: bool = True, error_flag: bool = False, file_name: str = "", file_path: str | Path | None = None) -> bool:
    """ログをファイルに出力する

    Deprecated:
        非推奨の関数です
        この関数は create_logger 関数によって代替されました

    Args:
        message: ログに出力する内容
        console_print: コンソール出力するかどうか
        error_flag: 通常ログではなく、エラーログに出力するかどうか
        file_name: 出力するファイル名を指定する ( 拡張子は不要 )
        file_path: 出力するファイルのパスを指定する

    Returns:
        正常にファイルに出力できた場合は True
    """
    log_path: Path = LOG_PATH
    if error_flag:  # エラーログの場合はファイルを変更する
        log_path = ERROR_LOG_PATH
    if file_name:
        log_path = OUTPUT_DIR / f"{file_name}.log"
    if file_path is not None:
        log_path = Path(file_path)
    if console_print:
        print_debug(message)
    if file_name and file_path:
        raise ValueError

    time_now = get_datetime_now(True)                                           # 現在時刻を取得する
    if not log_path.is_file() or log_path.stat().st_size < 1024 * 1000 * 50:    # 50MBより小さければ出力する
        os.makedirs(OUTPUT_DIR, exist_ok=True)                                  # データを出力するディレクトリを生成する
        with open(log_path, mode="a", encoding=DEFAULT_ENCODING) as f:
            if error_flag:                                                      # エラーログ
                frame = inspect.currentframe()                                  # 関数が呼ばれた場所の情報を取得する
                if frame is not None:
                    frame = frame.f_back
                if frame is not None:
                    frame = frame.f_back

                code_name = ""
                if frame is not None:
                    try:
                        class_name = str(frame.f_locals["self"])
                        class_name = re.match(r'.*?__main__.(.*?) .*?', class_name)
                        if class_name is not None:
                            class_name = class_name.group(1)
                    except KeyError:    # クラス名が見つからなければ
                        class_name = None
                    err_file_name = os.path.splitext(os.path.basename(frame.f_code.co_filename))[0]

                    if class_name is not None:
                        code_name = f"{err_file_name}.{class_name}.{frame.f_code.co_name}({frame.f_lineno})"
                    else:
                        code_name = f"{err_file_name}.{frame.f_code.co_name}({frame.f_lineno})"
                f.write(f"[{time_now}] {code_name}".ljust(90) + str(message).rstrip("\n").replace("\n", "\n" + f"[{time_now}]".ljust(90)) + "\n")   # 最後の改行文字を取り除いて文中の改行前にスペースを追加する
            else:                                                                                                                                   # 普通のログ
                f.write("[{}] {}\n".format(time_now, str(message).rstrip("\n")))
            return True
    else:
        print_debug("ログファイルの容量がいっぱいの為、出力を中止しました")
    return False


def print_error_log(message: object, console_print: bool = True) -> bool:
    """エラーログを出力する

    Deprecated:
        非推奨の関数です
        この関数は create_logger 関数によって代替されました

    Args:
        message: ログに出力する内容
        console_print: 内容をコンソールに出力するかどうか

    Returns:
        正常にファイルに出力できた場合は True
    """
    return print_log(message, console_print, True)


def print_debug(message: object, end: str = "\n") -> bool:
    """デバッグログをコンソールに出力する

    Deprecated:
        非推奨の関数です
        この関数は create_logger 関数によって代替されました

    Args:
        message: 出力する内容
        end: 最後に追加で出力される内容

    Returns:
        実際にコンソールに出力された場合は True
    """
    if DISPLAY_DEBUG_LOG_FLAG:
        print(message, end=end)
    return DISPLAY_DEBUG_LOG_FLAG


def load_json(file_path: str | Path) -> Any:
    """jsonファイルを読み込む

    Args:
        file_path: jsonファイルパス

    Returns:
        読み込んだjsonファイルのデータ
    """
    with open(file_path, "r", encoding=DEFAULT_ENCODING) as f:
        obj = json.load(f)
    return obj


def save_json(file_path: str | Path, obj: Any, ensure_ascii: bool = False) -> None:
    """データを json ファイルに保存する

    Args:
        file_path: json ファイルパス
        data: 保存するデータ
        ensure_ascii: 非 ASCII 文字文字をエスケープする
    """
    with open(file_path, "w", encoding=DEFAULT_ENCODING) as f:
        json.dump(obj, f, indent=4, ensure_ascii=ensure_ascii)
    return


def json_dumps(json_data: str | dict, ensure_ascii: bool = False) -> str:
    """Json 文字列か辞書を整形された Json 形式の文字列に変換する

    Args:
        json_data: Json ファイルのファイルパスか、出力したいデータの辞書
        ensure_ascii: 非 ASCII 文字文字をエスケープする

    Returns:
        整形された Json 形式の文字列
    """
    if type(json_data) is str:
        data = json.loads(json_data)
    else:
        data = json_data

    data_str = json.dumps(data, indent=4, ensure_ascii=ensure_ascii)
    return data_str


def update_nest_dict(dictionary: dict, keys: object | list | tuple, value: object) -> bool:
    """ネストされた辞書内の特定の値のみを再帰で変更する関数

    Args:
        dictionary: 更新する辞書
        keys: 更新する値にたどり着くまでのキーを指定し、複数あればlistかtupleで指定する
        value: 上書きする値

    Returns:
        再帰せずに更新した場合のみ True、再帰した場合は False
    """
    if type(keys) is not list and type(keys) is not tuple:
        keys = (keys, )                                         # 渡されがキーがリストでもタプルでもなければタプルに変換する
    if len(keys) == 1:
        dictionary[keys[0]] = value                             # 最深部に到達したら値を更新する
        return True
    if keys[0] in dictionary:
        update_nest_dict(dictionary[keys[0]], keys[1:], value)  # すでにキーがあればその内部から更に探す
    else:
        dictionary[keys[0]] = {}                                # キーが存在しなければ空の辞書を追加する
        update_nest_dict(dictionary[keys[0]], keys[1:], value)
    return False


def check_url(url: str) -> bool:
    """リンク先が存在するかどうかを確認する

    Args:
        url: 存在を確認するURL

    Returns:
        リンク先に正常にアクセスできた場合は True
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"}
        req = urllib.request.Request(url, None, headers)
        f = urllib.request.urlopen(req)
        f.close()
        time.sleep(0.1)
    except Exception:
        return False    # 失敗
    return True         # 成功


def download_file(url: str, dest_path: str, overwrite: bool = True) -> LibErrorCode:
    """インターネット上からファイルをダウンロードする

    Args:
        url: ダウンロードするファイルのURL
        dest_path: ダウンロードしたファイルを保存するローカルファイルパス
        overwrite: 同名のファイルが存在した場合に上書きするかどうか

    Returns:
        ライブラリのエラーコード
    """
    if not overwrite and os.path.isfile(dest_path):
        return LibErrorCode.cancel

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"}
        req = urllib.request.Request(url, None, headers)
        with urllib.request.urlopen(req) as web_file:
            data = web_file.read()
            with open(dest_path, mode="wb") as local_file:
                local_file.write(data)
                time.sleep(0.1)
                return LibErrorCode.success
    except urllib.error.HTTPError as e:
        print_error_log(f"{e} [url={url}]")
        return LibErrorCode.argument    # HTTPエラーが発生した場合は引数エラーを返す
    except (urllib.error.URLError, TimeoutError) as e:
        print_error_log(f"{e} [url={url}]")
        return LibErrorCode.http
    except FileNotFoundError as e:
        print_error_log(f"{e} [url={url}]")
        return LibErrorCode.file_not_found
    return LibErrorCode.unknown


def download_and_check_file(url: str, dest_path: str, overwrite: bool = True, trial_num: int = 3, trial_interval: int = 3) -> LibErrorCode:
    """ファイルをダウンロードして、失敗時に再ダウンロードを試みる

    Args:
        url: ダウンロードするファイルのURL
        dest_path: ダウンロードしたファイルを保存するローカルファイルパス
        overwrite: 同名のファイルが存在した場合に上書きするかどうか
        trial_num: 最初の一回を含むダウンロード失敗時の再試行回数
        trial_interval: ダウンロード再試行までのクールタイム

    Returns:
        ライブラリのエラーコード
    """
    result = download_file(url, dest_path, overwrite)
    if result in [LibErrorCode.cancel, LibErrorCode.argument, LibErrorCode.file_not_found]:     # 既にファイルが存在した場合と引数が間違えている場合は処理を終了する
        return result
    for i in range(trial_num):
        if not os.path.isfile(dest_path):
            print_debug(f"ダウンロードに失敗しました、{trial_interval}秒後に再ダウンロードします ( {i + 1} Fail )")
            time.sleep(trial_interval)
            result = download_file(url, dest_path, overwrite)                                   # 一度目はエラーコードに関わらず失敗すればもう一度ダウンロードする
            if result == LibErrorCode.argument:                                                 # URLが間違っていれば処理を終了する
                return result
        elif result == LibErrorCode.success:                                                    # ダウンロード成功
            return LibErrorCode.success
    return LibErrorCode.unknown


def read_tail(path: str, n: int, encoding: str | None = None) -> list[str]:
    """ファイルを後ろから指定した行だけ読み込む

    Args:
        path: 読み込むファイルのファイルパス
        n: 読み込む行数
        encoding: ファイルのエンコード

    Returns:
        実際に読み込んだ結果
    """
    try:
        with open(path, "r", encoding=encoding) as f:
            lines = f.readlines()   # すべての行を取得する
    except FileNotFoundError:
        lines = []
    return lines[-n:]               # 後ろから n 行だけ返す


def rename_path(file_path: str, dest_name: str, up_hierarchy_num: int = 0, slash_only: bool = False) -> str:
    """ファイルパスの指定した階層をリネームする

    Args:
        file_path: リネームするファイルパス
        dest_name: 変更後のディレクトリ名
        up_hierarchy_num: 変更するディレクトリの深さ ( 一番深いディレクトリが 0 )
        slash_only: パスの区切り文字をスラッシュのみにするかどうか

    Returns:
        変換後のファイルパス
    """
    file_name = ""
    for i in range(up_hierarchy_num):   # 指定された階層分だけパスの右側を避難する
        if i == 0:
            file_name = os.path.basename(file_path)
        else:
            file_name = os.path.join(os.path.basename(file_path), file_name)
        file_path = os.path.dirname(file_path)

    file_path = os.path.dirname(file_path)              # 一番深い階層を削除する
    file_path = os.path.join(file_path, dest_name)      # 一番深い階層を新しい名前で追加する
    if file_name != "":
        file_path = os.path.join(file_path, file_name)  # 避難したファイルパスを追加する
    if slash_only:
        file_path = file_path.replace("\\", "/")        # 引数で指定されていれば区切り文字をスラッシュで統一する
    return file_path


# JAN コードのチェックデジットを計算して取得する
def get_check_digit(jan_code: int | str) -> int | None:
    """JAN コードのチェックデジットを計算して取得する

    Args:
        jan_code: 13 桁の JAN コードか、その最初の 12 桁

    Returns:
        13 桁目のチェックデジット
    """
    if not type(jan_code) is str:
        jan_code = str(jan_code)
    if len(jan_code) == 13:
        jan_code = jan_code[:12]
    if len(jan_code) != 12:
        return None

    try:
        even_sum = 0
        odd_sum = 0
        for i in range(12):
            if (i + 1) % 2 == 0:
                even_sum += int(jan_code[i])                        # 偶数桁の合計
            else:
                odd_sum += int(jan_code[i])                         # 奇数桁の合計
        check_digit = (10 - (even_sum * 3 + odd_sum) % 10) % 10     # チェックデジット
    except Exception as e:
        print_error_log(e)
        return None
    return check_digit


def program_pause(program_end: bool = True) -> None:
    """入力待機でプログラムを一時停止する関数

    Args:
        program_end: 再開した時にプログラムを終了する場合は True、処理を続ける場合は False
    """
    if not False:   #__debug__:            # デバッグでなければ一時停止する
        if program_end:
            message = "Press Enter key to exit . . ."
        else:
            message = "Press Enter key to continue . . ."
        input(message)
    return


def input_while(str_info: str, branch: Callable[[str], bool] = lambda in_str: in_str != "") -> str:
    """条件に一致する文字が入力されるまで再入力を求める入力関数 ( デフォルトでは空白のみキャンセル )

    Args:
        str_info: 入力を求める時に表示する文字列
        branch: 正常な入力かどうかを判断する関数

    Returns:
        入力された文字列
    """
    while True:
        in_str = input(str_info)
        if branch(in_str):
            return in_str
        else:
            print("\n不正な値が入力されました、再度入力して下さい")
    return ""


@overload
def get_datetime_now() -> datetime.datetime:
    pass


@overload
def get_datetime_now(to_str: bool) -> str:
    pass


def get_datetime_now(to_str: bool = False) -> datetime.datetime | str:
    """日本の現在の datetime を取得する

    Args:
        to_str: 文字列に変換して取得するフラグ

    Returns:
        日本の現在時間を datetime 型か文字列で返す
    """
    datetime_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), "JST"))     # 日本の現在時刻を取得する
    if not to_str:
        return datetime_now
    return datetime_now.strftime("%Y-%m-%d %H:%M:%S")                                               # 文字列に変換する


def compress_hex(hex_str: str, decompression: bool = False) -> str:
    """16進数の文字列を圧縮、展開する

    Args:
        hex_str: 16 進数の値
        decompression: 渡された値を圧縮ではなく展開するフラグ

    Returns:
        圧縮 or 展開した文字列
    """
    if decompression:                                           # 展開が指定されていれば展開する
        if type(hex_str) is not str:
            return ""                                           # 文字列以外が渡されたら空白の文字列を返す
        hex_str = hex_str.replace("-", "+").replace("_", "/")   # 安全な文字列を base64 の記号に復元する
        hex_str += "=" * (len(hex_str) % 4)                     # 取り除いたパディングを復元する
        hex_bytes = hex_str.encode()

        hex_bytes = base64.b64decode(hex_bytes)
        hex_bytes = base64.b16encode(hex_bytes)
        return hex_bytes.decode()

    if type(hex_str) is str:
        hex_bytes = hex_str.encode()    # バイナリデータでなければバイナリに変換する
    elif type(hex_str) is bytes:
        hex_bytes = hex_str
    else:
        raise ValueError("使用できない型が使用されました")
    if len(hex_bytes) % 2 != 0:
        hex_bytes = b"0" + hex_bytes    # 奇数の場合は先頭に0を追加して偶数にする

    hex_bytes = base64.b16decode(hex_bytes, casefold=True)
    hex_bytes = base64.b64encode(hex_bytes)
    return hex_bytes.decode().replace("=", "").replace("+", "-").replace("/", "_")  # パディングを取り除いて安全な文字列に変換する


def subprocess_command(command: StrList) -> bytes:
    """OS のコマンドを実行する

    Args:
        command: 実行するコマンド

    Returns:
        実行結果
    """
    if platform.system() == "Windows":                  # Windows の環境ではコマンドプロンプトを表示しないようにする
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW   # コマンドプロンプトを表示しない
        return subprocess.check_output(command, startupinfo=si)
    else:                                               # STARTUPINFO が存在しない OS があるため処理を分岐する
        return subprocess.check_output(command)


def print_exc() -> None:
    """スタックされているエラーを表示する
    """
    if DISPLAY_DEBUG_LOG_FLAG:
        traceback.print_exc()
        print_debug("\n")
        print_debug(sys.exc_info())
    return


def can_cast(x: Any, cast_type: Callable) -> bool:
    """指定された値がキャストできるかどうかを確認する

    Args:
        x: 確認する値
        cast_type: チェックするためのキャスト関数

    Returns:
        キャストできる場合は True
    """
    try:
        cast_type(x)
    except ValueError:
        return False
    return True


def get_python_version() -> str:
    """Python のバージョン情報を文字列で取得する

    Returns:
        Python のバージョン
    """
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return version
