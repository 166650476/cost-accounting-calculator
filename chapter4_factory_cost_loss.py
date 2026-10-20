"""第四章 制造费用、生产损失与期间费用核算。

覆盖：
1. 制造费用归集与分配：生产工时、生产工资、机器工时、年度计划分配率法；
2. 不可修复废品损失：按定额成本、按实际成本；
3. 可修复废品损失；
4. 停工损失：正常停工与非正常停工；
5. 销售费用、管理费用、财务费用的归集与结转。

所有计算输出文字题意、公式、步骤、表格、分录和总结，并自动保存 CSV。
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
    require_positive,
    run_menu,
    safe_div,
)


OVERHEAD_SOURCES = ["原材料", "应付职工薪酬", "累计折旧", "银行存款", "其他应付款"]
OVERHEAD_METHODS = {
    1: "生产工时比例法",
    2: "生产工资比例法",
    3: "机器工时比例法",
}


# ---------------------------------------------------------------------------
# 一、制造费用归集与分配
# ---------------------------------------------------------------------------
def collect_overhead(items: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """归集制造费用明细项目，并按贷方来源汇总。"""
    if not items:
        raise ValidationError("至少需要一项制造费用明细。")
    rows: List[Dict[str, Any]] = []
    source_totals: Dict[str, float] = {}
    for index, item in enumerate(items, start=1):
        name = str(item.get("name") or f"费用项目{index}")
        amount = require_nonnegative(item.get("amount"), f"{name}的金额")
        source = str(item.get("source") or "银行存款")
        if source not in OVERHEAD_SOURCES:
            raise ValidationError(f"{name}的贷方来源必须是：{'、'.join(OVERHEAD_SOURCES)}。")
        rows.append({"name": name, "amount": amount, "source": source})
        source_totals[source] = round(source_totals.get(source, 0.0) + amount, 2)
    total = round(sum(item["amount"] for item in rows), 2)
    return {"rows": rows, "sources": source_totals, "total": total}


def allocate_overhead(total: Any, products: Sequence[Dict[str, Any]], method: str) -> Dict[str, Any]:
    """按生产工时、生产工资或机器工时分配制造费用。"""
    if not products:
        raise ValidationError("至少需要一种产品。")
    if method not in OVERHEAD_METHODS.values():
        raise ValidationError(f"未知的制造费用分配方法：{method}")
    total_value = require_nonnegative(total, "制造费用总额")
    names = [str(product.get("name") or f"产品{i + 1}") for i, product in enumerate(products)]
    bases: List[float] = []
    for name, product in zip(names, products):
        if method == "生产工时比例法":
            base = require_nonnegative(product.get("hours"), f"{name}的生产工时")
        elif method == "生产工资比例法":
            base = require_nonnegative(product.get("wages"), f"{name}的生产工资")
        else:
            base = require_nonnegative(product.get("machine_hours"), f"{name}的机器工时")
        bases.append(base)
    allocations, total_base = allocate_amount(total_value, bases, labels=names)
    rate = safe_div(total_value, total_base, "制造费用分配率")
    return {
        "method": method,
        "total": total_value,
        "names": names,
        "bases": bases,
        "total_base": total_base,
        "rate": rate,
        "allocations": allocations,
    }


def annual_planned_rate(
    annual_overhead: Any,
    annual_hours: Any,
    monthly_overhead: Any,
    products: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """年度计划分配率法。

    年度计划分配率 = 年度计划制造费用 ÷ 年度计划产量定额工时；
    本月某产品分配额 = 该产品本月实际工时 × 年度计划分配率；
    差异 = 本月实际制造费用 - 本月按计划分配率分配额。
    """
    annual = require_nonnegative(annual_overhead, "年度计划制造费用")
    annual_hours_value = require_positive(annual_hours, "年度计划定额工时")
    monthly = require_nonnegative(monthly_overhead, "本月实际制造费用")
    if not products:
        raise ValidationError("至少需要一种产品。")
    rate = safe_div(annual, annual_hours_value, "年度计划分配率")
    names = [str(product.get("name") or f"产品{i + 1}") for i, product in enumerate(products)]
    hours = [require_nonnegative(product.get("monthly_hours"), f"{name}本月实际工时") for name, product in zip(names, products)]
    allocations, total_hours = allocate_amount(
        round(rate * sum(hours), 2),
        hours,
        labels=names,
    )
    allocated_total = round(sum(allocations), 2)
    difference = round(monthly - allocated_total, 2)
    return {
        "rate": rate,
        "annual": annual,
        "annual_hours": annual_hours_value,
        "monthly": monthly,
        "names": names,
        "hours": hours,
        "total_hours": total_hours,
        "allocations": allocations,
        "allocated_total": allocated_total,
        "difference": difference,
    }


# ---------------------------------------------------------------------------
# 二、废品损失与停工损失
# ---------------------------------------------------------------------------
def unrepairable_quota(
    defective_qty: Any,
    unit_quota: Dict[str, Any],
    scrap_value: Any,
    compensation: Any,
) -> Dict[str, Any]:
    """不可修复废品损失——按定额成本计算。"""
    qty = require_positive(defective_qty, "废品数量")
    material = require_nonnegative(unit_quota.get("material"), "单位废品材料定额成本")
    labor = require_nonnegative(unit_quota.get("labor"), "单位废品人工定额成本")
    overhead = require_nonnegative(unit_quota.get("overhead"), "单位废品制造费用定额成本")
    scrap = require_nonnegative(scrap_value, "废品残料价值")
    compensate = require_nonnegative(compensation, "赔款收入")
    total = round((material + labor + overhead) * qty, 2)
    net_loss = round(total - scrap - compensate, 2)
    return {
        "qty": qty,
        "unit": {"material": material, "labor": labor, "overhead": overhead},
        "total": total,
        "scrap": scrap,
        "compensation": compensate,
        "net_loss": net_loss,
        "material_total": round(material * qty, 2),
        "labor_total": round(labor * qty, 2),
        "overhead_total": round(overhead * qty, 2),
    }


def unrepairable_actual(
    total_cost: Any,
    total_output: Any,
    defective_qty: Any,
    scrap_value: Any,
    compensation: Any,
) -> Dict[str, Any]:
    """不可修复废品损失——按实际成本计算。

    假设按全部产品实际总成本与总产量计算实际单位成本，废品成本 = 废品数量 × 实际单位成本。
    """
    cost = require_nonnegative(total_cost, "产品实际总成本")
    output = require_positive(total_output, "产品总产量")
    defective = require_positive(defective_qty, "废品数量")
    if defective > output + 1e-9:
        raise ValidationError("废品数量不能大于产品总产量。")
    scrap = require_nonnegative(scrap_value, "废品残料价值")
    compensate = require_nonnegative(compensation, "赔款收入")
    unit_cost = safe_div(cost, output, "实际单位成本")
    defective_cost = round(unit_cost * defective, 2)
    net_loss = round(defective_cost - scrap - compensate, 2)
    return {
        "total_cost": cost,
        "total_output": output,
        "defective_qty": defective,
        "unit_cost": unit_cost,
        "defective_cost": defective_cost,
        "scrap": scrap,
        "compensation": compensate,
        "net_loss": net_loss,
    }


def repairable_loss(
    material: Any,
    labor: Any,
    overhead: Any,
    scrap_value: Any,
    compensation: Any,
) -> Dict[str, Any]:
    """可修复废品修复费用及净损失。"""
    material_value = require_nonnegative(material, "修复用材料")
    labor_value = require_nonnegative(labor, "修复用人工")
    overhead_value = require_nonnegative(overhead, "修复用制造费用")
    scrap = require_nonnegative(scrap_value, "残料价值")
    compensate = require_nonnegative(compensation, "赔款收入")
    total = round(material_value + labor_value + overhead_value, 2)
    net_loss = round(total - scrap - compensate, 2)
    return {
        "material": material_value,
        "labor": labor_value,
        "overhead": overhead_value,
        "total": total,
        "scrap": scrap,
        "compensation": compensate,
        "net_loss": net_loss,
    }


def downtime_loss(total_loss: Any, is_normal: bool, insurance: Any = 0.0) -> Dict[str, Any]:
    """停工损失：正常停工计入生产成本；非正常停工计入营业外支出。"""
    loss = require_nonnegative(total_loss, "停工损失总额")
    insurance_value = require_nonnegative(insurance, "保险赔偿")
    net = round(loss - insurance_value, 2)
    if net < 0:
        raise ValidationError("保险赔偿不能大于停工损失总额。")
    return {
        "total": loss,
        "is_normal": is_normal,
        "insurance": insurance_value,
        "net": net,
        "treatment": "计入生产成本（停工损失）" if is_normal else "计入营业外支出",
    }


def period_expenses(sales: Any, admin: Any, finance: Any) -> Dict[str, Any]:
    """归集期间费用。"""
    sales_value = require_nonnegative(sales, "销售费用")
    admin_value = require_nonnegative(admin, "管理费用")
    finance_value = require_nonnegative(finance, "财务费用")
    total = round(sales_value + admin_value + finance_value, 2)
    return {
        "sales": sales_value,
        "admin": admin_value,
        "finance": finance_value,
        "total": total,
    }



# ---------------------------------------------------------------------------
# 三、交互式：制造费用归集与分配
# ---------------------------------------------------------------------------
def run_collect_overhead() -> None:
    """制造费用归集。"""
    print_heading("第四章 制造费用、生产损失与期间费用：制造费用归集", "-")
    print("  贷方来源：1 原材料；2 应付职工薪酬；3 累计折旧；4 银行存款；5 其他应付款")
    count = input_int("制造费用明细项目数", 5, min_value=1, max_value=30, name="明细项目数")
    defaults = [
        ("机物料消耗", 8000.0, 1),
        ("车间管理人员工资", 12000.0, 2),
        ("车间固定资产折旧", 10000.0, 3),
        ("车间水电费", 5000.0, 4),
        ("车间劳动保护费", 3000.0, 4),
    ]
    items = []
    for i in range(count):
        default_name, amount, source_code = defaults[i] if i < len(defaults) else (f"费用项目{i + 1}", 2000.0, 4)
        name = input_text(f"第{i + 1}项制造费用名称", default_name)
        amount_value = input_float(f"{name}的金额（元）", amount, min_value=0.0, name="费用金额")
        source_code = input_int(f"{name}的贷方来源（1原材料/2应付职工薪酬/3累计折旧/4银行存款/5其他应付款）", source_code, min_value=1, max_value=5, name="来源编号")
        items.append({"name": name, "amount": amount_value, "source": OVERHEAD_SOURCES[source_code - 1]})

    result = collect_overhead(items)
    question = (
        "某基本生产车间本月发生机物料消耗、车间管理人员工资、车间固定资产折旧、水电费和劳动保护费等间接费用。"
        "要求归集制造费用，编制制造费用明细表和会计分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "制造费用合计 = 各制造费用明细项目金额之和",
        "制造费用属于间接计入费用，期末应按一定标准分配计入各产品成本。",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [f"{item['name']}：{format_money(item['amount'])} 元，贷记“{item['source']}”。" for item in result["rows"]]
    steps.append(f"制造费用合计 = {format_money(result['total'])} 元。")
    print_steps(steps)

    headers = ["费用项目", "金额（元）", "贷方来源"]
    rows = [[item["name"], format_money(item["amount"]), item["source"]] for item in result["rows"]]
    rows.append(["合计", format_money(result["total"]), "—"])
    print_table(headers, rows, "制造费用明细表")

    journal = [f"借：制造费用     {format_money(result['total'])}"]
    for source, amount in result["sources"].items():
        journal.append(f"贷：{source}     {format_money(amount)}")
    print_journal(journal)

    summary = [
        "制造费用先通过“制造费用”账户归集，再按生产工时、生产工资或机器工时等标准分配。",
        "车间管理人员工资、车间折旧、机物料消耗等均属于制造费用，不直接计入产品成本。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第四章 制造费用与生产损失",
        "制造费用归集",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("制造费用明细表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"制造费用归集总额 {format_money(result['total'])} 元。",
    )



def run_overhead_allocation() -> None:
    """制造费用分配（四种方法）。"""
    print_heading("第四章 制造费用、生产损失与期间费用：制造费用分配", "-")
    print("  分配方法：1 生产工时比例法；2 生产工资比例法；3 机器工时比例法；4 年度计划分配率法")
    method_code = input_int("请选择分配方法", 1, min_value=1, max_value=4, name="分配方法")
    if method_code == 4:
        _run_annual_planned()
        return

    method = OVERHEAD_METHODS[method_code]
    total = input_float("制造费用总额（元）", 38000.0, min_value=0.0, name="制造费用")
    count = input_int("产品种类数", 2, min_value=1, max_value=20, name="产品种类数")
    defaults = [
        ("甲产品", 2000.0, 40000.0, 1200.0),
        ("乙产品", 1000.0, 20000.0, 800.0),
    ]
    products = []
    for i in range(count):
        default_name, hours, wages, machine_hours = defaults[i] if i < len(defaults) else (f"产品{i + 1}", 1000.0, 20000.0, 800.0)
        name = input_text(f"第{i + 1}种产品名称", default_name)
        products.append({
            "name": name,
            "hours": input_float(f"{name}的生产工时", hours, min_value=0.0, name="生产工时"),
            "wages": input_float(f"{name}的生产工资（元）", wages, min_value=0.0, name="生产工资"),
            "machine_hours": input_float(f"{name}的机器工时", machine_hours, min_value=0.0, name="机器工时"),
        })

    result = allocate_overhead(total, products, method)
    question = (
        f"某基本生产车间本月制造费用总额为 {format_money(result['total'])} 元，生产多种产品。"
        f"采用{method}分配制造费用，要求计算分配率、各产品应负担的制造费用并编制分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    basis_name = {"生产工时比例法": "生产工时", "生产工资比例法": "生产工资", "机器工时比例法": "机器工时"}[method]
    formulas = [
        f"制造费用分配率 = 制造费用总额 ÷ 各种产品{basis_name}合计",
        f"某产品应负担制造费用 = 该产品{basis_name} × 制造费用分配率",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"{basis_name}合计 = {result['total_base']:,.2f}。",
        f"制造费用分配率 = {format_money(result['total'])} ÷ {result['total_base']:,.2f} = {result['rate']:.6f}。",
    ]
    for name, base, amount in zip(result["names"], result["bases"], result["allocations"]):
        steps.append(f"{name}：{basis_name} {base:,.2f} × {result['rate']:.6f} = {format_money(amount)} 元。")
    steps.append(f"验算：分配额合计 {format_money(sum(result['allocations']))} 元 = 制造费用总额。")
    print_steps(steps)

    headers = ["产品名称", basis_name, "分配率", "分配金额（元）"]
    rows = [[name, f"{base:,.2f}", f"{result['rate']:.6f}", format_money(amount)] for name, base, amount in zip(result["names"], result["bases"], result["allocations"])]
    rows.append(["合计", f"{result['total_base']:,.2f}", "—", format_money(sum(result["allocations"]))])
    print_table(headers, rows, "制造费用分配表")

    journal = ["借：生产成本——基本生产成本"]
    for name, amount in zip(result["names"], result["allocations"]):
        journal.append(f"    ——{name}     {format_money(amount)}")
    journal.append(f"贷：制造费用     {format_money(result['total'])}")
    print_journal(journal)

    summary = [
        f"采用{method}，分配率 {result['rate']:.6f}。",
        "分配标准应与制造费用的发生具有较强相关性；方法一经确定，应保持前后期一致。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第四章 制造费用与生产损失",
        f"制造费用分配——{method}",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("制造费用分配表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"{method}分配率 {result['rate']:.6f}，制造费用分配完成。",
    )



def _run_annual_planned() -> None:
    """年度计划分配率法。"""
    annual_overhead = input_float("年度计划制造费用（元）", 480000.0, min_value=0.0, name="年度计划制造费用")
    annual_hours = input_float("年度计划定额工时", 120000.0, min_value=0.0, name="年度计划定额工时")
    monthly_overhead = input_float("本月实际制造费用（元）", 12500.0, min_value=0.0, name="本月实际制造费用")
    count = input_int("产品种类数", 2, min_value=1, max_value=20, name="产品种类数")
    defaults = [("甲产品", 2000.0), ("乙产品", 1000.0)]
    products = []
    for i in range(count):
        default_name, hours = defaults[i] if i < len(defaults) else (f"产品{i + 1}", 1000.0)
        name = input_text(f"第{i + 1}种产品名称", default_name)
        hours_value = input_float(f"{name}本月实际工时", hours, min_value=0.0, name="本月实际工时")
        products.append({"name": name, "monthly_hours": hours_value})

    result = annual_planned_rate(annual_overhead, annual_hours, monthly_overhead, products)
    question = (
        f"某车间年度计划制造费用 {format_money(result['annual'])} 元，年度计划定额工时 {result['annual_hours']:,.2f}；"
        f"本月实际发生制造费用 {format_money(result['monthly'])} 元。采用年度计划分配率法分配本月制造费用，"
        "并计算月末差异。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "年度计划分配率 = 年度计划制造费用 ÷ 年度计划定额工时",
        "某产品本月应分配制造费用 = 该产品本月实际工时 × 年度计划分配率",
        "本月分配额合计 = Σ各产品本月分配额",
        "成本差异 = 本月实际制造费用 - 本月分配额合计",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"年度计划分配率 = {format_money(result['annual'])} ÷ {result['annual_hours']:,.2f} = {result['rate']:.6f} 元/工时。",
    ]
    for name, hours, amount in zip(result["names"], result["hours"], result["allocations"]):
        steps.append(f"{name}：本月实际工时 {hours:,.2f} × {result['rate']:.6f} = {format_money(amount)} 元。")
    steps.append(f"本月分配额合计 = {format_money(result['allocated_total'])} 元。")
    steps.append(f"成本差异 = {format_money(result['monthly'])} - {format_money(result['allocated_total'])} = {format_money(result['difference'])} 元。")
    print_steps(steps)

    headers = ["产品名称", "本月实际工时", "年度计划分配率", "本月分配额（元）"]
    rows = [[name, f"{hours:,.2f}", f"{result['rate']:.6f}", format_money(amount)] for name, hours, amount in zip(result["names"], result["hours"], result["allocations"])]
    rows.append(["合计", f"{sum(result['hours']):,.2f}", "—", format_money(result["allocated_total"])])
    print_table(headers, rows, "年度计划分配率法制造费用分配表")

    journal = ["借：生产成本——基本生产成本"]
    for name, amount in zip(result["names"], result["allocations"]):
        journal.append(f"    ——{name}     {format_money(amount)}")
    journal.append(f"贷：制造费用     {format_money(result['allocated_total'])}")
    if abs(result["difference"]) >= 0.01:
        if result["difference"] > 0:
            journal.append(f"借：生产成本——基本生产成本     {format_money(result['difference'])}")
            journal.append(f"贷：制造费用     {format_money(result['difference'])}")
        else:
            journal.append(f"借：制造费用     {format_money(-result['difference'])}")
            journal.append(f"贷：生产成本——基本生产成本     {format_money(-result['difference'])}")
    print_journal(journal)

    summary = [
        f"年度计划分配率为 {result['rate']:.6f} 元/工时。",
        f"本月按计划分配 {format_money(result['allocated_total'])} 元，实际发生 {format_money(result['monthly'])} 元，差异 {format_money(result['difference'])} 元。",
        "年度计划分配率法可以简化日常核算，但年末应将差异调整至实际成本；本例按月末差异调整演示。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第四章 制造费用与生产损失",
        "制造费用分配——年度计划分配率法",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("年度计划分配率法制造费用分配表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"年度计划分配率 {result['rate']:.6f}，本月分配 {format_money(result['allocated_total'])} 元，差异 {format_money(result['difference'])} 元。",
    )



# ---------------------------------------------------------------------------
# 四、交互式：废品损失与停工损失
# ---------------------------------------------------------------------------
def run_unrepairable_quota() -> None:
    """不可修复废品损失——按定额成本。"""
    print_heading("第四章 生产损失：不可修复废品损失（按定额成本）", "-")
    product = input_text("产品名称", "甲产品")
    qty = input_float("不可修复废品数量", 20.0, min_value=0.0, name="废品数量")
    material = input_float("单位废品材料定额成本（元）", 80.0, min_value=0.0, name="材料定额")
    labor = input_float("单位废品人工定额成本（元）", 40.0, min_value=0.0, name="人工定额")
    overhead = input_float("单位废品制造费用定额成本（元）", 20.0, min_value=0.0, name="制造费用定额")
    scrap = input_float("废品残料价值（元）", 300.0, min_value=0.0, name="残料价值")
    compensation = input_float("应收赔款（元）", 500.0, min_value=0.0, name="赔款收入")
    result = unrepairable_quota(qty, {"material": material, "labor": labor, "overhead": overhead}, scrap, compensation)

    question = (
        f"某企业生产{product}，本月发现不可修复废品 {qty:g} 件，按定额成本计算废品损失。"
        "单位废品材料、人工、制造费用定额分别为 "
        f"{format_money(material)}、{format_money(labor)}、{format_money(overhead)} 元；"
        f"残料价值 {format_money(scrap)} 元，应收赔款 {format_money(compensation)} 元。要求计算废品损失并编制分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "废品定额成本 = 废品数量 ×（单位材料定额 + 单位人工定额 + 单位制造费用定额）",
        "废品净损失 = 废品定额成本 - 残料价值 - 应收赔款",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"材料定额成本 = {qty:g} × {format_money(material)} = {format_money(result['material_total'])} 元。",
        f"人工定额成本 = {qty:g} × {format_money(labor)} = {format_money(result['labor_total'])} 元。",
        f"制造费用定额成本 = {qty:g} × {format_money(overhead)} = {format_money(result['overhead_total'])} 元。",
        f"废品定额成本合计 = {format_money(result['total'])} 元。",
        f"废品净损失 = {format_money(result['total'])} - {format_money(result['scrap'])} - {format_money(result['compensation'])} = {format_money(result['net_loss'])} 元。",
    ]
    print_steps(steps)

    headers = ["成本项目", "单位定额（元/件）", "废品数量", "定额成本（元）"]
    rows = [
        ["直接材料", format_money(material), f"{qty:g}", format_money(result["material_total"])],
        ["直接人工", format_money(labor), f"{qty:g}", format_money(result["labor_total"])],
        ["制造费用", format_money(overhead), f"{qty:g}", format_money(result["overhead_total"])],
        ["合计", "—", f"{qty:g}", format_money(result["total"])],
        ["减：残料价值", "—", "—", format_money(result["scrap"])],
        ["减：应收赔款", "—", "—", format_money(result["compensation"])],
        ["废品净损失", "—", "—", format_money(result["net_loss"])],
    ]
    print_table(headers, rows, "不可修复废品损失计算表（按定额成本）")

    journal = [
        f"借：废品损失——{product}     {format_money(result['total'])}",
        f"贷：生产成本——基本生产成本（{product}）     {format_money(result['total'])}",
        f"借：原材料     {format_money(result['scrap'])}",
        f"借：其他应收款     {format_money(result['compensation'])}",
        f"贷：废品损失——{product}     {format_money(result['scrap'] + result['compensation'])}",
        f"借：生产成本——基本生产成本（{product}）——废品损失     {format_money(result['net_loss'])}",
        f"贷：废品损失——{product}     {format_money(result['net_loss'])}",
    ]
    print_journal(journal)

    summary = [
        f"废品定额成本 {format_money(result['total'])} 元，扣除残料和赔款后净损失 {format_money(result['net_loss'])} 元。",
        "按定额成本计算废品损失，适用于定额资料比较健全、废品数量较少的企业。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第四章 制造费用与生产损失",
        "不可修复废品损失——按定额成本",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("不可修复废品损失计算表（按定额成本）", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"废品净损失 {format_money(result['net_loss'])} 元。",
    )



def run_unrepairable_actual() -> None:
    """不可修复废品损失——按实际成本。"""
    print_heading("第四章 生产损失：不可修复废品损失（按实际成本）", "-")
    product = input_text("产品名称", "乙产品")
    total_cost = input_float("本月产品实际总成本（元）", 100000.0, min_value=0.0, name="实际总成本")
    total_output = input_float("本月产品总产量", 1000.0, min_value=0.0, name="总产量")
    qty = input_float("不可修复废品数量", 20.0, min_value=0.0, name="废品数量")
    scrap = input_float("废品残料价值（元）", 300.0, min_value=0.0, name="残料价值")
    compensation = input_float("应收赔款（元）", 500.0, min_value=0.0, name="赔款收入")
    result = unrepairable_actual(total_cost, total_output, qty, scrap, compensation)

    question = (
        f"某企业本月生产{product}，实际总成本 {format_money(result['total_cost'])} 元，总产量 {result['total_output']:,.2f} 件，"
        f"其中不可修复废品 {result['defective_qty']:g} 件。按实际成本计算废品损失，残料价值 "
        f"{format_money(result['scrap'])} 元，应收赔款 {format_money(result['compensation'])} 元。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "实际单位成本 = 产品实际总成本 ÷ 产品总产量",
        "废品实际成本 = 废品数量 × 实际单位成本",
        "废品净损失 = 废品实际成本 - 残料价值 - 应收赔款",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"实际单位成本 = {format_money(result['total_cost'])} ÷ {result['total_output']:,.2f} = {format_money(result['unit_cost'])} 元/件。",
        f"废品实际成本 = {result['defective_qty']:g} × {format_money(result['unit_cost'])} = {format_money(result['defective_cost'])} 元。",
        f"废品净损失 = {format_money(result['defective_cost'])} - {format_money(result['scrap'])} - {format_money(result['compensation'])} = {format_money(result['net_loss'])} 元。",
    ]
    print_steps(steps)

    headers = ["项目", "金额/数量"]
    rows = [
        ["产品实际总成本（元）", format_money(result["total_cost"])],
        ["产品总产量（件）", f"{result['total_output']:,.2f}"],
        ["实际单位成本（元/件）", format_money(result["unit_cost"])],
        ["不可修复废品数量（件）", f"{result['defective_qty']:g}"],
        ["废品实际成本（元）", format_money(result["defective_cost"])],
        ["减：残料价值（元）", format_money(result["scrap"])],
        ["减：应收赔款（元）", format_money(result["compensation"])],
        ["废品净损失（元）", format_money(result["net_loss"])],
    ]
    print_table(headers, rows, "不可修复废品损失计算表（按实际成本）")

    journal = [
        f"借：废品损失——{product}     {format_money(result['defective_cost'])}",
        f"贷：生产成本——基本生产成本（{product}）     {format_money(result['defective_cost'])}",
        f"借：原材料     {format_money(result['scrap'])}",
        f"借：其他应收款     {format_money(result['compensation'])}",
        f"贷：废品损失——{product}     {format_money(result['scrap'] + result['compensation'])}",
        f"借：生产成本——基本生产成本（{product}）——废品损失     {format_money(result['net_loss'])}",
        f"贷：废品损失——{product}     {format_money(result['net_loss'])}",
    ]
    print_journal(journal)

    summary = [
        f"按实际成本计算的废品净损失为 {format_money(result['net_loss'])} 元。",
        "按实际成本计算要求企业有完整的产量和成本资料；若废品数量较少，也可采用简化方法。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第四章 制造费用与生产损失",
        "不可修复废品损失——按实际成本",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("不可修复废品损失计算表（按实际成本）", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"废品净损失 {format_money(result['net_loss'])} 元。",
    )



def run_repairable() -> None:
    """可修复废品损失。"""
    print_heading("第四章 生产损失：可修复废品损失", "-")
    product = input_text("产品名称", "丙产品")
    material = input_float("修复用材料（元）", 800.0, min_value=0.0, name="修复用材料")
    labor = input_float("修复用人工（元）", 1200.0, min_value=0.0, name="修复用人工")
    overhead = input_float("修复用制造费用（元）", 500.0, min_value=0.0, name="修复用制造费用")
    scrap = input_float("残料价值（元）", 100.0, min_value=0.0, name="残料价值")
    compensation = input_float("应收赔款（元）", 200.0, min_value=0.0, name="赔款收入")
    result = repairable_loss(material, labor, overhead, scrap, compensation)

    question = (
        f"某企业生产{product}，本月发现可修复废品。修复过程中耗用材料 {format_money(result['material'])} 元、"
        f"人工 {format_money(result['labor'])} 元、制造费用 {format_money(result['overhead'])} 元；"
        f"回收残料 {format_money(result['scrap'])} 元，应收赔款 {format_money(result['compensation'])} 元。"
        "要求计算可修复废品损失并编制分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "可修复废品修复费用 = 修复用材料 + 修复用人工 + 修复用制造费用",
        "可修复废品净损失 = 修复费用 - 残料价值 - 应收赔款",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"修复费用合计 = {format_money(result['material'])} + {format_money(result['labor'])} + {format_money(result['overhead'])} = {format_money(result['total'])} 元。",
        f"可修复废品净损失 = {format_money(result['total'])} - {format_money(result['scrap'])} - {format_money(result['compensation'])} = {format_money(result['net_loss'])} 元。",
    ]
    print_steps(steps)

    headers = ["成本项目", "金额（元）"]
    rows = [
        ["修复用材料", format_money(result["material"])],
        ["修复用人工", format_money(result["labor"])],
        ["修复用制造费用", format_money(result["overhead"])],
        ["修复费用合计", format_money(result["total"])],
        ["减：残料价值", format_money(result["scrap"])],
        ["减：应收赔款", format_money(result["compensation"])],
        ["可修复废品净损失", format_money(result["net_loss"])],
    ]
    print_table(headers, rows, "可修复废品损失计算表")

    journal = [
        f"借：废品损失——{product}     {format_money(result['total'])}",
        f"贷：原材料     {format_money(result['material'])}",
        f"贷：应付职工薪酬     {format_money(result['labor'])}",
        f"贷：制造费用     {format_money(result['overhead'])}",
        f"借：原材料     {format_money(result['scrap'])}",
        f"借：其他应收款     {format_money(result['compensation'])}",
        f"贷：废品损失——{product}     {format_money(result['scrap'] + result['compensation'])}",
        f"借：生产成本——基本生产成本（{product}）——废品损失     {format_money(result['net_loss'])}",
        f"贷：废品损失——{product}     {format_money(result['net_loss'])}",
    ]
    print_journal(journal)

    summary = [
        f"可修复废品修复费用 {format_money(result['total'])} 元，净损失 {format_money(result['net_loss'])} 元。",
        "可修复废品在修复后仍可作为合格品出售，因此只将修复费用扣除残料和赔款后的净损失计入产品成本。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第四章 制造费用与生产损失",
        "可修复废品损失",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("可修复废品损失计算表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"可修复废品净损失 {format_money(result['net_loss'])} 元。",
    )


def run_downtime() -> None:
    """停工损失核算。"""
    print_heading("第四章 生产损失：停工损失", "-")
    total_loss = input_float("停工期间发生的损失总额（元）", 9000.0, min_value=0.0, name="停工损失")
    is_normal = input_yes_no("是否属于正常停工（如计划减产、季节性停工）", True)
    insurance = input_float("保险赔偿或责任赔偿（元）", 0.0 if is_normal else 2000.0, min_value=0.0, name="赔偿收入")
    result = downtime_loss(total_loss, is_normal, insurance)

    question = (
        f"某企业本月发生停工，停工期间发生工资、折旧、水电等损失合计 {format_money(result['total'])} 元；"
        f"取得赔偿 {format_money(result['insurance'])} 元。该停工属于{'正常' if is_normal else '非正常'}停工。"
        "要求计算停工净损失并编制会计分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "停工净损失 = 停工损失总额 - 保险赔偿/责任赔偿",
        "正常停工损失计入生产成本（停工损失），由开工后产品成本负担；",
        "非正常停工损失（如自然灾害、重大事故）计入营业外支出。",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"停工净损失 = {format_money(result['total'])} - {format_money(result['insurance'])} = {format_money(result['net'])} 元。",
        f"处理方式：{result['treatment']}。",
    ]
    print_steps(steps)

    headers = ["项目", "金额（元）"]
    rows = [
        ["停工损失总额", format_money(result["total"])],
        ["减：保险/责任赔偿", format_money(result["insurance"])],
        ["停工净损失", format_money(result["net"])],
        ["处理方向", result["treatment"]],
    ]
    print_table(headers, rows, "停工损失计算表")

    journal = [
        f"借：停工损失     {format_money(result['total'])}",
        f"贷：应付职工薪酬/制造费用等     {format_money(result['total'])}",
    ]
    if result["insurance"]:
        journal.append(f"借：其他应收款     {format_money(result['insurance'])}")
    if is_normal:
        journal.append(f"借：生产成本——基本生产成本（停工损失）     {format_money(result['net'])}")
    else:
        journal.append(f"借：营业外支出——非常损失     {format_money(result['net'])}")
    journal.append(f"贷：停工损失     {format_money(result['total'])}")
    if result["insurance"]:
        journal.append("说明：赔偿款先冲减停工损失，余额按正常/非正常停工分别处理。")
    print_journal(journal)

    summary = [
        f"停工净损失 {format_money(result['net'])} 元，处理方式为：{result['treatment']}。",
        "正常停工损失由开工后的产品成本负担；非正常停工损失不计入产品成本。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第四章 制造费用与生产损失",
        "停工损失核算",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("停工损失计算表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"停工净损失 {format_money(result['net'])} 元，{result['treatment']}。",
    )



def run_period_expenses() -> None:
    """期间费用结转。"""
    print_heading("第四章 期间费用：销售费用、管理费用、财务费用结转", "-")
    sales = input_float("销售费用（元）", 20000.0, min_value=0.0, name="销售费用")
    admin = input_float("管理费用（元）", 30000.0, min_value=0.0, name="管理费用")
    finance = input_float("财务费用（元）", 8000.0, min_value=0.0, name="财务费用")
    result = period_expenses(sales, admin, finance)

    question = (
        f"某企业本月发生销售费用 {format_money(result['sales'])} 元、管理费用 {format_money(result['admin'])} 元、"
        f"财务费用 {format_money(result['finance'])} 元。期末将期间费用结转至本年利润，要求计算期间费用合计并编制分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "期间费用合计 = 销售费用 + 管理费用 + 财务费用",
        "期间费用不计入产品生产成本，期末直接转入“本年利润”。",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = [
        f"销售费用 {format_money(result['sales'])} 元；管理费用 {format_money(result['admin'])} 元；财务费用 {format_money(result['finance'])} 元。",
        f"期间费用合计 = {format_money(result['sales'])} + {format_money(result['admin'])} + {format_money(result['finance'])} = {format_money(result['total'])} 元。",
    ]
    print_steps(steps)

    headers = ["期间费用项目", "金额（元）", "结转方向"]
    rows = [
        ["销售费用", format_money(result["sales"]), "本年利润"],
        ["管理费用", format_money(result["admin"]), "本年利润"],
        ["财务费用", format_money(result["finance"]), "本年利润"],
        ["合计", format_money(result["total"]), "—"],
    ]
    print_table(headers, rows, "期间费用结转表")

    journal = [
        f"借：本年利润     {format_money(result['total'])}",
        f"贷：销售费用     {format_money(result['sales'])}",
        f"贷：管理费用     {format_money(result['admin'])}",
        f"贷：财务费用     {format_money(result['finance'])}",
    ]
    print_journal(journal)

    summary = [
        f"期间费用合计 {format_money(result['total'])} 元，已全部结转至本年利润。",
        "期间费用不进入产品成本，因此不影响存货计价，但直接影响当期利润。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第四章 制造费用与生产损失",
        "期间费用结转",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("期间费用结转表", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"期间费用合计 {format_money(result['total'])} 元，已结转本年利润。",
    )


def show_unrepairable_comparison() -> None:
    """不可修复废品损失两种计算口径比较。"""
    print_heading("第四章 生产损失：不可修复废品损失计算口径比较", "-")
    headers = ["比较项目", "按定额成本计算", "按实际成本计算"]
    rows = [
        ["计算依据", "单位废品定额成本", "产品实际总成本和实际产量"],
        ["适用条件", "定额资料健全、废品较少", "实际成本资料完整"],
        ["优点", "计算简便、便于日常控制", "结果贴近实际耗费"],
        ["局限", "定额与实际可能偏离", "需要完整的产量和成本分配资料"],
        ["净损失公式", "定额成本 - 残料 - 赔款", "废品实际成本 - 残料 - 赔款"],
    ]
    print_table(headers, rows, "两种方法比较")
    print_summary(
        [
            "无论采用哪种口径，残料价值和应收赔款都应从废品损失中扣除。",
            "废品净损失最终由合格产品成本负担，计入“生产成本——基本生产成本（废品损失）”。",
        ],
        "核对提示",
    )


def run_unrepairable() -> None:
    """不可修复废品损失子菜单。"""
    options = [
        ("1", "按定额成本计算不可修复废品损失", run_unrepairable_quota),
        ("2", "按实际成本计算不可修复废品损失", run_unrepairable_actual),
        ("3", "两种计算口径比较", show_unrepairable_comparison),
    ]
    run_menu("第四章 生产损失：不可修复废品损失", options, back_text="返回生产损失菜单")


def run() -> None:
    """第四章菜单。"""
    options = [
        ("1", "制造费用归集", run_collect_overhead),
        ("2", "制造费用分配（工时/工资/机器工时/年度计划分配率）", run_overhead_allocation),
        ("3", "不可修复废品损失（定额成本/实际成本）", run_unrepairable),
        ("4", "可修复废品损失", run_repairable),
        ("5", "停工损失（正常/非正常停工）", run_downtime),
        ("6", "销售费用、管理费用、财务费用结转", run_period_expenses),
    ]
    run_menu("第四章 制造费用、生产损失与期间费用核算", options, back_text="返回主菜单")

