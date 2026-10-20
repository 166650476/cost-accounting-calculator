"""通用工具模块（成本会计学综合计算器）。

本模块集中提供：
1. 项目路径与目录初始化（output、chart）；
2. 数值校验、除零保护、金额分配、线性方程组求解；
3. 控制台交互输入（支持“回车使用默认值”）；
4. 中文宽度友好的表格、解题步骤、会计分录输出；
5. 章节菜单的统一定义与异常兜底。

所有业务章节只负责“核算逻辑 + 文字说明”，界面与容错逻辑尽量复用本模块。
"""

from __future__ import annotations

import math
import os
import sys
import unicodedata
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# 一、项目路径
# ---------------------------------------------------------------------------
# 源码运行时，输出目录位于项目文件夹；若将来用 PyInstaller 打包为 exe，
# 则把 output、chart 放在 exe 所在目录，避免写入临时解压目录。
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CHART_DIR = BASE_DIR / "chart"


def ensure_dirs() -> None:
    """创建 output 与 chart 目录。重复调用不会报错。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)


ensure_dirs()


class ValidationError(ValueError):
    """参数不合法时抛出的业务异常，用于输出友好的中文提示。"""


# ---------------------------------------------------------------------------
# 二、数值校验与基础计算
# ---------------------------------------------------------------------------
def require_number(
    value: Any,
    name: str = "数值",
    *,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> float:
    """把输入转换为有限浮点数，并检查上下限。

    拒绝 None、布尔值、空字符串、NaN、无穷大以及无法转换的文本。
    """
    if value is None or isinstance(value, bool):
        raise ValidationError(f"{name}必须是有效数字，不能为空。")
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if value == "":
            raise ValidationError(f"{name}不能为空。")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name}必须是数字，当前输入为：{value!r}。") from exc
    if not math.isfinite(number):
        raise ValidationError(f"{name}必须是有限数字，不能为 NaN 或无穷大。")
    if min_value is not None and number < min_value - 1e-12:
        raise ValidationError(f"{name}不能小于 {format_number(min_value)}。")
    if max_value is not None and number > max_value + 1e-12:
        raise ValidationError(f"{name}不能大于 {format_number(max_value)}。")
    return number


def require_nonnegative(value: Any, name: str = "数值") -> float:
    """校验非负数（大于等于 0）。"""
    return require_number(value, name, min_value=0.0)


def require_positive(value: Any, name: str = "数值") -> float:
    """校验严格正数（大于 0）。"""
    number = require_number(value, name)
    if number <= 0:
        raise ValidationError(f"{name}必须大于 0，当前为 {format_number(number)}。")
    return number


def require_int(
    value: Any,
    name: str = "数值",
    *,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> int:
    """校验整数，接受 3、3.0、"3"，拒绝 3.2。"""
    if isinstance(value, bool):
        raise ValidationError(f"{name}必须是整数。")
    number = require_number(value, name)
    if not number.is_integer():
        raise ValidationError(f"{name}必须是整数，当前输入为：{value!r}。")
    result = int(number)
    if min_value is not None and result < min_value:
        raise ValidationError(f"{name}不能小于 {min_value}。")
    if max_value is not None and result > max_value:
        raise ValidationError(f"{name}不能大于 {max_value}。")
    return result


def safe_div(numerator: Any, denominator: Any, name: str = "分母") -> float:
    """安全除法：先校验数值，再防止除数为 0。"""
    num = require_number(numerator, "分子")
    den = require_number(denominator, name)
    if abs(den) < 1e-12:
        raise ValidationError(f"{name}不能为 0，否则分配率/单位成本无意义。")
    return num / den


def allocate_amount(
    total: Any,
    bases: Sequence[Any],
    *,
    labels: Optional[Sequence[str]] = None,
    digits: int = 2,
) -> Tuple[List[float], float]:
    """按分配标准把总额分配到各对象，返回（分配额列表，标准合计）。

    规则：
    - 总额与各分配标准均不得为负；
    - 分配标准合计必须大于 0；
    - 各项先四舍五入到指定小数位，尾差调整到最后一个对象，保证合计等于总额。
    """
    total_value = require_nonnegative(total, "待分配费用总额")
    if not bases:
        raise ValidationError("分配标准不能为空。")
    base_values: List[float] = []
    for index, base in enumerate(bases, start=1):
        label = labels[index - 1] if labels and index - 1 < len(labels) else f"第{index}项"
        base_values.append(require_nonnegative(base, f"{label}的分配标准"))
    total_base = sum(base_values)
    if total_base <= 1e-12:
        raise ValidationError("分配标准合计必须大于 0，请检查产量、工时或定额数据。")

    raw = [total_value * base / total_base for base in base_values]
    rounded = [round(value, digits) for value in raw]
    difference = round(total_value - sum(rounded), digits)
    if rounded:
        rounded[-1] = round(rounded[-1] + difference, digits)
    return rounded, round(total_base, 10)


def equivalent_units(completed_qty: Any, wip_qty: Any, completion: Any) -> float:
    """计算约当产量：完工数量 + 在产品数量 × 完工程度。"""
    completed = require_nonnegative(completed_qty, "完工产品数量")
    wip = require_nonnegative(wip_qty, "在产品数量")
    degree = require_number(completion, "完工程度", min_value=0.0, max_value=1.0)
    result = completed + wip * degree
    if result <= 1e-12:
        raise ValidationError("约当产量必须大于 0，请检查完工数量和在产品数量。")
    return result


def solve_linear_system(matrix: Sequence[Sequence[Any]], vector: Sequence[Any]) -> List[float]:
    """高斯消元法（部分主元）求解线性方程组 Ax=b。

    用于辅助生产费用代数分配法。纯 Python 实现，不依赖 numpy。
    如果方程无唯一解，抛出中文 ValidationError。
    """
    n = len(vector)
    if n == 0:
        raise ValidationError("方程组不能为空。")
    if len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValidationError("方程组系数矩阵必须是 n×n 方阵。")

    # 构造增广矩阵并校验
    a: List[List[float]] = []
    for i, row in enumerate(matrix):
        new_row = [require_number(value, f"系数矩阵第{i + 1}行") for value in row]
        new_row.append(require_number(vector[i], f"常数项第{i + 1}行"))
        a.append(new_row)

    for col in range(n):
        # 选主元，避免除以接近 0 的数
        pivot_row = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot_row][col]) < 1e-12:
            raise ValidationError("方程组不存在唯一解，请检查辅助车间之间的服务量关系。")
        if pivot_row != col:
            a[col], a[pivot_row] = a[pivot_row], a[col]

        pivot = a[col][col]
        for j in range(col, n + 1):
            a[col][j] /= pivot

        for i in range(n):
            if i == col:
                continue
            factor = a[i][col]
            if abs(factor) < 1e-15:
                continue
            for j in range(col, n + 1):
                a[i][j] -= factor * a[col][j]

    return [a[i][n] for i in range(n)]


# ---------------------------------------------------------------------------
# 三、交互输入
# ---------------------------------------------------------------------------
def _default_text(default: Any, digits: int = 2) -> str:
    """把默认值转换为输入提示中的文本。"""
    if isinstance(default, float):
        return f"{default:,.{digits}f}".rstrip("0").rstrip(".")
    return str(default)


def input_text(prompt: str, default: Optional[str] = None) -> str:
    """读取文本；回车使用默认值。"""
    suffix = f" [默认 {default}]" if default is not None else ""
    while True:
        try:
            raw = input(f"{prompt}{suffix}：").strip()
        except EOFError:
            if default is not None:
                return default
            raise ValidationError("当前环境无法读取输入。")
        if raw:
            return raw
        if default is not None:
            return default
        print("  输入不能为空，请重新输入。")


def input_float(
    prompt: str,
    default: Optional[float] = None,
    *,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    allow_zero: bool = True,
    name: str = "数值",
) -> float:
    """读取浮点数；回车使用默认值，非法输入会提示并重新询问。"""
    if not allow_zero:
        if min_value is None or min_value <= 0:
            min_value = 1e-9
    suffix = f" [默认 {_default_text(default)}]" if default is not None else ""
    while True:
        try:
            raw = input(f"{prompt}{suffix}：").strip().replace(",", "")
        except EOFError:
            if default is not None:
                return float(default)
            raise ValidationError("当前环境无法读取输入。")
        if raw == "":
            if default is not None:
                value = float(default)
            else:
                print("  输入不能为空，请重新输入。")
                continue
        else:
            try:
                value = float(raw)
            except ValueError:
                print(f"  输入无效：{raw!r} 不是数字，请重新输入。")
                continue
        try:
            return require_number(value, name, min_value=min_value, max_value=max_value)
        except ValidationError as exc:
            print(f"  {exc} 请重新输入。")



def input_int(
    prompt: str,
    default: Optional[int] = None,
    *,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    name: str = "整数",
) -> int:
    """读取整数；回车使用默认值。"""
    suffix = f" [默认 {default}]" if default is not None else ""
    while True:
        try:
            raw = input(f"{prompt}{suffix}：").strip().replace(",", "")
        except EOFError:
            if default is not None:
                return int(default)
            raise ValidationError("当前环境无法读取输入。")
        if raw == "":
            if default is not None:
                value = default
            else:
                print("  输入不能为空，请重新输入。")
                continue
        else:
            try:
                value = int(raw)
            except ValueError:
                print(f"  输入无效：{raw!r} 不是整数，请重新输入。")
                continue
        try:
            return require_int(value, name, min_value=min_value, max_value=max_value)
        except ValidationError as exc:
            print(f"  {exc} 请重新输入。")


def input_percent(
    prompt: str,
    default_percent: float = 0.0,
    *,
    min_percent: float = 0.0,
    max_percent: float = 100.0,
    name: str = "比例",
) -> float:
    """读取百分数（如输入 14 表示 14%），返回小数 0.14。"""
    suffix = f" [默认 {default_percent:g}%]" if default_percent is not None else ""
    while True:
        try:
            raw = input(f"{prompt}（%）{suffix}：").strip().replace(",", "")
        except EOFError:
            return float(default_percent) / 100.0
        if raw == "":
            if default_percent is not None:
                value = float(default_percent)
            else:
                print("  输入不能为空，请重新输入。")
                continue
        else:
            raw = raw.rstrip("%")
            try:
                value = float(raw)
            except ValueError:
                print(f"  输入无效：{raw!r} 不是百分数，请重新输入。")
                continue
        try:
            require_number(value, name, min_value=min_percent, max_value=max_percent)
            return value / 100.0
        except ValidationError as exc:
            print(f"  {exc} 请重新输入。")


def input_yes_no(prompt: str, default: bool = True) -> bool:
    """读取是/否；回车使用默认值。"""
    suffix = " [默认 Y]" if default else " [默认 N]"
    while True:
        try:
            raw = input(f"{prompt}{suffix}（Y/N）：").strip().lower()
        except EOFError:
            return default
        if raw == "":
            return default
        if raw in ("y", "yes", "是", "1"):
            return True
        if raw in ("n", "no", "否", "0"):
            return False
        print("  请输入 Y 或 N。")


def pause(message: str = "按回车键继续...") -> None:
    """暂停，便于阅读输出；在非交互环境下自动跳过。"""
    try:
        input(f"\n{message}")
    except EOFError:
        return
    except KeyboardInterrupt:
        print("\n已返回。")
        return



# ---------------------------------------------------------------------------
# 四、格式化与中文表格
# ---------------------------------------------------------------------------
def format_number(value: Any, digits: int = 2) -> str:
    """格式化普通数字；无法转换时原样返回。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return str(value)
    if abs(number - round(number)) < 1e-10:
        return f"{int(round(number)):,}"
    return f"{number:,.{digits}f}"


