"""第九章 产品成本计算辅助方法。

覆盖：
1. 产品成本分类法：按产品类别归集费用，再按系数分配计算各种产品成本；
2. 联产品成本分配：售价法、实物量法、可变现净值法；
3. 副产品成本计算：从联合成本中扣除副产品价值；
4. 定额法：定额成本、脱离定额差异、定额变动差异、材料成本差异。
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

import export
from utils import (
    ValidationError,
    allocate_amount,
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
    require_number,
    require_positive,
    run_menu,
    safe_div,
)


def classification_method(
    category_name: str,
    total_cost: Any,
    products: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """分类法：按系数把类别总成本分配到各产品。"""
    if not products:
        raise ValidationError("至少需要一种产品。")
    total = require_nonnegative(total_cost, "类别总成本")
    names: List[str] = []
    outputs: List[float] = []
    coefficients: List[float] = []
    standards: List[float] = []
    for index, product in enumerate(products, start=1):
        name = str(product.get("name") or f"产品{index}")
        output = require_positive(product.get("output"), f"{name}的产量")
        coefficient = require_positive(product.get("coefficient"), f"{name}的系数")
        names.append(name)
        outputs.append(output)
        coefficients.append(coefficient)
        standards.append(output * coefficient)
    allocations, standard_total = allocate_amount(total, standards, labels=names)
    rate = safe_div(total, standard_total, "分类法分配率")
    unit_costs = [round(amount / output, 6) for amount, output in zip(allocations, outputs)]
    return {
        "category": category_name,
        "total": total,
        "names": names,
        "outputs": outputs,
        "coefficients": coefficients,
        "standards": standards,
        "standard_total": standard_total,
        "rate": rate,
        "allocations": allocations,
        "unit_costs": unit_costs,
    }


def joint_products(
    joint_cost: Any,
    products: Sequence[Dict[str, Any]],
    method: str,
) -> Dict[str, Any]:
    """联产品成本分配：售价法、实物量法、可变现净值法。"""
    if not products:
        raise ValidationError("至少需要一种联产品。")
    if method not in ("售价法", "实物量法", "可变现净值法"):
        raise ValidationError("联产品分配方法只能是：售价法、实物量法、可变现净值法。")
    total = require_nonnegative(joint_cost, "联合成本")
    names: List[str] = []
    outputs: List[float] = []
    prices: List[float] = []
    further_costs: List[float] = []
    sales_values: List[float] = []
    weights: List[float] = []
    for index, product in enumerate(products, start=1):
        name = str(product.get("name") or f"联产品{index}")
        output = require_positive(product.get("output"), f"{name}的产量")
        price = require_nonnegative(product.get("unit_price"), f"{name}的售价")
        further = require_nonnegative(product.get("further_cost", 0), f"{name}的进一步加工成本")
        sales_value = output * price
        if method == "售价法":
            weight = sales_value
        elif method == "实物量法":
            weight = output
        else:
            weight = max(sales_value - further, 0.0)
        if weight <= 0:
            raise ValidationError(f"{name}的分配基础必须大于 0，请检查售价、产量或加工成本。")
        names.append(name)
        outputs.append(output)
        prices.append(price)
        further_costs.append(further)
        sales_values.append(sales_value)
        weights.append(weight)
    allocations, weight_total = allocate_amount(total, weights, labels=names)
    rate = safe_div(total, weight_total, "联产品成本分配率")
    unit_costs = [round(amount / output, 6) for amount, output in zip(allocations, outputs)]
    margins = [
        round(sales_values[i] - further_costs[i] - allocations[i], 2)
        for i in range(len(names))
    ]
    return {
        "method": method,
        "total": total,
        "names": names,
        "outputs": outputs,
        "prices": prices,
        "further_costs": further_costs,
        "sales_values": sales_values,
        "weights": weights,
        "weight_total": weight_total,
        "rate": rate,
        "allocations": allocations,
        "unit_costs": unit_costs,
        "margins": margins,
    }


def byproduct_method(
    joint_cost: Any,
    main_output: Any,
    byproduct_output: Any,
    byproduct_price: Any,
    further_cost: Any = 0.0,
) -> Dict[str, Any]:
    """副产品成本计算：按副产品售价扣除加工成本后的价值冲减联合成本。"""
    total = require_nonnegative(joint_cost, "联合成本")
    main_qty = require_positive(main_output, "主产品产量")
    by_qty = require_nonnegative(byproduct_output, "副产品产量")
    price = require_nonnegative(byproduct_price, "副产品售价")
    further = require_nonnegative(further_cost, "副产品进一步加工成本")
    byproduct_value = round(by_qty * price - further, 2)
    if byproduct_value < 0:
        raise ValidationError("副产品售价收入不足以弥补进一步加工成本，请检查数据。")
    if byproduct_value > total:
        raise ValidationError("副产品价值不能大于联合成本，请检查副产品售价或产量。")
    main_cost = round(total - byproduct_value, 2)
    main_unit_cost = round(main_cost / main_qty, 6)
    by_unit_cost = round(byproduct_value / by_qty, 6) if by_qty > 0 else 0.0
    return {
        "total": total,
        "main_output": main_qty,
        "byproduct_output": by_qty,
        "byproduct_price": price,
        "further_cost": further,
        "byproduct_value": byproduct_value,
        "main_cost": main_cost,
        "main_unit_cost": main_unit_cost,
        "byproduct_unit_cost": by_unit_cost,
    }


def norm_method(
    completed_qty: Any,
    wip_qty: Any,
    new_quota: Dict[str, Any],
    old_quota: Dict[str, Any],
    actual_costs: Dict[str, Any],
    material_difference_rate: Any,
) -> Dict[str, Any]:
    """定额法：计算定额成本、脱离定额差异、定额变动差异和材料成本差异。

    教学口径：
    - 定额成本 = 数量 × 现行单位定额；
    - 脱离定额差异 = 实际费用（计划价格口径） - 定额成本；
    - 定额变动差异 =（新单位定额 - 旧单位定额）× 数量；
    - 材料成本差异 = 材料实际费用（计划价格口径）× 材料成本差异率；
    - 各项差异按完工产品与在产品的定额成本比例分配。
    """
    completed = require_positive(completed_qty, "完工产品数量")
    wip = require_nonnegative(wip_qty, "在产品数量")
    total_qty = completed + wip
    if total_qty <= 0:
        raise ValidationError("完工产品数量与在产品数量合计必须大于 0。")
    items = ["直接材料", "直接人工", "制造费用"]
    keys = ["material", "labor", "overhead"]
    new_values = [require_nonnegative(new_quota.get(key), f"新定额-{item}") for key, item in zip(keys, items)]
    old_values = [require_nonnegative(old_quota.get(key), f"旧定额-{item}") for key, item in zip(keys, items)]
    actual_values = [require_nonnegative(actual_costs.get(key), f"实际费用-{item}") for key, item in zip(keys, items)]
    # 材料成本差异率可正可负：正数为超支差异，负数为节约差异。
    material_rate = require_number(material_difference_rate, "材料成本差异率", min_value=-1.0, max_value=1.0)

    quota_values = [round(new_values[i] * total_qty, 2) for i in range(3)]
    quota_total = round(sum(quota_values), 2)
    actual_total = round(sum(actual_values), 2)
    deviation_values = [round(actual_values[i] - quota_values[i], 2) for i in range(3)]
    change_values = [round((new_values[i] - old_values[i]) * total_qty, 2) for i in range(3)]
    material_difference = round(actual_values[0] * material_rate, 2)
    difference_total = round(sum(deviation_values) + sum(change_values) + material_difference, 2)
    completed_quota_values = [round(new_values[i] * completed, 2) for i in range(3)]
    wip_quota_values = [round(new_values[i] * wip, 2) for i in range(3)]
    completed_quota_total = round(sum(completed_quota_values), 2)
    wip_quota_total = round(sum(wip_quota_values), 2)
    if abs(completed_quota_total + wip_quota_total - quota_total) > 0.01:
        raise ValidationError("定额成本分配合计与总定额成本不一致，请检查数量。")
    completed_share = round(difference_total * completed_quota_total / quota_total, 2)
    wip_share = round(difference_total - completed_share, 2)
    completed_actual = round(completed_quota_total + completed_share, 2)
    wip_actual = round(wip_quota_total + wip_share, 2)
    unit_cost = round(completed_actual / completed, 6)

    quota_rows = []
    for i, item in enumerate(items):
        quota_rows.append([
            item, format_money(quota_values[i]), format_money(actual_values[i]), format_money(deviation_values[i]),
            format_money(change_values[i]), format_money(material_difference if i == 0 else 0.0),
        ])
    quota_rows.append([
        "合计", format_money(quota_total), format_money(actual_total), format_money(sum(deviation_values)),
        format_money(sum(change_values)), format_money(material_difference),
    ])
    allocation_rows = [
        ["完工产品", format_money(completed_quota_total), format_money(completed_share), format_money(completed_actual)],
        ["期末在产品", format_money(wip_quota_total), format_money(wip_share), format_money(wip_actual)],
        ["合计", format_money(quota_total), format_money(difference_total), format_money(completed_actual + wip_actual)],
    ]
    return {
        "completed_qty": completed,
        "wip_qty": wip,
        "total_qty": total_qty,
        "quota_values": quota_values,
        "quota_total": quota_total,
        "actual_values": actual_values,
        "actual_total": actual_total,
        "deviation_values": deviation_values,
        "change_values": change_values,
        "material_difference": material_difference,
        "difference_total": difference_total,
        "completed_quota_total": completed_quota_total,
        "wip_quota_total": wip_quota_total,
        "completed_share": completed_share,
        "wip_share": wip_share,
        "completed_actual": completed_actual,
        "wip_actual": wip_actual,
        "unit_cost": unit_cost,
        "quota_rows": quota_rows,
        "allocation_rows": allocation_rows,
    }



def run_classification() -> None:
    """分类法交互计算。"""
    print_heading("第九章 辅助方法：产品成本分类法", "-")
    category = input_text("产品类别名称", "A类产品")
    total = input_float("类别总成本（元）", 120000.0, min_value=0.0, name="类别总成本")
    count = input_int("类别内产品种数", 3, min_value=1, max_value=20, name="产品种数")
    defaults = [
        ("甲产品", 1000.0, 1.0), ("乙产品", 600.0, 1.2), ("丙产品", 400.0, 0.8),
    ]
    products = []
    for i in range(count):
        default_name, output, coefficient = defaults[i] if i < len(defaults) else (f"产品{i + 1}", 500.0, 1.0)
        name = input_text(f"第{i + 1}种产品名称", default_name)
        output_value = input_float(f"{name}产量", output, min_value=0.0, name="产量")
        coefficient_value = input_float(f"{name}系数", coefficient, min_value=0.0, name="系数")
        products.append({"name": name, "output": output_value, "coefficient": coefficient_value})

    result = classification_method(category, total, products)
    question = (
        f"某企业将{category}归为一类，采用分类法计算成本。本月该类产品总成本 {format_money(result['total'])} 元，"
        "类内各产品产量和系数如下表。要求按系数折算标准产量，分配类别总成本并计算各产品单位成本。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "某产品标准产量 = 该产品产量 × 系数",
        "分类法分配率 = 类别总成本 ÷ Σ各产品标准产量",
        "某产品应分配成本 = 该产品标准产量 × 分配率",
        "某产品单位成本 = 该产品分配成本 ÷ 该产品产量",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        "标准产量合计 = " + " + ".join(f"{name} {standard:,.2f}" for name, standard in zip(result["names"], result["standards"])) + f" = {result['standard_total']:,.2f}。",
        f"分类法分配率 = {format_money(result['total'])} ÷ {result['standard_total']:,.2f} = {result['rate']:.6f}。",
    ]
    for name, output, standard, amount, unit_cost in zip(result["names"], result["outputs"], result["standards"], result["allocations"], result["unit_costs"]):
        steps.append(
            f"{name}：标准产量 {standard:,.2f} × {result['rate']:.6f} = {format_money(amount)} 元；"
            f"单位成本 = {format_money(amount)} ÷ {output:,.2f} = {format_money(unit_cost)} 元/件。"
        )
    print_steps(steps)

    headers = ["产品名称", "产量", "系数", "标准产量", "分配率", "分配成本（元）", "单位成本（元/件）"]
    rows = [
        [name, f"{output:,.2f}", f"{coef:g}", f"{standard:,.2f}", f"{result['rate']:.6f}", format_money(amount), format_money(unit_cost)]
        for name, output, coef, standard, amount, unit_cost in zip(
            result["names"], result["outputs"], result["coefficients"], result["standards"], result["allocations"], result["unit_costs"]
        )
    ]
    rows.append(["合计", f"{sum(result['outputs']):,.2f}", "—", f"{result['standard_total']:,.2f}", "—", format_money(sum(result["allocations"])), "—"])
    print_table(headers, rows, "分类法产品成本计算表")

    journal = []
    for name, amount in zip(result["names"], result["allocations"]):
        journal.append(f"借：库存商品——{name}     {format_money(amount)}")
    journal.append(f"贷：生产成本——基本生产成本（{category}）     {format_money(result['total'])}")
    print_journal(journal)

    summary = [
        f"分类法先按产品类别归集成本，再按系数折算标准产量分配，分配率 {result['rate']:.6f}。",
        "分类法适用于产品品种、规格繁多，但可按一定标准分类的企业；系数应能反映各产品之间的成本差异。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第九章 辅助成本计算方法",
        "产品成本分类法",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("分类法产品成本计算表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"分类法分配率 {result['rate']:.6f}，类别总成本 {format_money(result['total'])} 元已分配。",
    )



def run_joint() -> None:
    """联产品成本分配。"""
    print_heading("第九章 辅助方法：联产品成本分配", "-")
    print("  分配方法：1 售价法；2 实物量法；3 可变现净值法")
    method_code = input_int("请选择联产品成本分配方法", 1, min_value=1, max_value=3, name="分配方法")
    method = {1: "售价法", 2: "实物量法", 3: "可变现净值法"}[method_code]
    total = input_float("联合成本（元）", 200000.0, min_value=0.0, name="联合成本")
    count = input_int("联产品种数", 2, min_value=1, max_value=20, name="联产品种数")
    defaults = [
        ("甲联产品", 1000.0, 100.0, 10000.0),
        ("乙联产品", 500.0, 160.0, 20000.0),
    ]
    products = []
    for i in range(count):
        default_name, output, price, further = defaults[i] if i < len(defaults) else (f"联产品{i + 1}", 500.0, 100.0, 5000.0)
        name = input_text(f"第{i + 1}种联产品名称", default_name)
        products.append({
            "name": name,
            "output": input_float(f"{name}产量", output, min_value=0.0, name="产量"),
            "unit_price": input_float(f"{name}分离点售价（元/件）", price, min_value=0.0, name="售价"),
            "further_cost": input_float(f"{name}进一步加工成本（元）", further, min_value=0.0, name="进一步加工成本"),
        })

    result = joint_products(total, products, method)
    question = (
        f"某企业生产联产品，联合成本为 {format_money(result['total'])} 元。各联产品产量、售价和进一步加工成本如下表。"
        f"采用{method}分配联合成本，要求计算各联产品应负担的联合成本、单位成本和毛利。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = {
        "售价法": [
            "某产品售价总额 = 产量 × 分离点售价",
            "联合成本分配率 = 联合成本 ÷ Σ各产品售价总额",
            "某产品应分配联合成本 = 该产品售价总额 × 分配率",
        ],
        "实物量法": [
            "联合成本分配率 = 联合成本 ÷ Σ各产品产量",
            "某产品应分配联合成本 = 该产品产量 × 分配率",
        ],
        "可变现净值法": [
            "某产品可变现净值 = 产量 × 售价 - 进一步加工成本",
            "联合成本分配率 = 联合成本 ÷ Σ各产品可变现净值",
            "某产品应分配联合成本 = 该产品可变现净值 × 分配率",
        ],
    }[method]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"分配基础合计 = {result['weight_total']:,.2f}；联合成本分配率 = {format_money(result['total'])} ÷ {result['weight_total']:,.2f} = {result['rate']:.6f}。",
    ]
    for i, name in enumerate(result["names"]):
        steps.append(
            f"{name}：分配基础 {result['weights'][i]:,.2f} × {result['rate']:.6f} = {format_money(result['allocations'][i])} 元；"
            f"单位成本 = {format_money(result['unit_costs'][i])} 元/件；毛利 = {format_money(result['margins'][i])} 元。"
        )
    print_steps(steps)

    headers = ["联产品", "产量", "售价（元/件）", "售价总额（元）", "进一步加工成本（元）", "分配基础", "分配联合成本（元）", "单位成本（元/件）", "毛利（元）"]
    rows = []
    for i, name in enumerate(result["names"]):
        rows.append([
            name, f"{result['outputs'][i]:,.2f}", format_money(result["prices"][i]), format_money(result["sales_values"][i]),
            format_money(result["further_costs"][i]), f"{result['weights'][i]:,.2f}", format_money(result["allocations"][i]),
            format_money(result["unit_costs"][i]), format_money(result["margins"][i]),
        ])
    rows.append(["合计", "—", "—", format_money(sum(result["sales_values"])), format_money(sum(result["further_costs"])), f"{result['weight_total']:,.2f}", format_money(sum(result["allocations"])), "—", format_money(sum(result["margins"]))])
    print_table(headers, rows, f"联产品成本分配表——{method}")

    journal = ["借：库存商品"]
    for name, amount in zip(result["names"], result["allocations"]):
        journal.append(f"    ——{name}     {format_money(amount)}")
    journal.append(f"贷：生产成本——联产品联合成本     {format_money(result['total'])}")
    print_journal(journal)

    summary = [
        f"采用{method}，联合成本分配率 {result['rate']:.6f}，各联产品分配额合计 {format_money(sum(result['allocations']))} 元。",
        "售价法适用于分离点售价可靠的产品；实物量法适用于产品价值与实物量相关性较强的情况；可变现净值法考虑了进一步加工成本。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第九章 辅助成本计算方法",
        f"联产品成本分配——{method}",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[(f"联产品成本分配表——{method}", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"{method}分配率 {result['rate']:.6f}，联产品联合成本分配完成。",
    )



def run_byproduct() -> None:
    """副产品成本计算。"""
    print_heading("第九章 辅助方法：副产品成本计算", "-")
    total = input_float("联合成本（元）", 200000.0, min_value=0.0, name="联合成本")
    main_output = input_float("主产品产量", 1000.0, min_value=0.0, name="主产品产量")
    byproduct_output = input_float("副产品产量", 200.0, min_value=0.0, name="副产品产量")
    byproduct_price = input_float("副产品售价（元/件）", 50.0, min_value=0.0, name="副产品售价")
    further_cost = input_float("副产品进一步加工成本（元）", 2000.0, min_value=0.0, name="进一步加工成本")
    result = byproduct_method(total, main_output, byproduct_output, byproduct_price, further_cost)

    question = (
        f"某企业在生产主产品的同时生产副产品。联合成本 {format_money(result['total'])} 元，主产品产量 {result['main_output']:,.2f} 件，"
        f"副产品产量 {result['byproduct_output']:,.2f} 件，副产品售价 {format_money(result['byproduct_price'])} 元/件，"
        f"进一步加工成本 {format_money(result['further_cost'])} 元。要求按副产品价值冲减联合成本，计算主产品和副产品成本。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "副产品价值 = 副产品产量 × 售价 - 进一步加工成本",
        "主产品联合成本 = 联合成本 - 副产品价值",
        "主产品单位成本 = 主产品联合成本 ÷ 主产品产量",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"副产品价值 = {result['byproduct_output']:,.2f} × {format_money(result['byproduct_price'])} - {format_money(result['further_cost'])} = {format_money(result['byproduct_value'])} 元。",
        f"主产品应负担联合成本 = {format_money(result['total'])} - {format_money(result['byproduct_value'])} = {format_money(result['main_cost'])} 元。",
        f"主产品单位成本 = {format_money(result['main_cost'])} ÷ {result['main_output']:,.2f} = {format_money(result['main_unit_cost'])} 元/件。",
        f"副产品单位成本 = {format_money(result['byproduct_value'])} ÷ {result['byproduct_output']:,.2f} = {format_money(result['byproduct_unit_cost'])} 元/件。",
    ]
    print_steps(steps)

    headers = ["项目", "主产品", "副产品", "合计"]
    rows = [
        ["产量", f"{result['main_output']:,.2f}", f"{result['byproduct_output']:,.2f}", "—"],
        ["售价（元/件）", "—", format_money(result["byproduct_price"]), "—"],
        ["进一步加工成本（元）", "—", format_money(result["further_cost"]), "—"],
        ["应负担成本（元）", format_money(result["main_cost"]), format_money(result["byproduct_value"]), format_money(result["total"])],
        ["单位成本（元/件）", format_money(result["main_unit_cost"]), format_money(result["byproduct_unit_cost"]), "—"],
    ]
    print_table(headers, rows, "主产品与副产品成本计算表")

    journal = [
        f"借：库存商品——主产品     {format_money(result['main_cost'])}",
        f"借：库存商品——副产品     {format_money(result['byproduct_value'])}",
        f"贷：生产成本——联合成本     {format_money(result['total'])}",
    ]
    print_journal(journal)

    summary = [
        f"副产品价值 {format_money(result['byproduct_value'])} 元，冲减联合成本后主产品成本 {format_money(result['main_cost'])} 元。",
        "副产品价值通常按售价扣除进一步加工成本后的净额确定；如果副产品价值较低，也可采用简化方法。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第九章 辅助成本计算方法",
        "副产品成本计算",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("主产品与副产品成本计算表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"主产品成本 {format_money(result['main_cost'])} 元，副产品价值 {format_money(result['byproduct_value'])} 元。",
    )



def run_norm() -> None:
    """定额法交互计算。"""
    print_heading("第九章 辅助方法：定额法", "-")
    product = input_text("产品名称", "甲产品")
    completed_qty = input_float("完工产品数量", 500.0, min_value=0.0, name="完工产品数量")
    wip_qty = input_float("月末在产品数量", 100.0, min_value=0.0, name="在产品数量")
    print("  请输入现行（新）单位定额：")
    new_quota = {
        "material": input_float("直接材料单位定额（元/件）", 80.0, min_value=0.0, name="新材料定额"),
        "labor": input_float("直接人工单位定额（元/件）", 30.0, min_value=0.0, name="新人工定额"),
        "overhead": input_float("制造费用单位定额（元/件）", 20.0, min_value=0.0, name="新制造费用定额"),
    }
    print("  请输入修订前（旧）单位定额：")
    old_quota = {
        "material": input_float("旧直接材料单位定额（元/件）", 75.0, min_value=0.0, name="旧材料定额"),
        "labor": input_float("旧直接人工单位定额（元/件）", 30.0, min_value=0.0, name="旧人工定额"),
        "overhead": input_float("旧制造费用单位定额（元/件）", 20.0, min_value=0.0, name="旧制造费用定额"),
    }
    print("  请输入本月实际费用（计划价格口径）：")
    actual_costs = {
        "material": input_float("实际直接材料（元）", 46000.0, min_value=0.0, name="实际材料"),
        "labor": input_float("实际直接人工（元）", 16000.0, min_value=0.0, name="实际人工"),
        "overhead": input_float("实际制造费用（元）", 10000.0, min_value=0.0, name="实际制造费用"),
    }
    material_rate = input_percent("材料成本差异率（正数超支、负数节约）", 2.0, min_percent=-100.0, max_percent=100.0)
    result = norm_method(completed_qty, wip_qty, new_quota, old_quota, actual_costs, material_rate)

    question = (
        f"某企业采用定额法计算{product}成本。本月完工 {result['completed_qty']:,.2f} 件，在产品 {result['wip_qty']:,.2f} 件。"
        "现行单位定额与修订前单位定额如下，本月实际费用按计划价格口径给出，材料成本差异率为 "
        f"{format_percent(material_rate)}。要求计算定额成本、脱离定额差异、定额变动差异、材料成本差异，"
        "并将差异在完工产品与在产品之间分配。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "定额成本 = 数量 × 现行单位定额成本",
        "脱离定额差异 = 实际费用（计划价格口径） - 定额成本",
        "定额变动差异 =（新单位定额 - 旧单位定额）× 数量",
        "材料成本差异 = 材料实际费用（计划价格口径）× 材料成本差异率",
        "差异分配率 = 差异合计 ÷ 定额成本合计",
        "完工产品实际成本 = 完工产品定额成本 + 完工产品应负担差异",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"定额成本合计 = {result['total_qty']:,.2f} 件 × 现行单位定额 = {format_money(result['quota_total'])} 元。",
        f"脱离定额差异 = {format_money(result['actual_total'])} - {format_money(result['quota_total'])} = {format_money(sum(result['deviation_values']))} 元。",
        f"定额变动差异 = {format_money(sum(result['change_values']))} 元（正数表示定额提高使成本增加）。",
        f"材料成本差异 = {format_money(result['actual_values'][0])} × {format_percent(material_rate)} = {format_money(result['material_difference'])} 元。",
        f"差异合计 = {format_money(result['difference_total'])} 元。",
        f"完工产品定额成本 = {format_money(result['completed_quota_total'])} 元，应负担差异 = {format_money(result['completed_share'])} 元，"
        f"完工产品实际成本 = {format_money(result['completed_actual'])} 元。",
        f"在产品定额成本 = {format_money(result['wip_quota_total'])} 元，应负担差异 = {format_money(result['wip_share'])} 元，"
        f"在产品实际成本 = {format_money(result['wip_actual'])} 元。",
    ]
    print_steps(steps)

    quota_headers = ["成本项目", "定额成本（元）", "实际费用（元）", "脱离定额差异（元）", "定额变动差异（元）", "材料成本差异（元）"]
    print_table(quota_headers, result["quota_rows"], "定额成本与差异计算表")
    allocation_headers = ["项目", "定额成本（元）", "差异分配（元）", "调整后成本（元）"]
    print_table(allocation_headers, result["allocation_rows"], "完工产品与在产品成本计算表")

    journal = [
        f"借：库存商品——{product}     {format_money(result['completed_actual'])}",
        f"贷：生产成本——基本生产成本（{product}）     {format_money(result['completed_actual'])}",
    ]
    print_journal(journal)

    summary = [
        f"完工产品实际成本 {format_money(result['completed_actual'])} 元，单位成本 {format_money(result['unit_cost'])} 元/件。",
        f"期末在产品实际成本 {format_money(result['wip_actual'])} 元，与完工产品成本之和为 {format_money(result['completed_actual'] + result['wip_actual'])} 元。",
        "定额法将定额成本、脱离定额差异、定额变动差异和材料成本差异分别反映，便于成本控制和差异分析。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第九章 辅助成本计算方法",
        "定额法（定额成本与三类差异）",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[
            ("定额成本与差异计算表", quota_headers, result["quota_rows"]),
            ("完工产品与在产品成本计算表", allocation_headers, result["allocation_rows"]),
        ],
        journal=journal,
        summary=summary,
        conclusion=f"完工产品实际成本 {format_money(result['completed_actual'])} 元，单位成本 {format_money(result['unit_cost'])} 元/件。",
    )



def show_comparison() -> None:
    """辅助成本计算方法比较。"""
    print_heading("第九章 辅助成本计算方法：比较与要点", "-")
    headers = ["方法", "核心思路", "适用情形", "关键公式/指标"]
    rows = [
        ["分类法", "按类别归集，按系数折算标准产量分配", "品种规格多但可分类", "标准产量 = 产量 × 系数"],
        ["联产品售价法", "按分离点售价总额分配联合成本", "分离点售价可靠", "售价总额 = 产量 × 售价"],
        ["联产品实物量法", "按产量等实物量分配联合成本", "价值与实物量相关性较强", "分配率 = 联合成本 ÷ 总产量"],
        ["联产品可变现净值法", "按售价减进一步加工成本分配", "需要进一步加工后销售", "可变现净值 = 售价 - 加工成本"],
        ["副产品法", "副产品价值冲减联合成本", "主副产品同时生产", "主产品成本 = 联合成本 - 副产品价值"],
        ["定额法", "定额成本 ± 各类差异", "定额管理基础较好", "实际成本 = 定额成本 ± 差异"],
    ]
    print_table(headers, rows, "辅助成本计算方法比较")
    print_summary(
        [
            "分类法、联产品/副产品法解决“共同成本如何在多种产品之间分配”的问题。",
            "定额法解决“实际成本与定额成本的差异如何反映和控制”的问题。",
            "选择方法时应结合生产特点、管理要求以及资料取得成本。",
        ],
        "学习提示",
    )


def run() -> None:
    """第九章菜单。"""
    options = [
        ("1", "产品成本分类法（系数分配）", run_classification),
        ("2", "联产品成本分配（售价法/实物量法/可变现净值法）", run_joint),
        ("3", "副产品成本计算（冲减联合成本）", run_byproduct),
        ("4", "定额法（定额成本、脱离差异、定额变动差异、材料成本差异）", run_norm),
        ("5", "辅助成本计算方法比较", show_comparison),
    ]
    run_menu("第九章 产品成本计算辅助方法", options, back_text="返回主菜单")

