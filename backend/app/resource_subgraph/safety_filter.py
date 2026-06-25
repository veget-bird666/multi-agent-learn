"""
安全过滤节点（Safety Filter）
职责：对生成的所有资源进行内容安全审查和事实准确性检查。
      通过检查的资源放行，未通过的被标记（由 collector 统一过滤）。

位置：在子图中位于 generators → safety_filter → collector
行为：fan-in 节点，等待所有 Send() 分支完成后运行一次，检查完整的资源列表。
"""
from typing import List as TypingList

from app.core.content_safety import content_safety_checker
from app.resource_subgraph.state import ResourceSubState


def safety_filter(state: ResourceSubState) -> dict:
    """
    安全检查节点：遍历 generated_resources，对每个资源执行：
      1. 敏感词扫描
      2. LLM 内容安全审查
      3. 事实准确性检查（防幻觉）

    检查通过的资源保留在 generated_resources 中。
    未通过的资源 ID 记录到 unsafe_resource_ids 中，供 collector 过滤。

    备注：
    本节点不直接修改 generated_resources（避免与 reducer 冲突），
    而是通过 unsafe_resource_ids 标记问题资源，由 collector 统一过滤。
    """
    resources = state.get("generated_resources", [])
    topic = state.get("knowledge_point", "")

    if not resources:
        print(f"[SafetyFilter]  无资源需要检查，跳过")
        return {"unsafe_resource_ids": []}

    print(f"\n[SafetyFilter]  开始安全检查 ({len(resources)} 项资源)...")

    unsafe_ids: TypingList[str] = []

    for res in resources:
        # 略过非文字类资源（图片、视频只存储链接，内容不在系统内）
        if res.type in ("image", "video", "ppt"):
            print(f"  跳过 {res.type}: {res.title}（非文字内容，不做审查）")
            continue

        passed, issues = content_safety_checker.check_resource(
            resource=res,
            knowledge_context="",
        )

        if passed:
            print(f"  ✓ {res.type}: {res.title}")
        else:
            unsafe_ids.append(res.id)
            print(f"  ✗ {res.type}: {res.title}")
            for issue in issues:
                print(f"    原因: {issue}")

    if unsafe_ids:
        print(f"[SafetyFilter]  共标记 {len(unsafe_ids)} 项不安全资源")
    else:
        print(f"[SafetyFilter]  所有资源检查通过 ✓")

    return {"unsafe_resource_ids": unsafe_ids}
