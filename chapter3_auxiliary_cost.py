"""第三章 辅助生产费用的归集与分配。

完整实现四种方法：
1. 直接分配法：不考虑辅助生产车间之间相互提供劳务；
2. 一次交互分配法：先在各辅助生产车间之间交互分配，再对外分配；
3. 计划成本分配法：按计划单位成本分配，并计算、结转成本差异；
4. 代数分配法：建立联立方程，精确求解各辅助生产车间的实际单位成本。

所有方法均输出分配计算表、分步过程、会计分录，并自动保存 CSV。
案例为自行设计的供电、供水两个辅助生产车间的模拟教学案例。
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

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
    solve_linear_system,
)


DEFAULT_AUX_NAMES = ["供电车间", "供水车间"]
DEFAULT_RECIPIENTS = DEFAULT_AUX_NAMES + ["基本生产车间", "行政管理部门", "销售部门"]
DEFAULT_COSTS = [24000.0, 16000.0]
# 行：提供服务的辅助车间；列：受益对象（前两列为辅助车间，后三列为外部受益对象）
DEFAULT_Q = [
    [0.0, 3000.0, 20000.0, 4000.0, 3000.0],
    [500.0, 0.0, 7000.0, 1500.0, 1000.0],
]


def _recipient_names(aux_names: Sequence[str]) -> List[str]:
    """辅助车间名称 + 三个外部受益对象。"""
    return list(aux_names) + ["基本生产车间", "行政管理部门", "销售部门"]


def _validate_case(costs: Sequence[Any], q: Sequence[Sequence[Any]], names: Sequence[str]) -> Tuple[List[float], List[List[float]]]:
    """校验辅助生产费用和服务量数据。"""
    n = len(names)
    if n < 2:
        raise ValidationError("辅助生产车间至少需要 2 个，才能体现交互分配。")
    if len(costs) != n:
        raise ValidationError("辅助生产车间数量与直接费用数量不一致。")
    if len(q) != n:
        raise ValidationError("服务量矩阵行数与辅助生产车间数量不一致。")
    recipients_count = n + 3
    costs_value = [require_nonnegative(cost, f"{names[i]}的直接费用") for i, cost in enumerate(costs)]
    q_value: List[List[float]] = []
    for i, row in enumerate(q):
        if len(row) != recipients_count:
            raise ValidationError(f"{names[i]}的服务量记录列数不正确，应为 {recipients_count} 列。")
        new_row = [require_nonnegative(value, f"{names[i]}向{_recipient_names(names)[j]}提供的服务量") for j, value in enumerate(row)]
        total = sum(new_row) - new_row[i]
        if total <= 0:
            raise ValidationError(f"{names[i]}对外提供的服务量合计必须大于 0。")
        q_value.append(new_row)
    return costs_value, q_value


def _total_service(q_row: Sequence[float], exclude_self: int) -> float:
    """某辅助车间提供的劳务总量（不含向自身提供的服务）。"""
    return sum(value for index, value in enumerate(q_row) if index != exclude_self)


def direct_method(costs: Sequence[float], q: Sequence[Sequence[float]], names: Sequence[str]) -> Dict[str, Any]:
    """直接分配法：只对辅助生产车间以外的受益对象分配。"""
    n = len(names)
    external_indices = list(range(n, n + 3))
    rows: List[Dict[str, Any]] = []
    external_totals = [0.0, 0.0, 0.0]
    for i in range(n):
        external_qty = sum(q[i][j] for j in external_indices)
        if external_qty <= 0:
            raise ValidationError(f"{names[i]}对外提供的服务量为 0，不能采用直接分配法。")
        rate = safe_div(costs[i], external_qty, f"{names[i]}的分配率")
        allocations, _ = allocate_amount(
            costs[i],
            [q[i][j] for j in external_indices],
            labels=[_recipient_names(names)[j] for j in external_indices],
        )
        for k, amount in enumerate(allocations):
            external_totals[k] = round(external_totals[k] + amount, 2)
        rows.append({
            "name": names[i],
            "cost": costs[i],
            "external_qty": external_qty,
            "rate": rate,
            "allocations": allocations,
        })
    return {
        "method": "直接分配法",
        "rows": rows,
        "external_names": _recipient_names(names)[n:],
        "external_totals": external_totals,
        "total": round(sum(costs), 2),
    }


def interactive_method(costs: Sequence[float], q: Sequence[Sequence[float]], names: Sequence[str]) -> Dict[str, Any]:
    """一次交互分配法。

    第一步：各辅助车间按劳务总量（含向其他辅助车间提供的劳务）计算交互分配率，
            只在辅助车间之间分配；
    第二步：计算各辅助车间调整后的费用 = 直接费用 + 交互转入 - 交互转出，
            再按对外劳务量分配给基本生产车间、行政管理部门和销售部门。
    """
    n = len(names)
    external_indices = list(range(n, n + 3))
    total_services = [_total_service(q[i], i) for i in range(n)]
    first_rows: List[Dict[str, Any]] = []
    transferred_in = [0.0] * n
    transferred_out = [0.0] * n
    for i in range(n):
        rate = safe_div(costs[i], total_services[i], f"{names[i]}的交互分配率")
        allocations = []
        for j in range(n):
            if j == i:
                allocations.append(0.0)
            else:
                amount = round(q[i][j] * rate, 2)
                allocations.append(amount)
                transferred_in[j] = round(transferred_in[j] + amount, 2)
                transferred_out[i] = round(transferred_out[i] + amount, 2)
        first_rows.append({
            "name": names[i],
            "cost": costs[i],
            "total_service": total_services[i],
            "rate": rate,
            "allocations": allocations,
            "out_total": transferred_out[i],
        })

    adjusted_costs = [round(costs[i] + transferred_in[i] - transferred_out[i], 2) for i in range(n)]
    second_rows: List[Dict[str, Any]] = []
    external_totals = [0.0, 0.0, 0.0]
    for i in range(n):
        external_qty = sum(q[i][j] for j in external_indices)
        if external_qty <= 0:
            raise ValidationError(f"{names[i]}对外提供的服务量为 0，不能进行对外分配。")
        rate = safe_div(adjusted_costs[i], external_qty, f"{names[i]}的对外分配率")
        allocations, _ = allocate_amount(
            adjusted_costs[i],
            [q[i][j] for j in external_indices],
            labels=[_recipient_names(names)[j] for j in external_indices],
        )
        for k, amount in enumerate(allocations):
            external_totals[k] = round(external_totals[k] + amount, 2)
        second_rows.append({
            "name": names[i],
            "adjusted_cost": adjusted_costs[i],
            "external_qty": external_qty,
            "rate": rate,
            "allocations": allocations,
        })
    return {
        "method": "一次交互分配法",
        "first_rows": first_rows,
        "second_rows": second_rows,
        "transferred_in": transferred_in,
        "transferred_out": transferred_out,
        "adjusted_costs": adjusted_costs,
        "external_names": _recipient_names(names)[n:],
        "external_totals": external_totals,
        "total": round(sum(costs), 2),
        "total_adjusted": round(sum(adjusted_costs), 2),
    }


def planned_method(
    costs: Sequence[float],
    q: Sequence[Sequence[float]],
    names: Sequence[str],
    planned_rates: Sequence[float],
) -> Dict[str, Any]:
    """计划成本分配法。

    按计划单位成本向所有受益对象（含其他辅助车间）分配；
    实际成本 = 直接费用 + 按计划成本从其他辅助车间转入的费用；
    成本差异 = 实际成本 - 按计划成本分配转出的费用。
    """
    n = len(names)
    if len(planned_rates) != n:
        raise ValidationError("计划单位成本数量与辅助生产车间数量不一致。")
    rates = [require_nonnegative(rate, f"{names[i]}的计划单位成本") for i, rate in enumerate(planned_rates)]
    total_services = [_total_service(q[i], i) for i in range(n)]
    planned_out = [round(rates[i] * total_services[i], 2) for i in range(n)]
    planned_in = [0.0] * n
    allocation_rows: List[Dict[str, Any]] = []
    for i in range(n):
        allocations = []
        for j in range(n + 3):
            amount = 0.0 if j == i else round(q[i][j] * rates[i], 2)
            allocations.append(amount)
            if j != i and j < n:
                planned_in[j] = round(planned_in[j] + amount, 2)
        allocation_rows.append({
            "name": names[i],
            "planned_rate": rates[i],
            "total_service": total_services[i],
            "planned_out": planned_out[i],
            "allocations": allocations,
        })

    actual_costs = [round(costs[i] + planned_in[i], 2) for i in range(n)]
    differences = [round(actual_costs[i] - planned_out[i], 2) for i in range(n)]
    external_totals = [0.0, 0.0, 0.0]
    for i in range(n):
        for k, j in enumerate(range(n, n + 3)):
            external_totals[k] = round(external_totals[k] + allocation_rows[i]["allocations"][j], 2)
    return {
        "method": "计划成本分配法",
        "rates": rates,
        "rows": allocation_rows,
        "planned_in": planned_in,
        "planned_out": planned_out,
        "actual_costs": actual_costs,
        "differences": differences,
        "total_difference": round(sum(differences), 2),
        "external_names": _recipient_names(names)[n:],
        "external_totals": external_totals,
        "total": round(sum(costs), 2),
    }



def algebraic_method(costs: Sequence[float], q: Sequence[Sequence[float]], names: Sequence[str]) -> Dict[str, Any]:
    """代数分配法：联立方程求解各辅助车间的待分配总成本与单位成本。

    设 x_i 为第 i 个辅助车间的待分配总成本，则：
        x_i = 直接费用_i + Σ(第 j 个辅助车间向 i 提供的服务量 ÷ 第 j 个车间劳务总量) × x_j
    整理后得到线性方程组 A x = b，用高斯消元法求解；单位成本 = x_i ÷ 劳务总量。
    """
    n = len(names)
    total_services = [_total_service(q[i], i) for i in range(n)]
    matrix: List[List[float]] = []
    vector: List[float] = []
    for i in range(n):
        row = [0.0] * n
        row[i] = 1.0
        for j in range(n):
            if j == i:
                continue
            # 第 j 个车间向第 i 个车间提供的服务量占 j 车间劳务总量的比例
            row[j] -= q[j][i] / total_services[j]
        matrix.append(row)
        vector.append(costs[i])

    total_costs = solve_linear_system(matrix, vector)
    total_costs = [round(value, 10) for value in total_costs]
    unit_costs = [round(total_costs[i] / total_services[i], 10) for i in range(n)]
    allocation_rows: List[Dict[str, Any]] = []
    recipient_totals = [0.0] * (n + 3)
    for i in range(n):
        allocations = []
        for j in range(n + 3):
            amount = 0.0 if j == i else round(q[i][j] * unit_costs[i], 2)
            allocations.append(amount)
            recipient_totals[j] = round(recipient_totals[j] + amount, 2)
        allocation_rows.append({
            "name": names[i],
            "total_service": total_services[i],
            "total_cost": total_costs[i],
            "unit_cost": unit_costs[i],
            "allocations": allocations,
        })
    return {
        "method": "代数分配法",
        "rows": allocation_rows,
        "total_costs": total_costs,
        "unit_costs": unit_costs,
        "recipient_names": _recipient_names(names),
        "recipient_totals": recipient_totals,
        "external_names": _recipient_names(names)[n:],
        "external_totals": recipient_totals[n:],
        "external_total": round(sum(recipient_totals[n:]), 2),
        "total": round(sum(costs), 2),
        "total_allocated": round(sum(recipient_totals), 2),
    }


def _read_case() -> Tuple[List[str], List[float], List[List[float]]]:
    """读取辅助生产费用案例；默认使用内置模拟案例。"""
    names = list(DEFAULT_AUX_NAMES)
    recipients = _recipient_names(names)
    print_subheading("内置教学案例资料")
    print("  辅助车间：供电车间直接费用 24,000 元；供水车间直接费用 16,000 元。")
    print("  服务量：供电车间提供 30,000 千瓦时（其中供水 3,000）；供水车间提供 10,000 吨（其中供电 500）。")
    headers = ["提供服务车间"] + recipients
    rows = []
    for i, name in enumerate(names):
        rows.append([name] + [f"{value:,.0f}" for value in DEFAULT_Q[i]])
    print_table(headers, rows, "辅助生产车间服务量资料")
    if input_yes_no("是否使用上述内置案例", True):
        return names, list(DEFAULT_COSTS), [row[:] for row in DEFAULT_Q]

    count = input_int("辅助生产车间数量", 2, min_value=2, max_value=5, name="辅助生产车间数量")
    names = []
    for i in range(count):
        names.append(input_text(f"第{i + 1}个辅助生产车间名称", f"辅助车间{i + 1}"))
    recipients = _recipient_names(names)
    costs = []
    for name in names:
        costs.append(input_float(f"{name}的直接费用（元）", 10000.0, min_value=0.0, name="直接费用"))
    q: List[List[float]] = []
    for i, name in enumerate(names):
        row = []
        for j, recipient in enumerate(recipients):
            if i == j:
                row.append(0.0)
                continue
            default = 1000.0 if j >= count else 300.0
            row.append(input_float(f"{name}向{recipient}提供的服务量", default, min_value=0.0, name="服务量"))
        q.append(row)
    return names, costs, q


def _print_case(names: Sequence[str], costs: Sequence[float], q: Sequence[Sequence[float]]) -> None:
    """打印案例服务量资料。"""
    recipients = _recipient_names(names)
    headers = ["提供服务车间", "直接费用（元）"] + recipients
    rows = []
    for i, name in enumerate(names):
        rows.append([name, format_money(costs[i])] + [f"{q[i][j]:,.2f}" for j in range(len(recipients))])
    print_table(headers, rows, "辅助生产车间服务量与直接费用资料")



def run_direct() -> None:
    """直接分配法交互计算。"""
    print_heading("第三章 辅助生产费用：直接分配法", "-")
    names, costs, q = _read_case()
    costs, q = _validate_case(costs, q, names)
    _print_case(names, costs, q)
    result = direct_method(costs, q, names)
    external_names = result["external_names"]
    question = (
        "某企业设有若干辅助生产车间，本月各辅助生产车间发生的直接费用及向各受益对象提供的服务量如下表。"
        "采用直接分配法分配辅助生产费用，要求计算各辅助车间的对外分配率、各受益对象应负担的费用，并编制会计分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question} 直接分配法不考虑辅助生产车间之间相互提供的劳务。")
    formulas = [
        "某辅助车间分配率 = 该车间直接费用 ÷ 向辅助生产车间以外受益对象提供的劳务量合计",
        "某受益对象应负担费用 = 该对象接受的劳务量 × 该辅助车间分配率",
        "各辅助车间分配额合计应等于其直接费用。",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = []
    for row in result["rows"]:
        steps.append(
            f"{row['name']}：对外劳务量 = {row['external_qty']:,.2f}；分配率 = {format_money(row['cost'])} ÷ "
            f"{row['external_qty']:,.2f} = {row['rate']:.6f} 元/单位劳务。"
        )
        for name, amount in zip(external_names, row["allocations"]):
            steps.append(f"    {name}应负担 = {row['rate']:.6f} × 接受劳务量 = {format_money(amount)} 元。")
    steps.append(f"对外分配总额 = {format_money(sum(result['external_totals']))} 元，与辅助生产费用合计 {format_money(result['total'])} 元一致。")
    print_steps(steps)

    headers = ["辅助车间", "直接费用（元）", "对外劳务量", "分配率"] + external_names + ["分配合计（元）"]
    rows = []
    for row in result["rows"]:
        rows.append([
            row["name"], format_money(row["cost"]), f"{row['external_qty']:,.2f}", f"{row['rate']:.6f}",
            *[format_money(amount) for amount in row["allocations"]], format_money(sum(row["allocations"])),
        ])
    rows.append(["合计", format_money(result["total"]), "—", "—", *[format_money(amount) for amount in result["external_totals"]], format_money(sum(result["external_totals"]))])
    print_table(headers, rows, "辅助生产费用分配表——直接分配法")

    journal = []
    for name, amount in zip(external_names, result["external_totals"]):
        account = "制造费用" if name == "基本生产车间" else ("管理费用" if name == "行政管理部门" else "销售费用")
        journal.append(f"借：{account}     {format_money(amount)}")
    for row in result["rows"]:
        journal.append(f"贷：辅助生产成本——{row['name']}     {format_money(row['cost'])}")
    print_journal(journal)

    summary = [
        "直接分配法计算简便，但没有考虑辅助生产车间之间的交互服务，分配结果不够精确。",
        "适用于辅助生产车间之间相互提供劳务较少，或交互服务对成本影响较小的情况。",
        f"本次对外分配总额 {format_money(sum(result['external_totals']))} 元，分配平衡。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第三章 辅助生产费用",
        "辅助生产费用分配——直接分配法",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("辅助生产费用分配表——直接分配法", headers, rows)],
        journal=journal,
        summary=summary,
        conclusion=f"直接分配法对外分配总额 {format_money(sum(result['external_totals']))} 元。",
    )



def run_interactive() -> None:
    """一次交互分配法交互计算。"""
    print_heading("第三章 辅助生产费用：一次交互分配法", "-")
    names, costs, q = _read_case()
    costs, q = _validate_case(costs, q, names)
    _print_case(names, costs, q)
    result = interactive_method(costs, q, names)
    external_names = result["external_names"]
    question = (
        "某企业辅助生产车间之间相互提供劳务。采用一次交互分配法：先按各辅助车间劳务总量在辅助车间之间交互分配，"
        "再计算调整后的费用，对外分配给基本生产车间、行政管理部门和销售部门。要求完成两阶段分配并编制分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "交互分配率 = 某辅助车间直接费用 ÷ 该车间劳务总量（含向其他辅助车间提供的劳务）",
        "交互转入（转出）费用 = 接受（提供）劳务量 × 提供方交互分配率",
        "调整后费用 = 直接费用 + 交互转入 - 交互转出",
        "对外分配率 = 调整后费用 ÷ 向辅助车间以外提供的劳务量",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = ["第一阶段：辅助生产车间之间的交互分配。"]
    for i, row in enumerate(result["first_rows"]):
        steps.append(
            f"{row['name']}：劳务总量 = {row['total_service']:,.2f}，交互分配率 = {format_money(row['cost'])} ÷ "
            f"{row['total_service']:,.2f} = {row['rate']:.6f} 元/单位。"
        )
        for j, amount in enumerate(row["allocations"]):
            if j != i and amount:
                steps.append(f"    向{names[j]}分配 = {format_money(amount)} 元。")
    for i, name in enumerate(names):
        steps.append(
            f"{name}调整后费用 = {format_money(costs[i])} + 转入 {format_money(result['transferred_in'][i])} - "
            f"转出 {format_money(result['transferred_out'][i])} = {format_money(result['adjusted_costs'][i])} 元。"
        )
    steps.append("第二阶段：将调整后费用对外分配。")
    for row in result["second_rows"]:
        steps.append(
            f"{row['name']}：对外劳务量 = {row['external_qty']:,.2f}，对外分配率 = {format_money(row['adjusted_cost'])} ÷ "
            f"{row['external_qty']:,.2f} = {row['rate']:.6f} 元/单位。"
        )
        for name, amount in zip(external_names, row["allocations"]):
            steps.append(f"    {name}应负担 {format_money(amount)} 元。")
    print_steps(steps)

    first_headers = ["辅助车间", "直接费用（元）", "劳务总量", "交互分配率"] + list(names) + ["转出合计（元）"]
    first_rows = []
    for row in result["first_rows"]:
        first_rows.append([
            row["name"], format_money(row["cost"]), f"{row['total_service']:,.2f}", f"{row['rate']:.6f}",
            *[format_money(amount) for amount in row["allocations"]], format_money(row["out_total"]),
        ])
    print_table(first_headers, first_rows, "第一阶段：辅助车间交互分配表")

    second_headers = ["辅助车间", "调整后费用（元）", "对外劳务量", "对外分配率"] + external_names + ["分配合计（元）"]
    second_rows = []
    for row in result["second_rows"]:
        second_rows.append([
            row["name"], format_money(row["adjusted_cost"]), f"{row['external_qty']:,.2f}", f"{row['rate']:.6f}",
            *[format_money(amount) for amount in row["allocations"]], format_money(sum(row["allocations"])),
        ])
    second_rows.append(["合计", format_money(result["total_adjusted"]), "—", "—", *[format_money(amount) for amount in result["external_totals"]], format_money(sum(result["external_totals"]))])
    print_table(second_headers, second_rows, "第二阶段：辅助生产费用对外分配表")

    journal = []
    for i, name in enumerate(names):
        for j, amount in enumerate(result["first_rows"][i]["allocations"]):
            if j != i and amount:
                journal.append(f"借：辅助生产成本——{names[j]}     {format_money(amount)}")
                journal.append(f"贷：辅助生产成本——{name}     {format_money(amount)}")
    for name, amount in zip(external_names, result["external_totals"]):
        account = "制造费用" if name == "基本生产车间" else ("管理费用" if name == "行政管理部门" else "销售费用")
        journal.append(f"借：{account}     {format_money(amount)}")
    for i, name in enumerate(names):
        journal.append(f"贷：辅助生产成本——{name}     {format_money(result['adjusted_costs'][i])}")
    print_journal(journal)

    summary = [
        "一次交互分配法考虑了辅助生产车间之间的相互服务，分配结果比直接分配法更准确。",
        f"交互分配后调整费用合计 {format_money(result['total_adjusted'])} 元，与对外分配总额一致。",
        "注意：第一阶段的内部转账与第二阶段的对外分配应分别列示，避免重复分配。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第三章 辅助生产费用",
        "辅助生产费用分配——一次交互分配法",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[
            ("第一阶段：辅助车间交互分配表", first_headers, first_rows),
            ("第二阶段：辅助生产费用对外分配表", second_headers, second_rows),
        ],
        journal=journal,
        summary=summary,
        conclusion=f"交互分配后调整费用合计 {format_money(result['total_adjusted'])} 元，对外分配完成。",
    )



def run_planned() -> None:
    """计划成本分配法交互计算。"""
    print_heading("第三章 辅助生产费用：计划成本分配法", "-")
    names, costs, q = _read_case()
    costs, q = _validate_case(costs, q, names)
    _print_case(names, costs, q)
    planned_defaults = [0.85, 1.70] if len(names) == 2 else []
    rates = []
    print_subheading("计划单位成本输入")
    for i, name in enumerate(names):
        total_service = _total_service(q[i], i)
        default = planned_defaults[i] if i < len(planned_defaults) else round(costs[i] / total_service, 2)
        rates.append(input_float(f"{name}的计划单位成本（元/单位劳务）", default, min_value=0.0, name="计划单位成本"))
    result = planned_method(costs, q, names, rates)
    recipients = _recipient_names(names)
    question = (
        "某企业辅助生产车间之间相互提供劳务，采用计划成本分配法。按计划单位成本向所有受益对象分配，"
        "再计算各辅助车间的实际成本与成本差异。要求编制分配表、差异计算表及会计分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "按计划成本分配合计 = 计划单位成本 × 该车间劳务总量",
        "某受益对象应负担计划成本 = 接受劳务量 × 提供方计划单位成本",
        "某辅助车间实际成本 = 直接费用 + 按计划成本从其他辅助车间转入的费用",
        "成本差异 = 实际成本 - 按计划成本分配转出额（正数为超支，负数为节约）",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = []
    for i, row in enumerate(result["rows"]):
        steps.append(
            f"{row['name']}：计划单位成本 {row['planned_rate']:.2f} 元，劳务总量 {row['total_service']:,.2f}，"
            f"计划分配合计 = {format_money(row['planned_out'])} 元。"
        )
        for j, amount in enumerate(row["allocations"]):
            if amount:
                steps.append(f"    向{recipients[j]}分配 {format_money(amount)} 元。")
    for i, name in enumerate(names):
        steps.append(
            f"{name}：实际成本 = 直接费用 {format_money(costs[i])} + 计划转入 {format_money(result['planned_in'][i])} "
            f"= {format_money(result['actual_costs'][i])} 元；成本差异 = {format_money(result['actual_costs'][i])} - "
            f"{format_money(result['planned_out'][i])} = {format_money(result['differences'][i])} 元。"
        )
    print_steps(steps)

    headers = ["辅助车间", "计划单位成本", "劳务总量", "计划分配额（元）"] + recipients + ["分配合计（元）"]
    rows = []
    for row in result["rows"]:
        rows.append([
            row["name"], f"{row['planned_rate']:.2f}", f"{row['total_service']:,.2f}", format_money(row["planned_out"]),
            *[format_money(amount) for amount in row["allocations"]], format_money(sum(row["allocations"])),
        ])
    print_table(headers, rows, "辅助生产费用计划成本分配表")

    diff_headers = ["辅助车间", "直接费用（元）", "计划转入（元）", "实际成本（元）", "计划转出（元）", "成本差异（元）", "差异性质"]
    diff_rows = []
    for i, name in enumerate(names):
        difference = result["differences"][i]
        diff_rows.append([
            name, format_money(costs[i]), format_money(result["planned_in"][i]), format_money(result["actual_costs"][i]),
            format_money(result["planned_out"][i]), format_money(difference), "超支" if difference >= 0 else "节约",
        ])
    diff_rows.append(["合计", format_money(sum(costs)), format_money(sum(result["planned_in"])), format_money(sum(result["actual_costs"])), format_money(sum(result["planned_out"])), format_money(result["total_difference"]), "—"])
    print_table(diff_headers, diff_rows, "辅助生产成本差异计算表")

    journal = []
    for i, row in enumerate(result["rows"]):
        for j, amount in enumerate(row["allocations"]):
            if not amount:
                continue
            if j < len(names):
                account = f"辅助生产成本——{names[j]}"
            elif recipients[j] == "基本生产车间":
                account = "制造费用"
            elif recipients[j] == "行政管理部门":
                account = "管理费用"
            else:
                account = "销售费用"
            journal.append(f"借：{account}     {format_money(amount)}")
        journal.append(f"贷：辅助生产成本——{row['name']}     {format_money(row['planned_out'])}")
    for i, name in enumerate(names):
        difference = result["differences"][i]
        if abs(difference) < 0.005:
            continue
        if difference > 0:
            journal.append(f"借：管理费用——辅助生产成本差异     {format_money(difference)}")
            journal.append(f"贷：辅助生产成本——{name}     {format_money(difference)}")
        else:
            journal.append(f"借：辅助生产成本——{name}     {format_money(-difference)}")
            journal.append(f"贷：管理费用——辅助生产成本差异     {format_money(-difference)}")
    print_journal(journal)

    summary = [
        f"计划成本分配法下，各辅助车间计划分配额合计 {format_money(sum(result['planned_out']))} 元。",
        f"成本差异合计 {format_money(result['total_difference'])} 元，正数为超支、负数为节约，已结转至管理费用。",
        "计划成本分配法便于考核辅助车间成本计划执行情况，但计划单位成本应尽量接近实际。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第三章 辅助生产费用",
        "辅助生产费用分配——计划成本分配法",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[
            ("辅助生产费用计划成本分配表", headers, rows),
            ("辅助生产成本差异计算表", diff_headers, diff_rows),
        ],
        journal=journal,
        summary=summary,
        conclusion=f"计划成本分配完成，成本差异合计 {format_money(result['total_difference'])} 元。",
    )



def run_algebraic() -> None:
    """代数分配法交互计算。"""
    print_heading("第三章 辅助生产费用：代数分配法", "-")
    names, costs, q = _read_case()
    costs, q = _validate_case(costs, q, names)
    _print_case(names, costs, q)
    result = algebraic_method(costs, q, names)
    recipients = result["recipient_names"]
    question = (
        "某企业辅助生产车间之间相互提供劳务。采用代数分配法，设各辅助车间的单位成本为未知数，"
        "建立联立方程求解，再按各受益对象接受的劳务量分配辅助生产费用。要求写出方程、求解过程并编制分录。"
    )
    print_subheading("一、文字题意")
    print(f"  {question}")
    formulas = [
        "设 x_i 为第 i 个辅助车间的待分配总成本。",
        "x_i = 直接费用_i + Σ（第 j 个车间向 i 提供的服务量 ÷ 第 j 个车间劳务总量）× x_j",
        "单位成本 = x_i ÷ 第 i 个车间劳务总量",
        "某受益对象应负担费用 = 接受劳务量 × 提供方单位成本",
    ]
    print_subheading("二、公式")
    for formula in formulas:
        print(f"  · {formula}")

    steps = ["建立联立方程组："]
    for i, name in enumerate(names):
        terms = [f"{format_money(costs[i])}"]
        for j, other in enumerate(names):
            if i == j:
                continue
            ratio = q[j][i] / _total_service(q[j], j)
            terms.append(f"{ratio:.6f}×x_{other}")
        steps.append(f"x_{name} = " + " + ".join(terms))
    steps.append("求解方程组，得到各辅助车间待分配总成本和单位成本：")
    for i, name in enumerate(names):
        steps.append(
            f"x_{name} = {format_money(result['total_costs'][i])} 元；"
            f"单位成本 = {format_money(result['total_costs'][i])} ÷ {result['rows'][i]['total_service']:,.2f} = "
            f"{result['unit_costs'][i]:.6f} 元/单位劳务。"
        )
    steps.append("按单位成本向各受益对象分配：")
    for i, row in enumerate(result["rows"]):
        for j, amount in enumerate(row["allocations"]):
            if amount:
                steps.append(f"{row['name']}向{recipients[j]}分配 = {format_money(amount)} 元。")
    steps.append(
        f"对外分配总额 = {format_money(result['external_total'])} 元，与辅助生产费用合计 {format_money(result['total'])} 元一致；"
        f"各辅助车间分配总额（含内部交互）为 {format_money(result['total_allocated'])} 元。"
    )
    print_steps(steps)

    headers = ["辅助车间", "直接费用（元）", "劳务总量", "待分配总成本（元）", "单位成本（元/单位）"]
    rows = [
        [row["name"], format_money(costs[i]), f"{row['total_service']:,.2f}", format_money(row["total_cost"]), f"{row['unit_cost']:.6f}"]
        for i, row in enumerate(result["rows"])
    ]
    print_table(headers, rows, "代数分配法单位成本计算表")

    alloc_headers = ["辅助车间"] + recipients + ["分配合计（元）"]
    alloc_rows = []
    for row in result["rows"]:
        alloc_rows.append([row["name"], *[format_money(amount) for amount in row["allocations"]], format_money(sum(row["allocations"]))])
    alloc_rows.append(["合计", *[format_money(amount) for amount in result["recipient_totals"]], format_money(result["total_allocated"])])
    print_table(alloc_headers, alloc_rows, "代数分配法费用分配表")

    journal = []
    for i, row in enumerate(result["rows"]):
        for j, amount in enumerate(row["allocations"]):
            if not amount:
                continue
            if j < len(names):
                account = f"辅助生产成本——{names[j]}"
            elif recipients[j] == "基本生产车间":
                account = "制造费用"
            elif recipients[j] == "行政管理部门":
                account = "管理费用"
            else:
                account = "销售费用"
            journal.append(f"借：{account}     {format_money(amount)}")
        journal.append(f"贷：辅助生产成本——{row['name']}     {format_money(sum(row['allocations']))}")
    print_journal(journal)

    summary = [
        "代数分配法通过联立方程同时考虑辅助车间之间的交互服务，分配结果最精确。",
        "各辅助车间单位成本：" + "；".join(f"{name} {result['unit_costs'][i]:.6f} 元/单位" for i, name in enumerate(names)) + "。",
        f"对外分配总额 {format_money(result['external_total'])} 元，与直接费用合计 {format_money(result['total'])} 元一致。",
        "当辅助车间较多时，手工求解方程较繁琐，本工具使用高斯消元法精确求解。",
    ]
    print_summary(summary)
    export.save_calculation(
        "第三章 辅助生产费用",
        "辅助生产费用分配——代数分配法",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[
            ("代数分配法单位成本计算表", headers, rows),
            ("代数分配法费用分配表", alloc_headers, alloc_rows),
        ],
        journal=journal,
        summary=summary,
        conclusion=f"代数分配法求得单位成本并完成分配，对外分配总额 {format_money(result['external_total'])} 元。",
    )


def show_comparison() -> None:
    """四种辅助生产费用分配方法比较。"""
    print_heading("第三章 辅助生产费用：四种方法比较", "-")
    headers = ["方法", "是否考虑辅助车间交互服务", "计算精度", "计算工作量", "适用情形"]
    rows = [
        ["直接分配法", "否", "较低", "最小", "辅助车间之间相互服务很少"],
        ["一次交互分配法", "是（一次交互）", "较高", "较小", "辅助车间之间服务较多，要求适当简化"],
        ["计划成本分配法", "是（按计划价）", "取决于计划成本准确性", "中等", "计划成本较健全，便于考核"],
        ["代数分配法", "是（完全交互）", "最高", "最大", "辅助车间较少、要求精确分配"],
    ]
    print_table(headers, rows, "辅助生产费用分配方法比较")
    print_summary(
        [
            "选择方法时应综合考虑辅助车间数量、交互服务程度、计划成本资料是否健全以及管理要求。",
            "无论采用哪种方法，最终对外分配的费用总额都应等于各辅助车间直接费用合计（计划成本法还需结转差异）。",
        ],
        "方法选择提示",
    )


def run() -> None:
    """第三章菜单。"""
    options = [
        ("1", "直接分配法", run_direct),
        ("2", "一次交互分配法", run_interactive),
        ("3", "计划成本分配法（含成本差异）", run_planned),
        ("4", "代数分配法（联立方程精确求解）", run_algebraic),
        ("5", "四种方法比较与方法选择", show_comparison),
    ]
    run_menu("第三章 辅助生产费用的归集与分配", options, back_text="返回主菜单")

