"""
PPT 生成器（ppt_generator）
职责：封装现有的 ppt_tool，作为子图中的一个独立节点。
"""
import time
from app.resource_subgraph.state import ResourceSubState
from app.models.resources import Resource
from app.tools.ppt_tool import generate_ppt


def ppt_generator(state: ResourceSubState) -> dict:
    """
    根据知识点生成 PPT 课件。
    内部调用讯飞 PPT API（通过 ppt_tool.generate_ppt），返回下载链接。
    """
    knowledge_point = state.get("knowledge_point", "")
    rewritten = state.get("rewritten_query", "")

    topic = rewritten or knowledge_point
    if not topic:
        print(f"[PPTGenerator] ⚠️ 无知识点，跳过")
        return {"generated_resources": []}

    print(f"\n[PPTGenerator] 📊 开始生成 PPT: {topic}")

    try:
        # 调用现有的 PPT 生成工具
        download_url = generate_ppt(topic, use_outline=True)

        if not download_url or "失败" in download_url:
            print(f"[PPTGenerator] ⚠️ PPT 生成未成功: {download_url}")
            return {"generated_resources": []}

        resource = Resource(
            id=f"ppt_{int(time.time())}",
            type="ppt",
            title=f"{topic} 课件",
            content=download_url,  # 直接存下载链接
            knowledge_point=knowledge_point or topic,
            difficulty="medium",
        )
        print(f"[PPTGenerator] ✅ PPT 生成完成: {download_url[:60]}...")
        return {"generated_resources": [resource]}

    except Exception as e:
        print(f"[PPTGenerator] ❌ 生成失败: {e}")
        return {"generated_resources": []}
