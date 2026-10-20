"""第五章 生产费用在完工产品与在产品之间的分配。

完整实现六种方法：
1. 不计算在产品成本法；
2. 在产品按固定成本计价法；
3. 在产品按原材料费用计价法；
4. 约当产量比例法（原材料一次投入/陆续投入，加工费按完工程度）；
5. 在产品按定额成本计价法；
6. 定额比例法（材料定额和工时定额双标准分配）。

每一种方法均自动生成“产品成本计算单”，列示费用总额、完工产品成本、
期末在产品成本、单位完工成本，并输出分录和总结。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import export
from utils import (
    ValidationError,
    equivalent_units,
    format_money,
    format_percent,
    input_float,
    input_int,
    input_percent,
    input_text,
    print_heading,
    print_journal,
    print_steps,
    print_subheading,
    print_summary,
    print_table,
    require_nonnegative,
    require_positive,
    run_menu,
    safe_div,
)


COST_SHEET_HEADERS = ["成本项目", "费用总额（元）", "完工产品成本（元）", "期末在产品成本（元）", "单位完工成本（元/件）"]


def build_cost_sheet(
    material_total: Any,
    labor_total: Any,
    overhead_total: Any,
    completed_material: Any,
    completed_labor: Any,
    completed_overhead: Any,
    completed_qty: Any,
    product: str = "甲产品",
) -> Dict[str, Any]:
    """构造标准产品成本计算单。

    只负责把已经分配好的完工/在产品成本整理成表，并做金额平衡校验。
    """
    totals = [
        require_nonnegative(material_total, "直接材料总额"),
        require_nonnegative(labor_total, "直接人工总额"),
        require_nonnegative(overhead_total, "制造费用总额"),
    ]
    completed = [
        require_nonnegative(completed_material, "完工产品直接材料"),
        require_nonnegative(completed_labor, "完工产品直接人工"),
        require_nonnegative(completed_overhead, "完工产品制造费用"),
    ]
    qty = require_positive(completed_qty, "完工产品数量")
    wip = [round(totals[i] - completed[i], 2) for i in range(3)]
    if any(value < -0.01 for value in wip):
        raise ValidationError("完工产品成本不能大于费用总额，请检查分配标准或定额数据。")
    wip = [max(value, 0.0) for value in wip]
    total_cost = round(sum(totals), 2)
    completed_total = round(sum(completed), 2)
    wip_total = round(total_cost - completed_total, 2)
    unit_cost = round(completed_total / qty, 6)
    names = ["直接材料", "直接人工", "制造费用"]
    rows = []
    for i, name in enumerate(names):
        rows.append([
            name, format_money(totals[i]), format_money(completed[i]), format_money(wip[i]),
            format_money(round(completed[i] / qty, 6)),
        ])
    rows.append(["合计", format_money(total_cost), format_money(completed_total), format_money(wip_total), format_money(unit_cost)])
    return {
        "product": product,
        "totals": totals,
        "completed": completed,
        "wip": wip,
        "total_cost": total_cost,
        "completed_total": completed_total,
        "wip_total": wip_total,
        "completed_qty": qty,
        "unit_cost": unit_cost,
        "rows": rows,
    }


def finished_goods_journal(sheet: Dict[str, Any]) -> List[str]:
    """完工产品入库分录。"""
    return [
        f"借：库存商品——{sheet['product']}     {format_money(sheet['completed_total'])}",
        f"贷：生产成本——基本生产成本（{sheet['product']}）     {format_money(sheet['completed_total'])}",
    ]


def _finish(
    title: str,
    question: str,
    formulas: Sequence[str],
    steps: Sequence[str],
    sheet: Dict[str, Any],
    journal: Sequence[str],
    summary: Sequence[str],
    *,
    extra_tables: Optional[Sequence[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]]] = None,
    conclusion: Optional[str] = None,
) -> None:
    """统一输出并保存第五章计算结果。"""
    print_subheading("一、文字题意")
    print(f"  {question}")
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")
    print_steps(steps)
    print_table(COST_SHEET_HEADERS, sheet["rows"], "产品成本计算单")
    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = [("产品成本计算单", COST_SHEET_HEADERS, sheet["rows"])]
    if extra_tables:
        for table_title, headers, rows in extra_tables:
            print_table(headers, rows, table_title)
            tables.append((table_title, headers, rows))
    print_journal(journal)
    print_summary(summary)
    export.save_calculation(
        "第五章 完工产品与在产品分配",
        title,
        question=question,
        formulas=formulas,
        steps=steps,
        tables=tables,
        journal=journal,
        summary=summary,
        conclusion=conclusion or f"完工产品成本 {format_money(sheet['completed_total'])} 元，期末在产品成本 {format_money(sheet['wip_total'])} 元。",
    )


def method_no_wip(material: float, labor: float, overhead: float, completed_qty: float) -> Dict[str, Any]:
    """不计算在产品成本法：全部生产费用由完工产品负担。"""
    return build_cost_sheet(material, labor, overhead, material, labor, overhead, completed_qty)


def method_fixed_wip(
    material: float,
    labor: float,
    overhead: float,
    fixed_wip: Dict[str, Any],
    completed_qty: float,
) -> Dict[str, Any]:
    """在产品按固定成本计价法。"""
    fixed_material = require_nonnegative(fixed_wip.get("material"), "固定在产品材料成本")
    fixed_labor = require_nonnegative(fixed_wip.get("labor"), "固定在产品人工成本")
    fixed_overhead = require_nonnegative(fixed_wip.get("overhead"), "固定在产品制造费用")
    completed_material = material - fixed_material
    completed_labor = labor - fixed_labor
    completed_overhead = overhead - fixed_overhead
    if min(completed_material, completed_labor, completed_overhead) < -0.01:
        raise ValidationError("固定在产品成本不能大于对应费用总额，请调低固定成本。")
    return build_cost_sheet(material, labor, overhead, completed_material, completed_labor, completed_overhead, completed_qty)


def method_material_only(
    material: float,
    labor: float,
    overhead: float,
    completed_qty: float,
    wip_qty: float,
) -> Dict[str, Any]:
    """在产品按原材料费用计价法。

    原材料费用按完工产品和在产品数量比例分配；加工费用全部由完工产品负担。
    """
    completed = require_positive(completed_qty, "完工产品数量")
    wip = require_nonnegative(wip_qty, "在产品数量")
    base = completed + wip
    if base <= 0:
        raise ValidationError("完工产品数量与在产品数量合计必须大于 0。")
    material_wip = round(material * wip / base, 2)
    material_completed = round(material - material_wip, 2)
    return build_cost_sheet(material, labor, overhead, material_completed, labor, overhead, completed)


def method_equivalent(
    material: float,
    labor: float,
    overhead: float,
    completed_qty: float,
    wip_qty: float,
    material_completion: float,
    processing_completion: float,
) -> Dict[str, Any]:
    """约当产量比例法。

    材料约当产量 = 完工数量 + 在产品数量 × 材料投料程度；
    加工费约当产量 = 完工数量 + 在产品数量 × 加工完工程度。
    """
    completed = require_positive(completed_qty, "完工产品数量")
    wip = require_nonnegative(wip_qty, "在产品数量")
    material_degree = require_nonnegative(material_completion, "材料投料程度")
    processing_degree = require_nonnegative(processing_completion, "加工完工程度")
    if material_degree > 1 or processing_degree > 1:
        raise ValidationError("投料程度和完工程度必须在 0%～100% 之间。")
    material_eq = equivalent_units(completed, wip, material_degree)
    processing_eq = equivalent_units(completed, wip, processing_degree)
    material_rate = safe_div(material, material_eq, "材料费用分配率")
    labor_rate = safe_div(labor, processing_eq, "人工费用分配率")
    overhead_rate = safe_div(overhead, processing_eq, "制造费用分配率")
    completed_material = round(material_rate * completed, 2)
    completed_labor = round(labor_rate * completed, 2)
    completed_overhead = round(overhead_rate * completed, 2)
    sheet = build_cost_sheet(material, labor, overhead, completed_material, completed_labor, completed_overhead, completed)
    return {
        "sheet": sheet,
        "material_eq": material_eq,
        "processing_eq": processing_eq,
        "material_rate": material_rate,
        "labor_rate": labor_rate,
        "overhead_rate": overhead_rate,
    }


def method_quota_wip(
    material: float,
    labor: float,
    overhead: float,
    wip_qty: float,
    unit_quota: Dict[str, Any],
    completed_qty: float,
) -> Dict[str, Any]:
    """在产品按定额成本计价法。"""
    wip = require_nonnegative(wip_qty, "在产品数量")
    unit_material = require_nonnegative(unit_quota.get("material"), "单位在产品材料定额")
    unit_labor = require_nonnegative(unit_quota.get("labor"), "单位在产品人工定额")
    unit_overhead = require_nonnegative(unit_quota.get("overhead"), "单位在产品制造费用定额")
    wip_material = round(wip * unit_material, 2)
    wip_labor = round(wip * unit_labor, 2)
    wip_overhead = round(wip * unit_overhead, 2)
    if wip_material > material + 0.01 or wip_labor > labor + 0.01 or wip_overhead > overhead + 0.01:
        raise ValidationError("在产品定额成本不能大于对应费用总额，请检查定额数据。")
    return build_cost_sheet(
        material, labor, overhead,
        material - wip_material, labor - wip_labor, overhead - wip_overhead,
        completed_qty,
    )


def method_quota_ratio(
    material: float,
    labor: float,
    overhead: float,
    completed_material_quota: float,
    wip_material_quota: float,
    completed_hours_quota: float,
    wip_hours_quota: float,
    completed_qty: float,
) -> Dict[str, Any]:
    """定额比例法：材料按材料定额比例，加工费按工时定额比例分配。"""
    material_base = require_nonnegative(completed_material_quota, "完工产品材料定额") + require_nonnegative(wip_material_quota, "在产品材料定额")
    hours_base = require_nonnegative(completed_hours_quota, "完工产品工时定额") + require_nonnegative(wip_hours_quota, "在产品工时定额")
    if material_base <= 0 or hours_base <= 0:
        raise ValidationError("材料定额合计和工时定额合计都必须大于 0。")
    material_rate = safe_div(material, material_base, "材料定额分配率")
    labor_rate = safe_div(labor, hours_base, "人工定额分配率")
    overhead_rate = safe_div(overhead, hours_base, "制造费用定额分配率")
    completed_material = round(material_rate * completed_material_quota, 2)
    completed_labor = round(labor_rate * completed_hours_quota, 2)
    completed_overhead = round(overhead_rate * completed_hours_quota, 2)
    sheet = build_cost_sheet(material, labor, overhead, completed_material, completed_labor, completed_overhead, completed_qty)
    return {
        "sheet": sheet,
        "material_base": material_base,
        "hours_base": hours_base,
        "material_rate": material_rate,
        "labor_rate": labor_rate,
        "overhead_rate": overhead_rate,
    }



def run_no_wip() -> None:
    """不计算在产品成本法。"""
    print_heading("第五章 完工产品与在产品分配：不计算在产品成本法", "-")
    product = input_text("产品名称", "甲产品")
    completed_qty = input_float("完工产品数量", 800.0, min_value=0.0, name="完工产品数量")
    material = input_float("直接材料总额（元）", 50000.0, min_value=0.0, name="直接材料")
    labor = input_float("直接人工总额（元）", 18000.0, min_value=0.0, name="直接人工")
    overhead = input_float("制造费用总额（元）", 9000.0, min_value=0.0, name="制造费用")
    sheet = method_no_wip(material, labor, overhead, completed_qty)
    question = (
        f"某企业生产{product}，本月完工 {completed_qty:,.2f} 件，月末在产品数量很少且成本稳定，"
        "采用不计算在产品成本法。本月直接材料、直接人工、制造费用分别为 "
        f"{format_money(material)}、{format_money(labor)}、{format_money(overhead)} 元。"
        "要求计算完工产品总成本和单位成本。"
    )
    formulas = [
        "完工产品总成本 = 本月生产费用总额",
        "单位完工产品成本 = 完工产品总成本 ÷ 完工产品数量",
        "月末在产品成本 = 0",
    ]
    steps = [
        f"生产费用总额 = {format_money(material)} + {format_money(labor)} + {format_money(overhead)} = {format_money(sheet['total_cost'])} 元。",
        "月末在产品成本 = 0，全部由完工产品负担。",
        f"单位完工成本 = {format_money(sheet['completed_total'])} ÷ {completed_qty:,.2f} = {format_money(sheet['unit_cost'])} 元/件。",
    ]
    summary = [
        "不计算在产品成本法适用于月末在产品数量很少、价值较低，或各月在产品数量基本稳定的情况。",
        "该方法计算简便，但会把全部生产费用计入完工产品，可能高估完工产品成本。",
    ]
    _finish("不计算在产品成本法", question, formulas, steps, sheet, finished_goods_journal(sheet), summary)


def run_fixed_wip() -> None:
    """在产品按固定成本计价法。"""
    print_heading("第五章 完工产品与在产品分配：在产品按固定成本计价法", "-")
    product = input_text("产品名称", "甲产品")
    completed_qty = input_float("完工产品数量", 800.0, min_value=0.0, name="完工产品数量")
    wip_qty = input_float("月末在产品数量", 200.0, min_value=0.0, name="在产品数量")
    material = input_float("直接材料总额（元）", 50000.0, min_value=0.0, name="直接材料")
    labor = input_float("直接人工总额（元）", 18000.0, min_value=0.0, name="直接人工")
    overhead = input_float("制造费用总额（元）", 9000.0, min_value=0.0, name="制造费用")
    print("  请选择固定的月末在产品成本（各月保持不变）：")
    fixed_material = input_float("固定在产品成本——直接材料（元）", 10000.0, min_value=0.0, name="固定材料成本")
    fixed_labor = input_float("固定在产品成本——直接人工（元）", 2000.0, min_value=0.0, name="固定人工成本")
    fixed_overhead = input_float("固定在产品成本——制造费用（元）", 1000.0, min_value=0.0, name="固定制造费用")
    sheet = method_fixed_wip(material, labor, overhead, {"material": fixed_material, "labor": fixed_labor, "overhead": fixed_overhead}, completed_qty)
    question = (
        f"某企业生产{product}，本月完工 {completed_qty:,.2f} 件，月末在产品 {wip_qty:,.2f} 件。"
        f"采用在产品按固定成本计价法，固定在产品成本为材料 {format_money(fixed_material)} 元、"
        f"人工 {format_money(fixed_labor)} 元、制造费用 {format_money(fixed_overhead)} 元。"
        "本月生产费用合计见计算单，要求计算完工产品成本。"
    )
    formulas = [
        "月末在产品成本 = 固定的材料成本 + 固定的人工成本 + 固定的制造费用",
        "完工产品成本 = 本月生产费用总额 - 月末在产品固定成本",
        "单位完工成本 = 完工产品成本 ÷ 完工产品数量",
    ]
    steps = [
        f"固定在产品成本合计 = {format_money(fixed_material)} + {format_money(fixed_labor)} + {format_money(fixed_overhead)} = {format_money(sheet['wip_total'])} 元。",
        f"完工产品直接材料 = {format_money(material)} - {format_money(fixed_material)} = {format_money(sheet['completed'][0])} 元。",
        f"完工产品直接人工 = {format_money(labor)} - {format_money(fixed_labor)} = {format_money(sheet['completed'][1])} 元。",
        f"完工产品制造费用 = {format_money(overhead)} - {format_money(fixed_overhead)} = {format_money(sheet['completed'][2])} 元。",
        f"完工产品总成本 = {format_money(sheet['completed_total'])} 元，单位成本 = {format_money(sheet['unit_cost'])} 元/件。",
    ]
    summary = [
        "在产品按固定成本计价法适用于各月末在产品数量较少，或数量虽多但各月变化不大的情况。",
        "固定成本应按上年末或年初在产品成本确定；若各月在产品数量变化较大，不宜采用本方法。",
    ]
    _finish("在产品按固定成本计价法", question, formulas, steps, sheet, finished_goods_journal(sheet), summary)



def run_material_only() -> None:
    """在产品按原材料费用计价法。"""
    print_heading("第五章 完工产品与在产品分配：在产品按原材料费用计价法", "-")
    product = input_text("产品名称", "甲产品")
    completed_qty = input_float("完工产品数量", 800.0, min_value=0.0, name="完工产品数量")
    wip_qty = input_float("月末在产品数量", 200.0, min_value=0.0, name="在产品数量")
    material = input_float("直接材料总额（元）", 50000.0, min_value=0.0, name="直接材料")
    labor = input_float("直接人工总额（元）", 18000.0, min_value=0.0, name="直接人工")
    overhead = input_float("制造费用总额（元）", 9000.0, min_value=0.0, name="制造费用")
    sheet = method_material_only(material, labor, overhead, completed_qty, wip_qty)
    question = (
        f"某企业生产{product}，本月完工 {completed_qty:,.2f} 件，月末在产品 {wip_qty:,.2f} 件。"
        "原材料在生产开始时一次投入，采用在产品按原材料费用计价法。"
        f"本月直接材料 {format_money(material)} 元、直接人工 {format_money(labor)} 元、制造费用 {format_money(overhead)} 元。"
        "要求计算完工产品成本和在产品成本。"
    )
    formulas = [
        "材料费用分配率 = 直接材料总额 ÷（完工产品数量 + 在产品数量）",
        "在产品材料成本 = 在产品数量 × 材料费用分配率",
        "完工产品材料成本 = 直接材料总额 - 在产品材料成本",
        "加工费用全部由完工产品负担，在产品不负担人工和制造费用。",
    ]
    steps = [
        f"材料费用分配率 = {format_money(material)} ÷（{completed_qty:,.2f} + {wip_qty:,.2f}）= {material / (completed_qty + wip_qty):.6f} 元/件。",
        f"在产品材料成本 = {wip_qty:,.2f} × {material / (completed_qty + wip_qty):.6f} = {format_money(sheet['wip'][0])} 元。",
        f"完工产品材料成本 = {format_money(material)} - {format_money(sheet['wip'][0])} = {format_money(sheet['completed'][0])} 元。",
        f"完工产品人工和制造费用分别为 {format_money(labor)} 元、{format_money(overhead)} 元，全部由完工产品负担。",
        f"完工产品总成本 = {format_money(sheet['completed_total'])} 元，单位成本 = {format_money(sheet['unit_cost'])} 元/件。",
    ]
    summary = [
        "在产品按原材料费用计价法适用于原材料费用在产品成本中占很大比重，且原材料在生产开始时一次投入的企业。",
        "该方法下，在产品只负担材料费用，不负担加工费用。",
    ]
    _finish("在产品按原材料费用计价法", question, formulas, steps, sheet, finished_goods_journal(sheet), summary)



def run_equivalent() -> None:
    """约当产量比例法。"""
    print_heading("第五章 完工产品与在产品分配：约当产量比例法", "-")
    product = input_text("产品名称", "甲产品")
    completed_qty = input_float("完工产品数量", 800.0, min_value=0.0, name="完工产品数量")
    wip_qty = input_float("月末在产品数量", 200.0, min_value=0.0, name="在产品数量")
    material = input_float("直接材料总额（元）", 50000.0, min_value=0.0, name="直接材料")
    labor = input_float("直接人工总额（元）", 18000.0, min_value=0.0, name="直接人工")
    overhead = input_float("制造费用总额（元）", 9000.0, min_value=0.0, name="制造费用")
    print("  原材料投入方式：1 生产开始时一次投入（在产品投料程度 100%）；2 陆续投入（按给定投料程度）")
    material_mode = input_int("请选择原材料投入方式", 1, min_value=1, max_value=2, name="投料方式")
    if material_mode == 1:
        material_completion = 1.0
        print("  原材料一次投入：在产品材料投料程度按 100% 计算。")
    else:
        material_completion = input_percent("在产品材料投料程度", 60.0, min_percent=0.0, max_percent=100.0)
    processing_completion = input_percent("在产品加工完工程度（人工和制造费用共用）", 50.0, min_percent=0.0, max_percent=100.0)

    result = method_equivalent(
        material, labor, overhead, completed_qty, wip_qty, material_completion, processing_completion
    )
    sheet = result["sheet"]
    question = (
        f"某企业生产{product}，本月完工 {completed_qty:,.2f} 件，月末在产品 {wip_qty:,.2f} 件。"
        f"原材料{'在生产开始时一次投入' if material_mode == 1 else f'陆续投入，投料程度为 {format_percent(material_completion)}'}，"
        f"在产品加工完工程度为 {format_percent(processing_completion)}。本月直接材料 {format_money(material)} 元、"
        f"直接人工 {format_money(labor)} 元、制造费用 {format_money(overhead)} 元。要求用约当产量比例法计算完工产品和在产品成本。"
    )
    formulas = [
        "材料约当产量 = 完工产品数量 + 在产品数量 × 材料投料程度",
        "加工费约当产量 = 完工产品数量 + 在产品数量 × 加工完工程度",
        "某项费用分配率 = 该项费用总额 ÷ 该项约当产量",
        "完工产品某项成本 = 完工产品数量 × 该项费用分配率",
        "在产品某项成本 = 该项费用总额 - 完工产品该项成本",
    ]
    steps = [
        f"材料约当产量 = {completed_qty:,.2f} + {wip_qty:,.2f} × {format_percent(material_completion)} = {result['material_eq']:,.2f} 件。",
        f"加工费约当产量 = {completed_qty:,.2f} + {wip_qty:,.2f} × {format_percent(processing_completion)} = {result['processing_eq']:,.2f} 件。",
        f"材料费用分配率 = {format_money(material)} ÷ {result['material_eq']:,.2f} = {result['material_rate']:.6f} 元/件。",
        f"人工费用分配率 = {format_money(labor)} ÷ {result['processing_eq']:,.2f} = {result['labor_rate']:.6f} 元/件。",
        f"制造费用分配率 = {format_money(overhead)} ÷ {result['processing_eq']:,.2f} = {result['overhead_rate']:.6f} 元/件。",
        f"完工产品总成本 = {format_money(sheet['completed_total'])} 元；期末在产品成本 = {format_money(sheet['wip_total'])} 元；单位成本 = {format_money(sheet['unit_cost'])} 元/件。",
    ]
    extra_headers = ["成本项目", "费用总额（元）", "约当产量", "分配率", "完工产品成本（元）", "期末在产品成本（元）"]
    extra_rows = [
        ["直接材料", format_money(material), f"{result['material_eq']:,.2f}", f"{result['material_rate']:.6f}", format_money(sheet['completed'][0]), format_money(sheet['wip'][0])],
        ["直接人工", format_money(labor), f"{result['processing_eq']:,.2f}", f"{result['labor_rate']:.6f}", format_money(sheet['completed'][1]), format_money(sheet['wip'][1])],
        ["制造费用", format_money(overhead), f"{result['processing_eq']:,.2f}", f"{result['overhead_rate']:.6f}", format_money(sheet['completed'][2]), format_money(sheet['wip'][2])],
        ["合计", format_money(sheet['total_cost']), "—", "—", format_money(sheet['completed_total']), format_money(sheet['wip_total'])],
    ]
    summary = [
        "约当产量比例法下，材料按投料程度折算，加工费按完工程度折算。",
        f"完工产品成本 {format_money(sheet['completed_total'])} 元，期末在产品成本 {format_money(sheet['wip_total'])} 元。",
        "核对提示：如果原材料在生产开始时一次投入，在产品的材料投料程度应为 100%，不能与加工完工程度混用。",
    ]
    _finish(
        "约当产量比例法", question, formulas, steps, sheet, finished_goods_journal(sheet), summary,
        extra_tables=[("约当产量与费用分配表", extra_headers, extra_rows)],
    )



def run_quota_wip() -> None:
    """在产品按定额成本计价法。"""
    print_heading("第五章 完工产品与在产品分配：在产品按定额成本计价法", "-")
    product = input_text("产品名称", "甲产品")
    completed_qty = input_float("完工产品数量", 800.0, min_value=0.0, name="完工产品数量")
    wip_qty = input_float("月末在产品数量", 200.0, min_value=0.0, name="在产品数量")
    material = input_float("直接材料总额（元）", 50000.0, min_value=0.0, name="直接材料")
    labor = input_float("直接人工总额（元）", 18000.0, min_value=0.0, name="直接人工")
    overhead = input_float("制造费用总额（元）", 9000.0, min_value=0.0, name="制造费用")
    unit_material = input_float("单位在产品材料定额成本（元/件）", 50.0, min_value=0.0, name="材料定额")
    unit_labor = input_float("单位在产品人工定额成本（元/件）", 10.0, min_value=0.0, name="人工定额")
    unit_overhead = input_float("单位在产品制造费用定额成本（元/件）", 5.0, min_value=0.0, name="制造费用定额")
    sheet = method_quota_wip(
        material, labor, overhead, wip_qty,
        {"material": unit_material, "labor": unit_labor, "overhead": unit_overhead}, completed_qty,
    )
    question = (
        f"某企业生产{product}，本月完工 {completed_qty:,.2f} 件，月末在产品 {wip_qty:,.2f} 件。"
        "采用在产品按定额成本计价法，单位在产品材料、人工、制造费用定额分别为 "
        f"{format_money(unit_material)}、{format_money(unit_labor)}、{format_money(unit_overhead)} 元。"
        f"本月费用总额见计算单，要求计算月末在产品定额成本和完工产品成本。"
    )
    formulas = [
        "月末在产品材料定额成本 = 在产品数量 × 单位材料定额成本",
        "月末在产品人工定额成本 = 在产品数量 × 单位人工定额成本",
        "月末在产品制造费用定额成本 = 在产品数量 × 单位制造费用定额成本",
        "完工产品成本 = 费用总额 - 月末在产品定额成本",
    ]
    steps = [
        f"在产品材料定额成本 = {wip_qty:,.2f} × {format_money(unit_material)} = {format_money(sheet['wip'][0])} 元。",
        f"在产品人工定额成本 = {wip_qty:,.2f} × {format_money(unit_labor)} = {format_money(sheet['wip'][1])} 元。",
        f"在产品制造费用定额成本 = {wip_qty:,.2f} × {format_money(unit_overhead)} = {format_money(sheet['wip'][2])} 元。",
        f"月末在产品定额成本合计 = {format_money(sheet['wip_total'])} 元。",
        f"完工产品成本 = 费用总额 {format_money(sheet['total_cost'])} - {format_money(sheet['wip_total'])} = {format_money(sheet['completed_total'])} 元。",
        f"单位完工成本 = {format_money(sheet['unit_cost'])} 元/件。",
    ]
    summary = [
        "在产品按定额成本计价法适用于定额管理基础较好、各项消耗定额比较准确稳定的企业。",
        "月末在产品按定额成本计价，实际成本与定额成本的差异全部由完工产品负担。",
    ]
    _finish("在产品按定额成本计价法", question, formulas, steps, sheet, finished_goods_journal(sheet), summary)



def run_quota_ratio() -> None:
    """定额比例法。"""
    print_heading("第五章 完工产品与在产品分配：定额比例法", "-")
    product = input_text("产品名称", "甲产品")
    completed_qty = input_float("完工产品数量", 600.0, min_value=0.0, name="完工产品数量")
    wip_qty = input_float("月末在产品数量", 200.0, min_value=0.0, name="在产品数量")
    material = input_float("直接材料总额（元）", 60000.0, min_value=0.0, name="直接材料")
    labor = input_float("直接人工总额（元）", 20000.0, min_value=0.0, name="直接人工")
    overhead = input_float("制造费用总额（元）", 10000.0, min_value=0.0, name="制造费用")
    unit_material_quota = input_float("单位产品材料定额（元/件）", 80.0, min_value=0.0, name="材料定额")
    material_completion = input_percent("在产品材料投料程度", 100.0, min_percent=0.0, max_percent=100.0)
    unit_hour_quota = input_float("单位产品工时定额（小时/件）", 15.0, min_value=0.0, name="工时定额")
    processing_completion = input_percent("在产品加工完工程度", 40.0, min_percent=0.0, max_percent=100.0)

    completed_material_quota = round(completed_qty * unit_material_quota, 2)
    wip_material_quota = round(wip_qty * unit_material_quota * material_completion, 2)
    completed_hours_quota = round(completed_qty * unit_hour_quota, 2)
    wip_hours_quota = round(wip_qty * unit_hour_quota * processing_completion, 2)
    result = method_quota_ratio(
        material, labor, overhead,
        completed_material_quota, wip_material_quota,
        completed_hours_quota, wip_hours_quota,
        completed_qty,
    )
    sheet = result["sheet"]
    question = (
        f"某企业生产{product}，本月完工 {completed_qty:,.2f} 件，月末在产品 {wip_qty:,.2f} 件。"
        f"单位产品材料定额 {format_money(unit_material_quota)} 元，单位产品工时定额 {unit_hour_quota:g} 小时；"
        f"在产品材料投料程度 {format_percent(material_completion)}，加工完工程度 {format_percent(processing_completion)}。"
        "采用定额比例法分配材料费用和加工费用，要求计算完工产品和在产品成本。"
    )
    formulas = [
        "完工产品材料定额 = 完工数量 × 单位材料定额",
        "在产品材料定额 = 在产品数量 × 单位材料定额 × 投料程度",
        "完工产品工时定额 = 完工数量 × 单位工时定额",
        "在产品工时定额 = 在产品数量 × 单位工时定额 × 完工程度",
        "材料分配率 = 材料总额 ÷（完工材料定额 + 在产品材料定额）",
        "人工/制造费用分配率 = 人工或制造费用总额 ÷（完工工时定额 + 在产品工时定额）",
    ]
    steps = [
        f"完工产品材料定额 = {completed_qty:,.2f} × {format_money(unit_material_quota)} = {format_money(completed_material_quota)} 元。",
        f"在产品材料定额 = {wip_qty:,.2f} × {format_money(unit_material_quota)} × {format_percent(material_completion)} = {format_money(wip_material_quota)} 元。",
        f"完工产品工时定额 = {completed_qty:,.2f} × {unit_hour_quota:g} = {completed_hours_quota:,.2f} 小时。",
        f"在产品工时定额 = {wip_qty:,.2f} × {unit_hour_quota:g} × {format_percent(processing_completion)} = {wip_hours_quota:,.2f} 小时。",
        f"材料分配率 = {format_money(material)} ÷ {result['material_base']:,.2f} = {result['material_rate']:.6f}。",
        f"人工分配率 = {format_money(labor)} ÷ {result['hours_base']:,.2f} = {result['labor_rate']:.6f}。",
        f"制造费用分配率 = {format_money(overhead)} ÷ {result['hours_base']:,.2f} = {result['overhead_rate']:.6f}。",
        f"完工产品总成本 = {format_money(sheet['completed_total'])} 元；在产品成本 = {format_money(sheet['wip_total'])} 元；单位成本 = {format_money(sheet['unit_cost'])} 元/件。",
    ]
    extra_headers = ["成本项目", "费用总额（元）", "分配标准合计", "分配率", "完工产品成本（元）", "期末在产品成本（元）"]
    extra_rows = [
        ["直接材料", format_money(material), f"{result['material_base']:,.2f}", f"{result['material_rate']:.6f}", format_money(sheet['completed'][0]), format_money(sheet['wip'][0])],
        ["直接人工", format_money(labor), f"{result['hours_base']:,.2f}", f"{result['labor_rate']:.6f}", format_money(sheet['completed'][1]), format_money(sheet['wip'][1])],
        ["制造费用", format_money(overhead), f"{result['hours_base']:,.2f}", f"{result['overhead_rate']:.6f}", format_money(sheet['completed'][2]), format_money(sheet['wip'][2])],
        ["合计", format_money(sheet['total_cost']), "—", "—", format_money(sheet['completed_total']), format_money(sheet['wip_total'])],
    ]
    summary = [
        "定额比例法同时使用材料定额和工时定额两个分配标准，适用于定额管理基础较好、各月在产品数量变动较大的企业。",
        f"完工产品成本 {format_money(sheet['completed_total'])} 元，期末在产品成本 {format_money(sheet['wip_total'])} 元。",
        "核对提示：材料定额与工时定额必须分别与材料费用、加工费用对应，不能交叉使用。",
    ]
    _finish(
        "定额比例法", question, formulas, steps, sheet, finished_goods_journal(sheet), summary,
        extra_tables=[("定额比例法费用分配表", extra_headers, extra_rows)],
    )


def run() -> None:
    """第五章菜单。"""
    options = [
        ("1", "不计算在产品成本法", run_no_wip),
        ("2", "在产品按固定成本计价法", run_fixed_wip),
        ("3", "在产品按原材料费用计价法", run_material_only),
        ("4", "约当产量比例法（材料一次投入/陆续投入）", run_equivalent),
        ("5", "在产品按定额成本计价法", run_quota_wip),
        ("6", "定额比例法（材料定额+工时定额）", run_quota_ratio),
    ]
    run_menu("第五章 生产费用在完工产品与在产品之间分配", options, back_text="返回主菜单")

