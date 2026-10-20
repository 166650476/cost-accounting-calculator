"""成本会计学 Python 综合计算器——程序入口。

运行方式：
    python main.py

功能：
- 按课程教学大纲章节顺序组织菜单；
- 覆盖要素费用、辅助生产费用、制造费用、生产损失、完工与在产品分配、
  品种法、分批法、分步法、辅助方法、成本报表与分析；
- 每次计算输出题意、公式、分步过程、表格、会计分录、总结，并保存 CSV；
- 成本结构图、对比图等自动保存到 chart 文件夹。

本项目为学生自主开发的学习工具，仅用于成本会计课程学习与习题验算，
不是出版社官方配套软件；案例均为自行设计的模拟教学案例。
"""

from __future__ import annotations

import csv
import platform
from typing import List, Tuple

import chapter1_intro
import chapter2_element_cost
import chapter3_auxiliary_cost
import chapter4_factory_cost_loss
import chapter5_wip_allocation
import chapter6_variety_method
import chapter7_batch_method
import chapter8_step_method
import chapter9_special_method
import chapter10_cost_analysis
import export
import visual
from utils import (
    BASE_DIR,
    CHART_DIR,
    OUTPUT_DIR,
    print_disclaimer,
    print_heading,
    pause,
)


APP_VERSION = "1.0.0"

MODULES: List[Tuple[str, str, object]] = [
    ("1", "第一章 成本会计总论", chapter1_intro.run),
    ("2", "第二章 工业企业要素费用的归集与分配", chapter2_element_cost.run),
    ("3", "第三章 辅助生产费用的归集与分配", chapter3_auxiliary_cost.run),
    ("4", "第四章 制造费用、生产损失与期间费用核算", chapter4_factory_cost_loss.run),
    ("5", "第五章 生产费用在完工产品与在产品之间分配", chapter5_wip_allocation.run),
    ("6", "第六章 产品成本计算——品种法", chapter6_variety_method.run),
    ("7", "第七章 产品成本计算——分批法", chapter7_batch_method.run),
    ("8", "第八章 产品成本计算——分步法", chapter8_step_method.run),
    ("9", "第九章 产品成本计算辅助方法", chapter9_special_method.run),
    ("10", "第十章 成本报表编制与成本分析", chapter10_cost_analysis.run),
]


def show_welcome() -> None:
    """显示欢迎页、使用提示和免责声明。"""
    print_heading("成本会计学 Python 综合计算器", "=")
    print("  参考教材：《成本会计学》第10版（于富生、黎来芳、张敏主编）")
    print("  适用课程：会计专业《成本会计学》课程学习、课后习题验算、课程大作业")
    print("  覆盖章节：第一章至第十章，全部核心计算题型")
    print("\n  使用提示：")
    print("    1. 菜单按课程教学大纲章节顺序排列，输入编号进入对应章节；")
    print("    2. 所有输入均可用“回车”采用方括号中的默认教学案例数据；")
    print("    3. 比率按百分数输入，例如 14 表示 14%；")
    print("    4. 每次计算自动保存 CSV 到 output 文件夹，图表保存到 chart 文件夹；")
    print("    5. 输入 0 返回上一级菜单，Ctrl+C 可安全取消当前操作；")
    print("    6. 负数、零分母、非法字符等均有中文提示，程序不会闪退。")
    print_disclaimer()


def show_main_menu() -> None:
    """显示主菜单。"""
    print_heading("主菜单", "-")
    for key, name, _ in MODULES:
        print(f"  {key:>2}. {name}")
    print("  11. 查看输出文件与运行环境")
    print("  12. 使用说明与公式索引")
    print("   0. 退出程序")


