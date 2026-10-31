from conftest import login, cmd


def test_candidate_review_creates_separate_engineering_release(client):
    headers = login(client, "qc1")
    view = client.get("/api/v1/knowledge-graphs/views").json()
    ontology = view["ontology"]
    ontology["description"] = "工程定義說明更新；原對象與關係保持。"
    ontology["entityTypes"][0]["color"] = "#1234ab"
    created = client.post(
        "/api/v1/knowledge-graphs/drafts",
        headers=headers,
        json={
            "ontology": ontology,
            "base_release_id": "semantic-v1",
            "metadata_map": {"node_meta": view["node_meta"], "edge_meta": view["edge_meta"]},
        },
    )
    assert created.status_code == 200, created.text
    draft = created.json()
    submitted = client.post(
        "/api/v1/knowledge-graphs/drafts/" + draft["id"] + "/submit",
        headers=headers,
        json=cmd(draft["version"]),
    )
    assert submitted.status_code == 200, submitted.text
    headers = login(client, "expert1")
    forbidden = client.post(
        "/api/v1/knowledge-graphs/drafts/" + draft["id"] + "/review",
        headers=headers,
        json=cmd(submitted.json()["version"], {"decision": "approve"}),
    )
    assert forbidden.status_code == 403
    headers = login(client, "expert3")
    queue = client.get("/api/v1/knowledge-graphs/drafts").json()["items"]
    assert any(d["id"] == draft["id"] for d in queue)
    approved = client.post(
        "/api/v1/knowledge-graphs/drafts/" + draft["id"] + "/review",
        headers=headers,
        json=cmd(submitted.json()["version"], {"decision": "approve"}),
    )
    assert approved.status_code == 200, approved.text
    record = approved.json()
    assert not record["clinical_approved"] and record["semantic_release_id"] != "semantic-v1"
    after = client.get("/api/v1/knowledge-graphs/views?release_id=" + record["semantic_release_id"]).json()
    assert after["ontology"]["entityTypes"][0]["color"] == "#1234ab"
    original = client.get("/api/v1/knowledge-graphs/views?release_id=semantic-v1").json()
    assert original["ontology"]["entityTypes"][0]["color"] != "#1234ab"
    package = client.get("/api/v1/semantic/releases/" + record["semantic_release_id"] + "/package")
    assert package.status_code == 200 and package.headers["content-type"] == "application/zip"


def test_rule_definition_and_qualification_versions_are_separate(client):
    headers = login(client, "qc1")
    rule = client.get("/api/v1/rules").json()["items"][0]
    changed = client.post(
        "/api/v1/rules/" + rule["id"] + "/versions",
        headers=headers,
        json=cmd(rule["version"], {"content": rule["content"] + " 工程版本差異說明。"}),
    )
    assert changed.status_code == 200, changed.text
    candidate = changed.json()
    assert candidate["version"] == rule["version"] + 1 and candidate["id"] != rule["id"]
    headers = login(client, "expert3")
    reviewed = client.post(
        "/api/v1/rules/" + candidate["id"] + "/review",
        headers=headers,
        json=cmd(candidate["policy_version"], {"decision": "approve"}),
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "candidate" and not reviewed.json()["clinical_approved"]
    assert reviewed.json()["version"] == candidate["version"]
    assert reviewed.json()["policy_version"] == candidate["policy_version"] + 1
