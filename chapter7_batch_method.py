"""第七章 产品成本计算——分批法。

分批法以产品批别为成本计算对象，适用于单件、小批生产或按订单组织生产的企业。
本章实现：
1. 普通分批法：各批产品直接费用直接计入，制造费用按生产工时分配；完工批次结转库存商品；
2. 简化分批法（累计间接费用分配法）：只对完工批次分配累计间接费用，未完工批次保留直接费用；
3. 两种方法比较。
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

import export
from utils import (
    ValidationError,
    allocate_amount,
    format_money,
    input_float,
    input_int,
    input_text,
    input_yes_no,
    print_heading,
    print_journal,
    print_steps,
    print_subheading,
    print_summary,
    print_table,
    require_nonnegative,
    run_menu,
    safe_div,
)


def normal_batch(
    batches: Sequence[Dict[str, Any]],
    overhead_total: Any,
    basis: str = "labor_hours",
) -> Dict[str, Any]:
    """普通分批法。

    batches 中每批包含：name、product、quantity、direct_material、direct_labor、
    labor_hours、completed（True/False）、completed_qty（完工数量）。
    制造费用按各批生产工时分配，未完工批次也负担制造费用并保留为在产品。
    """
    if not batches:
        raise ValidationError("至少需要一个产品批次。")
    overhead = require_nonnegative(overhead_total, "制造费用总额")
    names = [str(batch.get("name") or f"批次{i + 1}") for i, batch in enumerate(batches)]
    hours = [require_nonnegative(batch.get("labor_hours"), f"{names[i]}的生产工时") for i, batch in enumerate(batches)]
    allocations, total_hours = allocate_amount(overhead, hours, labels=names)
    rate = safe_div(overhead, total_hours, "制造费用分配率")
    results = []
    completed_total = 0.0
    wip_total = 0.0
    for i, batch in enumerate(batches):
        material = require_nonnegative(batch.get("direct_material"), f"{names[i]}的直接材料")
        labor = require_nonnegative(batch.get("direct_labor"), f"{names[i]}的直接人工")
        total = round(material + labor + allocations[i], 2)
        is_completed = bool(batch.get("completed"))
        completed_qty = require_nonnegative(batch.get("completed_qty"), f"{names[i]}的完工数量")
        if is_completed:
            if completed_qty <= 0:
                raise ValidationError(f"{names[i]}已标记完工，完工数量必须大于 0。")
            unit_cost = round(total / completed_qty, 6)
            completed_total = round(completed_total + total, 2)
        else:
            unit_cost = None
            wip_total = round(wip_total + total, 2)
        results.append({
            "name": names[i],
            "product": str(batch.get("product") or names[i]),
            "material": material,
            "labor": labor,
            "hours": hours[i],
            "overhead": allocations[i],
            "total": total,
            "completed": is_completed,
            "completed_qty": completed_qty,
            "unit_cost": unit_cost,
        })
    return {
        "rows": results,
        "overhead": overhead,
        "total_hours": total_hours,
        "rate": rate,
        "completed_total": completed_total,
        "wip_total": wip_total,
        "total": round(completed_total + wip_total, 2),
    }


def simplified_batch(
    batches: Sequence[Dict[str, Any]],
    cumulative_overhead: Any,
) -> Dict[str, Any]:
    """简化分批法（累计间接费用分配法）。

    累计间接费用分配率 = 累计制造费用 ÷ 累计生产工时；
    只对已完工批次按其累计工时分配间接费用；未完工批次只保留直接材料、直接人工。
    """
    if not batches:
        raise ValidationError("至少需要一个产品批次。")
    overhead = require_nonnegative(cumulative_overhead, "累计制造费用")
    names = [str(batch.get("name") or f"批次{i + 1}") for i, batch in enumerate(batches)]
    hours = [require_nonnegative(batch.get("cumulative_hours"), f"{names[i]}的累计工时") for i, batch in enumerate(batches)]
    total_hours = sum(hours)
    if total_hours <= 0:
        raise ValidationError("累计生产工时合计必须大于 0。")
    rate = safe_div(overhead, total_hours, "累计间接费用分配率")
    results = []
    completed_total = 0.0
    wip_direct_total = 0.0
    allocated_total = 0.0
    for i, batch in enumerate(batches):
        material = require_nonnegative(batch.get("direct_material"), f"{names[i]}的累计直接材料")
        labor = require_nonnegative(batch.get("direct_labor"), f"{names[i]}的累计直接人工")
        is_completed = bool(batch.get("completed"))
        completed_qty = require_nonnegative(batch.get("completed_qty"), f"{names[i]}的完工数量")
        if is_completed:
            if completed_qty <= 0:
                raise ValidationError(f"{names[i]}已标记完工，完工数量必须大于 0。")
            allocated = round(hours[i] * rate, 2)
            total = round(material + labor + allocated, 2)
            unit_cost = round(total / completed_qty, 6)
            completed_total = round(completed_total + total, 2)
            allocated_total = round(allocated_total + allocated, 2)
            wip_direct = 0.0
        else:
            allocated = 0.0
            total = round(material + labor, 2)
            unit_cost = None
            wip_direct = total
            wip_direct_total = round(wip_direct_total + total, 2)
        results.append({
            "name": names[i],
            "product": str(batch.get("product") or names[i]),
            "material": material,
            "labor": labor,
            "hours": hours[i],
            "overhead": allocated,
            "total": total,
            "completed": is_completed,
            "completed_qty": completed_qty,
            "unit_cost": unit_cost,
            "wip_direct": wip_direct,
        })
    unallocated_overhead = round(overhead - allocated_total, 2)
    return {
        "rows": results,
        "overhead": overhead,
        "total_hours": total_hours,
        "rate": rate,
        "allocated_total": allocated_total,
        "unallocated_overhead": unallocated_overhead,
        "completed_total": completed_total,
        "wip_direct_total": wip_direct_total,
        "wip_total_with_overhead": round(wip_direct_total + unallocated_overhead, 2),
        "total": round(completed_total + wip_direct_total + unallocated_overhead, 2),
    }


def _read_batches(*, simplified: bool) -> List[Dict[str, Any]]:
    """读取批次数据，默认使用内置模拟案例。"""
    count = input_int("产品批次数", 3, min_value=1, max_value=20, name="产品批次数")
    if simplified:
        defaults = [
            {"name": "701批", "product": "A产品", "direct_material": 40000.0, "direct_labor": 18000.0, "cumulative_hours": 2000.0, "completed": True, "completed_qty": 100.0},
            {"name": "702批", "product": "B产品", "direct_material": 30000.0, "direct_labor": 14000.0, "cumulative_hours": 1500.0, "completed": True, "completed_qty": 80.0},
            {"name": "703批", "product": "C产品", "direct_material": 25000.0, "direct_labor": 12000.0, "cumulative_hours": 1000.0, "completed": False, "completed_qty": 0.0},
        ]
    else:
        defaults = [
            {"name": "601批", "product": "甲产品", "direct_material": 30000.0, "direct_labor": 12000.0, "labor_hours": 1500.0, "completed": True, "completed_qty": 20.0},
            {"name": "602批", "product": "乙产品", "direct_material": 24000.0, "direct_labor": 10000.0, "labor_hours": 1200.0, "completed": True, "completed_qty": 15.0},
            {"name": "603批", "product": "丙产品", "direct_material": 18000.0, "direct_labor": 8000.0, "labor_hours": 800.0, "completed": False, "completed_qty": 0.0},
        ]
    batches = []
    for i in range(count):
        item = defaults[i] if i < len(defaults) else {
            "name": f"{700 + i}批", "product": f"产品{i + 1}", "direct_material": 20000.0,
            "direct_labor": 8000.0, "labor_hours": 800.0, "cumulative_hours": 800.0,
            "completed": False, "completed_qty": 0.0,
        }
        name = input_text(f"第{i + 1}个批次号", item["name"])
        product = input_text(f"{name}的产品名称", item["product"])
        material = input_float(f"{name}累计直接材料（元）", item["direct_material"], min_value=0.0, name="直接材料")
        labor = input_float(f"{name}累计直接人工（元）", item["direct_labor"], min_value=0.0, name="直接人工")
        if simplified:
            hours = input_float(f"{name}累计生产工时", item["cumulative_hours"], min_value=0.0, name="累计工时")
        else:
            hours = input_float(f"{name}本月生产工时", item["labor_hours"], min_value=0.0, name="生产工时")
        completed = input_yes_no(f"{name}是否已全部完工", bool(item["completed"]))
        completed_qty = input_float(f"{name}完工数量", item["completed_qty"], min_value=0.0, name="完工数量") if completed else 0.0
        batch = {
            "name": name,
            "product": product,
            "direct_material": material,
            "direct_labor": labor,
            "completed": completed,
            "completed_qty": completed_qty,
        }
        if simplified:
            batch["cumulative_hours"] = hours
        else:
            batch["labor_hours"] = hours
        batches.append(batch)
    return batches



def run_normal() -> None:
    """普通分批法。"""
    print_heading("第七章 分批法：普通分批法", "-")
    overhead = input_float("本月制造费用总额（元）", 14000.0, min_value=0.0, name="制造费用")
    batches = _read_batches(simplified=False)
    result = normal_batch(batches, overhead)
    question = (
        f"某企业按客户订单组织生产，本月有 {len(batches)} 个批次，制造费用总额 {format_money(result['overhead'])} 元，"
        "按各批生产工时分配。部分批次已完工，部分批次尚未完工。要求计算各批产品成本、完工批次单位成本和期末在产品成本。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "制造费用分配率 = 本月制造费用总额 ÷ 各批生产工时合计",
        "某批应分配制造费用 = 该批生产工时 × 制造费用分配率",
        "某批产品总成本 = 直接材料 + 直接人工 + 分配的制造费用",
        "完工批次单位成本 = 该批总成本 ÷ 该批完工数量",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"各批生产工时合计 = {result['total_hours']:,.2f}。",
        f"制造费用分配率 = {format_money(result['overhead'])} ÷ {result['total_hours']:,.2f} = {result['rate']:.6f} 元/工时。",
    ]
    for row in result["rows"]:
        steps.append(
            f"{row['name']}（{row['product']}）：制造费用 = {row['hours']:,.2f} × {result['rate']:.6f} = "
            f"{format_money(row['overhead'])} 元；总成本 = {format_money(row['material'])} + {format_money(row['labor'])} + "
            f"{format_money(row['overhead'])} = {format_money(row['total'])} 元；"
            + (f"单位成本 = {format_money(row['unit_cost'])} 元/件。" if row["completed"] else "未完工，全部成本保留为在产品。")
        )
    print_steps(steps)

    headers = ["批次号", "产品", "直接材料（元）", "直接人工（元）", "生产工时", "制造费用（元）", "总成本（元）", "完工数量", "单位成本（元/件）"]
    rows = []
    for row in result["rows"]:
        rows.append([
            row["name"], row["product"], format_money(row["material"]), format_money(row["labor"]), f"{row['hours']:,.2f}",
            format_money(row["overhead"]), format_money(row["total"]), f"{row['completed_qty']:,.2f}",
            format_money(row["unit_cost"]) if row["unit_cost"] is not None else "在产品",
        ])
    rows.append(["合计", "—", format_money(sum(row["material"] for row in result["rows"])), format_money(sum(row["labor"] for row in result["rows"])), f"{result['total_hours']:,.2f}", format_money(result["overhead"]), format_money(result["total"]), "—", "—"])
    print_table(headers, rows, "普通分批法产品成本计算表")

    journal = ["借：生产成本——基本生产成本"]
    for row in result["rows"]:
        journal.append(f"    ——{row['name']}（{row['product']}）     {format_money(row['overhead'])}")
    journal.append(f"贷：制造费用     {format_money(result['overhead'])}")
    for row in result["rows"]:
        if row["completed"]:
            journal.append(f"借：库存商品——{row['product']}     {format_money(row['total'])}")
            journal.append(f"贷：生产成本——基本生产成本（{row['name']}）     {format_money(row['total'])}")
    print_journal(journal)

    summary = [
        f"完工批次成本合计 {format_money(result['completed_total'])} 元，未完工批次在产品成本 {format_money(result['wip_total'])} 元。",
        "普通分批法下，制造费用按当期生产工时在各批产品之间分配，未完工批次也负担制造费用。",
        "完工批次验收入库后，其成本从“生产成本”转入“库存商品”；未完工批次留在生产成本账户。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第七章 分批法",
        "普通分批法",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("普通分批法产品成本计算表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"完工批次成本 {format_money(result['completed_total'])} 元，未完工批次成本 {format_money(result['wip_total'])} 元。",
    )



def run_simplified() -> None:
    """简化分批法（累计间接费用分配法）。"""
    print_heading("第七章 分批法：简化分批法（累计间接费用分配法）", "-")
    overhead = input_float("累计制造费用（元）", 18000.0, min_value=0.0, name="累计制造费用")
    batches = _read_batches(simplified=True)
    result = simplified_batch(batches, overhead)
    question = (
        f"某企业采用简化分批法，本月累计制造费用 {format_money(result['overhead'])} 元。各批产品的累计直接材料、"
        "累计直接人工和累计生产工时如下。要求计算累计间接费用分配率，只对已完工批次分配间接费用，"
        "并计算完工批次成本、未完工批次在产品成本及二级账余额。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "累计间接费用分配率 = 累计制造费用 ÷ 各批累计生产工时合计",
        "完工批次应分配间接费用 = 该批累计工时 × 累计间接费用分配率",
        "完工批次总成本 = 累计直接材料 + 累计直接人工 + 分配的累计间接费用",
        "未完工批次只保留直接材料、直接人工；未分配的累计间接费用留在基本生产成本二级账。",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"累计生产工时合计 = {result['total_hours']:,.2f}。",
        f"累计间接费用分配率 = {format_money(result['overhead'])} ÷ {result['total_hours']:,.2f} = {result['rate']:.6f} 元/工时。",
    ]
    for row in result["rows"]:
        if row["completed"]:
            steps.append(
                f"{row['name']}（{row['product']}，完工）：分配间接费用 = {row['hours']:,.2f} × {result['rate']:.6f} = "
                f"{format_money(row['overhead'])} 元；总成本 = {format_money(row['total'])} 元；单位成本 = {format_money(row['unit_cost'])} 元/件。"
            )
        else:
            steps.append(
                f"{row['name']}（{row['product']}，未完工）：不分配间接费用，直接费用 {format_money(row['total'])} 元保留为在产品。"
            )
    steps.append(f"已分配累计间接费用 = {format_money(result['allocated_total'])} 元；未分配累计间接费用 = {format_money(result['unallocated_overhead'])} 元。")
    print_steps(steps)

    headers = ["批次号", "产品", "累计材料（元）", "累计人工（元）", "累计工时", "分配间接费用（元）", "完工成本（元）", "在产品直接成本（元）", "完工数量", "单位成本（元/件）"]
    rows = []
    for row in result["rows"]:
        rows.append([
            row["name"], row["product"], format_money(row["material"]), format_money(row["labor"]), f"{row['hours']:,.2f}",
            format_money(row["overhead"]), format_money(row["total"]) if row["completed"] else "—",
            format_money(row["wip_direct"]) if not row["completed"] else "—",
            f"{row['completed_qty']:,.2f}", format_money(row["unit_cost"]) if row["unit_cost"] is not None else "—",
        ])
    print_table(headers, rows, "简化分批法产品成本计算表")

    balance_headers = ["项目", "金额（元）"]
    balance_rows = [
        ["累计制造费用", format_money(result["overhead"])],
        ["已分配累计间接费用", format_money(result["allocated_total"])],
        ["未分配累计间接费用", format_money(result["unallocated_overhead"])],
        ["完工批次成本合计", format_money(result["completed_total"])],
        ["未完工批次直接成本", format_money(result["wip_direct_total"])],
        ["期末在产品成本（含未分配间接费用）", format_money(result["wip_total_with_overhead"])],
        ["成本合计", format_money(result["total"])],
    ]
    print_table(balance_headers, balance_rows, "基本生产成本二级账平衡表")

    journal = ["借：生产成本——基本生产成本（完工批次）"]
    for row in result["rows"]:
        if row["completed"]:
            journal.append(f"    ——{row['name']}（{row['product']}）     {format_money(row['overhead'])}")
    journal.append(f"贷：制造费用     {format_money(result['allocated_total'])}")
    for row in result["rows"]:
        if row["completed"]:
            journal.append(f"借：库存商品——{row['product']}     {format_money(row['total'])}")
            journal.append(f"贷：生产成本——基本生产成本（{row['name']}）     {format_money(row['total'])}")
    print_journal(journal)

    summary = [
        f"累计间接费用分配率 {result['rate']:.6f} 元/工时，已分配 {format_money(result['allocated_total'])} 元。",
        f"未分配累计间接费用 {format_money(result['unallocated_overhead'])} 元留在基本生产成本二级账，与未完工批次直接成本共同构成期末在产品成本。",
        "简化分批法适用于批数较多、生产周期较长、间接费用比重较大的企业，可简化间接费用分配工作。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第七章 分批法",
        "简化分批法（累计间接费用分配法）",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[
            ("简化分批法产品成本计算表", headers, rows),
            ("基本生产成本二级账平衡表", balance_headers, balance_rows),
        ],
        journal=journal,
        summary=summary,
        conclusion=f"完工批次成本 {format_money(result['completed_total'])} 元，未分配间接费用 {format_money(result['unallocated_overhead'])} 元。",
    )



def show_comparison() -> None:
    """普通分批法与简化分批法比较。"""
    print_heading("第七章 分批法：两种方法比较", "-")
    headers = ["比较项目", "普通分批法", "简化分批法"]
    rows = [
        ["成本计算对象", "各产品批别", "各产品批别"],
        ["制造费用分配", "各批均按当月工时分配", "只对完工批次按累计工时分配"],
        ["未完工批次", "负担制造费用，计入在产品", "只保留直接材料、直接人工"],
        ["核算工作量", "较大", "较小"],
        ["适用条件", "批数较少、生产周期较短", "批数较多、生产周期较长、间接费用比重大"],
        ["成本信息详细程度", "较详细", "相对简化"],
    ]
    print_table(headers, rows, "普通分批法与简化分批法比较")
    print_summary(
        [
            "简化分批法下，未完工批次不分摊间接费用，未分配的累计间接费用留在基本生产成本二级账。",
            "两种方法都应保证完工产品成本与期末在产品成本之和等于生产费用总额。",
        ],
        "核对提示",
    )


def run() -> None:
    """第七章菜单。"""
    options = [
        ("1", "普通分批法", run_normal),
        ("2", "简化分批法（累计间接费用分配法）", run_simplified),
        ("3", "两种分批法比较", show_comparison),
    ]
    run_menu("第七章 产品成本计算——分批法", options, back_text="返回主菜单")

