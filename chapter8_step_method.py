"""第八章 产品成本计算——分步法。

完整实现：
1. 逐步结转分步法——综合结转法，并自动进行成本还原；
2. 逐步结转分步法——分项结转法；
3. 平行结转分步法（广义在产品、份额计算）。

分步法适用于大量大批多步骤生产。案例为自行设计的两步骤模拟教学案例：
第一车间生产甲半成品，第二车间继续加工为甲产成品。
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

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
    input_yes_no,
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


DEFAULT_STEPS = [
    {
        "name": "第一车间", "product": "甲半成品", "completed_qty": 800.0, "wip_qty": 200.0,
        "completion": 0.5, "material": 50000.0, "labor": 18000.0, "overhead": 9000.0,
    },
    {
        "name": "第二车间", "product": "甲产成品", "completed_qty": 700.0, "wip_qty": 100.0,
        "completion": 0.5, "material": 0.0, "labor": 21000.0, "overhead": 14000.0,
    },
]


def _validate_steps(steps: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """校验并标准化分步法基础数据。"""
    if not steps:
        raise ValidationError("至少需要一个生产步骤。")
    validated = []
    for index, step in enumerate(steps, start=1):
        name = str(step.get("name") or f"步骤{index}")
        product = str(step.get("product") or f"{name}产品")
        completed = require_positive(step.get("completed_qty"), f"{name}完工数量")
        wip = require_nonnegative(step.get("wip_qty"), f"{name}在产品数量")
        completion = require_nonnegative(step.get("completion"), f"{name}在产品完工程度")
        if completion > 1:
            raise ValidationError(f"{name}在产品完工程度必须在 0%～100% 之间。")
        material = require_nonnegative(step.get("material"), f"{name}直接材料")
        labor = require_nonnegative(step.get("labor"), f"{name}直接人工")
        overhead = require_nonnegative(step.get("overhead"), f"{name}制造费用")
        validated.append({
            "name": name,
            "product": product,
            "completed_qty": completed,
            "wip_qty": wip,
            "completion": completion,
            "material": material,
            "labor": labor,
            "overhead": overhead,
        })
    return validated


def _restore_recursive(
    step_index: int,
    amount: float,
    completed_components: Sequence[Dict[str, float]],
    completed_totals: Sequence[float],
) -> Dict[str, float]:
    """把一定金额的上一步骤半成品成本按成本结构逐层还原。"""
    result = {"直接材料": 0.0, "直接人工": 0.0, "制造费用": 0.0}
    if step_index < 0 or amount <= 0:
        return result
    total = completed_totals[step_index]
    if total <= 0:
        return result
    scale = amount / total
    for item, value in completed_components[step_index].items():
        if item == "半成品":
            sub = _restore_recursive(step_index - 1, value * scale, completed_components, completed_totals)
            for key in result:
                result[key] += sub[key]
        elif item in result:
            result[item] += value * scale
    return result


def step_comprehensive(steps: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """逐步结转分步法——综合结转（含成本还原）。"""
    steps = _validate_steps(steps)
    completed_components: List[Dict[str, float]] = []
    completed_totals: List[float] = []
    step_results: List[Dict[str, Any]] = []

    for i, step in enumerate(steps):
        completed = step["completed_qty"]
        wip = step["wip_qty"]
        completion = step["completion"]
        processing_eq = equivalent_units(completed, wip, completion)
        if i == 0:
            material_eq = completed + wip
            material_unit = safe_div(step["material"], material_eq, "材料分配率")
            labor_unit = safe_div(step["labor"], processing_eq, "人工分配率")
            overhead_unit = safe_div(step["overhead"], processing_eq, "制造费用分配率")
            completed_material = round(material_unit * completed, 2)
            completed_labor = round(labor_unit * completed, 2)
            completed_overhead = round(overhead_unit * completed, 2)
            rows = [
                ["直接材料", format_money(step["material"]), f"{material_eq:,.2f}", f"{material_unit:.6f}", format_money(completed_material), format_money(step["material"] - completed_material)],
                ["直接人工", format_money(step["labor"]), f"{processing_eq:,.2f}", f"{labor_unit:.6f}", format_money(completed_labor), format_money(step["labor"] - completed_labor)],
                ["制造费用", format_money(step["overhead"]), f"{processing_eq:,.2f}", f"{overhead_unit:.6f}", format_money(completed_overhead), format_money(step["overhead"] - completed_overhead)],
            ]
            components = {"直接材料": completed_material, "直接人工": completed_labor, "制造费用": completed_overhead}
            total_completed = round(sum(components.values()), 2)
            total_cost = round(step["material"] + step["labor"] + step["overhead"], 2)
            wip_cost = round(total_cost - total_completed, 2)
        else:
            semi_total = completed_totals[i - 1]
            semi_eq = completed + wip  # 半成品在生产开始时一次投入
            semi_unit = safe_div(semi_total, semi_eq, "半成品分配率")
            labor_unit = safe_div(step["labor"], processing_eq, "人工分配率")
            overhead_unit = safe_div(step["overhead"], processing_eq, "制造费用分配率")
            completed_semi = round(semi_unit * completed, 2)
            completed_labor = round(labor_unit * completed, 2)
            completed_overhead = round(overhead_unit * completed, 2)
            rows = [
                ["半成品", format_money(semi_total), f"{semi_eq:,.2f}", f"{semi_unit:.6f}", format_money(completed_semi), format_money(semi_total - completed_semi)],
            ]
            components = {"半成品": completed_semi, "直接人工": completed_labor, "制造费用": completed_overhead}
            total_cost = round(semi_total + step["labor"] + step["overhead"], 2)
            # 若后续步骤还投入直接材料，单独按本步骤投料数量分配
            if step["material"] > 0:
                own_material_unit = safe_div(step["material"], semi_eq, "本步材料分配率")
                completed_own_material = round(own_material_unit * completed, 2)
                rows.append([
                    "直接材料（本步投入）", format_money(step["material"]), f"{semi_eq:,.2f}", f"{own_material_unit:.6f}",
                    format_money(completed_own_material), format_money(step["material"] - completed_own_material),
                ])
                components["直接材料"] = completed_own_material
                total_cost = round(total_cost + step["material"], 2)
            rows.extend([
                ["直接人工", format_money(step["labor"]), f"{processing_eq:,.2f}", f"{labor_unit:.6f}", format_money(completed_labor), format_money(step["labor"] - completed_labor)],
                ["制造费用", format_money(step["overhead"]), f"{processing_eq:,.2f}", f"{overhead_unit:.6f}", format_money(completed_overhead), format_money(step["overhead"] - completed_overhead)],
            ])
            total_completed = round(sum(components.values()), 2)
            wip_cost = round(total_cost - total_completed, 2)
        rows.append(["合计", format_money(total_cost), "—", "—", format_money(total_completed), format_money(wip_cost)])
        completed_components.append(components)
        completed_totals.append(total_completed)
        step_results.append({
            "step": step,
            "rows": rows,
            "total_cost": total_cost,
            "completed_total": total_completed,
            "wip_total": wip_cost,
            "processing_eq": processing_eq,
        })

    # 成本还原：最终产成品成本中的“半成品”按上一步骤成本结构逐层还原
    final_components = completed_components[-1]
    final_labor = final_components.get("直接人工", 0.0)
    final_overhead = final_components.get("制造费用", 0.0)
    before = {
        "半成品": final_components.get("半成品", 0.0),
        "直接材料": final_components.get("直接材料", 0.0),
        "直接人工": final_labor,
        "制造费用": final_overhead,
    }
    restored = {"直接材料": 0.0, "直接人工": 0.0, "制造费用": 0.0}
    if len(steps) > 1:
        restored = _restore_recursive(len(steps) - 2, final_components.get("半成品", 0.0), completed_components, completed_totals)
        # 最后一步自身投入的直接材料不需要还原，直接计入还原后成本
        restored["直接材料"] += final_components.get("直接材料", 0.0)
    else:
        restored["直接材料"] = final_components.get("直接材料", 0.0)
    restored["直接人工"] += final_labor
    restored["制造费用"] += final_overhead
    restored_total = round(sum(restored.values()), 2)
    restoration_rows = [
        ["半成品", format_money(before["半成品"]), format_money(-before["半成品"]), "0.00"],
        ["直接材料", format_money(before["直接材料"]), format_money(restored["直接材料"] - before["直接材料"]), format_money(restored["直接材料"])],
        ["直接人工", format_money(before["直接人工"]), format_money(restored["直接人工"] - before["直接人工"]), format_money(restored["直接人工"])],
        ["制造费用", format_money(before["制造费用"]), format_money(restored["制造费用"] - before["制造费用"]), format_money(restored["制造费用"])],
        ["合计", format_money(sum(before.values())), "—", format_money(restored_total)],
    ]
    return {
        "steps": steps,
        "results": step_results,
        "completed_components": completed_components,
        "completed_totals": completed_totals,
        "final_total": completed_totals[-1],
        "before_restoration": before,
        "restored": restored,
        "restored_total": restored_total,
        "restoration_rows": restoration_rows,
        "final_wip": step_results[-1]["wip_total"],
    }



def step_itemized(steps: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """逐步结转分步法——分项结转。

    上一步骤转入的半成品成本按成本项目分别结转。由于半成品已包含前一步骤的
    完整加工成本，本工具将转入成本按实物数量比例（100%投料程度）分配；
    本步骤新发生的加工费用按本步骤约当产量分配。
    """
    steps = _validate_steps(steps)
    step_results: List[Dict[str, Any]] = []
    completed_components: List[Dict[str, float]] = []
    for i, step in enumerate(steps):
        completed = step["completed_qty"]
        wip = step["wip_qty"]
        completion = step["completion"]
        processing_eq = equivalent_units(completed, wip, completion)
        quantity_base = completed + wip
        rows: List[List[str]] = []
        if i == 0:
            material_rate = safe_div(step["material"], quantity_base, "材料分配率")
            labor_rate = safe_div(step["labor"], processing_eq, "人工分配率")
            overhead_rate = safe_div(step["overhead"], processing_eq, "制造费用分配率")
            completed_material = round(material_rate * completed, 2)
            completed_labor = round(labor_rate * completed, 2)
            completed_overhead = round(overhead_rate * completed, 2)
            total_cost = round(step["material"] + step["labor"] + step["overhead"], 2)
            rows = [
                ["直接材料", format_money(step["material"]), f"{quantity_base:,.2f}", f"{material_rate:.6f}", format_money(completed_material), format_money(step["material"] - completed_material)],
                ["直接人工", format_money(step["labor"]), f"{processing_eq:,.2f}", f"{labor_rate:.6f}", format_money(completed_labor), format_money(step["labor"] - completed_labor)],
                ["制造费用", format_money(step["overhead"]), f"{processing_eq:,.2f}", f"{overhead_rate:.6f}", format_money(completed_overhead), format_money(step["overhead"] - completed_overhead)],
            ]
        else:
            prior = completed_components[i - 1]
            prior_material = prior["直接材料"]
            prior_labor = prior["直接人工"]
            prior_overhead = prior["制造费用"]
            prior_material_rate = safe_div(prior_material, quantity_base, "上步转入材料分配率")
            prior_labor_rate = safe_div(prior_labor, quantity_base, "上步转入人工分配率")
            prior_overhead_rate = safe_div(prior_overhead, quantity_base, "上步转入制造费用分配率")
            own_material_rate = safe_div(step["material"], quantity_base, "本步材料分配率")
            own_labor_rate = safe_div(step["labor"], processing_eq, "本步人工分配率")
            own_overhead_rate = safe_div(step["overhead"], processing_eq, "本步制造费用分配率")
            completed_material = round((prior_material_rate + own_material_rate) * completed, 2)
            completed_labor = round((prior_labor_rate + own_labor_rate) * completed, 2)
            completed_overhead = round((prior_overhead_rate + own_overhead_rate) * completed, 2)
            total_cost = round(prior_material + prior_labor + prior_overhead + step["material"] + step["labor"] + step["overhead"], 2)
            rows = [
                ["上步转入直接材料", format_money(prior_material), f"{quantity_base:,.2f}", f"{prior_material_rate:.6f}", format_money(prior_material_rate * completed), format_money(prior_material - prior_material_rate * completed)],
                ["本步发生直接材料", format_money(step["material"]), f"{quantity_base:,.2f}", f"{own_material_rate:.6f}", format_money(own_material_rate * completed), format_money(step["material"] - own_material_rate * completed)],
                ["上步转入直接人工", format_money(prior_labor), f"{quantity_base:,.2f}", f"{prior_labor_rate:.6f}", format_money(prior_labor_rate * completed), format_money(prior_labor - prior_labor_rate * completed)],
                ["本步发生直接人工", format_money(step["labor"]), f"{processing_eq:,.2f}", f"{own_labor_rate:.6f}", format_money(own_labor_rate * completed), format_money(step["labor"] - own_labor_rate * completed)],
                ["上步转入制造费用", format_money(prior_overhead), f"{quantity_base:,.2f}", f"{prior_overhead_rate:.6f}", format_money(prior_overhead_rate * completed), format_money(prior_overhead - prior_overhead_rate * completed)],
                ["本步发生制造费用", format_money(step["overhead"]), f"{processing_eq:,.2f}", f"{own_overhead_rate:.6f}", format_money(own_overhead_rate * completed), format_money(step["overhead"] - own_overhead_rate * completed)],
            ]
        total_completed = round(completed_material + completed_labor + completed_overhead, 2)
        wip_cost = round(total_cost - total_completed, 2)
        rows.append(["合计", format_money(total_cost), "—", "—", format_money(total_completed), format_money(wip_cost)])
        components = {"直接材料": completed_material, "直接人工": completed_labor, "制造费用": completed_overhead}
        completed_components.append(components)
        step_results.append({
            "step": step,
            "rows": rows,
            "total_cost": total_cost,
            "completed_total": total_completed,
            "wip_total": wip_cost,
            "components": components,
        })
    final = step_results[-1]
    return {
        "steps": steps,
        "results": step_results,
        "completed_components": completed_components,
        "final_total": final["completed_total"],
        "final_components": completed_components[-1],
        "final_wip": final["wip_total"],
    }



def parallel_method(final_qty: Any, steps: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """平行结转分步法。

    各步骤只计算本步骤费用应计入最终产成品的“份额”，不结转半成品成本。
    某步骤约当产量 = 最终产成品数量 + 本步骤在产品约当产量 + 后续步骤在产品数量
    （后续步骤在产品对本步骤而言已全部加工完成，按 100% 计入）。
    """
    final = require_positive(final_qty, "最终产成品数量")
    if not steps:
        raise ValidationError("至少需要一个生产步骤。")
    validated = []
    for index, step in enumerate(steps, start=1):
        name = str(step.get("name") or f"步骤{index}")
        wip = require_nonnegative(step.get("wip_qty"), f"{name}在产品数量")
        completion = require_nonnegative(step.get("completion"), f"{name}在产品完工程度")
        if completion > 1:
            raise ValidationError(f"{name}在产品完工程度必须在 0%～100% 之间。")
        validated.append({
            "name": name,
            "wip_qty": wip,
            "completion": completion,
            "material": require_nonnegative(step.get("material"), f"{name}直接材料"),
            "labor": require_nonnegative(step.get("labor"), f"{name}直接人工"),
            "overhead": require_nonnegative(step.get("overhead"), f"{name}制造费用"),
        })

    results = []
    total_shares = {"直接材料": 0.0, "直接人工": 0.0, "制造费用": 0.0}
    total_wip = 0.0
    for i, step in enumerate(validated):
        later_wip = sum(item["wip_qty"] for item in validated[i + 1:])
        material_eq = final + step["wip_qty"] + later_wip
        processing_eq = final + step["wip_qty"] * step["completion"] + later_wip
        rows = []
        step_share = 0.0
        if step["material"] > 0:
            material_rate = safe_div(step["material"], material_eq, f"{step['name']}材料分配率")
            share = round(material_rate * final, 2)
            wip_cost = round(step["material"] - share, 2)
            rows.append(["直接材料", format_money(step["material"]), f"{material_eq:,.2f}", f"{material_rate:.6f}", format_money(share), format_money(wip_cost)])
            total_shares["直接材料"] += share
            step_share += share
        labor_rate = safe_div(step["labor"], processing_eq, f"{step['name']}人工分配率")
        share_labor = round(labor_rate * final, 2)
        wip_labor = round(step["labor"] - share_labor, 2)
        rows.append(["直接人工", format_money(step["labor"]), f"{processing_eq:,.2f}", f"{labor_rate:.6f}", format_money(share_labor), format_money(wip_labor)])
        total_shares["直接人工"] += share_labor
        step_share += share_labor

        overhead_rate = safe_div(step["overhead"], processing_eq, f"{step['name']}制造费用分配率")
        share_overhead = round(overhead_rate * final, 2)
        wip_overhead = round(step["overhead"] - share_overhead, 2)
        rows.append(["制造费用", format_money(step["overhead"]), f"{processing_eq:,.2f}", f"{overhead_rate:.6f}", format_money(share_overhead), format_money(wip_overhead)])
        total_shares["制造费用"] += share_overhead
        step_share += share_overhead

        step_total = round(step["material"] + step["labor"] + step["overhead"], 2)
        step_wip = round(step_total - step_share, 2)
        total_wip = round(total_wip + step_wip, 2)
        rows.append(["合计", format_money(step_total), "—", "—", format_money(step_share), format_money(step_wip)])
        results.append({
            "step": step,
            "rows": rows,
            "total_cost": step_total,
            "share": round(step_share, 2),
            "wip": step_wip,
            "material_eq": material_eq,
            "processing_eq": processing_eq,
            "later_wip": later_wip,
        })

    shares = {key: round(value, 2) for key, value in total_shares.items()}
    final_total = round(sum(shares.values()), 2)
    total_cost = round(sum(item["total_cost"] for item in results), 2)
    return {
        "final_qty": final,
        "steps": validated,
        "results": results,
        "shares": shares,
        "final_total": final_total,
        "total_wip": round(total_cost - final_total, 2),
        "total_cost": total_cost,
        "check_wip": total_wip,
    }



def _show_default_steps() -> None:
    """显示分步法内置案例。"""
    headers = ["生产步骤", "产品", "完工数量", "在产品数量", "完工程度", "直接材料（元）", "直接人工（元）", "制造费用（元）"]
    rows = []
    for step in DEFAULT_STEPS:
        rows.append([
            step["name"], step["product"], f"{step['completed_qty']:,.0f}", f"{step['wip_qty']:,.0f}",
            format_percent(step["completion"]), format_money(step["material"]), format_money(step["labor"]), format_money(step["overhead"]),
        ])
    print_table(headers, rows, "内置两步骤案例资料")


def _read_steps() -> List[Dict[str, Any]]:
    """读取逐步结转分步法步骤数据。"""
    _show_default_steps()
    if input_yes_no("是否使用上述内置案例", True):
        return [dict(step) for step in DEFAULT_STEPS]
    count = input_int("生产步骤数", 2, min_value=2, max_value=4, name="生产步骤数")
    steps = []
    for i in range(count):
        default = DEFAULT_STEPS[i] if i < len(DEFAULT_STEPS) else {
            "name": f"第{i + 1}车间", "product": f"第{i + 1}步骤产品", "completed_qty": 600.0,
            "wip_qty": 100.0, "completion": 0.5, "material": 0.0, "labor": 15000.0, "overhead": 10000.0,
        }
        name = input_text(f"第{i + 1}步骤名称", default["name"])
        product = input_text(f"{name}的产品名称", default["product"])
        completed = input_float(f"{name}完工数量", default["completed_qty"], min_value=0.0, name="完工数量")
        wip = input_float(f"{name}在产品数量", default["wip_qty"], min_value=0.0, name="在产品数量")
        completion = input_percent(f"{name}在产品完工程度", default["completion"] * 100, min_percent=0.0, max_percent=100.0)
        material = input_float(f"{name}直接材料（元，半成品步骤通常为0）", default["material"], min_value=0.0, name="直接材料")
        labor = input_float(f"{name}直接人工（元）", default["labor"], min_value=0.0, name="直接人工")
        overhead = input_float(f"{name}制造费用（元）", default["overhead"], min_value=0.0, name="制造费用")
        steps.append({
            "name": name, "product": product, "completed_qty": completed, "wip_qty": wip,
            "completion": completion, "material": material, "labor": labor, "overhead": overhead,
        })
    return steps


def _read_parallel_steps() -> Tuple[float, List[Dict[str, Any]]]:
    """读取平行结转分步法数据。"""
    _show_default_steps()
    final_qty = input_float("最终产成品数量", 700.0, min_value=0.0, name="最终产成品数量")
    if input_yes_no("是否使用上述内置案例（忽略各步骤完工数量）", True):
        steps = [
            {
                "name": step["name"], "wip_qty": step["wip_qty"], "completion": step["completion"],
                "material": step["material"], "labor": step["labor"], "overhead": step["overhead"],
            }
            for step in DEFAULT_STEPS
        ]
        return final_qty, steps
    count = input_int("生产步骤数", 2, min_value=2, max_value=4, name="生产步骤数")
    steps = []
    for i in range(count):
        default = DEFAULT_STEPS[i] if i < len(DEFAULT_STEPS) else {
            "name": f"第{i + 1}车间", "wip_qty": 100.0, "completion": 0.5,
            "material": 0.0, "labor": 15000.0, "overhead": 10000.0,
        }
        name = input_text(f"第{i + 1}步骤名称", default["name"])
        wip = input_float(f"{name}在产品数量", default["wip_qty"], min_value=0.0, name="在产品数量")
        completion = input_percent(f"{name}在产品完工程度", default["completion"] * 100, min_percent=0.0, max_percent=100.0)
        material = input_float(f"{name}直接材料（元）", default["material"], min_value=0.0, name="直接材料")
        labor = input_float(f"{name}直接人工（元）", default["labor"], min_value=0.0, name="直接人工")
        overhead = input_float(f"{name}制造费用（元）", default["overhead"], min_value=0.0, name="制造费用")
        steps.append({
            "name": name, "wip_qty": wip, "completion": completion,
            "material": material, "labor": labor, "overhead": overhead,
        })
    return final_qty, steps



def run_comprehensive() -> None:
    """逐步结转分步法——综合结转（含成本还原）。"""
    print_heading("第八章 分步法：逐步结转分步法——综合结转", "-")
    steps = _read_steps()
    result = step_comprehensive(steps)
    question = (
        "某企业生产甲产品经过两个或两个以上生产步骤，第一步骤生产半成品，第二步骤继续加工为产成品。"
        "半成品成本采用综合结转法转入下一步骤。各步骤完工数量、在产品数量、完工程度及本月费用如下表。"
        "要求编制各步骤产品成本计算单，进行成本还原，并编制结转分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "某步骤加工费约当产量 = 完工数量 + 在产品数量 × 完工程度",
        "半成品（直接材料）约当产量 = 完工数量 + 在产品数量（半成品一次投入）",
        "某项费用分配率 = 该项费用总额 ÷ 该项约当产量",
        "完工半成品成本转入下一步骤，最终步骤完工成本转入库存商品",
        "成本还原率 = 产成品所耗半成品成本 ÷ 上一步骤所产半成品总成本",
        "还原后某成本项目 = 该成本项目原始成本 × 成本还原率",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps_lines = []
    for i, item in enumerate(result["results"]):
        step = item["step"]
        steps_lines.append(
            f"{step['name']}（{step['product']}）：完工 {step['completed_qty']:,.2f} 件，在产品 {step['wip_qty']:,.2f} 件，"
            f"完工程度 {format_percent(step['completion'])}，加工费约当产量 {item['processing_eq']:,.2f}。"
        )
        if i > 0:
            steps_lines.append(f"    从上一步骤转入半成品成本 {format_money(result['completed_totals'][i - 1])} 元。")
        for row in item["rows"][:-1]:
            steps_lines.append(f"    {row[0]}：分配率 {row[3]}，完工成本 {row[4]} 元，在产品成本 {row[5]} 元。")
        steps_lines.append(f"    本步骤完工成本合计 {format_money(item['completed_total'])} 元，期末在产品成本 {format_money(item['wip_total'])} 元。")
    final_semi = result["before_restoration"]["半成品"]
    if len(steps) > 1:
        previous_total = result["completed_totals"][-2]
        steps_lines.append(
            f"成本还原：产成品所耗半成品成本 {format_money(final_semi)} 元，上一步骤完工半成品总成本 {format_money(previous_total)} 元，"
            f"还原率 = {format_money(final_semi)} ÷ {format_money(previous_total)} = {final_semi / previous_total:.6f}。"
        )
        for key in ("直接材料", "直接人工", "制造费用"):
            steps_lines.append(f"    还原后{key} = {format_money(result['restored'][key])} 元。")
    else:
        steps_lines.append("单步骤生产无需成本还原。")
    print_steps(steps_lines)

    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = []
    for item in result["results"]:
        headers = ["成本项目", "费用总额（元）", "约当产量/数量", "分配率", "完工产品成本（元）", "期末在产品成本（元）"]
        print_table(headers, item["rows"], f"{item['step']['name']}产品成本计算单（综合结转）")
        tables.append((f"{item['step']['name']}产品成本计算单（综合结转）", headers, item["rows"]))

    restoration_headers = ["成本项目", "还原前成本（元）", "半成品还原（元）", "还原后成本（元）"]
    print_table(restoration_headers, result["restoration_rows"], "产成品成本还原计算表")
    tables.append(("产成品成本还原计算表", restoration_headers, result["restoration_rows"]))

    final_headers = ["成本项目", "还原后金额（元）", "单位成本（元/件）"]
    final_qty = steps[-1]["completed_qty"]
    final_rows = [
        ["直接材料", format_money(result["restored"]["直接材料"]), format_money(result["restored"]["直接材料"] / final_qty)],
        ["直接人工", format_money(result["restored"]["直接人工"]), format_money(result["restored"]["直接人工"] / final_qty)],
        ["制造费用", format_money(result["restored"]["制造费用"]), format_money(result["restored"]["制造费用"] / final_qty)],
        ["合计", format_money(result["restored_total"]), format_money(result["restored_total"] / final_qty)],
    ]
    print_table(final_headers, final_rows, "还原后产成品成本计算单")
    tables.append(("还原后产成品成本计算单", final_headers, final_rows))

    journal = []
    for i in range(len(steps) - 1):
        journal.append(f"借：生产成本——基本生产成本（{steps[i + 1]['name']}）     {format_money(result['completed_totals'][i])}")
        journal.append(f"贷：生产成本——基本生产成本（{steps[i]['name']}）     {format_money(result['completed_totals'][i])}")
    journal.append(f"借：库存商品——{steps[-1]['product']}     {format_money(result['final_total'])}")
    journal.append(f"贷：生产成本——基本生产成本（{steps[-1]['name']}）     {format_money(result['final_total'])}")
    print_journal(journal)

    summary = [
        f"最终产成品成本（还原前）{format_money(result['final_total'])} 元，成本还原后仍为 {format_money(result['restored_total'])} 元。",
        "综合结转法下，半成品成本以“半成品”综合项目结转，最终产成品成本需要进行成本还原，才能反映原始成本结构。",
        "成本还原只用于成本分析，不改变产成品总成本，也不需要单独编制会计分录。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第八章 分步法",
        "逐步结转分步法——综合结转（含成本还原）",
        question=question,
        formulas=formulas,
        steps=steps_lines,
        tables=tables,
        journal=journal,
        summary=summary,
        conclusion=f"产成品成本 {format_money(result['final_total'])} 元，还原后直接材料 {format_money(result['restored']['直接材料'])} 元。",
    )



def run_itemized() -> None:
    """逐步结转分步法——分项结转。"""
    print_heading("第八章 分步法：逐步结转分步法——分项结转", "-")
    steps = _read_steps()
    result = step_itemized(steps)
    question = (
        "某企业生产甲产品经过多个生产步骤，半成品成本按直接材料、直接人工、制造费用分项结转至下一步骤。"
        "各步骤完工数量、在产品数量、完工程度及本月费用如下表。要求编制各步骤产品成本计算单，"
        "计算最终产成品成本并编制结转分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "上一步骤转入成本按实物数量比例分配（半成品已在上一阶段完整加工）；",
        "本步骤新发生加工费按本步骤约当产量分配；",
        "某成本项目完工成本 = 完工数量 ×（上步转入该项目分配率 + 本步发生该项目分配率）；",
        "分项结转法下，最终产成品成本仍保留原始成本项目，一般不需要成本还原。",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps_lines = []
    for i, item in enumerate(result["results"]):
        step = item["step"]
        steps_lines.append(
            f"{step['name']}（{step['product']}）：完工 {step['completed_qty']:,.2f} 件，在产品 {step['wip_qty']:,.2f} 件，"
            f"完工程度 {format_percent(step['completion'])}。"
        )
        if i > 0:
            steps_lines.append("    上一步骤转入成本按成本项目分别计入本步骤直接材料、直接人工、制造费用。")
        for row in item["rows"][:-1]:
            steps_lines.append(f"    {row[0]}：分配率 {row[3]}，完工成本 {row[4]} 元，在产品成本 {row[5]} 元。")
        steps_lines.append(f"    本步骤完工成本 {format_money(item['completed_total'])} 元，期末在产品成本 {format_money(item['wip_total'])} 元。")
    print_steps(steps_lines)

    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = []
    for item in result["results"]:
        headers = ["成本项目", "费用总额（元）", "约当产量/数量", "分配率", "完工产品成本（元）", "期末在产品成本（元）"]
        print_table(headers, item["rows"], f"{item['step']['name']}产品成本计算单（分项结转）")
        tables.append((f"{item['step']['name']}产品成本计算单（分项结转）", headers, item["rows"]))

    final_components = result["final_components"]
    final_qty = steps[-1]["completed_qty"]
    final_headers = ["成本项目", "完工总成本（元）", "单位成本（元/件）"]
    final_rows = [
        ["直接材料", format_money(final_components["直接材料"]), format_money(final_components["直接材料"] / final_qty)],
        ["直接人工", format_money(final_components["直接人工"]), format_money(final_components["直接人工"] / final_qty)],
        ["制造费用", format_money(final_components["制造费用"]), format_money(final_components["制造费用"] / final_qty)],
        ["合计", format_money(result["final_total"]), format_money(result["final_total"] / final_qty)],
    ]
    print_table(final_headers, final_rows, "分项结转法最终产成品成本计算单")
    tables.append(("分项结转法最终产成品成本计算单", final_headers, final_rows))

    journal = []
    for i in range(len(steps) - 1):
        journal.append(f"借：生产成本——基本生产成本（{steps[i + 1]['name']}）     {format_money(result['results'][i]['completed_total'])}")
        journal.append(f"贷：生产成本——基本生产成本（{steps[i]['name']}）     {format_money(result['results'][i]['completed_total'])}")
    journal.append(f"借：库存商品——{steps[-1]['product']}     {format_money(result['final_total'])}")
    journal.append(f"贷：生产成本——基本生产成本（{steps[-1]['name']}）     {format_money(result['final_total'])}")
    print_journal(journal)

    summary = [
        f"分项结转法最终产成品成本 {format_money(result['final_total'])} 元，其中直接材料 {format_money(final_components['直接材料'])} 元。",
        "分项结转法下，半成品成本按成本项目结转，最终产成品成本不需要进行综合成本还原。",
        "本工具按“上步转入成本按实物数量比例分配、本步加工费按约当产量分配”的教学口径计算。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第八章 分步法",
        "逐步结转分步法——分项结转",
        question=question,
        formulas=formulas,
        steps=steps_lines,
        tables=tables,
        journal=journal,
        summary=summary,
        conclusion=f"分项结转法最终产成品成本 {format_money(result['final_total'])} 元。",
    )



def run_parallel() -> None:
    """平行结转分步法。"""
    print_heading("第八章 分步法：平行结转分步法", "-")
    final_qty, steps = _read_parallel_steps()
    result = parallel_method(final_qty, steps)
    question = (
        f"某企业生产甲产品经过多个生产步骤，采用平行结转分步法。最终产成品数量为 {final_qty:,.2f} 件，"
        "各步骤在产品数量、完工程度及本步骤生产费用如下表。要求计算各步骤应计入最终产成品的成本份额，"
        "以及广义在产品成本，并编制产成品入库分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "某步骤约当产量 = 最终产成品数量 + 本步骤在产品约当产量 + 后续步骤在产品数量",
        "本步骤在产品约当产量 = 本步骤在产品数量 × 本步骤完工程度",
        "某成本项目分配率 = 本步骤该项费用 ÷ 该步骤约当产量",
        "应计入产成品份额 = 最终产成品数量 × 分配率",
        "广义在产品成本 = 本步骤费用总额 - 应计入产成品份额",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps_lines = []
    for item in result["results"]:
        steps_lines.append(
            f"{item['step']['name']}：后续步骤在产品 {item['later_wip']:,.2f} 件；加工费约当产量 {item['processing_eq']:,.2f}；"
            f"应计入产成品份额 {format_money(item['share'])} 元；广义在产品成本 {format_money(item['wip'])} 元。"
        )
    steps_lines.append(
        f"产成品成本合计 = 直接材料 {format_money(result['shares']['直接材料'])} + 直接人工 {format_money(result['shares']['直接人工'])} + "
        f"制造费用 {format_money(result['shares']['制造费用'])} = {format_money(result['final_total'])} 元。"
    )
    print_steps(steps_lines)

    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = []
    headers = ["成本项目", "本步骤费用（元）", "约当产量", "分配率", "产成品份额（元）", "广义在产品成本（元）"]
    for item in result["results"]:
        print_table(headers, item["rows"], f"{item['step']['name']}成本份额计算表")
        tables.append((f"{item['step']['name']}成本份额计算表", headers, item["rows"]))

    final_headers = ["成本项目", "产成品成本（元）", "单位成本（元/件）"]
    final_rows = [
        ["直接材料", format_money(result["shares"]["直接材料"]), format_money(result["shares"]["直接材料"] / final_qty)],
        ["直接人工", format_money(result["shares"]["直接人工"]), format_money(result["shares"]["直接人工"] / final_qty)],
        ["制造费用", format_money(result["shares"]["制造费用"]), format_money(result["shares"]["制造费用"] / final_qty)],
        ["合计", format_money(result["final_total"]), format_money(result["final_total"] / final_qty)],
    ]
    print_table(final_headers, final_rows, "平行结转法产成品成本汇总表")
    tables.append(("平行结转法产成品成本汇总表", final_headers, final_rows))

    wip_headers = ["项目", "金额（元）"]
    wip_rows = [
        ["各步骤费用总额", format_money(result["total_cost"])],
        ["产成品成本", format_money(result["final_total"])],
        ["广义在产品成本合计", format_money(result["total_wip"])],
        ["平衡校验（费用总额 - 产成品成本）", format_money(result["total_cost"] - result["final_total"])],
    ]
    print_table(wip_headers, wip_rows, "平行结转法成本平衡表")
    tables.append(("平行结转法成本平衡表", wip_headers, wip_rows))

    journal = [f"借：库存商品——甲产品     {format_money(result['final_total'])}"]
    for item in result["results"]:
        journal.append(f"贷：生产成本——基本生产成本（{item['step']['name']}）     {format_money(item['share'])}")
    print_journal(journal)

    summary = [
        "平行结转分步法下，各步骤只计算应计入最终产成品的“份额”，半成品成本不逐步结转。",
        f"最终产成品成本 {format_money(result['final_total'])} 元，广义在产品成本 {format_money(result['total_wip'])} 元，二者之和等于各步骤费用总额。",
        "“广义在产品”包括本步骤正在加工的在产品、本步骤已完工但尚未形成最终产成品的半成品，以及后续步骤的在产品。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第八章 分步法",
        "平行结转分步法（广义在产品）",
        question=question,
        formulas=formulas,
        steps=steps_lines,
        tables=tables,
        journal=journal,
        summary=summary,
        conclusion=f"产成品成本 {format_money(result['final_total'])} 元，广义在产品成本 {format_money(result['total_wip'])} 元。",
    )



def show_comparison() -> None:
    """分步法各方法比较。"""
    print_heading("第八章 分步法：方法比较与要点", "-")
    headers = ["方法", "半成品成本结转", "是否需成本还原", "在产品口径", "适用情形"]
    rows = [
        ["逐步结转——综合结转", "以“半成品”综合项目结转", "需要", "本步骤在产品", "需要逐步控制半成品成本"],
        ["逐步结转——分项结转", "按成本项目分项结转", "一般不需要", "本步骤在产品", "需要保留原始成本项目结构"],
        ["平行结转", "不结转半成品成本，只计算份额", "不需要", "广义在产品", "半成品不对外销售、管理上要求平行汇总"],
    ]
    print_table(headers, rows, "分步法方法比较")
    print_summary(
        [
            "综合结转法便于半成品成本日常管理，但最终产成品成本需要进行成本还原。",
            "分项结转法保留了原始成本项目，但转账工作量较大。",
            "平行结转法不逐步结转半成品成本，各步骤只计算应计入产成品的份额，关键是正确确定广义在产品。",
        ],
        "学习提示",
    )


def run() -> None:
    """第八章菜单。"""
    options = [
        ("1", "逐步结转分步法——综合结转（含成本还原）", run_comprehensive),
        ("2", "逐步结转分步法——分项结转", run_itemized),
        ("3", "平行结转分步法（广义在产品）", run_parallel),
        ("4", "分步法方法比较与要点", show_comparison),
    ]
    run_menu("第八章 产品成本计算——分步法", options, back_text="返回主菜单")

