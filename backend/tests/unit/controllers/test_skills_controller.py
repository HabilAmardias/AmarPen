from pentest_platform.controllers.deps import get_actor, get_skills
from pentest_platform.domain.entities import SkillPack, SkillRelease
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

PACK = SkillPack(id="pack-1", key="wstg-web", name="WSTG", version=1, state="DRAFT", skills=[])
RELEASE = SkillRelease(id="release-1", name="baseline", manifest={"wstg-web": "pack-1"}, validated=True)


class StubSkills:
    def list_packs(self, actor, include_skills=False):
        return [{"id": PACK.id, "key": PACK.key, "name": PACK.name, "state": PACK.state, "skill_count": 0}]

    def get_pack(self, actor, pack_id):
        return {"id": pack_id, "key": PACK.key, "name": PACK.name, "skills": []}

    def create_pack(self, actor, payload):
        return PACK

    def update_pack(self, actor, pack_id, payload):
        return PACK

    def validate_pack(self, actor, pack_id):
        return {"passed": True, "errors": []}

    def publish_pack(self, actor, pack_id):
        return PACK

    def retire_pack(self, actor, pack_id):
        return PACK

    def list_releases(self, actor):
        return [RELEASE]

    def create_release(self, actor, name, manifest):
        return RELEASE

    def validate_release(self, actor, release_id):
        return RELEASE

    def activate_release(self, actor, release_id, reason=""):
        return RELEASE

    def rollback_release(self, actor, release_id, reason=""):
        return RELEASE


def test_skill_admin_endpoints():
    client = make_client({get_actor: lambda: actor(), get_skills: lambda: StubSkills()})
    assert client.get("/api/v1/admin/skills/packs").json()["items"][0]["key"] == "wstg-web"
    assert client.get("/api/v1/admin/skills/packs/pack-1").json()["name"] == "WSTG"
    assert client.post("/api/v1/admin/skills/packs", json={"key": "wstg-web", "name": "WSTG", "skills": []}).status_code == 201
    assert client.put("/api/v1/admin/skills/packs/pack-1", json={"expected_version": 1, "name": "Updated"}).status_code == 200
    assert client.post("/api/v1/admin/skills/packs/pack-1/validate").json()["passed"] is True
    assert client.post("/api/v1/admin/skills/packs/pack-1/publish").status_code == 200
    assert client.post("/api/v1/admin/skills/packs/pack-1/retire").status_code == 200
    assert client.get("/api/v1/admin/skills/releases").json()["items"][0]["name"] == "baseline"
    assert client.post("/api/v1/admin/skills/releases", json={"name": "baseline", "manifest": {"wstg-web": "pack-1"}}).status_code == 201
    assert client.post("/api/v1/admin/skills/releases/release-1/validate").status_code == 200
    assert client.post("/api/v1/admin/skills/releases/release-1/activate", json={"reason": "test"}).status_code == 200
    assert client.post("/api/v1/admin/skills/releases/release-1/rollback", json={"reason": "test"}).status_code == 200