def format_money(value: Any) -> str:
    """金额格式化：保留两位小数并加千分位。"""
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def format_percent(value: Any, digits: int = 2) -> str:
    """小数转百分数文本，如 0.125 -> 12.50%。"""
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return str(value)


def display_width(text: Any) -> int:
    """计算终端显示宽度：中文/全角字符按 2 列计算。"""
    width = 0
    for char in str(text):
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def pad_text(text: Any, width: int, align: str = "left") -> str:
    """按显示宽度补空格。"""
    text = "" if text is None else str(text)
    space = max(width - display_width(text), 0)
    if align == "right":
        return " " * space + text
    if align == "center":
        left = space // 2
        return " " * left + text + " " * (space - left)
    return text + " " * space


def print_heading(title: str, char: str = "=", width: int = 78) -> None:
    """打印居中的标题。"""
    print("\n" + char * width)
    print(pad_text(title, width, "center"))
    print(char * width)


def print_subheading(title: str, char: str = "-", width: int = 78) -> None:
    """打印小节标题。"""
    print(f"\n{char * width}")
    print(title)
    print(char * width)


def print_table(
    headers: Sequence[Any],
    rows: Sequence[Sequence[Any]],
    title: Optional[str] = None,
    *,
    align: Optional[Sequence[str]] = None,
) -> None:
    """打印带边框的中文表格。

    align 可为每列指定 left/right/center；默认第一列左对齐，其余右对齐。
    """
    if title:
        print(f"\n【{title}】")
    headers_text = [str(item) for item in headers]
    body = [["" if cell is None else str(cell) for cell in row] for row in rows]
    if not body:
        print("  （暂无数据）")
        return

    # 统一列数，防止某行列数不足
    col_count = len(headers_text)
    for row in body:
        if len(row) < col_count:
            row.extend([""] * (col_count - len(row)))

    widths = []
    for col in range(col_count):
        widths.append(
            max(
                [display_width(headers_text[col])]
                + [display_width(row[col]) for row in body]
            )
        )

    if align is None:
        align = ["left"] + ["right"] * (col_count - 1)
    aligns = list(align) + ["left"] * max(0, col_count - len(align))

    separator = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    print(separator)
    print(
        "|"
        + "|".join(
            " " + pad_text(headers_text[i], widths[i], "center") + " "
            for i in range(col_count)
        )
        + "|"
    )
    print(separator)
    for row in body:
        print(
            "|"
            + "|".join(
                " " + pad_text(row[i], widths[i], aligns[i]) + " "
                for i in range(col_count)
            )
            + "|"
        )
    print(separator)



