"""第十章 成本报表编制与成本分析。

覆盖：
1. 全部产品生产成本报表；
2. 可比产品成本降低额、降低率及因素分析（产量、品种结构、单位成本）；
3. 主要产品单位成本分析（材料量价差异、人工效率/工资率差异）；
4. 成本项目结构与同比变动分析；
5. 自动生成成本结构饼图、结构分析图和差异对比图。

本章计算与绘图数据均为自行设计的模拟教学案例。
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

import export
import visual
from utils import (
    ValidationError,
    format_money,
    format_percent,
    input_float,
    input_int,
    input_text,
    print_heading,
    print_steps,
    print_subheading,
    print_summary,
    print_table,
    require_nonnegative,
    require_positive,
    run_menu,
    safe_div,
)


def production_cost_report(products: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """编制全部产品生产成本报表。

    products 每项包含：name、output、actual_material、actual_labor、actual_overhead、
    plan_material、plan_labor、plan_overhead（均为单位成本）。
    """
    if not products:
        raise ValidationError("至少需要一种产品。")
    rows: List[Dict[str, Any]] = []
    for index, product in enumerate(products, start=1):
        name = str(product.get("name") or f"产品{index}")
        output = require_positive(product.get("output"), f"{name}的产量")
        actual = [
            require_nonnegative(product.get("actual_material"), f"{name}实际单位材料"),
            require_nonnegative(product.get("actual_labor"), f"{name}实际单位人工"),
            require_nonnegative(product.get("actual_overhead"), f"{name}实际单位制造费用"),
        ]
        plan = [
            require_nonnegative(product.get("plan_material"), f"{name}计划单位材料"),
            require_nonnegative(product.get("plan_labor"), f"{name}计划单位人工"),
            require_nonnegative(product.get("plan_overhead"), f"{name}计划单位制造费用"),
        ]
        actual_total = round(sum(actual) * output, 2)
        plan_total = round(sum(plan) * output, 2)
        rows.append({
            "name": name,
            "output": output,
            "actual_material": round(actual[0] * output, 2),
            "actual_labor": round(actual[1] * output, 2),
            "actual_overhead": round(actual[2] * output, 2),
            "actual_total": actual_total,
            "unit_actual": round(actual_total / output, 6),
            "plan_total": plan_total,
            "unit_plan": round(plan_total / output, 6),
            "difference": round(actual_total - plan_total, 2),
        })
    total_actual = round(sum(row["actual_total"] for row in rows), 2)
    total_plan = round(sum(row["plan_total"] for row in rows), 2)
    return {
        "rows": rows,
        "total_actual": total_actual,
        "total_plan": total_plan,
        "difference": round(total_actual - total_plan, 2),
    }


def comparable_product_analysis(products: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """可比产品成本降低额、降低率及三因素分析。"""
    if not products:
        raise ValidationError("至少需要一种可比产品。")
    rows: List[Dict[str, Any]] = []
    for index, product in enumerate(products, start=1):
        name = str(product.get("name") or f"产品{index}")
        plan_output = require_nonnegative(product.get("plan_output"), f"{name}计划产量")
        actual_output = require_nonnegative(product.get("actual_output"), f"{name}实际产量")
        last_year = require_nonnegative(product.get("last_year_unit"), f"{name}上年实际单位成本")
        plan_unit = require_nonnegative(product.get("plan_unit"), f"{name}本年计划单位成本")
        actual_unit = require_nonnegative(product.get("actual_unit"), f"{name}本年实际单位成本")
        plan_base = round(plan_output * last_year, 2)
        plan_cost = round(plan_output * plan_unit, 2)
        actual_base = round(actual_output * last_year, 2)
        actual_cost = round(actual_output * actual_unit, 2)
        rows.append({
            "name": name,
            "plan_output": plan_output,
            "actual_output": actual_output,
            "last_year_unit": last_year,
            "plan_unit": plan_unit,
            "actual_unit": actual_unit,
            "plan_base": plan_base,
            "plan_cost": plan_cost,
            "plan_reduction": round(plan_base - plan_cost, 2),
            "actual_base": actual_base,
            "plan_cost_at_actual": round(actual_output * plan_unit, 2),
            "actual_cost": actual_cost,
            "actual_reduction": round(actual_base - actual_cost, 2),
        })
    plan_base_total = round(sum(row["plan_base"] for row in rows), 2)
    plan_cost_total = round(sum(row["plan_cost"] for row in rows), 2)
    actual_base_total = round(sum(row["actual_base"] for row in rows), 2)
    actual_cost_total = round(sum(row["actual_cost"] for row in rows), 2)
    plan_reduction = round(plan_base_total - plan_cost_total, 2)
    actual_reduction = round(actual_base_total - actual_cost_total, 2)
    plan_rate = safe_div(plan_reduction, plan_base_total, "计划降低率分母")
    actual_rate = safe_div(actual_reduction, actual_base_total, "实际降低率分母")
    actual_structure_plan_rate = safe_div(
        sum(row["actual_output"] * (row["last_year_unit"] - row["plan_unit"]) for row in rows),
        actual_base_total,
        "实际结构下计划降低率分母",
    )
    output_effect = round((actual_base_total - plan_base_total) * plan_rate, 2)
    structure_effect = round(actual_base_total * (actual_structure_plan_rate - plan_rate), 2)
    unit_cost_effect = round(
        sum(row["actual_output"] * (row["plan_unit"] - row["actual_unit"]) for row in rows), 2
    )
    factor_total = round(output_effect + structure_effect + unit_cost_effect, 2)
    return {
        "rows": rows,
        "plan_base_total": plan_base_total,
        "plan_cost_total": plan_cost_total,
        "actual_base_total": actual_base_total,
        "actual_cost_total": actual_cost_total,
        "plan_reduction": plan_reduction,
        "actual_reduction": actual_reduction,
        "plan_rate": plan_rate,
        "actual_rate": actual_rate,
        "actual_structure_plan_rate": actual_structure_plan_rate,
        "plan_completion": round(actual_reduction - plan_reduction, 2),
        "output_effect": output_effect,
        "structure_effect": structure_effect,
        "unit_cost_effect": unit_cost_effect,
        "factor_total": factor_total,
        "check": round(actual_reduction - plan_reduction - factor_total, 2),
    }



def unit_cost_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """主要产品单位成本分析。

    data 包含：
        product、last_year、plan、actual（均为 {"material","labor","overhead"} 单位成本）；
        material: plan_qty、plan_price、actual_qty、actual_price；
        labor: plan_hours、plan_rate、actual_hours、actual_rate。
    """
    product = str(data.get("product") or "甲产品")
    items = [("material", "直接材料"), ("labor", "直接人工"), ("overhead", "制造费用")]
    last_year = data.get("last_year", {})
    plan = data.get("plan", {})
    actual = data.get("actual", {})
    rows = []
    for key, name in items:
        ly = require_nonnegative(last_year.get(key), f"{product}上年{name}")
        pl = require_nonnegative(plan.get(key), f"{product}计划{name}")
        ac = require_nonnegative(actual.get(key), f"{product}实际{name}")
        rows.append({
            "key": key,
            "name": name,
            "last_year": ly,
            "plan": pl,
            "actual": ac,
            "diff_plan": round(ac - pl, 2),
            "diff_last_year": round(ac - ly, 2),
            "change_rate": round((ac - pl) / pl, 6) if pl > 0 else None,
        })
    material = data.get("material", {})
    labor = data.get("labor", {})
    plan_qty = require_nonnegative(material.get("plan_qty"), "计划材料用量")
    plan_price = require_nonnegative(material.get("plan_price"), "计划材料单价")
    actual_qty = require_nonnegative(material.get("actual_qty"), "实际材料用量")
    actual_price = require_nonnegative(material.get("actual_price"), "实际材料单价")
    plan_hours = require_nonnegative(labor.get("plan_hours"), "计划工时")
    plan_rate = require_nonnegative(labor.get("plan_rate"), "计划工资率")
    actual_hours = require_nonnegative(labor.get("actual_hours"), "实际工时")
    actual_rate = require_nonnegative(labor.get("actual_rate"), "实际工资率")

    material_qty_effect = round((actual_qty - plan_qty) * plan_price, 2)
    material_price_effect = round((actual_price - plan_price) * actual_qty, 2)
    labor_efficiency_effect = round((actual_hours - plan_hours) * plan_rate, 2)
    labor_rate_effect = round((actual_rate - plan_rate) * actual_hours, 2)
    overhead_effect = round(actual.get("overhead", 0) - plan.get("overhead", 0), 2)
    plan_total = round(sum(require_nonnegative(plan.get(key), f"计划{name}") for key, name in items), 2)
    actual_total = round(sum(require_nonnegative(actual.get(key), f"实际{name}") for key, name in items), 2)
    last_year_total = round(sum(require_nonnegative(last_year.get(key), f"上年{name}") for key, name in items), 2)
    difference = round(actual_total - plan_total, 2)
    factor_total = round(material_qty_effect + material_price_effect + labor_efficiency_effect + labor_rate_effect + overhead_effect, 2)
    return {
        "product": product,
        "rows": rows,
        "plan_total": plan_total,
        "actual_total": actual_total,
        "last_year_total": last_year_total,
        "difference": difference,
        "difference_last_year": round(actual_total - last_year_total, 2),
        "material_qty_effect": material_qty_effect,
        "material_price_effect": material_price_effect,
        "labor_efficiency_effect": labor_efficiency_effect,
        "labor_rate_effect": labor_rate_effect,
        "overhead_effect": overhead_effect,
        "factor_total": factor_total,
        "check": round(difference - factor_total, 2),
    }


def cost_structure_analysis(items: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """成本项目结构分析与同比变动分析。"""
    if not items:
        raise ValidationError("至少需要一个成本项目。")
    rows = []
    for index, item in enumerate(items, start=1):
        name = str(item.get("name") or f"成本项目{index}")
        current = require_nonnegative(item.get("current"), f"{name}本期金额")
        prior = require_nonnegative(item.get("prior"), f"{name}上期金额")
        rows.append({"name": name, "current": current, "prior": prior})
    current_total = round(sum(row["current"] for row in rows), 2)
    prior_total = round(sum(row["prior"] for row in rows), 2)
    if current_total <= 0 or prior_total <= 0:
        raise ValidationError("本期和上期成本合计都必须大于 0，才能计算结构占比。")
    total_change = round(current_total - prior_total, 2)
    for row in rows:
        row["current_structure"] = row["current"] / current_total
        row["prior_structure"] = row["prior"] / prior_total
        row["change"] = round(row["current"] - row["prior"], 2)
        row["change_rate"] = (row["current"] - row["prior"]) / row["prior"] if row["prior"] > 0 else None
        row["structure_change"] = row["current_structure"] - row["prior_structure"]
        row["contribution"] = row["change"] / total_change if abs(total_change) > 1e-12 else None
    return {
        "rows": rows,
        "current_total": current_total,
        "prior_total": prior_total,
        "total_change": total_change,
        "total_change_rate": (current_total - prior_total) / prior_total,
    }



def _report_table(result: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
    headers = ["产品", "产量", "实际材料（元）", "实际人工（元）", "实际制造费用（元）", "实际总成本（元）", "单位实际成本（元/件）", "计划总成本（元）", "差异（元）"]
    rows = [
        [
            row["name"], f"{row['output']:,.2f}", format_money(row["actual_material"]), format_money(row["actual_labor"]),
            format_money(row["actual_overhead"]), format_money(row["actual_total"]), format_money(row["unit_actual"]),
            format_money(row["plan_total"]), format_money(row["difference"]),
        ]
        for row in result["rows"]
    ]
    rows.append(["合计", "—", format_money(sum(row["actual_material"] for row in result["rows"])), format_money(sum(row["actual_labor"] for row in result["rows"])), format_money(sum(row["actual_overhead"] for row in result["rows"])), format_money(result["total_actual"]), "—", format_money(result["total_plan"]), format_money(result["difference"])])
    return headers, rows


def _comparable_table(result: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
    headers = ["产品", "计划产量", "实际产量", "上年单位成本", "计划单位成本", "实际单位成本", "计划降低额（元）", "实际降低额（元）"]
    rows = [
        [
            row["name"], f"{row['plan_output']:,.2f}", f"{row['actual_output']:,.2f}", format_money(row["last_year_unit"]),
            format_money(row["plan_unit"]), format_money(row["actual_unit"]), format_money(row["plan_reduction"]), format_money(row["actual_reduction"]),
        ]
        for row in result["rows"]
    ]
    rows.append(["合计", "—", "—", "—", "—", "—", format_money(result["plan_reduction"]), format_money(result["actual_reduction"])])
    return headers, rows


def _comparable_factor_table(result: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
    headers = ["影响因素", "影响金额（元）", "说明"]
    rows = [
        ["产量变动", format_money(result["output_effect"]), "产量变化对成本降低额的影响"],
        ["品种结构变动", format_money(result["structure_effect"]), "产品结构变化对成本降低额的影响"],
        ["单位成本变动", format_money(result["unit_cost_effect"]), "各产品单位成本变化对成本降低额的影响"],
        ["合计", format_money(result["factor_total"]), "应等于实际降低额 - 计划降低额"],
    ]
    return headers, rows


def _unit_table(result: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
    headers = ["成本项目", "上年实际（元/件）", "本年计划（元/件）", "本年实际（元/件）", "比计划差异（元）", "比上年差异（元）", "比计划差异率"]
    rows = []
    for row in result["rows"]:
        rate = format_percent(row["change_rate"]) if row["change_rate"] is not None else "—"
        rows.append([
            row["name"], format_money(row["last_year"]), format_money(row["plan"]), format_money(row["actual"]),
            format_money(row["diff_plan"]), format_money(row["diff_last_year"]), rate,
        ])
    rows.append(["合计", format_money(result["last_year_total"]), format_money(result["plan_total"]), format_money(result["actual_total"]), format_money(result["difference"]), format_money(result["difference_last_year"]), "—"])
    return headers, rows


def _unit_factor_table(result: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
    headers = ["差异因素", "影响金额（元）", "说明"]
    rows = [
        ["材料用量差异", format_money(result["material_qty_effect"]), "（实际用量 - 计划用量）× 计划单价"],
        ["材料价格差异", format_money(result["material_price_effect"]), "（实际单价 - 计划单价）× 实际用量"],
        ["人工效率差异", format_money(result["labor_efficiency_effect"]), "（实际工时 - 计划工时）× 计划工资率"],
        ["工资率差异", format_money(result["labor_rate_effect"]), "（实际工资率 - 计划工资率）× 实际工时"],
        ["制造费用差异", format_money(result["overhead_effect"]), "实际制造费用 - 计划制造费用"],
        ["合计", format_money(result["factor_total"]), "应等于单位成本实际与计划的差异"],
    ]
    return headers, rows


def _structure_table(result: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
    headers = ["成本项目", "本期金额（元）", "上期金额（元）", "本期结构", "上期结构", "结构变动", "金额变动（元）", "变动率", "对总变动贡献"]
    rows = []
    for row in result["rows"]:
        rate = format_percent(row["change_rate"]) if row["change_rate"] is not None else "—"
        contribution = format_percent(row["contribution"]) if row["contribution"] is not None else "—"
        rows.append([
            row["name"], format_money(row["current"]), format_money(row["prior"]), format_percent(row["current_structure"]),
            format_percent(row["prior_structure"]), f"{row['structure_change'] * 100:+.2f} 个百分点",
            format_money(row["change"]), rate, contribution,
        ])
    total_contribution = "100.00%" if abs(result["total_change"]) > 1e-12 else "—"
    rows.append(["合计", format_money(result["current_total"]), format_money(result["prior_total"]), "100.00%", "100.00%", "—", format_money(result["total_change"]), format_percent(result["total_change_rate"]), total_contribution])
    return headers, rows



def run_production_report() -> None:
    """全部产品生产成本报表。"""
    print_heading("第十章 成本报表：全部产品生产成本报表", "-")
    count = input_int("产品种数", 2, min_value=1, max_value=20, name="产品种数")
    defaults = [
        {"name": "甲产品", "output": 1000.0, "actual": (40.0, 20.0, 10.0), "plan": (38.0, 21.0, 11.0)},
        {"name": "乙产品", "output": 500.0, "actual": (60.0, 30.0, 15.0), "plan": (62.0, 28.0, 14.0)},
    ]
    products = []
    for i in range(count):
        item = defaults[i] if i < len(defaults) else {"name": f"产品{i + 1}", "output": 500.0, "actual": (50.0, 25.0, 12.0), "plan": (50.0, 25.0, 12.0)}
        name = input_text(f"第{i + 1}种产品名称", item["name"])
        output = input_float(f"{name}产量", item["output"], min_value=0.0, name="产量")
        print(f"  请输入{name}的单位成本（元/件）：")
        actual_material = input_float("实际直接材料", item["actual"][0], min_value=0.0, name="实际材料")
        actual_labor = input_float("实际直接人工", item["actual"][1], min_value=0.0, name="实际人工")
        actual_overhead = input_float("实际制造费用", item["actual"][2], min_value=0.0, name="实际制造费用")
        plan_material = input_float("计划直接材料", item["plan"][0], min_value=0.0, name="计划材料")
        plan_labor = input_float("计划直接人工", item["plan"][1], min_value=0.0, name="计划人工")
        plan_overhead = input_float("计划制造费用", item["plan"][2], min_value=0.0, name="计划制造费用")
        products.append({
            "name": name, "output": output,
            "actual_material": actual_material, "actual_labor": actual_labor, "actual_overhead": actual_overhead,
            "plan_material": plan_material, "plan_labor": plan_labor, "plan_overhead": plan_overhead,
        })
    result = production_cost_report(products)
    question = (
        f"某企业本月生产 {count} 种产品，各产品产量、实际单位成本和计划单位成本如下表。"
        "要求编制全部产品生产成本报表，计算各产品实际总成本、单位成本和与计划总成本的差异。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "某产品实际总成本 = 产量 ×（实际单位材料 + 实际单位人工 + 实际单位制造费用）",
        "某产品计划总成本 = 产量 ×（计划单位材料 + 计划单位人工 + 计划单位制造费用）",
        "成本差异 = 实际总成本 - 计划总成本（正数为超支，负数为节约）",
        "单位实际成本 = 实际总成本 ÷ 产量",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")
    steps = [
        f"全部产品实际总成本 = {format_money(result['total_actual'])} 元；计划总成本 = {format_money(result['total_plan'])} 元；差异 = {format_money(result['difference'])} 元。",
    ]
    for row in result["rows"]:
        steps.append(
            f"{row['name']}：实际总成本 {format_money(row['actual_total'])} 元，单位成本 {format_money(row['unit_actual'])} 元/件；"
            f"计划总成本 {format_money(row['plan_total'])} 元，差异 {format_money(row['difference'])} 元。"
        )
    print_steps(steps)
    headers, rows = _report_table(result)
    print_table(headers, rows, "全部产品生产成本报表")
    summary = [
        f"全部产品实际总成本 {format_money(result['total_actual'])} 元，比计划 {format_money(result['difference'])} 元。",
        "成本报表应分别反映可比产品与不可比产品，并结合产量、品种结构和单位成本进行进一步分析。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第十章 成本报表与分析",
        "全部产品生产成本报表",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("全部产品生产成本报表", headers, rows)],
        journal=["本报表为成本报表编制，不涉及单独会计分录。"],
        summary=summary,
        conclusion=f"全部产品实际总成本 {format_money(result['total_actual'])} 元，差异 {format_money(result['difference'])} 元。",
    )



def run_comparable() -> None:
    """可比产品成本降低额与降低率分析。"""
    print_heading("第十章 成本分析：可比产品成本降低分析", "-")
    count = input_int("可比产品种数", 2, min_value=1, max_value=20, name="可比产品种数")
    defaults = [
        {"name": "甲产品", "plan_output": 1000.0, "actual_output": 1100.0, "last_year_unit": 100.0, "plan_unit": 95.0, "actual_unit": 92.0},
        {"name": "乙产品", "plan_output": 500.0, "actual_output": 480.0, "last_year_unit": 80.0, "plan_unit": 78.0, "actual_unit": 79.0},
    ]
    products = []
    for i in range(count):
        item = defaults[i] if i < len(defaults) else {"name": f"产品{i + 1}", "plan_output": 500.0, "actual_output": 500.0, "last_year_unit": 100.0, "plan_unit": 95.0, "actual_unit": 94.0}
        name = input_text(f"第{i + 1}种可比产品名称", item["name"])
        products.append({
            "name": name,
            "plan_output": input_float(f"{name}计划产量", item["plan_output"], min_value=0.0, name="计划产量"),
            "actual_output": input_float(f"{name}实际产量", item["actual_output"], min_value=0.0, name="实际产量"),
            "last_year_unit": input_float(f"{name}上年实际单位成本（元）", item["last_year_unit"], min_value=0.0, name="上年单位成本"),
            "plan_unit": input_float(f"{name}本年计划单位成本（元）", item["plan_unit"], min_value=0.0, name="计划单位成本"),
            "actual_unit": input_float(f"{name}本年实际单位成本（元）", item["actual_unit"], min_value=0.0, name="实际单位成本"),
        })
    result = comparable_product_analysis(products)
    question = (
        f"某企业生产 {count} 种可比产品，各产品计划产量、实际产量及上年、计划、实际单位成本如下。"
        "要求计算可比产品成本计划降低额、计划降低率、实际降低额、实际降低率，并进行产量、品种结构和单位成本三因素分析。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "计划降低额 = Σ计划产量×上年单位成本 - Σ计划产量×计划单位成本",
        "计划降低率 = 计划降低额 ÷ Σ计划产量×上年单位成本",
        "实际降低额 = Σ实际产量×上年单位成本 - Σ实际产量×实际单位成本",
        "实际降低率 = 实际降低额 ÷ Σ实际产量×上年单位成本",
        "产量变动影响 =（实际产量按上年成本计算的总成本 - 计划产量按上年成本计算的总成本）× 计划降低率",
        "品种结构变动影响 = 实际产量按上年成本计算的总成本 ×（实际结构下计划降低率 - 计划降低率）",
        "单位成本变动影响 = Σ实际产量×（计划单位成本 - 实际单位成本）",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")
    steps = [
        f"计划降低额 = {format_money(result['plan_base_total'])} - {format_money(result['plan_cost_total'])} = {format_money(result['plan_reduction'])} 元；计划降低率 = {format_percent(result['plan_rate'])}。",
        f"实际降低额 = {format_money(result['actual_base_total'])} - {format_money(result['actual_cost_total'])} = {format_money(result['actual_reduction'])} 元；实际降低率 = {format_percent(result['actual_rate'])}。",
        f"实际比计划多降低 {format_money(result['plan_completion'])} 元。",
        f"产量变动影响 = {format_money(result['output_effect'])} 元；品种结构变动影响 = {format_money(result['structure_effect'])} 元；单位成本变动影响 = {format_money(result['unit_cost_effect'])} 元。",
        f"三因素影响合计 = {format_money(result['factor_total'])} 元，与实际降低额减计划降低额一致（校验差异 {format_money(result['check'])} 元）。",
    ]
    print_steps(steps)
    headers, rows = _comparable_table(result)
    print_table(headers, rows, "可比产品成本降低额计算表")
    factor_headers, factor_rows = _comparable_factor_table(result)
    print_table(factor_headers, factor_rows, "可比产品成本降低因素分析表")
    summary_headers = ["项目", "金额/比率"]
    summary_rows = [
        ["计划降低额（元）", format_money(result["plan_reduction"])],
        ["计划降低率", format_percent(result["plan_rate"])],
        ["实际降低额（元）", format_money(result["actual_reduction"])],
        ["实际降低率", format_percent(result["actual_rate"])],
        ["实际比计划多降低（元）", format_money(result["plan_completion"])],
    ]
    print_table(summary_headers, summary_rows, "可比产品成本降低情况汇总")

    chart_path = visual.plot_comparison_chart(
        [row["name"] for row in result["rows"]],
        {
            "上年基准成本": [row["actual_base"] for row in result["rows"]],
            "按计划单位成本计算": [row["plan_cost_at_actual"] for row in result["rows"]],
            "本年实际成本": [row["actual_cost"] for row in result["rows"]],
        },
        "可比产品成本对比图",
        "chapter10_可比产品成本对比",
    )
    summary = [
        f"计划降低率 {format_percent(result['plan_rate'])}，实际降低率 {format_percent(result['actual_rate'])}，实际降低额 {format_money(result['actual_reduction'])} 元。",
        f"实际比计划多降低 {format_money(result['plan_completion'])} 元；其中产量、品种结构、单位成本影响分别为 {format_money(result['output_effect'])}、{format_money(result['structure_effect'])}、{format_money(result['unit_cost_effect'])} 元。",
    ]
    if chart_path:
        summary.append(f"对比图已保存：{chart_path}")
    print_summary(summary)
    export.save_calculation(
        "第十章 成本报表与分析",
        "可比产品成本降低额与降低率分析",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[
            ("可比产品成本降低额计算表", headers, rows),
            ("可比产品成本降低因素分析表", factor_headers, factor_rows),
            ("可比产品成本降低情况汇总", summary_headers, summary_rows),
        ],
        journal=["本分析为成本报表分析，不涉及单独会计分录。"],
        summary=summary,
        conclusion=f"实际降低额 {format_money(result['actual_reduction'])} 元，实际降低率 {format_percent(result['actual_rate'])}。",
    )



def run_unit_cost() -> None:
    """主要产品单位成本分析。"""
    print_heading("第十章 成本分析：主要产品单位成本分析", "-")
    product = input_text("产品名称", "甲产品")
    print("  请输入单位成本资料（元/件）：")
    last_year = {
        "material": input_float("上年直接材料", 52.0, min_value=0.0, name="上年材料"),
        "labor": input_float("上年直接人工", 48.0, min_value=0.0, name="上年人工"),
        "overhead": input_float("上年制造费用", 20.0, min_value=0.0, name="上年制造费用"),
    }
    plan = {
        "material": input_float("计划直接材料", 50.0, min_value=0.0, name="计划材料"),
        "labor": input_float("计划直接人工", 48.0, min_value=0.0, name="计划人工"),
        "overhead": input_float("计划制造费用", 20.0, min_value=0.0, name="计划制造费用"),
    }
    actual = {
        "material": input_float("实际直接材料", 46.8, min_value=0.0, name="实际材料"),
        "labor": input_float("实际直接人工", 48.0, min_value=0.0, name="实际人工"),
        "overhead": input_float("实际制造费用", 21.0, min_value=0.0, name="实际制造费用"),
    }
    print("  材料用量与价格：")
    material_data = {
        "plan_qty": input_float("计划材料用量（千克/件）", 10.0, min_value=0.0, name="计划用量"),
        "plan_price": input_float("计划材料单价（元/千克）", 5.0, min_value=0.0, name="计划单价"),
        "actual_qty": input_float("实际材料用量（千克/件）", 9.0, min_value=0.0, name="实际用量"),
        "actual_price": input_float("实际材料单价（元/千克）", 5.2, min_value=0.0, name="实际单价"),
    }
    print("  人工工时与工资率：")
    labor_data = {
        "plan_hours": input_float("计划工时（小时/件）", 8.0, min_value=0.0, name="计划工时"),
        "plan_rate": input_float("计划工资率（元/小时）", 6.0, min_value=0.0, name="计划工资率"),
        "actual_hours": input_float("实际工时（小时/件）", 7.5, min_value=0.0, name="实际工时"),
        "actual_rate": input_float("实际工资率（元/小时）", 6.4, min_value=0.0, name="实际工资率"),
    }
    result = unit_cost_analysis({
        "product": product,
        "last_year": last_year,
        "plan": plan,
        "actual": actual,
        "material": material_data,
        "labor": labor_data,
    })
    question = (
        f"某企业生产{product}，其单位成本资料如下。要求编制单位成本分析表，计算实际与计划、上年的差异，"
        "并对直接材料进行用量差异和价格差异分析、对直接人工进行效率差异和工资率差异分析。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "单位成本差异 = 实际单位成本 - 计划单位成本（或上年实际单位成本）",
        "材料用量差异 =（实际用量 - 计划用量）× 计划单价",
        "材料价格差异 =（实际单价 - 计划单价）× 实际用量",
        "人工效率差异 =（实际工时 - 计划工时）× 计划工资率",
        "工资率差异 =（实际工资率 - 计划工资率）× 实际工时",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")
    steps = [
        f"计划单位成本 = {format_money(result['plan_total'])} 元/件；实际单位成本 = {format_money(result['actual_total'])} 元/件；差异 = {format_money(result['difference'])} 元/件。",
        f"材料用量差异 = {format_money(result['material_qty_effect'])} 元；材料价格差异 = {format_money(result['material_price_effect'])} 元。",
        f"人工效率差异 = {format_money(result['labor_efficiency_effect'])} 元；工资率差异 = {format_money(result['labor_rate_effect'])} 元。",
        f"制造费用差异 = {format_money(result['overhead_effect'])} 元；差异因素合计 = {format_money(result['factor_total'])} 元。",
        f"校验：单位成本差异 {format_money(result['difference'])} - 因素合计 {format_money(result['factor_total'])} = {format_money(result['check'])} 元（应为 0）。",
    ]
    print_steps(steps)
    headers, rows = _unit_table(result)
    print_table(headers, rows, "主要产品单位成本分析表")
    factor_headers, factor_rows = _unit_factor_table(result)
    print_table(factor_headers, factor_rows, "单位成本差异因素分析表")

    chart_path = visual.plot_comparison_chart(
        [row["name"] for row in result["rows"]],
        {
            "上年实际": [row["last_year"] for row in result["rows"]],
            "本年计划": [row["plan"] for row in result["rows"]],
            "本年实际": [row["actual"] for row in result["rows"]],
        },
        f"{product}单位成本项目对比图",
        f"chapter10_{product}_单位成本对比",
    )
    summary = [
        f"实际单位成本 {format_money(result['actual_total'])} 元/件，比计划 {format_money(result['difference'])} 元/件，比上年 {format_money(result['difference_last_year'])} 元/件。",
        f"材料用量差异 {format_money(result['material_qty_effect'])} 元，材料价格差异 {format_money(result['material_price_effect'])} 元；人工效率差异 {format_money(result['labor_efficiency_effect'])} 元，工资率差异 {format_money(result['labor_rate_effect'])} 元。",
    ]
    if chart_path:
        summary.append(f"单位成本对比图已保存：{chart_path}")
    print_summary(summary)
    export.save_calculation(
        "第十章 成本报表与分析",
        "主要产品单位成本分析",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[
            ("主要产品单位成本分析表", headers, rows),
            ("单位成本差异因素分析表", factor_headers, factor_rows),
        ],
        journal=["本分析为成本报表分析，不涉及单独会计分录。"],
        summary=summary,
        conclusion=f"实际单位成本 {format_money(result['actual_total'])} 元/件，差异 {format_money(result['difference'])} 元/件。",
    )



def run_structure() -> None:
    """成本项目结构分析与同比变动分析（自动绘图）。"""
    print_heading("第十章 成本分析：成本项目结构与同比变动", "-")
    count = input_int("成本项目数", 3, min_value=1, max_value=12, name="成本项目数")
    defaults = [("直接材料", 60000.0, 55000.0), ("直接人工", 25000.0, 24000.0), ("制造费用", 15000.0, 16000.0)]
    items = []
    for i in range(count):
        default_name, current, prior = defaults[i] if i < len(defaults) else (f"成本项目{i + 1}", 10000.0, 9000.0)
        name = input_text(f"第{i + 1}个成本项目名称", default_name)
        current_value = input_float(f"{name}本期金额（元）", current, min_value=0.0, name="本期金额")
        prior_value = input_float(f"{name}上期金额（元）", prior, min_value=0.0, name="上期金额")
        items.append({"name": name, "current": current_value, "prior": prior_value})
    result = cost_structure_analysis(items)
    question = (
        f"某企业本期成本合计 {format_money(result['current_total'])} 元，上期成本合计 {format_money(result['prior_total'])} 元。"
        "各成本项目金额如下表。要求计算成本项目结构占比、结构变动、金额变动率和对总变动的贡献，并生成结构图与对比图。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "某项目结构占比 = 该项目金额 ÷ 成本合计",
        "结构变动 = 本期结构占比 - 上期结构占比",
        "金额变动率 =（本期金额 - 上期金额）÷ 上期金额",
        "对总变动贡献 = 该项目金额变动 ÷ 成本总变动",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")
    steps = [
        f"本期成本合计 = {format_money(result['current_total'])} 元；上期成本合计 = {format_money(result['prior_total'])} 元；总变动 = {format_money(result['total_change'])} 元（{format_percent(result['total_change_rate'])}）。",
    ]
    for row in result["rows"]:
        steps.append(
            f"{row['name']}：本期结构 {format_percent(row['current_structure'])}，上期结构 {format_percent(row['prior_structure'])}，"
            f"结构变动 {row['structure_change'] * 100:+.2f} 个百分点；金额变动 {format_money(row['change'])} 元。"
        )
    print_steps(steps)
    headers, rows = _structure_table(result)
    print_table(headers, rows, "成本项目结构与同比变动分析表")

    labels = [row["name"] for row in result["rows"]]
    current_values = [row["current"] for row in result["rows"]]
    prior_values = [row["prior"] for row in result["rows"]]
    chart_paths = []
    path1 = visual.plot_cost_pie(labels, current_values, "本期成本项目结构饼图", "chapter10_成本结构饼图")
    if path1:
        chart_paths.append(path1)
    path2 = visual.plot_structure_chart(labels, current_values, "本期成本项目结构分析", "chapter10_成本结构分析")
    if path2:
        chart_paths.append(path2)
    path3 = visual.plot_comparison_chart(labels, {"本期实际": current_values, "上期实际": prior_values}, "成本项目同比对比图", "chapter10_成本同比对比")
    if path3:
        chart_paths.append(path3)

    summary = [
        f"本期成本较上期变动 {format_money(result['total_change'])} 元，变动率 {format_percent(result['total_change_rate'])}。",
        "结构分析应结合金额变动率和结构变动百分点，判断成本变动的主要来源。",
    ]
    for path in chart_paths:
        summary.append(f"图表已保存：{path}")
    print_summary(summary)
    export.save_calculation(
        "第十章 成本报表与分析",
        "成本项目结构与同比变动分析",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("成本项目结构与同比变动分析表", headers, rows)],
        journal=["本分析为成本报表分析，不涉及单独会计分录。"],
        summary=summary,
        conclusion=f"本期成本 {format_money(result['current_total'])} 元，较上期变动 {format_money(result['total_change'])} 元。",
    )



def run_comprehensive_demo() -> None:
    """一键综合演示：成本报表 + 三类分析 + 图表（内置案例）。"""
    print_heading("第十章 成本报表与分析：一键综合演示", "-")
    products = [
        {"name": "甲产品", "output": 1000.0, "actual_material": 40.0, "actual_labor": 20.0, "actual_overhead": 10.0, "plan_material": 38.0, "plan_labor": 21.0, "plan_overhead": 11.0},
        {"name": "乙产品", "output": 500.0, "actual_material": 60.0, "actual_labor": 30.0, "actual_overhead": 15.0, "plan_material": 62.0, "plan_labor": 28.0, "plan_overhead": 14.0},
    ]
    report = production_cost_report(products)
    comparable = comparable_product_analysis([
        {"name": "甲产品", "plan_output": 1000.0, "actual_output": 1100.0, "last_year_unit": 100.0, "plan_unit": 95.0, "actual_unit": 92.0},
        {"name": "乙产品", "plan_output": 500.0, "actual_output": 480.0, "last_year_unit": 80.0, "plan_unit": 78.0, "actual_unit": 79.0},
    ])
    unit = unit_cost_analysis({
        "product": "甲产品",
        "last_year": {"material": 52.0, "labor": 48.0, "overhead": 20.0},
        "plan": {"material": 50.0, "labor": 48.0, "overhead": 20.0},
        "actual": {"material": 46.8, "labor": 48.0, "overhead": 21.0},
        "material": {"plan_qty": 10.0, "plan_price": 5.0, "actual_qty": 9.0, "actual_price": 5.2},
        "labor": {"plan_hours": 8.0, "plan_rate": 6.0, "actual_hours": 7.5, "actual_rate": 6.4},
    })
    structure = cost_structure_analysis([
        {"name": "直接材料", "current": 60000.0, "prior": 55000.0},
        {"name": "直接人工", "current": 25000.0, "prior": 24000.0},
        {"name": "制造费用", "current": 15000.0, "prior": 16000.0},
    ])

    report_headers, report_rows = _report_table(report)
    print_table(report_headers, report_rows, "1. 全部产品生产成本报表")
    comparable_headers, comparable_rows = _comparable_table(comparable)
    print_table(comparable_headers, comparable_rows, "2. 可比产品成本降低额计算表")
    factor_headers, factor_rows = _comparable_factor_table(comparable)
    print_table(factor_headers, factor_rows, "3. 可比产品成本降低因素分析表")
    unit_headers, unit_rows = _unit_table(unit)
    print_table(unit_headers, unit_rows, "4. 甲产品单位成本分析表")
    unit_factor_headers, unit_factor_rows = _unit_factor_table(unit)
    print_table(unit_factor_headers, unit_factor_rows, "5. 甲产品单位成本差异因素表")
    structure_headers, structure_rows = _structure_table(structure)
    print_table(structure_headers, structure_rows, "6. 成本项目结构与同比变动分析表")

    labels = [row["name"] for row in structure["rows"]]
    current_values = [row["current"] for row in structure["rows"]]
    prior_values = [row["prior"] for row in structure["rows"]]
    chart_paths = []
    for path in (
        visual.plot_cost_pie(labels, current_values, "本期成本结构饼图", "chapter10_demo_成本结构饼图"),
        visual.plot_structure_chart(labels, current_values, "本期成本结构分析", "chapter10_demo_成本结构分析"),
        visual.plot_comparison_chart(labels, {"本期实际": current_values, "上期实际": prior_values}, "成本项目同比对比图", "chapter10_demo_成本同比对比"),
        visual.plot_comparison_chart(
            [row["name"] for row in comparable["rows"]],
            {
                "上年基准": [row["actual_base"] for row in comparable["rows"]],
                "按计划单位成本计算": [row["plan_cost_at_actual"] for row in comparable["rows"]],
                "本年实际": [row["actual_cost"] for row in comparable["rows"]],
            },
            "可比产品成本对比图",
            "chapter10_demo_可比产品对比",
        ),
    ):
        if path:
            chart_paths.append(path)

    summary = [
        f"全部产品实际总成本 {format_money(report['total_actual'])} 元，与计划差异 {format_money(report['difference'])} 元。",
        f"可比产品实际降低额 {format_money(comparable['actual_reduction'])} 元，实际降低率 {format_percent(comparable['actual_rate'])}。",
        f"甲产品实际单位成本 {format_money(unit['actual_total'])} 元/件，比计划 {format_money(unit['difference'])} 元/件。",
        f"本期成本 {format_money(structure['current_total'])} 元，较上期变动 {format_money(structure['total_change'])} 元。",
    ]
    for path in chart_paths:
        summary.append(f"图表已保存：{path}")
    print_summary(summary)
    export.save_calculation(
        "第十章 成本报表与分析",
        "成本报表与分析一键综合演示",
        question="使用内置模拟教学案例，连续编制全部产品生产成本报表、可比产品成本降低分析、主要产品单位成本分析和成本项目结构分析，并自动生成图表。",
        formulas=[
            "全部产品实际总成本 = Σ（产量 × 单位成本）",
            "可比产品成本降低额 = 按上年单位成本计算的总成本 - 实际总成本",
            "单位成本差异 = 实际单位成本 - 计划单位成本",
            "成本项目结构 = 该项目金额 ÷ 成本合计",
        ],
        steps=summary,
        tables=[
            ("全部产品生产成本报表", report_headers, report_rows),
            ("可比产品成本降低额计算表", comparable_headers, comparable_rows),
            ("可比产品成本降低因素分析表", factor_headers, factor_rows),
            ("甲产品单位成本分析表", unit_headers, unit_rows),
            ("甲产品单位成本差异因素表", unit_factor_headers, unit_factor_rows),
            ("成本项目结构与同比变动分析表", structure_headers, structure_rows),
        ],
        journal=["本演示为成本报表与分析，不涉及单独会计分录。"],
        summary=summary,
        conclusion=f"综合演示完成，共生成 {len(chart_paths)} 张图表。",
    )


def run() -> None:
    """第十章菜单。"""
    options = [
        ("1", "全部产品生产成本报表", run_production_report),
        ("2", "可比产品成本降低额、降低率与因素分析", run_comparable),
        ("3", "主要产品单位成本分析（材料量价、人工效率工资率）", run_unit_cost),
        ("4", "成本项目结构分析与同比变动（自动绘图）", run_structure),
        ("5", "一键综合演示（报表+分析+图表）", run_comprehensive_demo),
    ]
    run_menu("第十章 成本报表编制与成本分析", options, back_text="返回主菜单")

