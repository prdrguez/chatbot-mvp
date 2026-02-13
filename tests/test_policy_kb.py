from chatbot_mvp.knowledge.policy_kb import load_kb, retrieve


def test_policy_kb_retrieval_regalos():
    kb_text = """
Articulo 1
Principios generales de conducta.

Articulo 2
Regalos y hospitalidades: no se pueden recibir regalos de clientes que comprometan la independencia.
"""
    kb_index = load_kb(kb_text, "securin.txt")
    matches = retrieve("Se pueden recibir regalos de clientes?", kb_index, top_k=3)

    assert matches
    assert any("regalos" in match["text"].lower() for match in matches)
    assert any("articulo" in match["source"].lower() for match in matches)
