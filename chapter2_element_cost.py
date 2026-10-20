"""第二章 工业企业要素费用的归集与分配。

覆盖：
1. 材料费用分配：定额消耗量比例法、定额费用比例法、产品重量比例法、产量比例法；
2. 外购动力费用分配；
3. 职工薪酬费用分配（工资、福利费、社会保险费）；
4. 折旧费用、低值易耗品摊销分配；
5. 税金和其他支出费用分配。

每个计算均输出文字题意、公式、分步过程、费用分配表、会计分录和总结，
并自动保存 CSV 记录。所有案例均为自行设计的模拟教学案例。
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
    require_positive,
    run_menu,
    safe_div,
)


MATERIAL_METHODS = {
    1: "定额消耗量比例法",
    2: "定额费用比例法",
    3: "产品重量比例法",
    4: "产量比例法",
}

DEPARTMENT_NAMES = {
    1: "制造费用",
    2: "管理费用",
    3: "销售费用",
    4: "财务费用",
}


# ---------------------------------------------------------------------------
# 一、材料费用分配
# ---------------------------------------------------------------------------
def allocate_material(total_cost: Any, products: Sequence[Dict[str, Any]], method: str) -> Dict[str, Any]:
    """按指定标准分配材料费用。

    products 中每个元素至少包含：
        name: 产品名称；output: 产量；
        quota: 单位定额消耗量（定额消耗量法/定额费用法使用）；
        unit_price: 材料计划单价（定额费用法使用）；
        weight: 单位产品重量（重量法使用）。
    返回分配标准、分配率、各产品分配额和单位材料成本。
    """
    if not products:
        raise ValidationError("至少需要一种产品。")
    if method not in MATERIAL_METHODS.values():
        raise ValidationError(f"未知的材料费用分配方法：{method}")

    total = require_nonnegative(total_cost, "材料实际费用总额")
    names: List[str] = []
    bases: List[float] = []
    outputs: List[float] = []

    for index, product in enumerate(products, start=1):
        name = str(product.get("name") or f"产品{index}")
        output = require_positive(product.get("output"), f"{name}的产量")
        if method == "定额消耗量比例法":
            quota = require_nonnegative(product.get("quota"), f"{name}的单位定额消耗量")
            basis = output * quota
        elif method == "定额费用比例法":
            quota = require_nonnegative(product.get("quota"), f"{name}的单位定额消耗量")
            price = require_nonnegative(product.get("unit_price"), f"{name}的材料计划单价")
            basis = output * quota * price
        elif method == "产品重量比例法":
            weight = require_nonnegative(product.get("weight"), f"{name}的单位产品重量")
            basis = output * weight
        else:  # 产量比例法
            basis = output
        names.append(name)
        outputs.append(output)
        bases.append(basis)

    allocations, total_basis = allocate_amount(total, bases, labels=names)
    rate = safe_div(total, total_basis, "材料费用分配率")
    unit_costs = [safe_div(amount, output, f"{name}的产量") for amount, output in zip(allocations, outputs)]
    return {
        "method": method,
        "total": total,
        "names": names,
        "outputs": outputs,
        "bases": bases,
        "total_basis": total_basis,
        "rate": rate,
        "allocations": allocations,
        "unit_costs": unit_costs,
    }


def run_material() -> None:
    """交互式材料费用分配。"""
    print_heading("第二章 要素费用：材料费用分配", "-")
    print("  分配方法：1 定额消耗量比例法；2 定额费用比例法；3 产品重量比例法；4 产量比例法")
    method_code = input_int("请选择分配方法", 1, min_value=1, max_value=4, name="分配方法编号")
    method = MATERIAL_METHODS[method_code]

    total_cost = input_float("材料实际费用总额（元）", 48000.0, min_value=0.0, name="材料费用")
    count = input_int("产品种类数", 2, min_value=1, max_value=20, name="产品种类数")
    defaults = [
        {"name": "甲产品", "output": 200.0, "quota": 15.0, "unit_price": 10.0, "weight": 2.0},
        {"name": "乙产品", "output": 150.0, "quota": 12.0, "unit_price": 10.0, "weight": 2.5},
    ]
    products: List[Dict[str, Any]] = []
    for i in range(count):
        item = defaults[i] if i < len(defaults) else {
            "name": f"产品{i + 1}", "output": 100.0, "quota": 10.0, "unit_price": 10.0, "weight": 1.0,
        }
        name = input_text(f"第{i + 1}种产品名称", item["name"])
        product: Dict[str, Any] = {"name": name}
        product["output"] = input_float(f"{name}的产量", item["output"], min_value=0.0, name=f"{name}产量")
        if method_code in (1, 2):
            product["quota"] = input_float(f"{name}的单位定额消耗量", item["quota"], min_value=0.0, name="单位定额")
        if method_code == 2:
            product["unit_price"] = input_float(f"{name}的材料计划单价（元）", item["unit_price"], min_value=0.0, name="材料单价")
        if method_code == 3:
            product["weight"] = input_float(f"{name}的单位产品重量", item["weight"], min_value=0.0, name="单位重量")
        products.append(product)

    result = allocate_material(total_cost, products, method)
    question = (
        f"某企业本月耗用材料实际费用 {format_money(result['total'])} 元，"
        f"生产 {len(result['names'])} 种产品。采用{method}分配材料费用。"
        "各产品产量及分配标准如下表，要求计算分配率、各产品应负担的材料费用并编制会计分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")

    basis_name = {
        "定额消耗量比例法": "定额消耗量",
        "定额费用比例法": "定额费用",
        "产品重量比例法": "产品重量",
        "产量比例法": "产量",
    }[method]
    formulas = [
        f"某产品分配标准 = 产量 × 单位{basis_name}（产量比例法直接用产量）",
        f"材料费用分配率 = 材料实际费用总额 ÷ 分配标准合计 = {format_money(result['total'])} ÷ {result['total_basis']:,.2f}",
        "某产品应负担材料费用 = 该产品分配标准 × 分配率",
        "某产品单位材料成本 = 该产品材料费用 ÷ 该产品产量",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = []
    for name, output, basis, amount, unit_cost in zip(
        result["names"], result["outputs"], result["bases"], result["allocations"], result["unit_costs"]
    ):
        steps.append(
            f"{name}：分配标准 = {basis:,.2f}；应分配材料费用 = {basis:,.2f} × {result['rate']:.6f} = {format_money(amount)} 元；"
            f"单位材料成本 = {format_money(amount)} ÷ {output:,.2f} = {format_money(unit_cost)} 元/件。"
        )
    steps.append(
        f"验算：各产品材料费用合计 = {format_money(sum(result['allocations']))} 元，"
        f"与材料实际费用总额 {format_money(result['total'])} 元一致。"
    )
    print_steps(steps)

    headers = ["产品名称", "产量", "分配标准", "分配率", "分配金额（元）", "单位材料成本（元/件）"]
    rows = []
    for name, output, basis, amount, unit_cost in zip(
        result["names"], result["outputs"], result["bases"], result["allocations"], result["unit_costs"]
    ):
        rows.append([name, f"{output:,.2f}", f"{basis:,.2f}", f"{result['rate']:.6f}", format_money(amount), format_money(unit_cost)])
    rows.append(["合计", f"{sum(result['outputs']):,.2f}", f"{result['total_basis']:,.2f}", "—", format_money(sum(result['allocations'])), "—"])
    print_table(headers, rows, "材料费用分配表")

    journal = ["借：生产成本——基本生产成本"]
    for name, amount in zip(result["names"], result["allocations"]):
        journal.append(f"    ——{name}     {format_money(amount)}")
    journal.append(f"贷：原材料     {format_money(result['total'])}")
    print_journal(journal)

    summary = [
        f"采用{method}，材料费用分配率为 {result['rate']:.6f} 元/单位分配标准。",
        f"分配后各产品材料费用合计 {format_money(sum(result['allocations']))} 元，分配结果平衡。",
        "核对提示：分配标准的口径必须与分配率分母保持一致；尾差已调整到最后一个产品。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第二章 要素费用",
        f"材料费用分配——{method}",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("材料费用分配表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"{method}分配率 {result['rate']:.6f}，各产品材料费用已分配并平衡。",
    )



# ---------------------------------------------------------------------------
# 二、外购动力费用分配
# ---------------------------------------------------------------------------
def allocate_power(total_cost: Any, products: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """按机器工时（或生产工时）分配外购动力费用。"""
    if not products:
        raise ValidationError("至少需要一种产品。")
    total = require_nonnegative(total_cost, "外购动力费用总额")
    names = [str(product.get("name") or f"产品{i + 1}") for i, product in enumerate(products)]
    hours = [require_nonnegative(product.get("machine_hours"), f"{name}的机器工时") for name, product in zip(names, products)]
    allocations, total_hours = allocate_amount(total, hours, labels=names)
    rate = safe_div(total, total_hours, "动力费用分配率")
    return {
        "total": total,
        "names": names,
        "hours": hours,
        "total_hours": total_hours,
        "rate": rate,
        "allocations": allocations,
    }


def run_power() -> None:
    """交互式外购动力费用分配。"""
    print_heading("第二章 要素费用：外购动力费用分配", "-")
    total_cost = input_float("本月外购动力费用总额（元）", 18000.0, min_value=0.0, name="动力费用")
    count = input_int("产品种类数", 2, min_value=1, max_value=20, name="产品种类数")
    defaults = [("甲产品", 1200.0), ("乙产品", 800.0)]
    products = []
    for i in range(count):
        default_name, default_hours = defaults[i] if i < len(defaults) else (f"产品{i + 1}", 1000.0)
        name = input_text(f"第{i + 1}种产品名称", default_name)
        hours = input_float(f"{name}的机器工时", default_hours, min_value=0.0, name="机器工时")
        products.append({"name": name, "machine_hours": hours})

    result = allocate_power(total_cost, products)
    question = (
        f"某企业本月支付外购电力费 {format_money(result['total'])} 元，按机器工时比例在生产产品之间分配。"
        "要求计算动力费用分配率、各产品应负担的动力费用，并编制会计分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "动力费用分配率 = 外购动力费用总额 ÷ 各种产品机器工时合计",
        "某产品应负担动力费用 = 该产品机器工时 × 动力费用分配率",
        "如果动力费用中有一部分用于车间照明或行政管理，应先计入“制造费用”或“管理费用”，再按受益对象分配。",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"机器工时合计 = {result['total_hours']:,.2f} 工时。",
        f"动力费用分配率 = {format_money(result['total'])} ÷ {result['total_hours']:,.2f} = {result['rate']:.6f} 元/工时。",
    ]
    for name, hours, amount in zip(result["names"], result["hours"], result["allocations"]):
        steps.append(f"{name}应负担动力费用 = {hours:,.2f} × {result['rate']:.6f} = {format_money(amount)} 元。")
    steps.append(f"验算：分配额合计 {format_money(sum(result['allocations']))} 元 = 动力费用总额。")
    print_steps(steps)

    headers = ["产品名称", "机器工时", "分配率（元/工时）", "分配金额（元）"]
    rows = [
        [name, f"{hours:,.2f}", f"{result['rate']:.6f}", format_money(amount)]
        for name, hours, amount in zip(result["names"], result["hours"], result["allocations"])
    ]
    rows.append(["合计", f"{result['total_hours']:,.2f}", "—", format_money(sum(result["allocations"]))])
    print_table(headers, rows, "外购动力费用分配表")

    journal = ["借：生产成本——基本生产成本"]
    for name, amount in zip(result["names"], result["allocations"]):
        journal.append(f"    ——{name}     {format_money(amount)}")
    journal.append(f"贷：应付账款——供电公司     {format_money(result['total'])}")
    print_journal(journal)

    summary = [
        "外购动力费用按机器工时分配，符合“谁受益、谁负担”的受益原则。",
        "若动力用于多个车间或管理部门，应先按用电量分配至各车间、部门，再进入制造费用或管理费用。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第二章 要素费用",
        "外购动力费用分配",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("外购动力费用分配表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"动力费用分配率 {result['rate']:.6f} 元/工时，分配额合计 {format_money(sum(result['allocations']))} 元。",
    )



# ---------------------------------------------------------------------------
# 三、职工薪酬费用分配
# ---------------------------------------------------------------------------
def allocate_payroll(
    total_wage: Any,
    products: Sequence[Dict[str, Any]],
    welfare_rate: Any,
    social_rate: Any,
) -> Dict[str, Any]:
    """按生产工时分配工资，并计提福利费和社会保险费。"""
    if not products:
        raise ValidationError("至少需要一种产品。")
    total = require_nonnegative(total_wage, "生产工人工资总额")
    welfare = require_nonnegative(welfare_rate, "福利费计提比例")
    social = require_nonnegative(social_rate, "社会保险费计提比例")
    names = [str(product.get("name") or f"产品{i + 1}") for i, product in enumerate(products)]
    hours = [require_nonnegative(product.get("hours"), f"{name}的生产工时") for name, product in zip(names, products)]
    wages, total_hours = allocate_amount(total, hours, labels=names)
    welfare_amounts = [round(amount * welfare, 2) for amount in wages]
    social_amounts = [round(amount * social, 2) for amount in wages]
    totals = [round(w + f + s, 2) for w, f, s in zip(wages, welfare_amounts, social_amounts)]
    rate = safe_div(total, total_hours, "工资分配率")
    return {
        "total": total,
        "welfare_rate": welfare,
        "social_rate": social,
        "names": names,
        "hours": hours,
        "total_hours": total_hours,
        "rate": rate,
        "wages": wages,
        "welfare": welfare_amounts,
        "social": social_amounts,
        "totals": totals,
    }


def run_payroll() -> None:
    """交互式职工薪酬费用分配。"""
    print_heading("第二章 要素费用：职工薪酬费用分配", "-")
    total_wage = input_float("生产工人工资总额（元）", 60000.0, min_value=0.0, name="工资总额")
    welfare_rate = input_percent("职工福利费计提比例", 14.0, min_percent=0.0, max_percent=100.0)
    social_rate = input_percent("社会保险费计提比例", 26.0, min_percent=0.0, max_percent=100.0)
    count = input_int("产品种类数", 2, min_value=1, max_value=20, name="产品种类数")
    defaults = [("甲产品", 2000.0), ("乙产品", 1000.0)]
    products = []
    for i in range(count):
        default_name, default_hours = defaults[i] if i < len(defaults) else (f"产品{i + 1}", 1000.0)
        name = input_text(f"第{i + 1}种产品名称", default_name)
        hours = input_float(f"{name}的生产工时", default_hours, min_value=0.0, name="生产工时")
        products.append({"name": name, "hours": hours})

    result = allocate_payroll(total_wage, products, welfare_rate, social_rate)
    question = (
        f"某企业本月生产工人工资总额为 {format_money(result['total'])} 元，按生产工时比例在甲、乙产品之间分配；"
        f"职工福利费按工资的 {format_percent(result['welfare_rate'])} 计提，社会保险费按工资的 "
        f"{format_percent(result['social_rate'])} 计提。要求计算各产品工资、福利费、社会保险费及合计数。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "工资分配率 = 生产工人工资总额 ÷ 各种产品生产工时合计",
        "某产品应分配工资 = 该产品生产工时 × 工资分配率",
        "某产品职工福利费 = 该产品工资 × 福利费计提比例",
        "某产品社会保险费 = 该产品工资 × 社会保险费计提比例",
        "某产品职工薪酬合计 = 工资 + 福利费 + 社会保险费",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"生产工时合计 = {result['total_hours']:,.2f} 工时。",
        f"工资分配率 = {format_money(result['total'])} ÷ {result['total_hours']:,.2f} = {result['rate']:.6f} 元/工时。",
    ]
    for name, hours, wage, welfare, social, total in zip(
        result["names"], result["hours"], result["wages"], result["welfare"], result["social"], result["totals"]
    ):
        steps.append(
            f"{name}：工资 = {hours:,.2f} × {result['rate']:.6f} = {format_money(wage)} 元；"
            f"福利费 = {format_money(wage)} × {format_percent(result['welfare_rate'])} = {format_money(welfare)} 元；"
            f"社会保险费 = {format_money(wage)} × {format_percent(result['social_rate'])} = {format_money(social)} 元；"
            f"合计 = {format_money(total)} 元。"
        )
    steps.append(f"验算：工资合计 {format_money(sum(result['wages']))} 元；职工薪酬合计 {format_money(sum(result['totals']))} 元。")
    print_steps(steps)

    headers = ["产品名称", "生产工时", "工资分配率", "工资（元）", "福利费（元）", "社会保险费（元）", "合计（元）"]
    rows = [
        [name, f"{hours:,.2f}", f"{result['rate']:.6f}", format_money(wage), format_money(welfare), format_money(social), format_money(total)]
        for name, hours, wage, welfare, social, total in zip(
            result["names"], result["hours"], result["wages"], result["welfare"], result["social"], result["totals"]
        )
    ]
    rows.append([
        "合计", f"{result['total_hours']:,.2f}", "—", format_money(sum(result["wages"])),
        format_money(sum(result["welfare"])), format_money(sum(result["social"])), format_money(sum(result["totals"])),
    ])
    print_table(headers, rows, "职工薪酬费用分配表")

    journal = ["借：生产成本——基本生产成本"]
    for name, total in zip(result["names"], result["totals"]):
        journal.append(f"    ——{name}     {format_money(total)}")
    journal.append(f"贷：应付职工薪酬——工资     {format_money(sum(result['wages']))}")
    journal.append(f"贷：应付职工薪酬——职工福利     {format_money(sum(result['welfare']))}")
    journal.append(f"贷：应付职工薪酬——社会保险费     {format_money(sum(result['social']))}")
    print_journal(journal)

    summary = [
        "工资按生产工时分配，福利费和社会保险费以各产品工资为基数分别计提。",
        "核对提示：职工福利费、社会保险费的计提基数应与工资分配结果保持一致。",
        f"职工薪酬总额 = {format_money(sum(result['totals']))} 元。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第二章 要素费用",
        "职工薪酬费用分配",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("职工薪酬费用分配表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"工资分配率 {result['rate']:.6f} 元/工时，职工薪酬合计 {format_money(sum(result['totals']))} 元。",
    )



# ---------------------------------------------------------------------------
# 四、折旧费用与低值易耗品摊销
# ---------------------------------------------------------------------------
def calculate_depreciation(assets: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """按年限平均法计算固定资产月折旧额，并按部门汇总。

    月折旧额 = 原值 ×（1 - 预计净残值率）÷ 预计使用年限 ÷ 12。
    """
    if not assets:
        raise ValidationError("至少需要一项固定资产。")
    rows: List[Dict[str, Any]] = []
    department_totals: Dict[str, float] = {}
    for index, asset in enumerate(assets, start=1):
        name = str(asset.get("name") or f"固定资产{index}")
        original = require_positive(asset.get("original"), f"{name}的原值")
        residual_rate = require_nonnegative(asset.get("residual_rate"), f"{name}的预计净残值率")
        if residual_rate >= 1:
            raise ValidationError(f"{name}的预计净残值率必须小于 100%。")
        life = require_positive(asset.get("life_years"), f"{name}的预计使用年限")
        department = str(asset.get("department") or "制造费用")
        monthly = original * (1 - residual_rate) / life / 12
        rows.append({
            "name": name,
            "original": original,
            "residual_rate": residual_rate,
            "life": life,
            "department": department,
            "monthly": round(monthly, 2),
        })
        department_totals[department] = round(department_totals.get(department, 0.0) + monthly, 2)
    total = round(sum(item["monthly"] for item in rows), 2)
    return {"rows": rows, "departments": department_totals, "total": total}


def run_depreciation() -> None:
    """交互式折旧费用计算与分配。"""
    print_heading("第二章 要素费用：折旧费用计算与分配", "-")
    print("  部门类别：1 制造费用（生产车间）；2 管理费用（行政管理部门）；3 销售费用（销售部门）")
    count = input_int("固定资产项目数", 3, min_value=1, max_value=30, name="固定资产项目数")
    defaults = [
        ("生产车间机器设备", 600000.0, 5.0, 10.0, 1),
        ("行政办公楼", 900000.0, 5.0, 20.0, 2),
        ("销售部门运输设备", 240000.0, 5.0, 5.0, 3),
    ]
    assets = []
    for i in range(count):
        default_name, original, residual, life, department_code = (
            defaults[i] if i < len(defaults) else (f"固定资产{i + 1}", 300000.0, 5.0, 10.0, 1)
        )
        name = input_text(f"第{i + 1}项固定资产名称", default_name)
        original_value = input_float(f"{name}的原值（元）", original, min_value=0.0, name="原值")
        residual_rate = input_percent(f"{name}的预计净残值率", residual, min_percent=0.0, max_percent=99.0)
        life_years = input_float(f"{name}的预计使用年限（年）", life, min_value=0.0, name="使用年限")
        department_code = input_int(f"{name}的受益部门（1制造费用/2管理费用/3销售费用）", department_code, min_value=1, max_value=3, name="部门编号")
        assets.append({
            "name": name,
            "original": original_value,
            "residual_rate": residual_rate,
            "life_years": life_years,
            "department": DEPARTMENT_NAMES[department_code],
        })

    result = calculate_depreciation(assets)
    question = (
        "某企业采用年限平均法计提固定资产折旧。各项固定资产原值、预计净残值率、预计使用年限和受益部门如下表。"
        "要求计算各项固定资产月折旧额，按部门汇总并编制折旧费用分配分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "月折旧额 = 固定资产原值 ×（1 - 预计净残值率）÷ 预计使用年限 ÷ 12",
        "某部门折旧费用 = 该部门各项固定资产月折旧额之和",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = []
    for item in result["rows"]:
        steps.append(
            f"{item['name']}：月折旧额 = {format_money(item['original'])} ×（1 - {format_percent(item['residual_rate'])}）"
            f" ÷ {item['life']:g} ÷ 12 = {format_money(item['monthly'])} 元，计入{item['department']}。"
        )
    for department, amount in result["departments"].items():
        steps.append(f"{department}折旧费用合计 = {format_money(amount)} 元。")
    steps.append(f"本月折旧费用总额 = {format_money(result['total'])} 元。")
    print_steps(steps)

    headers = ["固定资产名称", "原值（元）", "净残值率", "使用年限", "月折旧额（元）", "受益部门"]
    rows = [
        [
            item["name"], format_money(item["original"]), format_percent(item["residual_rate"]),
            f"{item['life']:g} 年", format_money(item["monthly"]), item["department"],
        ]
        for item in result["rows"]
    ]
    rows.append(["合计", "—", "—", "—", format_money(result["total"]), "—"])
    print_table(headers, rows, "折旧费用计算与分配表")

    journal = ["借：制造费用——折旧费     " + format_money(result["departments"].get("制造费用", 0.0))]
    if result["departments"].get("管理费用", 0.0):
        journal.append("借：管理费用——折旧费     " + format_money(result["departments"]["管理费用"]))
    if result["departments"].get("销售费用", 0.0):
        journal.append("借：销售费用——折旧费     " + format_money(result["departments"]["销售费用"]))
    journal.append("贷：累计折旧     " + format_money(result["total"]))
    print_journal(journal)

    summary = [
        "生产车间固定资产折旧计入“制造费用”，行政管理部门计入“管理费用”，销售部门计入“销售费用”。",
        "折旧费用不直接计入“生产成本”，而是按受益部门先归集，再通过制造费用分配进入产品成本。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第二章 要素费用",
        "折旧费用计算与分配",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("折旧费用计算与分配表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"本月折旧费用合计 {format_money(result['total'])} 元，已按受益部门分配。",
    )



def amortize_low_value(items: Sequence[Dict[str, Any]], method: str) -> Dict[str, Any]:
    """低值易耗品摊销。

    method = "一次转销法"：领用时全额摊销；
    method = "五五摊销法"：领用时摊销 50%，报废时再摊销 50%（本表只列本月领用摊销额）。
    """
    if not items:
        raise ValidationError("至少需要一项低值易耗品领用记录。")
    if method not in ("一次转销法", "五五摊销法"):
        raise ValidationError("低值易耗品摊销方法只能是“一次转销法”或“五五摊销法”。")
    rows: List[Dict[str, Any]] = []
    department_totals: Dict[str, float] = {}
    ratio = 0.5 if method == "五五摊销法" else 1.0
    for index, item in enumerate(items, start=1):
        name = str(item.get("name") or f"低值易耗品{index}")
        amount = require_nonnegative(item.get("amount"), f"{name}的领用金额")
        department = str(item.get("department") or "制造费用")
        current = round(amount * ratio, 2)
        rows.append({
            "name": name,
            "amount": amount,
            "department": department,
            "current": current,
            "remaining": round(amount - current, 2),
        })
        department_totals[department] = round(department_totals.get(department, 0.0) + current, 2)
    total = round(sum(item["current"] for item in rows), 2)
    return {"rows": rows, "departments": department_totals, "total": total, "method": method, "ratio": ratio}


def run_low_value() -> None:
    """交互式低值易耗品摊销。"""
    print_heading("第二章 要素费用：低值易耗品摊销分配", "-")
    print("  摊销方法：1 一次转销法；2 五五摊销法")
    method_code = input_int("请选择摊销方法", 1, min_value=1, max_value=2, name="摊销方法")
    method = "一次转销法" if method_code == 1 else "五五摊销法"
    count = input_int("领用记录数", 3, min_value=1, max_value=20, name="领用记录数")
    defaults = [
        ("生产车间工具", 12000.0, 1),
        ("行政管理部门办公用具", 6000.0, 2),
        ("销售部门包装器具", 4000.0, 3),
    ]
    items = []
    for i in range(count):
        default_name, amount, department_code = defaults[i] if i < len(defaults) else (f"低值易耗品{i + 1}", 5000.0, 1)
        name = input_text(f"第{i + 1}项低值易耗品名称", default_name)
        amount_value = input_float(f"{name}的领用金额（元）", amount, min_value=0.0, name="领用金额")
        department_code = input_int(f"{name}的受益部门（1制造费用/2管理费用/3销售费用）", department_code, min_value=1, max_value=3, name="部门编号")
        items.append({"name": name, "amount": amount_value, "department": DEPARTMENT_NAMES[department_code]})

    result = amortize_low_value(items, method)
    question = (
        f"某企业本月领用低值易耗品若干，采用{method}核算。各项领用金额及受益部门如下表，"
        "要求计算本月应摊销金额、按部门汇总并编制会计分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "一次转销法：本月摊销额 = 领用金额",
        "五五摊销法：本月摊销额 = 领用金额 × 50%，报废时再摊销剩余 50%",
        "某部门摊销额 = 该部门各项低值易耗品本月摊销额之和",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = []
    for item in result["rows"]:
        if method == "五五摊销法":
            steps.append(
                f"{item['name']}：领用金额 {format_money(item['amount'])} 元，本月摊销 50% = {format_money(item['current'])} 元，"
                f"剩余 {format_money(item['remaining'])} 元待报废时摊销，计入{item['department']}。"
            )
        else:
            steps.append(
                f"{item['name']}：领用金额 {format_money(item['amount'])} 元，本月全额摊销 {format_money(item['current'])} 元，计入{item['department']}。"
            )
    for department, amount in result["departments"].items():
        steps.append(f"{department}本月低值易耗品摊销合计 = {format_money(amount)} 元。")
    steps.append(f"本月摊销总额 = {format_money(result['total'])} 元。")
    print_steps(steps)

    headers = ["低值易耗品名称", "领用金额（元）", "摊销方法", "本月摊销（元）", "尚待摊销（元）", "受益部门"]
    rows = [
        [item["name"], format_money(item["amount"]), method, format_money(item["current"]), format_money(item["remaining"]), item["department"]]
        for item in result["rows"]
    ]
    rows.append(["合计", format_money(sum(item["amount"] for item in result["rows"])), "—", format_money(result["total"]), format_money(sum(item["remaining"] for item in result["rows"])), "—"])
    print_table(headers, rows, "低值易耗品摊销分配表")

    journal = []
    for department, amount in result["departments"].items():
        journal.append(f"借：{department}——低值易耗品摊销     {format_money(amount)}")
    credit_account = "周转材料——低值易耗品（摊销）" if method == "五五摊销法" else "周转材料——低值易耗品"
    journal.append(f"贷：{credit_account}     {format_money(result['total'])}")
    if method == "五五摊销法":
        journal.append("说明：领用时还应按领用金额借记“周转材料——低值易耗品（在用）”，贷记“周转材料——低值易耗品（在库）”。")
    print_journal(journal)

    summary = [
        f"采用{method}，本月低值易耗品摊销额为 {format_money(result['total'])} 元。",
        "生产车间领用计入制造费用，行政管理部门计入管理费用，销售部门计入销售费用。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第二章 要素费用",
        f"低值易耗品摊销——{method}",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("低值易耗品摊销分配表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"{method}本月摊销额 {format_money(result['total'])} 元。",
    )



# ---------------------------------------------------------------------------
# 五、税金和其他支出费用分配
# ---------------------------------------------------------------------------
def allocate_taxes_other(items: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """归集税金和其他支出，并按费用类别汇总。

    items 中每项包含：name、amount、department、kind（"税金"或"其他支出"）。
    """
    if not items:
        raise ValidationError("至少需要一项税金或其他支出。")
    rows: List[Dict[str, Any]] = []
    department_totals: Dict[str, float] = {}
    kind_totals: Dict[str, float] = {"税金": 0.0, "其他支出": 0.0}
    for index, item in enumerate(items, start=1):
        name = str(item.get("name") or f"项目{index}")
        amount = require_nonnegative(item.get("amount"), f"{name}的金额")
        department = str(item.get("department") or "管理费用")
        kind = str(item.get("kind") or "其他支出")
        if kind not in ("税金", "其他支出"):
            raise ValidationError(f"{name}的类别必须是“税金”或“其他支出”。")
        rows.append({"name": name, "amount": amount, "department": department, "kind": kind})
        department_totals[department] = round(department_totals.get(department, 0.0) + amount, 2)
        kind_totals[kind] = round(kind_totals.get(kind, 0.0) + amount, 2)
    total = round(sum(item["amount"] for item in rows), 2)
    return {"rows": rows, "departments": department_totals, "kinds": kind_totals, "total": total}


def run_taxes_other() -> None:
    """交互式税金和其他支出费用分配。"""
    print_heading("第二章 要素费用：税金和其他支出分配", "-")
    print("  受益部门：1 制造费用；2 管理费用；3 销售费用；4 财务费用")
    print("  费用类别：1 税金；2 其他支出")
    count = input_int("费用项目数", 5, min_value=1, max_value=30, name="费用项目数")
    defaults = [
        ("房产税", 3000.0, 2, 1),
        ("土地使用税", 2000.0, 2, 1),
        ("生产车间办公费", 1500.0, 1, 2),
        ("销售部门差旅费", 2500.0, 3, 2),
        ("行政管理部门其他支出", 1000.0, 2, 2),
    ]
    items = []
    for i in range(count):
        default_name, amount, department_code, kind_code = (
            defaults[i] if i < len(defaults) else (f"费用项目{i + 1}", 1000.0, 2, 2)
        )
        name = input_text(f"第{i + 1}项费用名称", default_name)
        amount_value = input_float(f"{name}的金额（元）", amount, min_value=0.0, name="费用金额")
        department_code = input_int(f"{name}的受益部门（1制造费用/2管理费用/3销售费用/4财务费用）", department_code, min_value=1, max_value=4, name="部门编号")
        kind_code = input_int(f"{name}的类别（1税金/2其他支出）", kind_code, min_value=1, max_value=2, name="类别编号")
        items.append({
            "name": name,
            "amount": amount_value,
            "department": DEPARTMENT_NAMES[department_code],
            "kind": "税金" if kind_code == 1 else "其他支出",
        })

    result = allocate_taxes_other(items)
    question = (
        "某企业本月发生房产税、土地使用税、车间办公费、销售部门差旅费和行政管理部门其他支出等。"
        "要求按受益部门归集税金和其他支出，计算各部门费用合计并编制会计分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "某部门税金及附加/其他支出 = 该部门各明细项目金额之和",
        "税金通常先贷记“应交税费”，其他支出通常贷记“银行存款”“库存现金”或其他应付款。",
        "生产车间发生的费用计入“制造费用”，行政管理部门计入“管理费用”，销售部门计入“销售费用”。",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = []
    for item in result["rows"]:
        steps.append(
            f"{item['name']}：金额 {format_money(item['amount'])} 元，属于{item['kind']}，计入{item['department']}。"
        )
    for department, amount in result["departments"].items():
        steps.append(f"{department}合计 = {format_money(amount)} 元。")
    steps.append(f"全部项目合计 = {format_money(result['total'])} 元；其中税金 {format_money(result['kinds']['税金'])} 元，其他支出 {format_money(result['kinds']['其他支出'])} 元。")
    print_steps(steps)

    headers = ["费用项目", "金额（元）", "类别", "受益部门"]
    rows = [[item["name"], format_money(item["amount"]), item["kind"], item["department"]] for item in result["rows"]]
    rows.append(["合计", format_money(result["total"]), "—", "—"])
    print_table(headers, rows, "税金和其他支出分配表")

    journal = []
    for item in result["rows"]:
        journal.append(f"借：{item['department']}——{item['name']}     {format_money(item['amount'])}")
    if result["kinds"]["税金"]:
        journal.append(f"贷：应交税费     {format_money(result['kinds']['税金'])}")
    other = result["kinds"]["其他支出"]
    if other:
        journal.append(f"贷：银行存款等     {format_money(other)}")
    print_journal(journal)

    summary = [
        "税金和其他支出应按受益部门归集，不能直接全部计入产品成本。",
        "本期费用合计与各明细项目金额合计一致，借贷双方金额平衡。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第二章 要素费用",
        "税金和其他支出分配",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("税金和其他支出分配表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"税金和其他支出合计 {format_money(result['total'])} 元，已按受益部门归集。",
    )


def run() -> None:
    """第二章菜单。"""
    options = [
        ("1", "材料费用分配（定额消耗量/定额费用/重量/产量）", run_material),
        ("2", "外购动力费用分配", run_power),
        ("3", "职工薪酬费用分配（工资、福利费、社保）", run_payroll),
        ("4", "折旧费用计算与分配", run_depreciation),
        ("5", "低值易耗品摊销分配", run_low_value),
        ("6", "税金和其他支出费用分配", run_taxes_other),
    ]
    run_menu("第二章 工业企业要素费用的归集与分配", options, back_text="返回主菜单")

