"""第六章 产品成本计算——品种法。

品种法以产品品种为成本计算对象，适用于大量大批单步骤生产，或管理上不要求
分步骤计算成本的多步骤生产。本章实现：
1. 单一品种品种法：要素费用归集 → 生产费用在完工产品与在产品之间分配 → 完工结转；
2. 多品种品种法：共同费用按材料定额、生产工时等标准分配 → 各产品完工与在产品分配；
3. 品种法核算流程与要点说明。
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

import export
from chapter5_wip_allocation import COST_SHEET_HEADERS, build_cost_sheet
from utils import (
    ValidationError,
    allocate_amount,
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


def single_variety(
    material: float,
    labor: float,
    overhead: float,
    completed_qty: float,
    wip_qty: float,
    completion: float,
    product: str = "甲产品",
) -> Dict[str, Any]:
    """单一品种品种法：按约当产量分配完工产品与在产品成本。"""
    completed = require_positive(completed_qty, "完工产品数量")
    wip = require_nonnegative(wip_qty, "在产品数量")
    degree = require_nonnegative(completion, "在产品完工程度")
    if degree > 1:
        raise ValidationError("在产品完工程度必须在 0%～100% 之间。")
    material_eq = completed + wip  # 原材料在生产开始时一次投入
    processing_eq = equivalent_units(completed, wip, degree)
    material_rate = safe_div(material, material_eq, "材料费用分配率")
    labor_rate = safe_div(labor, processing_eq, "人工费用分配率")
    overhead_rate = safe_div(overhead, processing_eq, "制造费用分配率")
    sheet = build_cost_sheet(
        material, labor, overhead,
        round(material_rate * completed, 2),
        round(labor_rate * completed, 2),
        round(overhead_rate * completed, 2),
        completed,
        product,
    )
    return {
        "sheet": sheet,
        "material_eq": material_eq,
        "processing_eq": processing_eq,
        "material_rate": material_rate,
        "labor_rate": labor_rate,
        "overhead_rate": overhead_rate,
    }


def multi_variety(
    total_material: float,
    total_labor: float,
    total_overhead: float,
    products: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """多品种品种法。

    第一步：材料按“产量 × 单位材料定额”分配；人工和制造费用按生产工时分配。
    第二步：各产品分别按约当产量法分配完工产品与在产品成本。
    """
    if not products:
        raise ValidationError("至少需要一种产品。")
    names: List[str] = []
    outputs: List[float] = []
    wip_qtys: List[float] = []
    completions: List[float] = []
    material_bases: List[float] = []
    hour_bases: List[float] = []
    for index, product in enumerate(products, start=1):
        name = str(product.get("name") or f"产品{index}")
        output = require_positive(product.get("output"), f"{name}的完工产量")
        wip = require_nonnegative(product.get("wip_qty"), f"{name}的在产品数量")
        completion = require_nonnegative(product.get("completion"), f"{name}的完工程度")
        if completion > 1:
            raise ValidationError(f"{name}的完工程度必须在 0%～100% 之间。")
        quota = require_nonnegative(product.get("material_quota"), f"{name}的单位材料定额")
        hours = require_nonnegative(product.get("labor_hours"), f"{name}的生产工时")
        names.append(name)
        outputs.append(output)
        wip_qtys.append(wip)
        completions.append(completion)
        material_bases.append(output * quota)
        hour_bases.append(hours)

    material_allocations, material_base_total = allocate_amount(total_material, material_bases, labels=names)
    labor_allocations, hour_total = allocate_amount(total_labor, hour_bases, labels=names)
    overhead_allocations, _ = allocate_amount(total_overhead, hour_bases, labels=names)
    material_rate = safe_div(total_material, material_base_total, "材料费用分配率")
    labor_rate = safe_div(total_labor, hour_total, "人工费用分配率")
    overhead_rate = safe_div(total_overhead, hour_total, "制造费用分配率")

    product_results: List[Dict[str, Any]] = []
    for i, name in enumerate(names):
        output = outputs[i]
        wip = wip_qtys[i]
        completion = completions[i]
        material_eq = output + wip
        processing_eq = equivalent_units(output, wip, completion)
        product_material_rate = safe_div(material_allocations[i], material_eq, f"{name}材料分配率")
        product_labor_rate = safe_div(labor_allocations[i], processing_eq, f"{name}人工分配率")
        product_overhead_rate = safe_div(overhead_allocations[i], processing_eq, f"{name}制造费用分配率")
        sheet = build_cost_sheet(
            material_allocations[i], labor_allocations[i], overhead_allocations[i],
            round(product_material_rate * output, 2),
            round(product_labor_rate * output, 2),
            round(product_overhead_rate * output, 2),
            output,
            name,
        )
        product_results.append({
            "name": name,
            "output": output,
            "wip_qty": wip,
            "completion": completion,
            "material_base": material_bases[i],
            "hour_base": hour_bases[i],
            "material_alloc": material_allocations[i],
            "labor_alloc": labor_allocations[i],
            "overhead_alloc": overhead_allocations[i],
            "material_eq": material_eq,
            "processing_eq": processing_eq,
            "sheet": sheet,
        })
    total_completed = round(sum(item["sheet"]["completed_total"] for item in product_results), 2)
    total_wip = round(sum(item["sheet"]["wip_total"] for item in product_results), 2)
    return {
        "names": names,
        "material_bases": material_bases,
        "hour_bases": hour_bases,
        "material_base_total": material_base_total,
        "hour_total": hour_total,
        "material_rate": material_rate,
        "labor_rate": labor_rate,
        "overhead_rate": overhead_rate,
        "material_allocations": material_allocations,
        "labor_allocations": labor_allocations,
        "overhead_allocations": overhead_allocations,
        "products": product_results,
        "total_material": total_material,
        "total_labor": total_labor,
        "total_overhead": total_overhead,
        "total_completed": total_completed,
        "total_wip": total_wip,
        "total_cost": round(total_material + total_labor + total_overhead, 2),
    }



def run_single() -> None:
    """单一品种品种法。"""
    print_heading("第六章 品种法：单一品种核算", "-")
    product = input_text("产品名称", "甲产品")
    completed_qty = input_float("完工产品数量", 800.0, min_value=0.0, name="完工产品数量")
    wip_qty = input_float("月末在产品数量", 200.0, min_value=0.0, name="在产品数量")
    completion = input_percent("在产品完工程度", 50.0, min_percent=0.0, max_percent=100.0)
    material = input_float("直接材料（元）", 50000.0, min_value=0.0, name="直接材料")
    labor = input_float("直接人工（元）", 18000.0, min_value=0.0, name="直接人工")
    overhead = input_float("制造费用（元）", 9000.0, min_value=0.0, name="制造费用")
    result = single_variety(material, labor, overhead, completed_qty, wip_qty, completion, product)
    sheet = result["sheet"]

    question = (
        f"某企业采用品种法计算{product}成本。本月完工 {completed_qty:,.2f} 件，月末在产品 {wip_qty:,.2f} 件，"
        f"完工程度 {format_percent(completion)}。原材料在生产开始时一次投入。本月直接材料 {format_money(material)} 元、"
        f"直接人工 {format_money(labor)} 元、制造费用 {format_money(overhead)} 元。"
        "要求完成生产费用归集、完工与在产品分配及完工产品结转。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "材料约当产量 = 完工产品数量 + 在产品数量（材料一次投入）",
        "加工费约当产量 = 完工产品数量 + 在产品数量 × 完工程度",
        "某项费用分配率 = 该项费用总额 ÷ 该项约当产量",
        "完工产品成本 = Σ（完工产品数量 × 各项费用分配率）",
        "单位成本 = 完工产品总成本 ÷ 完工产品数量",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"材料约当产量 = {completed_qty:,.2f} + {wip_qty:,.2f} = {result['material_eq']:,.2f} 件。",
        f"加工费约当产量 = {completed_qty:,.2f} + {wip_qty:,.2f} × {format_percent(completion)} = {result['processing_eq']:,.2f} 件。",
        f"材料分配率 = {format_money(material)} ÷ {result['material_eq']:,.2f} = {result['material_rate']:.6f} 元/件。",
        f"人工分配率 = {format_money(labor)} ÷ {result['processing_eq']:,.2f} = {result['labor_rate']:.6f} 元/件。",
        f"制造费用分配率 = {format_money(overhead)} ÷ {result['processing_eq']:,.2f} = {result['overhead_rate']:.6f} 元/件。",
        f"完工产品总成本 = {format_money(sheet['completed_total'])} 元；月末在产品成本 = {format_money(sheet['wip_total'])} 元；单位成本 = {format_money(sheet['unit_cost'])} 元/件。",
    ]
    print_steps(steps)
    print_table(COST_SHEET_HEADERS, sheet["rows"], "产品成本计算单")

    flow_headers = ["核算环节", "主要内容", "金额（元）"]
    flow_rows = [
        ["要素费用归集", "直接材料", format_money(material)],
        ["要素费用归集", "直接人工", format_money(labor)],
        ["要素费用归集", "制造费用", format_money(overhead)],
        ["生产费用合计", "本月生产费用", format_money(sheet["total_cost"])],
        ["完工与在产品分配", "完工产品成本", format_money(sheet["completed_total"])],
        ["完工与在产品分配", "期末在产品成本", format_money(sheet["wip_total"])],
        ["完工产品结转", "库存商品", format_money(sheet["completed_total"])],
    ]
    print_table(flow_headers, flow_rows, "品种法核算流程表")

    journal = [
        f"借：生产成本——基本生产成本（{product}）     {format_money(sheet['total_cost'])}",
        f"贷：原材料     {format_money(material)}",
        f"贷：应付职工薪酬     {format_money(labor)}",
        f"贷：制造费用     {format_money(overhead)}",
        f"借：库存商品——{product}     {format_money(sheet['completed_total'])}",
        f"贷：生产成本——基本生产成本（{product}）     {format_money(sheet['completed_total'])}",
    ]
    print_journal(journal)
    summary = [
        "品种法以产品品种为成本计算对象，生产费用按产品归集，月末在完工产品与在产品之间分配。",
        f"完工产品总成本 {format_money(sheet['completed_total'])} 元，单位成本 {format_money(sheet['unit_cost'])} 元/件。",
        "结转后“生产成本——基本生产成本”账户余额即为期末在产品成本。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第六章 品种法",
        "单一品种品种法",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[
            ("产品成本计算单", COST_SHEET_HEADERS, sheet["rows"]),
            ("品种法核算流程表", flow_headers, flow_rows),
        ],
        journal=journal,
        summary=summary,
        conclusion=f"完工产品成本 {format_money(sheet['completed_total'])} 元，单位成本 {format_money(sheet['unit_cost'])} 元/件。",
    )



def run_multi() -> None:
    """多品种品种法。"""
    print_heading("第六章 品种法：多品种核算", "-")
    total_material = input_float("直接材料总额（元）", 60000.0, min_value=0.0, name="直接材料")
    total_labor = input_float("直接人工总额（元）", 25000.0, min_value=0.0, name="直接人工")
    total_overhead = input_float("制造费用总额（元）", 15000.0, min_value=0.0, name="制造费用")
    count = input_int("产品品种数", 2, min_value=1, max_value=20, name="产品品种数")
    defaults = [
        {"name": "甲产品", "output": 600.0, "wip_qty": 100.0, "completion": 0.5, "material_quota": 50.0, "labor_hours": 3000.0},
        {"name": "乙产品", "output": 400.0, "wip_qty": 100.0, "completion": 0.5, "material_quota": 40.0, "labor_hours": 2000.0},
    ]
    products = []
    for i in range(count):
        item = defaults[i] if i < len(defaults) else {
            "name": f"产品{i + 1}", "output": 300.0, "wip_qty": 50.0, "completion": 0.5, "material_quota": 40.0, "labor_hours": 1500.0,
        }
        name = input_text(f"第{i + 1}种产品名称", item["name"])
        products.append({
            "name": name,
            "output": input_float(f"{name}完工产量", item["output"], min_value=0.0, name="完工产量"),
            "wip_qty": input_float(f"{name}月末在产品数量", item["wip_qty"], min_value=0.0, name="在产品数量"),
            "completion": input_percent(f"{name}在产品完工程度", item["completion"] * 100, min_percent=0.0, max_percent=100.0),
            "material_quota": input_float(f"{name}单位产品材料定额（元/件）", item["material_quota"], min_value=0.0, name="材料定额"),
            "labor_hours": input_float(f"{name}生产工时", item["labor_hours"], min_value=0.0, name="生产工时"),
        })

    result = multi_variety(total_material, total_labor, total_overhead, products)
    question = (
        f"某企业采用品种法同时生产 {count} 种产品。本月直接材料 {format_money(result['total_material'])} 元、"
        f"直接人工 {format_money(result['total_labor'])} 元、制造费用 {format_money(result['total_overhead'])} 元。"
        "材料按“产量 × 单位材料定额”分配，人工和制造费用按生产工时分配；各产品再按约当产量法分配完工与在产品成本。"
        "要求编制费用分配表、各产品成本计算单和完工结转分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "材料费用分配率 = 材料总额 ÷ Σ（各产品产量 × 单位材料定额）",
        "人工（制造费用）分配率 = 人工（制造费用）总额 ÷ Σ各产品生产工时",
        "某产品材料约当产量 = 完工产量 + 在产品数量（材料一次投入）",
        "某产品加工费约当产量 = 完工产量 + 在产品数量 × 完工程度",
        "某产品完工成本 = 完工产量 × 该产品各项单位分配率",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"材料分配标准合计 = {result['material_base_total']:,.2f}；材料分配率 = {format_money(result['total_material'])} ÷ {result['material_base_total']:,.2f} = {result['material_rate']:.6f}。",
        f"生产工时合计 = {result['hour_total']:,.2f}；人工分配率 = {format_money(result['total_labor'])} ÷ {result['hour_total']:,.2f} = {result['labor_rate']:.6f}。",
        f"制造费用分配率 = {format_money(result['total_overhead'])} ÷ {result['hour_total']:,.2f} = {result['overhead_rate']:.6f}。",
    ]
    for item in result["products"]:
        steps.append(
            f"{item['name']}：分配材料 {format_money(item['material_alloc'])} 元、人工 {format_money(item['labor_alloc'])} 元、"
            f"制造费用 {format_money(item['overhead_alloc'])} 元；材料约当产量 {item['material_eq']:,.2f}，"
            f"加工费约当产量 {item['processing_eq']:,.2f}。"
        )
    print_steps(steps)



    alloc_headers = ["产品名称", "完工产量", "材料定额标准", "生产工时", "材料分配额（元）", "人工分配额（元）", "制造费用分配额（元）", "费用合计（元）"]
    alloc_rows = []
    for item in result["products"]:
        alloc_rows.append([
            item["name"], f"{item['output']:,.2f}", f"{item['material_base']:,.2f}", f"{item['hour_base']:,.2f}",
            format_money(item["material_alloc"]), format_money(item["labor_alloc"]), format_money(item["overhead_alloc"]),
            format_money(item["material_alloc"] + item["labor_alloc"] + item["overhead_alloc"]),
        ])
    alloc_rows.append([
        "合计", f"{sum(item['output'] for item in result['products']):,.2f}", f"{result['material_base_total']:,.2f}",
        f"{result['hour_total']:,.2f}", format_money(sum(item["material_alloc"] for item in result["products"])),
        format_money(sum(item["labor_alloc"] for item in result["products"])),
        format_money(sum(item["overhead_alloc"] for item in result["products"])),
        format_money(result["total_cost"]),
    ])
    print_table(alloc_headers, alloc_rows, "多品种共同费用分配表")

    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = [("多品种共同费用分配表", alloc_headers, alloc_rows)]
    for item in result["products"]:
        print_table(COST_SHEET_HEADERS, item["sheet"]["rows"], f"{item['name']}产品成本计算单")
        tables.append((f"{item['name']}产品成本计算单", COST_SHEET_HEADERS, item["sheet"]["rows"]))

    summary_headers = ["产品名称", "完工总成本（元）", "期末在产品成本（元）", "单位成本（元/件）"]
    summary_rows = []
    for item in result["products"]:
        sheet = item["sheet"]
        summary_rows.append([item["name"], format_money(sheet["completed_total"]), format_money(sheet["wip_total"]), format_money(sheet["unit_cost"])])
    summary_rows.append(["合计", format_money(result["total_completed"]), format_money(result["total_wip"]), "—"])
    print_table(summary_headers, summary_rows, "多品种完工产品成本汇总表")
    tables.append(("多品种完工产品成本汇总表", summary_headers, summary_rows))

    journal = ["借：生产成本——基本生产成本"]
    for item in result["products"]:
        total = item["material_alloc"] + item["labor_alloc"] + item["overhead_alloc"]
        journal.append(f"    ——{item['name']}     {format_money(total)}")
    journal.append(f"贷：原材料     {format_money(total_material)}")
    journal.append(f"贷：应付职工薪酬     {format_money(total_labor)}")
    journal.append(f"贷：制造费用     {format_money(total_overhead)}")
    for item in result["products"]:
        sheet = item["sheet"]
        journal.append(f"借：库存商品——{item['name']}     {format_money(sheet['completed_total'])}")
        journal.append(f"贷：生产成本——基本生产成本（{item['name']}）     {format_money(sheet['completed_total'])}")
    print_journal(journal)

    summary = [
        f"各产品共同费用按材料定额和生产工时分配，分配结果合计 {format_money(result['total_cost'])} 元。",
        f"全部完工产品成本 {format_money(result['total_completed'])} 元，期末在产品成本 {format_money(result['total_wip'])} 元。",
        "核对提示：各产品费用合计之和应等于本月生产费用总额；完工成本与在产品成本之和应等于各产品费用合计。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第六章 品种法",
        "多品种品种法",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=tables,
        journal=journal,
        summary=summary,
        conclusion=f"多品种完工产品成本合计 {format_money(result['total_completed'])} 元，期末在产品成本 {format_money(result['total_wip'])} 元。",
    )


def show_flow() -> None:
    """品种法核算流程与要点。"""
    print_heading("第六章 品种法：核算流程与要点", "-")
    points = [
        "1. 成本计算对象：产品品种；成本计算期：通常按月。",
        "2. 生产费用按产品品种设置基本生产成本明细账，按成本项目设专栏。",
        "3. 直接材料、直接人工直接计入；制造费用按生产工时、生产工资或机器工时分配计入。",
        "4. 月末通常需要将生产费用在完工产品与在产品之间分配，常用约当产量法、定额比例法等。",
        "5. 完工产品验收入库时，借记“库存商品”，贷记“生产成本——基本生产成本”。",
        "6. 品种法适用于大量大批单步骤生产，如发电、采掘、铸造等，也适用于管理上不要求分步骤核算的多步骤生产。",
        "7. 多品种生产时，共同费用应先按合理标准分配至各产品，再分别计算各产品完工成本。",
    ]
    for point in points:
        print(f"  {point}")
    print_summary(
        [
            "品种法的核心是“按产品归集费用，按约当产量或定额比例分配完工与在产品成本”。",
            "多品种情况下，先分配共同费用，再分别计算各产品成本，注意两次分配的先后顺序。",
        ],
        "学习提示",
    )


def run() -> None:
    """第六章菜单。"""
    options = [
        ("1", "单一品种品种法（完整流程）", run_single),
        ("2", "多品种品种法（共同费用分配+各产品成本）", run_multi),
        ("3", "品种法核算流程与要点", show_flow),
    ]
    run_menu("第六章 产品成本计算——品种法", options, back_text="返回主菜单")