def show_runtime_info() -> None:
    """显示项目路径、输出文件数量、图片数量和运行环境。"""
    print_heading("输出文件与运行环境", "-")
    print(f"  项目目录：{BASE_DIR}")
    print(f"  输出目录：{OUTPUT_DIR}")
    print(f"  图表目录：{CHART_DIR}")
    print(f"  程序版本：{APP_VERSION}")
    print(f"  Python：{platform.python_version()}")
    print(f"  操作系统：{platform.platform()}")
    print(f"  中文字体：{visual.CHINESE_FONT}")
    csv_files = sorted(OUTPUT_DIR.glob("*.csv"))
    chart_files = sorted(CHART_DIR.glob("*.png"))
    print(f"  已生成 CSV：{len(csv_files)} 个")
    print(f"  已生成图表：{len(chart_files)} 张")
    if export.get_summary_path().exists():
        try:
            with export.get_summary_path().open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle))
            print(f"  计算记录汇总：{max(len(rows) - 1, 0)} 条")
        except Exception as exc:
            print(f"  汇总文件读取失败：{exc}")
    if chart_files:
        print("  最近图表：")
        for path in chart_files[-5:]:
            print(f"    - {path.name}")


def show_help() -> None:
    """显示使用说明与公式索引。"""
    print_heading("使用说明与公式索引", "-")
    print("  一、输入说明")
    print("    · 所有金额单位为元，数量单位按题目口径输入；")
    print("    · 百分比直接输入数字（如 14 表示 14%）；")
    print("    · 直接按回车可使用默认教学案例数据；")
    print("    · 输入 0 返回上一级菜单。")
    print("\n  二、核心公式索引")
    print("    要素费用：分配率 = 待分配费用 ÷ 分配标准合计；")
    print("    辅助生产：直接分配、一次交互、计划成本、代数分配；")
    print("    制造费用：生产工时/工资/机器工时/年度计划分配率；")
    print("    完工与在产品：约当产量、定额成本、定额比例等六种方法；")
    print("    品种法：按产品归集，约当产量分配完工与在产品；")
    print("    分批法：按批别归集，普通分批法与简化分批法；")
    print("    分步法：综合结转+成本还原、分项结转、平行结转；")
    print("    辅助方法：分类法、联产品/副产品、定额法；")
    print("    成本分析：可比产品降低额/降低率三因素分析、单位成本量价分析。")
    print("\n  三、输出说明")
    print("    · output：每次计算的完整 CSV 记录及“计算记录汇总.csv”；")
    print("    · chart：成本结构饼图、结构分析图、差异对比图；")
    print("    · CSV 使用 utf-8-sig 编码，Excel 双击打开不会乱码。")


def main() -> None:
    """主程序循环。"""
    show_welcome()
    while True:
        show_main_menu()
        try:
            choice = input("请选择功能编号：").strip()
        except EOFError:
            print("\n未检测到输入，程序结束。")
            break
        except KeyboardInterrupt:
            print("\n已取消输入，程序结束。")
            break

        if choice in ("0", "q", "Q"):
            print("\n感谢使用成本会计学综合计算器，再见！")
            break
        if choice == "11":
            try:
                show_runtime_info()
            except Exception as exc:
                print(f"\n[提示] 读取运行信息时出现问题：{exc}")
            pause("按回车键返回主菜单...")
            continue
        if choice == "12":
            show_help()
            pause("按回车键返回主菜单...")
            continue

        selected = next((item for item in MODULES if item[0] == choice), None)
        if selected is None:
            print("  无效编号，请输入主菜单中存在的数字。")
            continue

        _, name, func = selected
        print(f"\n>>> 正在进入：{name}")
        try:
            func()  # type: ignore[operator]
        except KeyboardInterrupt:
            print("\n[操作提示] 已取消当前章节，返回主菜单。")
        except Exception as exc:
            print(f"\n[程序提示] 章节运行过程中出现问题：{exc}")
            print("  已返回主菜单；可设置环境变量 COST_DEBUG=1 查看详细错误信息。")
        pause("按回车键返回主菜单...")


if __name__ == "__main__":
    main()