def print_steps(steps: Iterable[str], title: str = "分步计算过程") -> None:
    """按序号打印解题步骤。"""
    print_subheading(title)
    for index, step in enumerate(steps, start=1):
        print(f"  （{index}）{step}")


def print_formulas(formulas: Iterable[str], title: str = "公式") -> None:
    """打印公式清单。"""
    print_subheading(title)
    for formula in formulas:
        print(f"  · {formula}")


def print_journal(lines: Iterable[str], title: str = "会计分录") -> None:
    """打印会计分录。"""
    print_subheading(f"{title}（单位：元）")
    lines = list(lines)
    if not lines:
        print("  （本计算无需编制分录）")
        return
    for line in lines:
        print(f"  {line}")


def print_summary(lines: Iterable[str], title: str = "总结") -> None:
    """打印结论与提示。"""
    print_subheading(title)
    for line in lines:
        print(f"  {line}")


def print_disclaimer() -> None:
    """打印项目性质说明。"""
    print("  说明：本项目为学生自主开发的学习工具，仅用于成本会计课程学习与习题验算，")
    print("        不是出版社官方配套软件；案例均为自行设计的模拟教学案例。")


# ---------------------------------------------------------------------------
# 五、菜单与异常兜底
# ---------------------------------------------------------------------------
MenuFunction = Callable[[], None]


def run_menu(
    title: str,
    options: Sequence[Tuple[str, str, MenuFunction]],
    *,
    back_text: str = "返回上一级菜单",
) -> None:
    """运行章节子菜单。

    options 为 (编号, 名称, 函数) 序列。函数运行中出现的参数错误、除零错误等
    会在此统一转换为中文提示，保证程序不会闪退。
    """
    mapping = {key: (label, func) for key, label, func in options}
    while True:
        print_heading(title, "-")
        for key, label, _ in options:
            print(f"  {key}. {label}")
        print(f"  0. {back_text}")
        try:
            choice = input("请选择功能编号：").strip()
        except EOFError:
            return
        except KeyboardInterrupt:
            print("\n已取消选择。")
            continue

        if choice in ("0", "q", "Q", ""):
            return
        if choice not in mapping:
            print("  无效编号，请输入菜单中存在的数字。")
            continue

        label, func = mapping[choice]
        print(f"\n>>> 正在运行：{label}")
        try:
            func()
        except ValidationError as exc:
            print(f"\n[输入提示] {exc}")
        except ZeroDivisionError:
            print("\n[计算提示] 出现除数为 0 的情况，请检查数量、工时或分配标准是否为零。")
        except KeyboardInterrupt:
            print("\n[操作提示] 已取消当前计算，返回菜单。")
        except Exception as exc:  # 兜底，避免任何意外异常导致程序闪退
            print(f"\n[程序提示] 计算过程中出现问题：{exc}")
            if os.environ.get("COST_DEBUG") == "1":
                import traceback

                traceback.print_exc()
            print("  请检查输入数据；若问题持续存在，可设置环境变量 COST_DEBUG=1 查看详细错误。")
        pause("按回车键返回菜单...")

